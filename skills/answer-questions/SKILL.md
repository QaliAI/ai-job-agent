---
name: answer-questions
description: Answer job application form questions (e.g. behavioral, challenge resolution, sponsorship) grounded in candidate STAR stories.
user-invocable: true
allowed-tools: Read, Write
---

# answer-questions

Drafts factual, compelling answers to common employer application form questions:
- "Describe a challenging technical problem you solved" (drawn from `candidate/CAREER_STORIES.md`)
- "Why do you want to work at [Company]?" (drawn from candidate domain interests)
- "What are your salary expectations?" (drawn from `candidate/SEARCH_PREFERENCES.md`)
- "Will you now or in the future require visa sponsorship?" (drawn from `candidate/MASTER_PROFILE.md` work authorization)

All answers are strictly factual and grounded in candidate files.
