# BASELINE — forecast/wave_forge/tests collection errors (8) · recorded 2026-10-25

**State:** PRE-EXISTING, baselined per repair-to-release mandate. Not caused by
077d2c9f (test fix) or f2e9f7d (contract reversal).

**Reproduce:** `python3 -m pytest forecast/wave_forge/tests -q --co`
**Observed (2026-10-25, 333-AGI):** `Interrupted: 8 errors during collection` —
ALL 8 are one root cause:
`ModuleNotFoundError: No module named 'pywt'` (PyWavelets).
Files: test_000_causality, test_111_decomposer, test_222_wave_state,
test_333_path_forge, test_444_stability, test_555_auditor, test_888_judge,
test_e2e_pipeline.

**Verified in BOTH interpreters** (system python3 AND /root/WEALTH/.venv/bin/python)
— so this is a real missing dependency, not a venv-vs-system artifact. `pywavelets`
is NOT declared in pyproject.toml/uv.lock.

**Named follow-up (not done here):** declare `pywavelets` in the wave_forge
dependency set (pyproject → uv sync), then the 8 tests can collect and their real
pass/fail state becomes measurable. Until then these 8 are KNOWN-UNMEASURED, not
passing and not failing — do not count them either way in CI health.
