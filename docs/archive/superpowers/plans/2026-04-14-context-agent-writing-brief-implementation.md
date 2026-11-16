# Context Agent Writing Brief Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `context-agent` the sole pre-writing entry point. Code prepares only the research working document, and `context-agent` directly writes the final brief for Step 2 following the examples.

**Architecture:** Do not introduce a template renderer. `extract_chapter_context.py` continues assembling the research working document. `context-agent` directly produces the final writing brief from that document, fixed guidelines, and the examples in the documentation. Step 2 of `webnovel-write` consumes only this brief, without adding rules or assembling intermediate blocks itself.

**Tech Stack:** Python 3、pytest、Markdown agent/skill prompt、`webnovel.py` CLI

---

## File Structure

### Modified Files

- `webnovel-writer/scripts/extract_chapter_context.py`
  - Remain a working-document assembler, not a final-text generator
- `webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py`
  - Verify working-document fields and legacy text output
- `webnovel-writer/agents/context-agent.md`
  - Absorb Step 0.5 responsibilities and require direct writing-brief output following the examples
- `webnovel-writer/skills/webnovel-write/SKILL.md`
  - Remove Step 0.5; change Step 2 to consume only the writing brief
- `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`
  - Lock in the new prompt boundaries
- `webnovel-writer/skills/webnovel-write/evals/evals.json`
  - Update workflow expectations
- `docs/guides/commands.md`
  - Update the `/webnovel-write` description

### Deleted Files

- `webnovel-writer/scripts/data_modules/writing_brief_renderer.py`
- `webnovel-writer/scripts/data_modules/tests/test_writing_brief_renderer.py`

---

### Task 1: Remove the renderer approach and restore working-document responsibilities

**Files:**
- Delete: `webnovel-writer/scripts/data_modules/writing_brief_renderer.py`
- Delete: `webnovel-writer/scripts/data_modules/tests/test_writing_brief_renderer.py`
- Modify: `webnovel-writer/scripts/extract_chapter_context.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py`

- [ ] **Step 1: Delete renderer files**

```bash
git rm webnovel-writer/scripts/data_modules/writing_brief_renderer.py
git rm webnovel-writer/scripts/data_modules/tests/test_writing_brief_renderer.py
```

- [ ] **Step 2: Remove renderer calls from `extract_chapter_context.py`**

```python
# webnovel-writer/scripts/extract_chapter_context.py
# Remove:
from data_modules.writing_brief_renderer import render_writer_brief

# Remove:
def _plugin_root() -> Path: ...
def _load_fixed_guides() -> Dict[str, str]: ...
def _extract_book_title(project_root: Path, state: Dict[str, Any]) -> str: ...
def _extract_chapter_title(outline: str, chapter_num: int) -> str: ...

# Keep build_chapter_context_payload as working-document output:
return {
    "chapter": chapter_num,
    "outline": outline,
    "previous_summaries": prev_summaries,
    "state_summary": state_summary,
    "context_contract_version": contract_context.get("context_contract_version"),
    "context_weight_stage": contract_context.get("context_weight_stage"),
    "story_contract": contract_context.get("story_contract", {}),
    "runtime_status": contract_context.get("runtime_status", {}),
    "latest_commit": contract_context.get("latest_commit", {}),
    "prewrite_validation": contract_context.get("prewrite_validation", {}),
    "reader_signal": contract_context.get("reader_signal", {}),
    "genre_profile": contract_context.get("genre_profile", {}),
    "writing_guidance": contract_context.get("writing_guidance", {}),
    "plot_structure": plot_structure,
    "long_term_memory": contract_context.get("long_term_memory", {}),
    "scene": contract_context.get("scene", {}),
    "core": contract_context.get("core", {}),
    "rag_assist": rag_assist,
}
```

- [ ] **Step 3: Remove `writer_brief` tests and restore legacy text-output assertions**

```python
# webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py
# Remove:
def test_build_chapter_context_payload_includes_writer_brief(...): ...
def test_render_text_returns_writer_brief_instead_of_old_audit_sections(...): ...

# Keep:
def test_render_text_contains_writing_guidance_section(...): ...
def test_render_text_contains_contract_first_runtime_section(...): ...
```

- [ ] **Step 4: Run tests to verify that the working-document pipeline is restored**

Run:

```bash
python -m pytest webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py -q --no-cov
```

Expected:

```text
All pass, 0 failures
```

- [ ] **Step 5: Commit this change**

```bash
git add webnovel-writer/scripts/extract_chapter_context.py \
        webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py
git commit -m "refactor: keep chapter context as research draft only"
```

---

### Task 2: Have `context-agent` directly produce the writing brief following examples

