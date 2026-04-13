# Inventra Health — Hospital Supply Chain Intelligence

> AI-powered supply chain operations analyst for US hospitals.
> Current version: Runs entirely locally — Llama 3 via Ollama, no API keys, no cloud, no cost.

---

## What it does

Answers natural language questions about hospital supply chain data
and responds with structured, plain-text recommendations:

- Which items will stockout before the next delivery?
- Which vendors are running late and what should I do?
- What supplies do ICU patients consume most?
- Summarise this month's spending by category
- Which staff departments have the highest overtime?

Responses use exact item names, stock levels, vendor names, and 
dollar figures and gives action/suggestion/recommendations.

No Information Overload!

---

## Project structure

```
Hospital_Supply_Chain_Bot/
├── app.py                    ← Streamlit UI entry point
├── requirements.txt
├── .gitignore
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── config.py             ← Paths, Ollama settings, security, validation
│   ├── database.py           ← Read-only SQL queries, PII-safe
│   ├── retriever.py          ← FAISS loading + vector search
│   └── chain.py              ← Llama 3 prompt + markdown stripper
│
├── notebooks/
│   ├── 01_load_data.ipynb    ← CSVs → hospital.db
│   ├── 02_build_faiss.ipynb  ← PDFs → faiss_index/
│   ├── 03_rag_chain.ipynb    ← Test pipeline
│   └── 04_test_queries.ipynb ← End-to-end validation
│
├── hospital.db               ← SQLite (5 tables, 1,509 records)
├── faiss_index/              ← FAISS vector index
├── data/                     ← Source CSVs
└── docs/                     ← Knowledge base PDFs
```

---

## Security & governance

| Control | Implementation |
|---|---|
| No API keys | Fully local Ollama|
| Database | Read-only|
| PII protection | Patient_ID, Staff_ID stripped before LLM |
| SQL injection | Parameterised queries only |
| Prompt injection | 13 blocked patterns on every input |
| Rate limiting | 200 requests per session |
| Markdown stripping | LLM output cleaned before rendering |
| Response sanitisation | Prompt echo detection and removal |
| Logging | Structured INFO logs throughout |

---

## Run locally

```bash
# 1. Start Ollama
brew services start ollama
ollama pull llama3

# 2. Create environment
conda create -n hospital-bot python=3.10 -y
conda activate hospital-bot
pip install -r requirements.txt

# 3. Build data pipeline (if starting fresh)
# jupyter notebook → run 01_load_data.ipynb → 02_build_faiss.ipynb

# 4. Launch
cd ~/Hospital_Supply_Chain_Bot
streamlit run app.py
# Opens at http://localhost:8501
```

---

*Built by Somita Chaudhari · Data Scientist
