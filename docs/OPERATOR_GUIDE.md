# Operator guide — personal job agent setup

Internal notes for someone who sets this up for another person. This is not a sales page.

## What the client supplies

- A resume they are willing to store on the machine that will run the agent
- Target titles, and any titles they will not consider
- Locations and remote / hybrid / on-site preference, if they care
- Salary range, if they want pay used as a filter
- Companies to prefer or skip
- Skills they can defend in an interview
- Work authorization and travel limits, only if they want those stated
- Where the digest should go (file on disk, or an email address they control)
- How many roles they want in a digest (default 10)

They do not have to supply a field they do not want used. Leave it empty.

## What we configure

- A private directory, `profiles/<name>/`, on their machine
- `profile.json` filled only with facts they provided
- Their resume copied into that directory
- Portal on/off, and a fixture path if the first run should stay offline
- A scheduled command: `job-agent run --profile <name>`
- Email environment variables on that machine, if they asked for mail

## What we do not promise

- Interviews, offers, or a particular response rate
- That every live posting is still open. The digest is a research aid
- Auto-apply. The agent never submits an application
- Invented experience. Tailoring only reorders and rephrases the file they gave us
- A hosted multi-tenant product. Each person has a directory on a machine they control
- That a portal will stay up. If credentials or the network are missing, the digest is saved and the run is still a success

## Setup checklist

1. Clone the repo and confirm Python 3.10+.
2. `job-agent init --profile <name>`.
3. Add the resume. Do not paste a different client's files.
4. Fill only the preferences they stated.
5. Leave `portals.enabled` false until they want live boards.
6. `job-agent preflight --profile <name>` and clear every blocker.
7. `job-agent run --profile <name>` and read the digest with them.
8. Show a gap on purpose so they see that missing skills are not hidden.
9. Schedule the daily command.
10. If they want mail, set `notification.to` and the SMTP or Resend variables. Run once with the variables unset and confirm the digest still saves.

## Privacy checklist

- The profile directory stays on their computer
- `profiles/` is gitignored. Do not commit `profile.json`, resumes, `jobs/`, or `output/`
- Do not put their address, phone, or inbox password in the repository or in a shared example
- Email credentials live in the environment, not in git
- Do not copy `jobs/history.json` from one profile into another
- The sample client in `examples/sample-client/` is fiction. Do not mix it with a real resume
- Delete a profile directory when the engagement ends, including `output/applications/`

## Support boundary

We help them run preflight, read a digest, and fix a broken schedule or a missing file.

We do not write applications as them, log into employer sites, or decide that they should apply. We do not add a skill, metric, or employer they did not already document. If claim check flags a draft, the draft is not "cleaned up" with a better-sounding fact. The source profile is corrected only when they supply the missing fact.

## Handoff checklist

- [ ] Profile directory path and the `job-agent` commands written down for them
- [ ] Preflight result is READY
- [ ] One successful `run` output they have opened (digest and `dashboard.html`)
- [ ] They know how to mark a role applied, interviewing, rejected, or archived
- [ ] Schedule is registered, or they know the command if they will run it by hand
- [ ] Mail either works or they have agreed the digest stays on disk
- [ ] They know nothing is submitted without them
- [ ] Repo remotes were not changed. Their private files are not in the commit history
