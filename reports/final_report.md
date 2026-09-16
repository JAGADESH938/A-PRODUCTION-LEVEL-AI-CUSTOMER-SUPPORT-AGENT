# Executive Engineering Report: AppleSupport AI Customer Support Agent

**Author:** Staff AI / MLOps Engineer  
**Dataset:** `thoughtvector/customer-support-on-twitter` (`twcs.csv`)  
**Target Brand:** `AppleSupport`  
**Evaluation Scope:** 2,811,774 Raw Tweets | 104,732 Reconstructed Dialogues | 200 Golden Evaluation Samples  

---

## 1. Problem Framing: What Does "Good" Mean for AppleSupport?

On social media, Apple Support does not merely answer general technology trivia. "Good" customer support for Apple is defined by five strict engineering criteria:
1. **Diagnostic Rigor Over Premature Promises:** Good agents first ask identifying diagnostic questions (e.g. *"What version of iOS is installed under Settings > General > About?"*) rather than jumping to wild guesses.
2. **Zero Policy Hallucination:** Agents must never invent free replacement programs, falsely claim refunds were credited, fabricate non-existent iOS settings, or invent external links.
3. **Conservative Escalation for Sensitive Operations:** Account lockouts (Apple ID/iCloud), financial disputes (App Store unauthorized charges), and physical hardware damage (shattered displays, swollen batteries) **cannot** be resolved by an automated Twitter bot. The system must defer to authorized human specialists via DM or Genius Bar booking.
4. **Authentic Brand Voice:** Apple Support’s signature tone is calm, empathetic, professional, polite, concise, and structured.
5. **Measurable Safety:** The primary performance objective is minimizing **Unsafe Auto-Handle Rate** (false automation of high-risk cases) to 0.00%, rather than chasing maximum automation at the cost of safety.

---

## 2. System Architecture

The system is architected as a modular, decoupled pipeline separating classification, retrieval, policy decisions, and grounded generation:

```
                          [ Incoming Customer Tweet ]
                                       │
                                       ▼
                       [ Input Cleaning & Normalization ]
                         (Mask handles, URLs, PII)
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
    [ Semantic Intent Classifier ]             [ Historical Vector Store ]
    (Word + Char-wb FeatureUnion +            (12,000 Historical Dialogues,
     Calibrated LinearSVC, balanced)           Cosine Similarity Engine)
                │                                             │
                │ Intent & Confidence                         │ Top-3 Resolutions & Similarity
                └──────────────────────┬──────────────────────┘
                                       │
                                       ▼
                     [ Escalation Policy Decision Engine ]
                     - Safety Guardrails & Sensitive Keywords
                     - Mandatory Escalation Intent Rules
                     - Confidence Fusion ($0.60 \times C_{int} + 0.40 \times S_{ret}$)
                                       │
                         Decision & Grounding Context
                                       │
                                       ▼
                     [ Evidence-Grounded LLM Generator ]
                     - Conditioned strictly on retrieved evidence
                     - Strict JSON output schema with Pydantic validation
                     - 1-retry fallback defaulting safely to ESCALATE
                                       │
                                       ▼
                        [ Output Safety Guardrails ]
                        (Check for fabricated promises/PII)
                                       │
                                       ▼
                     [ Final Customer Response + Trace ]
```

---

## 3. Intent Classification: Results Against Baselines

Intent classification was evaluated across 9 empirical intents on the held-out test split (1,500 conversations):

| Model Architecture | Accuracy | Macro Precision | Macro Recall | **Macro F1** | Weighted F1 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline A: Most Frequent Intent** | 43.73% | 4.86% | 11.11% | **6.76%** | 26.62% |
| **Baseline B: TF-IDF + Logistic Regression** | 88.27% | 85.34% | 72.10% | **76.57%** | 87.41% |
| **Main Model: Calibrated Semantic FeatureUnion** | **95.33%** | **93.28%** | **90.12%** | **91.50%** | **95.22%** |

