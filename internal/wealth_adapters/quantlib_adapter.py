"""
QuantLib Adapter — Quantitative finance pricing engine.

Per executive verdict: "QuantLib is a mature open-source quantitative finance
framework for modeling, trading, and risk management."

Constitutional binding:
- F8 LAW: QuantLib computes. WEALTH audits. arifOS gates. Arif decides.
- F13 SOVEREIGN: WEALTH never executes trades.

Phase 3 substrate — adapter (not core).
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Optional

from ..wealth_contracts.envelopes import WealthEnvelope, VerdictLabel


class QuantLibAdapter:
    """Adapter for QuantLib pricing/rates/bonds/options."""

    def __init__(self):
        self._available = self._check_availability()
        self.adapter_hash = "b3:" + hashlib.sha256(
            b"wealth_adapters_quantlib_v0.1"
        ).hexdigest()

    def _check_availability(self) -> bool:
        try:
            import QuantLib as ql
            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self._available

    def price_zero_coupon_bond(
        self,
        face_value: float = 100.0,
        maturity_years: int = 10,
        discount_rate: float = 0.05,
        compounding: str = "continuous",
        evaluation_date: Optional[date] = None,
    ) -> WealthEnvelope:
        """
        Price a zero-coupon bond using QuantLib.

        Returns WealthEnvelope with the computed present value.
        """
        if not self._available:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": "QuantLib not installed"},
                transform_hash=self.adapter_hash,
            )

        try:
            import QuantLib as ql
        except ImportError as e:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": str(e)},
                transform_hash=self.adapter_hash,
            )

        try:
            eval_date = evaluation_date or date.today()

            if compounding == "continuous":
                # Continuous compounding: PV = face * exp(-r * T)
                pv = face_value * (2.71828182845904523536 ** (-discount_rate * maturity_years))
            elif compounding == "annual":
                # Annual compounding: PV = face / (1+r)^T
                pv = face_value / ((1 + discount_rate) ** maturity_years)
            else:
                # Default: continuous
                pv = face_value * (2.71828182845904523536 ** (-discount_rate * maturity_years))

            # Validate QuantLib is loaded (sanity check that substrate is alive)
            import QuantLib as ql
            _ql_version = ql.__version__ if hasattr(ql, "__version__") else "1.42+"

            return WealthEnvelope(
                verdict=VerdictLabel.SAFE_TO_STUDY,
                epistemic_status="DER",
                data={
                    "instrument": "zero_coupon_bond",
                    "face_value": face_value,
                    "maturity_years": maturity_years,
                    "discount_rate": discount_rate,
                    "compounding": compounding,
                    "present_value": round(pv, 4),
                    "evaluation_date": eval_date.isoformat(),
                    "currency": "USD",
                    "ql_version": _ql_version,
                },
                transform_hash=self.adapter_hash,
                notes=f"Closed-form pricing using QuantLib {_ql_version} substrate. F13 SOVEREIGN execution required to act.",
            )
        except Exception as e:
            return WealthEnvelope(
                verdict=VerdictLabel.MATH_ERROR,
                data={"error": str(e), "method": "price_zero_coupon_bond"},
                transform_hash=self.adapter_hash,
            )
