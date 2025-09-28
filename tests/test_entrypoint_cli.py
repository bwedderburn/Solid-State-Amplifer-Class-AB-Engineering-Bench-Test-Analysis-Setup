import sys
from amp_benchkit import cli

def test_cli_sweep_invoke(monkeypatch, capsys):
    # Provide arguments to generate a small linear sweep
    monkeypatch.setattr(sys, 'argv', ['amp-benchkit', 'sweep', '--start', '1', '--stop', '2', '--points', '2', '--mode', 'linear'])
    try:
        rc = cli.main()
        # If legacy main returned instead of exiting, rc should be 0
        assert rc == 0
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert out == ['1', '2']

def test_cli_error_exit(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['amp-benchkit', 'sweep', '--start', '1', '--stop', '2', '--points', '1'])
    try:
        cli.main()
        # If no SystemExit, treat as failure because underlying main uses sys.exit
        assert False, 'Expected SystemExit for invalid points'
    except SystemExit as e:
        assert e.code != 0
