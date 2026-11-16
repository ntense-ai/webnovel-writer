# Story System Phase 2 Contract-First Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build on the Phase 1 contract seed layer with `VOLUME_BRIEF`, `REVIEW_CONTRACT`, pre-writing prohibitions and disambiguation scopes, outline fulfillment diffs, and a contract-first `context_manager` pack, making planning/writing/review consume contracts first rather than assemble references ad hoc.

**Architecture:** Use `.story-system/*.json` as the sole contract source of truth. Add volume and review contracts to Phase 1 `MASTER_SETTING / CHAPTER_BRIEF / anti_patterns`, splitting the flat Phase 1 aggregation into a schema-based contract family. Runtime follows the fixed priority `chapter -> volume -> master -> old profile/reference fallback`. In this phase, Markdown becomes a read-only rendering of JSON.

**Tech Stack:** Python 3.13, Pydantic, argparse, pytest, unified CLI `webnovel.py`, Markdown + JSON contract artifacts

**Spec:** `docs/superpowers/specs/2026-04-12-story-system-evolution-spec.md`

**Companion Specs:** `docs/superpowers/specs/2026-04-12-webnovel-story-intelligence-system-spec.md`, `docs/superpowers/plans/2026-04-12-story-system-phase1-contract-seed.md`

---

## Scope Split

This plan covers only Phase 2:

1. `VOLUME_BRIEF`
2. `REVIEW_CONTRACT`
3. Pre-writing prohibitions and disambiguation scopes
4. Outline fulfillment diff
5. `context_manager` contract-first pack

Explicit non-goals:

- Do not introduce `CHAPTER_COMMIT`
- Do not change post-writing persistence to commit-driven operation
- Do not establish a canonical event log
- Do not expand or migrate the override ledger

Exit criteria for this phase:

1. `MASTER / VOLUME / CHAPTER / REVIEW` all have stable JSON schemas
2. `context_manager` outputs packs in contract-priority order
3. Pre-writing can produce `prewrite_validation` and `fulfillment_seed`
4. The default read order of `webnovel-plan` / `webnovel-write` / `webnovel-review` is contract-first
5. `genre-profiles.md` and legacy references serve only as fallbacks, not peer sources of truth for system decisions

Reuse the `Story System` documentation sections established in Phase 1:

- Phase 2 adds only `contract-first runtime`, `VOLUME_BRIEF`, and `REVIEW_CONTRACT`
- Do not restructure `README.md / overview.md / commands.md`

---

## File Structure

### Files to Create

- `webnovel-writer/scripts/data_modules/story_contract_schema.py`
- `webnovel-writer/scripts/data_modules/runtime_contract_builder.py`
- `webnovel-writer/scripts/data_modules/prewrite_validator.py`
- `webnovel-writer/scripts/data_modules/tests/test_story_contract_schema.py`
- `webnovel-writer/scripts/data_modules/tests/test_runtime_contract_builder.py`
- `webnovel-writer/scripts/data_modules/tests/test_prewrite_validator.py`
- `docs/architecture/story-system-phase2.md`

### Files to Modify

- `webnovel-writer/scripts/data_modules/story_contracts.py`
- `webnovel-writer/scripts/data_modules/story_system_engine.py`
- `webnovel-writer/scripts/story_system.py`
- `webnovel-writer/scripts/data_modules/context_manager.py`
- `webnovel-writer/scripts/data_modules/tests/test_context_manager.py`
- `webnovel-writer/scripts/extract_chapter_context.py`
- `webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py`
- `webnovel-writer/scripts/chapter_outline_loader.py`
- `webnovel-writer/scripts/data_modules/webnovel.py`
- `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`
- `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`
- `webnovel-writer/skills/webnovel-plan/SKILL.md`
- `webnovel-writer/skills/webnovel-write/SKILL.md`
- `webnovel-writer/skills/webnovel-review/SKILL.md`
- `README.md`
- `docs/architecture/overview.md`
- `docs/guides/commands.md`
- `docs/superpowers/README.md`

### File Responsibilities

