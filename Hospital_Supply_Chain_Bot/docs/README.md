# Inventra Health — Knowledge Base Documentation

This folder contains the PDF documents loaded into the FAISS vector index
that powers Inventra Health's RAG pipeline. When a user asks a question,
the system retrieves the most relevant chunks from these documents and
injects them alongside live hospital data to ground the LLM's response
in supply chain best practices.

---

## Documents in this folder

### 1. MSH Chapter 23 — Inventory Management
`mds3-ch23-inventorymgmt-mar2012.pdf`


This chapter from the WHO-affiliated Management Sciences for Health
handbook is the most directly applicable supply chain reference for
hospital inventory operations. It covers safety stock formulas, reorder
point logic, ABC analysis for item prioritisation, and lead time variance
— the exact concepts behind the `Days_Until_Stockout`, `Restock_Alert`,
and `Restock_Lead_Time` columns in this dataset. When Inventra Health
recommends emergency orders or flags stockout risk, this document
provides the authoritative methodology behind those decisions. It
bridges textbook supply chain theory directly to the data the chatbot
reasons over, making recommendations defensible rather than generic.

**Citation (APA 7th):**
Management Sciences for Health. (2012). *Inventory management*
(Chapter 23). In *MDS-3: Managing access to medicines and health
technologies*. Management Sciences for Health.
https://msh.org/wp-content/uploads/2013/04/mds3-ch23-inventorymgmt-mar2012.pdf

---

### 2. MSH Chapter 44 — Medical Stores Management
`mds3-ch44-medicalstores-mar2012.pdf`

Chapter 44 covers the operational side of running a hospital supply
system — stock receipt and inspection, FIFO/FEFO rotation, warehouse
zoning, vendor performance monitoring, and procurement lead time
tracking. This directly maps to the vendor delay logic in this project:
EquipMed Co. running 14 days late and HealthTools Ltd. running 5 days
late are exactly the scenarios this chapter teaches managers to detect
and act on. It also covers stock record accuracy, which underpins the
data quality flags in the patient and staff tables. It gives Inventra
Health the vocabulary and reasoning framework to speak like an
experienced hospital supply chain manager, not a generic chatbot.

**Citation (APA 7th):**
Management Sciences for Health. (2012). *Medical stores management*
(Chapter 44). In *MDS-3: Managing access to medicines and health
technologies*. Management Sciences for Health.
https://msh.org/wp-content/uploads/2013/04/mds3-ch44-medicalstores-mar2012.pdf

---

### 3. Just-in-Time Approach in Healthcare Inventory Management
`main.pdf`

This peer-reviewed article from the *Saudi Pharmaceutical Journal* (2022)
directly evaluates JIT inventory systems in healthcare settings — their
cost-saving benefits under normal conditions and their catastrophic
failure modes during demand surges like COVID-19. This is precisely
the tension present in this hospital's data: 299 active restock alerts
and 182 critical stockout items suggest a lean inventory posture that
has become fragile. The paper's recommendations — safety buffer stocks,
supplier diversification, and supply chain risk management systems —
give Inventra Health the clinical and operational language to frame
recommendations beyond just "order more units."

**Citation (APA 7th):**
Balkhi, B., Alshahrani, A., & Khan, A. (2022). Just-in-time approach in
healthcare inventory management: Does it really work?
*Saudi Pharmaceutical Journal, 30*(12), 1830–1835.
https://doi.org/10.1016/j.jsps.2022.10.013

---

### 4. Supply Chain Resilience — A Review from the Inventory Management Perspective
`main__1_.pdf`


This 2025 review article from *Fundamental Research* (Elsevier) provides
the strategic framework for understanding why EquipMed Co.'s 14-day
delay matters beyond the immediate stockout risk. It covers inventory
pre-positioning, multiple sourcing, demand surge management, and the
cascading ripple effects of vendor disruptions through a supply network.
For a hospital already running 298 critical items, a delayed primary
vendor is a systemic risk, not just an operational inconvenience. This
paper gives Inventra Health the conceptual grounding to recommend
backup sourcing strategies, capacity reservation, and risk tiering —
moving recommendations from reactive to strategic.

**Citation (APA 7th):**
Guo, Y., Liu, F., Song, J.-S., & Wang, S. (2025). Supply chain resilience:
A review from the inventory management perspective.
*Fundamental Research, 5*, 450–463.
https://doi.org/10.1016/j.fmre.2024.08.002

---

### 5. Hospital Supply Chain Data Dictionary
`hospital_supply_chain_data_dictionary.pdf`

**Not uploaded to GitHub — included in FAISS index only.**

**What it is and how it was developed:**
This document was custom-generated specifically for the Inventra Health
chatbot knowledge base. It defines every column across all five hospital
supply chain CSV files used in this project — 49 columns across
inventory, vendor, financial, patient, and staff tables. For each column
it documents the data type, value range, business logic, flag definitions,
computed column formulas, and cross-table join keys.

It was built by systematically analysing the cleaned datasets and
encoding the domain knowledge required to reason correctly about the
data — for example, that `Days_Until_Stockout` is computed as
`Current_Stock / Avg_Usage_Per_Day`, that `Restock_Alert = True` when
that value is less than or equal to `Restock_Lead_Time`, and that 195
patient records have inverted dates that require using
`Admission_Date_Only` instead of the raw datetime column.


Without this document, the LLM only has the data values it sees in the
SQL context. With it, the LLM understands *why* those values matter —
that a `Days_Until_Stockout` of 0.2 is catastrophic because the lead
time is 14 days, that `Flag_HoursExceedShift` indicates genuine overwork
rather than a data error, and that `Staff_ID` and `Patient_ID` are
excluded from context for privacy reasons. It transforms the chatbot
from a data reader into a domain-aware analyst that can reason about
the data the way a supply chain manager would.

---

## How the knowledge base is used

At query time, Inventra Health runs the user's question through the
FAISS index and retrieves the 3 most semantically relevant chunks
across all five documents. These are injected into the LLM prompt
alongside live SQL data from the hospital database. The combination
ensures that every recommendation is grounded in both real-time
hospital data and authoritative supply chain methodology.

The data dictionary is the highest-value document in the index for
operational questions. The MSH chapters dominate for methodology
questions (safety stock, reorder logic, vendor SLAs). The JIT and
resilience papers provide strategic framing for questions about
systemic risk, vendor diversification, and demand volatility.

---

*Knowledge base assembled by Somita Chaudhari · Data Scientist 
*Inventra Health — Hospital Supply Chain Intelligence*
