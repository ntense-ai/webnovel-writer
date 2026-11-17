# English-only new projects

The `ntense` branch targets English-speaking authors and new book projects.
Project paths, filenames, schema keys, enum identifiers, reference data, prompts,
reports, and dashboard labels use English. Old project layouts and schemas are
not supported, and this branch does not provide migration or legacy mappings.
Do not open an old book expecting automatic conversion; preserve it separately.

Story prose and names may contain Unicode characters. Unicode content does not
change the English identifiers used by the project or command-line tools.
Prose defaults to English and English length is measured in words.

## Layout

Use `chapters/`, `outlines/`, `settings/`, and `reviews/`. Chapter filenames are
`chapter-0001.md`; volume outlines are `volume-1-outline.md`. Use
`project_paths.py --project-root <book-root>` to inspect the paths and
`--path outlines/master-outline.md` to resolve a specific file.

## Reference retrieval

Reference-table guidance, examples, keywords, synonyms, headers, and routing
identifiers use English. For example:

```bash
python webnovel-writer/scripts/reference_search.py --skill write --table techniques --query "dialogue subtext"
python webnovel-writer/scripts/reference_search.py --skill write --table scenes --query "combat description"
```

Table names are `naming`, `scenes`, `techniques`, `tropes`, `pacing`, `characters`,
`powers`, `genre-routing`, and `adjudication`. Retrieval is lexical; arbitrary
synonyms and semantic paraphrases are not guaranteed to match.

## Host adapters

[Codex and Antigravity adapters](../integrations/README.md) reuse this engine.
They do not install Claude hooks or promise native host parity. Mandatory
independent review requires actual host subagent support; unsupported gated
workflows stop rather than inventing reviewer results. Model and host writing
quality require separate validation.

## Multilingual retrieval limits

Story storage accepts Unicode. BM25 uses Unicode normalization and lexical tokens;
CJK, kana and Hangul runs use character/bigram matching rather than a dictionary
segmenter. There is no stemming, translation or guarantee that different-language
queries retrieve equivalent meaning. Embedding/reranking quality depends on the
chosen models. Graph alias extraction and writing-analysis heuristics are not
validated equally across every language. See [index refresh details](../releases/v6.3.1.md).
