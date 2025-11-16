# # router_fixed.py
# # Fixed router with proper error handling and agent calling
# import json
# import asyncio
# from acp_sdk.client import Client
# from acp_sdk.models import Message, MessagePart

# def query_rag_agent(disease: str) -> dict:
#     """
#     Query the NephrologyAssistant agent (on port 8001) using ACP SDK.
    
#     Args:
#         disease (str): Disease name (e.g., "Congestive Heart Failure")
    
#     Returns:
#         dict: Parsed JSON response with 'answer', 'sources', 'confidence', etc.
#               On error: includes 'error' key.
#     """
#     print(f"\nSending '{disease}' to NephrologyAssistant...")

#     async def _run_agent():
#         try:
#             # Connect to local ACP server
#             async with Client(base_url="http://localhost:8001") as client:
#                 # Call the agent with a proper Message
#                 run = await client.run_sync(
#                     agent="NephrologyAssistant",  # Must match @server.agent(name=...)
#                     input=[
#                         Message(
#                             parts=[
#                                 MessagePart(
#                                     content=disease,
#                                     content_type="text/plain"
#                                 )
#                             ]
#                         )
#                     ]
#                 )

#                 # Extract output
#                 if not run.output or not run.output[0].parts:
#                     raise ValueError("Empty response from agent")

#                 raw_output = run.output[0].parts[0].content.strip()
#                 print("Raw response received")

#                 # Parse JSON
#                 try:
#                     result = json.loads(raw_output)
#                     print("JSON parsed successfully")
#                     return result
#                 except json.JSONDecodeError as e:
#                     raise ValueError(f"Invalid JSON from agent: {e}\nRaw: {raw_output[:200]}...")

#         except ConnectionError:
#             error_msg = "Cannot connect to server. Is research2.py running on port 8001?"
#             print(f"Connection failed: {error_msg}")
#             return {"error": error_msg, "answer": "Server unreachable"}
#         except Exception as e:
#             error_msg = f"Agent call failed: {str(e)}"
#             print(f"{error_msg}")
#             return {"error": error_msg, "answer": "Agent execution error"}

#     # Run async function in sync context
#     return asyncio.run(_run_agent())
# def generate_clinical_report(patient_data: dict) -> str:
#     """Generate a formatted clinical report"""
    
#     # Extract patient info
#     name = patient_data.get("name", "Unknown Patient")
#     diagnosis = patient_data.get("diagnosis", "Not specified")
#     medications = patient_data.get("medications", "None listed")
#     diet = patient_data.get("diet", "Standard")
    
#     # Query textbook for diagnosis info
#     rag_result = query_rag_agent(diagnosis)
    
#     # Extract textbook info
#     textbook_info = rag_result.get("answer", "Textbook unavailable")
#     sources_count = len(rag_result.get("sources", []))
#     confidence = rag_result.get("confidence", "Unknown")
    
#     # Check for errors
#     if "error" in rag_result:
#         error_msg = rag_result["error"]
#         textbook_info = f"⚠️ Textbook lookup encountered an error: {error_msg}"
    
#     # Format the report
#     report = f"""
# {'='*80}
# CLINICAL AI REPORT: {name}
# {'='*80}
# Diagnosis: {diagnosis}
# Treatment: {medications}
# Diet: {diet}

# TEXTBOOK KNOWLEDGE:
# {textbook_info}

# Sources: {sources_count} textbook chunks
# Confidence: {confidence}
# {'='*80}
# """
    
#     return report


# def main():
#     """Main function to demonstrate the router"""
#     print("="*80)
#     print("MULTI-AGENT HOSPITAL AI STARTED")
#     print("="*80)
    
#     # Example patient data
#     patient = {
#         "name": "Sarah Jones",
#         "diagnosis": "Congestive Heart Failure",
#         "medications": "Insulin glargine 10 units at bedtime, Amlodipine 5mg daily, Albuterol inhaler as needed",
#         "diet": "Renal diet"
#     }
    
#     print(f"Querying patient: {patient['name']}")
#     print(f"Diagnosis: {patient['diagnosis']}")
#     print(f"Meds: {patient['medications']}")
    
#     # Generate report
#     report = generate_clinical_report(patient)
#     print(report)
    
#     # Test with another condition
#     print("\n" + "="*80)
#     print("TESTING ANOTHER QUERY")
#     print("="*80)
    
