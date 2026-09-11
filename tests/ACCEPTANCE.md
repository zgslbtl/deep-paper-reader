# v0.2 acceptance · Bridging AI Prompting and Design Thinking

Verified locally on 2026-09-10/11. The real-paper source and generated Reader remain in ignored `output/`; they are not packaged as the synthetic demo.

## Actual checks

- Chrome 152: direct `file://`, with old 8766 server stopped. Ten original PDF pages render, text layer is present, 2× screen density is respected, zoom rerenders, page input and evidence navigation work. No remote requests or uncaught browser errors observed.
- Safari 26.5.2: native UI inspection of direct local opening, original PDF, 200% zoom, navigation to page 7, evidence jump to page 4, centered CLIP card and Escape/focus restoration. Safari WebDriver was unavailable because remote automation was disabled; no browser security settings were changed. This is native Safari inspection, not a WebKit substitute or a full automated Safari suite.
- Three independent panes at desktop size, 50/35/15 grid; no whole-page horizontal overflow in the Chrome test. Article and PDF positions remain stable after modal closing. All ten cards open/close; Escape returns focus to the card.
- All six figures and two tables load. Original crops were visually reviewed, including legends, labels and the Table 2 statistics. The middle pane intentionally displays reduced images; clicking opens their original size. Crop quality cannot exceed the source PDF's embedded image resolution.
- Fallback: an isolated Chrome test simulates a Worker restriction and checks the visible opening instructions. The actual Python fallback starts on a free loopback port and renders the full ten-page document. Both tested browsers supported ordinary file opening; a naturally restricted browser was not available.
- Five Python tests pass: source preservation, escaped text, invalid resources/pages/URLs, quote warnings, textless extraction and source identity, plus free-port fallback serving. PyMuPDF emits upstream SWIG deprecation warnings, without test failures.
- Skill frontmatter validator passes. `git diff --check` passes.

Run:

```sh
python -m pytest tests/test_reader.py -q
node tests/reader_browser.cjs output/bridging-reader-simple/index.html
node tests/fallback_browser.cjs output/bridging-reader-simple
```

## Content reading review against the 17 questions

This is a Codex reading review against the original PDF and crop images, separate from structural tests. It is not independent human peer review.

| Reading question | Where the article answers it |
| --- | --- |
| 1. Why study this? | Background: polished AI images do not directly establish reflective design activity. |
| 2. What is the gap? | Research Gap: author-reported limits of static prompting and longer-term refinement research. |
| 3. What is the purpose? | Purpose: map transitions into process representations and compare proficiency groups. |
| 4. How was it conducted? | Study Setup: two-week CAD field study, tasks, grouping and filtering, with details collapsed. |
| 5. What did participants do? | Tasks A/B and Figure 1 distinguish practice reference from scene-design task. |
| 6. What data were collected? | Data Collected: anonymized IDs, timestamps, prompts, images; derived variables are separate. |
| 7. How were data processed? | Six ordered analysis steps connect grouping, selection, deltas, codes, metrics and comparisons. |
| 8. What do the methods mean? | Ten knowledge cards provide plain-language principles and important formulas. |
| 9. Why do methods produce these outputs? | Cards explain the mathematics/representations; PAPER usage states only supported implementation. |
| 10. What are the axes? | Each figure walkthrough describes actual axes; Figures 1–3 are explicitly non-axis visuals. |
| 11. What do visual elements mean? | Figures 3–6 explain code symbols, Turn markers, stacked colors and ECDF/shading. |
| 12. What can be seen? | Each walkthrough states visible patterns; representative sessions are not group-level proof. |
| 13. How do results support findings? | Findings and Table 2 connect group differences, numerical support and author interpretation. |
| 14. What is contributed? | Contributions distinguishes representation, empirical comparisons and proposed teaching use. |
| 15. What is unreported? | Limitations and method details identify missing formula/settings, grouping counts and validation. |
| 16. Where is this in the field? | Compact EXTERNAL Field Position connects generative design, design cognition and learning analytics. |
| 17. What should I read next? | Original CLIP/LDM papers, Atman's academic material and sourced statistical cards. |

## Paper-specific checks retained

64 participants were invited; 34 entered analysis. 14 proficient / 35 novice are session counts, not participant counts. CLIP is explicitly used for practice-image scoring; the semantic delta model is not supplied. Mann–Whitney's no-normality rationale is actually reported. Activity entropy p=0.061 is not significant at the table's p<0.05 threshold. CMP marks in Figure 4 contradict the prose; the threshold cross-reference points to a statistics table. Missing formulas remain missing. No 95% level, coding accuracy, causal learning gain or fully reproducible implementation is invented.

## Remaining v0 limits

Recent desktop browsers are the target. Very large PDFs have base64 startup/memory costs; scans need separate OCR, and image quality is capped by the original. Python 3 is needed only for the fallback launcher. Formula display uses Unicode text. Browser policies vary; successful local tests do not guarantee every locked-down device. The builder validates basic inputs and warns about extraction-sensitive quotations; it does not certify scientific entailment or link contents.
