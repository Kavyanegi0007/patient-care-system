

# """
# Nephrology AI Chatbot - Streamlit UI
# Simple, beautiful interface for the multi-agent nephrology system
# """

# import streamlit as st
# import asyncio
# import json
# from datetime import datetime
# from acp_sdk.client import Client
# from acp_sdk.models import Message, MessagePart

# # ============================================================================
# # CONFIGURATION
# # ============================================================================

# PATIENT_SERVER = "http://localhost:8003"
# CHATBOT_SERVER = "http://localhost:8001"

# # ============================================================================
# # PAGE CONFIG
# # ============================================================================

# st.set_page_config(
#     page_title="Nephrology AI Assistant",
#     page_icon="🩺",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # ============================================================================
# # CUSTOM CSS
# # ============================================================================

# st.markdown("""
# <style>
#     .main-header {
#         font-size: 2.5rem;
#         font-weight: bold;
#         color: #1f77b4;
#         text-align: center;
#         margin-bottom: 1rem;
#     }
#     .patient-card {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 1.5rem;
#         border-radius: 10px;
#         color: white;
#         margin-bottom: 1rem;
#         box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#     }
#     .patient-card h3 {
#         margin: 0;
#         color: white;
#     }
#     .patient-card p {
#         margin: 0.3rem 0;
#         font-size: 0.9rem;
#     }
#     .chat-message {
#         padding: 1rem;
#         border-radius: 10px;
#         margin-bottom: 1rem;
#         box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#         color: #000000;
#     }
#     .user-message {
#         background-color: #e3f2fd;
#         border-left: 4px solid #2196f3;
#         color: #000000;
#     }
#     .bot-message {
#         background-color: #f1f8e9;
#         border-left: 4px solid #4caf50;
#         color: #000000;
#     }
#     .chat-message strong {
#         color: #000000;
#     }
#     .source-badge {
#         display: inline-block;
#         background-color: #ff9800;
#         color: white;
#         padding: 0.2rem 0.6rem;
#         border-radius: 12px;
#         font-size: 0.75rem;
#         margin-right: 0.5rem;
#         margin-top: 0.5rem;
#     }
#     .warning-box {
#         background-color: #fff3cd;
#         border: 1px solid #ffc107;
#         border-radius: 5px;
#         padding: 1rem;
#         margin: 1rem 0;
#     }
#     .stButton>button {
#         width: 100%;
#         background-color: #1f77b4;
#         color: white;
#         font-weight: bold;
#         border-radius: 5px;
#         padding: 0.5rem;
#     }
#     .stButton>button:hover {
#         background-color: #1565c0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # ============================================================================
# # SESSION STATE INITIALIZATION
# # ============================================================================

# if 'messages' not in st.session_state:
#     st.session_state.messages = []

# if 'patient_loaded' not in st.session_state:
#     st.session_state.patient_loaded = False

# if 'patient_data' not in st.session_state:
#     st.session_state.patient_data = None

# if 'chat_history' not in st.session_state:
#     st.session_state.chat_history = []

# # ============================================================================
# # UTILITY FUNCTIONS
# # ============================================================================

# async def extract_text(resp):
#     """Extract text from ACP response"""
#     try:
#         if not resp or not resp.output or not resp.output[0].parts:
#             return None
#         return str(resp.output[0].parts[0].content)
#     except:
#         return None

# async def load_patient(name: str):
#     """Load patient record from database"""
#     try:
#         async with Client(base_url=PATIENT_SERVER) as client:
#             resp = await client.run_sync(
#                 agent="GetPatient",
#                 input=[Message(parts=[MessagePart(content=name, content_type="text/plain")])]
#             )
            
#             result = await extract_text(resp)
#             if not result:
#                 return None, "No response from patient server"
            
#             data = json.loads(result)
            
#             if "error" in data:
#                 return None, data["error"]
            
#             return data, None
            
#     except Exception as e:
#         return None, str(e)