#     patient2 = {
#         "name": "John Doe",
#         "diagnosis": "Acute Kidney Injury",
#         "medications": "IV fluids, monitoring",
#         "diet": "Low sodium"
#     }
    
#     print(f"Querying patient: {patient2['name']}")
#     print(f"Diagnosis: {patient2['diagnosis']}")
    
#     report2 = generate_clinical_report(patient2)
#     print(report2)


# if __name__ == "__main__":
#     import sys
    
#     if len(sys.argv) > 1:
#         # Test with command-line disease
#         disease = " ".join(sys.argv[1:])
#         print(f"Testing with disease: {disease}")
#         result = query_rag_agent(disease)
#         print("\n" + "="*80)
#         print("RESULT")
#         print("="*80)
#         print(json.dumps(result, indent=2))
#     else:
#         main()



"""
Interactive Patient Chat Router
Connects GetPatient (8003) → NephrologyChat (8001)
Provides a natural chatbot interface for patients
"""

import asyncio
import json
import sys
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart

# === CONFIG ===
PATIENT_SERVER = "http://localhost:8003"   # recept.py
CHATBOT_SERVER = "http://localhost:8001"   # Enhanced research.py

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def extract_text(resp):
    """Safely extract text from any ACP response"""
    try:
        if not resp or not resp.output or not resp.output[0].parts:
            return None
        return str(resp.output[0].parts[0].content)
    except Exception as e:
        print(f"[DEBUG] Response extraction failed: {e}")
        return None

def print_banner(text: str, char: str = "="):
    """Print formatted banner"""
    print(f"\n{char * 80}")
    print(text)
    print(f"{char * 80}\n")

# ============================================================================
# CHAT SESSION CLASS
# ============================================================================

class PatientChatSession:
    """Manages patient information and chat state"""
    
    def __init__(self):
        self.patient = None
        self.diagnosis = None
        self.medications = []
        self.diet = None
        self.warnings = None
        self.patient_loaded = False

    async def lookup_patient(self, client: Client, name: str):
        """Load patient record from database"""
        print(f"\n🔍 Looking up patient: {name}...")
        
        try:
            resp = await client.run_sync(
                agent="GetPatient",
                input=[Message(parts=[MessagePart(content=name, content_type="text/plain")])]
            )
            
            result = await extract_text(resp)
            if not result:
                print("❌ No response from patient server")
                return False
            
            data = json.loads(result)
            
            if "error" in data:
                print(f"❌ {data['error']}")
                return False
            
            # Store patient data
            self.patient = data
            self.diagnosis = data.get("diagnosis", "Unknown")
            self.medications = data.get("medications", [])
            self.diet = data.get("diet", "Not specified")
            self.warnings = data.get("warnings", "None")
            self.patient_loaded = True
            
            # Display patient summary
            print_banner("✅ PATIENT RECORD LOADED", "=")
            print(f"👤 Name: {data['name']}")
            print(f"🏥 Diagnosis: {self.diagnosis}")
            print(f"💊 Medications: {', '.join(self.medications[:5])}")
            if len(self.medications) > 5:
                print(f"   ... and {len(self.medications) - 5} more")
            print(f"🍽️  Diet: {self.diet}")
            if self.warnings and self.warnings != "None":
                print(f"⚠️  Warnings: {self.warnings}")
            print("="*80)
            
            return True
            
        except Exception as e:
            print(f"❌ Patient server error: {e}")
            return False

    async def chat(self, client: Client, user_message: str):
        """Send message to nephrology chatbot"""
        
        # Build message payload
        if self.patient_loaded:
            # Include patient context for personalized responses
            payload = {
                "message": user_message,
                "disease": self.diagnosis,
                "patient_name": self.patient.get("name"),
                "medications": self.medications[:5]  # Top 5 meds for context
            }
        else:
            # No patient context, general query
            payload = {
                "message": user_message
            }
        
        try:
            # Show thinking indicator
            print("\n🤔 Nephrology AI is thinking...", end="", flush=True)
            
            # Call chatbot
            resp = await client.run_sync(
                agent="NephrologyChat",
                input=[Message(parts=[MessagePart(
                    content=json.dumps(payload), 
                    content_type="application/json"
                )])]
            )
            
            result = await extract_text(resp)
            
            # Clear thinking indicator
            print("\r" + " " * 40 + "\r", end="")
            
            if not result:
                return "❌ Sorry, I didn't get a response from the medical AI."
            
            try:
                data = json.loads(result)
                
                if data.get("status") == "error":
                    return f"❌ Error: {data.get('error', 'Unknown error')}"
                
                response_text = data.get("response", "No response generated.")
                
                # Add metadata footer
                sources = data.get("sources", {})
                web_used = data.get("web_search_used", False)
                time_taken = data.get("processing_time_seconds", 0)
                
                footer = f"\n\n{'─' * 80}\n"
                footer += f"📊 Sources: {sources.get('textbook_chunks', 0)} textbook chunks"
                
                if web_used:
                    footer += f" + {sources.get('web_sources', 0)} web sources"
                
                footer += f" | ⏱️ {time_taken}s"
                
                return response_text + footer
                
            except json.JSONDecodeError:
                # Fallback: raw text response
                return result[:3000]
                
        except Exception as e:
            print("\r" + " " * 40 + "\r", end="")
            return f"❌ Chatbot temporarily unavailable: {e}"

    def get_summary(self) -> str:
        """Get patient summary for display"""
        if not self.patient_loaded:
            return "No patient record loaded"
        
        return f"{self.patient['name']} | {self.diagnosis} | {len(self.medications)} medications"

