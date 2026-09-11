# Writing the paper and figures

## The continuous article

Use this order: One-minute Overview (150–250 Chinese characters), Background, Research Gap, Purpose, Research Questions / Hypotheses, Study Setup, Data Collected, How the Data Were Analysed, Findings, Contributions, Limitations, Figures & Tables.

Explain why the problem matters, what is already known, what remains unresolved and what the study attempts. A motivating question is not necessarily a formal RQ. Describe who did what, with which materials, how grouping worked and how long the study lasted. Distinguish people from sessions and collected records from derived variables.

Tell the analysis in order: input → transformation → metric → comparison → output. Explain each method's specific job. Preserve numbers, units, thresholds and qualifications. If the paper gives a rationale, retain it; otherwise say it is not reported. For each finding, connect the observation, numerical support, author interpretation and inferential boundary. Separate author-acknowledged limitations from information you could not locate.

At important claims use short original-language evidence with physical PDF page numbers (starting at 1). Quote text exactly; check the image for extraction errors. Build warnings about quotation differences require review, not a complex certification workflow.

## Figures and tables

For each important visual, display a full readable original crop and caption, then teach:
- Why it exists; its data source and preprocessing.
- The actual axes, units, colors, marks, lines, shaded areas and labels.
- How to read a concrete comparison and what is visibly present.
- Corresponding statistical evidence, author explanation and boundaries.

Do not list absent graphical elements. Say a schematic is not an axis plot and explain its flow. Do not invent observation units, significance or confidence levels. Clearly sourced general principles belong in EXTERNAL notes or cards. Explain table rows/columns and key numbers; wide tables scroll only within their own container. Preserve contradictions, ambiguous thresholds and missing definitions instead of silently repairing the paper.

## One small page-oriented JSON

No schema files or evidence wrappers around every name. The builder accepts these fields:

```json
{
  "paper": {"title": "Paper title", "meta": "Authors · venue"},
  "sections": [{"title": "One-minute Overview", "blocks": [
    {"zh": "中文解释", "en": "Short English digest.",
     "evidence": [{"page": 1, "quote": "Exact original text"}]}
  ]}],
  "knowledge_cards": [],
  "field_position": null
}
```

A block may have `title`, `zh`, `en`, `kind` (default PAPER), `formula` (Unicode/plain text), `flow` (list of strings), `table` (`headers` and `rows`), `evidence`, `details` (nested blocks), `detail_label`, `cards` (knowledge-card keys), and `sources` (`title`/`url`). `details` renders collapsed. Card keys only connect opening controls; there is no research relationship graph.

A section may also include `figures`: each has `title`, `image` (local path relative to content.json), `caption`, and `blocks`. Tables can use the same visual container. Formula text must define variables in surrounding prose; it is not a substitute for a missing author formula. Strings are escaped; do not use raw HTML or Markdown in JSON prose.

`examples/demo/content.json` is a minimal runnable fixture, not a complete scientific reading. For real papers, author the full article rather than inflating this fixture with placeholders.
