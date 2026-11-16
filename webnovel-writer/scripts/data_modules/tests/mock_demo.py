"""
Generate simulation data and launch Dashboard, for visual acceptance testing.

Usage:
    python -m data_modules.tests.mock_demo
    Then open in the browser http://localhost:8765
"""

from __future__ import annotations

import json
import math
import random
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TOTAL_CHAPTERS = 120
TOTAL_VOLUMES = 4
VOLUME_RANGES = [
    (1, 1, 30),
    (2, 31, 60),
    (3, 61, 90),
    (4, 91, 120),
]

STRANDS = ["quest", "fire", "constellation"]
HOOK_STRENGTHS = ["weak", "medium", "strong"]
LOCATIONS = [
    "Azure Origin Sect", "Azure Realm", "Eastern Sea Immortal City", "black-market", "Heavenly Demon Cult headquarters",
    "Dragon Vein Cave", "Great Void Hall", "Phoenix Song Valley", "Sword Tomb", "Star River Mirage",
    "Bone Wasteland", "Purple Heaven Mountain", "Azure Celestial Pool", "Netherworld Crossing", "Nine Heavens Thunder Realm",
]
CHARACTERS = [
    "lintian", "fenglinger", "laodaoshi", "baiyujing", "heishifanzi",
    "jianling", "tianyao", "zixiao", "qingyun", "mozu",
]
CHARACTER_NAMES = {
    "lintian": "Lin Changqing",
    "fenglinger": "Feng Ling'er",
    "laodaoshi": "Old Taoist",
    "baiyujing": "Bai Yujing",
    "heishifanzi": "Black Market Broker",
    "jianling": "Sword Spirit",
    "tianyao": "Sky Demon",
    "zixiao": "Master Purple Heaven",
    "qingyun": "Azure Cloud",
    "mozu": "Demon Ancestor Remnant",
}

FORESHADOWING = [
    {"content": "whereabouts of the Azure Realm key fragments", "status": "unresolved", "tier": "core", "planted_chapter": 15, "target_chapter": 45},
    {"content": "clues to Feng Ling'er's true identity", "status": "unresolved", "tier": "core", "planted_chapter": 28, "target_chapter": 80},
    {"content": "the numbers in the old Taoist's dying words", "status": "unresolved", "tier": "core", "planted_chapter": 42, "target_chapter": 100},
    {"content": "the faction behind the black-market auction", "status": "unresolved", "tier": "subplot", "planted_chapter": 55, "target_chapter": 90},
    {"content": "the true cause of the protagonist's altered technique", "status": "unresolved", "tier": "core", "planted_chapter": 65, "target_chapter": 130},
    {"content": "signs of awakening the Heavenly Demon bloodline", "status": "unresolved", "tier": "subplot", "planted_chapter": 70, "target_chapter": 140},
    {"content": "the secret of the immortal city's forbidden zone", "status": "unresolved", "tier": "subplot", "planted_chapter": 38, "target_chapter": 110},
    {"content": "clues to the sect's destruction", "status": "resolved", "tier": "core", "planted_chapter": 3, "target_chapter": 50, "resolved_chapter": 48},
    {"content": "the function of the founding master's relic", "status": "resolved", "tier": "subplot", "planted_chapter": 10, "target_chapter": 40, "resolved_chapter": 38},
    {"content": "the origin of the Dragon Vein seal", "status": "resolved", "tier": "decorative", "planted_chapter": 25, "target_chapter": 60, "resolved_chapter": 58},
    {"content": "the Sword Tomb guardian's identity", "status": "resolved", "tier": "subplot", "planted_chapter": 50, "target_chapter": 85, "resolved_chapter": 82},
    {"content": "Purple Heaven Mountain forbidden art", "status": "unresolved", "tier": "decorative", "planted_chapter": 78, "target_chapter": 150},
    {"content": "the secret of Azure Pool's water source", "status": "unresolved", "tier": "decorative", "planted_chapter": 90, "target_chapter": 160},
    {"content": "conditions for awakening the demon ancestor's remnant", "status": "unresolved", "tier": "core", "planted_chapter": 95, "target_chapter": 180},
    {"content": "the ancient formation of the Nine Heavens Thunder Realm", "status": "unresolved", "tier": "subplot", "planted_chapter": 105, "target_chapter": 170},
]