# ============================================================================
# MAIN INTERACTIVE LOOP
# ============================================================================

async def main():
    print_banner("🩺 NEPHROLOGY AI ASSISTANT", "=")
    print("Welcome! This AI assistant can help you understand kidney conditions,")
    print("medications, diet, and answer questions about your health.")
    print("\nFeatures:")
    print("  • Searches medical textbooks and latest online guidelines")
    print("  • Provides clear, patient-friendly explanations")
    print("  • Maintains conversation context")
    print("\n⚠️  IMPORTANT: This is educational only. Always consult your doctor!")
    print("="*80)

    session = PatientChatSession()

    async with Client(base_url=PATIENT_SERVER) as patient_client, \
               Client(base_url=CHATBOT_SERVER) as chatbot_client:

        # ===== STEP 1: Patient Lookup (Optional) =====
        print("\n" + "─"*80)
        print("STEP 1: Patient Record Lookup (Optional)")
        print("─"*80)
        name = input("\nEnter your name to load your medical record (or press Enter to skip): ").strip()
        
        if name:
            await session.lookup_patient(patient_client, name)
        else:
            print("\n✓ Continuing without patient record - I can still answer general questions!")

        # ===== STEP 2: Interactive Chat =====
        print_banner("💬 CHAT SESSION STARTED", "=")
        print("Ask me anything about kidney health, your condition, medications, diet, etc.")
        print("\nCommands:")
        print("  • Type your question naturally")
        print("  • 'patient' - Show loaded patient info")
        print("  • 'clear' - Start fresh conversation")
        print("  • 'exit' or 'bye' - End session")
        print("="*80)

        while True:
            try:
                # Show prompt with patient context if available
                if session.patient_loaded:
                    prompt = f"\nYou [{session.get_summary()}]: "
                else:
                    prompt = "\nYou: "
                
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ["exit", "bye", "quit", "goodbye"]:
                    print("\n" + "="*80)
                    print("👋 Take care! Remember to always consult your healthcare provider.")
                    print("="*80)
                    break
                
                if user_input.lower() == "patient":
                    if session.patient_loaded:
                        print_banner("PATIENT INFORMATION", "─")
                        print(f"Name: {session.patient['name']}")
                        print(f"Diagnosis: {session.diagnosis}")
                        print(f"Discharge Date: {session.patient.get('discharge_date', 'Unknown')}")
                        print(f"\nMedications ({len(session.medications)}):")
                        for med in session.medications:
                            print(f"  • {med}")
                        print(f"\nDiet: {session.diet}")
                        print(f"Warnings: {session.warnings}")
                        print("─"*80)
                    else:
                        print("\n❌ No patient record loaded")
                    continue
                
                if user_input.lower() == "clear":
                    # Clear conversation on chatbot side
                    try:
                        await chatbot_client.run_sync(
                            agent="ClearConversation",
                            input=[Message(parts=[MessagePart(content="clear", content_type="text/plain")])]
                        )
                        print("\n✓ Conversation history cleared")
                    except:
                        print("\n✓ Starting fresh conversation")
                    continue
                
                # Send to chatbot
                response = await session.chat(chatbot_client, user_input)
                
                # Display response
                print(f"\n🩺 Nephrology AI:\n{response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again or type 'exit' to quit.")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Session ended")
        sys.exit(0)