- `story_contract_schema.py`: Pydantic schemas and version metadata for `MASTER_SETTING / VOLUME_BRIEF / CHAPTER_BRIEF / REVIEW_CONTRACT`
- `runtime_contract_builder.py`: generate `VOLUME_BRIEF` and `REVIEW_CONTRACT` from the Phase 1 seed, volume range, outline structure, and plot structure
- `prewrite_validator.py`: pre-writing prohibition checks, disambiguation-scope construction, fulfillment seeds, and must-check lists
- `story_contracts.py`: add `volumes/` and `reviews/` paths, write JSON sources of truth, and rebuild read-only Markdown
- `context_manager.py`: use contract-first pack assembly by default
- `skills/*/SKILL.md`: switch runtime entry points to generate/read contracts before writing or reviewing

---

## Task 1: Establish Phase 2 Contract Schemas and Directory Extensions

**Files:**
- Create: `webnovel-writer/scripts/data_modules/story_contract_schema.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_story_contract_schema.py`
- Modify: `webnovel-writer/scripts/data_modules/story_contracts.py`

- [ ] **Step 1: Write failing schema tests first**

```python
# webnovel-writer/scripts/data_modules/tests/test_story_contract_schema.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest

from data_modules.story_contract_schema import ChapterBrief, MasterSetting, ReviewContract, VolumeBrief


def test_master_setting_and_chapter_brief_accept_phase1_seed_shape():
    master = MasterSetting.model_validate(
        {
            "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING"},
            "route": {"primary_genre": "玄幻退婚流"},
            "master_constraints": {"core_tone": "先压后爆", "pacing_strategy": "三章内首个反打"},
            "base_context": [],
            "source_trace": [],
            "override_policy": {"locked": ["route.primary_genre"], "append_only": ["anti_patterns"], "override_allowed": []},
        }
    )
    chapter = ChapterBrief.model_validate(
        {
            "meta": {"schema_version": "story-system/v1", "contract_type": "CHAPTER_BRIEF"},
            "override_allowed": {"chapter_focus": "退婚现场反打"},
            "dynamic_context": [],
            "source_trace": [],
        }
    )
    assert master.route["primary_genre"] == "玄幻退婚流"
    assert chapter.override_allowed["chapter_focus"] == "退婚现场反打"


def test_volume_brief_requires_selected_fields():
    payload = {
        "meta": {"schema_version": "story-system/v1", "contract_type": "VOLUME_BRIEF"},
        "volume_goal": {"summary": "卷一站稳脚跟"},
        "selected_tropes": ["退婚反击"],
        "selected_pacing": {"wave": "压抑后爆"},
        "selected_scenes": ["宗门大厅", "资源争夺"],
        "anti_patterns": ["配角抢主角兑现"],
        "system_constraints": ["金手指每日限一次"],
        "overrides": {"locked": {}, "append_only": {}, "override_allowed": {}},
    }
    model = VolumeBrief.model_validate(payload)
    assert model.volume_goal["summary"] == "卷一站稳脚跟"


def test_review_contract_requires_blocking_rules_list():
    with pytest.raises(Exception):
        ReviewContract.model_validate(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "REVIEW_CONTRACT"},
                "must_check": ["mandatory_nodes"],
                "blocking_rules": "not-a-list",
                "genre_specific_risks": [],
                "anti_patterns": [],
                "system_constraints": [],
                "review_thresholds": {"blocking_count": 0},
                "overrides": {"locked": {}, "append_only": {}, "override_allowed": {}},
            }
        )
```

- [ ] **Step 2: Run tests and confirm failures**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_contract_schema.py -q --no-cov`

Expected: `ModuleNotFoundError: No module named 'data_modules.story_contract_schema'`

- [ ] **Step 3: Implement Phase 2 schemas and directory paths**

```python
# webnovel-writer/scripts/data_modules/story_contract_schema.py
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ContractMeta(BaseModel):
    schema_version: str = "story-system/v1"
    contract_type: str
    generator_version: str = "phase2"
    source_trace: List[Dict[str, Any]] = Field(default_factory=list)


class OverrideBundle(BaseModel):
    locked: Dict[str, Any] = Field(default_factory=dict)
    append_only: Dict[str, Any] = Field(default_factory=dict)
    override_allowed: Dict[str, Any] = Field(default_factory=dict)


class MasterSetting(BaseModel):
    meta: ContractMeta
    route: Dict[str, Any] = Field(default_factory=dict)
    master_constraints: Dict[str, Any] = Field(default_factory=dict)
    base_context: List[Dict[str, Any]] = Field(default_factory=list)
    source_trace: List[Dict[str, Any]] = Field(default_factory=list)
    override_policy: Dict[str, List[str]] = Field(default_factory=dict)


