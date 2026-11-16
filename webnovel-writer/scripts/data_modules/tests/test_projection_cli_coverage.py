"""Exercise projection recovery diagnostics without modifying story canon."""
import json
from pathlib import Path

import pytest

from data_modules import projections
from data_modules.write_gates import format_gate_report, gate_report, issue, run_write_gate


@pytest.mark.parametrize('contents,error', [('broken{', 'invalid_json:'), ('[]', 'commit_not_object')])
def test_retry_reports_invalid_commit(tmp_path, contents, error):
    path = tmp_path / '.story-system/commits/chapter_001.commit.json'
    path.parent.mkdir(parents=True)
    path.write_text(contents)
    report = projections.retry_projection(tmp_path, chapter=1)
    assert report['ok'] is False
    assert report['error'].startswith(error)
    assert path.read_text() == contents


def test_unreadable_commit_reports_error(tmp_path, monkeypatch):
    path = tmp_path / 'commit.json'
    path.write_text('{}')
    def denied(self, **kwargs):
        raise PermissionError('denied')
    monkeypatch.setattr(Path, 'read_text', denied)
    payload, error = projections._read_commit(path)
    assert payload == {}
    assert error == 'read_error:denied'


@pytest.mark.parametrize('start,end', [(0, 1), (1, 0), (2, 1)])
def test_replay_rejects_invalid_range(tmp_path, start, end):
    report = projections.replay_projections(tmp_path, start_chapter=start, end_chapter=end)
    assert not report['ok']
    assert report['error'] == 'invalid_chapter_range'
    assert report['results'] == []
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('action,args', [('retry', ['--chapter', '1']), ('replay', ['--from-chapter', '1', '--to-chapter', '2'])])
def test_projection_cli_missing_commit_fails_with_actionable_text(tmp_path, monkeypatch, capsys, action, args):
    monkeypatch.setattr('sys.argv', ['projections', '--project-root', str(tmp_path), action, *args, '--format', 'text'])
    with pytest.raises(SystemExit) as exc:
        projections.main()
    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert f'ERROR projections {action}' in output
    assert 'missing_commit' in output
    if action == 'replay':
        assert '- chapter 1: ERROR' in output
        assert '- chapter 2: ERROR' in output


@pytest.mark.parametrize('action,args', [('retry', ['--chapter', '3']), ('replay', ['--from-chapter', '3', '--to-chapter', '4'])])
def test_projection_cli_success_exit_and_json(tmp_path, monkeypatch, capsys, action, args):
    calls = []
    def retry(root, *, chapter):
        calls.append((root, chapter))
        return {'ok': True, 'action': 'retry', 'chapter': chapter, 'projection_status': {'state': 'done'}}
    monkeypatch.setattr(projections, 'retry_projection', retry)
    monkeypatch.setattr('sys.argv', ['projections', '--project-root', str(tmp_path), action, *args])
    with pytest.raises(SystemExit) as exc:
        projections.main()
    assert exc.value.code == 0
    result = json.loads(capsys.readouterr().out)
    assert result['ok'] is True
    assert [chapter for _, chapter in calls] == ([3] if action == 'retry' else [3, 4])


def test_gate_report_text_retains_recovery_details(tmp_path):
    blocker = issue('MISSING', message='Missing review', path='review.json', impact='Cannot commit', repair='Run reviewer')
    warning = issue('SLOW', message='Review took longer', severity='warning')
    report = gate_report(stage='precommit', project_root=tmp_path, chapter=2, phase='review', errors=[blocker], warnings=[warning])
    assert report['ok'] is False
    assert json.loads(format_gate_report(report)) == report
    text = format_gate_report(report, 'text')
    for expected in ['ERROR write-gate precommit', 'chapter: 2', 'ERROR MISSING: Missing review', 'path: review.json', 'impact: Cannot commit', 'repair: Run reviewer', 'WARNING SLOW: Review took longer']:
        assert expected in text
    assert 'OK write-gate precommit' in format_gate_report(gate_report(stage='precommit', project_root=tmp_path, chapter=2, phase='ready'), 'text')


def test_unknown_gate_stage_is_rejected(tmp_path):
    with pytest.raises(ValueError, match='unknown write-gate stage: typo'):
        run_write_gate(tmp_path, chapter=1, stage='typo')


def test_invalid_projection_status_is_not_success():
    assert projections._projection_failed({'projection_status': ['done']}) is True
