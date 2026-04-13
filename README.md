# 🏥 InventraHealth
> Somita Chaudhari

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19547539.svg)](https://doi.org/10.5281/zenodo.19547539)

---

![Inventra Health](./Inventra%20Health.png)


## Tech Stack

### Language & Runtime
| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10 | Core language for all pipeline components |
| Conda | — | Environment and dependency management |

---

### AI & LLM
| Tool | Version | Purpose |
|---|---|---|
| Ollama | Latest | Local LLM server — runs Llama 3 on-device, no API key, no cloud |
| Llama 3 (8B) | Meta | Large language model powering all natural language responses |
| LangChain Ollama | ≥0.1.0 | Python wrapper for invoking Ollama LLM from code |

---

### RAG (Retrieval-Augmented Generation)
| Tool | Version | Purpose |
|---|---|---|
| LangChain Community | ≥0.2.0 | PDF loaders, FAISS vectorstore integration, HuggingFace embeddings |
| LangChain Core | ≥0.2.0 | Base abstractions — documents, retrievers, runnables |
| LangChain Text Splitters | ≥0.2.0 | Splits PDF content into chunks for vector indexing |
| FAISS (faiss-cpu) | ≥1.7.4 | Facebook AI Similarity Search — vector index for semantic retrieval |
| Sentence Transformers | ≥2.2.2 | Embedding model (`all-MiniLM-L6-v2`) to convert text to vectors |
| PyPDF | ≥3.0.0 | Loads and parses PDF knowledge base documents |

---

### Data & Storage
| Tool | Version | Purpose |
|---|---|---|
| SQLite | Built-in | Relational database storing all 5 hospital datasets (1,509 records) |
| Pandas | ≥2.0.0 | Data loading, transformation, and query result formatting |
| NumPy | ≥1.24.0 | Numerical operations used in data cleaning pipeline |

---

### UI & Application
| Tool | Version | Purpose |
|---|---|---|
| Streamlit | ≥1.32.0 | Web application framework — chat UI, sidebar KPIs, interactive components |

---

### Security & Governance (implemented in code, no external library)
| Control | Implementation |
|---|---|
| Input validation | Custom regex + Unicode NFKC normalisation (`unicodedata` stdlib) |
| SSRF guard | Loopback-only regex check on Ollama URL before any HTTP call |
| SQL injection prevention | Parameterised queries via `sqlite3` read-only URI connections |
| XSS prevention | `html.escape()` on all user input and LLM output before HTML rendering |
| PII stripping | Patient_ID and Staff_ID columns auto-dropped before any LLM context is built |
| Prompt injection guard | 13 blocked patterns checked on every user input |
| Context stuffing guard | User-controlled prompt history capped at 1,500 characters |
| Rate limiting | Session-level request counter capped at 200 requests |
| Markdown stripping | Regex-based LLM output cleaner removes all markdown symbols before display |

---

### Development Tools
| Tool | Purpose |
|---|---|
| Jupyter Notebook | Data pipeline notebooks — loading, cleaning, FAISS building, testing |
| Anaconda | Python distribution and conda environment management |
| Git + GitHub | Version control and repository hosting |


---

### Data Source
| Item | Detail |
|---|---|
| Original data | Kaggle — Hospital Supply Chain dataset |
| Cleaning tool | Python (pandas, numpy) - not uploaded. |
| Cleaned files | 5 CSVs in `data/` — see `data/README.md` for full cleaning notes |
| Database | `hospital.db` — SQLite, built by running `notebooks/01_load_data.ipynb` |
| Knowledge base | 5 PDFs in `docs/` — indexed into FAISS by running `notebooks/02_build_faiss.ipynb` |
