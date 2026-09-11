# External knowledge, after the paper

Select concepts by their usefulness to understanding this paper. Prefer original method papers, official documentation, academic books and university material. Read the source before citing; do not treat search snippets, uncited model memory or SEO summaries as verification. Use stable direct links and keep paraphrases concise.

Each compact card shows a name, type and one sentence. Its centered dialog may explain the principle, inputs/outputs, important formula and variables, suitable use and limits. Include a separate PAPER block for this paper's actual use. The dialog's EXTERNAL label covers the background; the PAPER block must never import unsupported implementation details from it.

```json
{
  "id": "example-method",
  "title": "Method name",
  "type": "统计方法",
  "summary": "一句说明它帮助理解什么。",
  "blocks": [{"title": "原理", "zh": "经查证的背景解释"}],
  "paper_usage": {"zh": "本文的实际做法", "evidence": [{"page": 2, "quote": "Exact original text"}]},
  "sources": [{"title": "Original paper or official documentation", "url": "https://example.org/method"}]
}
```

Author-defined metrics need special care: explain the paper's actual definition and state missing details. A standard entropy, distance or effect-size formula is background, not evidence of the implementation used. Do not infer an unreported embedding model from another part of the paper. Distinguish the statistical test's generic assumptions from the author's stated selection rationale.

`field_position` is a short block with `kind: "EXTERNAL"` and sources. Describe the paper's research neighborhood as a synthesis. Keep foundational reading modest; do not create rankings or a literature database. External blocks elsewhere in the article must carry `kind: "EXTERNAL"` and their own sources. Only PAPER, EXTERNAL and NOT REPORTED labels are supported.

All background is written into HTML at build time. Source links may open online when deliberately selected, but page loading, PDF rendering and card opening must stay offline.
