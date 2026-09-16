# Production-Grade AI Customer Support Agent for AppleSupport

An evidence-grounded, safety-critical AI customer support agent trained and evaluated on the Kaggle Twitter Customer Support dataset (`thoughtvector/customer-support-on-twitter` / `twcs.csv`), specialized in **AppleSupport**.

---

## 1. Project Overview

This system is an enterprise-grade customer support assistant engineered for high reliability and conservative safety. Rather than generating ungrounded responses from general LLM knowledge, it:
1. Classifies customer intent across 9 data-grounded support categories.
2. Retrieves historically verified Apple Support resolution patterns.
3. Enforces an independent, deterministic escalation policy layer.
4. Generates schema-validated responses grounded strictly in historical evidence.
5. Evaluates system trustworthiness through safety-critical metrics, including **Unsafe Auto-Handle Rate**.

---

## 2. Architecture Diagram

```mermaid
flowchart TD
    A[Customer Tweet / Inquiry] --> B[Text Cleaner & PII Filter]
    B --> C[Calibrated Semantic Intent Classifier]
    B --> D[Historical Vector Store (12k Pairs)]
    
    C -->|Predicted Intent & Confidence| E[Escalation Policy Engine]
    D -->|Top-3 Evidence & Similarities| E
    
    E -->|Safety Rules, Confidence Fusion, Mandatory Intent Checks| F{Policy Decision}
    F -->|ESCALATE| G[Grounded Response Generator]
    F -->|AUTO_HANDLE| G
    
    G --> H[Output Safety & Hallucination Guardrails]
    H --> I[Validated Support Response + Audit Trace]
```

---

## 3. Why This Brand Was Selected: AppleSupport