class ChapterBrief(BaseModel):
    meta: ContractMeta
    override_allowed: Dict[str, Any] = Field(default_factory=dict)
    dynamic_context: List[Dict[str, Any]] = Field(default_factory=list)
    source_trace: List[Dict[str, Any]] = Field(default_factory=list)


class VolumeBrief(BaseModel):
    meta: ContractMeta
    volume_goal: Dict[str, Any]
    selected_tropes: List[str] = Field(default_factory=list)
    selected_pacing: Dict[str, Any] = Field(default_factory=dict)
    selected_scenes: List[str] = Field(default_factory=list)
    anti_patterns: List[str] = Field(default_factory=list)
    system_constraints: List[str] = Field(default_factory=list)
    overrides: OverrideBundle = Field(default_factory=OverrideBundle)


class ReviewContract(BaseModel):
    meta: ContractMeta
    must_check: List[str] = Field(default_factory=list)
    blocking_rules: List[str] = Field(default_factory=list)
    genre_specific_risks: List[str] = Field(default_factory=list)
    anti_patterns: List[str] = Field(default_factory=list)
    system_constraints: List[str] = Field(default_factory=list)
    review_thresholds: Dict[str, Any] = Field(default_factory=dict)
    overrides: OverrideBundle = Field(default_factory=OverrideBundle)
```

Keep `blocking_rules` as `List[str]` in Phase 2 to avoid premature schema complexity. Explicitly document it as **a placeholder that may become `List[BlockingRule]` in Phase 5**; add structure later if severity, source, and matching patterns are needed.

- [ ] **Step 4: Extend volume/review paths in `story_contracts.py`**

```python
# webnovel-writer/scripts/data_modules/story_contracts.py
@property
def volumes_dir(self) -> Path:
    return self.root / "volumes"

@property
def reviews_dir(self) -> Path:
    return self.root / "reviews"

def volume_json(self, volume: int) -> Path:
    return self.volumes_dir / f"volume_{volume:03d}.json"

def review_json(self, chapter: int) -> Path:
    return self.reviews_dir / f"chapter_{chapter:03d}.review.json"
```

- [ ] **Step 5: Rerun tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_story_contract_schema.py -q --no-cov`

Expected: Pass

- [ ] **Step 6: Commit**

```bash
git add webnovel-writer/scripts/data_modules/story_contract_schema.py \
        webnovel-writer/scripts/data_modules/story_contracts.py \
        webnovel-writer/scripts/data_modules/tests/test_story_contract_schema.py
git commit -m "feat: add phase2 contract schemas and paths"
```

---

## Task 2: Generate `VOLUME_BRIEF` and `REVIEW_CONTRACT`

**Files:**
- Create: `webnovel-writer/scripts/data_modules/runtime_contract_builder.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_runtime_contract_builder.py`
- Modify: `webnovel-writer/scripts/data_modules/story_system_engine.py`
- Modify: `webnovel-writer/scripts/data_modules/story_contracts.py`
- Modify: `webnovel-writer/scripts/story_system.py`
- Modify: `webnovel-writer/scripts/chapter_outline_loader.py`

- [ ] **Step 1: Write generator tests first**

```python
# webnovel-writer/scripts/data_modules/tests/test_runtime_contract_builder.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from data_modules.runtime_contract_builder import RuntimeContractBuilder


def test_runtime_contract_builder_creates_volume_and_review_contracts(tmp_path):
    project_root = tmp_path
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text(
        json.dumps(
            {
                "progress": {"volumes_planned": [{"volume": 1, "chapters_range": "1-20"}]},
                "chapter_meta": {},
                "disambiguation_pending": [],
                "disambiguation_warnings": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (project_root / ".story-system" / "MASTER_SETTING.json").parent.mkdir(parents=True, exist_ok=True)
    (project_root / ".story-system" / "MASTER_SETTING.json").write_text(
        json.dumps(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING"},
                "route": {"primary_genre": "玄幻退婚流"},
                "master_constraints": {"core_tone": "先压后爆"},
                "base_context": [],
                "source_trace": [],
                "override_policy": {"locked": ["route.primary_genre"], "append_only": ["anti_patterns"], "override_allowed": []},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (project_root / ".story-system" / "anti_patterns.json").write_text(
        json.dumps([{"text": "配角不能抢主角兑现"}], ensure_ascii=False),
        encoding="utf-8",
    )
    (project_root / "大纲").mkdir(parents=True, exist_ok=True)
    (project_root / "大纲" / "第1卷-详细大纲.md").write_text(
        "### 第3章：试压\\nCBN：继续压迫\\n必须覆盖节点：发现陷阱、决定隐忍\\n本章禁区：不可提前摊牌",
        encoding="utf-8",
    )

    builder = RuntimeContractBuilder(project_root)
    volume_brief, review_contract = builder.build_for_chapter(3)

    assert volume_brief["meta"]["contract_type"] == "VOLUME_BRIEF"
    assert review_contract["meta"]["contract_type"] == "REVIEW_CONTRACT"
    assert "发现陷阱" in review_contract["must_check"]
    assert "不可提前摊牌" in review_contract["blocking_rules"]
```