**Files:**
- Modify: `webnovel-writer/agents/context-agent.md`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`

- [ ] **Step 1: Add static tests first to lock in example-driven output**

```python
# webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py
def test_context_agent_loads_fixed_guides_and_outputs_writer_brief():
    text = (AGENTS_DIR / "context-agent.md").read_text(encoding="utf-8")
    assert "core-constraints.md" in text
    assert "anti-ai-guide.md" in text
    assert "写作任务书" in text
    assert "### 示例" in text
    assert "你现在要写《凡人修仙传》第47章《坊市试探》。" in text
    assert "Step 2 直写提示词" not in text
    assert "Context Contract" not in text
```

- [ ] **Step 2: Update `context-agent.md`**

```md
### webnovel-writer/agents/context-agent.md

## 8. Output Format

Output only one final writing brief.

Use five fixed sections. The descriptions and examples below explain which data sources to weave into each section.

### 1. Opening Commission
### 2. This Chapter’s Story
### 3. This Chapter’s Characters
### 4. How to Make This Chapter Flow
### 5. Where This Chapter Ends

### Example

You are writing chapter 47, “Testing the Market,” of *A Record of a Mortal’s Journey to Immortality*.
...
Leave readers asking “Who exactly is this person?” as they turn to the next chapter.
```

- [ ] **Step 3: Run static tests**

Run:

```bash
python -m pytest webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py -q --no-cov
```

Expected:

```text
All relevant assertions pass
```

- [ ] **Step 4: Commit this change**

```bash
git add webnovel-writer/agents/context-agent.md \
        webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py
git commit -m "feat: make context agent write briefs from example"
```

---

### Task 3: Consolidate the `/webnovel-write` mainline

**Files:**
- Modify: `webnovel-writer/skills/webnovel-write/SKILL.md`
- Modify: `webnovel-writer/skills/webnovel-write/evals/evals.json`
- Modify: `docs/guides/commands.md`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`

- [ ] **Step 1: Add static tests first to lock in the new workflow**

```python
# webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py
def test_webnovel_write_skill_routes_step2_through_writing_brief():
    text = (SKILLS_DIR / "webnovel-write" / "SKILL.md").read_text(encoding="utf-8")
    assert "写作任务书" in text
    assert "context-agent" in text
    assert "Step 0.5" not in text
    assert 'cat "${SKILL_ROOT}/../../references/shared/core-constraints.md"' not in text
    assert 'cat "${SKILL_ROOT}/references/anti-ai-guide.md"' not in text
```

- [ ] **Step 2: Update `webnovel-write/SKILL.md`**

```md
### Step 1: Call Context Agent to Generate the Writing Brief

### Step 2: Draft the Prose

Hard requirements:
- Step 2 drafts solely from the writing brief generated in Step 1
- Step 2 no longer directly loads `core-constraints.md`
- Step 2 no longer directly loads `anti-ai-guide.md`
- Step 2 no longer assembles intermediate blocks or legacy direct-writing blocks itself
```

- [ ] **Step 3: Update eval and command documentation**

```json
// webnovel-writer/skills/webnovel-write/evals/evals.json
"expected_output": "完成 Step 1 到 Step 6 的完整流程，由 context-agent 先生成写作任务书，再起草第4章正文..."
```

```md
### docs/guides/commands.md

Execute the complete chapter-creation workflow (`context-agent` researches and generates a writing brief → draft from the brief → review → polish → persist data).
```

- [ ] **Step 4: Run static tests**

Run:

```bash
python -m pytest webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py -q --no-cov
```

Expected:

```text
All relevant assertions pass
```

- [ ] **Step 5: Commit this change**

```bash
git add webnovel-writer/skills/webnovel-write/SKILL.md \
        webnovel-writer/skills/webnovel-write/evals/evals.json \
        docs/guides/commands.md \
        webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py
git commit -m "feat: make write step consume only final brief"
```

---

### Task 4: Regression Verification

**Files:**
- Test: `webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py`
- Test: `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`

- [ ] **Step 1: Run regression tests**

Run:

```bash
python -m pytest \
  webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py \
  webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py \
  -q --no-cov
```

Expected:

```text
All pass, 0 failures
```

- [ ] **Step 2: grep self-check**

Run:

```bash
rg -n "Step 0\\.5|writing_brief_renderer|test_writing_brief_renderer|Context Contract|Step 2 直写提示词|cat \\\"\\$\\{SKILL_ROOT\\}/../../references/shared/core-constraints.md\\\"|cat \\\"\\$\\{SKILL_ROOT\\}/references/anti-ai-guide.md\\\"" \
  webnovel-writer \
  docs/guides/commands.md
```

Expected:

```text
No remaining production-code references, apart from historical records in planning documents
```

---

## Coverage Check

This plan covers the current actual approach:

1. Code prepares only the working document
2. `context-agent` writes the brief directly following examples
3. `/webnovel-write` Step 2 consumes only the brief
4. No template renderer is used
5. `anti-ai-guide.md` and `core-constraints.md` remain, but `context-agent` absorbs and rewrites their guidance

## Self-Check

- The template-renderer approach has been removed
- No field-mapping table is required
- Aligned with the current uncommitted implementation direction
