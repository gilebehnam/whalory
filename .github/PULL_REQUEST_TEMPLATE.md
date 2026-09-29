## What this changes

<!-- One or two sentences. Link the issue it closes, for example "Closes #12". -->

## Why

<!-- The problem it solves. For a linter change, name the rule id. -->

## Kind

- [ ] Linter rule, new or changed
- [ ] False-positive fix
- [ ] Reference or playbook text (English, Persian, or both)
- [ ] Host install route or docs
- [ ] Something else

## Before and after

<!-- For a linter change: the findings on the same text before and after your change.
     For a reference change: the sentence before and after. -->

## Checks

- [ ] `python skills/whalory/scripts/selftest.py` passes. Summary line:
- [ ] I linted the Markdown I changed with `python skills/whalory/scripts/lint.py <file> --md`, with no errors.
- [ ] Scripts use the Python standard library only and still run on Python 3.8.
- [ ] Every new limit, spelling rule, or statistic has a source and a check date.
- [ ] English and Persian stay in step, or I explained below why this change is one language only.
- [ ] No client copy, personal data, license keys, or Whalory Pro content.

This repository is built from the Whalory source. If we accept the change, the maintainers carry it into the source. It comes back with the next release, credited in the changelog, and this pull request is closed with a link to that release.