- [ ] **Step 2: Run and confirm failing tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_runtime_contract_builder.py -q --no-cov`

Expected: `ModuleNotFoundError: No module named 'data_modules.runtime_contract_builder'`

- [ ] **Step 3: Implement the generator**

```python
# webnovel-writer/scripts/data_modules/runtime_contract_builder.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from chapter_outline_loader import load_chapter_plot_structure, volume_num_for_chapter_from_state

from data_modules.story_contract_schema import MasterSetting, ReviewContract, VolumeBrief


class RuntimeContractBuilder:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def build_for_chapter(self, chapter: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        master = self._load_master_setting()
        anti_patterns = self._load_anti_patterns()
        plot = self._load_plot_structure(chapter)
        volume = self._resolve_volume(chapter)

        volume_brief = VolumeBrief.model_validate(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "VOLUME_BRIEF"},
                "volume_goal": {"summary": f"第{volume}卷延续 {master.route.get('primary_genre', '')} 的主冲突"},
                "selected_tropes": [master.route.get("primary_genre", "")],
                "selected_pacing": {"wave": master.master_constraints.get("pacing_strategy", "")},
                "selected_scenes": list(plot.get("cpns") or []),
                "anti_patterns": [row.get("text", "") for row in anti_patterns if row.get("text")],
                "system_constraints": [master.master_constraints.get("core_tone", "")],
                "overrides": {"locked": {}, "append_only": {}, "override_allowed": {}},
            }
        ).model_dump()
        review_contract = ReviewContract.model_validate(
            {
                "meta": {"schema_version": "story-system/v1", "contract_type": "REVIEW_CONTRACT"},
                "must_check": list(plot.get("mandatory_nodes") or []),
                "blocking_rules": list(plot.get("prohibitions") or []),
                "genre_specific_risks": [master.route.get("primary_genre", "")],
                "anti_patterns": volume_brief["anti_patterns"],
                "system_constraints": volume_brief["system_constraints"],
                "review_thresholds": {"blocking_count": 0, "missed_nodes": 0},
                "overrides": {"locked": {}, "append_only": {}, "override_allowed": {}},
            }
        ).model_dump()
        return volume_brief, review_contract

    def _load_master_setting(self) -> MasterSetting:
        raw = json.loads((self.project_root / ".story-system" / "MASTER_SETTING.json").read_text(encoding="utf-8"))
        return MasterSetting.model_validate(raw)

    def _load_anti_patterns(self) -> list[Dict[str, Any]]:
        raw = json.loads((self.project_root / ".story-system" / "anti_patterns.json").read_text(encoding="utf-8"))
        return list(raw or [])

    def _load_plot_structure(self, chapter: int) -> Dict[str, Any]:
        raw = load_chapter_plot_structure(self.project_root, chapter) or {}
        return {
            "mandatory_nodes": list(raw.get("mandatory_nodes") or []),
            "prohibitions": list(raw.get("prohibitions") or []),
            "cpns": list(raw.get("cpns") or []),
        }

    def _resolve_volume(self, chapter: int) -> int:
        return volume_num_for_chapter_from_state(self.project_root, chapter) or 1
```

- [ ] **Step 4: Add a `build-runtime-contracts` entry point to `story_system.py`**

```python
# webnovel-writer/scripts/data_modules/story_contracts.py
from chapter_outline_loader import volume_num_for_chapter_from_state


