# 🏥 Inventra Health — Hospital Supply Chain Intelligence

> AI-powered supply chain operations analyst for US hospitals with enterprise grade security and HIPAA aligned data governance..
> Current version: Runs entirely locally - Llama 3 via Ollama, no API keys, no cloud, no cost.

---

## What it does

Inventra Health is a conversational supply chain analyst built for hospital operations teams.
Ask it anything in plain English, it queries live data, retrieves relevant domain knowledge,
and responds with structured, specific, actionable recommendations.

No dashboards. No filters. No clutter.
Just ask—and get the answer you actually need.

No noise. No overload. Just decisions.

---

### Example questions

These are starting points. You are not limited to these, ask anything related to hospital supply chain operations.

**Inventory & Stockouts**
- Which items will run out before their vendor can restock them?
- How much capital is tied up in overstocked items right now?
- Which items are both critically low and supplied by a delayed vendor?

**Vendor Performance**
- Which vendors are causing the most risk to patient care?
- If EquipMed Co. delays again, which items will hit zero stock first?
- Which vendor has the worst track record and what should I do about it?

**Financials & Spend**
- Summarise this month's spending by category with totals
- Where are we overspending compared to what we actually use?
- Which expense category has the highest average transaction cost?

**Patient Demand**
- What supplies do ICU patients consume most?
- Which diagnosis type puts the most pressure on our inventory?
- What equipment is most demanded and how does our stock compare?

**Staff & Workload**
- Which staff departments have the highest overtime right now?
- Are we understaffed relative to patient assignments in the ER?
- Which staff type is working the most beyond their scheduled hours?

**Cross-dataset (most powerful)**
- Which items used heavily by ICU patients are also in critical stockout?
- What is our single biggest operational risk right now?
- Show me everything that needs immediate action today across all departments.

---

### How responses are structured

Every response follows a clean, consistent format — no walls of text, no generic output.

```
Summary: <one line — the direct answer>

Top issues / Key findings / Vendor issues / Opportunities:
1. <item or finding> — <exact values: stock, days, cost, vendor, delay>
2. ...
3. ...

Actions:
1. <specific recommendation with names and numbers>
2. ...
3. ...
```

Responses use exact item names, stock levels, vendor names, dollar figures, and day counts
pulled directly from live data. No invented numbers. No vague advice.

---

### What it does NOT do

- Invent data — if something is not in the database, it says so
- Answer questions unrelated to hospital supply chain
- Give clinical or medical advice

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

Note: If Ollama times out:
In terminal, use:
OLLAMA_KEEP_ALIVE=30m ollama serve

```

---
## CITATIONS
*Data* :

Van Patangan. (n.d.). Hospital Supply Chain: Saving Lives (and Money) One Bandage at a Time. Kaggle.
Retrieved from Kaggle Dataset Platform.

*Docs*:
1. Management Sciences for Health. (2012). Medical stores management (Chapter 44). In MDS-3: Managing access to medicines and health technologies. Management Sciences for Health. https://msh.org/wp-content/uploads/2013/04/mds3-ch44-medicalstores-mar2012.pdf

2. Management Sciences for Health. (2012). Inventory management (Chapter 23). In MDS-3: Managing access to medicines and health technologies. Management Sciences for Health. https://msh.org/wp-content/uploads/2013/04/mds3-ch23-inventorymgmt-mar2012.pdf

3. Guo, Y., Liu, F., Song, J. S., & Wang, S. (2024). Supply chain resilience: A review from the inventory management perspective. Fundamental research, 5(2), 450–463. https://doi.org/10.1016/j.fmre.2024.08.002

4. Balkhi, B., Alshahrani, A., & Khan, A. (2022). Just-in-time approach in healthcare inventory management: Does it really work?. Saudi pharmaceutical journal : SPJ : the official publication of the Saudi Pharmaceutical Society, 30(12), 1830–1835. https://doi.org/10.1016/j.jsps.2022.10.013


*Built by Somita Chaudhari · Data Scientist*
