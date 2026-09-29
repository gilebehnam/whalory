# How to contribute

Thank you for helping. This page covers the four contributions we get most: a false positive, a new linter rule, a new host, and a fix to the references. It also lists the tests to run before a pull request.

Persian speakers can write issues and pull requests in Persian. The maintainers read both languages.

## Contents

- [How this repository works](#how-this-repository-works)
- [Report a false positive](#report-a-false-positive)
- [Propose a linter rule](#propose-a-linter-rule)
- [Add or update a host](#add-or-update-a-host)
- [Fix the references](#fix-the-references)
- [Tests to run](#tests-to-run)
- [Ground rules](#ground-rules)
- [License of your contribution](#license-of-your-contribution)

## How this repository works

The files in this repository are built from the Whalory source by the release build. The build also makes every other package, so a change must work in all of them. When a pull request is accepted, the maintainers carry the change into the source, and it comes back here with the next release. The changelog names you, and your pull request is closed with a link to that release.

Whalory Pro and Studio files are not in this repository. Please don't send Pro content, and don't ask for it in an issue.

## Report a false positive

A false positive is a finding that should not have fired: a correct Persian word marked as misspelt, or a plain sentence called a cliché.

Open a [linter false positive](https://github.com/gilebehnam/whalory/issues/new?template=linter_false_positive.yml) issue with:

1. The shortest text that still triggers the finding. Remove client names and anything you may not share.
2. Your exact command, for example `python skills/whalory/scripts/lint.py sample.txt --format caption`.
3. Its full output line, which includes the rule id, such as `en-buzzword` or `lexicon`.
4. Your version, from `python skills/whalory/scripts/lint.py --version`.
5. Why the text is correct as written. A source helps: a style guide, a dictionary, or the Academy of Persian Language and Literature for Persian spelling.

Until a fix ships, you can wrap intentional examples in `<!-- lint-ignore -->` and `<!-- /lint-ignore -->`.

## Propose a linter rule

A good rule catches a pattern that real copy gets wrong, and stays quiet on copy that is right. Open a [feature request](https://github.com/gilebehnam/whalory/issues/new?template=feature_request.yml) first, so we can agree on the rule before you write code. Include:

- The pattern, in one sentence, and the language it applies to.
- Three or more sentences it should flag, and three or more close cousins it must not flag. The second list matters most.
- A proposed rule id in the house style: lower case with hyphens, and an `en-` prefix for English rules.
- A severity. `error` is for something that is plainly wrong or invented, and `warning` covers the rest.
- A source for any spelling, grammar, or channel limit, with the date you checked it.

For the pull request:

1. Add the rule to `skills/whalory/scripts/lint_en.py` or `skills/whalory/scripts/lint_fa.py`. Use the standard library only, and keep the code valid for Python 3.8.
2. Add test cases. English rules go in the `CASES` list of `scripts/selftest_en.py`, with a case that must fire and a case that must not. Persian rules go in `scripts/selftest.py`; sample files live in `scripts/samples/`.
3. If the rule matches a phrase list, keep each pattern literal or anchored, and check a long input still finishes quickly. The self-tests include a timing check for this.
4. Run `python skills/whalory/scripts/lint.py --rules` and check that the rule and its message appear.

## Add or update a host

A host is an assistant or editor that can load Whalory. Use a [host install problem](https://github.com/gilebehnam/whalory/issues/new?template=host_install.yml) issue for a route that fails, and a feature request for a new host.

We list a host route only with:

- A link to the host's own documentation for skills, plugins, or MCP servers, with the date you read it.
- The exact steps, starting from a clean install.
- A test record: the host's name and version, your operating system, the date, and what worked. Say which parts you checked: the skill loading, the commands, the MCP tools, and the file tools reading your project.

A route counts as tested only with a dated record. Until then, the install guide says it was checked against the documentation.

## Fix the references

The method files and the English and Persian craft files live in `skills/whalory/references/`. When you fix one:

- Keep the English and Persian craft files in step. If you change `references/en/claims.md`, say whether `references/fa/claims.md` needs the same change.
- Give a source and a check date for every limit, rule, or statistic. Mark anything you could not verify as unverified.
- Write the way Whalory asks copy to be written: concrete, no invented facts, and no dash in the middle of a sentence.
- Run the linter on your change: `python skills/whalory/scripts/lint.py <file> --md`.

## Tests to run

You need Python 3.8 or later and nothing else. From the repository root:

```bash
python skills/whalory/scripts/selftest.py
```

This runs the Persian suite, then `selftest_en.py` and `selftest_mcp.py`, and checks that every script still parses as Python 3.8. It prints one line per check and exits with 1 if any check fails. Checks that need a Pro file are skipped, not failed.

Also lint any Markdown you changed:

```bash
python skills/whalory/scripts/lint.py README.md CONTRIBUTING.md --md
```

The CI workflow runs the self-tests for every pull request and every push to `main`. It uses Python 3.8 and 3.14 on Linux, and Python 3.14 on Windows.

## Ground rules

- Python scripts use the standard library only, run on Python 3.8 or later, and make no network calls.
- The MCP server stays read-only. Its file tools read only inside the folders they are given.
- Keep personal data out of samples and issues. Leave out client copy you may not share, and the contact details of real people.
- No invented numbers anywhere, in code comments and docs included. A number needs a source.
- Everyone follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## License of your contribution

By sending a pull request, you agree that your contribution is licensed like the file it changes. That means the [MIT License](LICENSE-MIT) for files in a `scripts/` folder, and [CC BY 4.0](LICENSE-CC-BY-4.0) for everything else. You keep your copyright, and the changelog credits you.