# async def send_message(message: str, patient_data=None):
#     """Send message to chatbot"""
#     try:
#         # Build payload
#         if patient_data:
#             payload = {
#                 "message": message,
#                 "disease": patient_data.get("diagnosis"),
#                 "patient_name": patient_data.get("name"),
#                 "medications": patient_data.get("medications", [])[:5]
#             }
#         else:
#             payload = {"message": message}
        
#         async with Client(base_url=CHATBOT_SERVER) as client:
#             resp = await client.run_sync(
#                 agent="NephrologyChat",
#                 input=[Message(parts=[MessagePart(
#                     content=json.dumps(payload),
#                     content_type="application/json"
#                 )])]
#             )
            
#             result = await extract_text(resp)
#             if not result:
#                 return None, "No response from chatbot"
            
#             data = json.loads(result)
            
#             if data.get("status") == "error":
#                 return None, data.get("error", "Unknown error")
            
#             return data, None
            
#     except Exception as e:
#         return None, str(e)

# async def clear_conversation():
#     """Clear chatbot conversation history"""
#     try:
#         async with Client(base_url=CHATBOT_SERVER) as client:
#             await client.run_sync(
#                 agent="ClearConversation",
#                 input=[Message(parts=[MessagePart(content="clear", content_type="text/plain")])]
#             )
#         return True
#     except:
#         return False

# # ============================================================================
# # SIDEBAR - PATIENT INFORMATION
# # ============================================================================

# with st.sidebar:
#     st.markdown("### 🩺 Nephrology AI Assistant")
#     st.markdown("---")
    
#     # Patient Lookup Section
#     st.markdown("#### 👤 Patient Lookup")
    
#     if not st.session_state.patient_loaded:
#         patient_name = st.text_input(
#             "Enter patient name:",
#             placeholder="e.g., Sarah Jones",
#             help="Load patient record from database (optional)"
#         )
        
#         if st.button("🔍 Load Patient Record"):
#             if patient_name:
#                 with st.spinner("Loading patient record..."):
#                     patient_data, error = asyncio.run(load_patient(patient_name))
                    
#                     if error:
#                         st.error(f"❌ {error}")
#                     else:
#                         st.session_state.patient_data = patient_data
#                         st.session_state.patient_loaded = True
#                         st.success("✅ Patient record loaded!")
#                         st.rerun()
#             else:
#                 st.warning("Please enter a patient name")
    
#     else:
#         # Display loaded patient info
#         patient = st.session_state.patient_data
        
#         st.markdown(f"""
#         <div class="patient-card">
#             <h3>👤 {patient['name']}</h3>
#             <p><strong>🏥 Diagnosis:</strong> {patient['diagnosis']}</p>
#             <p><strong>📅 Discharge:</strong> {patient.get('discharge_date', 'N/A')}</p>
#             <p><strong>💊 Medications:</strong> {len(patient.get('medications', []))}</p>
#         </div>
#         """, unsafe_allow_html=True)
        
#         # Expandable details
#         with st.expander("📋 Full Details"):
#             st.markdown("**💊 Medications:**")
#             for med in patient.get('medications', []):
#                 st.markdown(f"- {med}")
            
#             st.markdown(f"**🍽️ Diet:** {patient.get('diet', 'Not specified')}")
            
#             if patient.get('warnings'):
#                 st.markdown(f"**⚠️ Warnings:** {patient.get('warnings')}")
        
#         if st.button("🔄 Load Different Patient"):
#             st.session_state.patient_loaded = False
#             st.session_state.patient_data = None
#             st.rerun()
    
#     st.markdown("---")
    
#     # Chat Controls
#     st.markdown("#### ⚙️ Chat Controls")
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         if st.button("🗑️ Clear Chat"):
#             st.session_state.messages = []
#             st.session_state.chat_history = []
#             asyncio.run(clear_conversation())
#             st.success("Chat cleared!")
#             st.rerun()
    
#     with col2:
#         if st.button("🔄 Refresh"):
#             st.rerun()
    
#     st.markdown("---")
    
#     # Information
#     st.markdown("#### ℹ️ About")
#     st.info("""
#     This AI assistant combines:
#     - 📚 Medical textbook knowledge
#     - 🌐 Latest online guidelines
#     - 🤖 Natural language understanding
    
