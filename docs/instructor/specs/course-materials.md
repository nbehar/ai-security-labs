# Spec: Course Materials Package

**Scope:** `docs/instructor/course-materials/`
**Category:** Content
**Issue:** #35

---

## Goal

Provide a complete course materials package that an instructor can adapt in under 4 hours to run a 16-week California Community College 200-level AI Security course using AI Security Labs as the lab component.

---

## Deliverables

### 1. Sample Syllabus (`docs/instructor/course-materials/sample-syllabus.md`)

A fully-populated CCC-format syllabus including:

- **Course prefix/number placeholder:** `CIS 2XX — AI Security Fundamentals` (instructor fills in actual number)
- **Catalog description:** 3 sentences appropriate for submission to a CCC curriculum committee
- **Student Learning Outcomes (SLOs):** 5 SLOs mapped to Bloom's 3–5, aligned to CCC C-ID descriptors where applicable
  1. Identify and classify AI attack vectors using industry taxonomies (OWASP LLM Top 10)
  2. Apply defensive controls to harden LLM-based systems against common attack patterns
  3. Analyze AI system telemetry to detect and characterize attacks
  4. Evaluate tradeoffs between security, usability, and performance in AI system design
  5. Construct professional security documentation (threat models, audit reports, incident post-mortems)
- **Prerequisite statement:** Introduction to Networking OR Introduction to Programming (or equivalent)
- **Required materials:** "No textbook purchase required. All labs run in a browser."
- **Grading breakdown:** Labs 40% · Exams 35% · Written Assignments 20% · Participation 5%
- **Academic integrity policy** referencing the HMAC receipt system
- **ADA/Section 504 accommodation statement** (standard CCC language)
- **Regular Effective Contact policy** (Title 5 § 55204 language for DE sections)
- **Withdrawal / Incomplete policy** (standard CCC language)

### 2. 16-Week Pacing Guide (`docs/instructor/course-materials/pacing-guide.md`)

| Week | Topic | Lab | Assessment Due |
|------|-------|-----|----------------|
| 1 | AI Systems Overview + Threat Landscape | — (orientation) | Pre-assessment diagnostic |
| 2 | Prompt Injection Fundamentals | OWASP Lab (formative) | — |
| 3 | OWASP LLM Top 10 Deep Dive | OWASP Lab (complete) | Lab 1 worksheet |
| 4 | Defense Mechanisms: Hardening + WAF | Blue Team Lab (formative) | — |
| 5 | Blue Team Strategies | Blue Team Lab (complete) | Lab 2 worksheet |
| 6 | Exam 1 (OWASP + Blue Team) | Exam Mode | Exam 1 receipt upload |
| 7 | Adversarial Prompting + Jailbreaks | Red Team Lab (formative) | — |
| 8 | Red Team Techniques | Red Team Lab (complete) | Lab 3 worksheet |
| 9 | Multimodal Attack Surfaces | Multimodal Lab (formative) | — |
| 10 | Multimodal Defense | Multimodal Lab (complete) | Lab 4 worksheet |
| 11 | Exam 2 (Red Team + Multimodal) | Exam Mode | Exam 2 receipt upload |
| 12 | Data Poisoning + RAG Security | Data Poisoning Lab | Lab 5 worksheet |
| 13 | Detection + Monitoring | Detection Lab | Lab 6 worksheet |
| 14 | Threat Modeling Project Workshop | (group work) | Project draft |
| 15 | Project Presentations | — | Final project |
| 16 | Finals Week | Final Exam (all labs) | Final exam receipt + Post-assessment |

### 3. Pre/Post Diagnostic Instrument (`docs/instructor/course-materials/pre-post-diagnostic.md`)

A 10-question diagnostic that measures learning gain across the semester.

**Design constraints:**
- Same 10 questions administered week 1 and week 16
- Bloom's 2–3 (understand + apply) — not Bloom's 4–6 (those are exam questions)
- Scenario-based: each question presents a 2-sentence NexaCore situation
- No AI Security jargon in week-1 version questions — accessible to students with only the prerequisite
- Multiple choice (4 options), machine-scorable
- Published openly (students can see questions); security through content, not secrecy

**Question coverage map:**
| Q | Topic | Lab Connection |
|---|-------|---------------|
| 1 | Identify a prompt injection in a sample exchange | OWASP |
| 2 | Select the best defense for a given threat | Blue Team |
| 3 | Classify an LLM output as safe or dangerous | Detection D3 |
| 4 | Recognize a jailbreak strategy | Red Team |
| 5 | Identify data exfiltration in log entries | Detection D1 |
| 6 | Explain why rate limiting reduces DoS risk | All |
| 7 | Match attack technique to OWASP LLM category | OWASP |
| 8 | Evaluate a WAF rule for false-positive risk | Blue Team |
| 9 | Identify an anomaly in a time-series chart | Detection D2 |
| 10 | Describe one consequence of RAG corpus poisoning | Data Poisoning |

**Scoring + use:** Score is recorded in Canvas (not graded for credit). Gain = (week 16 score − week 1 score) / (10 − week 1 score). Target: ≥ 0.6 normalized gain (consistent with documented interactive engagement learning outcomes in STEM).

### 4. Lab Worksheet Template (`docs/instructor/course-materials/lab-worksheet-template.md`)

A 1-page worksheet structure students fill out during each lab session. Supports writing-across-curriculum requirements common in CCC programs.

Sections:
1. **Hypothesis** (before starting): "I predict that [attack type] will succeed/fail because..."
2. **What I tried** (3–5 bullet observations during the lab)
3. **What the results showed** (score, key metrics)
4. **What I would do differently in a real deployment** (1 paragraph)
5. **One question I still have**

---

## Expected Outputs

- `docs/instructor/course-materials/sample-syllabus.md` (600–900 words)
- `docs/instructor/course-materials/pacing-guide.md` (table + notes)
- `docs/instructor/course-materials/pre-post-diagnostic.md` (10 questions with answer key)
- `docs/instructor/course-materials/lab-worksheet-template.md` (1 page)

---

## Acceptance Checks

- [ ] Syllabus SLOs use Bloom's action verbs and are measurable
- [ ] Pacing guide maps every lab to at least one SLO
- [ ] Pre/post diagnostic reviewed by a second person who has not seen the labs (cold-read for jargon)
- [ ] Diagnostic questions are answerable by a student who has only completed the stated prerequisite (week 1 baseline)
- [ ] Worksheet template reviewed against CCC Writing Across the Curriculum guidelines
- [ ] All documents use plain language (Flesch-Kincaid ≤ grade 12)

---

## What Could Go Wrong

- **Pacing guide assumes all 10 labs are live** — only 3 are live now. Weeks 9–13 content must be marked as "coming soon" and the guide versioned (v1 = 3-lab course, v2 = full 10-lab course).
- **Diagnostic questions leak exam content** — diagnostic covers concepts, not specific lab datasets. Exam questions use different NexaCore scenarios. Keep them distinct.
