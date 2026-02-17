# Shipment Extraction System (Production Demo)

LLM-powered extraction engine for logistics automation. This system autonomously parses unstructured freight forwarding emails into structured data with **93%+ accuracy**.

This repository is a high-fidelity demonstration of a production-scale AI engine developed for a logistics client.

---

## 🏗️ AI System Architecture

The system is built using **Clean Architecture** principles to ensure modularity, testability, and scalability:

- **Connectors**: Pluggable ingestion layers (Live IMAP fetch vs. Batch JSON loading).
- **Engine**: The core extraction logic powered by Llama-3.1-8B via the Groq GroqCloud API.
- **Reliability Protocol**: v6 "Resilient Architect" prompt with alias-aware mapping.
- **Data Integrity**: Powered by Pydantic for strict schema validation and normalization.

---

## 🚀 Key Features

- **Live Integration**: Connect to real mailboxes via IMAP to pull and process live shipment requests.
- **Batch Processing**: Ingest and process large JSON datasets for retrospective analysis.
- **Precision Engineering**:
  - **93% Accuracy** on messy/difficult data.
  - **Fuzzy Port Mapping**: Handles typos (e.g., 'Cheenai' -> 'Chennai') and legacy aliases (e.g., 'Madras' -> 'Chennai').
  - **Unit Conversion**: Automatic conversion of `lbs` to `kg` and `MT` to `kg` with rounding.
- **Production Safety**: Built-in retry mechanisms, exponential backoff for rate limits, and checkpointing.

---

## 🛠️ Setup Instructions

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**
   - Create a `.env` file based on `.env.example`.
   - Add your `GROQ_API_KEY`.
   - (Optional) Configure IMAP settings to enable live email processing.

3. **Execution (Professional CLI)**
   - **Batch Mode (JSON)**:
     ```bash
     python main.py --source json
     ```
   - **Live Mode (IMAP Email)**:
     ```bash
     python main.py --source email --limit 5
     ```

---

## 📈 System Evolution

This system evolved through rigorous testing and prompt engineering phases:

| Version | Focus              | Accuracy | Key Milestone                           |
| ------- | ------------------ | -------- | --------------------------------------- |
| v1-v3   | Basic Mapping      | ~70%     | Initial UN/LOCODE integration           |
| v4      | Strict Protocol    | 91.6%    | Math stabilization & rounding           |
| v5      | Prod Engine        | 92%+     | Unit precedence logic (RT vs CBM)       |
| **v6**  | **Resilient Arch** | **93%+** | **Alias/Typo awareness & Noise Filter** |

---

## ☁️ AI Engineering Philosophy

This project demonstrates a "Small Model, Large Brain" approach:

- **Cost Efficiency**: Using Llama-3.1-8B instead of GPT-4 to reduce operational costs by 95% while maintaining enterprise accuracy.
- **In-Context Learning**: Avoiding expensive fine-tuning by using compressed, high-density context injection for port global reference data.
- **Observability**: Structured logging with `loguru` for production-ready monitoring.