def persist_runtime_contracts(project_root: Path, chapter: int, volume_brief: dict, review_contract: dict) -> None:
    paths = StoryContractPaths.from_project_root(project_root)
    volume = volume_num_for_chapter_from_state(project_root, chapter) or 1
    paths.volumes_dir.mkdir(parents=True, exist_ok=True)
    paths.reviews_dir.mkdir(parents=True, exist_ok=True)
    write_json(paths.volume_json(volume), volume_brief)
    write_json(paths.review_json(chapter), review_contract)

# webnovel-writer/scripts/story_system.py
parser.add_argument("--emit-runtime-contracts", action="store_true")

if args.emit_runtime_contracts:
    builder = RuntimeContractBuilder(project_root)
    volume_brief, review_contract = builder.build_for_chapter(args.chapter)
    persist_runtime_contracts(project_root, args.chapter, volume_brief, review_contract)
```

- [ ] **Step 5: Rerun tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_runtime_contract_builder.py -q --no-cov`

Expected: Pass

- [ ] **Step 6: Commit**

```bash
git add webnovel-writer/scripts/data_modules/runtime_contract_builder.py \
        webnovel-writer/scripts/data_modules/tests/test_runtime_contract_builder.py \
        webnovel-writer/scripts/data_modules/story_contracts.py \
        webnovel-writer/scripts/story_system.py \
        webnovel-writer/scripts/chapter_outline_loader.py
git commit -m "feat: generate volume brief and review contract"
```

---

## Task 3: Pre-writing Prohibitions, Disambiguation Scopes, and Outline Fulfillment Diffs

**Files:**
- Create: `webnovel-writer/scripts/data_modules/prewrite_validator.py`
- Create: `webnovel-writer/scripts/data_modules/tests/test_prewrite_validator.py`
- Modify: `webnovel-writer/scripts/data_modules/context_manager.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_context_manager.py`

- [ ] **Step 1: Write failing `prewrite_validator` tests first**

```python
# webnovel-writer/scripts/data_modules/tests/test_prewrite_validator.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

from data_modules.prewrite_validator import PrewriteValidator


def test_prewrite_validator_builds_disambiguation_domain_and_fulfillment_seed(tmp_path):
    project_root = tmp_path
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text(
        json.dumps(
            {
                "disambiguation_pending": [],
                "disambiguation_warnings": [{"mention": "宗主"}],
                "chapter_meta": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    review_contract = {"must_check": ["发现陷阱"], "blocking_rules": ["不可提前摊牌"]}
    plot_structure = {"mandatory_nodes": ["发现陷阱"], "prohibitions": ["不可提前摊牌"]}

    payload = PrewriteValidator(project_root).build(chapter=3, review_contract=review_contract, plot_structure=plot_structure)

    assert payload["blocking"] is False
    assert payload["fulfillment_seed"]["planned_nodes"] == ["发现陷阱"]
    assert payload["disambiguation_domain"]["pending_count"] == 0
```

- [ ] **Step 2: Run and confirm failing tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_prewrite_validator.py -q --no-cov`

Expected: `ModuleNotFoundError: No module named 'data_modules.prewrite_validator'`

- [ ] **Step 3: Implement the pre-writing validator**

```python
# webnovel-writer/scripts/data_modules/prewrite_validator.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class PrewriteValidator:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)

    def build(self, chapter: int, review_contract: Dict[str, Any], plot_structure: Dict[str, Any]) -> Dict[str, Any]:
        state = json.loads((self.project_root / ".webnovel" / "state.json").read_text(encoding="utf-8"))
        pending = state.get("disambiguation_pending") or []
        warnings = state.get("disambiguation_warnings") or []
        return {
            "chapter": chapter,
            "blocking": bool(pending),
            "blocking_reasons": ["存在高优先级 disambiguation_pending"] if pending else [],
            "forbidden_zones": list(review_contract.get("blocking_rules") or []),
            "disambiguation_domain": {
                "pending_count": len(pending),
                "warning_count": len(warnings),
                "allowed_mentions": [item.get("mention", "") for item in warnings if item.get("mention")],
            },
            "fulfillment_seed": {
                "planned_nodes": list(plot_structure.get("mandatory_nodes") or []),
                "prohibitions": list(plot_structure.get("prohibitions") or []),
            },
        }
