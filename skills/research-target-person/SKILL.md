---
name: research-target-person
description: Research the likely human owner of a verified opportunity and produce an evidence-backed contact hypothesis without guessing identity or contact details.
user-invocable: true
allowed-tools: Read, Write, WebSearch, WebFetch
---

# research-target-person

Use after an opportunity has already been qualified.

## Inputs

- normalized opportunity record;
- target-person role categories from `target_person_roles`;
- company name and source evidence.

## Workflow

1. Start with the highest-priority target-person role category.
2. Search the company's own leadership/team pages first.
3. Use reputable professional/public sources to confirm current title and company.
4. Require at least one source supporting the person's current role.
5. Record only contact information that is publicly provided or obtained through an authorized enrichment source.
6. If no reliable person can be identified, return **unresolved** rather than guessing.

## Output

Return:
- name;
- exact current title;
- company;
- why this person is relevant to the specific opportunity;
- source URL(s);
- confidence: high / medium / unresolved;
- public/authorized contact fields if actually available;
- suggested next action: apply, ask for intro, LinkedIn connection, email draft, or no action.

Never infer private email patterns and never fabricate phone numbers or addresses.
