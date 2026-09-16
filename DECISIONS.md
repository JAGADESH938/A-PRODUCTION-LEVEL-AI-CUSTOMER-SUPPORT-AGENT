# Engineering Decision Log (DECISIONS.md)

This document records the 14 critical architectural, modeling, and policy decisions made during the design and implementation of the AppleSupport Customer Support AI Agent.

---

### Decision 1: Selected Brand — AppleSupport
- **Decision:** Select `AppleSupport` as the single target brand.
- **Reason:** AppleSupport has over 106,860 brand interactions with high-quality, multi-step technical diagnostic dialogues (restarts, battery health checks, network resets) and a balanced ratio of automated troubleshooting vs private escalation.
- **Alternative Considered:** `AmazonHelp` or `Uber_Support`.
- **Why Rejected:** AmazonHelp responses are overwhelmingly generic link deflections (`amzn.to/...`) or immediate private message requests for privacy reasons. Uber_Support conversations are predominantly post-trip fare disputes requiring private rider account database lookups with minimal public technical troubleshooting.

---

### Decision 2: Conversation-Level Data Splitting
- **Decision:** Split data strictly on `conversation_id` (root thread ID) rather than individual tweet rows.
- **Reason:** Individual tweet splitting causes severe data leakage: a customer tweet could appear in the train set while its corresponding brand reply or follow-up turn appears in the test set.
- **Alternative Considered:** Stratified random row-level splitting.
- **Why Rejected:** Severe cross-split contamination artificially inflates evaluation metrics.

---

### Decision 3: Intent Classification Metric — Macro-F1 Over Accuracy
- **Decision:** Emphasize Macro-F1 as the primary model selection criterion over overall accuracy.
- **Reason:** Customer support datasets suffer from severe class imbalance (`general_inquiry` is ~42% of volume, while `billing_subscriptions` and `wifi_cellular` are <3%). A naive model predicting majority classes scores ~44% accuracy with an abysmal 6.7% Macro-F1.
- **Alternative Considered:** Standard Accuracy or Weighted-F1.
- **Why Rejected:** Weighted-F1 and accuracy conceal catastrophic failures on safety-critical, low-frequency classes like account security and billing fraud.

---

### Decision 4: Main Classifier Architecture — FeatureUnion (Word + Char-wb) with Calibrated LinearSVC
- **Decision:** Use a FeatureUnion of Word N-grams (1-3) and Character-wb N-grams (3-5) with Sigmoid Calibrated LinearSVC and balanced class weights.
- **Reason:** Twitter customer text is filled with typos (*"updat"*, *"batry"*), abbreviations (*"2fa"*, *"ios11"*), and punctuation anomalies. Subword character n-grams ensure robust classification even on misspelled words, achieving 95.33% accuracy and 91.50% Macro-F1.
- **Alternative Considered:** Fine-tuned BERT / RoBERTa transformer.
- **Why Rejected:** Full neural transformer fine-tuning requires heavyweight GPU infrastructure and high inference latency (>150ms), violating the requirement for sub-15-minute laptop reproducibility.

---

### Decision 5: Local Vector Store Engine — TF-IDF Sublinear Embeddings + Cosine Similarity
- **Decision:** Implement an in-memory, deterministic cosine similarity vector store persisted via pickle rather than an external vector DB.
- **Reason:** Zero external network latency, sub-2ms query time, 100% deterministic reproducibility, zero native C++ build hurdles on Windows with Python 3.14.
- **Alternative Considered:** ChromaDB or Pinecone.
- **Why Rejected:** External vector databases add unnecessary network dependencies, API keys, disk bloat, or native C++ compilation failures on pre-release Python versions without measurable benefit for a 12,000-document index.

---

### Decision 6: Grounded RAG Retrieval Before Generation
- **Decision:** Force the LLM generator to condition strictly on retrieved historical brand responses.
- **Reason:** LLMs answering purely from parametric pretraining hallucinate outdated or fictional Apple policies, non-existent URLs, or fabricated refund promises.
- **Alternative Considered:** Direct zero-shot LLM prompting without retrieval.
- **Why Rejected:** Zero-shot prompting lacks brand voice fidelity and risks catastrophic policy hallucinations.

---

