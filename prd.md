# CreatorPulse PRD (MVP)

## 📝 Abstract

CreatorPulse is a daily feed curator and newsletter drafting assistant for independent creators. It aggregates trusted sources, detects trending topics, and generates voice-matched newsletter drafts that can be reviewed and sent in under 20 minutes. The goal is to eliminate the manual research and drafting burden, allowing creators to publish consistently with quality.

---

## 🎯 Business Objectives

* Reduce time spent curating and writing newsletters from hours to minutes.
* Improve content consistency and audience engagement for creators.
* Establish CreatorPulse as the go-to AI-powered curation assistant for individual publishers.

---

## 📊 KPI

| GOAL                         | METRIC                              | TARGET (90 days) | QUESTION                                    |
| ---------------------------- | ----------------------------------- | ---------------- | ------------------------------------------- |
| Faster newsletter turnaround | Avg. review time per accepted draft | ≤ 20 min         | Are creators saving meaningful time?        |
| Higher draft quality         | Draft acceptance rate               | ≥ 70%            | Are AI drafts good enough to use regularly? |
| Better audience engagement   | Median open/CTR uplift              | ≥2× baseline     | Are curated newsletters performing better?  |

---

## 🏆 Success Criteria

* Creators can review and send a ready-to-publish newsletter in under 20 minutes.
* At least 70% of drafts are accepted without major rework.
* Over 60% of active users see uplift in engagement metrics (open rate or CTR).

---

## 🚶‍♀️ User Journeys

**Primary Persona:** Independent Creator / Curator using Substack, Beehiiv, or similar platforms.

**Journey:**

1. Connect preferred content sources (Twitter, YouTube, RSS).
2. CreatorPulse aggregates insights and detects trending content.
3. Generates a morning newsletter draft in the creator’s voice.
4. User reviews, tweaks, and approves within 20 minutes.
5. Newsletter is delivered via email (or optional WhatsApp).
6. User feedback (👍/👎) refines future drafts.

---

## 📖 Scenarios

* **Morning Workflow:** Creator receives draft at 8:00 AM, reviews, tweaks, and sends.
* **Source Update:** User adds a new Twitter handle or RSS feed to improve content variety.
* **Feedback Loop:** User gives thumbs down on an off-tone paragraph; model adjusts style next day.
* **Deliverability Fix:** Verified sender setup ensures newsletters land in inbox, not spam.

---

## 🕹️ User Flow

* Sign up / log in via web app.
* Connect sources (Twitter handle, YouTube channel, RSS feed).
* Upload past newsletters for style learning.
* System runs scheduled crawls and detects top trends.
* Auto-generates newsletter draft and sends email at 8:00 AM local time.
* User reviews and provides quick feedback.

---

## 🧰 Functional Requirements

| SECTION              | SUB-SECTION             | USER STORY & EXPECTED BEHAVIORS                     | SCREENS |
| -------------------- | ----------------------- | --------------------------------------------------- | ------- |
| Signup               | Email                   | User can sign up using email and verify account     | TBD     |
| Login                | Email                   | User logs in securely                               | TBD     |
| Source Connection    | Twitter / YouTube / RSS | Connect and authenticate sources                    | TBD     |
| Draft Generation     | Daily Email Delivery    | Auto-generated newsletter with trends and summaries | TBD     |
| Feedback Loop        | Reactions               | Inline thumbs up/down improve model over time       | TBD     |
| Dashboard (optional) | Preferences & Billing   | Manage sources, schedule, and usage overview        | TBD     |

---

## 📐 Model Requirements

| SPECIFICATION          | REQUIREMENT                                   | RATIONALE                                         |
| ---------------------- | --------------------------------------------- | ------------------------------------------------- |
| Open vs Proprietary    | Open (e.g., GPT-4/Claude-like)                | Flexibility & cost efficiency                     |
| Context Window         | ≥20K tokens                                   | To hold multiple source summaries + writing style |
| Modalities             | Text                                          | Newsletter-focused                                |
| Fine Tuning Capability | Not needed initially; use in-context learning | Faster MVP iteration                              |
| Latency                | P50 < 10s, P95 < 30s                          | Must feel responsive during draft review          |
| Parameters             | N/A                                           | Lean on hosted LLM APIs                           |

---

## 🧮 Data Requirements

* User uploads 20+ newsletters or posts for voice training.
* System stores curated text snippets from connected sources.
* Data used only for personalization and model improvement (no external sharing).
* Retention: 90 days for source cache; newsletters retained until deletion.

---

## 💬 Prompt Requirements

* Prompts must produce structured newsletter drafts (intro, links, summaries, commentary).
* Include tone/style adaptation from uploaded samples.
* Support fallback tone if insufficient data.
* Ensure refusals or errors gracefully fallback to plain summaries.

---

## 🧪 Testing & Measurement

* **Offline tests:** Use golden set of sample drafts to evaluate tone accuracy (pass if ≥70% match to reference).
* **Online tests:** Track time-to-approval and thumbs feedback.
* **Live metrics:** Monitor open rates and draft acceptance trends.

---

## ⚠️ Risks & Mitigations

| RISK                                          | MITIGATION                                |
| --------------------------------------------- | ----------------------------------------- |
| API rate limits (Twitter/YouTube/newsletters) | Caching, delta crawls, back-off queues    |
| Voice mismatch edges                          | Human-in-loop feedback + retrain path     |
| Trend false positives                         | Ensemble detection + manual override flag |
| Email deliverability                          | Verified sender domains, batch sending    |

---

## 💰 Costs

* **Development:** React frontend, Python backend, Supabase DB, API integrations.
* **Operational:** LLM inference costs, email delivery (e.g., Resend or AWS SES), cloud hosting.

---

## 🔗 Assumptions & Dependencies

* User provides newsletter samples for training.
* Cloud infra uses Supabase and affordable LLM API.
* MVP delivered within 3 months.
* Dashboard is optional and lightweight.

---

## 🔒 Compliance/Privacy/Legal

* No external data resale or sharing.
* GDPR-aligned data retention and deletion options.
* Encrypted storage for user data and source tokens.

---

## 📣 GTM/Rollout Plan (MVP Only)

* **Phase 1:** Private beta (10–20 creators for real-world feedback).
* **Phase 2:** Public MVP with open signup and limited email volume.
* **Phase 3:** Add analytics + agency support in v2.

---

**End of PRD (MVP)**