```

- [ ] **Step 4: Add a `prewrite_validation` section to `context_manager`**

```python
# webnovel-writer/scripts/data_modules/context_manager.py
SECTION_ORDER = [
    "core",
    "story_contract",
    "prewrite_validation",
    "scene",
    "global",
    "reader_signal",
    "genre_profile",
    "writing_guidance",
    "plot_structure",
    "story_skeleton",
    "memory",
    "long_term_memory",
    "preferences",
    "alerts",
]

validator = PrewriteValidator(self.config.project_root)
pack["prewrite_validation"] = validator.build(
    chapter=chapter,
    review_contract=story_contract.get("review_contract") or {},
    plot_structure=plot_structure,
)
```

- [ ] **Step 5: Rerun tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_prewrite_validator.py webnovel-writer/scripts/data_modules/tests/test_context_manager.py -q --no-cov`

Expected: Pass

- [ ] **Step 6: Commit**

```bash
git add webnovel-writer/scripts/data_modules/prewrite_validator.py \
        webnovel-writer/scripts/data_modules/tests/test_prewrite_validator.py \
        webnovel-writer/scripts/data_modules/context_manager.py \
        webnovel-writer/scripts/data_modules/tests/test_context_manager.py
git commit -m "feat: add prewrite validation and fulfillment seed"
```

---

## Task 4: Switch Runtime to Contract-First and Integrate Skills / CLI

**Files:**
- Modify: `webnovel-writer/scripts/extract_chapter_context.py`
- Modify: `webnovel-writer/scripts/data_modules/webnovel.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py`
- Modify: `webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py`
- Modify: `webnovel-writer/skills/webnovel-plan/SKILL.md`
- Modify: `webnovel-writer/skills/webnovel-write/SKILL.md`
- Modify: `webnovel-writer/skills/webnovel-review/SKILL.md`

- [ ] **Step 1: Add contract-first read-order tests first**

Add more robust step-block assertions to `test_prompt_integrity.py` rather than bare substring checks:

```python
def test_story_system_runtime_contract_commands_exist():
    import re

    text = Path("webnovel-writer/skills/webnovel-write/SKILL.md").read_text(encoding="utf-8")
    block = re.search(r"story-system[\\s\\S]+--emit-runtime-contracts[\\s\\S]+REVIEW_CONTRACT", text)
    assert block, "webnovel-write skill 必须包含生成 runtime contracts 的完整步骤块"
```

Add to `test_webnovel_unified_cli.py`:

```python
def test_webnovel_story_system_runtime_forwards(monkeypatch, tmp_path):
    from data_modules import webnovel as cli
    project_root = tmp_path / "book"
    (project_root / ".webnovel").mkdir(parents=True, exist_ok=True)
    (project_root / ".webnovel" / "state.json").write_text("{}", encoding="utf-8")
    called = {}

    def _fake_run_script(script_name, argv):
        called["script_name"] = script_name
        called["argv"] = argv
        return 0

    monkeypatch.setattr(cli, "_run_script", _fake_run_script)
    monkeypatch.setattr(sys, "argv", ["webnovel", "--project-root", str(project_root), "story-system", "玄幻退婚流", "--emit-runtime-contracts"])
    cli.main()

    assert called["script_name"] == "story_system.py"
    assert "--emit-runtime-contracts" in called["argv"]
```

- [ ] **Step 2: Run and confirm failing tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py -q --no-cov`

Expected: The new assertions fail

- [ ] **Step 3: Update skills and the text-extraction script**

Insert the same Phase 2 prerequisite step into all three skills:

```bash
python -X utf8 "${SCRIPTS_DIR}/webnovel.py" --project-root "${WORKSPACE_ROOT}" \
  story-system "{chapter_goal}" --chapter {chapter_num} --persist --emit-runtime-contracts --format both
```

Also output the following from `extract_chapter_context.py`:

```python
story_contract = contract_context.get("story_contract") or {}
review_contract = story_contract.get("review_contract") or {}
prewrite_validation = payload.get("prewrite_validation") or {}

