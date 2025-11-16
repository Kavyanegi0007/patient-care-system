
import sqlite3
import json
from acp_sdk.server import Server

server = Server()
DB_PATH = "/Users/kavyanegi/Downloads/acp-2 /hospital.db"

def get_patient_full(name_query: str):
    if not name_query or not name_query.strip():
        return {"error": "No name provided"}
    
    pattern = '%' + '%'.join(name_query.strip().split()) + '%'
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""
        SELECT p.*, d.restriction_text as diet, w.warning_text as warnings
        FROM patients p
        LEFT JOIN dietary_restrictions d ON p.diet_id = d.diet_id
        LEFT JOIN warning_signs w ON p.warning_id = w.warning_id
        WHERE p.patient_name LIKE ?
        ORDER BY discharge_date DESC LIMIT 1
    """, (pattern,))
    row = cur.fetchone()
    
    if not row:
        conn.close()
        return {"error": f"Patient '{name_query}' not found"}
    
    meds = conn.execute("""
        SELECT m.medication_name FROM patient_medications pm
        JOIN medications m ON pm.med_id = m.med_id
        WHERE pm.patient_id = ?
    """, (row['patient_id'],)).fetchall()
    conn.close()
    
    return {
        "name": row['patient_name'],
        "diagnosis": row['primary_diagnosis'],
        "discharge_date": row['discharge_date'],
        "medications": [m['medication_name'] for m in meds],
        "diet": row['diet'],
        "warnings": row['warnings']
    }

# THE ONLY EXTRACTOR THAT WORKS WITH REAL ACP MESSAGES
def extract_text_from_acp(input_obj) -> str:
    """Handles: Message → parts → MessagePart → content"""
    text = ""
    
    if isinstance(input_obj, list):
        for msg in input_obj:
            if hasattr(msg, 'parts') and msg.parts:
                for part in msg.parts:
                    if hasattr(part, 'content') and part.content:
                        text += str(part.content) + " "
    
    elif hasattr(input_obj, 'parts') and input_obj.parts:
        for part in input_obj.parts:
            if hasattr(part, 'content') and part.content:
                text += str(part.content) + " "
    
    elif hasattr(input_obj, 'content'):
        text = str(input_obj.content)
    
    return text.strip()

@server.agent(name="GetPatient")
def patient_agent(input: any, context):
    print(f"Raw input type: {type(input)}")
    
    query = extract_text_from_acp(input)
    print(f"Extracted query: '{query}'")
    
    if not query:
        return json.dumps({"error": "Empty input received"}, indent=2)
    
    result = get_patient_full(query)
    return json.dumps(result, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    print("PATIENT SERVER v4 (REAL ACP MESSAGE HANDLER) → http://localhost:8003")
    server.run(port=8003)