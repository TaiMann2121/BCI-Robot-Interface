# tools

Generate the shareable Word versions in `share/` from the Markdown in `docs/`.
The Markdown is the source of truth; `share/*.docx` are build artifacts.

## Dependency

Both scripts need the `docx` npm package:

```bash
npm install docx
```

Run them from a directory where that package resolves (either install it here,
or run with `NODE_PATH` pointing at an install that has it).

## Usage

`md2docx.js` — generic Markdown to Word. Takes input/output pairs:

```bash
node tools/md2docx.js \
  docs/SUPERVISOR_BRIEF.md share/Physical_Piano_Supervisor_Brief.docx \
  docs/BUILD.md            share/Physical_Piano_Build_Spec.docx \
  docs/TECHSPARK_PLAN.md   share/Physical_Piano_TechSpark_Plan.docx \
  README.md                share/Physical_Piano_Overview.docx
```

It handles headings, paragraphs, lists, tables, fenced code, blockquotes,
horizontal rules, and inline bold / italic / code / links.

`build_bom_docx.js` — the parts list only. It is hand-laid-out rather than
converted, because the BOM wants summary cards and a four-column item table
that Markdown can't express. Writes `Physical_Piano_BOM.docx` to the working
directory; move it into `share/`.

## After editing any doc

Regenerate, or `share/` silently goes stale. The figures in these documents are
cross-referenced (budget totals, key mass limits, heights), so check the numbers
still agree across files after a change.
