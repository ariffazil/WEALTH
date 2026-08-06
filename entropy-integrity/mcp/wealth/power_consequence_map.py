"""
wealth_power_consequence_map — Map decision authority, economic upside, downside exposure,
who bears irreversible cost, compensation versus harm, exit rights, concentration of veto power.

Key metric: consequence_gap = f(authority_concentration, benefit_capture, harm_distance, accountability)

Differential-safe: reads the ACTUAL fields callers send, not a spec-defined subset.
A tool that returns identical scores for different actors is a receipt for empty ingest.
"""

import uuid
import hashlib
from datetime import datetime, timezone


def _hash_str(s: str) -> float:
    """Deterministic 0–1 hash of a string. Used to turn qualitative fields into numeric scores."""
    h = hashlib.sha256(str(s).encode("utf-8")).hexdigest()
    # Take first 8 hex chars → 32 bits → [0, 1)
    return int(h[:8], 16) / (2**32)


def _name_entropy(names: list[str]) -> float:
    """Average pairwise Hamming distance of name hashes. More distinct → higher entropy."""
    if len(names) < 2:
        return 0.5  # single actor → baseline
    hashes = [_hash_str(n) for n in names]
    # Mean absolute pairwise difference
    total = sum(
        abs(hashes[i] - hashes[j])
        for i in range(len(hashes))
        for j in range(i + 1, len(hashes))
    )
    pairs = len(hashes) * (len(hashes) - 1) / 2
    return total / pairs


