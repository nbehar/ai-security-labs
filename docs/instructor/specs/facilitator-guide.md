# Spec: Facilitator Guides — 3 Live Labs

**Scope:** `spaces/owasp-top-10/`, `spaces/blue-team/`, `spaces/red-team/`
**Category:** Content
**Issue:** #34

---

## Goal

Provide a structured facilitator guide for each of the three live labs so that an instructor with no prior AI security background can deliver the lab confidently in a 90-minute or 3-hour session.

---

## Output Format

Each guide is a single Markdown document published at `spaces/{lab}/docs/facilitator-guide.md` and linked from that space's README. It is NOT student-facing — the guide is for the instructor.

---

## Guide Structure (required sections for each lab)

### 1. At a Glance
- **Learning objectives** (copy from Info tab, verbatim)
- **Prerequisite skills** (what students must know before arriving)
- **Time estimates:** 90-min version (condensed) vs. 3-hour version (full)
- **Materials needed:** browser, no installs required; instructor needs GROQ_API_KEY (or note if model-free)

### 2. Before the Session
- Instructor setup checklist (verify space is running, test one attack, confirm leaderboard resets if needed)
- Recommended pre-reading to assign (1–2 links to real-world incidents this lab is based on)
- Suggested slide outline (titles only — 10–15 slides for 20-min intro lecture)

### 3. Lab Walkthrough (condensed)
- Step-by-step of the happy path a student takes
- Screenshot callouts for the 2–3 UI moments most likely to confuse students
- Correct answers / expected outputs for each exercise (INSTRUCTOR EYES ONLY — do not share)

### 4. Common Student Mistakes
- The 3–5 errors instructors see most often, with diagnostic questions to ask
- "If a student says X, ask them Y" format

### 5. Discussion Prompts (Regular Effective Contact)
- 3 discussion questions timed for mid-lab check-in (satisfies Title 5 § 55204 for DE sections)
- 2 debrief questions for end of session

### 6. Grading Notes
- How the score is calculated (plain English, no formulas)
- What a strong score looks like vs. a minimum-passing score
- How to interpret common score patterns (e.g., high recall + low precision in D1 = student is flagging everything)

### 7. Extension Activities
- 1–2 optional challenges for students who finish early
- Connection to next lab in the course sequence

---

## Lab-Specific Notes

### OWASP Top 10 Lab
- Prerequisites: HTTP basics, what a system prompt is, JSON familiarity
- Key misconception: students think longer prompts are always stronger attacks — address in intro
- Time note: 25 attacks across 5 defenses; 90-min version should scope to OWASP #1, #2, #6 only

### Blue Team Lab
- Prerequisites: regex basics (can be covered in 10-min intro), understanding of WAF concept
- Key misconception: students think more rules = better security; F1 scoring corrects this
- Time note: 4 challenges; 90-min version should scope to WAF Rules + Hardening only

### Red Team Lab
- Prerequisites: prompt injection concept (can come from OWASP lab), jailbreak awareness
- Key misconception: students give up after level 3 thinking it's impossible — address in briefing
- Sensitive content note: Level 4–5 system prompts contain fictional but realistic security scenarios; brief students on the educational framing before they encounter them
- Time note: 5 levels; 90-min version should scope to levels 1–3 only

---

## Expected Outputs

- `spaces/owasp-top-10/docs/facilitator-guide.md`
- `spaces/blue-team/docs/facilitator-guide.md`
- `spaces/red-team/docs/facilitator-guide.md`

Each guide: 800–1200 words, no code blocks, instructor-only framing throughout.

---

## Acceptance Checks

- [ ] Each guide has all 7 required sections
- [ ] Prerequisite skills are explicit (not "basic CS knowledge")
- [ ] Time estimates given for both 90-min and 3-hour formats
- [ ] Common mistakes section has ≥ 3 entries with diagnostic questions
- [ ] Discussion prompts satisfy Title 5 § 55204 (regular effective contact in DE context)
- [ ] Correct answers / expected outputs present (instructor eyes only)
- [ ] Guide reviewed by someone who has not used the lab before (cold-read test)

---

## What Could Go Wrong

- **Guide becomes stale when lab content changes** — facilitator guides must be updated whenever KC questions, scoring formulas, or dataset counts change. Add to Definition of Done for all future lab changes.
- **Instructor shares guide with students** — mark the document header `INSTRUCTOR GUIDE — NOT FOR STUDENT DISTRIBUTION` and exclude from student-facing links.
