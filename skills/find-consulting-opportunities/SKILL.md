---
name: find-consulting-opportunities
description: Discover evidence-backed consulting, fractional, advisory, coaching, implementation, and buyer-signal opportunities that are not ordinary job postings.
user-invocable: true
allowed-tools: Read, Write, RunCommand, WebSearch, WebFetch
---

# find-consulting-opportunities

Use this skill when the candidate wants revenue opportunities beyond conventional employment.

## Goal

Find organizations with a **verifiable current signal** that maps to one of the candidate's opportunity tracks, then produce a normalized research lead. Do not infer a need from industry stereotypes alone.

## Good source signals

- a company explicitly announcing an AI, automation, CRM, digital-transformation, or growth initiative;
- a company posting several related implementation roles that indicate an active program;
- a public request for an advisor, fractional executive, trainer, workshop leader, product builder, or automation implementer;
- a project marketplace listing;
- a company publicly describing a manual workflow, integration gap, lead-response problem, or growth-system problem;
- a warm/referral signal provided by the user.

## Required evidence

Every opportunity must include:
- company or organization;
- source and source URL when available;
- dated/current evidence whenever possible;
- the exact signal that makes the opportunity relevant;
- the best matching candidate opportunity lane;
- likely **role categories** that own the problem.

Never invent a person's name, title, email, phone number, budget, or business pain.

## Workflow

1. Read `candidate/MASTER_PROFILE.md`, `candidate/OPPORTUNITY_TRACKS.json`, and `candidate/SEARCH_PREFERENCES.md`.
2. Search public sources for current evidence.
3. Save raw research records using `templates/CONSULTING_OPPORTUNITY_TEMPLATE.json` as the contract.
4. Normalize them with `scripts/opportunity_model.py` or equivalent tool invocation.
5. Generate a brief with `scripts/opportunity_brief.py`.
6. Present opportunities for human review before any contact or application.

## Person targeting

Use the normalized `target_person_roles` as a **research order**, not as proof that a specific person is correct.

Examples:
- AI transformation -> Chief AI Officer, CIO, CTO, COO, transformation leader.
- AI product build -> CTO, VP Engineering, Head of Product, founder.
- Growth / CRM / automation -> CMO, CRO, VP Growth, RevOps leader, founder.
- Fractional advisory -> founder/CEO, president, COO, operating partner.
- Coworking / PropTech -> owner, CEO, COO, CMO, VP Sales.

## Outreach boundary

The skill may prepare a factual draft after the user selects a lead. It must not mass-send messages or fabricate personalization.
