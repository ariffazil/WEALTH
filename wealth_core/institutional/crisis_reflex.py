"""
WEALTH Core — Crisis Reflex (Channel H).

Answers one question: When pressure arrives, what does the institution
protect, sacrifice, conceal and centralise first?

Core design:
  - 8 dimensions, each with TWO values:
      protection_priority: 0.0–1.0 (what is shielded)
      sacrifice_exposure: 0.0–1.0 (what is cut/exposed)
  - Never collapsed into a single score until the composite
  - No motive inference: workforce cut ≠ exploitation.
    executive retained ≠ corruption.
    Those become findings only when supporting patterns converge.

DITEMPA BUKAN DIBERI — Forged 2026-07-12.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def compute_crisis_reflex(
    capital_allocation: Optional[List[Dict[str, Any]]] = None,
    capability_moves: Optional[List[Dict[str, Any]]] = None,
    truth_events: Optional[List[Dict[str, Any]]] = None,
    burden_data: Optional[Dict[str, Any]] = None,
    decision_shifts: Optional[List[Dict[str, Any]]] = None,
    recovery_data: Optional[Dict[str, Any]] = None,
    external_events: Optional[List[Dict[str, Any]]] = None,
    dignity_data: Optional[List[Dict[str, Any]]] = None,
    org_name: str = "",
) -> Dict[str, Any]:
    """
    Compute crisis reflex profile across 8 dimensions.

    Each dimension produces:
      - protection_priority: 0.0–1.0
      - sacrifice_exposure: 0.0–1.0
      - epistemic_tag: OBSERVED | DERIVED | PLAUSIBLE | HYPOTHESIS | UNKNOWN

    Returns composite reflex profile with band classification.
    """
    dimensions: Dict[str, Any] = {}
    warnings: List[str] = []
    data_count = 0

    # ── 1. Capital Protection ─────────────────────────────────────────
    if capital_allocation and len(capital_allocation) >= 1:
        data_count += 1
        dim = _score_capital_protection(capital_allocation)
        dimensions["capital_protection"] = dim
        if dim.get("warning"):
            warnings.append(dim["warning"])
    else:
        dimensions["capital_protection"] = {
            "protection_priority": None,
            "sacrifice_exposure": None,
            "epistemic_tag": "UNKNOWN",
            "status": "UNKNOWN",
        }
        warnings.append("CAPITAL_DATA: Insufficient capital allocation data")

    # ── 2. Capability Protection ──────────────────────────────────────
    if capability_moves and len(capability_moves) >= 1:
        data_count += 1
        dim = _score_capability_protection(capability_moves)
        dimensions["capability_protection"] = dim
        if dim.get("warning"):
            warnings.append(dim["warning"])
    else:
        dimensions["capability_protection"] = {
            "protection_priority": None,
            "sacrifice_exposure": None,
            "epistemic_tag": "UNKNOWN",
            "status": "UNKNOWN",
        }
        warnings.append("CAPABILITY_DATA: Insufficient capability movement data")

    # ── 3. Truth Protection ───────────────────────────────────────────
    if truth_events and len(truth_events) >= 1:
        data_count += 1
        dim = _score_truth_protection(truth_events)
        dimensions["truth_protection"] = dim
        if dim.get("warning"):
            warnings.append(dim["warning"])
    else:
        dimensions["truth_protection"] = {
            "protection_priority": None,
            "sacrifice_exposure": None,
            "epistemic_tag": "UNKNOWN",
            "status": "UNKNOWN",
        }
        warnings.append("TRUTH_DATA: Insufficient truth event data")

    # ── 4. Burden Distribution ────────────────────────────────────────
    if burden_data:
        data_count += 1
        dim = _score_burden_distribution(burden_data)
        dimensions["burden_distribution"] = dim
        if dim.get("warning"):
            warnings.append(dim["warning"])
    else:
        dimensions["burden_distribution"] = {
            "protection_priority": None,
            "sacrifice_exposure": None,
            "epistemic_tag": "UNKNOWN",
            "status": "UNKNOWN",
        }
        warnings.append("BURDEN_DATA: Insufficient burden distribution data")

    # ── 5. Decision Reflex ────────────────────────────────────────────
    if decision_shifts and len(decision_shifts) >= 1:
        data_count += 1
        dim = _score_decision_reflex(decision_shifts)
        dimensions["decision_reflex"] = dim
        if dim.get("warning"):
            warnings.append(dim["warning"])
    else:
        dimensions["decision_reflex"] = {
            "protection_priority": None,
            "sacrifice_exposure": None,
            "epistemic_tag": "UNKNOWN",
            "status": "UNKNOWN",
        }
        warnings.append("DECISION_DATA: Insufficient decision shift data")

    # ── 6. Recovery Investment ────────────────────────────────────────
    if recovery_data:
        data_count += 1
        dim = _score_recovery_investment(recovery_data)
        dimensions["recovery_investment"] = dim
        if dim.get("warning"):
            warnings.append(dim["warning"])
    else:
        dimensions["recovery_investment"] = {
            "protection_priority": None,
            "sacrifice_exposure": None,
            "epistemic_tag": "UNKNOWN",
            "status": "UNKNOWN",
        }
        warnings.append("RECOVERY_DATA: Insufficient recovery investment data")

    # ── 7. External Posture ───────────────────────────────────────────
    if external_events and len(external_events) >= 1:
        data_count += 1
        dim = _score_external_posture(external_events)
        dimensions["external_posture"] = dim
        if dim.get("warning"):
            warnings.append(dim["warning"])
    else:
        dimensions["external_posture"] = {
            "protection_priority": None,
            "sacrifice_exposure": None,
            "epistemic_tag": "UNKNOWN",
            "status": "UNKNOWN",
        }
        warnings.append("EXTERNAL_DATA: Insufficient external event data")

    # ── 8. Human Dignity ──────────────────────────────────────────────
    if dignity_data and len(dignity_data) >= 1:
        data_count += 1
        dim = _score_human_dignity(dignity_data)
        dimensions["human_dignity"] = dim
        if dim.get("warning"):
            warnings.append(dim["warning"])
    else:
        dimensions["human_dignity"] = {
            "protection_priority": None,
            "sacrifice_exposure": None,
            "epistemic_tag": "UNKNOWN",
            "status": "UNKNOWN",
        }
        warnings.append("DIGNITY_DATA: Insufficient dignity data")

    # ── Composite ─────────────────────────────────────────────────────
    active_dims = {
        k: v for k, v in dimensions.items() if v.get("protection_priority") is not None
    }

    if not active_dims:
        return {
            "crisis_reflex": None,
            "band": "INSUFFICIENT_DATA",
            "dimensions": dimensions,
            "key_signals": [],
            "warnings": warnings + ["No data for any crisis reflex dimension"],
            "alternative_explanations": [
                "No measurement possible without data",
                "Institution may have protective reflexes but no data was supplied",
            ],
            "falsification_test": "Provide data for at least one dimension",
            "data_dimensions_active": 0,
            "data_dimensions_total": 8,
            "org_name": org_name,
        }

    # Composite: average protection vs average sacrifice
    avg_protection = sum(d["protection_priority"] for d in active_dims.values()) / len(
        active_dims
    )

    avg_sacrifice = sum(d["sacrifice_exposure"] for d in active_dims.values()) / len(
        active_dims
    )

    # Net = protection - sacrifice. Positive = regenerative, negative = extractive
    net = avg_protection - avg_sacrifice
    # Normalise to 0.0-1.0 where 0.5 = neutral
    composite = 0.5 + (net / 2)
    composite = max(0.0, min(1.0, composite))

    band = _classify_band(composite)
    key_signals = _extract_signals(active_dims)

    alternative_explanations = _generate_alternatives(
        active_dims, band, data_count, key_signals
    )
    falsification_test = _generate_falsification(band, key_signals)

    return {
        "crisis_reflex": round(composite, 4),
        "band": band,
        "avg_protection_priority": round(avg_protection, 4),
        "avg_sacrifice_exposure": round(avg_sacrifice, 4),
        "net_protection_minus_sacrifice": round(net, 4),
        "dimensions": dimensions,
        "key_signals": key_signals,
        "warnings": warnings,
        "alternative_explanations": alternative_explanations,
        "falsification_test": falsification_test,
        "data_dimensions_active": len(active_dims),
        "data_dimensions_total": 8,
        "org_name": org_name,
    }


# ── Dimension Scorers ───────────────────────────────────────────────────


def _score_capital_protection(
    data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Capital protection: what gets funded vs cut.
    High protection_priority = dividends, exec costs, cash preserved.
    High sacrifice_exposure = people, renewal, R&D cut.
    """
    allocation = data[-1]
    evidence = []

    cuts = allocation.get("cuts", {})
    protected = allocation.get("protected", {})

    # Sacrifice: what got cut
    people_cut = cuts.get("people_pct", 0)
    renewal_cut = cuts.get("renewal_pct", 0)
    r_and_d_cut = cuts.get("r_and_d_pct", 0)
    maintenance_cut = cuts.get("maintenance_pct", 0)

    # Protection: what stayed
    dividend_kept = protected.get("dividend_pct", 100)
    exec_cost_kept = protected.get("exec_cost_pct", 100)
    cash_reserve = protected.get("cash_reserve_pct", 100)

    sacrifice_exposure = (
        people_cut + renewal_cut + r_and_d_cut + maintenance_cut
    ) / 400  # normalise to 0-1

    protection_priority = (
        (100 - dividend_kept) + (100 - exec_cost_kept) + (100 - cash_reserve)
    ) / 300  # lower = more protected

    # Invert: higher protection_priority = protected
    protection_priority = 1.0 - protection_priority

    sacrifice_exposure = min(1.0, sacrifice_exposure)
    protection_priority = max(0.0, min(1.0, protection_priority))

    if people_cut > 30:
        evidence.append(f"People cut {people_cut:.0f}%")
    if renewal_cut > 20:
        evidence.append(f"Renewal/R&D cut {renewal_cut:.0f}%")
    if dividend_kept > 90:
        evidence.append("Dividends maintained near 100%")
    if exec_cost_kept > 95:
        evidence.append("Executive costs preserved")

    warning = None
    if people_cut > 30 and dividend_kept > 90:
        warning = (
            f"CAPITAL_ASYMMETRY: People cut {people_cut:.0f}% while "
            f"dividends maintained at {dividend_kept:.0f}%"
        )

    return {
        "protection_priority": round(protection_priority, 4),
        "sacrifice_exposure": round(sacrifice_exposure, 4),
        "evidence": evidence,
        "epistemic_tag": "DERIVED",
        "warning": warning,
    }


