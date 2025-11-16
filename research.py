
import json
import time
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from acp_sdk.server import Server
from acp_sdk.models import Message, MessagePart

# === WEB SEARCH (Google SERP) ===
try:
    from serpapi import GoogleSearch
    SERP_AVAILABLE = True
except ImportError:
    print("⚠️  serpapi not installed → pip install google-search-results")
    SERP_AVAILABLE = False

# Initialize server
server = Server()

# ============================================================================
# CONFIGURATION
# ============================================================================

import os
from dotenv import load_dotenv

# Load .env file (only needed in local development)
load_dotenv()  # ← remove or comment this line in production

# Azure Cognitive Search
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")          # ← this is the line you asked for

# Azure OpenAI
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
API_VERSION = os.getenv("API_VERSION", "2024-12-01-preview")  # default fallback
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o-08-06")

# SerpAPI
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ConversationContext:
    """Maintains conversation state for each session"""
    disease: Optional[str] = None
    conversation_history: List[Dict] = None
    textbook_context: Optional[str] = None
    last_search_time: float = 0
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []

# Global conversation storage (in production, use Redis or similar)
conversations: Dict[str, ConversationContext] = {}

# ============================================================================
# AZURE CLIENTS
# ============================================================================

def initialize_clients():
    """Initialize Azure OpenAI and Search clients"""
    openai_client = AzureOpenAI(
        api_key=Config.AZURE_OPENAI_KEY,
        api_version=Config.API_VERSION,
        azure_endpoint=Config.AZURE_OPENAI_ENDPOINT
    )
    
    search_client = SearchClient(
        endpoint=Config.AZURE_SEARCH_ENDPOINT,
        index_name=Config.AZURE_SEARCH_INDEX,
        credential=AzureKeyCredential(Config.AZURE_SEARCH_KEY)
    )
    
    return openai_client, search_client

def generate_embeddings(text: str, client) -> List[float]:
    """Generate embeddings for semantic search"""
    return client.embeddings.create(
        input=[text],
        model=Config.EMBEDDING_MODEL
    ).data[0].embedding

# ============================================================================
# DATABASE SEARCH (TEXTBOOK RAG)
# ============================================================================

def search_textbook(disease: str, search_client, openai_client) -> Dict:
    """Search nephrology textbook using vector similarity"""
    try:
        print(f"📚 Searching textbook for: {disease}")
        
        # Generate query embedding
        embeddings = generate_embeddings(disease, openai_client)
        
        # Perform vector search
        vector_query = VectorizedQuery(
            vector=embeddings, 
            k_nearest_neighbors=8, 
            fields="contentVector"
        )
        
        results = search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            top=8
        )
        
        # Collect and format results
        chunks = []
        sources = []
        
        for idx, result in enumerate(results):
            content = result.get('content', '').strip()
            if content:
                # Add metadata
                metadata = []
                if result.get('page'):
                    metadata.append(f"Page {result['page']}")
                if result.get('chapter'):
                    metadata.append(f"Chapter {result['chapter']}")
                
                chunk_text = content
                if metadata:
                    chunk_text += f" [{', '.join(metadata)}]"
                
                chunks.append(chunk_text)
                sources.append({
                    'type': 'textbook',
                    'page': result.get('page'),
                    'chapter': result.get('chapter'),
                    'id': result.get('id', f'chunk_{idx}')
                })
        
        combined_text = "\n\n---\n\n".join(chunks) if chunks else None
        
        return {
            "found": bool(chunks),
            "context": combined_text,
            "sources": sources,
            "num_chunks": len(chunks)
        }
        
    except Exception as e:
        print(f"❌ Textbook search error: {e}")
        return {
            "found": False,
            "context": None,
            "sources": [],
            "error": str(e)
        }

# ============================================================================
# WEB SEARCH (Google via SerpAPI)
# ============================================================================

