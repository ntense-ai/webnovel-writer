#!/usr/bin/env python3
'Visual status reporting for long novels.\n\nProvide a broad overview across hundreds of chapters: character absence, unresolved foreshadowing and urgency, payoff frequency, word-count distribution, relationship trends, and Quest/Fire/Constellation strand balance. Foreshadowing priority uses core, subplot, and decorative tiers.\n\nOutput Markdown to .webnovel/health_report.md with Mermaid relationship diagrams and pacing summaries.\n\nUsage:\n  python status_reporter.py --output .webnovel/health_report.md\n  python status_reporter.py --focus characters\n  python status_reporter.py --focus foreshadowing\n  python status_reporter.py --focus pacing\n  python status_reporter.py --focus strand\n\nExample report: 450 chapters, 1,985,432 words, 4,412 words per chapter, and 99.3% of a two-million-word target. Character tables show last appearance, chapters absent, and severity. Foreshadowing tables show planting chapter, elapsed chapters, and overdue status. Pacing bands report words per payoff; relationship diagrams show affection and hostility between the protagonist, allies, and enemies.'

import json
import os
import re
import sys
from pathlib import Path

from project_paths import project_dir
from text_metrics import count_words
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from collections import defaultdict
from project_locator import resolve_project_root
from chapter_paths import extract_chapter_num_from_filename
from runtime_compat import enable_windows_utf8_stdio

# Import configuration.
try:
    from data_modules.config import get_config, DataModulesConfig
    from data_modules.index_manager import IndexManager
    from data_modules.state_validator import (
        get_chapter_meta_entry,
        is_resolved_foreshadowing_status,
        normalize_foreshadowing_tier,
        normalize_state_runtime_sections,
        resolve_chapter_field,
        to_positive_int,
    )
except ImportError:
    from scripts.data_modules.config import get_config, DataModulesConfig
    from scripts.data_modules.index_manager import IndexManager
    from scripts.data_modules.state_validator import (
        get_chapter_meta_entry,
        is_resolved_foreshadowing_status,
        normalize_foreshadowing_tier,
        normalize_state_runtime_sections,
        resolve_chapter_field,
        to_positive_int,
    )

def _is_resolved_foreshadowing_status(raw_status: Any) -> bool:
    'Determine whether foreshadowing is resolved, accepting historical fields and synonyms.'
    return is_resolved_foreshadowing_status(raw_status)

def _enable_windows_utf8_stdio() -> None:
    'Enable UTF-8 output on Windows; skip under pytest to avoid capture conflicts.'
    enable_windows_utf8_stdio(skip_in_pytest=True)



def _display_label(value: Any) -> str:
    """Render analytical labels for author-facing reports."""
    labels = {
        "✅ Active": "✅ Active", "🟢 Normal": "🟢 Normal",
        "🟡 Mild absence": "🟡 Mild absence", "🔴 Severe absence": "🔴 Severe absence",
        "🟡 Mildly overdue": "🟡 Mildly overdue", "🔴 Severely overdue": "🔴 Severely overdue",
        "🔴 Overdue": "🔴 Overdue", "⚪ Insufficient data": "⚪ Insufficient data",
        "🔴 Urgent": "🔴 Urgent", "🟡 Warning": "🟡 Warning",
        "core": "Core", "subplot": "Subplot", "decorative": "Decorative",
        "Insufficient data": "Insufficient data", "Excellent": "Excellent", "Good": "Good",
        "Adequate": "Adequate", "Low⚠️": "Low ⚠️",
    }
    return labels.get(str(value), str(value))