ENTITIES = [
    {"id": "lintian", "canonical_name": "Lin Changqing", "type": "character", "tier": "S", "is_protagonist": True, "first_appearance": 1, "last_appearance": 120, "desc": "Great Void Sect disciple, carries the Heavenly Demon bloodline, cultivates the Boundless Scripture."},
    {"id": "fenglinger", "canonical_name": "Feng Ling'er", "type": "character", "tier": "S", "is_protagonist": False, "first_appearance": 8, "last_appearance": 118, "desc": "Lin Changqing's junior sister, true identity remains a mystery."},
    {"id": "laodaoshi", "canonical_name": "Old Taoist", "type": "character", "tier": "A", "is_protagonist": False, "first_appearance": 1, "last_appearance": 42, "desc": "Lin Changqing's teacher, former Great Void Sect elder, left a numerical puzzle before dying."},
    {"id": "baiyujing", "canonical_name": "Bai Yujing", "type": "character", "tier": "A", "is_protagonist": False, "first_appearance": 20, "last_appearance": 115, "desc": "young lord of the Heavenly Demon Cult, Lin Changqing's nemesis."},
    {"id": "heishifanzi", "canonical_name": "Black Market Broker", "type": "character", "tier": "B", "is_protagonist": False, "first_appearance": 50, "last_appearance": 110, "desc": "black-market information broker, unclear allegiance."},
    {"id": "jianling", "canonical_name": "Sword Spirit", "type": "character", "tier": "A", "is_protagonist": False, "first_appearance": 75, "last_appearance": 120, "desc": "sword-spirit consciousness in the founding master's relic."},
    {"id": "tianyao", "canonical_name": "Sky Demon", "type": "character", "tier": "B", "is_protagonist": False, "first_appearance": 35, "last_appearance": 95, "desc": "Heavenly Demon Cult guardian, unfathomable strength."},
    {"id": "zixiao", "canonical_name": "Master Purple Heaven", "type": "character", "tier": "A", "is_protagonist": False, "first_appearance": 60, "last_appearance": 120, "desc": "Great Void Sect master, secretly scheming for a century."},
    {"id": "qingyun", "canonical_name": "Azure Cloud", "type": "character", "tier": "B", "is_protagonist": False, "first_appearance": 15, "last_appearance": 100, "desc": "Lin Changqing's senior fellow disciple, deeply jealous."},
    {"id": "mozu", "canonical_name": "Demon Ancestor Remnant", "type": "character", "tier": "S", "is_protagonist": False, "first_appearance": 95, "last_appearance": 120, "desc": "remaining will of the ancient demon ancestor, sleeping beneath the Dragon Vein seal."},
    {"id": "taixuzong", "canonical_name": "Great Void Sect", "type": "faction", "tier": "S", "is_protagonist": False, "first_appearance": 1, "last_appearance": 120, "desc": "the leading immortal sect of the Eastern Wastes."},
    {"id": "tianmojiao", "canonical_name": "Heavenly Demon Cult", "type": "faction", "tier": "A", "is_protagonist": False, "first_appearance": 20, "last_appearance": 120, "desc": "the leading demonic faction."},
    {"id": "donghaixiancheng", "canonical_name": "Eastern Sea Immortal City", "type": "faction", "tier": "B", "is_protagonist": False, "first_appearance": 40, "last_appearance": 110, "desc": "independent cultivators' alliance base."},
    {"id": "qingyuanmianjing", "canonical_name": "Azure Realm", "type": "location", "tier": "A", "is_protagonist": False, "first_appearance": 15, "last_appearance": 90, "desc": "an ancient hidden realm governed by the Great Void Sect."},
    {"id": "longmaidonfu", "canonical_name": "Dragon Vein Cave", "type": "location", "tier": "B", "is_protagonist": False, "first_appearance": 55, "last_appearance": 120, "desc": "where the demon ancestor's remnant is sealed."},
]

