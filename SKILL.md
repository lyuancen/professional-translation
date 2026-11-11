---
name: professional-translation
description: Translate, review, and verify Chinese–English professional texts in commercial vehicles, international business, contracts, and corporate governance using the shared Word glossary and targeted authoritative sources.
---

# Professional translation

Use this skill for Chinese→English by default; also support English→Chinese and review of an existing translation. The shared, editable source of terminology is `glossary/English 0928.docx`. Treat its notes as evidence about meaning and scope, not as interchangeable synonyms.

## Before each task

1. Identify direction, domain, document type, audience, and whether the request is **Translate**, **Review**, or **Terminology Check**. Respect definitions and style requirements supplied with the current document.
2. Run `python3 scripts/glossary.py status`, then `python3 scripts/glossary.py search --query '中文或英文术语'` for important terms (`py -3` on Windows). Search the Chinese concepts when translating into English; search English terms when translating into Chinese. Use repeated `--query` arguments for a batch. The script checks the Word file's SHA-256 and automatically rebuilds an external temporary index if changed. A missing source or failed rebuild is an error: disclose it and do not claim the glossary was checked.
3. Read each relevant hit's **full original paragraph and section**. `direct_match` is a retrieval signal, not a translation decision; weaker hits are related candidates. For ambiguous hits, inspect neighboring records with `python3 scripts/glossary.py show --id N --neighbors 2`; compare the source passage and the glossary's usage notes. If a complex paragraph was not safely parsed, use its raw text only and do not infer a word pair mechanically.
4. Make a temporary task-specific terminology map in reasoning, including the chosen form, scope, and unresolved questions. Do not write source text, translations, or task terms into this repository.

## Decision order

Current user instructions → actual source meaning and the document's defined terms → applicable confirmed Word entry → verified authoritative industry or official source → other reliable material and language judgment. This order never overrides technical or legal facts. Preserve distinctions such as dealer/distributor, execute/enter into, advance payment/down payment, homologation/type approval, vehicle telematics/intelligent connected vehicle, and series-production vehicle/mass-produced when the context calls for them. A slash in the Word file does not prove equivalence. If an entry seems misspelled, outdated, or substantively wrong, flag it without changing the Word file. Explain a material conflict before departing from a confirmed entry.

## Targeted verification

Verify terms absent from the Word, ambiguous or high-risk technical/legal terms, and current standards, regulations, or official names. Prefer manufacturers and suppliers' original English technical materials, official standards/regulators, issuer disclosures (especially HKEX for governance), and official legal/trade institutions (such as ICC and UNCITRAL). Read [source guidance](references/source-guidance.md) when choosing a source or dealing with conflicting sources. Search with generic, nonsensitive terms only; never send a complete internal contract, board paper, or technical document to a search service just to check a term. Record URLs and why a term was chosen for material verification; never invent a source. When network access is unavailable, use the Word and existing context, mark online verification as incomplete, and avoid claiming otherwise.

## Complete the selected mode

- **Translate:** Preserve meaning, structure, figures, units, model names, abbreviations, contractual obligations and exceptions. Use natural domain English or Chinese and consistent terms. Independently review the finished translation against the source and task terminology map for omissions, additions, numbers, legal effect, and scope before responding. Default output: clean, ready-to-use translation. Add only concise notes for material ambiguity or unresolved risk.
- **Review:** Compare source and supplied translation independently. Keep sound wording. Report only real issues with original wording, proposed change, and short reason, then give the complete corrected translation. Check glossary conformity, meaning, domain usage, consistency, numbers, and legal/technical effect.
- **Terminology Check:** Show the recommended rendering, relevant Word paragraph/section, contextual distinctions, any necessary verified source links, and the reason. State clearly when a proposed term has no Word entry or online check was unavailable.

For attached DOCX and other document types, use Codex's available document/file capabilities to preserve structure and formatting as far as practical. Put output at the user's requested location or outside this repository; do not save routine translation materials here. Editing the Word source, Git commits, pushes, and repository creation require separate user direction.
