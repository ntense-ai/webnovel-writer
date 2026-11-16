#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CSV_CONFIG and actual CSV header alignment validation。"""
import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from reference_search import CSV_CONFIG

CSV_DIR = Path(__file__).resolve().parent.parent.parent.parent / "references" / "csv"


@pytest.mark.parametrize("table_name,config", list(CSV_CONFIG.items()))
def test_csv_config_columns_exist_in_csv_header(table_name, config):
    csv_path = CSV_DIR / config["file"]
    if not csv_path.exists():
        pytest.skip(f"{config['file']} not yet created")

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])

    all_cols = set()
    for col in config.get("search_cols", {}):
        all_cols.add(col)
    for col in config.get("output_cols", []):
        all_cols.add(col)
    poison = config.get("poison_col", "")
    if poison:
        all_cols.add(poison)

    missing = all_cols - headers
    assert not missing, f"table {table_name} Missing columns: {missing}"


def test_csv_config_file_field_matches_filename():
    for name, config in CSV_CONFIG.items():
        assert config["file"] == f"{name}.csv"


def test_csv_config_has_prefix_field():
    for name, config in CSV_CONFIG.items():
        assert "prefix" in config, f"table {name} Missing prefix field"
        assert isinstance(config["prefix"], str)
        assert len(config["prefix"]) >= 2


def test_csv_config_has_required_cols_field():
    for name, config in CSV_CONFIG.items():
        assert "required_cols" in config, f"table {name} Missing required_cols field"
        assert isinstance(config["required_cols"], list)
        assert len(config["required_cols"]) >= 1


def test_csv_config_has_contract_inject_field():
    for name, config in CSV_CONFIG.items():
        assert "contract_inject" in config, f"table {name} Missing contract_inject field"
        assert isinstance(config["contract_inject"], str)
        assert "." in config["contract_inject"]


def test_csv_config_prefix_matches_actual_data():
    """Every row's id must start with the declared prefix."""
    for name, config in CSV_CONFIG.items():
        csv_path = CSV_DIR / config["file"]
        if not csv_path.exists():
            continue
        prefix = config["prefix"]
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                row_id = row.get("id", "")
                assert row_id.startswith(prefix + "-"), (
                    f"table {name} line {row_id} ID does not start with {prefix}- Beginning"
                )
