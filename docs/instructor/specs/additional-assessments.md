# Spec: Additional Assessment Types

**Scope:** `docs/instructor/assessments/`
**Category:** Pedagogy — QM S3.4 (varied assessment types)
**Issue:** #36

---

## Goal

Provide four supplemental assessment instruments that complement the platform's hands-on practical exams — covering analytical writing, professional communication, synthesis, and peer learning. All instruments are platform-agnostic (Canvas assignments, not new code).

---

## Assessment 1: Security Audit Report

**File:** `docs/instructor/assessments/security-audit-report.md`
**Type:** Individual written assignment
**Bloom's level:** 5 (Evaluate)
**Timing:** After each exam (students write one report per exam section)
**Length:** 400–600 words
**Weight in sample syllabus:** Included in Written Assignments 20%

### Prompt
After completing [OWASP / Blue Team / Red Team] exam mode, write a memo addressed to the fictional NexaCore CISO summarizing your findings as a security analyst. Your memo must:
1. Identify the two most critical vulnerabilities you observed (cite specific exercise IDs)
2. Explain the business risk of each vulnerability in non-technical terms
3. Recommend one mitigation for each, with a rationale for why it is preferred over alternatives
4. Acknowledge one limitation of your analysis (what you could not test in this lab environment)

### Rubric (20 points)
| Criterion | 4 | 3 | 2 | 1 | 0 |
|-----------|---|---|---|---|---|
| Technical accuracy | Correct attack class, mechanism, OWASP category | Minor error in classification | Correct concept, wrong specifics | Significant confusion | Not present |
| Audience appropriateness | No jargon; CISO framing throughout | Mostly accessible; 1–2 jargon terms | Mixed audience; inconsistent framing | Technical throughout; no translation | Not present |
| Evidence from lab | Cites specific exercise IDs + scores | References lab generally | Vague reference to "the exercise" | No lab evidence | Not present |
| Recommendation quality | Mitigation is specific, feasible, prioritized | Mitigation is valid but generic | Mitigation is vague or incomplete | Mitigation is incorrect | Not present |
| Conciseness | 400–600 words; tight prose | 601–750 words or minor padding | 751–900 or significant padding | > 900 or < 300 words | Not submitted |

---

## Assessment 2: Incident Post-Mortem Analysis

**File:** `docs/instructor/assessments/incident-postmortem.md`
**Type:** Individual short-answer (Canvas quiz, 4 questions)
**Bloom's level:** 4 (Analyze)
**Timing:** Week 7 and Week 13 (mid-course and near-end)
**Length:** 100–200 words per question
**Weight:** Included in Written Assignments 20%

### Case Study Format
Instructor selects one published AI security incident (e.g., a documented prompt injection in a deployed assistant). A 300-word case description is provided in the assignment.

### Questions
1. What OWASP LLM Top 10 category does this incident fall under? Justify your classification with two specific details from the case.
2. Which defense mechanism from the labs would have provided the highest coverage against this attack? What is its failure mode in this scenario?
3. What detection signal (log pattern, anomaly metric, or output rule) would have identified this attack earliest in the kill chain?
4. Write one sentence you would add to the affected system's system prompt to reduce the attack surface. Explain the tradeoff introduced by this addition.

### Rubric: same 5-criterion × 4-point scale as the SA rubric in exam_questions.py

---

## Assessment 3: Threat Modeling Group Project

**File:** `docs/instructor/assessments/threat-modeling-project.md`
**Type:** Group project (2–3 students)
**Bloom's level:** 6 (Synthesize)
**Timing:** Weeks 14–15
**Length:** 4–6 page report + 10-minute presentation
**Weight:** Included in Written Assignments 20%

### Prompt
You are the AI security team for a fictional company deploying an LLM-based system. Choose one of the following deployment scenarios:
- A. Customer service chatbot with access to a product knowledge base (RAG)
- B. Internal HR assistant with access to employee policy documents
- C. Code review assistant integrated into the engineering CI/CD pipeline

Produce a threat model using the STRIDE framework that includes:
1. A data flow diagram showing the AI system components (user, LLM, retrieval system, backend APIs)
2. A STRIDE threat table: for each component, list at least one threat per STRIDE category
3. An attack priority matrix: rank the top 5 threats by likelihood × impact (2×2 grid)
4. A defense recommendation for each of the top 5 threats, citing which lab demonstrated the defense
5. One residual risk the team cannot fully mitigate and why

### Rubric (40 points total)
- Data flow diagram: 8 pts (completeness, accuracy of trust boundaries)
- STRIDE table: 12 pts (coverage, specificity, no generic entries)
- Priority matrix: 8 pts (reasoning is explicit, not just gut feel)
- Defense recommendations: 8 pts (cites lab evidence, not just names a control)
- Residual risk: 4 pts (honest, specific, professionally framed)

---

## Assessment 4: Reflection Portfolio

**File:** `docs/instructor/assessments/reflection-portfolio.md`
**Type:** Running Canvas journal (one entry per lab, submitted end of semester)
**Bloom's level:** Metacognitive (evaluating one's own learning process)
**Timing:** One entry due within 3 days of each lab completion
**Length:** 150–250 words per entry
**Weight:** Included in Participation 5%

### Entry Prompt (same for every lab)
1. What was your initial hypothesis about how this attack/defense would work?
2. What surprised you when you ran the actual lab? (cite a specific score or result)
3. What would you do differently if you encountered this scenario in a real job?
4. What one concept from this lab are you still uncertain about?

### Grading
Credit/no-credit per entry (not graded for correctness — graded for honest engagement).
- Full credit: all 4 questions answered, specific lab reference present, submitted on time
- Half credit: 2–3 questions answered or vague
- No credit: not submitted or < 100 words

Portfolio submitted as PDF export of all entries at end of week 15. Instructor reads before writing LORs or advising students.

---

## Expected Outputs

- `docs/instructor/assessments/security-audit-report.md`
- `docs/instructor/assessments/incident-postmortem.md`
- `docs/instructor/assessments/threat-modeling-project.md`
- `docs/instructor/assessments/reflection-portfolio.md`

---

## Acceptance Checks

- [ ] Each rubric sums to a whole-number point total compatible with Canvas grade book
- [ ] Each assessment maps to at least one course SLO from the sample syllabus
- [ ] Rubric criteria are specific enough that two instructors grading the same submission would agree within 1 point per criterion
- [ ] Threat modeling project prompt is solvable using only skills from the 3 live labs (no dependency on unbuilt labs)
- [ ] Incident post-mortem case studies do not use the same NexaCore scenarios as the exam question banks

---

## What Could Go Wrong

- **Group project free-rider problem** — mitigation: include a peer evaluation form (5-point scale, 3 criteria) submitted individually and factored into individual grades.
- **Audit report is too close to the short-answer exam question** — keep them distinct: SA exam asks about lab mechanics; audit report asks about professional communication of findings.