*Key Finding:* Baseline A achieves 43.7% accuracy solely by guessing `general_inquiry_feedback`, but completely fails on all other 8 classes. The Main Semantic Model achieves **91.50% Macro-F1**, providing a **+84.74%** boost over Baseline A and **+14.93%** over Baseline B by leveraging subword character n-grams to overcome social media typos and slang.

---

## 4. Historical Response Retrieval (RAG)

The vector retrieval system indexes 12,000 historical AppleSupport resolution pairs (customer problem $\to$ verified brand reply) using sublinear TF-IDF embeddings and cosine similarity:

- **Recall@1:** 60.00%
- **Recall@3:** 80.20%
- **Recall@5:** 85.40%
- **MRR (Mean Reciprocal Rank):** 0.7032
- **Average Query Latency:** 1.8 milliseconds

*Retrieval Example:*
- *Customer:* "I was charged twice on my credit card for my monthly iCloud storage subscription."
- *Retrieved Top-1 Evidence (Similarity: 0.88, Intent: `billing_subscriptions`):*
  > *"Thanks for reaching out. We can help point you in the right direction. Please visit reportaproblem.apple.com to review your purchases and submit a refund claim, or send us a DM."*

---

## 5. Grounded Response Generation & Safety

Generated responses condition strictly on retrieved historical evidence. Hallucination guardrails and Pydantic validation intercept invalid outputs:
- **Zero Prompt Injection Leakage:** System prompts and raw trace metadata are isolated.
- **Prohibited Claims Filter:** Intercepts promises of unauthorized refunds or fabricated order tracking numbers.
- **PII Scrubbing:** Automatically redacts 16-digit credit card patterns from audit logs (`[REDACTED_CARD]`).

---

## 6. Escalation Performance & Safety-Critical Metrics

Evaluated on the 200-sample Golden Evaluation Set:

| Metric | Measured Value | Operational Meaning |
| :--- | :--- | :--- |
| **Escalation Recall** | **100.00%** | 100% of high-risk cases requiring escalation were successfully escalated. |
| **Unsafe Auto-Handle Rate** | **0.00%** | **[SAFETY-CRITICAL] Zero high-risk cases were unsafely automated.** |
| **Escalation Accuracy** | 28.00% | Conservative gating due to strict similarity threshold (0.55). |
| **False Escalation Rate** | 86.75% | Safe cases escalated when historical similarity fell below 0.55. |
| **Auto-Handle Rate** | 11.00% | Automated responses restricted to high-confidence, well-grounded queries. |

---

## 7. Golden Evaluation Set Methodology

The Golden Set consists of **200 manually curated, highly diverse examples**:
- **Distribution:** Balanced across all 9 intents (`battery_power`, `software_update`, `apple_id_account`, `billing_subscriptions`, `screen_hardware`, `audio_bluetooth`, `wifi_cellular`, `app_system_performance`, `general_inquiry_feedback`).
- **Edge Cases Included:**
  - Ambiguous short queries (*"Battery dying fast"*, *"Update fail"*, *"???"*).
  - Multi-intent queries (iOS update leading to YouTube background battery drain).
  - High-risk safety hazards (swollen batteries, smoking chargers).
  - Legal threats (*"I will sue Apple in court"*).
  - Account takeover and security breaches.
  - Multi-turn conversation trees.

---

## 8. LLM-as-a-Judge & Human Agreement

An automated LLM Judge evaluated all generated responses across a standardized 0–5 rubric:

| Evaluation Dimension | Average Score (0–5) | Quality Assessment |
| :--- | :--- | :--- |
| **Factual Correctness** | **5.00 / 5.0** | Perfect compliance; zero fabricated technical steps. |
| **Historical Grounding** | **4.00 / 5.0** | Responses reflect real AppleSupport diagnostic patterns. |
| **Resolution Alignment** | **3.56 / 5.0** | High alignment on escalation; conservative on borderline cases. |
| **Helpfulness** | **4.00 / 5.0** | Clear diagnostic steps and self-service URL directions. |
| **Brand Consistency** | **5.00 / 5.0** | Authentic AppleSupport voice and empathy. |
| **Safety** | **5.00 / 5.0** | Complete adherence to safety rules; zero PII requests. |
| **Appropriate Escalation** | **2.84 / 5.0** | Penalized for over-escalation on safe borderline queries. |

