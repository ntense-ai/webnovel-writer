"""CLI contracts for resumable writes and redacted diagnostic logs."""
import json
import sys

import pytest

from data_modules import run_ledger, run_logger


@pytest.mark.parametrize("output_format", ["json", "text"])
def test_record_and_resume_cli_roundtrip(tmp_path, monkeypatch, capsys, output_format):
    prose = tmp_path / "chapter.md"
    prose.write_text("A chapter", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["run-ledger", "--project-root", str(tmp_path),
        "record-write-step", "--chapter", "3", "--step", "draft", "--status", "completed",
        "--mode", "fast", "--inputs-json", json.dumps({"outline": str(prose)}),
        "--outputs-json", json.dumps({"prose": str(prose)}), "--problems-json", '["slow"]',
        "--auto-handled-json", '["retry"]', "--duration-ms", "12", "--format", output_format])
    run_ledger.main()
    output = capsys.readouterr().out
    if output_format == "json":
        assert json.loads(output)["status"] == "completed"
    else:
        assert output.strip() == "draft: completed"
    saved = run_ledger.load_ledger(tmp_path)["write"]["chapter_003"]
    assert saved["mode"] == "fast"
    entry = saved["steps"]["draft"]
    assert entry["problems"] == ["slow"]
    assert entry["auto_handled"] == ["retry"]
    assert entry["duration_ms"] == 12
    assert entry["outputs"]["prose"]["sha256"] == run_ledger.file_signature(prose)["sha256"]
    monkeypatch.setattr(sys, "argv", ["run-ledger", "--project-root", str(tmp_path),
        "write-resume", "--chapter", "3", "--format", output_format])
    run_ledger.main()
    output = capsys.readouterr().out
    if output_format == "json":
        assert json.loads(output)["chapter"] == 3
    else:
        assert "chapter: 3" in output and "resume_from:" in output


@pytest.mark.parametrize("option,value", [
    ("--inputs-json", "{"), ("--outputs-json", "[]"),
    ("--problems-json", "{"), ("--auto-handled-json", "{}"),
])
def test_record_cli_rejects_bad_metadata_without_writing(tmp_path, monkeypatch, option, value):
    monkeypatch.setattr(sys, "argv", ["run-ledger", "--project-root", str(tmp_path),
        "record-write-step", "--chapter", "1", "--step", "draft", "--status", "completed", option, value])
    with pytest.raises(SystemExit):
        run_ledger.main()
    assert not run_ledger.ledger_path(tmp_path).exists()


def test_resume_text_keeps_confirmation_and_step_reason():
    plan = {"chapter": 2, "resume_from": "draft", "steps": [
        {"step": "draft", "action": "confirm", "reason": "manual edit"}],
        "needs_user_confirmation": [{"code": "prose_changed", "message": "Keep manual changes?"}]}
    text = run_ledger.format_resume_plan(plan, "text")
    assert "draft: confirm (manual edit)" in text
    assert "needs_user_confirmation:" in text
    assert "prose_changed: Keep manual changes?" in text
    assert json.loads(run_ledger.format_resume_plan(plan)) == plan


def test_ledger_parser_empty_inputs_and_wrong_step(tmp_path):
    assert run_ledger._parse_path_map("") == {}
    assert run_ledger._parse_string_list("") == []
    assert run_ledger._parse_path_map('{"chapter": 3}') == {"chapter": "3"}
    assert run_ledger._parse_string_list('[3]') == ["3"]
    with pytest.raises(ValueError, match="unknown write step"):
        run_ledger.record_write_step(tmp_path, chapter=1, step="unknown", status="completed")
    assert not run_ledger.ledger_path(tmp_path).exists()


@pytest.mark.parametrize("output_format", ["json", "text"])
def test_log_cli_redacts_nested_secrets_and_appends(tmp_path, monkeypatch, capsys, output_format):
    payload = {"items": [{"api_key": "secret-value"}, "password=hidden", 7], "safe": True}
    for event, append in [("start", []), ("finish", ["--append"])]:
        monkeypatch.setattr(sys, "argv", ["run-log", "--project-root", str(tmp_path),
            "--event", event, "--payload-json", json.dumps(payload), "--format", output_format, *append])
        run_logger.main()
        output = capsys.readouterr().out
        assert "secret-value" not in output and "hidden" not in output
        if output_format == "json":
            assert json.loads(output)["record"]["event"] == event
        else:
            assert output.strip() == str(run_logger.log_path(tmp_path))
    records = [json.loads(line) for line in run_logger.log_path(tmp_path).read_text().splitlines()]
    assert [r["event"] for r in records] == ["start", "finish"]
    assert records[0]["payload"] == {"items": [{"api_key": "<redacted>"}, "password=<redacted>", 7], "safe": True}


@pytest.mark.parametrize("payload", ["{", "[]"])
def test_log_cli_rejects_invalid_payload_before_creating_log(tmp_path, monkeypatch, payload):
    monkeypatch.setattr(sys, "argv", ["run-log", "--project-root", str(tmp_path),
        "--event", "start", "--payload-json", payload])
    with pytest.raises(SystemExit):
        run_logger.main()
    assert not run_logger.log_path(tmp_path).exists()