### Decision 7: Independent Deterministic Escalation Policy Layer
- **Decision:** Decouple the escalation decision from the LLM generator and enforce it via a deterministic Python policy engine.
- **Reason:** LLMs are prone to sycophancy and instruction drifting. Allowing an LLM to freely decide whether to escalate leads to unpredictable false auto-handling of dangerous cases.
- **Alternative Considered:** Asking the LLM to output whether it wants to escalate.
- **Why Rejected:** Unsafe; non-deterministic LLMs cannot be trusted as the sole safety gatekeeper in production enterprise support.

---

### Decision 8: Safety-Critical Metric Priority — Unsafe Auto-Handle Rate
- **Decision:** Treat `Unsafe Auto-Handle Rate` as the primary North Star safety metric (targeted at 0.00%).
- **Reason:** A false escalation merely costs a few human minutes; an unsafe auto-handle (e.g. attempting to auto-resolve a swollen burning battery or hacked Apple ID) poses serious physical, legal, and financial harm.
- **Alternative Considered:** Maximizing raw Auto-Handle Rate.
- **Why Rejected:** Optimizing for maximum automation incentivizes models to guess on high-risk cases, creating safety vulnerabilities.

---

### Decision 9: Composite Confidence Score Fusion
- **Decision:** Compute a weighted composite confidence: $0.60 \times \text{Intent Confidence} + 0.40 \times \text{Retrieval Similarity}$.
- **Reason:** Even if the classifier is 99% confident that a query is `battery_power`, if no similar historical resolution exists in the index (similarity < 0.55), the system should not fabricate a response.
- **Alternative Considered:** Relying solely on classifier softmax probability.
- **Why Rejected:** Softmax probabilities are notoriously overconfident on out-of-distribution inputs.

---

### Decision 10: Mandatory Escalation Intents
- **Decision:** Hardcode mandatory escalation for `apple_id_account`, `billing_subscriptions`, and `screen_hardware`.
- **Reason:** Apple's actual support policy strictly prohibits public resolution of account takeovers, billing refunds, and hardware repairs on Twitter.
- **Alternative Considered:** Allowing auto-handling if classification confidence is >0.98.
- **Why Rejected:** Even with 100% classification confidence, an AI agent cannot process credit card refunds or inspect physical broken glass.

---

### Decision 11: LLM Provider Abstraction with Offline Mock Fallback
- **Decision:** Implement a modular `BaseLLMProvider` interface with live adapters (OpenAI, Gemini) and a fully deterministic offline `MockLLMProvider`.
- **Reason:** Enables new developers, CI pipelines, and evaluators to run and reproduce the entire pipeline and test suite in under 15 minutes without providing an external paid API key.
- **Alternative Considered:** Hardcoding OpenAI API calls.
- **Why Rejected:** Fails reproducibility if the evaluator lacks an active paid OpenAI key.

---

### Decision 12: Dual-Pass Human Agreement Evaluation
- **Decision:** Benchmark LLM-as-a-Judge against dual-pass human evaluation on 50 golden samples and report Cohen's kappa.
- **Reason:** LLM judges can suffer from self-preference bias or lenient grading; measuring human-LLM agreement establishes whether the judge is reliable.
- **Alternative Considered:** Reporting only LLM judge scores without human validation.
- **Why Rejected:** Violates AI evaluation rigor; unvalidated LLM judges can hide significant qualitative failures.

---

### Decision 13: Strict Pydantic Structured Output Validation with Retry
- **Decision:** Validate all LLM completions against Pydantic schemas, with a 1-retry fallback that defaults safely to `ESCALATE` upon failure.
- **Reason:** Malformed JSON or schema drift must never crash the production API or leak raw trace errors to customers.
- **Alternative Considered:** Relaxed regex parsing of raw LLM text.
- **Why Rejected:** Brittle and prone to silent failures.

---

### Decision 14: Fast Local API Architecture (FastAPI + Pydantic)
- **Decision:** Deploy via FastAPI with async endpoints, structured JSON logging, and standardized HTTP status codes (400, 422, 429, 500, 503).
- **Reason:** Lightweight, asynchronous, high-throughput, and self-documenting via OpenAPI/Swagger.
- **Alternative Considered:** Heavyweight distributed microservices with Kafka.
- **Why Rejected:** Unnecessary infrastructure overhead for single-brand deployment on a laptop.
