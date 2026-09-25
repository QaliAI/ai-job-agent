# Multi-Track Opportunity Hunter

The original workflow assumes a candidate has one primary professional identity and is
looking for conventional full-time postings. That model is too narrow for portfolio
operators, consultants, builders, fractional executives, and hybrid business/technical
candidates.

This extension keeps the factual-grounding and claim-check guarantees while allowing one
candidate to pursue several legitimate opportunity lanes at the same time.

## Candidate-private configuration

Personal data remains under `candidate/` and is never committed.

Copy:

```text
templates/OPPORTUNITY_TRACKS_TEMPLATE.json
    -> candidate/OPPORTUNITY_TRACKS.json
```

Then edit only the candidate copy. A track should exist only when the candidate has
evidence to support it.

## What changed

1. Search preferences are parsed by markdown section instead of treating every bullet as
   a possible target title.
2. `OPPORTUNITY_TRACKS.json` defines multiple role/revenue lanes.
3. Search queries are balanced round-robin across tracks.
4. Employer ATS boards are fetched once per company and matched against all configured
   queries locally.
5. The full company registry is scanned by default instead of silently stopping after
   the first 12 companies.
6. The scorer records the best matching opportunity lane without bypassing skills,
   experience, location, or claim-grounding checks.
7. The morning brief surfaces the opportunity lane for each result.

## Recommended lane model

A portfolio operator may reasonably use lanes such as:

- AI Strategy, Transformation & Enablement
- AI Product & Solutions Builder
- Growth, Marketing & AI Automation
- Full-Stack AI Builder
- Fractional / Contract Advisory

Do not score all of these as one giant title list. The point of tracks is to let the same
verified evidence be framed differently depending on the opportunity.

## Discovery layers

### Layer 1 — implemented: direct employer openings

The deterministic pipeline continues to use first-party public ATS feeds and now scans
the entire configured registry efficiently.

### Layer 2 — next: broader technical job coverage

The legacy `QaliAI/ai-job-search` repo already contains a FreeHire adapter that uses
freehire.dev's public API. Reuse or port that adapter rather than rewriting it. Preserve
its upstream attribution and best-effort-service caveats.

### Layer 3 — opt-in: LinkedIn public job discovery

The legacy repo also includes a LinkedIn guest-job search adapter. It should remain
explicitly opt-in because automated access can conflict with LinkedIn's terms. Never
require it for the core workflow.

### Layer 4 — consulting and fractional opportunity signals

Conventional ATS feeds do not capture most consulting demand. Add a separate opportunity
source that can normalize:

- fractional executive networks,
- contract/project marketplaces,
- companies publicly announcing AI adoption or automation initiatives,
- companies hiring multiple AI/automation roles,
- organizations with obvious CRM, lead-response, workflow, or integration pain,
- referrals and warm-network signals.

These records should not pretend to be job postings. Use a distinct opportunity type and
retain source evidence.

## Person targeting model

For each qualified opportunity, identify the person most likely to own the problem:

| Opportunity | Likely owner |
| --- | --- |
| AI transformation / adoption | CEO, COO, CIO, CTO, Chief AI Officer, transformation lead |
| AI product / prototype | CTO, VP Engineering, Head of Product, founder |
| Growth + automation | CMO, CRO, VP Growth, RevOps leader, owner |
| Fractional advisory | founder, CEO, president, operating partner |
| Local service / SMB build | owner, managing partner, GM, marketing leader |

Person targeting is research, not permission to spam. Outreach should stay human-reviewed
and should cite the specific problem/signal that made the person relevant.

## Outcome feedback loop

The next durable layer should learn from actual results:

`found -> qualified -> contacted/applied -> reply -> meeting/interview -> proposal/offer -> won/lost`

Store the outcome, source, track, company, role, contact, and reason. Use aggregate
outcomes to tune track weights and query choices; never rewrite candidate history to fit
what happened.
