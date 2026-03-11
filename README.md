# 📊 AI Telecom Warehouse Analyst

A production-grade **Natural Language to SQL engine** built for Indian telecom data. Ask business questions in plain English — get SQL, results, and a plain-English answer back in seconds.

> *"Which operators have above-average call drop rates in states where their market share exceeds 15%?"*
> → Automatically generates SQL, executes it, and explains the result.

---

## 🎥 Demo

<p align="center">
  <img src="https://github.com/user-attachments/assets/c5634e4b-fcd3-4ad9-bfea-d278668f4d98"  width="45%" />
  <img src="https://github.com/user-attachments/assets/cf2025e2-3e40-45c8-b312-a8e9a0d23329" width="45%" />
</p>

---

## 🏗️ Architecture

```
User Question (Natural Language)
        │
        ▼
┌───────────────────┐
│  Vector Search    │  ← ChromaDB finds similar past questions
│  (Few-Shot RAG)   │    and injects them as examples into prompt
└───────────────────┘
        │
        ▼
┌───────────────────┐
│   Schema Context  │  ← Table descriptions + column meanings
│                   │    passed to LLM for accurate SQL
└───────────────────┘
        │
        ▼
┌───────────────────────────────┐
│   LLM Fallback Chain          │
│   Groq (llama-3.3-70b)        │  ← Primary
│      ↓ on rate limit/failure  │
│   Gemini (gemini-2.5-flash)   │  ← Fallback
└───────────────────────────────┘
        │
        ▼
┌───────────────────┐
│  SQL Validation   │  ← Auto-corrects failed queries
│  + Retry Loop     │    up to 2 times with error feedback
└───────────────────┘
        │
        ▼
┌───────────────────┐
│    DuckDB         │  ← Executes validated SQL
│    Warehouse      │    on 180K+ rows of telecom data
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Answer + Chart   │  ← Plain English answer + auto-visualization
│  + Feedback Loop  │    👍 saves to ChromaDB as future example
└───────────────────┘
```

---

## ✨ Features

### Core NL2SQL Pipeline
- **Natural language to SQL** — type questions in plain English, get accurate DuckDB SQL
- **Schema-aware prompting** — every column has a plain English description passed to the LLM, eliminating hallucinated column names

### RAG-Powered Few-Shot Learning
- **ChromaDB vector store** — stores successful `(question → SQL)` pairs as embeddings
- **Semantic retrieval** — finds the 3 most similar past queries and injects them as examples
- **Improves over time** — every 👍 feedback adds a new few-shot example to the store

### Reliability
- **LLM fallback chain** — Groq → Gemini, automatically falls through on rate limits or failures
- **Auto-correcting SQL** — if DuckDB throws an error, feeds it back to the LLM for self-correction (up to 2 retries)
- **SELECT-only guard** — blocks any INSERT / UPDATE / DROP statements

### User Experience
- **Multi-turn conversation** — follow-up questions like *"now filter that by Maharashtra"* resolve correctly
- **Auto-visualization** — results are visible in tabular format which can be downloaded in csv format
- **Schema preview** — explore table schemas directly in the sidebar
- **Feedback buttons** — 👍/👎 after every answer; 👍 indexes to ChromaDB as a training example

### Data
- **180K+ rows** across 5 realistic Indian telecom tables
- **24 months** of historical data (Jan 2023 – Dec 2024)
- **City-level granularity** — 10 cities per state, 22 states

---

## 🗄️ Dataset

All data is synthetically generated to mirror real Indian telecom operations.

| Table | Rows | Description |
|---|---|---|
| `trai_subscribers` | 26,400 | Monthly wireless/wireline subscriber counts by city, state, operator |
| `operator_revenue` | 26,400 | Monthly revenue (₹ Crore) and ARPU by city, state, operator |
| `tower_qos` | 26,400 | Network quality metrics — call drop rate, data speed, uptime, latency |
| `service_provider_billing` | 52,800 | Vendor billing — base payout, penalties, rewards, performance scores |
| `telco_churn` | 50,000 | Customer-level churn dataset with plan type, tenure, complaints |

