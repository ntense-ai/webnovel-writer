# References

This directory contains all reference material for `webnovel-writer`, read by skills and scripts at runtime.

## Directory Structure

| Directory/file | Responsibility | Consumer |
|-------------|------|----------|
| `csv/` | Structured knowledge entries (9 tables) | BM25 search through `reference_search.py` |
| `csv/README.md` | CSV schema specifications and entry rules | Human reference |
| `csv/genre-canonical.md` | Authoritative genre enumeration (canonical + platform_tag mapping) | Human reference + code-constant cross-checks |
| `genre-profiles.md` | Genre profiles (fallback; common genres have moved to Story Contracts) | Read directly by `ContextManager` |
| `reading-power-taxonomy.md` | Reader-retention taxonomy | Read directly by skills |
| `review-schema.md` | Review output format | Read by `webnovel-review` |
| `index/` | Metadata indexes (loading-map, gap-register) | Human reference |
| `outlining/` | Outline references | Read by `webnovel-plan` |
| `review/` | Review references | Read by `webnovel-review` |
| `shared/` | Cross-skill references | Read by multiple skills |

## Markdown vs CSV Boundary

- `md`: workflow specifications, methodology, review schemas, hard constraints, polishing guidance
- `CSV`: writing knowledge, naming rules, scene techniques, and plot templates that can be represented as entries

Markdown provides behavioral gates for language models; CSV provides a searchable knowledge base.

## Consumption Chain

See `index/reference-loading-map.md` for the full `init -> plan -> write -> review` reference-loading path.

## Validation

```bash
cd webnovel-writer/scripts
python validate_csv.py
python validate_csv.py --format json
```
