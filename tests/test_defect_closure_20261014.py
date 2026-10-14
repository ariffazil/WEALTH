"""
WEALTH_THREE_DEFECT_CLOSURE_20261014 — minimum regression contract for D1/D2/D3.

D1  capital_health sovereign_fiscal      — canonical payload must yield a
     structured fiscal result with resolved-mode reflection; invalid input
     must fail explicitly (structured UNKNOWN_MODE / MISSING_REQUIRED_PARAMS),
     never a bare raise (the historical -32602 crash shape).
D2  capital_health corporate_runway      — must resolve to the corporate
     branch (never personal_finance), reflect resolved mode, keep corporate
     fields, differ materially across payloads, and reject personal-only
     fields explicitly instead of silently dropping them.
D3  capital_diagnose collapse_signature  — top-level domain_scope must be
     consumed (scenario chain + corpus prior + output reflection); different
     scopes must differ; unknown scopes must be rejected; empty input must
     not produce a confident negative.

Receipts: /root/WEALTH/forge_work/wealth_defect_closure_20261014/
Fail-closed: these tests assert OBSERVED behavior of the live tool layer.
"""

from __future__ import annotations

import json

import pytest

# NOTE: do NOT insert tests/ onto sys.path — tests/mcp/ is a local package
# that would shadow the MCP SDK (`mcp.server`) and break fastmcp imports.
from tests.test_monotonicity import _tool_fn  # noqa: E402

_FISCAL = {
    # Engine-canonical units: RM billions per fiscal_breakeven_oil_price docstring
    "total_govt_expenditure": 380.0,
    "non_oil_revenue": 260.0,
    "petronas_dividend_base_rm": 40.0,
    "oil_price_assumption_usd": 80.0,
}


async def _health(**kw):
    fn = _tool_fn("capital_health")
    return await fn(**kw)


async def _diagnose(**kw):
    fn = _tool_fn("capital_diagnose")
    return await fn(**kw)


# ═══ D1 — sovereign_fiscal ═════════════════════════════════════════════════


class TestD1SovereignFiscal:
    @pytest.mark.asyncio
    async def test_d1_canonical_payload_structured_result(self):
        """Canonical sovereign_fiscal payload → structured fiscal result."""
        r = await _health(
            mode="survival", survival_submode="sovereign_fiscal", **_FISCAL
        )
        res = r.get("result", {})
        assert res.get("status") != "ERROR", res.get("message")
        for key in (
            "breakeven_price_usd",
            "current_deficit_rm_b",
            "fiscal_sensitivity_rm_b_per_usd",
        ):
            assert key in res, f"missing {key}"
        # Material sovereign fields detectable in output
        assert res.get("total_govt_expenditure_rm_b") is not None
        assert res.get("non_oil_revenue_rm_b") is not None
        assert res.get("petronas_dividend_base_rm_b") is not None
        assert res.get("current_oil_price_usd") == 80.0

    @pytest.mark.asyncio
    async def test_d1_resolved_mode_reflected(self):
        r = await _health(
            mode="survival", survival_submode="sovereign_fiscal", **_FISCAL
        )
        res = r.get("result", {})
        assert res.get("mode") == "survival"
        assert res.get("survival_submode") == "sovereign_fiscal"

    @pytest.mark.asyncio
    async def test_d1_partial_fiscal_explicit_error(self):
        """Missing fiscal params → explicit structured error, no raise."""
        r = await _health(
            mode="survival",
            survival_submode="sovereign_fiscal",
            total_govt_expenditure=380.0,
            petronas_dividend_base_rm=40.0,
        )
        res = r.get("result", {})
        assert res.get("status") == "ERROR"
        assert res.get("error_code") == "MISSING_REQUIRED_PARAMS"
        assert set(res.get("missing_params", [])) == {
            "non_oil_revenue",
            "oil_price_assumption_usd",
        }

    @pytest.mark.asyncio
    async def test_d1_unknown_mode_structured_not_raised(self):
        """mode='sovereign_fiscal' (not a mode) → structured UNKNOWN_MODE.

        A bare raise here exits as INTERNAL_ERROR/FATAL/ESCALATE_TO_888 —
        the historical crash classification. Must not raise.
        """
        r = await _health(mode="sovereign_fiscal", **_FISCAL)
        res = r.get("result", {})
        assert res.get("status") == "ERROR"
        assert res.get("error_code") == "UNKNOWN_MODE"
        assert "survival" in res.get("valid_modes", [])

    @pytest.mark.asyncio
    async def test_d1_garbage_mode_structured(self):
        r = await _health(mode="garbage_mode_test")
        res = r.get("result", {})
        assert res.get("error_code") == "UNKNOWN_MODE"


# ═══ D2 — corporate_runway ═════════════════════════════════════════════════