RELATIONSHIPS = [
    {"from_entity": "lintian", "to_entity": "laodaoshi", "type": "mentor-student", "chapter": 1, "description": "mentor-student"},
    {"from_entity": "lintian", "to_entity": "taixuzong", "type": "affiliation", "chapter": 3, "description": "new disciple"},
    {"from_entity": "lintian", "to_entity": "fenglinger", "type": "fellow-disciple", "chapter": 8, "description": "fellow male and female disciples"},
    {"from_entity": "lintian", "to_entity": "qingyun", "type": "fellow-disciple", "chapter": 15, "description": "fellow disciples"},
    {"from_entity": "baiyujing", "to_entity": "tianmojiao", "type": "affiliation", "chapter": 20, "description": "Young Lord"},
    {"from_entity": "lintian", "to_entity": "baiyujing", "type": "hostile", "chapter": 25, "description": "First Clash"},
    {"from_entity": "taixuzong", "to_entity": "tianmojiao", "type": "hostile", "chapter": 30, "description": "hereditary enemies"},
    {"from_entity": "tianyao", "to_entity": "tianmojiao", "type": "affiliation", "chapter": 35, "description": "Guardian"},
    {"from_entity": "laodaoshi", "to_entity": "donghaixiancheng", "type": "Retreat", "chapter": 40, "description": "Retreat"},
    {"from_entity": "heishifanzi", "to_entity": "tianmojiao", "type": "Informant", "chapter": 55, "description": "secret cooperation"},
    {"from_entity": "lintian", "to_entity": "longmaidonfu", "type": "discover", "chapter": 60, "description": "Discover the Dragon Vein"},
    {"from_entity": "zixiao", "to_entity": "taixuzong", "type": "affiliation", "chapter": 60, "description": "Sect Master"},
    {"from_entity": "lintian", "to_entity": "jianling", "type": "Pact", "chapter": 75, "description": "form a sword-spirit contract"},
    {"from_entity": "jianling", "to_entity": "longmaidonfu", "type": "Seal", "chapter": 80, "description": "Seal protection"},
    {"from_entity": "mozu", "to_entity": "longmaidonfu", "type": "Seal", "chapter": 95, "description": "sleeps here"},
    {"from_entity": "lintian", "to_entity": "mozu", "type": "confrontation", "chapter": 100, "description": "First Perception"},
]

RELATIONSHIP_EVENTS = [
    {"from_entity": "lintian", "to_entity": "fenglinger", "chapter": 45, "event_type": "warming", "description": "survive the hidden realm together"},
    {"from_entity": "lintian", "to_entity": "baiyujing", "chapter": 60, "event_type": "worsening", "description": "Dragon Vein War"},
    {"from_entity": "lintian", "to_entity": "baiyujing", "chapter": 90, "event_type": "worsening", "description": "Immortal City Showdown"},
    {"from_entity": "qingyun", "to_entity": "lintian", "chapter": 70, "event_type": "betrayal", "description": "leaks information to the Heavenly Demon Cult"},
    {"from_entity": "lintian", "to_entity": "zixiao", "chapter": 85, "event_type": "trust", "description": "receives the master's secret inheritance"},
    {"from_entity": "lintian", "to_entity": "jianling", "chapter": 100, "event_type": "Awakening", "description": "full awakening of the sword spirit"},
    {"from_entity": "fenglinger", "to_entity": "tianmojiao", "chapter": 110, "event_type": "Reveal", "description": "Identity Crisis"},
]


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def volume_for_chapter(ch: int) -> int:
    for vol, start, end in VOLUME_RANGES:
        if start <= ch <= end:
            return vol
    return TOTAL_VOLUMES


