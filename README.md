# 🩺 Nephrology AI Assistant

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![Azure OpenAI](https://img.shields.io/badge/Azure-OpenAI-0089D6)](https://azure.microsoft.com/en-us/products/ai-services/openai-service)

An intelligent, multi-agent healthcare system that combines patient medical records, medical textbook knowledge (RAG), and real-time web search to provide accurate, personalized nephrology information to patients and healthcare providers.

</p><img width="2926" height="1588" alt="image" src="https://github.com/user-attachments/assets/01da60bf-79e3-4bbf-8d55-252e7a6e1ccd" />
---

## 🌟 Features

- 🏥 **Patient Record Integration** - Load and contextualize patient medical history
- 📚 **Medical Knowledge Base** - Semantic search across nephrology textbooks using Azure AI Search
- 🌐 **Real-Time Web Search** - Fetch latest treatment guidelines from trusted medical sources
- 💬 **Conversational AI** - Natural language interface powered by GPT-4
- 🎯 **Personalized Responses** - Tailored answers based on patient diagnosis and medications
- 📊 **Source Attribution** - Transparent citation of all medical information
- 🔒 **Safety First** - Prominent medical disclaimers and healthcare provider reminders
- 🎨 **User-Friendly UI** - Beautiful Streamlit interface with intuitive design

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Web UI                         │
│                        (st.py)                               │
└───────────────┬─────────────────────┬───────────────────────┘
                │                     │
                ▼                     ▼
    ┌───────────────────┐   ┌─────────────────────┐
    │  Patient Server   │   │  Chatbot Server     │
    │   (recept.py)     │   │   (research.py)     │
    │   Port: 8003      │   │   Port: 8001        │
    └─────────┬─────────┘   └──────────┬──────────┘
              │                        │
              ▼                        ▼
      ┌─────────────┐         ┌───────────────────┐
      │   SQLite    │         │  Azure AI Search  │
      │  Patient DB │         │  Vector Database  │
      └─────────────┘         └─────────┬─────────┘
                                        │
                              ┌─────────┴─────────┐
                              │                   │
                              ▼                   ▼
                      ┌──────────────┐    ┌─────────────┐
                      │ Azure OpenAI │    │  SerpAPI    │
                      │    GPT-4     │    │ Web Search  │
                      └──────────────┘    └─────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Azure OpenAI API access
- Azure AI Search instance
- SerpAPI key (optional, for web search)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nephrology-ai.git
   cd nephrology-ai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (optional)
   ```bash
   export SERPAPI_KEY="your_serpapi_key_here"
   ```

4. **Configure Azure credentials**
   
   Edit the configuration in `research.py`:
   ```python
   AZURE_OPENAI_ENDPOINT = "your_endpoint"
   AZURE_OPENAI_KEY = "your_key"
   AZURE_SEARCH_ENDPOINT = "your_search_endpoint"
   AZURE_SEARCH_KEY = "your_search_key"
   ```

### Running the System

Open **three terminal windows**:

**Terminal 1 - Patient Database Server:**
```bash
python recept.py
# Server starts on http://localhost:8003
```

**Terminal 2 - Nephrology Chatbot Server:**
```bash
python research.py
# Server starts on http://localhost:8001
```

**Terminal 3 - Streamlit UI:**
```bash
streamlit run st.py
# Opens browser at http://localhost:8501
```

---

## 📦 Dependencies

Create a `requirements.txt` file:

```txt
streamlit==1.28.0
acp-sdk==0.1.0
openai==1.3.0
azure-search-documents==11.4.0
azure-core==1.29.0
google-search-results==2.4.2
pydantic==2.4.0
```

Install with:
```bash
pip install -r requirements.txt
```

---

## 🎮 Usage

### 1. Load Patient Record (Optional)

In the sidebar, enter a patient name:
```
Sarah Jones
```

The system will load:
- Diagnosis
- Medications
- Diet restrictions
- Warnings

### 2. Ask Questions

**General Questions:**
- "What is chronic kidney disease?"
- "How do kidneys work?"
- "What are the stages of CKD?"

**Personalized Questions** (with patient loaded):
- "Tell me about my disease"
- "Can I eat bananas with my condition?"
- "What are the side effects of my medications?"

**Latest Guidelines:**
- "What are the latest treatment guidelines for CKD?"
- "Recent research on diabetic nephropathy"

### 3. View Sources

Each response includes:
- 📚 Number of textbook sources used
- 🌐 Number of web sources (if searched)
- ⏱️ Processing time

---

## 🏥 Database Schema

The system uses SQLite with the following tables:

**patients**
- patient_id, patient_name, primary_diagnosis, discharge_date, diet_id, warning_id

**medications**
- med_id, medication_name

**patient_medications**
- patient_id, med_id

**dietary_restrictions**
- diet_id, restriction_text

**warning_signs**
- warning_id, warning_text

**Sample Data:**
```sql
INSERT INTO patients VALUES (
  1, 
  'Sarah Jones', 
  'Congestive Heart Failure', 
  '2024-12-08', 
  1, 
  1
);
```

---

## 🔧 Configuration

### Azure OpenAI Settings

In `research.py`:
```python
class Config:
    AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
    AZURE_OPENAI_KEY = "your_key_here"
    API_VERSION = "2024-12-01-preview"
    GPT_MODEL = "gpt-4o-08-06"
    EMBEDDING_MODEL = "text-embedding-3-small"
```

### Azure AI Search Settings

```python
class Config:
    AZURE_SEARCH_ENDPOINT = "https://your-search.search.windows.net"
    AZURE_SEARCH_INDEX = "vectors-index2"
    AZURE_SEARCH_KEY = "your_search_key"
```

### SerpAPI (Web Search)

Get a free API key at [serpapi.com](https://serpapi.com) (100 searches/month free)

```python
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "your_key_here")
```

---

## 🧪 Testing

### Test Patient Server
```bash
curl -X POST http://localhost:8003/GetPatient \
  -H "Content-Type: application/json" \
  -d '{"content": "Sarah Jones"}'
```

### Test Chatbot Server
```bash
curl -X POST http://localhost:8001/NephrologyChat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is chronic kidney disease?"}'
```

### Run Interactive CLI (Alternative to Streamlit)
```bash
python router1.py
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Patient Lookup | ~0.5s |
| Textbook Search | 2-4s |
| With Web Search | 5-8s |
| Average Response Length | 400-800 tokens |
| Concurrent Users | Up to 10 (current) |

---

## 🛡️ Safety & Ethics

### Medical Disclaimer

⚠️ **This system is for educational purposes only.** It does NOT:
- Diagnose medical conditions
- Prescribe medications
- Replace professional medical advice
- Provide emergency medical services

**Always consult a healthcare provider for medical decisions.**

### Privacy

- Session-based storage (no persistent data)
- Patient data stays local
- No PHI transmitted to external APIs
- HIPAA considerations for production use

### Source Reliability

Web search is limited to:
- NIH.gov
- MayoClinic.org
- UpToDate.com
- NEJM.org
- KDIGO.org

---

## 🗂️ Project Structure

```
nephrology-ai/
│
├── recept.py              # Patient database server (Port 8003)
├── research.py            # Nephrology chatbot server (Port 8001)
├── st.py                  # Streamlit web interface
├── router1.py             # CLI interface (alternative)
│
├── hospital.db            # SQLite patient database
│
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── LICENSE               # MIT License
│
└── docs/
    ├── API.md            # API documentation
    ├── DEPLOYMENT.md     # Deployment guide
    └── CONTRIBUTING.md   # Contribution guidelines
```

---

## 🔮 Roadmap

### Version 1.1 (Q1 2026)
- [ ] Multi-language support (Spanish, Mandarin)
- [ ] Voice interface (speech-to-text)
- [ ] Mobile-responsive design improvements
- [ ] Enhanced caching with Redis

### Version 2.0 (Q2 2026)
- [ ] Lab result interpretation (upload images)
- [ ] Appointment scheduling integration
- [ ] Medication reminder system
- [ ] Progress tracking dashboard

### Version 3.0 (Q3 2026)
- [ ] EHR system integration (FHIR standard)
- [ ] Provider dashboard for reviewing patient interactions
- [ ] Clinical decision support features
- [ ] HIPAA-compliant production deployment

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Make your changes
4. Run tests
   ```bash
   pytest tests/
   ```
5. Commit your changes
   ```bash
   git commit -m "Add amazing feature"
   ```
6. Push to your fork
   ```bash
   git push origin feature/amazing-feature
   ```
7. Open a Pull Request

---

## 🐛 Troubleshooting

### Issue: "Port already in use"
```bash
# Kill process on port 8001
lsof -ti:8001 | xargs kill -9

# Kill process on port 8003
lsof -ti:8003 | xargs kill -9
```

### Issue: "Patient not found"
Check database path in `recept.py`:
```python
DB_PATH = "/path/to/your/hospital.db"
```

### Issue: "Web search not working"
1. Check SerpAPI key is set
2. Verify API quota (100 free searches/month)
3. System works without web search (textbook only)

### Issue: "Azure API errors"
1. Verify API keys are correct
2. Check Azure subscription is active
3. Ensure model deployment names match config

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Nephrology AI Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## 📧 Contact

**Project Lead**: Your Name  
**Email**: your.email@example.com  
**Project Link**: [https://github.com/yourusername/nephrology-ai](https://github.com/yourusername/nephrology-ai)

---

## 🙏 Acknowledgments

- Azure OpenAI for GPT-4 access
- Azure AI Search for vector database
- SerpAPI for web search capabilities
- Streamlit for the amazing UI framework
- The nephrology medical community for knowledge resources

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/nephrology-ai&type=Date)](https://star-history.com/#yourusername/nephrology-ai&Date)

---

## 📚 Citations

If you use this project in research, please cite:

```bibtex
@software{nephrology_ai_2025,
  title = {Nephrology AI Assistant: A Multi-Agent Healthcare System},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/nephrology-ai}
}
```

---

<p align="center">
  Made with ❤️ for better kidney health
</p>

<p align="center">
  <a href="#top">Back to Top ⬆️</a>