def search_web(query: str, disease: str) -> Dict:
    """Search Google for latest medical information using SerpAPI"""
    if not SERP_AVAILABLE:
        return {
            "found": False,
            "context": None,
            "sources": [],
            "error": "SerpAPI not installed"
        }
    
    try:
        print(f"🌐 Searching web for: {query}")
        
        # Build medical-focused search query
        search_query = f"{disease} {query} site:nih.gov OR site:mayoclinic.org OR site:uptodate.com OR site:nejm.org OR site:kdigo.org"
        
        params = {
            "q": search_query,
            "api_key": Config.SERPAPI_KEY,
            "num": 6,
            "gl": "us",
            "hl": "en"
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        organic_results = results.get("organic_results", [])
        
        if not organic_results:
            return {
                "found": False,
                "context": "No reliable medical sources found on the web.",
                "sources": []
            }
        
        # Format results
        snippets = []
        sources = []
        
        for idx, result in enumerate(organic_results[:5]):
            title = result.get("title", "No title")
            snippet = result.get("snippet", "")
            link = result.get("link", "")
            
            snippets.append(f"[{idx+1}] {title}\n{snippet}\nSource: {link}\n")
            sources.append({
                "type": "web",
                "title": title,
                "url": link,
                "snippet": snippet[:200]
            })
        
        web_context = f"""[WEB SEARCH RESULTS - {disease.upper()}]
Based on latest information from medical websites (as of November 2025):

{"".join(snippets)}

⚠️ Always verify with your healthcare provider.
"""
        
        return {
            "found": True,
            "context": web_context,
            "sources": sources
        }
        
    except Exception as e:
        print(f"❌ Web search error: {e}")
        return {
            "found": False,
            "context": None,
            "sources": [],
            "error": str(e)
        }

# ============================================================================
# AI RESPONSE GENERATION
# ============================================================================

def generate_response(
    user_message: str,
    textbook_context: Optional[str],
    web_context: Optional[str],
    conversation_history: List[Dict],
    disease: str,
    openai_client
) -> str:
    """Generate natural, contextual response using GPT-4"""
    
    # Build system prompt
    system_prompt = f"""You are a friendly, knowledgeable nephrology assistant helping patients understand their kidney condition: {disease}.

Your role:
- Explain medical concepts in simple, clear language
- Be warm, empathetic, and supportive
- Always remind patients to consult their healthcare provider
- Use the provided textbook and web information to give accurate answers
- If you don't know something, admit it and suggest they ask their doctor

Guidelines:
- Keep responses concise (2-4 paragraphs max unless asked for details)
- Avoid medical jargon; use everyday language
- Be encouraging and reduce anxiety
- Never diagnose or prescribe
"""
    
    # Build context section
    context_section = ""
    if textbook_context:
        context_section += f"\n### MEDICAL TEXTBOOK INFORMATION:\n{textbook_context[:3000]}\n"
    
    if web_context:
        context_section += f"\n### LATEST WEB INFORMATION:\n{web_context[:2000]}\n"
    
    # Build conversation history
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add recent conversation history (last 6 messages)
    for msg in conversation_history[-6:]:
        messages.append(msg)
    
    # Add current query with context
    user_prompt = f"{context_section}\n\n### PATIENT'S QUESTION:\n{user_message}\n\nPlease provide a helpful, patient-friendly answer."
    messages.append({"role": "user", "content": user_prompt})
    
    try:
        response = openai_client.chat.completions.create(
            model=Config.GPT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"❌ AI generation error: {e}")
        return f"I'm having trouble generating a response right now. Please try again. (Error: {str(e)})"

# ============================================================================
# DETERMINE IF WEB SEARCH IS NEEDED
# ============================================================================

def should_search_web(user_message: str, textbook_found: bool, openai_client) -> bool:
    """Use AI to determine if web search would be helpful"""
    
    # Obvious triggers
    web_triggers = [
        "latest", "recent", "new", "current", "today", "2024", "2025",
        "guidelines", "study", "research", "treatment options",
        "side effects", "medications", "drugs"
    ]
    
    if any(trigger in user_message.lower() for trigger in web_triggers):
        return True
    
    # If textbook has nothing, definitely search web
    if not textbook_found:
        return True
    
    # Use AI to decide for ambiguous cases
    try:
        decision_prompt = f"""Does this patient question require current/recent medical information that might not be in a standard textbook?

Question: "{user_message}"

Answer with just 'YES' or 'NO'."""

        response = openai_client.chat.completions.create(
            model=Config.GPT_MODEL,
            messages=[{"role": "user", "content": decision_prompt}],
            temperature=0.3,
            max_tokens=10
        )
        
        answer = response.choices[0].message.content.strip().upper()
        return "YES" in answer
        
    except:
        return False  # Default to no web search if AI check fails

# ============================================================================
# INPUT EXTRACTION
# ============================================================================

def extract_message_content(input_obj) -> Optional[str]:
    """Extract text from various ACP input formats"""
    try:
        if isinstance(input_obj, str):
            return input_obj.strip()
        
        if isinstance(input_obj, list):
            for item in input_obj:
                if hasattr(item, 'parts') and item.parts:
                    for part in item.parts:
                        if hasattr(part, 'content'):
                            return str(part.content).strip()
        
        if hasattr(input_obj, 'parts') and input_obj.parts:
            for part in input_obj.parts:
                if hasattr(part, 'content'):
                    return str(part.content).strip()
        
        if hasattr(input_obj, 'content'):
            return str(input_obj.content).strip()
        
        # Try JSON parsing
        if isinstance(input_obj, dict):
            return input_obj.get('message') or input_obj.get('question') or input_obj.get('content')
        
        return str(input_obj).strip()
        
    except Exception as e:
        print(f"❌ Input extraction error: {e}")
        return None

# ============================================================================
# MAIN CHATBOT AGENT
# ============================================================================

@server.agent(name="NephrologyChat")
def nephrology_chatbot(input: any, context) -> str:
    """
    Interactive nephrology chatbot that:
    1. Searches textbook database
    2. Uses web search when needed
    3. Maintains conversation context
    4. Provides patient-friendly responses
    """
    
    print("\n" + "="*80)
    print("🩺 NEPHROLOGY CHATBOT - Processing Query")
    print("="*80)
    
    start_time = time.time()
    
    # Extract user message
    user_message = extract_message_content(input)
    if not user_message:
        return json.dumps({
            "error": "Could not understand input. Please send a text message.",
            "status": "error"
        }, indent=2)
    
    print(f"💬 User: {user_message}")
    
    # Initialize clients
    openai_client, search_client = initialize_clients()
    
    # Get or create conversation context
    session_id = context.get('session_id', 'default') if hasattr(context, 'get') else 'default'
    
    if session_id not in conversations:
        conversations[session_id] = ConversationContext()
    
    conv = conversations[session_id]
    
    # Extract disease if mentioned (simple keyword extraction)
    # In production, use NER or more sophisticated extraction
    disease = conv.disease
    if not disease:
        # Try to detect disease from message
        common_conditions = [
            "chronic kidney disease", "CKD", "acute kidney injury", "AKI",
            "diabetic nephropathy", "glomerulonephritis", "nephrotic syndrome",
            "polycystic kidney", "kidney stones", "hypertension"
        ]
        for condition in common_conditions:
            if condition.lower() in user_message.lower():
                disease = condition
                conv.disease = disease
                break
        
        if not disease:
            disease = "kidney disease"  # Default
            conv.disease = disease
    
    try:
        # STEP 1: Search textbook database
        textbook_result = search_textbook(disease, search_client, openai_client)
        textbook_context = textbook_result.get("context")
        sources = textbook_result.get("sources", [])
        
        print(f"📚 Textbook: {'Found' if textbook_result['found'] else 'Not found'} ({textbook_result.get('num_chunks', 0)} chunks)")
        
        # STEP 2: Decide if web search is needed
        need_web = should_search_web(user_message, textbook_result['found'], openai_client)
        
        web_context = None
        if need_web:
            web_result = search_web(user_message, disease)
            web_context = web_result.get("context")
            sources.extend(web_result.get("sources", []))
            print(f"🌐 Web Search: {'Used' if web_result['found'] else 'Failed'}")
        else:
            print("🌐 Web Search: Not needed")
        
        # STEP 3: Generate response
        response_text = generate_response(
            user_message=user_message,
            textbook_context=textbook_context,
            web_context=web_context,
            conversation_history=conv.conversation_history,
            disease=disease,
            openai_client=openai_client
        )
        
        # STEP 4: Update conversation history
        conv.conversation_history.append({"role": "user", "content": user_message})
        conv.conversation_history.append({"role": "assistant", "content": response_text})
        
        # Keep only last 12 messages
        if len(conv.conversation_history) > 12:
            conv.conversation_history = conv.conversation_history[-12:]
        
        # STEP 5: Format final response
        elapsed = round(time.time() - start_time, 2)
        
        result = {
            "response": response_text,
            "disease": disease,
            "sources": {
                "textbook_chunks": textbook_result.get('num_chunks', 0),
                "web_sources": len([s for s in sources if s.get('type') == 'web']),
                "total": len(sources)
            },
            "web_search_used": need_web and web_context is not None,
            "conversation_length": len(conv.conversation_history),
            "processing_time_seconds": elapsed,
            "status": "success"
        }
        
        print(f"✅ Response generated in {elapsed}s")
        print("="*80 + "\n")
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return json.dumps({
            "error": str(e),
            "status": "error",
            "processing_time_seconds": round(time.time() - start_time, 2)
        }, indent=2)

# ============================================================================
# CLEAR CONVERSATION (Optional utility endpoint)
# ============================================================================

@server.agent(name="ClearConversation")
def clear_conversation(input: any, context) -> str:
    """Clear conversation history for a session"""
    session_id = context.get('session_id', 'default') if hasattr(context, 'get') else 'default'
    
    if session_id in conversations:
        del conversations[session_id]
        return json.dumps({"message": "Conversation cleared", "status": "success"})
    
    return json.dumps({"message": "No conversation to clear", "status": "success"})

# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🩺 NEPHROLOGY CHATBOT SERVER")
    print("="*80)
    print(f"📍 Port: 8001")
    print(f"🤖 Agent: NephrologyChat")
    print(f"📚 Database: Azure AI Search + Vector RAG")
    print(f"🌐 Web Search: {'Enabled (SerpAPI)' if SERP_AVAILABLE else 'Disabled (install serpapi)'}")
    print("="*80)
    print("\n💡 Test with:")
    print("   curl -X POST http://localhost:8001/NephrologyChat \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"message\": \"What is chronic kidney disease?\"}'")
    print("\n   Or use the router.py client to chat interactively!")
    print("="*80 + "\n")
    
    if not SERP_AVAILABLE:
        print("⚠️  Install SerpAPI for web search: pip install google-search-results")
        print("⚠️  Get free API key at: https://serpapi.com/\n")
    
    server.run(port=8001)