From the 2,811,774 tweets in `twcs.csv`, `AppleSupport` was selected over all candidate brands (`AmazonHelp`, `Uber_Support`, `Delta`, `SpotifyCares`):
- **High Volume & Data Quality:** 106,860 verified brand responses.
- **Actionable Diagnostic Conversations:** Unlike AmazonHelp (dominated by generic link deflections) or Uber_Support (private trip dispute refunds), AppleSupport historical agents perform real multi-step technical diagnostics (checking iOS version, battery health, force restarts, resetting network settings).
- **Clean Escalation Boundaries:** Realistic boundary between automated public troubleshooting and private escalation (Apple ID lockouts, billing disputes, broken hardware).
- See detailed comparative metrics in [`reports/brand_selection.md`](file:///c:/Users/jagad/OneDrive/Desktop/Projects/Chatbot/reports/brand_selection.md).

---

## 4. Dataset Processing & Leakage Prevention

- **Raw Dataset:** `twcs.csv` (2.81 million tweets, ~516 MB).
- **Cleaned Dialogues:** 104,732 valid customer $\to$ brand dialogues reconstructed via reply graph tracing.
- **Conversation-Level Splitting:** Split on `conversation_id` (root thread ID) to eliminate cross-split data leakage:
  - **Train:** 12,000 conversations (80%)
  - **Validation:** 1,500 conversations (10%)
  - **Test:** 1,500 conversations (10%)

---

## 5. Intent Taxonomy (9 Empirical Categories)

Formulated directly from keyword clustering and frequency analysis of 12,000 AppleSupport queries:

| Intent Name | Default Policy | Diagnostic Focus |
| :--- | :--- | :--- |
| `battery_power` | `AUTO_HANDLE` | Battery health, fast drain, sudden shutdowns, charging issues. |
| `software_update` | `AUTO_HANDLE` | iOS/macOS update stuck, unable to verify, storage full errors. |
| `apple_id_account` | `ESCALATE` | Locked Apple ID, 2FA codes, forgotten password, security holds. |
| `audio_bluetooth` | `AUTO_HANDLE` | AirPods pairing, disconnects, microphone, speaker crackling. |
| `screen_hardware` | `ESCALATE` | Cracked screen, digitizer failure, green lines, Genius Bar repair. |
| `wifi_cellular` | `AUTO_HANDLE` | Wi-Fi drop, 'No Service', cellular data loss, reset network settings. |
| `billing_subscriptions`| `ESCALATE` | App Store charges, unauthorized purchases, refund claims. |
| `app_system_performance`| `AUTO_HANDLE`| Sluggish UI, app crash, keyboard lag, storage warnings. |
| `general_inquiry_feedback`| `AUTO_HANDLE`| Hardware compatibility, retail store hours, feature inquiries. |

Documented in [`configs/intents.yaml`](file:///c:/Users/jagad/OneDrive/Desktop/Projects/Chatbot/configs/intents.yaml) and [`reports/intent_discovery.md`](file:///c:/Users/jagad/OneDrive/Desktop/Projects/Chatbot/reports/intent_discovery.md).

---

## 6. System Architecture

The codebase follows a clean, decoupled production structure:
```text
Chatbot/
├── configs/             # YAML configurations (intents, thresholds, paths)
├── data/
│   ├── raw/             # Original twcs.csv
│   ├── interim/         # Inspection and interim reports
│   └── processed/       # Reconstructed splits & vector indices
├── src/
│   ├── api/             # FastAPI REST endpoints
│   ├── data/            # Preprocessing, conversation reconstruction, labeling
│   ├── models/          # Baseline A, Baseline B, and Main Semantic Classifiers
│   ├── retrieval/       # Local vector store with cosine similarity
│   ├── generation/      # Evidence-grounded prompt builder and generator
│   ├── decision/        # Escalation policy engine and confidence fusion
│   ├── safety/          # Guardrails, sensitive triggers, PII redaction
│   ├── llm/             # Base provider, OpenAI, Gemini, and Mock providers
│   ├── schemas/         # Pydantic schemas
│   └── pipeline.py      # Master orchestrator
├── evaluation/          # Evaluation harness, metrics, golden set, LLM judge
├── reports/             # Brand selection, failure analysis, final report
├── scripts/             # Setup, build index, CLI demo
└── tests/               # 20 unit and integration tests (pytest)
```

---

## 7. Retrieval Architecture

- **Engine:** In-memory sublinear TF-IDF + Cosine Similarity Vector Store (`src/retrieval/vector_store.py`).
- **Index:** 12,000 historical resolution pairs.
- **Latency:** Sub-2 milliseconds per search.
- **Metrics:**
  - `Recall@1`: **60.00%**
  - `Recall@3`: **80.20%**
  - `Recall@5`: **85.40%**
  - `MRR`: **0.7032**

---

## 8. Escalation Policy

Default policy is **conservative**:
- **Mandatory Escalation:** `apple_id_account`, `billing_subscriptions`, `screen_hardware`.
- **Sensitive Keyword Triggers:** `stolen`, `hacked`, `unauthorized`, `lawyer`, `court`, `police`, `smoke`, `fire`.
- **Confidence Fusion:** Composite Confidence = $0.60 \times \text{Intent Confidence} + 0.40 \times \text{Retrieval Similarity}$.
- **Thresholds:** Minimum Intent Confidence: `0.70`, Minimum Retrieval Similarity: `0.55`, Minimum Composite: `0.72`.

---

## 9. Setup

```bash
# 1. Clone repository and navigate to folder
cd Chatbot

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

## 10. Quickstart

Run the interactive CLI demonstration:
```bash
python -m scripts.run_demo
```

Launch the production FastAPI service:
```bash
uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
Test with curl:
```bash
curl -X POST http://127.0.0.1:8000/v1/support/respond \
  -H "Content-Type: application/json" \
  -d '{"customer_message": "I was charged twice on my credit card for my monthly iCloud storage subscription."}'
```

---

## 11. Reproduce Headline Results (< 15 Minutes)

Run the automated setup and unified evaluation harness:
```bash
# Verify environment and build index
python -m scripts.setup_env

# Run full evaluation harness
python -m evaluation.run_evaluation
```

---

## 12. Evaluation Methodology

- **Golden Evaluation Set:** 200 curated, non-leakage examples representing rare intents, noisy Twitter slang, multi-turn contexts, and edge cases.
- **LLM-as-a-Judge:** Fixed 0–5 rubric across Factual Correctness, Historical Grounding, Resolution Alignment, Helpfulness, Brand Consistency, Safety, and Appropriate Escalation.
- **Human vs LLM Agreement:** Dual-pass human annotation on 50 samples measuring Exact Agreement, $\pm 1$ point agreement, and Quadratic Weighted Cohen's Kappa.

---

## 13. Baselines

1. **Baseline A (Most Frequent):** Predicts majority class (`general_inquiry_feedback`).
2. **Baseline B (TF-IDF + Logistic Regression):** Standard multinomial logistic regression.
3. **Main System:** Word + Character-wb FeatureUnion with Calibrated LinearSVC.

---

## 14. Results

### Intent Classification Benchmark (Test Set: 1,500 samples)
| Model | Accuracy | Macro Precision | Macro Recall | **Macro F1** |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline A (Most Frequent)** | 43.73% | 4.86% | 11.11% | **6.76%** |
| **Baseline B (TF-IDF + Logistic)** | 88.27% | 85.34% | 72.10% | **76.57%** |
| **Main Semantic Model** | **95.33%** | **93.28%** | **90.12%** | **91.50%** |

### Golden Set (200 samples) & Safety Metrics
| Metric | Result | Target / Standard |
| :--- | :--- | :--- |
| **Main Model Golden Set Macro-F1** | **83.40%** | >80.00% |
| **Escalation Recall** | **100.00%** | High (>95%) |
| **Unsafe Auto-Handle Rate** | **0.00%** | **0.00% [SAFETY-CRITICAL]** |
| **Auto-Handle Rate** | **11.00%** | Safe subset |
| **False Escalation Rate** | **86.75%** | Conservative |
| **Retrieval Recall@3** | **80.20%** | >75.00% |
| **Retrieval MRR** | **0.7032** | >0.6500 |
| **Judge Factual Correctness** | **5.00 / 5.0** | Perfect |
| **Judge Brand Consistency** | **5.00 / 5.0** | Perfect |
| **Human–Judge Agreement ($\pm 1$)**| **100.00%** | High (>90%) |
| **Cohen's Kappa (Quadratic)** | **0.6479** | Substantial agreement |

---

## 15. Failure Analysis

Top 5 failure modes identified in [`reports/failure_analysis.md`](file:///c:/Users/jagad/OneDrive/Desktop/Projects/Chatbot/reports/failure_analysis.md):
1. **Conservative Retrieval Under-Matching:** Over-escalation on synonym variations (*"getting super hot"* vs *"overheating"*).
2. **Multi-Intent Masking:** Software update keywords overshadowing battery symptoms.
3. **Lexical Sparsity in Short Queries:** 2-word queries fail the 0.55 similarity threshold.
4. **Broad Mandatory Escalation:** Benign $1 authorization hold queries triggering mandatory escalation.
5. **App Freeze vs Screen Digitizer Ambiguity:** Single turn unable to differentiate software lockup from broken hardware.

---

## 16. "What is Misleading About My Headline Number?"

- **The Headline:** `0.00% Unsafe Auto-Handle Rate` & `100.00% Escalation Recall`.
- **The Reality:** 0% unsafe auto-handling was achieved by escalating **89%** of queries (False Escalation Rate of 86.75%). In a live contact center, escalating 89% of queries would strain human support staff.
- **Fluency vs Resolution:** High LLM judge scores (5.0/5.0) reflect polished brand tone and safe advice, but polite clarification questions (*"What version of iOS are you on?"*) do not equal final ticket resolution.

---

## 17. Limitations

1. **Static 2017 Dataset:** References legacy tools (iTunes rather than Finder/Apple Devices).
2. **No Live Device Telemetry:** Cannot query real AppleCare warranty databases or battery cycle counts.
3. **Single-Turn Dominance:** Multi-turn context is concatenated into text rather than tracked via persistent dialog state tracking.

---

## 18. What I Would Do With One More Week

1. **Dense Bi-Encoder (Day 1-2):** Deploy `bge-small-en-v1.5` embeddings to elevate Recall@1 to >85%.
2. **Dynamic Intent Thresholds (Day 3):** Tune per-intent thresholds (e.g. 0.42 for general inquiries) to lower false escalation from 86.7% to <30% while retaining 0% unsafe automation.
3. **Sub-Intent Granularity (Day 4):** Split `billing_subscriptions` into self-help holds vs fraud disputes.
4. **Interactive Multi-Turn State Machine (Day 5):** Guide customers through sequential troubleshooting (Reboot $\to$ Re-test $\to$ Escalate).
5. **Observability Dashboard (Day 6-7):** Integrate Prometheus metrics and nightly automated regression tests.

---

## 19. Test Suite Verification

Run the full pytest suite:
```bash
pytest tests -v
```
**Status:** `20 passed in 1.89s` (100% passing).
