# v0.1 acceptance record

Run: 2026-09-09, macOS, Python 3.9, PyMuPDF 1.26.5, jsonschema 4.25.1, Chromium via Playwright CLI. Source fixture: `examples/demo/paper.pdf`, explicitly synthetic, three pages.

| Criterion | Result | Evidence |
| --- | --- | --- |
| A: PDF → document_index | PASS | Actual PDF parsing test; 3 pages, text blocks with bboxes, 1 figure and 1 table |
| B: formal analysis schema | PASS | Draft 2020-12 validation, required fields and reusable Evidence Blocks |
| C: complete readable demo | PASS | All three provenance states, collected + derived data, connected analysis/results/finding/contribution |
| D: evidence + ID validator | PASS | Positive fixture and deliberate invalid page/status/quote/bbox/section/typed reference mutations |
| E: usable Reader | PASS | Six tabs, bilingual content, original evidence expansion, later-page jump, bbox, zoom, PDF assets, search, atlas, exports |
| F: independent Knowledge Panel | PASS | knowledge_cards.json and field_context.json loaded; Article Only and Background empty-state behavior |
| G: executable Skill | PASS | SKILL.md frontmatter validator; phase instructions, schemas, 7 prompts, CLI implementation |

Python: **38 passed**. Five PyMuPDF/SWIG deprecation warnings were emitted by the dependency under Python 3.9; no test failures.

Evidence validation: **PASS, 0 issues**. This checks schema, source anchoring and reference integrity; it does not prove semantic entailment or exhaustive extraction.

Browser smoke output:

```json
{
  "tabs": 6,
  "originalEvidence": true,
  "evidence": {"page": "3", "scroll": 2096, "highlight": true},
  "zoomAlignment": true,
  "consoleErrors": [],
  "externalRequests": [],
  "pdfPages": 3,
  "search": true,
  "atlas": true,
  "knowledgeMode": true,
  "exports": true
}
```

The first browser pass exposed grid minimum-height overflow, which prevented independent PDF scrolling. The fix constrains grid/flex children to the viewport. Zoom was also corrected to preserve the current page. The full smoke suite passed after both changes.

Visual QA: inspected the synthetic PDF page render and the desktop reader screenshot showing a third-page quote highlighted over the matching sentence. The browser screenshot is produced at `output/playwright/reader-evidence.png` when running from the current repository root (or under the Skill directory when following its README).

Scope limits: no real published-paper end-to-end reasoning run was performed; the demo is a fixture. Automatic OCR, PDF text selection, full figure-boundary detection, online knowledge generation and real-time Q&A are not implemented. These are explicitly disclosed in README/SKILL/UI where relevant.