def generate_state(project_root: Path) -> None:
    webnovel = project_root / ".webnovel"
    webnovel.mkdir(parents=True, exist_ok=True)

    chapter_meta = {}
    for ch in range(1, TOTAL_CHAPTERS + 1):
        chapter_meta[f"{ch:04d}"] = {"summary": f"Chapter {ch} outline: plot development."}

    state = {
        "project_info": {
            "title": "《Evergreen Immortal Path》",
            "genre": "xianxia",
            "target_words": 2000000,
            "target_chapters": 800,
        },
        "progress": {
            "current_chapter": TOTAL_CHAPTERS,
            "current_volume": volume_for_chapter(TOTAL_CHAPTERS),
            "total_words": sum(2800 + int(math.sin(ch / 10) * 500 + random.randint(-200, 400)) for ch in range(1, TOTAL_CHAPTERS + 1)),
            "volumes_planned": [
                {"volume": v, "chapters_range": f"{s}-{e}"} for v, s, e in VOLUME_RANGES
            ],
        },
        "protagonist_state": {
            "name": "Lin Changqing",
            "power": {"realm": "Mid Golden Core", "level": 7},
            "location": {"current": "Dragon Vein Cave"},
        },
        "strand_tracker": {
            "current_dominant": "constellation",
            "history": [
                {"chapter": ch, "strand": STRANDS[(ch * 7 + ch // 3) % 3]}
                for ch in range(1, TOTAL_CHAPTERS + 1)
            ],
        },
        "plot_threads": {
            "foreshadowing": FORESHADOWING,
        },
        "chapter_meta": chapter_meta,
    }

    (webnovel / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def generate_index_db(project_root: Path) -> None:
    db_path = project_root / ".webnovel" / "index.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # chapters
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chapters (
            chapter INTEGER PRIMARY KEY,
            title TEXT,
            location TEXT,
            word_count INTEGER,
            characters TEXT,
            summary TEXT
        )
    """)

    titles = [
        "First Arrival at the Sect", "Master Bestows a Sword", "sect tournament", "Hidden Realm Opens", "Bloody Beast Battle",
        "Path to Golden Core", "Black Market Intrigue", "Dragon Vein Disturbance", "Demon Invasion", "Sword Spirit Awakening",
        "Changes in the Immortal City", "Purple Heaven Secret Art", "Thunder Realm Trial", "Shadow of the Demon Ancestor", "Fated Duel",
    ]

    random.seed(42)
    for ch in range(1, TOTAL_CHAPTERS + 1):
        title = titles[(ch - 1) % len(titles)] + f" ({ch})"
        location = LOCATIONS[(ch * 3 + ch // 7) % len(LOCATIONS)]
        word_count = 2800 + int(math.sin(ch / 10) * 500) + random.randint(-200, 400)
        chars = random.sample(CHARACTERS[:6], k=random.randint(1, 3))
        if ch <= 5:
            chars = ["lintian"]
        summary = f"Chapter {ch}: Lin Changqing begins an adventure at {location}."

        cursor.execute(
            "INSERT INTO chapters VALUES (?,?,?,?,?,?)",
            (ch, title, location, word_count, json.dumps(chars), summary),
        )

    # entities
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id TEXT PRIMARY KEY,
            canonical_name TEXT,
            type TEXT,
            tier TEXT,
            is_protagonist INTEGER DEFAULT 0,
            is_archived INTEGER DEFAULT 0,
            first_appearance INTEGER,
            last_appearance INTEGER,
            desc TEXT,
            current_json TEXT
        )
    """)
    for e in ENTITIES:
        current_json = json.dumps({
            "realm": "Mid Golden Core" if e["id"] == "lintian" else "unknown",
            "location": LOCATIONS[hash(e["id"]) % len(LOCATIONS)],
        }, ensure_ascii=False)
        cursor.execute(
            "INSERT INTO entities VALUES (?,?,?,?,?,0,?,?,?,?)",
            (e["id"], e["canonical_name"], e["type"], e["tier"],
             1 if e.get("is_protagonist") else 0,
             e["first_appearance"], e["last_appearance"],
             e.get("desc", ""), current_json),
        )

    # relationships
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_entity TEXT,
            to_entity TEXT,
            type TEXT,
            chapter INTEGER,
            description TEXT
        )
    """)
    for r in RELATIONSHIPS:
        cursor.execute(
            "INSERT INTO relationships (from_entity, to_entity, type, chapter, description) VALUES (?,?,?,?,?)",
            (r["from_entity"], r["to_entity"], r["type"], r["chapter"], r["description"]),
        )

    # relationship_events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relationship_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_entity TEXT,
            to_entity TEXT,
            chapter INTEGER,
            event_type TEXT,
            description TEXT
        )
    """)
    for ev in RELATIONSHIP_EVENTS:
        cursor.execute(
            "INSERT INTO relationship_events (from_entity, to_entity, chapter, event_type, description) VALUES (?,?,?,?,?)",
            (ev["from_entity"], ev["to_entity"], ev["chapter"], ev["event_type"], ev["description"]),
        )

    # state_changes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS state_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT,
            chapter INTEGER,
            field TEXT,
            old_value TEXT,
            new_value TEXT
        )
    """)
    state_changes = [
        ("lintian", 1, "realm", "mortal", "Qi Refining Level One"),
        ("lintian", 15, "realm", "Qi Refining Level Nine", "Early Foundation Establishment"),
        ("lintian", 40, "realm", "Peak Foundation Establishment", "Early Golden Core"),
        ("lintian", 80, "realm", "Early Golden Core", "Mid Golden Core"),
        ("lintian", 25, "location", "Azure Origin Sect", "Azure Realm"),
        ("lintian", 50, "location", "Eastern Sea Immortal City", "black-market"),
        ("lintian", 75, "location", "Sword Tomb", "Dragon Vein Cave"),
        ("fenglinger", 8, "realm", "unknown", "Qi Refining Level Five"),
        ("fenglinger", 35, "realm", "Qi Refining Level Nine", "Early Foundation Establishment"),
        ("fenglinger", 70, "realm", "Peak Foundation Establishment", "Early Golden Core"),
        ("baiyujing", 25, "realm", "Early Golden Core", "Mid Golden Core"),
        ("baiyujing", 60, "realm", "Mid Golden Core", "Peak Golden Core"),
        ("baiyujing", 90, "attitude", "hostility", "killing intent"),
        ("qingyun", 70, "loyalty", "Great Void Sect", "Heavenly Demon Cult"),
    ]
    for entity_id, chapter, field, old_val, new_val in state_changes:
        cursor.execute(
            "INSERT INTO state_changes (entity_id, chapter, field, old_value, new_value) VALUES (?,?,?,?,?)",
            (entity_id, chapter, field, old_val, new_val),
        )

    # aliases
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT,
            alias TEXT
        )
    """)
    aliases = [
        ("lintian", "Changqing"), ("lintian", "Junior Brother Lin"),
        ("fenglinger", "Ling'er"), ("fenglinger", "Junior Sister Feng"),
        ("baiyujing", "Young Lord Bai"), ("laodaoshi", "Nameless Taoist"),
    ]
    for entity_id, alias in aliases:
        cursor.execute("INSERT INTO aliases (entity_id, alias) VALUES (?,?)", (entity_id, alias))

    # chapter_reading_power
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chapter_reading_power (
            chapter INTEGER PRIMARY KEY,
            hook_type TEXT,
            hook_strength TEXT,
            is_transition INTEGER DEFAULT 0,
            override_count INTEGER DEFAULT 0,
            debt_balance REAL DEFAULT 0.0,
            coolpoint_patterns TEXT
        )
    """)
    hook_types = ["mystery", "reversal", "pursuit", "Emotional hook", "Secret hook"]
    for ch in range(1, TOTAL_CHAPTERS + 1):
        strength = HOOK_STRENGTHS[min(2, max(0, int(math.sin(ch / 8) * 1.5 + 1.2)))]
        is_transition = 1 if ch % 30 in (0, 1) else 0
        override_count = random.randint(0, 2) if ch > 50 else 0
        debt = round(random.uniform(-0.5, 2.0), 2) if ch > 30 else 0.0
        cursor.execute(
            "INSERT INTO chapter_reading_power VALUES (?,?,?,?,?,?,?)",
            (ch, hook_types[ch % len(hook_types)], strength, is_transition,
             override_count, debt, json.dumps([hook_types[ch % len(hook_types)]])),
        )

    # review_metrics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_chapter INTEGER,
            end_chapter INTEGER,
            overall_score REAL,
            dimension_scores TEXT,
            severity_counts TEXT,
            critical_issues TEXT
        )
    """)
    for ch in range(1, TOTAL_CHAPTERS + 1):
        base = 65 + math.sin(ch / 15) * 12 + random.uniform(-5, 5)
        score = round(min(98, max(50, base)), 1)
        dims = json.dumps({"plot": round(score + random.uniform(-3, 3), 1),
                           "character": round(score + random.uniform(-3, 3), 1),
                           "pacing": round(score + random.uniform(-5, 5), 1)})
        severity = json.dumps({"high": random.randint(0, 1),
                               "medium": random.randint(0, 2),
                               "low": random.randint(0, 3)})
        critical = json.dumps([]) if score > 60 else json.dumps(["Pacing too slow"])
        cursor.execute(
            "INSERT INTO review_metrics (start_chapter, end_chapter, overall_score, dimension_scores, severity_counts, critical_issues) VALUES (?,?,?,?,?,?)",
            (ch, ch, score, dims, severity, critical),
        )

    # Extended tables (Empty table, prevent _fetchall_safe error)
    for table_sql in [
        "CREATE TABLE IF NOT EXISTS override_contracts (id INTEGER PRIMARY KEY AUTOINCREMENT, chapter INTEGER, status TEXT, record_type TEXT, description TEXT)",
        "CREATE TABLE IF NOT EXISTS chase_debt (id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT, updated_at TEXT)",
        "CREATE TABLE IF NOT EXISTS debt_events (id INTEGER PRIMARY KEY AUTOINCREMENT, debt_id INTEGER, chapter INTEGER)",
        "CREATE TABLE IF NOT EXISTS invalid_facts (id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT, marked_at TEXT)",
        "CREATE TABLE IF NOT EXISTS rag_query_log (id INTEGER PRIMARY KEY AUTOINCREMENT, query_type TEXT, created_at TEXT)",
        "CREATE TABLE IF NOT EXISTS tool_call_stats (id INTEGER PRIMARY KEY AUTOINCREMENT, tool_name TEXT, created_at TEXT)",
        "CREATE TABLE IF NOT EXISTS writing_checklist_scores (id INTEGER PRIMARY KEY AUTOINCREMENT, chapter INTEGER)",
        "CREATE TABLE IF NOT EXISTS story_events (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT, chapter INTEGER, event_type TEXT, subject TEXT, payload_json TEXT, created_at TEXT)",
    ]:
        cursor.execute(table_sql)

    # scenes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chapter INTEGER,
            scene_index INTEGER,
            content TEXT
        )
    """)

    # vector db (Simulation)
    vector_db_path = project_root / ".webnovel" / "vectors.db"
    with sqlite3.connect(str(vector_db_path)) as vconn:
        vconn.execute("""
            CREATE TABLE IF NOT EXISTS vectors (
                chunk_id TEXT PRIMARY KEY,
                chapter INTEGER,
                scene_index INTEGER,
                content TEXT,
                embedding BLOB,
                parent_chunk_id TEXT,
                chunk_type TEXT,
                source_file TEXT
            )
        """)
        for ch in range(1, TOTAL_CHAPTERS + 1):
            for scene in range(1, random.randint(2, 5)):
                vconn.execute(
                    "INSERT INTO vectors VALUES (?,?,?,?,?,?,?,?)",
                    (f"ch{ch:04d}_s{scene}", ch, scene,
                     f"Chapter {ch}, scene {scene}: content excerpt",
                     b"\x00" * 16, None, "scene", f"chapters/chapter-{ch:04d}.md"),
                )
        vconn.commit()

    conn.commit()
    conn.close()


def generate_story_system(project_root: Path) -> None:
    story_root = project_root / ".story-system"
    for subdir in ("chapters", "volumes", "reviews", "commits", "events"):
        (story_root / subdir).mkdir(parents=True, exist_ok=True)

    # MASTER_SETTING
    (story_root / "MASTER_SETTING.json").write_text(json.dumps({
        "meta": {"schema_version": "story-system/v1", "contract_type": "MASTER_SETTING"},
        "route": {"primary_genre": "xianxia progression"},
        "master_constraints": {"core_tone": "Suppress then erupt"},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    # Volumes
    for vol, start, end in VOLUME_RANGES:
        (story_root / "volumes" / f"volume_{vol:03d}.json").write_text(json.dumps({
            "meta": {"contract_type": "VOLUME_BRIEF", "volume": vol},
            "chapters_range": f"{start}-{end}",
        }, ensure_ascii=False), encoding="utf-8")

    # Chapter briefs + reviews + commits
    random.seed(99)
    for ch in range(max(1, TOTAL_CHAPTERS - 15), TOTAL_CHAPTERS + 1):
        (story_root / "chapters" / f"chapter_{ch:03d}.json").write_text(json.dumps({
            "meta": {"contract_type": "CHAPTER_BRIEF", "chapter": ch},
        }, ensure_ascii=False), encoding="utf-8")

        (story_root / "reviews" / f"chapter_{ch:03d}.review.json").write_text(json.dumps({
            "meta": {"contract_type": "REVIEW_CONTRACT", "chapter": ch},
        }, ensure_ascii=False), encoding="utf-8")

        status = "accepted" if random.random() > 0.15 else "rejected"
        proj_state = "done" if status == "accepted" else "skipped"
        (story_root / "commits" / f"chapter_{ch:03d}.commit.json").write_text(json.dumps({
            "meta": {"schema_version": "story-system/v1", "chapter": ch, "status": status},
            "provenance": {"write_fact_role": "chapter_commit"},
            "projection_status": {
                "state": proj_state,
                "index": proj_state,
                "summary": proj_state,
                "memory": proj_state,
                "vector": proj_state,
            },
        }, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_content_files(project_root: Path) -> None:
    for folder in ("chapters", "outlines", "settings"):
        (project_root / folder).mkdir(parents=True, exist_ok=True)

    # chapters
    for ch in range(1, TOTAL_CHAPTERS + 1):
        vol = volume_for_chapter(ch)
        vol_dir = project_root / "chapters" / f"volume-{vol}"
        vol_dir.mkdir(exist_ok=True)
        content = f"# Chapter {ch}\n\nLin Changqing slowly opened his eyes, Spiritual power circulated continuously through the meridians.\n\n" + "This is simulated manuscript content.\n" * 10
        (vol_dir / f"chapter-{ch:04d}.md").write_text(content, encoding="utf-8")

    # outlines
    (project_root / "outlines" / "master-outline.md").write_text("# Evergreen Immortal Path master-outline\n\ncultivation world, Young Lin Changqing sets out on the path of cultivation...\n", encoding="utf-8")
    for vol, _, _ in VOLUME_RANGES:
        (project_root / "outlines" / f"volume-{vol}-outline.md").write_text(f"# Volume {vol} outline\n\nmain plot of this volume...\n", encoding="utf-8")

    # settings
    (project_root / "settings" / "cultivation system.md").write_text("# cultivation system\n\nqi-refining → foundation-establishment → golden-core → Nascent Soul → Spirit Transformation\n", encoding="utf-8")
    (project_root / "settings" / "Sect factions.md").write_text("# Sect factions\n\nGreat Void Sect、Heavenly Demon Cult、Eastern Sea Immortal City...\n", encoding="utf-8")
    (project_root / "settings" / "Artifact list.md").write_text("# Artifact list\n\nBoundless Sword、Heavenly Demon Banner、Azure Origin Mirror...\n", encoding="utf-8")


def generate_env(project_root: Path) -> None:
    (project_root / ".env").write_text("\n".join([
        "EMBED_BASE_URL=https://api.voyageai.com/v1",
        "EMBED_MODEL=voyage-3-lite",
        "EMBED_API_KEY=demo-embed-key-xxxxx",
        "RERANK_BASE_URL=https://api.cohere.com/v2",
        "RERANK_MODEL=rerank-v3.5",
        "RERANK_API_KEY=demo-rerank-key-xxxxx",
    ]), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    demo_root = Path(tempfile.mkdtemp(prefix="pixelwriter_demo_"))
    print(f"[mock_demo] Generate simulation data → {demo_root}")

    generate_state(demo_root)
    generate_index_db(demo_root)
    generate_story_system(demo_root)
    generate_content_files(demo_root)
    generate_env(demo_root)

    print(f"[mock_demo] Data ready:")
    print(f"  state.json  : {demo_root / '.webnovel' / 'state.json'}")
    print(f"  index.db    : {demo_root / '.webnovel' / 'index.db'}")
    print(f"  vectors.db  : {demo_root / '.webnovel' / 'vectors.db'}")
    print(f"  .story-system/commits: {len(list((demo_root / '.story-system' / 'commits').glob('*.json')))} files")
    print(f"  chapters/        : {sum(1 for _ in (demo_root / 'chapters').rglob('*.md'))} chapters")
    print()

    # Launch
    plugin_root = Path(__file__).resolve().parents[3]
    scripts_dir = plugin_root / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    if str(plugin_root) not in sys.path:
        sys.path.insert(0, str(plugin_root))

    from dashboard.app import create_app

    app = create_app(demo_root)

    import uvicorn

    print("[mock_demo] Launch Dashboard → http://localhost:8765")
    print("[mock_demo] Ctrl+C Stop\n")

    try:
        uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")
    finally:
        print(f"\n[mock_demo] Clean up the temporary directory: {demo_root}")
        shutil.rmtree(demo_root, ignore_errors=True)


if __name__ == "__main__":
    main()