class StatusReporter:
    'Generate status reports.'

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config = get_config(self.project_root)
        self.state_file = self.project_root / ".webnovel/state.json"
        self.chapters_dir = project_dir(self.project_root, "chapters")

        self.state = None
        self.chapters_data = []
        self._reading_power_cache: Dict[int, Optional[Dict[str, Any]]] = {}

        # Introduced in v5.1: read entities through IndexManager.
        self._index_manager = IndexManager(self.config)

    def _extract_stats_field(self, content: str, field_name: str) -> str:
        'Extract a field from the chapter-statistics block, such as the dominant strand value quest.'
        pattern = rf"^\s*-\s*\*\*{re.escape(field_name)}\*\*\s*:\s*(.+?)\s*$"
        for line in content.splitlines():
            m = re.match(pattern, line)
            if m:
                return m.group(1).strip()
        return ""

    def load_state(self) -> bool:
        'Load state.json.'
        if not self.state_file.exists():
            print(f"❌ State file not found: {self.state_file}")
            return False

        with open(self.state_file, 'r', encoding='utf-8') as f:
            self.state = json.load(f)

        if isinstance(self.state, dict):
            self.state = normalize_state_runtime_sections(self.state)

        return True

    def _to_positive_int(self, value: Any) -> Optional[int]:
        'Parse a positive integer, returning None on failure.'
        return to_positive_int(value)

    def _normalize_foreshadowing_tier(self, raw_tier: Any) -> Tuple[str, float]:
        'Normalize a foreshadowing tier and return its weight.'
        tier = normalize_foreshadowing_tier(raw_tier)

        if tier == "core":
            return "core", self.config.foreshadowing_tier_weight_core
        if tier == "decorative":
            return "decorative", self.config.foreshadowing_tier_weight_decor
        return "subplot", self.config.foreshadowing_tier_weight_sub

    def _resolve_chapter_field(self, item: Dict[str, Any], keys: List[str]) -> Optional[int]:
        'Read a chapter number in candidate-key order.'
        return resolve_chapter_field(item, keys)

    def _collect_foreshadowing_records(self) -> List[Dict[str, Any]]:
        'Collect unresolved foreshadowing and build analysis records from actual fields.'
        if not self.state:
            return []

        current_chapter = self.state.get("progress", {}).get("current_chapter", 0)
        plot_threads = self.state.get("plot_threads", {}) if isinstance(self.state.get("plot_threads"), dict) else {}
        foreshadowing = plot_threads.get("foreshadowing", [])
        if not isinstance(foreshadowing, list):
            return []

        records: List[Dict[str, Any]] = []
        for item in foreshadowing:
            if not isinstance(item, dict):
                continue
            if _is_resolved_foreshadowing_status(item.get("status")):
                continue

            content = str(item.get("content") or "").strip() or "[Untitled foreshadowing]"
            tier, weight = self._normalize_foreshadowing_tier(item.get("tier"))

            planted_chapter = self._resolve_chapter_field(
                item,
                [
                    "planted_chapter",
                    "added_chapter",
                    "source_chapter",
                    "start_chapter",
                    "chapter",
                ],
            )
            target_chapter = self._resolve_chapter_field(
                item,
                [
                    "target_chapter",
                    "due_chapter",
                    "deadline_chapter",
                    "resolve_by_chapter",
                    "target",
                ],
            )

            elapsed = None
            if planted_chapter is not None:
                elapsed = max(0, current_chapter - planted_chapter)

            remaining = None
            if target_chapter is not None:
                remaining = target_chapter - current_chapter

            if remaining is not None and remaining < 0:
                overtime_status = "🔴 Overdue"
            elif elapsed is None:
                overtime_status = "⚪ Insufficient data"
            else:
                overtime_status = self._get_foreshadowing_status(elapsed)

            urgency: Optional[float] = None
            if (
                planted_chapter is not None
                and target_chapter is not None
                and target_chapter > planted_chapter
                and elapsed is not None
            ):
                urgency = round((elapsed / (target_chapter - planted_chapter)) * weight, 2)
            elif (
                planted_chapter is not None
                and target_chapter is not None
                and target_chapter <= planted_chapter
                and elapsed is not None
            ):
                urgency = round(weight * 2.0, 2)

            if remaining is not None and remaining < 0:
                urgency_status = "🔴 Overdue"
            elif urgency is None:
                urgency_status = "⚪ Insufficient data"
            else:
                urgency_status = self._get_urgency_status(urgency, remaining if remaining is not None else 0)

            records.append(
                {
                    "content": content,
                    "tier": tier,
                    "weight": weight,
                    "planted_chapter": planted_chapter,
                    "target_chapter": target_chapter,
                    "elapsed": elapsed,
                    "remaining": remaining,
                    "status": overtime_status,
                    "urgency": urgency,
                    "urgency_status": urgency_status,
                }
            )

        return records

    def _get_chapter_meta(self, chapter: int) -> Dict[str, Any]:
        'Read chapter_meta for a chapter, accepting zero-padded or plain numeric keys.'
        if not self.state:
            return {}
        return get_chapter_meta_entry(self.state, chapter)

    def _parse_pattern_count(self, raw_value: Any) -> Optional[int]:
        'Parse the payoff-pattern count, returning None on failure.'
        if raw_value is None:
            return None

        if isinstance(raw_value, list):
            patterns = [str(x).strip() for x in raw_value if str(x).strip()]
            return len(set(patterns))

        if isinstance(raw_value, str):
            text = raw_value.strip()
            if not text:
                return None
            parts = [p.strip() for p in re.split(r"[、,，/|+；;]+", text) if p.strip()]
            if parts:
                return len(set(parts))
            return 1

        return None

    def _get_chapter_reading_power_cached(self, chapter: int) -> Optional[Dict[str, Any]]:
        'Read and cache chapter_reading_power.'
        if chapter in self._reading_power_cache:
            return self._reading_power_cache[chapter]

        try:
            record = self._index_manager.get_chapter_reading_power(chapter)
        except Exception:
            record = None

        self._reading_power_cache[chapter] = record
        return record

    def _get_chapter_cool_points(self, chapter: int, chapter_data: Dict[str, Any]) -> Tuple[Optional[int], str]:
        "Get a chapter's payoff count, preferring actual metadata."
        reading_power = self._get_chapter_reading_power_cached(chapter)
        if isinstance(reading_power, dict):
            count = self._parse_pattern_count(reading_power.get("coolpoint_patterns"))
            if count is not None:
                return count, "chapter_reading_power"

        chapter_meta = self._get_chapter_meta(chapter)
        for key in ("coolpoint_patterns", "coolpoint_pattern", "cool_point_patterns", "cool_point_pattern", "patterns", "pattern"):
            count = self._parse_pattern_count(chapter_meta.get(key))
            if count is not None:
                return count, "chapter_meta"

        count = self._parse_pattern_count(chapter_data.get("cool_point"))
        if count is not None:
            return count, "chapter_stats"

        return None, "none"

    def scan_chapters(self):
        'Scan all chapter files.'
        if not self.chapters_dir.exists():
            print(f"⚠️  Chapter directory not found: {self.chapters_dir}")
            return

        # Support two directory layouts.
        # 1) Flat chapter files.
        # 2) Chapter files grouped into volume directories.
        chapter_files = sorted(self.chapters_dir.rglob("*.md"))

        # Introduced in v5.1: get known character names from SQLite.
        known_character_names: List[str] = []
        protagonist_name = ""
        if self.state:
            protagonist_name = self.state.get("protagonist_state", {}).get("name", "") or ""

        # Read each character's canonical_name from SQLite.
        try:
            characters_from_db = self._index_manager.get_entities_by_type("character")
            known_character_names = [
                c.get("canonical_name", c.get("id", ""))
                for c in characters_from_db
                if c.get("canonical_name")
            ]
        except Exception:
            known_character_names = []

        for chapter_file in chapter_files:
            chapter_num = extract_chapter_num_from_filename(chapter_file.name)
            if not chapter_num:
                continue

            # Read chapter contents.
            with open(chapter_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Count text after stripping Markdown markers.
            text = re.sub(r'```[\s\S]*?```', '', content)  # Remove code blocks.
            text = re.sub(r'#+ .+', '', text)  # Remove headings.
            text = re.sub(r'---', '', text)  # Remove separators.
            word_count = count_words(text)

            # Prefer the chapter-statistics block for dominant strand and payoff type.
            dominant_strand = (self._extract_stats_field(content, "Dominant Strand") or "").lower()
            cool_point_type = self._extract_stats_field(content, "payoff")

            # Introduced in v5.1: read character extraction from the SQLite chapters table.
            characters: List[str] = []
            try:
                chapter_info = self._index_manager.get_chapter(chapter_num)
                if chapter_info and chapter_info.get("characters"):
                    stored = chapter_info["characters"]
                    if isinstance(stored, str):
                        stored = json.loads(stored)
                    if isinstance(stored, list):
                        for entity_id in stored:
                            entity_id = str(entity_id).strip()
                            if not entity_id:
                                continue
                            # Try to obtain canonical_name.
                            entity = self._index_manager.get_entity(entity_id)
                            name = entity.get("canonical_name", entity_id) if entity else entity_id
                            characters.append(name)
            except Exception:
                characters = []

            if not characters and (protagonist_name or known_character_names):
                # Bound candidate counts to avoid slowdowns with very large character databases.
                candidates = []
                if protagonist_name:
                    candidates.append(protagonist_name)
                candidates.extend(known_character_names[:self.config.character_candidates_limit])

                seen = set()
                for name in candidates:
                    if not name or name in seen:
                        continue
                    if name in content:
                        characters.append(name)
                        seen.add(name)

            self.chapters_data.append({
                "chapter": chapter_num,
                "file": chapter_file,
                "word_count": word_count,
                "characters": characters,
                "dominant": dominant_strand,
                "cool_point": cool_point_type,
            })

    def analyze_characters(self) -> Dict:
        'Analyze character activity (introduced in v5.1; retained in v5.4).'
        if not self.state:
            return {}

        current_chapter = self.state.get("progress", {}).get("current_chapter", 0)

        # Introduced in v5.1: get all characters from SQLite.
        try:
            characters_list = self._index_manager.get_entities_by_type("character")
        except Exception:
            characters_list = []

        # Track each character's last appearance chapter.
        character_activity = {}

        for char in characters_list:
            char_name = char.get("canonical_name", char.get("id", ""))
            if not char_name:
                continue

            # Find the last appearance chapter.
            last_appearance = char.get("last_appearance", 0) or 0

            # Also check chapters_data.
            for ch_data in self.chapters_data:
                if char_name in ch_data.get("characters", []):
                    last_appearance = max(last_appearance, ch_data["chapter"])

            absence = current_chapter - last_appearance

            character_activity[char_name] = {
                "last_appearance": last_appearance,
                "absence": absence,
                "status": self._get_absence_status(absence)
            }

        return character_activity

    def _get_absence_status(self, absence: int) -> str:
        "Classify a character's absence severity."
        if absence == 0:
            return "✅ Active"
        elif absence < self.config.character_absence_warning:
            return "🟢 Normal"
        elif absence < self.config.character_absence_critical:
            return "🟡 Mild absence"
        else:
            return "🔴 Severe absence"

    def analyze_foreshadowing(self) -> List[Dict]:
        'Analyze foreshadowing depth.'
        records = self._collect_foreshadowing_records()
        return [
            {
                "content": item["content"],
                "planted_chapter": item["planted_chapter"],
                "estimated_chapter": item["planted_chapter"],
                "target_chapter": item["target_chapter"],
                "elapsed": item["elapsed"],
                "status": item["status"],
            }
            for item in records
        ]

    def _get_foreshadowing_status(self, elapsed: int) -> str:
        'Classify overdue foreshadowing.'
        if elapsed < self.config.foreshadowing_urgency_pending_medium:
            return "🟢 Normal"
        elif elapsed < self.config.foreshadowing_urgency_pending_high + 50:
            return "🟡 Mildly overdue"
        else:
            return "🔴 Severely overdue"

    def analyze_foreshadowing_urgency(self) -> List[Dict]:
        'Analyze foreshadowing urgency using three tiers.\n\nCore: weight 3.0, essential to plot integrity.\nSubplot: weight 2.0, expected to resolve or the author seems forgetful.\nDecorative: weight 1.0, optional resolution that adds realism.\n\nUrgency is the elapsed-to-target chapter ratio multiplied by the tier weight.'
        records = self._collect_foreshadowing_records()
        urgency_list = [
            {
                "content": item["content"],
                "tier": item["tier"],
                "weight": item["weight"],
                "planted_chapter": item["planted_chapter"],
                "target_chapter": item["target_chapter"],
                "elapsed": item["elapsed"],
                "remaining": item["remaining"],
                "urgency": item["urgency"],
                "status": item["urgency_status"],
            }
            for item in records
        ]

        # Sort computable records first, then by descending urgency.
        return sorted(
            urgency_list,
            key=lambda x: (x["urgency"] is None, -(x["urgency"] if x["urgency"] is not None else -1)),
        )

    def _get_urgency_status(self, urgency: float, remaining: int) -> str:
        'Classify urgency.'
        if remaining < 0:
            return "🔴 Overdue"
        elif urgency >= self.config.foreshadowing_tier_weight_sub:
            return "🔴 Urgent"
        elif urgency >= 1.0:
            return "🟡 Warning"
        else:
            return "🟢 Normal"

    def analyze_strand_weave(self) -> Dict:
        'Analyze Strand Weave distribution.\n\nQuest covers combat, missions, and progression, targeting 55-65%. Fire covers relationships and interaction, targeting 20-30%. Constellation covers worldbuilding and factions, targeting 10-20%.\n\nCheck for more than five consecutive Quest chapters, Fire absent for over ten chapters, and Constellation absent for over fifteen.'
        if not self.state:
            return {}

        strand_tracker = self.state.get("strand_tracker", {})
        history = strand_tracker.get("history", [])

        if not history:
            return {
                "has_data": False,
                "message": "No Strand Weave data yet"
            }

        # Count each strand's share.
        quest_count = 0
        fire_count = 0
        constellation_count = 0
        total = len(history)

        for entry in history:
            strand = (entry.get("strand") or entry.get("dominant") or "").lower()
            if strand in ["quest", "main", "combat", "mission"]:
                quest_count += 1
            elif strand in ["fire", "relationship", "relationship", "interaction"]:
                fire_count += 1
            elif strand in ["constellation", "worldbuilding", "background", "faction"]:
                constellation_count += 1

        # Calculate proportions.
        quest_ratio = (quest_count / total * 100) if total > 0 else 0
        fire_ratio = (fire_count / total * 100) if total > 0 else 0
        constellation_ratio = (constellation_count / total * 100) if total > 0 else 0

        # Check violations.
        violations = []

        # Check for more than five consecutive Quest chapters.
        quest_streak = 0
        max_quest_streak = 0
        for entry in history:
            strand = (entry.get("strand") or entry.get("dominant") or "").lower()
            if strand in ["quest", "main", "combat", "mission"]:
                quest_streak += 1
                max_quest_streak = max(max_quest_streak, quest_streak)
            else:
                quest_streak = 0

        if max_quest_streak > self.config.strand_quest_max_consecutive:
            violations.append(f"Quest consecutive chapters: {max_quest_streak} chapters (exceeds {self.config.strand_quest_max_consecutive} chapter limit)")

        # Check for Fire absent for over ten chapters.
        fire_gap = 0
        max_fire_gap = 0
        for entry in history:
            strand = (entry.get("strand") or entry.get("dominant") or "").lower()
            if strand in ["fire", "relationship", "relationship", "interaction"]:
                max_fire_gap = max(max_fire_gap, fire_gap)
                fire_gap = 0
            else:
                fire_gap += 1
        max_fire_gap = max(max_fire_gap, fire_gap)

        if max_fire_gap > self.config.strand_fire_max_gap:
            violations.append(f"Fire missing for {max_fire_gap} chapters (exceeds {self.config.strand_fire_max_gap} chapter limit)")

        # Check for Constellation absent for over fifteen chapters.
        const_gap = 0
        max_const_gap = 0
        for entry in history:
            strand = (entry.get("strand") or entry.get("dominant") or "").lower()
            if strand in ["constellation", "worldbuilding", "background", "faction"]:
                max_const_gap = max(max_const_gap, const_gap)
                const_gap = 0
            else:
                const_gap += 1
        max_const_gap = max(max_const_gap, const_gap)

        if max_const_gap > self.config.strand_constellation_max_gap:
            violations.append(f"Constellation missing for {max_const_gap} chapters (exceeds {self.config.strand_constellation_max_gap} chapter limit)")

        # Check whether proportions fall within their target ranges.
        cfg = self.config
        if quest_ratio < cfg.strand_quest_ratio_min:
            violations.append(f"Quest ratio {quest_ratio:.1f}% is low (target {cfg.strand_quest_ratio_min}-{cfg.strand_quest_ratio_max}%)")
        elif quest_ratio > cfg.strand_quest_ratio_max:
            violations.append(f"Quest ratio {quest_ratio:.1f}% is high (target {cfg.strand_quest_ratio_min}-{cfg.strand_quest_ratio_max}%)")

        if fire_ratio < cfg.strand_fire_ratio_min:
            violations.append(f"Fire ratio {fire_ratio:.1f}% is low (target {cfg.strand_fire_ratio_min}-{cfg.strand_fire_ratio_max}%)")
        elif fire_ratio > cfg.strand_fire_ratio_max:
            violations.append(f"Fire ratio {fire_ratio:.1f}% is high (target {cfg.strand_fire_ratio_min}-{cfg.strand_fire_ratio_max}%)")

        if constellation_ratio < cfg.strand_constellation_ratio_min:
            violations.append(f"Constellation ratio {constellation_ratio:.1f}% is low (target {cfg.strand_constellation_ratio_min}-{cfg.strand_constellation_ratio_max}%)")
        elif constellation_ratio > cfg.strand_constellation_ratio_max:
            violations.append(f"Constellation ratio {constellation_ratio:.1f}% is high (target {cfg.strand_constellation_ratio_min}-{cfg.strand_constellation_ratio_max}%)")

        return {
            "has_data": True,
            "total_chapters": total,
            "quest": {"count": quest_count, "ratio": quest_ratio},
            "fire": {"count": fire_count, "ratio": fire_ratio},
            "constellation": {"count": constellation_count, "ratio": constellation_ratio},
            "violations": violations,
            "max_quest_streak": max_quest_streak,
            "max_fire_gap": max_fire_gap,
            "max_const_gap": max_const_gap,
            "health": "✅ Healthy" if not violations else f"⚠️ {len(violations)} issues"
        }

    def analyze_pacing(self) -> List[Dict]:
        'Analyze payoff pacing in groups of N chapters.'
        segment_size = self.config.pacing_segment_size
        segments = []

        for i in range(0, len(self.chapters_data), segment_size):
            segment_chapters = self.chapters_data[i:i+segment_size]

            if not segment_chapters:
                continue

            start_ch = segment_chapters[0]["chapter"]
            end_ch = segment_chapters[-1]["chapter"]
            total_words = sum(ch["word_count"] for ch in segment_chapters)

            cool_points = 0
            chapters_with_data = 0
            source_counter: Dict[str, int] = {}

            for chapter_data in segment_chapters:
                chapter = chapter_data["chapter"]
                count, source = self._get_chapter_cool_points(chapter, chapter_data)
                source_counter[source] = source_counter.get(source, 0) + 1
                if count is None:
                    continue
                chapters_with_data += 1
                cool_points += count

            words_per_point = None
            if cool_points > 0:
                words_per_point = total_words / cool_points

            rating = self._get_pacing_rating(words_per_point)
            missing_chapters = len(segment_chapters) - chapters_with_data
            dominant_source = "none"
            if source_counter:
                dominant_source = max(source_counter.items(), key=lambda x: x[1])[0]

            segments.append({
                "start": start_ch,
                "end": end_ch,
                "total_words": total_words,
                "cool_points": cool_points,
                "words_per_point": words_per_point,
                "rating": rating,
                "missing_chapters": missing_chapters,
                "data_coverage": (chapters_with_data / len(segment_chapters)) if segment_chapters else 0.0,
                "dominant_source": dominant_source,
            })

        return segments

    def _get_pacing_rating(self, words_per_point: Optional[float]) -> str:
        'Classify pacing quality.'
        if words_per_point is None:
            return "Insufficient data"
        if words_per_point < self.config.pacing_words_per_point_excellent:
            return "Excellent"
        elif words_per_point < self.config.pacing_words_per_point_good:
            return "Good"
        elif words_per_point < self.config.pacing_words_per_point_acceptable:
            return "Adequate"
        else:
            return "Low⚠️"

    def _resolve_protagonist_entity_id(self) -> Optional[str]:
        'Resolve the protagonist entity ID, preferring index.db.'
        protagonist = self._index_manager.get_protagonist()
        if protagonist and protagonist.get("id"):
            return str(protagonist["id"])

        if not self.state:
            return None
        name = str(self.state.get("protagonist_state", {}).get("name", "") or "").strip()
        if not name:
            return None
        hits = self._index_manager.get_entities_by_alias(name)
        if hits:
            return str(hits[0].get("id") or "")
        return None

    def _generate_relationship_graph_from_index(self) -> str:
        'Build a relationship graph from index.db.'
        protagonist_id = self._resolve_protagonist_entity_id()
        if not protagonist_id:
            return ""

        current_chapter = 0
        if self.state:
            current_chapter = int(self.state.get("progress", {}).get("current_chapter", 0) or 0)
        chapter = current_chapter if current_chapter > 0 else None

        graph = self._index_manager.build_relationship_subgraph(
            center_entity=protagonist_id,
            depth=2,
            chapter=chapter,
            top_edges=40,
        )
        if not graph.get("nodes"):
            return ""
        return self._index_manager.render_relationship_subgraph_mermaid(graph)

    def generate_relationship_graph(self) -> str:
        'Generate a Mermaid relationship diagram.'
        if not self.state:
            return ""

        # v5.5: prefer the index.db relationship graph unless disabled in configuration.
        if bool(getattr(self.config, "relationship_graph_from_index_enabled", True)):
            try:
                graph = self._generate_relationship_graph_from_index()
                if graph:
                    return graph
            except Exception:
                # Fall back to legacy logic rather than interrupt report generation.
                pass

        # Accept the older state.json relationships structure.
        relationships = self.state.get("relationships", {})
        protagonist_name = self.state.get("protagonist_state", {}).get("name", "Protagonist")

        lines = ["```mermaid", "graph LR"]

        # Support two formats.
        # New format: {"allies": [...], "enemies": [...]}
        # Legacy format: {"character_name": {"affection": X, "hatred": Y}}

        allies = relationships.get("allies", [])
        enemies = relationships.get("enemies", [])

        if allies or enemies:
            # New format.
            for ally in allies:
                if isinstance(ally, dict):
                    name = ally.get("name", "Unknown")
                    relation = ally.get("relation", "Friendly")
                    lines.append(f"    {protagonist_name} -->|{relation}| {name}")

            for enemy in enemies:
                if isinstance(enemy, dict):
                    name = enemy.get("name", "Unknown")
                    relation = enemy.get("relation", "Hostile")
                    lines.append(f"    {protagonist_name} -.->|{relation}| {name}")
        else:
            # Legacy-format compatibility.
            for char_name, rel_data in relationships.items():
                if isinstance(rel_data, dict):
                    affection = rel_data.get("affection", 0)
                    hatred = rel_data.get("hatred", 0)

                    if affection > 0:
                        lines.append(f"    {protagonist_name} -->|Affection {affection}| {char_name}")

                    if hatred > 0:
                        lines.append(f"    {protagonist_name} -.->|Hostility {hatred}| {char_name}")

        lines.append("```")

        return "\n".join(lines)

    def generate_report(self, focus: str = "all") -> str:
        'Generate a Markdown health report.'

        report_lines = [
            "# Book Health Report",
            "",
            f"> **Generated at**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]

        # Basic Statistics
        if focus in ["all", "basic"]:
            report_lines.extend(self._generate_basic_stats())

        # Long-term memory statistics.
        if focus in ["all", "basic"]:
            report_lines.extend(self._generate_memory_section())

        # Character activity.
        if focus in ["all", "characters"]:
            report_lines.extend(self._generate_character_section())

        # Foreshadowing depth.
        if focus in ["all", "foreshadowing"]:
            report_lines.extend(self._generate_foreshadowing_section())

        # Foreshadowing urgency, newly added.
        if focus in ["all", "foreshadowing", "urgency"]:
            report_lines.extend(self._generate_urgency_section())

        # Payoff pacing.
        if focus in ["all", "pacing"]:
            report_lines.extend(self._generate_pacing_section())

        # Strand Weave pacing, newly added.
        if focus in ["all", "strand", "pacing"]:
            report_lines.extend(self._generate_strand_section())

        # Relationships.
        if focus in ["all", "relationships"]:
            report_lines.extend(self._generate_relationship_section())

        return "\n".join(report_lines)

    def _generate_memory_section(self) -> List[str]:
        'Generate the Long-term Memory Statistics section on a best-effort basis.'
        try:
            from data_modules.memory.store import ScratchpadManager
        except Exception:
            try:
                from scripts.data_modules.memory.store import ScratchpadManager
            except Exception:
                return []

        try:
            manager = ScratchpadManager(self.config)
            stats = manager.stats()
            conflicts = manager.conflicts()
        except Exception:
            return []

        return [
            "## 🧠 Long-term Memory Statistics",
            "",
            f"- **Total entries**: {stats.get('total', 0)}",
            f"- **Active**: {stats.get('active', 0)}",
            f"- **Outdated**: {stats.get('outdated', 0)}",
            f"- **Contradicted**: {stats.get('contradicted', 0)}",
            f"- **Tentative**: {stats.get('tentative', 0)}",
            f"- **Conflicting keys**: {len(conflicts)}",
            "",
            "---",
            "",
        ]

    def _generate_basic_stats(self) -> List[str]:
        'Generate basic statistics.'
        if not self.state:
            return []

        progress = self.state.get("progress", {})
        current_chapter = progress.get("current_chapter", 0)
        total_words = progress.get("total_words", 0)
        target_words = self.state.get("project_info", {}).get("target_words", 2000000)

        avg_words = total_words / current_chapter if current_chapter > 0 else 0
        completion = (total_words / target_words * 100) if target_words > 0 else 0

        return [
            "## 📊 Basic Statistics",
            "",
            f"- **Total chapters**: {current_chapter} chapters",
            f"- **Total words**: {total_words:,} words",
            f"- **Average chapter length**: {avg_words:,.0f} words",
            f"- **Writing progress**: {completion:.1f}% (target {target_words:,} words)",
            "",
            "---",
            ""
        ]

    def _generate_character_section(self) -> List[str]:
        'Generate the character-analysis section.'
        activity = self.analyze_characters()

        if not activity:
            return []

        # Filter absent characters.
        dropped = {name: data for name, data in activity.items()
                  if "absence" in data["status"]}

        lines = [
            f"## ⚠️ Absent Characters ({len(dropped)})",
            ""
        ]

        if dropped:
            lines.extend([
                "| Character | Last appearance | Chapters absent | Status |",
                "|------|---------|---------|------|"
            ])

            for char_name, data in sorted(dropped.items(),
                                         key=lambda x: x[1]["absence"],
                                         reverse=True):
                lines.append(
                    f"| {char_name} | Chapter {data['last_appearance']} | "
                    f"{data['absence']} chapters | {_display_label(data['status'])} |"
                )
        else:
            lines.append("✅ All characters have normal activity")

        lines.extend(["", "---", ""])

        return lines

    def _generate_foreshadowing_section(self) -> List[str]:
        'Generate the foreshadowing-analysis section.'
        overdue = self.analyze_foreshadowing()

        # Filter overdue foreshadowing.
        overdue_items = [
            item for item in overdue if "overdue" in item["status"] or "Overdue" in item["status"]
        ]
        unknown_items = [item for item in overdue if item["status"] == "⚪ Insufficient data"]

        lines = [
            f"## ⚠️ Overdue Foreshadowing ({len(overdue_items)})",
            ""
        ]

        if overdue_items:
            lines.extend([
                "| Foreshadowing | Planted chapter | Chapters elapsed | Status |",
                "|---------|---------|---------|------|"
            ])

            for item in sorted(overdue_items, key=lambda x: (x["elapsed"] if x["elapsed"] is not None else -1), reverse=True):
                planted = item["planted_chapter"] if item["planted_chapter"] is not None else "Unknown"
                elapsed = item["elapsed"] if item["elapsed"] is not None else "Unknown"
                lines.append(
                    f"| {item['content'][:30]}... | Chapter {planted} | "
                    f"{elapsed} chapters | {_display_label(item['status'])} |"
                )
        else:
            lines.append("✅ All foreshadowing is on track")

        if unknown_items:
            lines.append("")
            lines.append(f"⚪ {len(unknown_items)} other foreshadowing entries lack chapter information; overdue status is unknown")

        lines.extend(["", "---", ""])

        return lines

    def _generate_urgency_section(self) -> List[str]:
        'Generate tier-based foreshadowing urgency analysis.'
        urgency_list = self.analyze_foreshadowing_urgency()

        # Filter urgent foreshadowing.
        urgent_items = [
            item
            for item in urgency_list
            if (item["urgency"] is not None and item["urgency"] >= 1.0) or item["status"] == "🔴 Overdue"
        ]

        lines = [
            f"## 🚨 Foreshadowing Urgency ({len(urgent_items)} need attention)",
            "",
            "> Three tiers: Core (×3) / Subplot (×2) / Decorative (×1)",
            "> Urgency = (elapsed chapters / (target chapter - planted chapter)) × tier weight",
            ""
        ]

        unknown_items = [item for item in urgency_list if item["urgency"] is None]
        if unknown_items:
            lines.append(f"> {len(unknown_items)} foreshadowing entries lack planted/target chapters; urgency is N/A")
            lines.append("")

        if urgency_list:
            lines.extend([
                "| Foreshadowing | Tier | Planted | Target | Urgency | Status |",
                "|---------|------|------|------|--------|------|"
            ])

            for item in urgency_list[:10]:  # Show only the first ten entries.
                planted = f"Chapter {item['planted_chapter']}" if item["planted_chapter"] is not None else "Unknown"
                target = f"Chapter {item['target_chapter']}" if item["target_chapter"] is not None else "Unknown"
                urgency_text = f"{item['urgency']:.2f}" if item["urgency"] is not None else "N/A"
                lines.append(
                    f"| {item['content'][:20]}... | {_display_label(item['tier'])} | "
                    f"{planted} | {target} | "
                    f"{urgency_text} | {_display_label(item['status'])} |"
                )
        else:
            lines.append("✅ No foreshadowing data yet")

        lines.extend(["", "---", ""])

        return lines

    def _generate_strand_section(self) -> List[str]:
        'Generate the Strand Weave pacing section.'
        strand_data = self.analyze_strand_weave()

        lines = [
            "## 🎭 Strand Weave Pacing Analysis",
            ""
        ]

        if not strand_data.get("has_data"):
            lines.append(f"⚠️ {strand_data.get('message', 'No data yet')}")
            lines.extend(["", "---", ""])
            return lines

        # Proportion statistics.
        cfg = self.config
        lines.extend([
            "### Strand Ratios",
            "",
            "| Strand | Chapters | Ratio | Target range | Status |",
            "|--------|--------|------|----------|------|"
        ])

        q = strand_data["quest"]
        q_status = "✅" if cfg.strand_quest_ratio_min <= q["ratio"] <= cfg.strand_quest_ratio_max else "⚠️"
        lines.append(f"| Quest (main plot) | {q['count']} | {q['ratio']:.1f}% | {cfg.strand_quest_ratio_min}-{cfg.strand_quest_ratio_max}% | {q_status} |")

        f = strand_data["fire"]
        f_status = "✅" if cfg.strand_fire_ratio_min <= f["ratio"] <= cfg.strand_fire_ratio_max else "⚠️"
        lines.append(f"| Fire (relationships) | {f['count']} | {f['ratio']:.1f}% | {cfg.strand_fire_ratio_min}-{cfg.strand_fire_ratio_max}% | {f_status} |")

        c = strand_data["constellation"]
        c_status = "✅" if cfg.strand_constellation_ratio_min <= c["ratio"] <= cfg.strand_constellation_ratio_max else "⚠️"
        lines.append(f"| Constellation (worldbuilding) | {c['count']} | {c['ratio']:.1f}% | {cfg.strand_constellation_ratio_min}-{cfg.strand_constellation_ratio_max}% | {c_status} |")

        lines.append("")

        # Continuity Checks
        lines.extend([
            "### Continuity Checks",
            "",
            f"- Quest longest streak: {strand_data['max_quest_streak']} chapters (limit ≤5)",
            f"- Fire longest gap: {strand_data['max_fire_gap']} chapters (limit ≤10)",
            f"- Constellation longest gap: {strand_data['max_const_gap']} chapters (limit ≤15)",
            ""
        ])

        # Violations
        if strand_data["violations"]:
            lines.extend([
                "### ⚠️ Violations",
                ""
            ])
            for v in strand_data["violations"]:
                lines.append(f"- {v}")
        else:
            lines.append("### ✅ No violations")

        lines.extend(["", f"**Overall health**: {strand_data['health']}", "", "---", ""])

        return lines

    def _generate_pacing_section(self) -> List[str]:
        'Generate the pacing-analysis section.'
        segments = self.analyze_pacing()

        lines = [
            "## 📈 Payoff Pacing Distribution",
            "",
            "```"
        ]

        for seg in segments:
            words_per_point = seg["words_per_point"]
            if words_per_point is None:
                lines.append(
                    f"Chapter {seg['start']}-{seg['end']}   ░ Insufficient data"
                    f" (missing payoff data for {seg['missing_chapters']} chapters)"
                )
                continue

            bar_length = int(12 - (words_per_point / 2000 * 12))
            bar_length = max(1, min(12, bar_length))
            bar = "█" * bar_length

            suffix = ""
            if seg["missing_chapters"] > 0:
                suffix = f", missing payoff data for {seg['missing_chapters']} chapters"

            lines.append(
                f"Chapter {seg['start']}-{seg['end']}   {bar} {_display_label(seg['rating'])}"
                f" ({words_per_point:.0f} words/payoff, recorded {seg['cool_points']} payoffs{suffix})"
            )

        lines.extend(["```", "", "---", ""])

        return lines

    def _generate_relationship_section(self) -> List[str]:
        'Generate the relationships section.'
        graph = self.generate_relationship_graph()

        lines = [
            "## 💑 Relationship Trends",
            "",
            graph,
            "",
            "---",
            ""
        ]

        return lines

def main():
    import argparse

    _enable_windows_utf8_stdio()

    parser = argparse.ArgumentParser(
        description="Visual status report generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a complete health report
  python status_reporter.py --output .webnovel/health_report.md

  # Analyze character activity only
  python status_reporter.py --focus characters

  # Analyze foreshadowing only
  python status_reporter.py --focus foreshadowing

  # Analyze payoff pacing only
  python status_reporter.py --focus pacing
        """
    )

    parser.add_argument('--output', default='.webnovel/health_report.md',
                       help='Output file path')
    parser.add_argument('--focus', choices=['all', 'basic', 'characters',
                                            'foreshadowing', 'urgency', 'pacing',
                                            'strand', 'relationships'],
                       default='all', help='Analysis focus, including urgency and strand')
    parser.add_argument('--project-root', default='.', help='Project root')

    args = parser.parse_args()

    # Resolve the actual book project root; a workspace root is also accepted.
    try:
        project_root = str(resolve_project_root(args.project_root))
    except FileNotFoundError as exc:
        print(f"❌ Cannot locate project root (requires .webnovel/state.json): {exc}", file=sys.stderr)
        sys.exit(1)

    # Create the report generator.
    reporter = StatusReporter(project_root)

    # Load state.
    if not reporter.load_state():
        sys.exit(1)

    print("📖 Scanning chapter files...")
    reporter.scan_chapters()

    print(f"✅ Scanned {len(reporter.chapters_data)} chapters")

    print("\n📊 Analyzing...")

    # Generate the report.
    report = reporter.generate_report(args.focus)

    # Save the report.
    output_file = Path(args.output)
    if args.output == '.webnovel/health_report.md' and project_root != '.':
        output_file = Path(project_root) / '.webnovel' / 'health_report.md'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ Health report generated: {output_file}")

    # Preview the first 30 lines.
    print("\n" + "="*60)
    print("📄 Report preview:\n")
    print("\n".join(report.split("\n")[:30]))
    print("\n...")
    print("="*60)

if __name__ == "__main__":
    main()
