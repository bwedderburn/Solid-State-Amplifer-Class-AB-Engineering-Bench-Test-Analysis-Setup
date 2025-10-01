from amp_benchkit import __version__

def test_version_semver():
    parts = __version__.split('.')
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts), "Version should be numeric semver-like"
