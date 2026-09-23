# AI Mechanical Safety Compliance Advisor
## AI-Powered Industrial Machine Safety Compliance Prototype
### College Project | Educational Use Only

---

## 🛡️ Project Title
**AI Mechanical Safety Compliance Advisor**

## 📋 Problem Statement
Problem Statement No. 35 — AI Mechanical Safety Compliance Advisor.

Industrial machines must comply with strict safety regulations and operational standards. Monitoring compliance across large industrial facilities can be difficult, and violations may lead to safety hazards, accidents, and regulatory penalties. This project builds an AI-powered prototype that analyzes machine operations and safety regulations to detect compliance risks.

## 🎯 Objective
Build an AI-powered Mechanical Safety Compliance Advisor that:
- Analyzes machine operations and safety regulations
- Detects compliance risks using retrieved safety information
- Generates corrective recommendations
- Displays results in a professional dashboard

---

## ✨ Features
- ✅ Multi-Agent AI System (4 specialized agents)
- ✅ RAG (Retrieval-Augmented Generation) for safety document retrieval
- ✅ Risk Detection with risk level classification
- ✅ Compliance Verification against retrieved requirements
- ✅ Safety Recommendations with priority levels
- ✅ Streamlit Dashboard with visual indicators
- ✅ Safety Check History with JSON storage
- ✅ Demo machine data (4 pre-loaded scenarios)
- ✅ Knowledge Base management with document upload
- ✅ Fallback rule-based analysis (works without LLM)
- ✅ Downloadable safety reports (TXT + JSON)

---

## 🏗️ Architecture

### System Workflow
```
USER
  ↓
STREAMLIT MACHINE INPUT
  ↓
SAFETY DATA AGENT  ←── RAG KNOWLEDGE RETRIEVAL (TF-IDF Vector Store)
  ↓
RISK DETECTION AGENT
  ↓
COMPLIANCE AGENT
  ↓
SAFETY RECOMMENDATION AGENT
  ↓
FINAL SAFETY REPORT
  ↓
STREAMLIT DASHBOARD
```

### Multi-Agent System
| Agent | File | Responsibility |
|---|---|---|
| Safety Data Agent | `agents/safety_data_agent.py` | Retrieves relevant safety info via RAG |
| Risk Detection Agent | `agents/risk_detection_agent.py` | Identifies hazardous conditions |
| Compliance Agent | `agents/compliance_agent.py` | Verifies parameter compliance |
| Safety Recommendation Agent | `agents/recommendation_agent.py` | Generates corrective actions |

### RAG System
1. Documents loaded from `data/knowledge_base/`
2. Text split into ~500 character chunks with overlap
3. TF-IDF vectors computed via scikit-learn
4. Cosine similarity search for relevant chunks
5. Top-K chunks passed to LLM agents as context
6. Source documents preserved in output

---

## 🔧 Technology Stack
| Technology | Purpose |
|---|---|
| Python 3.9+ | Core programming language |
| Streamlit | Web UI framework |
| Groq API | LLM inference API |
| openai/gpt-oss-120b | LLM model (via Groq) |
| scikit-learn | TF-IDF vectorization for RAG |
| numpy | Numerical operations |
| python-dotenv | Environment variable management |
| PyPDF2 | PDF document support (optional) |

---

## 📁 Project Structure
```
mechanical-safety-advisor/
│
├── app.py                          # Streamlit main application
│
├── agents/
│   ├── __init__.py
│   ├── safety_data_agent.py        # Agent 1: RAG retrieval + context
│   ├── risk_detection_agent.py     # Agent 2: Risk identification
│   ├── compliance_agent.py         # Agent 3: Compliance verification
│   └── recommendation_agent.py    # Agent 4: Corrective recommendations
│
├── rag/
│   ├── __init__.py
│   ├── document_loader.py          # Loads + chunks .txt/.pdf documents
│   ├── vector_store.py             # TF-IDF vector store + search
│   └── retriever.py                # RAG pipeline orchestrator
│
├── llm/
│   ├── __init__.py
│   └── groq_client.py              # Groq API client wrapper
│
├── prompts/
│   ├── safety_data_prompt.txt      # System prompt for Safety Data Agent
│   ├── risk_detection_prompt.txt   # System prompt for Risk Detection Agent
│   ├── compliance_prompt.txt       # System prompt for Compliance Agent
│   └── recommendation_prompt.txt  # System prompt for Recommendation Agent
│
├── data/
│   ├── demo_machines.csv           # 4 demo machine scenarios
│   └── knowledge_base/
│       ├── safety_guidelines.txt
│       ├── machine_operation.txt
│       ├── emergency_procedures.txt
│       ├── maintenance_safety.txt
│       └── safety_inspection_guidelines.txt
│
├── storage/
│   ├── history.json                # Safety check history (auto-created)
│   └── rag_index/                  # Vector index cache (auto-created)
│
├── utils/
│   └── helpers.py                  # History, formatting, UI helpers
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd mechanical-safety-advisor
```