def _score_capability_protection(
    data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Capability protection: are technical experts moved or protected?
    High protection = senior experts retained with authority.
    High sacrifice = expertise removed without succession.
    """
    moves = data[-1]
    evidence = []

    senior_moved = moves.get("senior_technical_moved", 0)
    senior_exited = moves.get("senior_technical_exited", 0)
    succession_rate = moves.get(
        "succession_rate_pct", 100
    )  # % of key roles with successor
    consultant_dependence = moves.get("consultant_dependence_pct", 0)
    total_senior = moves.get("total_senior_technical", 1)

    total_loss = senior_moved + senior_exited
    loss_rate = total_loss / max(total_senior, 1)

    # Sacrifice: loss rate + consultant dependence
    sacrifice_exposure = (loss_rate * 0.6) + (consultant_dependence / 100 * 0.4)
    sacrifice_exposure = min(1.0, sacrifice_exposure)

    # Protection: succession coverage + retained proportion
    protection_priority = (succession_rate / 100) * (1.0 - loss_rate)
    protection_priority = max(0.0, min(1.0, protection_priority))

    if senior_moved > 0:
        evidence.append(f"{senior_moved} senior technical roles moved")
    if senior_exited > 0:
        evidence.append(f"{senior_exited} senior technical exits")
    if succession_rate < 50:
        evidence.append(f"Succession rate at {succession_rate:.0f}%")
    if consultant_dependence > 30:
        evidence.append(f"Consultant dependence at {consultant_dependence:.0f}%")

    warning = None
    if loss_rate > 0.2 and succession_rate < 50:
        warning = (
            f"CAPABILITY_LOSS: {total_loss} senior technical roles lost ({loss_rate:.0%}) "
            f"with {succession_rate:.0f}% succession coverage"
        )

    return {
        "protection_priority": round(protection_priority, 4),
        "sacrifice_exposure": round(sacrifice_exposure, 4),
        "evidence": evidence,
        "epistemic_tag": "DERIVED",
        "warning": warning,
    }


def _score_truth_protection(
    data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Truth protection: does bad news reach the centre?
    High protection = dissent safe, bad news travels fast.
    High sacrifice = messengers punished, data removed.
    """
    events = data[-1]
    evidence = []

    messenger = events.get("messenger_treatment", "unknown")
    data_removed = events.get("data_removed_from_reports", [])
    definition_changes = events.get("definition_changes", [])
    internal_comms = events.get("internal_communication", "unknown")
    disclosure_delay = events.get("public_disclosure_days", 30)

    if messenger == "protected":
        protection_priority = 0.9
        sacrifice_exposure = 0.1
        evidence.append("Messengers protected — dissent is safe")
    elif messenger == "ignored":
        protection_priority = 0.4
        sacrifice_exposure = 0.6
        evidence.append("Messengers ignored — dissent has no effect")
    elif messenger == "retaliated":
        protection_priority = 0.1
        sacrifice_exposure = 0.95
        evidence.append("Messengers retaliated against — dissent is punished")
    else:
        protection_priority = 0.5
        sacrifice_exposure = 0.5

    # Penalty for data removal
    removed_count = len(data_removed) if isinstance(data_removed, list) else 0
    if removed_count > 0:
        protection_priority -= 0.15 * min(removed_count, 3)
        sacrifice_exposure += 0.1 * min(removed_count, 3)
        evidence.append(f"{removed_count} data series removed from reports")

    # Penalty for definition changes
    def_count = len(definition_changes) if isinstance(definition_changes, list) else 0
    if def_count > 0:
        protection_priority -= 0.1 * min(def_count, 3)
        evidence.append(f"{def_count} metric definitions changed")

    # Penalty for slow disclosure
    if disclosure_delay > 30:
        protection_priority -= 0.2
        evidence.append(f"Public disclosure delayed {disclosure_delay}d")

    if internal_comms == "suppressed":
        sacrifice_exposure += 0.15
        evidence.append("Internal communication suppressed")

    protection_priority = max(0.0, min(1.0, protection_priority))
    sacrifice_exposure = max(0.0, min(1.0, sacrifice_exposure))

    warning = None
    if messenger == "retaliated":
        warning = "TRUTH_SUPPRESSION: Messengers of bad news face retaliation"

    return {
        "protection_priority": round(protection_priority, 4),
        "sacrifice_exposure": round(sacrifice_exposure, 4),
        "evidence": evidence,
        "epistemic_tag": "DERIVED",
        "warning": warning,
    }


def _score_burden_distribution(
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Burden distribution: who absorbs the downside?
    High protection = burden shared across levels.
    High sacrifice = downside concentrated on weakest.
    """
    evidence = []

    workforce_cut = data.get("workforce_cut_pct", 0)
    exec_cut = data.get("exec_comp_cut_pct", 0)
    middle_cut = data.get("middle_mgmt_cut_pct", 0)
    contractor_cut = data.get("contractor_cut_pct", 0)

    # Who carries the burden?
    # Protective: exec, middle, workforce share proportionally
    # Extractive: workforce absorbs most, exec absorbs least
    total_data = sum(1 for v in [workforce_cut, exec_cut, middle_cut] if v > 0)

    if total_data >= 2:
        asymmetry = workforce_cut - exec_cut
        if asymmetry > 20:
            sacrifice_exposure = 0.8
            protection_priority = 0.2
            evidence.append(
                f"Burden asymmetrical: workforce cut {workforce_cut:.0f}% "
                f"vs exec {exec_cut:.0f}%"
            )
        elif asymmetry > 10:
            sacrifice_exposure = 0.6
            protection_priority = 0.4
        elif asymmetry < -5:
            sacrifice_exposure = 0.2
            protection_priority = 0.8
            evidence.append("Burden shared proportionally across levels")
        else:
            sacrifice_exposure = 0.4
            protection_priority = 0.6
            evidence.append("Moderate asymmetry in burden distribution")
    else:
        sacrifice_exposure = 0.5
        protection_priority = 0.5

    protection_priority = max(0.0, min(1.0, protection_priority))
    sacrifice_exposure = max(0.0, min(1.0, sacrifice_exposure))

    warning = None
    if workforce_cut - exec_cut > 20:
        warning = (
            f"BURDEN_ASYMMETRY: Workforce cut {workforce_cut:.0f}% vs "
            f"executive {exec_cut:.0f}%"
        )

    return {
        "protection_priority": round(protection_priority, 4),
        "sacrifice_exposure": round(sacrifice_exposure, 4),
        "evidence": evidence,
        "epistemic_tag": "DERIVED",
        "warning": warning,
    }


def _score_decision_reflex(
    data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Decision reflex: delegation vs centralisation during stress.
    High protection = decisions stay at competent level.
    High sacrifice = authority moves up, accountability moves down.
    """
    shifts = data[-1]
    evidence = []

    centralised = shifts.get("decisions_centralised_pct", 0)
    new_layers = shifts.get("new_approval_layers", 0)
    delegation_revoked = shifts.get("delegation_revoked", [])

    if centralised < 10:
        protection_priority = 0.9
        sacrifice_exposure = 0.1
        evidence.append("Decisions remain at operating level")
    elif centralised < 25:
        protection_priority = 0.6
        sacrifice_exposure = 0.4
        evidence.append(f"{centralised:.0f}% of decisions centralised upward")
    elif centralised < 50:
        protection_priority = 0.3
        sacrifice_exposure = 0.7
        evidence.append(
            f"{centralised:.0f}% centralised, {new_layers} new approval layers"
        )
    else:
        protection_priority = 0.1
        sacrifice_exposure = 0.95
        evidence.append(f"Over 50% centralised — authority concentrating rapidly")

    revoked_list = delegation_revoked if isinstance(delegation_revoked, list) else []
    if len(revoked_list) > 0:
        protection_priority -= 0.1 * min(len(revoked_list), 3)
        evidence.append(f"{len(revoked_list)} delegations revoked")

    protection_priority = max(0.0, min(1.0, protection_priority))
    sacrifice_exposure = max(0.0, min(1.0, sacrifice_exposure))

    warning = None
    if centralised > 40:
        warning = (
            f"DECISION_CENTRALISATION: {centralised:.0f}% of decisions moved upward "
            f"with {new_layers} new approval layers — accountability may not follow"
        )

    return {
        "protection_priority": round(protection_priority, 4),
        "sacrifice_exposure": round(sacrifice_exposure, 4),
        "evidence": evidence,
        "epistemic_tag": "DERIVED",
        "warning": warning,
    }


def _score_recovery_investment(
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Recovery investment: does the institution reinvest or consume?
    High protection = maintenance, exploration, hiring funded.
    High sacrifice = reserves consumed without replacement.
    """
    evidence = []

    maintenance_spend = data.get("maintenance_spend_pct", 100)  # % of required
    exploration_spend = data.get("exploration_spend_pct", 100)
    hiring_frozen = data.get("hiring_frozen", False)
    asset_sales = data.get("asset_sales_for_cash", False)
    r_and_d_spend = data.get("r_and_d_spend_pct", 100)

    avg_spend = (maintenance_spend + exploration_spend + r_and_d_spend) / 300
    sacrifice_exposure = 1.0 - avg_spend

    # Protection: keeping critical investment going
    protection_priority = avg_spend

    if hiring_frozen:
        protection_priority -= 0.15
        sacrifice_exposure += 0.1
        evidence.append("Hiring frozen")

    if asset_sales:
        protection_priority -= 0.1
        sacrifice_exposure += 0.15
        evidence.append("Assets sold to fund operations")

    if maintenance_spend < 50:
        evidence.append(f"Maintenance at {maintenance_spend:.0f}% of requirement")

    protection_priority = max(0.0, min(1.0, protection_priority))
    sacrifice_exposure = max(0.0, min(1.0, sacrifice_exposure))

    warning = None
    if maintenance_spend < 60 and asset_sales:
        warning = (
            f"RECOVERY_DEFICIT: Maintenance at {maintenance_spend:.0f}% + asset sales — "
            f"institution consuming reserves faster than replacing"
        )

    return {
        "protection_priority": round(protection_priority, 4),
        "sacrifice_exposure": round(sacrifice_exposure, 4),
        "evidence": evidence,
        "epistemic_tag": "DERIVED",
        "warning": warning,
    }


def _score_external_posture(
    data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    External posture: how does the institution behave when weakness is detected?
    High protection = counterparties respect boundaries.
    High sacrifice = institution concedes value under pressure.
    """
    events = data[-1]
    evidence = []

    litigation_count = events.get("active_litigation_count", 0)
    payment_freeze = events.get("payment_freeze_detected", False)
    freeze_amount = events.get("freeze_amount_musd", 0)
    renegotiations = events.get("forced_renegotiations", [])
    counterparty_advantage = events.get("counterparty_value_extraction", False)

    # Litigation can be offensive or defensive
    if litigation_count > 0:
        evidence.append(f"{litigation_count} active litigations")

    if payment_freeze:
        sacrifice_exposure = 0.8
        protection_priority = 0.2
        evidence.append(
            f"Payment freeze (~${freeze_amount}M) — counterparty extracting"
        )
    elif counterparty_advantage:
        sacrifice_exposure = 0.6
        protection_priority = 0.4
        evidence.append("Counterparty extracting value through legal leverage")
    else:
        sacrifice_exposure = 0.3
        protection_priority = 0.7
        evidence.append("External boundaries intact")

    renegotiation_list = renegotiations if isinstance(renegotiations, list) else []
    if len(renegotiation_list) > 0:
        sacrifice_exposure += 0.1 * min(len(renegotiation_list), 3)
        evidence.append(f"{len(renegotiation_list)} forced renegotiations")

    protection_priority = max(0.0, min(1.0, protection_priority))
    sacrifice_exposure = max(0.0, min(1.0, sacrifice_exposure))

    warning = None
    if payment_freeze:
        warning = (
            f"EXTERNAL_EXTRACTION: Payment freeze ~${freeze_amount}M — "
            f"counterparty exploiting institutional weakness"
        )

    return {
        "protection_priority": round(protection_priority, 4),
        "sacrifice_exposure": round(sacrifice_exposure, 4),
        "evidence": evidence,
        "epistemic_tag": "DERIVED",
        "warning": warning,
    }


def _score_human_dignity(
    data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Human dignity: are people treated as people or as metrics?
    High protection = notice, due process, transparency, support.
    High sacrifice = people reduced to ratings, files, removal categories.
    """
    events = data[-1]
    evidence = []

    notice_period = events.get("notice_period_weeks", 4)
    due_process = events.get("due_process_observed", True)
    support_provided = events.get("support_provided", True)
    people_as_metrics = events.get("people_reduced_to_ratings", False)
    dossier_pattern = events.get("dossier_pattern_detected", False)

    if people_as_metrics or dossier_pattern:
        protection_priority = 0.15
        sacrifice_exposure = 0.9
        evidence.append("People reduced to ratings/files — dossier pattern detected")
    elif not due_process:
        protection_priority = 0.3
        sacrifice_exposure = 0.7
        evidence.append("Due process not observed in personnel actions")
    elif notice_period < 2:
        protection_priority = 0.4
        sacrifice_exposure = 0.6
        evidence.append(f"Minimal notice period ({notice_period} weeks)")
    else:
        protection_priority = 0.8
        sacrifice_exposure = 0.2
        evidence.append(
            "People treated with dignity — notice, process, support present"
        )

    if support_provided:
        protection_priority += 0.1
    else:
        sacrifice_exposure += 0.1
        evidence.append("No support provided to affected staff")

    protection_priority = max(0.0, min(1.0, protection_priority))
    sacrifice_exposure = max(0.0, min(1.0, sacrifice_exposure))

    warning = None
    if dossier_pattern:
        warning = (
            "DIGNITY_FAILURE: Dossier pattern detected — "
            "personnel system weaponized against individuals"
        )

    return {
        "protection_priority": round(protection_priority, 4),
        "sacrifice_exposure": round(sacrifice_exposure, 4),
        "evidence": evidence,
        "epistemic_tag": "DERIVED",
        "warning": warning,
    }


# ── Classification ─────────────────────────────────────────────────────


def _classify_band(composite: float) -> str:
    if composite >= 0.80:
        return "REGENERATIVE"
    elif composite >= 0.60:
        return "DISCIPLINED"
    elif composite >= 0.40:
        return "DEFENSIVE"
    elif composite >= 0.20:
        return "EXTRACTIVE"
    else:
        return "SELF_CANNIBALISING"


def _extract_signals(
    dims: Dict[str, Any],
) -> List[str]:
    signals = []
    for name, dim in dims.items():
        prot = dim.get("protection_priority", 0.5)
        sac = dim.get("sacrifice_exposure", 0.5)
        if prot < 0.3 and sac > 0.7:
            signals.append(f"{name}: High sacrifice, low protection")
        elif prot > 0.7 and sac < 0.3:
            signals.append(f"{name}: High protection, low sacrifice")
        elif prot < 0.3:
            signals.append(f"{name}: Low protection priority")
        elif sac > 0.7:
            signals.append(f"{name}: High sacrifice exposure")
    return signals


def _generate_alternatives(
    dims: Dict[str, Any],
    band: str,
    data_count: int,
    signals: List[str],
) -> List[Dict[str, str]]:
    alternatives = []

    if band in ("EXTRACTIVE", "SELF_CANNIBALISING"):
        alternatives.append(
            {
                "hypothesis": "Institution's crisis reflex reveals structural priorities under pressure",
                "evidence_for": f"{len(signals)} dimensions showing extractive patterns",
                "evidence_against": "Could be transitional — new leadership may reset reflexes",
            }
        )
        alternatives.append(
            {
                "hypothesis": "Apparent extraction reflects capability constraints, not intent",
                "evidence_for": "Budget limits force difficult trade-offs",
                "evidence_against": "Protective institutions share sacrifice evenly even under constraint",
            }
        )

    if data_count < 4:
        alternatives.append(
            {
                "hypothesis": f"Only {data_count}/8 dimensions active — reading may be partial",
                "evidence_for": "Multiple dimensions missing data",
                "evidence_against": "Active dimensions may capture dominant pattern",
            }
        )

    if not alternatives:
        alternatives.append(
            {
                "hypothesis": "Institution's crisis reflexes are intact",
                "evidence_for": "Protection exceeds sacrifice across measured dimensions",
                "evidence_against": "Healthy reflexes in one domain don't guarantee cross-domain protection",
            }
        )

    return alternatives


def _generate_falsification(band: str, signals: List[str]) -> str:
    signal_count = len(signals)

    if band == "REGENERATIVE":
        return (
            "If within 12 months, protection_priority drops below 0.5 on 3+ dimensions "
            "or sacrifice_exposure rises above 0.5 — the regenerative reading was lagging"
        )
    elif band == "EXTRACTIVE":
        return (
            "If within 12 months, the institution publishes post-crisis review, "
            "reinstates delegated authorities, and shares burden across levels — "
            "the extractive reflex was situational, not structural"
        )
    elif band == "SELF_CANNIBALISING":
        return (
            "If within 6 months, critical knowledge is removed without succession, "
            "recovery investment remains suppressed, and decision quality deteriorates — "
            "self-cannibalisation is confirmed. If investment returns, it was transitional."
        )
    return (
        f"If {signal_count} dimensions improve protection_priority by 0.2+ within "
        f"12 months, the current reading was transitional"
    )