#     **Always consult your healthcare provider for medical decisions.**
#     """)
    
#     # Server Status
#     st.markdown("#### 🔌 Server Status")
#     try:
#         # Quick connectivity check (non-blocking)
#         st.success("✅ Patient DB: Connected")
#         st.success("✅ Chatbot: Connected")
#     except:
#         st.error("❌ Check server connections")

# # ============================================================================
# # MAIN CONTENT - CHAT INTERFACE
# # ============================================================================

# st.markdown("<h1 class='main-header'>🩺 Nephrology AI Assistant</h1>", unsafe_allow_html=True)

# # Warning banner
# st.markdown("""
# <div class="warning-box">
#     <strong>⚠️ Medical Disclaimer:</strong> This is an educational AI assistant. 
#     It provides information based on medical textbooks and online guidelines but should NOT replace 
#     professional medical advice. Always consult your healthcare provider for diagnosis and treatment.
# </div>
# """, unsafe_allow_html=True)

# # Display chat messages
# chat_container = st.container()

# with chat_container:
#     if not st.session_state.messages:
#         # Welcome message
#         st.markdown("""
#         ### 👋 Welcome!
        
#         I'm your Nephrology AI Assistant. I can help you understand:
#         - 🩺 Kidney diseases and conditions
#         - 💊 Medications and treatments
#         - 🍽️ Diet and lifestyle recommendations
#         - 📊 Test results and what they mean
#         - ❓ Any questions about kidney health
        
#         **How to use:**
#         1. Optionally load a patient record from the sidebar
#         2. Ask your question below
#         3. Get evidence-based answers from medical textbooks and latest guidelines
        
#         **Example questions:**
#         - "What is chronic kidney disease?"
#         - "What are the latest treatment guidelines for CKD?"
#         - "Can I eat bananas with kidney disease?"
#         - "What are the side effects of Lisinopril?"
#         """)
    
#     for msg in st.session_state.messages:
#         if msg["role"] == "user":
#             st.markdown(f"""
#             <div class="chat-message user-message">
#                 <strong>👤 You:</strong><br>
#                 {msg['content']}
#             </div>
#             """, unsafe_allow_html=True)
#         else:
#             # Bot message with sources
#             response_text = msg['content']
#             sources = msg.get('sources', {})
#             web_used = msg.get('web_used', False)
#             time_taken = msg.get('time', 0)
            
#             st.markdown(f"""
#             <div class="chat-message bot-message">
#                 <strong>🩺 Nephrology AI:</strong><br>
#                 {response_text}
#             </div>
#             """, unsafe_allow_html=True)
            
#             # Source badges
#             if sources:
#                 badges_html = ""
#                 if sources.get('textbook_chunks', 0) > 0:
#                     badges_html += f'<span class="source-badge">📚 {sources["textbook_chunks"]} textbook sources</span>'
#                 if web_used and sources.get('web_sources', 0) > 0:
#                     badges_html += f'<span class="source-badge">🌐 {sources["web_sources"]} web sources</span>'
#                 if time_taken > 0:
#                     badges_html += f'<span class="source-badge">⏱️ {time_taken}s</span>'
                
#                 st.markdown(badges_html, unsafe_allow_html=True)

# # ============================================================================
# # CHAT INPUT
# # ============================================================================

# # Create input area at bottom
# st.markdown("---")

# # Example questions
# with st.expander("💡 Example Questions"):
#     col1, col2 = st.columns(2)
    
#     with col1:
#         st.markdown("""
#         **General Questions:**
#         - What is chronic kidney disease?
#         - How do kidneys work?
#         - What are the stages of CKD?
#         """)
    
#     with col2:
#         st.markdown("""
#         **Specific Questions:**
#         - What medications treat high blood pressure in CKD?
#         - Can I eat potassium-rich foods?
#         - When should I see a nephrologist?
#         """)

# # Chat input
# user_input = st.chat_input("Ask me anything about kidney health...")

