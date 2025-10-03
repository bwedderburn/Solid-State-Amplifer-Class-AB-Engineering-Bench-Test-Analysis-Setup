import os, sys, subprocess, json, textwrap, tempfile, pathlib

SCRIPT = pathlib.Path(__file__).parent.parent / 'unified_gui_layout.py'

# We verify that when AMP_BENCHKIT_ENABLE_U3 is NOT set the CLI JSON output
# for a command is clean (no leading warning lines). This guards against
# regressions like the earlier Exodriver warning polluting stdout.

def _run_freq_json(extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    cp = subprocess.run([sys.executable, str(SCRIPT), 'freq-gen', '--start', '10', '--stop', '20', '--points', '3', '--mode', 'linear', '--format', 'json'], capture_output=True, text=True, env=env)
    return cp.returncode, cp.stdout, cp.stderr


def test_u3_env_gating_clean_output():
    # Ensure variable absent / falsey
    for k in ('AMP_BENCHKIT_ENABLE_U3',):
        os.environ.pop(k, None)
    rc, out, err = _run_freq_json()
    assert rc == 0, err
    # Should start with '{' (JSON object) – no prior warning lines
    assert out.lstrip().startswith('{')
    data = json.loads(out)
    assert data['start'] == 10
    assert data['stop'] == 20
    # sanity: exactly 3 freq values
    assert len(data['frequencies']) == 3


def test_u3_env_gating_opt_in_does_not_pollute():
    # Setting the env should still produce clean JSON (any hardware errors
    # are captured/suppressed inside unified_gui_layout gating logic).
    rc, out, err = _run_freq_json({'AMP_BENCHKIT_ENABLE_U3': '1'})
    # We tolerate non-zero return if hardware path genuinely errors, but
    # output must still be parseable JSON. However, normal flow should remain rc==0.
    assert out.lstrip().startswith('{')
    data = json.loads(out)
    assert data['frequencies'][0] == 10
