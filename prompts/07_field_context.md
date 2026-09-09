# Field Context — optional Phase 7

## Allowed sources
External sources only after paper-only validation and a user-requested extension.

## Required input
Validated analysis and sourced external materials.

## Required output schema
[field_context.schema.json](../schemas/field_context.schema.json). Default generation_status=not_generated; context=[].

## Evidence requirements
Every context object has provenance=external_knowledge, bilingual text and references with source URL and access date. Keep this file separate from paper_analysis.json.

## Task
Provide clearly bounded field context if requested. v0.1 only supplies the interface and UI; no automatic literature search is promised.

## Forbidden behavior
Do not use field context to fill paper omissions, claim unverified novelty or rewrite article findings. Do not show background in Article Only mode.