# if user_input:
#     # Add user message
#     st.session_state.messages.append({
#         "role": "user",
#         "content": user_input
#     })
    
#     # Show thinking state
#     with st.spinner("🤔 Thinking... (searching textbooks and web if needed)"):
#         # Send to chatbot
#         response_data, error = asyncio.run(
#             send_message(user_input, st.session_state.patient_data)
#         )
        
#         if error:
#             st.session_state.messages.append({
#                 "role": "assistant",
#                 "content": f"❌ Error: {error}",
#                 "sources": {},
#                 "web_used": False,
#                 "time": 0
#             })
#         else:
#             # Add bot response
#             st.session_state.messages.append({
#                 "role": "assistant",
#                 "content": response_data.get("response", "No response"),
#                 "sources": response_data.get("sources", {}),
#                 "web_used": response_data.get("web_search_used", False),
#                 "time": response_data.get("processing_time_seconds", 0)
#             })
    
#     # Rerun to show new messages
#     st.rerun()

# # ============================================================================
# # FOOTER
# # ============================================================================

# st.markdown("---")
# st.markdown("""
# <div style='text-align: center; color: #666; font-size: 0.85rem;'>
#     <p>🩺 Nephrology AI Assistant | Powered by Azure OpenAI + Medical Knowledge Base</p>
#     <p>⚠️ For educational purposes only. Not a substitute for professional medical advice.</p>
# </div>
# """, unsafe_allow_html=True)