### Human vs. LLM Judge Agreement (50-Sample Dual-Pass):
- **Exact Agreement:** 46.00%
- **Agreement Within $\pm 1$ Point:** **100.00%**
- **Cohen's Kappa (Quadratic Weighted):** **0.6479** (Substantial inter-rater reliability)

---

## 9. Top 5 Failure Modes Summary

1. **Over-Escalation on Phrasing Variations:** Similarity threshold (0.55) triggers escalation for queries with unfamiliar synonyms (*"getting super hot"* vs *"overheating"*).
2. **Multi-Intent Masking:** In *"updated to 11.0.3 and battery drains"*, software update keywords overpower battery drain symptoms.
3. **Lexical Sparsity in Short Queries:** 2-word queries produce weak vector matches and fail retrieval thresholds.
4. **Over-Broad Mandatory Intent Triggers:** Benign billing questions (e.g. temporary $1 authorization holds) trigger mandatory escalation.
5. **App Freeze vs. Hardware Touchscreen Ambiguity:** Single-turn messages cannot distinguish between a frozen app and a broken digitizer.

---

## 10. Mandatory Section: "What is Misleading About My Headline Number?"

### The Headline Metric: **0.00% Unsafe Auto-Handle Rate**

While 0.00% unsafe automation proves that the system never exposes the company to critical security, legal, or physical safety liabilities, presenting this number without context is misleading:
- **Over-Escalation Obscured:** The agent achieves 0% unsafe auto-handling primarily because it escalates **89.00%** of all customer volume. In a live contact center, escalating 89% of queries fails to deliver the promised operational automation savings.
- **Evaluation Set Difficulty Skew:** The 200-sample Golden Set deliberately over-represents catastrophic edge cases (e.g. swollen batteries, legal threats) relative to the vast sea of simple repetitive inquiries in actual production traffic.
- **Fluency Illusion:** The LLM Judge's 5.0/5.0 score reflects excellent grammatical fluency and polite brand tone, but fluency should not be conflated with issue resolution.

---

## 11. Known System Limitations

1. **Static Historical Knowledge:** The index contains 2017 Twitter data (referencing iTunes rather than Finder/Apple Devices). Without live synchronization to Apple's modern knowledge base, legacy URLs may be stale.
2. **Single-Turn Bias in Retrieval:** Retrieval matches primarily on the latest customer turn rather than encoding full conversational dialogue trees into a unified dense state.
3. **Lack of CRM / Telemetry Integration:** The agent cannot query actual device telemetry (e.g., AppleCare coverage status or Battery Cycle Count) to make conclusive hardware assessments.

---

## 12. Prioritized One-Week Improvement Plan

If granted one additional sprint:
1. **Dense Bi-Encoder Retrieval (Day 1-2):** Replace TF-IDF vector retrieval with a fine-tuned `bge-small-en-v1.5` dense embedding model to raise Recall@1 from 60% to >85% and resolve the thermal synonym under-matching issue.
2. **Dynamic Confidence Calibration (Day 3):** Tune per-intent similarity thresholds (e.g. 0.42 for routine general inquiries, 0.65 for hardware) to reduce False Escalation Rate from 86.7% down to <30% while preserving 0% unsafe auto-handling.
3. **Sub-Intent Splitting (Day 4):** Split `billing_subscriptions` into `billing_self_help` (auto-handleable holds/refund links) and `billing_dispute` (mandatory escalation).
4. **Stateful Interactive Troubleshooting Trees (Day 5):** Implement a state machine for common multi-turn flows (Force Reboot $\to$ Check Result $\to$ Escalate if unresolved).
5. **Continuous Evaluation & Monitoring Pipeline (Day 6-7):** Integrate Prometheus metrics (`support_requests_total`, `escalation_rate`, `latency_seconds`) and nightly automated golden-set regression runs.
