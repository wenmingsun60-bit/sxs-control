# Contributing

Please open a GitHub issue for a reproducible defect or discuss a larger feature before implementation. Include Windows/Python versions, an anonymized minimal example and the expected behavior. Never attach real device configuration, credentials, screenshots with private content or unrestricted debug logs.

Install with `python -m pip install -e .`. Run `python -m unittest discover -s tests -v` and `python scripts/check_release.py`. On Windows, also run `python scripts/windows_smoke.py`. Tests must use temporary files and must not operate on the contributor's real desktop inputs or registry.

Keep stdio stdout reserved for JSON-RPC. Keep HTTP loopback-only. Preserve the local-only product scope. Describe user-visible compatibility changes in `CHANGELOG.md`. Add focused regression coverage when fixing a behavioral bug.

For third-party code, include its repository URL, original file, revision and license; preserve notices and check compatibility before proposing a copy. Prefer a dependency or a small clearly documented adapter over copying unknown source.

By submitting a contribution, you confirm that you have permission to submit it and agree to license your contribution under this repository's MIT license. The same terms do not override existing third-party licenses.