lines.append("## Contract-First Runtime")
lines.append(f"- Review blocking rules: {len(review_contract.get('blocking_rules') or [])}")
lines.append(f"- Prewrite blocking: {prewrite_validation.get('blocking')}")
```

- [ ] **Step 4: Rerun tests**

Run: `python -m pytest webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py -q --no-cov`

Expected: Pass

- [ ] **Step 5: Commit**

```bash
git add webnovel-writer/scripts/extract_chapter_context.py \
        webnovel-writer/scripts/data_modules/webnovel.py \
        webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py \
        webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py \
        webnovel-writer/skills/webnovel-plan/SKILL.md \
        webnovel-writer/skills/webnovel-write/SKILL.md \
        webnovel-writer/skills/webnovel-review/SKILL.md
git commit -m "feat: switch runtime entrypoints to contract-first flow"
```

---

## Task 5: Documentation Updates and Phase 2 Regression Validation

**Files:**
- Create: `docs/architecture/story-system-phase2.md`
- Modify: `README.md`
- Modify: `docs/architecture/overview.md`
- Modify: `docs/guides/commands.md`
- Modify: `docs/superpowers/README.md`

- [ ] **Step 1: Create Phase 2 architecture documentation**

`docs/architecture/story-system-phase2.md` must include at least:

```markdown
# Story System Phase 2

## Contract Source of Truth
- `MASTER_SETTING.json`
- `volumes/volume_XXX.json`
- `chapters/chapter_XXX.json`
- `reviews/chapter_XXX.review.json`

## Runtime Order
1. chapter brief
2. volume brief
3. master setting
4. fallback references

## Pre-Writing Validation
- forbidden zones
- disambiguation domain
- fulfillment seed

## Non-Goals
- Do not introduce `CHAPTER_COMMIT`
- Do not introduce a canonical event log
```

- [ ] **Step 2: Update command documentation**

Add to `docs/guides/commands.md`:

```bash
python -X utf8 "<CLAUDE_PLUGIN_ROOT>/scripts/webnovel.py" \
  --project-root "<WORKSPACE_ROOT>" \
  story-system "玄幻退婚流" --chapter 3 --persist --emit-runtime-contracts --format both
```

- [ ] **Step 3: Run the minimal Phase 2 validation suite**

Run:

```bash
python -m pytest \
  webnovel-writer/scripts/data_modules/tests/test_story_contract_schema.py \
  webnovel-writer/scripts/data_modules/tests/test_runtime_contract_builder.py \
  webnovel-writer/scripts/data_modules/tests/test_prewrite_validator.py \
  webnovel-writer/scripts/data_modules/tests/test_context_manager.py \
  webnovel-writer/scripts/data_modules/tests/test_extract_chapter_context.py \
  webnovel-writer/scripts/data_modules/tests/test_webnovel_unified_cli.py \
  webnovel-writer/scripts/data_modules/tests/test_prompt_integrity.py \
  -q --no-cov
```

Expected: All pass

- [ ] **Step 4: Regression-test `reference_search.py`**

Run: `python -m pytest webnovel-writer/scripts/tests/test_reference_search.py -q --no-cov`

Expected: Pass

- [ ] **Step 5: Final commit**

```bash
git add README.md \
        docs/architecture/story-system-phase2.md \
        docs/architecture/overview.md \
        docs/guides/commands.md \
        docs/superpowers/README.md
git commit -m "docs: document story system phase2 contract-first runtime"
```

---

## Spec Coverage Check

- `13.3 Phase 2: Contract-first runtime`
  - `VOLUME_BRIEF`：Task 1 / Task 2
  - `REVIEW_CONTRACT`：Task 1 / Task 2
  - Pre-writing prohibitions and disambiguation scopes: Task 3
  - Outline fulfillment diff seed: Task 3
  - `context_manager` contract-first pack：Task 3 / Task 4

- `7.2 Runtime priorities`
  - `chapter -> volume -> master -> old profile`：Task 3 / Task 4

- `11.1 Pre-writing validation`
  - Visible contracts, prohibitions, pending disambiguation, and must-cover items: Task 3

- `17.1 Documentation update requirements`
  - Schemas, directories, workflows, and commands: Task 5

---

## Placeholder Scan

- No `TODO / TBD / implement later` placeholders
- Skill integration is concrete, with specific skill files identified
- Phase 3 `CHAPTER_COMMIT` is not mixed into this phase

---

## Next Plan

After completing Phase 2, proceed to:

1. `Phase 3 Chapter Commit Chain`
2. `Phase 4 Event Log And Override Ledger`
