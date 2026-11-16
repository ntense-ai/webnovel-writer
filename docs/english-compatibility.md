# English defaults and compatibility

The `ntense` branch targets English-speaking authors. New projects use English
starter content and filenames in `chapters/`, `outlines/`, `settings/`, and
`reviews/`. Chapter files use `chapter-0001.md`; volume outlines use
`volume-1-outline.md`. Prompts request natural English prose by default, and
English prose is measured in words rather than raw characters.

## Existing books

Existing Chinese directory and file names remain supported. The resolver does
not rename, delete or migrate book content. If both directory spellings exist,
the English directory is preferred; existing files within the selected layout
are discovered before a new default filename is chosen. Do not split a book
between two parallel trees. Back up a book before any manual layout migration.
Legacy chapter headings and outline directives remain readable alongside English
headings. Old state keys, genre identifiers, contract enums and reference-table
identifiers remain stable so existing projects do not require a schema migration.
Their presence in structured records is intentional, not a request to generate
Chinese prose. Historical test fixtures and source template identifiers also remain.

## Reference retrieval

Reference-table guidance, examples, keywords and synonyms are English. CSV
headers, stable IDs and routing metadata retain their established spellings.
Use English aliases rather than needing to type internal table filenames:

```bash
python webnovel-writer/scripts/reference_search.py --skill write --table techniques --query "dialogue subtext"
python webnovel-writer/scripts/reference_search.py --skill write --table scenes --query "combat description"
```

Available aliases are `naming`, `scenes`, `techniques`, `tropes`, `pacing`,
`characters`, `powers`, `genre-routing`, and `adjudication`. Search results expose
English keys `id`, `table`, `summary`, and `instruction`, alongside legacy keys
for existing callers. Use the English fields for author-facing presentation.
An input-only legacy vocabulary index preserves older Chinese keyword queries;
it is not returned as writing guidance. Retrieval is lexical, not a guarantee
that arbitrary synonyms or every semantic paraphrase will match.

## Host adapters

[Codex and Antigravity adapters](../integrations/README.md) reuse this engine.
They do not install Claude hooks or promise identical native host capabilities.
Mandatory independent review still needs real subagents. The adapter stops a
gated workflow when those are unavailable rather than fabricating a review.

Deterministic tests cover paths, schemas, English retrieval, CLI output,
installer layouts and existing-project compatibility. They do not replace
end-to-end writing-quality evaluation in each host with a real model session.
