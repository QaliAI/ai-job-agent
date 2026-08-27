---
name: score-fit
description: Score candidate fit against target jobs using an explainable 6-factor rubric with explicit strength and gap analysis.
user-invocable: true
allowed-tools: Read, Write, RunCommand
---

# score-fit

Evaluates candidate fit against job postings using transparent, weighted criteria rather than arbitrary LLM percentages.

## Rubric Factors
1. **Title & Role Relevance (25%)**: Title overlap, level, target keyword alignment.
2. **Core Required Skills (25%)**: Proven candidate technologies vs requirements.
3. **Seniority & Experience (15%)**: Years of experience and level expectations.
4. **Domain & Industry Fit (15%)**: Alignment with candidate domain expertise.
5. **Location & Work Mode (10%)**: Remote / hybrid / onsite compatibility.
6. **Preferred Qualifications (10%)**: Transferable skills and nice-to-haves.

## Output Breakdown
* **Score**: 0 to 100
* **Recommendation**: `APPLY` (>=80), `CONSIDER` (65-79), `SKIP` (<65)
* **Proven Matches**: Specific overlapping technical competencies
* **Material Gaps**: Specific requirements candidate profile lacks
* **Hard Disqualifiers**: Immediate blockers (clearance, visa, company blacklist)