---

## 💬 Example Queries

```
# Single table
"Top 10 cities by Jio wireless subscribers in Maharashtra"
"Which vendors had more than 5 SLA breaches in December 2024?"
"Show average ARPU by operator for the last 6 months"

# Multi-table JOINs
"Which operators have above-average call drop rates in states where their market share exceeds 15%?"
"Do high-churn customers cluster in states with below-average data speeds?"
"Compare net vendor payout vs performance score for top 10 vendors in Karnataka"

# Time-series
"Show Jio vs Airtel revenue trend over 24 months"
"Which states had negative subscriber growth for Vi in Q3 2024?"

# Follow-ups (multi-turn)
"Top 5 states by churn rate"
→ "Now filter those by postpaid customers only"
→ "Which operator has the highest churn in those states?"
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM (Primary)** | Groq — `llama-3.3-70b-versatile` |
| **LLM (Fallback)** | Google Gemini — `gemini-2.5-flash` |
| **Vector DB** | ChromaDB (persistent, local) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Data Warehouse** | DuckDB |
| **Frontend** | Streamlit |
| **Data Generation** | Python, NumPy, Pandas |

---

## 📁 Project Structure

```
nl2sql-telecom-analyst/
│
├── data/
│   ├── raw/                        # CSV files (generated by generate_data.py)
│   │   ├── trai_subscribers.csv
│   │   ├── operator_revenue.csv
│   │   ├── tower_qos.csv
│   │   ├── service_provider_billing.csv
│   │   └── telco_churn.csv
│   ├── warehouse.duckdb            # DuckDB database (auto-created)
│   ├── vector_store/               # ChromaDB persistent store (auto-created)
│   ├── duckdb_manager.py           # DuckDB connection + query execution
│   └── schema_definitions.py       # Table schemas + column descriptions + JOIN hints
│
├── scripts/
│   ├── llm_client.py               # LLM fallback chain + SQL generation + retry logic
│   ├── vector_client.py            # ChromaDB wrapper + embedding + retrieval
│   └── generate_data.py            # Synthetic data generator
│
├── app/
│   ├── streamlit_app.py            # Main Streamlit app
│   ├── left_sidebar.py             # Table selector + schema preview
│   ├── right_sidebar.py            # Auto chart panel
│   └── feedback.py                 # 👍/👎 feedback buttons
│
├── init_db.py                      # One-time DB setup: create tables + load CSVs
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/your-username/nl2sql-telecom-analyst.git
cd nl2sql-telecom-analyst
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up API keys
```bash
cp .env.example .env
# Edit .env and add your keys
```

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

Get free API keys:
- Groq: [console.groq.com](https://console.groq.com) — free tier, very fast
- Gemini: [aistudio.google.com](https://aistudio.google.com) — free tier

### 4. Generate data and initialise the database
```bash
# Generate all 5 CSV files (~180K rows total)
python scripts/generate_data.py

# Create DuckDB tables and load the CSVs
python init_db.py
```

### 5. Run the app
```bash
streamlit run app/streamlit_app.py
```

Open `http://localhost:8501` in your browser.

---

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `MONTHS` | `24` | Months of historical data to generate |
| `VENDORS_PER_STATE` | `100` | Vendors per state in billing table |
| `n_customers` | `50,000` | Rows in churn table |
| `START_MONTH` | `2023-01` | First month of generated data |

Edit the `CONFIG` section at the top of `scripts/generate_data.py` to resize the dataset.

---

## 📦 Requirements

```txt
streamlit
duckdb
groq
google-generativeai
chromadb
sentence-transformers
pandas
numpy
python-dotenv
python-dateutil
```

Thanks for reading 😁😁😁 !!!
