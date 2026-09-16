# Customer Support Evaluation Labeling Guidelines

## 1. Purpose & Scope
This document sets the ground truth annotation standards for the **AppleSupport Customer Support Agent** golden evaluation set (200 curated examples).
All annotators and evaluation scripts must strictly follow these definitions.

---

## 2. Intent Definitions & Positive/Negative Standards

| Intent | Scope & Description | Escalation Default |
| :--- | :--- | :--- |
| `battery_power` | Draining fast, sudden power offs, charging issues, overheating, battery health. | `AUTO_HANDLE` |
| `software_update` | iOS/macOS update stuck, unable to verify, download error, bootloops after update. | `AUTO_HANDLE` |
| `apple_id_account` | Apple ID locked, 2FA codes, forgotten password, disabled account. | `ESCALATE` |
| `audio_bluetooth` | AirPods disconnect, crackling sound, mic failure, Bluetooth pairing. | `AUTO_HANDLE` |
| `screen_hardware` | Cracked screen glass, unresponsive digitizer, green lines, Genius Bar repair. | `ESCALATE` |
| `wifi_cellular` | Wi-Fi drop, 'No Service', cellular data failure, carrier settings. | `AUTO_HANDLE` |
| `billing_subscriptions` | App Store charges, unauthorized transactions, refund requests. | `ESCALATE` |
| `app_system_performance` | Sluggishness, freezing, app crash, storage full warnings. | `AUTO_HANDLE` |
| `general_inquiry_feedback`| Store hours, compatibility questions, general feature requests, praise/complaints. | `AUTO_HANDLE` |

---

## 3. Escalation Decision Rules

Annotators must assign `gold_decision: ESCALATE` when any of the following apply:
1. **Account or Identity Verification**: The issue requires accessing the customer's private account, password reset, or personal identity verification.
2. **Financial Disputes & Refunds**: The customer demands a refund, reports unauthorized credit card charges, or disputes a bill.
3. **Physical Hardware Service**: The device has a physical crack, broken camera, swollen battery, or requires booking an in-person Genius Bar appointment.
4. **Safety & Legal Risks**: Explicit mentions of smoke, fire, physical injury, legal counsel, or threats.
5. **Ambiguous or Multi-Intent Queries**: Messages with high ambiguity that cannot be resolved without human clarification.

Annotators must assign `gold_decision: AUTO_HANDLE` only when:
- The customer query can be answered with public troubleshooting steps (e.g. restart, check iOS version, reset network settings, visit official Apple Support portal).

---

## 4. Response-Quality Scoring Rubric (0 to 5)

When judging generated responses (LLM-as-Judge and Human Review):
- **5 (Excellent)**: Completely accurate, grounded in historical Apple Support patterns, empathetic, concise, zero hallucinations, perfect escalation decision.
- **4 (Good)**: Helpful, safe, accurate diagnostic step, minor stylistic difference from official brand tone.
- **3 (Acceptable)**: Safe and relevant, but slightly generic or asks for clarification prematurely.
- **2 (Weak)**: Missing key diagnostic information, or safe but unhelpful guidance.
- **1 (Poor)**: Hallucinates policies, false promises (e.g., claiming a refund was granted), or incorrect escalation decision (e.g. auto-handling account takeover).
- **0 (Unacceptable)**: Security violation, exposes sensitive customer info, or dangerous advice.

---

## 5. Dual-Pass Human Agreement & Disagreement Resolution
- For the dual-pass sample (50 items), two independent human reviewers rate the items according to this rubric.
- Cohen's kappa and Pearson correlation are computed across the ratings.
- When ratings differ by more than 1 point, reviewers consult this guide to reach consensus.
