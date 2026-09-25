---
name: refresh-candidate-brand
description: Rebuild the candidate's base resume, LinkedIn positioning, project portfolio, and lane-specific professional narrative from verified profile evidence.
user-invocable: true
allowed-tools: Read, Write, RunCommand, WebSearch, WebFetch
---

# refresh-candidate-brand

Use this when the candidate's recent projects, consulting work, AI builds, or career direction have changed enough that the base résumé / LinkedIn positioning is stale.

## Source hierarchy

1. `candidate/MASTER_PROFILE.md`
2. `candidate/VERIFIED_ACHIEVEMENTS.md`
3. `candidate/CAREER_STORIES.md`
4. `candidate/skills.json`
5. candidate-provided source documents, including a LinkedIn export or prior résumé
6. candidate-provided portfolio / GitHub URLs
7. public evidence that can be independently verified

Never use an unverified memory or inference as a résumé fact.

## Required outputs

Write to `output/profile/`:

- `base_resume.md` — the strongest general résumé, not tied to one posting;
- `linkedin_headline.md` — one recommended headline plus 2 materially different alternatives;
- `linkedin_about.md` — concise first-person About section;
- `project_portfolio.md` — selected builds with problem, action, stack, and result/evidence;
- `positioning_by_track.md` — how the same verified experience should be emphasized for each configured opportunity track;
- `profile_gaps.md` — missing dates, metrics, credentials, or chronology that must be verified before submission.

## Positioning rules

For hybrid candidates, do **not** flatten the profile into one overloaded identity such as "software engineer / marketer / consultant / everything."

Instead:
1. define a durable umbrella narrative;
2. preserve 3–5 opportunity lanes from `OPPORTUNITY_TRACKS.json`;
3. map the strongest verified evidence to each lane;
4. let application tailoring change emphasis, not history.

Examples of distinct lanes:
- AI transformation / enablement;
- AI product / solutions builder;
- growth + CRM / automation systems;
- fractional advisory / coaching;
- domain-specialist roles such as coworking / PropTech.

## LinkedIn review

When a current LinkedIn export or public profile is available:
- identify stale titles, About copy, services, Featured items, and skills;
- recommend additions from verified recent work;
- recommend Featured links for the strongest working products, talks, publications, demos, and case studies;
- do not claim that a profile change was made unless it was actually made.

## Project evidence

A project is résumé-worthy when it demonstrates at least one of:
- shipped user-facing software;
- AI/agent/automation implementation;
- revenue or operating workflow;
- technical integration;
- measurable business outcome;
- domain expertise;
- client adoption;
- meaningful leadership or decision-making.

Avoid long inventories of experiments. Select the projects that prove the target narrative.

## QA

Before releasing any base résumé or LinkedIn copy:
- run `claim-check`;
- surface every unresolved chronology/metric issue in `profile_gaps.md`;
- never convert system-wide scope into a personal outcome claim without evidence.