### 2. Create a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

### 1. Copy the example file
```bash
cp .env.example .env
```

### 2. Edit `.env` and add your Groq API key
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

> Get your free API key at: https://console.groq.com/

---

## ▶️ How to Run

```bash
streamlit run app.py
```

Then open your browser at: `http://localhost:8501`

---

## 🎮 Demo Instructions

### Quick 5-Step Demo

**Step 1:** Open the app → `streamlit run app.py`

**Step 2:** Navigate to **🔍 Safety Check** in the sidebar

**Step 3:** In the **Load Demo Machine** dropdown, select:
- `[Machine with Multiple Risks] M003 — Hydraulic Pump`

**Step 4:** Click **CHECK SAFETY**

**Step 5:** Watch the 4 agents execute in sequence:
- Safety Data Agent retrieves relevant knowledge from RAG
- Risk Detection Agent identifies HIGH risks
- Compliance Agent finds NON-COMPLIANT parameters
- Recommendation Agent generates IMMEDIATE action items

**Step 6:** Navigate to **📊 Safety Report** to see the full structured report

**Step 7:** Navigate to **📜 History** to see the check has been saved

---

## 🧪 Test Scenarios

### TEST 1: Normal Machine (M001 — Industrial Press)
- Expected: LOW risk, COMPLIANT
- All parameters within safe ranges

### TEST 2: Single Safety Risk (M002 — CNC Milling Machine)
- Expected: HIGH risk, NON-COMPLIANT
- Safety guard OPEN

### TEST 3: Multiple Risks (M003 — Hydraulic Pump)
- Expected: HIGH risk, NON-COMPLIANT
- Temperature 115°C + Pressure 220 PSI + RPM 4800 + Guard OPEN + E-Stop NON-FUNCTIONAL

### TEST 4: Missing Data (M004 — Industrial Conveyor)
- Expected: INSUFFICIENT EVIDENCE
- Most parameters not provided

### TEST 5: Custom Machine
- Enter parameters not covered by the knowledge base
- Agent should return INSUFFICIENT EVIDENCE, not hallucinate

---

## 📊 Example Input
```
Machine ID:          M003
Machine Type:        Hydraulic Pump
Temperature:         115°C
Pressure:            220 PSI
RPM:                 4800
Safety Guard:        OPEN
Emergency Stop:      NON-FUNCTIONAL
Operating Condition: FAULT
Notes:               Multiple unsafe conditions detected
```

## 📋 Example Output
```
Overall Risk Level:   HIGH
Compliance Status:    NON-COMPLIANT
Action Required:      STOP MACHINE

Detected Risks:
  [HIGH] safety_guard — Safety guard is open during operation
  [HIGH] emergency_stop — Emergency stop is non-functional
  [HIGH] temperature — Temperature exceeds HIGH risk threshold (115°C > 100°C)
  [HIGH] pressure — Pressure exceeds HIGH risk threshold (220 PSI > 200 PSI)
  [HIGH] rpm — RPM exceeds HIGH risk threshold (4800 > 4500)

Recommendations:
  1. [IMMEDIATE] Stop machine. Close and verify safety guard.
  2. [IMMEDIATE] Isolate power. Repair emergency stop.
  3. [IMMEDIATE] Reduce load, check cooling system.
```

---

## ⚠️ Limitations
1. **Prototype only** — not for production industrial use
2. **Demo knowledge base** — documents are not official standards
3. **No physical connectivity** — does not connect to real machines
4. **Fallback mode** — works without LLM but with rule-based analysis only
5. **Local storage** — history stored in JSON; no database

---

## 🔒 Safety Disclaimer
> **This application is a prototype for educational and demonstration purposes only.
> It does not replace qualified safety professionals, official regulatory standards,
> formal safety inspections, or legal compliance procedures.
> Do not use this system to make real safety decisions about industrial machinery.**

---

## 👨‍💻 Development Environment
Built using **IBM Bob** in VS Code.
