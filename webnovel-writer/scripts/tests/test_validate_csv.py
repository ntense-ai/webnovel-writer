#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for validate_csv.py."""

import subprocess
import sys
from pathlib import Path
import csv
import tempfile
import uuid


SCRIPT = str(Path(__file__).resolve().parents[1] / "validate_csv.py")
CSV_DIR = str(Path(__file__).resolve().parents[2] / "references" / "csv")


def _make_local_tmp_path() -> Path:
    return Path(tempfile.mkdtemp(prefix=f"validate_csv_cases_{uuid.uuid4().hex}_"))


def run_validate(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, SCRIPT, "--csv-dir", CSV_DIR, *args],
        capture_output=True,
        text=True,
    )


class TestValidateCsvRuns:
    def test_script_runs_without_crash(self):
        result = run_validate()
        assert result.returncode in (0, 1)
        assert "Traceback" not in result.stderr

    def test_json_output_mode(self):
        import json

        result = run_validate("--format", "json")
        assert result.returncode in (0, 1)
        data = json.loads(result.stdout)
        assert "errors" in data
        assert "warnings" in data

    def test_current_csv_data_has_no_errors_or_warnings(self):
        import json

        result = run_validate("--format", "json")
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["errors"] == []
        assert data["warnings"] == []

    def test_phase2_row_count_thresholds(self):
        csv_dir = Path(CSV_DIR)
        with open(csv_dir / "genre-routing.csv", "r", encoding="utf-8-sig", newline="") as f:
            route_rows = list(csv.DictReader(f))
        with open(csv_dir / "adjudication.csv", "r", encoding="utf-8-sig", newline="") as f:
            reasoning_rows = list(csv.DictReader(f))

        assert len(route_rows) >= 16
        assert len(reasoning_rows) >= 14

    def test_detects_extra_csv_fields(self):
        tmp_path = _make_local_tmp_path()
        (tmp_path / "naming.csv").write_text(
            "\n".join(
                [
                    "id,applicable_skills,category,level,keywords,intent_synonyms,applicable_genres,model_instruction,summary,details,naming_target,rule,positive_example,negative_example,pitfalls",
                    "NR-999,write,Test,knowledge,character naming,,xuanhuan,Instruction,Summary,Details,Person name,rule,positive_example,negative_example,pitfalls,EXTRA",
                ]
            ),
            encoding="utf-8-sig",
        )

        result = subprocess.run(
            [sys.executable, SCRIPT, "--csv-dir", str(tmp_path), "--format", "json"],
            capture_output=True,
            text=True,
        )

        import json

        data = json.loads(result.stdout)
        assert any("More fields than headers" in error for error in data["errors"])

    def test_detects_invalid_skill_and_level(self):
        tmp_path = _make_local_tmp_path()
        (tmp_path / "naming.csv").write_text(
            "\n".join(
                [
                    "id,applicable_skills,category,level,keywords,intent_synonyms,applicable_genres,model_instruction,summary,details,naming_target,rule,positive_example,negative_example,pitfalls",
                    "NR-998,bogus,Test,reasoning,character naming,,xuanhuan,Instruction,Summary,Details,Person name,rule,positive_example,negative_example,pitfalls",
                ]
            ),
            encoding="utf-8-sig",
        )

        result = subprocess.run(
            [sys.executable, SCRIPT, "--csv-dir", str(tmp_path), "--format", "json"],
            capture_output=True,
            text=True,
        )

        import json

        data = json.loads(result.stdout)
        assert any("Invalid applicable_skills value 'bogus'" in error for error in data["errors"])
        assert any("Invalid level value 'reasoning'" in error for error in data["errors"])