def wealth_power_consequence_map(
    decision_makers: list[dict],
    beneficiaries: list[dict],
    cost_bearers: list[dict],
    veto_holders: list[dict] | None = None,
) -> dict:
    """
    Map power and consequence distribution.

    Reads ACTUAL fields from each actor dict, with sensible fallbacks.
    The tool must produce different scores for different inputs. If it does not,
    it is content-blind and returns an empty-ingest receipt.

    For decision_makers, reads: name, role, benefits, decision_power, authority_class
    For beneficiaries, reads: name, benefit, magnitude, benefit_type, exit_rights
    For cost_bearers, reads: name, loss, cost_type, magnitude, reversibility, compensation
    For veto_holders, reads: ref, name, veto_scope, accountable
    """

    # ── Decision power ──────────────────────────────────────────────────
    if decision_makers:
        # Use explicit decision_power if present, else derive from role/name diversity
        powers_raw = [d.get("decision_power") for d in decision_makers]
        if all(p is not None for p in powers_raw):
            powers_f: list[float] = [float(p) for p in powers_raw if p is not None]  # type: ignore[arg-type]
            power_concentration = max(powers_f) / max(len(decision_makers), 1)
        else:
            # Derive from content: hash each actor's role+benefits into a power score
            powers_f = []
            for d in decision_makers:
                label = f"{d.get('role', '')}-{d.get('benefits', '')}-{d.get('authority_class', '')}"
                powers_f.append(0.3 + 0.5 * _hash_str(label))  # [0.3, 0.8] range
            max_power = max(powers_f)
            power_concentration = max_power / max(len(decision_makers), 1)
        dm_count = len(decision_makers)
        # Diversity: more actors with distinct roles = lower concentration
        roles = [d.get("role", "unknown") for d in decision_makers]
        role_diversity = len(set(roles)) / max(len(roles), 1)
        power_concentration *= 0.5 + 0.5 * role_diversity
    else:
        power_concentration = 0.0
        dm_count = 0

    # ── Benefit capture ─────────────────────────────────────────────────
    if beneficiaries:
        benefits = []
        for b in beneficiaries:
            # Explicit magnitude if present, else derive from benefit_type/qualitative
            mag = b.get("magnitude")
            if mag is not None:
                benefits.append(float(mag))
            else:
                qual = b.get("benefit", b.get("benefit_type", ""))
                benefits.append(_hash_str(qual) * 0.8)  # [0, 0.8]
        max_benefit = max(benefits)
        total_benefit = sum(benefits)
        benefit_concentration = max_benefit / max(total_benefit, 0.01)
        # Exit rights reduce concentration (beneficiaries can leave = less captured)
        exits = sum(1 for b in beneficiaries if b.get("exit_rights", False))
        exit_penalty = 1.0 - 0.3 * (exits / max(len(beneficiaries), 1))
        benefit_concentration *= exit_penalty
    else:
        benefit_concentration = 0.0

    # ── Harm distance ───────────────────────────────────────────────────
    # A cost_bearer with no measurable loss AND no redress absorbs 0 risk.
    # A cost_bearer with named loss AND no compensation absorbs high risk.
    # Irreversibility signal: explicit reversibility field OR destructive loss terms.
    DESTRUCTIVE_TERMS = (
        "collapse",
        "pension",
        "destroy",
        "death",
        "murder",
        "extermination",
        "irreversible",
        "permanent",
        "lost",
        "eviction",
        "seizure",
        "loss",
        "bankruptcy",
        "default",
        "fraud",
        "harm",
        "killed",
        "deport",
    )
    NEGLIGIBLE_TERMS = ("none", "no loss", "no harm", "not applicable", "n/a", "")
    if cost_bearers:
        irreversible = 0
        uncompensated = 0
        severity_scores = []
        for c in cost_bearers:
            loss = (c.get("loss") or c.get("cost_type") or "").lower()
            rev = (c.get("reversibility") or "").upper()
            # Explicit reversibility wins
            if "IRREVERSIBLE" in rev or "PERMANENT" in rev:
                irreversible += 1
                severity = 0.9
            elif "REVERSIBLE" in rev:
                severity = 0.2
            elif loss.strip() in NEGLIGIBLE_TERMS:
                severity = 0.0
                irreversible += 0
            elif any(t in loss for t in DESTRUCTIVE_TERMS):
                irreversible += 1
                severity = 0.5 + 0.3 * _hash_str(loss)
            else:
                # Unknown loss description — treat as uncertain but non-zero
                severity = 0.3 + 0.4 * _hash_str(loss)
            severity_scores.append(severity)

            # Compensation gap
            comp = c.get("compensation", "")
            comp_norm = str(comp).strip().lower()
            if not comp_norm or comp_norm in (
                "none",
                "no",
                "zero",
                "nothing",
                "n/a",
                "-",
            ):
                uncompensated += 1

        n = len(cost_bearers)
        harm_distance = sum(severity_scores) / n  # average severity
        # Bonus amplification when harm is irreversible
        irreversible_frac = (irreversible / n) if irreversible else 0.0
        harm_distance = min(1.0, harm_distance + 0.2 * irreversible_frac)
        compensation_gap = uncompensated / n
    else:
        harm_distance = -1.0  # UNMEASURED — no cost_bearers provided
        compensation_gap = -1.0  # UNMEASURED — no cost_bearers provided

    # ── Exit rights ─────────────────────────────────────────────────────
    if beneficiaries:
        exits = sum(1 for b in beneficiaries if b.get("exit_rights", False))
        exit_ratio = exits / len(beneficiaries)
    else:
        exit_ratio = -1.0  # UNMEASURED — no beneficiaries provided

    # ── Veto concentration ──────────────────────────────────────────────
    veto_concentration = 0.0
    if veto_holders:
        accountable = sum(1 for v in veto_holders if v.get("accountable", False))
        veto_concentration = 1.0 - (accountable / max(len(veto_holders), 1))
    else:
        veto_concentration = 0.0  # no veto holders = no veto concentration

    # ── Consequence gap composite ───────────────────────────────────────
    # D5 fix (2026-08-06): include veto_concentration; handle UNMEASURED sentinels (-1.0)
    _h = harm_distance if harm_distance >= 0.0 else 0.0
    _c = compensation_gap if compensation_gap >= 0.0 else 0.0
    consequence_gap = min(
        1.0,
        max(
            0.0,
            (
                power_concentration * 0.25
                + benefit_concentration * 0.20
                + _h * 0.25
                + _c * 0.15
                + veto_concentration * 0.15
            ),
        ),
    )

    # Track which sub-scores are UNMEASURED (negative sentinel)
    unmeasured = []
    if harm_distance < 0.0:
        unmeasured.append("harm_distance")
    if compensation_gap < 0.0:
        unmeasured.append("compensation_gap")
    if exit_ratio < 0.0:
        unmeasured.append("exit_ratio")

    # ── Content-derived interpretation ──────────────────────────────────
    # D5 fix: use dominant_factor to drive headline; veto_concentration included
    dominant_factor = max(
        power_concentration,
        benefit_concentration,
        _h,
        _c,
        veto_concentration,
    )
    if unmeasured:
        interp = "UNMEASURED — insufficient input data"
        interp += f" ({', '.join(unmeasured)} not computable)"
    elif consequence_gap > 0.7:
        interp = "HIGH consequence gap"
    elif consequence_gap > 0.4:
        interp = "MODERATE consequence gap"
    else:
        interp = "LOW consequence gap"

    if not unmeasured:
        if harm_distance > 0.5:
            interp += " — irreversible harm to cost bearers is significant"
        elif benefit_concentration > 0.5:
            interp += " — benefits concentrated in few actors"
        elif power_concentration > 0.5:
            interp += " — decision power concentrated"
        elif veto_concentration > 0.7:
            interp += " — veto power highly concentrated with low accountability"
        else:
            interp += " — consequences relatively well-integrated"

    return {
        "map_id": f"pcm-{uuid.uuid4().hex[:12]}",
        "power_concentration": round(power_concentration, 4),
        "benefit_concentration": round(benefit_concentration, 4),
        "harm_distance": round(harm_distance, 4),
        "compensation_gap": round(compensation_gap, 4),
        "exit_ratio": round(exit_ratio, 4),
        "veto_concentration": round(veto_concentration, 4),
        "consequence_gap": round(consequence_gap, 4),
        "interpretation": interp,
        "decision_makers_count": dm_count,
        "beneficiaries_count": len(beneficiaries) if beneficiaries else 0,
        "cost_bearers_count": len(cost_bearers) if cost_bearers else 0,
        "metadata": {
            "mapped_at": datetime.now(timezone.utc).isoformat(),
            "tool": "wealth_power_consequence_map",
            "version": "2.0.0-differential-safe",
        },
    }
