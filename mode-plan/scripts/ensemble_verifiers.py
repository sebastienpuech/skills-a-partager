#!/usr/bin/env python3
"""ensemble_verifiers.py — module frontière+ V2 (item 2) : ensemble de vérifieurs.

Contexte forfait Max (Agent SDK, tarif à plat) : PAS de vérifieur "cheap" — Opus/Haiku/
Sonnet coûtent pareil. La question n'est donc pas l'économie mais l'AUTO-COHÉRENCE :
3 vérifieurs OPUS qui votent à la majorité battent-ils 1 Juge OPUS sur la JUSTESSE ?
Le coût de l'ensemble est en latence/tokens ×3 (pas en $).

Opt-in (`--ensemble=on`, OFF par défaut). Adopté seulement si +0.03 de justesse (gate D1,
objet=ensemble_verifieurs). Mesuré sur des cas de vérification DIFFICILES (evals/ensemble/)
à vérité-terrain annotée — sinon aucune marge (un Juge fort a déjà ~100 % sur des cas faciles).

Writer-unique (archi §4bis) : les 3 vérifieurs LISENT en parallèle ; l'agrégation (vote) et
la décision restent SÉRIALISÉES ici (un seul agent agrège). Pas d'écritures concurrentes.

Règle d'agrégation (déterministe) :
  - majorité (≥ 2 verdicts identiques sur 3) → ce verdict.
  - 3 verdicts distincts (pas de majorité) → **PARTIELLE** (hedge : ni confirmer ni rejeter
    sans accord ; documenté et figé).

Usage :
  python ensemble_verifiers.py --check                    # mécanisme d'agrégation (CI)
  python ensemble_verifiers.py --measure --ensemble=on --mode live   # baseline Opus vs ensemble -> gate
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _normalize import norm          # noqa: E402
from _constants import SEUIL_MIN     # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parent.parent
ENSEMBLE_DIR = SKILL_ROOT / "evals" / "ensemble"
VERDICTS = ("CONFIRMÉE", "REJETÉE", "PARTIELLE")


def norm_verdict(v: str) -> str | None:
    """Ramène un verdict brut (accents/casse/JSON) à la forme canonique."""
    if not v:
        return None
    n = norm(v)
    if "confirm" in n:
        return "CONFIRMÉE"
    if "rejet" in n:
        return "REJETÉE"
    if "partiel" in n:
        return "PARTIELLE"
    return None


def aggregate(verdicts: list[str]) -> str:
    """Vote majoritaire ; 3 distincts -> PARTIELLE (règle figée)."""
    clean = [v for v in verdicts if v]
    if not clean:
        return "PARTIELLE"
    top, n = Counter(clean).most_common(1)[0]
    if n >= 2:
        return top
    return "PARTIELLE"  # aucune majorité (3 distincts) -> hedge


# --------------------------------------------------------------------------- #
#  Chargement
# --------------------------------------------------------------------------- #
def _parse_json_tolerant(text: str):
    import re
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9]*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        i, j = text.find("{"), text.rfind("}")
        if i != -1 and j != -1 and j > i:
            return json.loads(text[i:j + 1])
        raise


def _load_verdict_file(path: Path) -> str | None:
    if not path.exists():
        return None
    data = _parse_json_tolerant(path.read_text(encoding="utf-8"))
    return norm_verdict(data.get("verdict", ""))


def discover_cases(root: Path) -> list[Path]:
    return [d for d in sorted(root.iterdir()) if d.is_dir() and (d / "case.json").exists()]


def run_measure(root: Path, mode: str) -> dict:
    sub = "live" if mode == "live" else "recorded"
    per_case, n_ok_base, n_ok_cand, n = [], 0, 0, 0
    for case_dir in discover_cases(root):
        case = _parse_json_tolerant((case_dir / "case.json").read_text(encoding="utf-8"))
        truth = norm_verdict(case["ground_truth"]["verdict"])
        vdir = case_dir / sub
        opus = _load_verdict_file(vdir / "opus_judge.json")
        members = [_load_verdict_file(vdir / f"ens_{i}.json") for i in (1, 2, 3)]
        if opus is None or any(m is None for m in members):
            per_case.append({"case": case_dir.name, "skipped": True,
                             "raison": f"verdicts manquants en mode {mode}"})
            continue
        ensemble = aggregate(members)
        base_ok = (opus == truth)
        cand_ok = (ensemble == truth)
        n += 1
        n_ok_base += int(base_ok)
        n_ok_cand += int(cand_ok)
        per_case.append({
            "case": case_dir.name, "verite": truth,
            "baseline_opus": opus, "base_ok": base_ok,
            "membres": members, "ensemble": ensemble, "cand_ok": cand_ok,
        })
    if n == 0:
        return {"mode": mode, "error": "aucun cas mesurable", "per_case": per_case}
    baseline = round(n_ok_base / n, 4)
    candidate = round(n_ok_cand / n, 4)
    return {
        "mode": mode, "n_cas": n,
        "baseline_score": baseline, "candidate_score": candidate,
        "gain_oriente": round(candidate - baseline, 4), "per_case": per_case,
    }


def build_gate(live: dict | None, replay: dict | None) -> dict:
    src = "live" if (live and "gain_oriente" in live) else "replay"
    m = live if src == "live" else replay
    gain = m["gain_oriente"]
    # Sous Max, le coût de l'ensemble = latence/tokens ×3. Gain de justesse nul -> décision
    # d'efficience (payer ×3 pour rien), PAS le gate capability.
    if gain >= SEUIL_MIN:
        decision, enabled, note = "activer", True, "l'ensemble Opus (auto-cohérence) est plus juste que 1 Juge Opus"
    elif abs(gain) < 1e-9:
        decision, enabled, note = ("efficience_a_decider", False,
            "justesse ÉGALE : ne PAS auto-adopter ; l'ensemble coûte ×3 en latence/tokens "
            "pour 0 gain de justesse -> décision d'efficience (à trancher par l'humain)")
    else:
        decision, enabled, note = "rejeter", False, "l'ensemble Opus n'est pas plus juste que 1 Juge Opus (et coûte ×3)"
    return {
        "decision_type": "D1_activer_module", "objet": "ensemble_verifieurs",
        "baseline_score": m["baseline_score"], "candidate_score": m["candidate_score"],
        "gain_oriente": gain, "seuil_min": SEUIL_MIN,
        "decision": decision, "ensemble_enabled": enabled, "raison": note,
        "decision_source": src, "mesures": {"live": live, "replay": replay},
        "note_integrite": ("Forfait Max (tarif à plat via Agent SDK) : pas de vérifieur 'cheap' "
                           "-> baseline = 1 Juge Opus, candidate = 3 vérifieurs Opus (vote majoritaire "
                           "= auto-cohérence). Le coût de l'ensemble est en latence/tokens ×3, pas en $. "
                           "Vérité-terrain annotée à la main, lecture seule. Décision sur le LIVE."),
    }


def run_check() -> dict:
    """Mécanisme d'agrégation (CI, déterministe) : le vote majoritaire + la règle
    d'égalité sont-ils corrects ? Cas fixes, aucune dépendance externe."""
    cases = [
        (["CONFIRMÉE", "CONFIRMÉE", "REJETÉE"], "CONFIRMÉE"),
        (["REJETÉE", "REJETÉE", "REJETÉE"], "REJETÉE"),
        (["PARTIELLE", "CONFIRMÉE", "PARTIELLE"], "PARTIELLE"),
        (["CONFIRMÉE", "REJETÉE", "PARTIELLE"], "PARTIELLE"),   # 3 distincts -> hedge
        (["confirmee", "CONFIRMÉE", "rejetée"], "CONFIRMÉE"),   # normalisation
    ]
    results = []
    for verdicts, expected in cases:
        got = aggregate([norm_verdict(v) for v in verdicts])
        results.append({"in": verdicts, "expected": expected, "got": got, "ok": got == expected})
    green = all(r["ok"] for r in results)
    return {"mode": "check", "green": green, "results": results}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="ensemble de vérifieurs cheap (V2, opt-in)")
    ap.add_argument("--ensemble", choices=["on", "off"], default="off")
    ap.add_argument("--check", action="store_true", help="mécanisme d'agrégation (CI)")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--mode", choices=["live", "replay"], default="live")
    ap.add_argument("--dir", default=str(ENSEMBLE_DIR))
    ap.add_argument("--out", default=str(SKILL_ROOT / "_mode-plan-meta" / "adoption_gate_ensemble.json"))
    ap.add_argument("root", nargs="?", default=None)
    args = ap.parse_args()

    if args.check:
        rep = run_check()
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        print(f"[ensemble] check green={rep['green']}", file=sys.stderr)
        return 0 if rep["green"] else 1

    if args.measure:
        if args.ensemble != "on":
            print(json.dumps({"skipped": "ensemble OFF (--ensemble=on pour mesurer)"}, ensure_ascii=False))
            return 0
        root = Path(args.root) if args.root else Path(args.dir)
        live = run_measure(root, "live")
        live = live if "gain_oriente" in live else None
        replay = run_measure(root, "replay")
        replay = replay if "gain_oriente" in replay else None
        if not live and not replay:
            print(json.dumps({"error": "aucune mesure (ni live ni replay)"}, ensure_ascii=False))
            return 1
        gate = build_gate(live, replay)
        Path(args.out).write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(gate, ensure_ascii=False, indent=2))
        print(f"[ensemble] ensemble_enabled={gate['ensemble_enabled']} "
              f"gain={gate['gain_oriente']} decision={gate['decision']} -> {args.out}", file=sys.stderr)
        return 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
