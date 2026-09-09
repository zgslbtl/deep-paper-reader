# External Knowledge Cards — optional Phase 6

## Allowed sources
Only after paper-only analysis and strict validation pass: user-requested external sources with traceable URLs, alongside separately marked paper usage. v0.1 does not require generating these cards.

## Required input
Validated paper_analysis.json, document_index.json, explicit external-context request, any retrieved source metadata.

## Required output schema
[knowledge_cards.schema.json](../schemas/knowledge_cards.schema.json). Default is generation_status=not_generated and cards=[].

## Task
Use statistical_method, computational_method, theory_or_concept or author_defined_method. Keep paper_usage as an Evidence Block. Definition, plain_explanation, input/process/output, formula, assumptions, theoretical_basis and origin are separately tagged external_knowledge with source references. Preserve related_cards IDs. For author-defined methods, proposed_in_this_paper, how_defined and how_derived refer only to paper evidence; derivation_status=not_reported when derivation is absent.

## Evidence requirements
External assertions require source references and must not be presented as the paper authors’ explanations. Article Only must hide all external text. Validate the JSON again before building.

## Forbidden behavior
Never use textbook rationale to populate paper_rationale. Never invent references, derivations or historical priority. Do not start this phase before the paper-only gate passes.