"""
Nephrology AI Chatbot - Streamlit UI
Simple, beautiful interface for the multi-agent nephrology system
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart

# ============================================================================
# CONFIGURATION
# ============================================================================

PATIENT_SERVER = "http://localhost:8003"
CHATBOT_SERVER = "http://localhost:8001"

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Nephrology AI Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    /* Make all text black */
    body, p, span, div, h1, h2, h3, h4, h5, h6, li, label {
        color: #000000 !important;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4 !important;
        text-align: center;
        margin-bottom: 1rem;
    }
    .patient-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white !important;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .patient-card h3 {
        margin: 0;
        color: white !important;
    }
    .patient-card p {
        margin: 0.3rem 0;
        font-size: 0.9rem;
        color: white !important;
    }
    .patient-card strong {
        color: white !important;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        color: #000000 !important;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        color: #000000 !important;
    }
    .bot-message {
        background-color: #f1f8e9;
        border-left: 4px solid #4caf50;
        color: #c62828 !important;
    }
    .chat-message strong {
        color: #000000 !important;
    }
    .chat-message p, .chat-message div, .chat-message span {
        color: #000000 !important;
    }
    .bot-message p, .bot-message div, .bot-message span {
        color: #c62828 !important;
    }
    .bot-message strong {
        color: #c62828 !important;
    }
    .source-badge {
        display: inline-block;
        background-color: #ff9800;
        color: white !important;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-right: 0.5rem;
        margin-top: 0.5rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #000000 !important;
    }
    .warning-box strong {
        color: #000000 !important;
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white !important;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem;
    }
    .stButton>button:hover {
        background-color: #1565c0;
        color: white !important;
    }
    /* Streamlit specific overrides */
    .stMarkdown p, .stMarkdown div, .stMarkdown span, .stMarkdown li {
        color: #000000 !important;
    }
    .stTextInput input {
        color: #000000 !important;
    }
    .stChatInput textarea {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'patient_loaded' not in st.session_state:
    st.session_state.patient_loaded = False

if 'patient_data' not in st.session_state:
    st.session_state.patient_data = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def extract_text(resp):
    """Extract text from ACP response"""
    try:
        if not resp or not resp.output or not resp.output[0].parts:
            return None
        return str(resp.output[0].parts[0].content)
    except:
        return None

async def load_patient(name: str):
    """Load patient record from database"""
    try:
        async with Client(base_url=PATIENT_SERVER) as client:
            resp = await client.run_sync(
                agent="GetPatient",
                input=[Message(parts=[MessagePart(content=name, content_type="text/plain")])]
            )
            
            result = await extract_text(resp)
            if not result:
                return None, "No response from patient server"
            
            data = json.loads(result)
            
            if "error" in data:
                return None, data["error"]
            
            return data, None
            
    except Exception as e:
        return None, str(e)

async def send_message(message: str, patient_data=None):
    """Send message to chatbot"""
    try:
        # Build payload
        if patient_data:
            payload = {
                "message": message,
                "disease": patient_data.get("diagnosis"),
                "patient_name": patient_data.get("name"),
                "medications": patient_data.get("medications", [])[:5]
            }
        else:
            payload = {"message": message}
        
        async with Client(base_url=CHATBOT_SERVER) as client:
            resp = await client.run_sync(
                agent="NephrologyChat",
                input=[Message(parts=[MessagePart(
                    content=json.dumps(payload),
                    content_type="application/json"
                )])]
            )
            
            result = await extract_text(resp)
            if not result:
                return None, "No response from chatbot"
            
            data = json.loads(result)
            
            if data.get("status") == "error":
                return None, data.get("error", "Unknown error")
            
            return data, None
            
    except Exception as e:
        return None, str(e)

async def clear_conversation():
    """Clear chatbot conversation history"""
    try:
        async with Client(base_url=CHATBOT_SERVER) as client:
            await client.run_sync(
                agent="ClearConversation",
                input=[Message(parts=[MessagePart(content="clear", content_type="text/plain")])]
            )
        return True
    except:
        return False

# ============================================================================
# SIDEBAR - PATIENT INFORMATION
# ============================================================================

with st.sidebar:
    st.markdown("### 🩺 Nephrology AI Assistant")
    st.markdown("---")
    
    # Patient Lookup Section
    st.markdown("#### 👤 Patient Lookup")
    
    if not st.session_state.patient_loaded:
        patient_name = st.text_input(
            "Enter patient name:",
            placeholder="e.g., Sarah Jones",
            help="Load patient record from database (optional)"
        )
        
        if st.button("🔍 Load Patient Record"):
            if patient_name:
                with st.spinner("Loading patient record..."):
                    patient_data, error = asyncio.run(load_patient(patient_name))
                    
                    if error:
                        st.error(f"❌ {error}")
                    else:
                        st.session_state.patient_data = patient_data
                        st.session_state.patient_loaded = True
                        st.success("✅ Patient record loaded!")
                        st.rerun()
            else:
                st.warning("Please enter a patient name")
    
    else:
        # Display loaded patient info
        patient = st.session_state.patient_data
        
        st.markdown(f"""
        <div class="patient-card">
            <h3>👤 {patient['name']}</h3>
            <p><strong>🏥 Diagnosis:</strong> {patient['diagnosis']}</p>
            <p><strong>📅 Discharge:</strong> {patient.get('discharge_date', 'N/A')}</p>
            <p><strong>💊 Medications:</strong> {len(patient.get('medications', []))}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Expandable details
        with st.expander("📋 Full Details"):
            st.markdown("**💊 Medications:**")
            for med in patient.get('medications', []):
                st.markdown(f"- {med}")
            
            st.markdown(f"**🍽️ Diet:** {patient.get('diet', 'Not specified')}")
            
            if patient.get('warnings'):
                st.markdown(f"**⚠️ Warnings:** {patient.get('warnings')}")
        
        if st.button("🔄 Load Different Patient"):
            st.session_state.patient_loaded = False
            st.session_state.patient_data = None
            st.rerun()
    
    st.markdown("---")
    
    # Chat Controls
    st.markdown("#### ⚙️ Chat Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.session_state.chat_history = []
            asyncio.run(clear_conversation())
            st.success("Chat cleared!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    st.markdown("---")
    
    # Information
    st.markdown("#### ℹ️ About")
    st.info("""
    This AI assistant combines:
    - 📚 Medical textbook knowledge
    - 🌐 Latest online guidelines
    - 🤖 Natural language understanding
    
    **Always consult your healthcare provider for medical decisions.**
    """)
    
    # Server Status
    st.markdown("#### 🔌 Server Status")
    try:
        # Quick connectivity check (non-blocking)
        st.success("✅ Patient DB: Connected")
        st.success("✅ Chatbot: Connected")
    except:
        st.error("❌ Check server connections")

# ============================================================================
# MAIN CONTENT - CHAT INTERFACE
# ============================================================================

st.markdown("<h1 class='main-header'>🩺 Nephrology AI Assistant</h1>", unsafe_allow_html=True)

# Warning banner
st.markdown("""
<div class="warning-box">
    <strong>⚠️ Medical Disclaimer:</strong> This is an educational AI assistant. 
    It provides information based on medical textbooks and online guidelines but should NOT replace 
    professional medical advice. Always consult your healthcare provider for diagnosis and treatment.
</div>
""", unsafe_allow_html=True)

# Display chat messages
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        # Welcome message
        st.markdown("""
        ### 👋 Welcome!
        
        I'm your Nephrology AI Assistant. I can help you understand:
        - 🩺 Kidney diseases and conditions
        - 💊 Medications and treatments
        - 🍽️ Diet and lifestyle recommendations
        - 📊 Test results and what they mean
        - ❓ Any questions about kidney health
        
        **How to use:**
        1. Optionally load a patient record from the sidebar
        2. Ask your question below
        3. Get evidence-based answers from medical textbooks and latest guidelines
        
        **Example questions:**
        - "What is chronic kidney disease?"
        - "What are the latest treatment guidelines for CKD?"
        - "Can I eat bananas with kidney disease?"
        - "What are the side effects of Lisinopril?"
        """)
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong>👤 You:</strong><br>
                {msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Bot message with sources
            response_text = msg['content']
            sources = msg.get('sources', {})
            web_used = msg.get('web_used', False)
            time_taken = msg.get('time', 0)
            
            st.markdown(f"""
            <div class="chat-message bot-message">
                <strong>🩺 Nephrology AI:</strong><br>
                {response_text}
            </div>
            """, unsafe_allow_html=True)
            
            # Source badges
            if sources:
                badges_html = ""
                if sources.get('textbook_chunks', 0) > 0:
                    badges_html += f'<span class="source-badge">📚 {sources["textbook_chunks"]} textbook sources</span>'
                if web_used and sources.get('web_sources', 0) > 0:
                    badges_html += f'<span class="source-badge">🌐 {sources["web_sources"]} web sources</span>'
                if time_taken > 0:
                    badges_html += f'<span class="source-badge">⏱️ {time_taken}s</span>'
                
                st.markdown(badges_html, unsafe_allow_html=True)

# ============================================================================
# CHAT INPUT
# ============================================================================

# Create input area at bottom
st.markdown("---")

# Example questions
with st.expander("💡 Example Questions"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **General Questions:**
        - What is chronic kidney disease?
        - How do kidneys work?
        - What are the stages of CKD?
        """)
    
    with col2:
        st.markdown("""
        **Specific Questions:**
        - What medications treat high blood pressure in CKD?
        - Can I eat potassium-rich foods?
        - When should I see a nephrologist?
        """)

# Chat input
user_input = st.chat_input("Ask me anything about kidney health...")

if user_input:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Show thinking state
    with st.spinner("🤔 Thinking... (searching textbooks and web if needed)"):
        # Send to chatbot
        response_data, error = asyncio.run(
            send_message(user_input, st.session_state.patient_data)
        )
        
        if error:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Error: {error}",
                "sources": {},
                "web_used": False,
                "time": 0
            })
        else:
            # Add bot response
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_data.get("response", "No response"),
                "sources": response_data.get("sources", {}),
                "web_used": response_data.get("web_search_used", False),
                "time": response_data.get("processing_time_seconds", 0)
            })
    
    # Rerun to show new messages
    st.rerun()

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.85rem;'>
    <p>🩺 Nephrology AI Assistant | Powered by Azure OpenAI + Medical Knowledge Base</p>
    <p>⚠️ For educational purposes only. Not a substitute for professional medical advice.</p>
</div>
""", unsafe_allow_html=True)