class TestD2CorporateRunway:
    @pytest.mark.asyncio
    async def test_d2_resolves_corporate_not_personal(self):
        r = await _health(
            mode="survival",
            survival_submode="corporate_runway",
            liquid_assets=12_000_000.0,
            monthly_burn=1_000_000.0,
        )
        res = r.get("result", {})
        assert res.get("status") != "ERROR", res.get("message")
        assert res.get("mode") == "survival"
        assert res.get("survival_submode") == "corporate_runway"
        # No personal_finance downgrade artifacts
        assert "assumptions" not in res
        assert res.get("verdict", "").startswith("CORPORATE_RUNWAY_")

    @pytest.mark.asyncio
    async def test_d2_corporate_fields_survive(self):
        r = await _health(
            mode="survival",
            survival_submode="corporate_runway",
            liquid_assets=12_000_000.0,
            monthly_burn=1_000_000.0,
        )
        res = r.get("result", {})
        assert res.get("liquid_assets") == 12_000_000.0
        assert res.get("monthly_burn") == 1_000_000.0
        assert res.get("runway_months") == 12.0

    @pytest.mark.asyncio
    async def test_d2_payloads_materially_different(self):
        ra = await _health(
            mode="survival",
            survival_submode="corporate_runway",
            liquid_assets=12_000_000.0,
            monthly_burn=2_000_000.0,
        )
        rb = await _health(
            mode="survival",
            survival_submode="corporate_runway",
            liquid_assets=12_000_000.0,
            monthly_burn=1_000_000.0,
        )
        a, b = ra.get("result", {}), rb.get("result", {})
        assert a.get("runway_months") == 6.0
        assert b.get("runway_months") == 12.0
        assert a.get("verdict") != b.get("verdict")

    @pytest.mark.asyncio
    async def test_d2_missing_required_explicit(self):
        r = await _health(mode="survival", survival_submode="corporate_runway")
        res = r.get("result", {})
        assert res.get("status") == "ERROR"
        assert res.get("error_code") == "MISSING_REQUIRED_PARAMS"
        assert set(res.get("missing_params", [])) == {"liquid_assets", "monthly_burn"}

    @pytest.mark.asyncio
    async def test_d2_personal_fields_rejected_not_dropped(self):
        """Personal-finance fields with corporate submode → explicit rejection."""
        r = await _health(
            mode="survival",
            survival_submode="corporate_runway",
            liquid_assets=5_000_000.0,
            monthly_burn=500_000.0,
            income=[{"name": "rev", "amount": 300000.0}],
            expenses=[{"name": "opex", "amount": 100000.0}],
        )
        res = r.get("result", {})
        assert res.get("status") == "ERROR"
        assert res.get("error_code") == "UNSUPPORTED_FIELDS"
        assert set(res.get("unsupported_fields", [])) == {"income", "expenses"}


# ═══ D3 — collapse_signature.domain_scope ══════════════════════════════════


def _norm(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


class TestD3CollapseSignatureDomainScope:
    @pytest.mark.asyncio
    async def test_d3_top_level_scope_consumed_and_reflected(self):
        r = await _diagnose(mode="collapse_signature", domain_scope="enron_2000")
        res = r.get("result", {})
        assert res.get("status") != "ERROR", res.get("message")
        assert res.get("domain_scope") == "enron_2000"
        assert res.get("domain_scope_resolved") == "enron_2000_ar"
        assert res.get("priors_used") == ["enron_2000_ar"]

    @pytest.mark.asyncio
    async def test_d3_source_text_populated(self):
        r = await _diagnose(mode="collapse_signature", domain_scope="enron_2000")
        profile = r.get("result", {}).get("profile", {})
        assert profile.get("_source_text") == "enron_2000"

    @pytest.mark.asyncio
    async def test_d3_scope_differential(self):
        """Materially different scopes must produce explainable differences."""
        ra = await _diagnose(mode="collapse_signature", domain_scope="enron_2000")
        rb = await _diagnose(mode="collapse_signature", domain_scope="enron_1999")
        a, b = ra.get("result", {}), rb.get("result", {})
        assert a.get("domain_scope_resolved") == "enron_2000_ar"
        assert b.get("domain_scope_resolved") == "enron_1999_ar"
        assert _norm(a) != _norm(b)

    @pytest.mark.asyncio
    async def test_d3_unsupported_scope_rejected(self):
        r = await _diagnose(mode="collapse_signature", domain_scope="planet_mars_2199")
        res = r.get("result", {})
        assert res.get("status") == "ERROR"
        assert res.get("error_code") == "UNSUPPORTED_DOMAIN_SCOPE"
        assert "enron_2000_ar" in res.get("available_scopes", [])

    @pytest.mark.asyncio
    async def test_d3_blank_scope_no_confident_negative(self):
        """No narrative and no scope → explicit MISSING_REQUIRED_INPUT.

        Removing domain_scope must not silently preserve an affirmative
        (MINIMAL 'no signature') result built on zero evidence.
        """
        r = await _diagnose(mode="collapse_signature")
        res = r.get("result", {})
        assert res.get("status") == "ERROR"
        assert res.get("error_code") == "MISSING_REQUIRED_INPUT"

    @pytest.mark.asyncio
    async def test_d3_payload_narrative_backcompat(self):
        """Payload narrative text still drives the analysis (no regression)."""
        r = await _diagnose(
            mode="collapse_signature",
            payload={
                "scenario": (
                    "Company with off-balance-sheet vehicles, related-party "
                    "transactions, mark-to-market accounting."
                )
            },
        )
        res = r.get("result", {})
        assert res.get("status") != "ERROR"
        assert res.get("domain_scope_resolved") is None
        assert "profile" in res

    @pytest.mark.asyncio
    async def test_d3_payload_scope_still_works(self):
        """Payload-embedded domain_scope keeps working (pre-fix path)."""
        r = await _diagnose(
            mode="collapse_signature", payload={"domain_scope": "enron_2000"}
        )
        res = r.get("result", {})
        assert res.get("domain_scope") == "enron_2000"
        assert res.get("domain_scope_resolved") == "enron_2000_ar"


if __name__ == "__main__":
    raise SystemExit(
        pytest.main(
            [
                __file__,
                "-v",
                "--no-header",
                "-p",
                "no:cacheprovider",
            ]
        )
    )
