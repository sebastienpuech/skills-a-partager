#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_convergence.py - Decide whether to continue or break the Phase 3 loop

Reads the verdict history of all rounds executed so far and returns a decision:
  CONTINUE  -> run another round of Debate Room
  CONVERGED -> score reached threshold, deliver
  PLATEAU   -> score barely moved between rounds, deliver
  NO_ISSUES -> 0 confirmed patches, deliver
  MAX_ITERATIONS -> hit round cap, deliver

Usage:
    python3 check_convergence.py <work_dir> [--max-iterations=3] [--threshold=8.0] [--plateau-delta=0.5]

work_dir should contain : verdict_round_1.json, verdict_round_2.json, ...

Output: JSON with decision + reasoning, exit 0 always (decision is in stdout).
"""

from __future__ import annotations
import argparse
import json
import sys
import re
from pathlib import Path


def find_verdict_rounds(work_dir):
    """Find all verdict_round_N.json files, sorted by N."""
    files = list(work_dir.glob("verdict_round_*.json"))
    pairs = []
    for f in files:
        m = re.match(r"verdict_round_(\d+)\.json", f.name)
        if m:
            pairs.append((int(m.group(1)), f))
    pairs.sort()
    return pairs


def load_round(path):
    """Load a verdict_round_N.json, return dict with score + confirmed counts."""
    data = json.loads(path.read_text(encoding="utf-8"))
    stats = data.get("statistiques")
    # Fail-closed (audit 2026-07-03, CODE-005) : bloc statistiques ABSENT (dérive de
    # schéma d'agent) ≠ « 0 confirmée » — sinon NO_ISSUES conclut « deliver » à tort
    # sur un artefact vide. Statut dédié STATS_MISSING, décidé en priorité 0.
    if not isinstance(stats, dict):
        return {"stats_missing": True, "fichier": path.name,
                "global_verdict": data.get("verdict_global", "unknown")}
    clamped = float(stats.get("score_convergence", 0))
    return {
        "score": clamped,
        # v4.1 : score NON borné (formule brute avant clamp [0,10]). Fallback sur le
        # score clampé si absent (verdicts pré-v4.1 -> comportement inchangé).
        "score_raw": float(stats.get("score_convergence_raw", clamped)),
        "confirmed": int(stats.get("confirmees", stats.get("confirmees_count", 0))),
        "rejected": int(stats.get("rejetees", 0)),
        "partial": int(stats.get("partielles", 0)),
        "total": int(stats.get("total", 0)),
        "global_verdict": data.get("verdict_global", "unknown"),
    }


def decide(rounds, max_iterations, threshold, plateau_delta):
    """Return decision dict given history of rounds."""
    if not rounds:
        return {
            "decision": "ERROR",
            "reason": "no verdict_round_*.json found",
        }
    last = rounds[-1]
    n_rounds = len(rounds)

    # Priority 0 : verdict sans bloc statistiques -> jamais un deliver
    if last.get("stats_missing"):
        return {
            "decision": "STATS_MISSING",
            "reason": f"{last.get('fichier', 'verdict')} : bloc 'statistiques' absent — "
                      "dérive de schéma du Juge ; régénérer le verdict avant de conclure.",
            "rounds_run": n_rounds,
        }

    # Priority 1 : converged
    if last["score"] >= threshold and last["confirmed"] == 0:
        return {
            "decision": "CONVERGED",
            "reason": f"score {last['score']:.1f} >= {threshold} with 0 confirmed patches",
            "rounds_run": n_rounds,
            "final_score": last["score"],
        }
    if last["score"] >= threshold:
        return {
            "decision": "CONVERGED",
            "reason": f"score {last['score']:.1f} >= {threshold}",
            "rounds_run": n_rounds,
            "final_score": last["score"],
        }

    # Priority 2 : no issues this round
    if last["confirmed"] == 0 and last["partial"] == 0:
        return {
            "decision": "NO_ISSUES",
            "reason": f"round {n_rounds}: 0 confirmed and 0 partial patches",
            "rounds_run": n_rounds,
            "final_score": last["score"],
        }

    # Priority 3 : max iterations
    if n_rounds >= max_iterations:
        return {
            "decision": "MAX_ITERATIONS",
            "reason": f"reached cap of {max_iterations} rounds",
            "rounds_run": n_rounds,
            "final_score": last["score"],
        }

    # Priority 4 : plateau (need at least 2 rounds)
    # v4.1 : delta calculé sur le score NON borné (score_raw). Sinon deux rounds
    # saturés à 0 (bruts -9 puis -6,1) affichent un delta 0 -> faux PLATEAU par
    # saturation, alors que le plan s'améliore réellement dans le bas de l'échelle.
    if n_rounds >= 2:
        prev = rounds[-2]
        delta = abs(last["score_raw"] - prev["score_raw"])
        if delta < plateau_delta:
            return {
                "decision": "PLATEAU",
                "reason": (
                    f"score (brut) moved by {delta:.2f} between round {n_rounds-1} "
                    f"({prev['score_raw']:.1f}) and round {n_rounds} "
                    f"({last['score_raw']:.1f}), below plateau delta {plateau_delta}"
                ),
                "rounds_run": n_rounds,
                "final_score": last["score"],
                "final_score_raw": last["score_raw"],
            }

    # Otherwise, continue
    return {
        "decision": "CONTINUE",
        "reason": (
            f"round {n_rounds}: score {last['score']:.1f} < {threshold}, "
            f"{last['confirmed']} confirmed patches, "
            f"{n_rounds}/{max_iterations} rounds used"
        ),
        "rounds_run": n_rounds,
        "next_round": n_rounds + 1,
        "current_score": last["score"],
    }


def main():
    ap = argparse.ArgumentParser(description="Decide convergence of Debate Room loop")
    ap.add_argument("work_dir", type=Path)
    ap.add_argument("--max-iterations", type=int, default=3,
                    help="Maximum number of rounds (default: 3)")
    ap.add_argument("--threshold", type=float, default=8.0,
                    help="Score threshold to declare CONVERGED (default: 8.0)")
    ap.add_argument("--plateau-delta", type=float, default=0.5,
                    help="Min score delta to avoid PLATEAU (default: 0.5)")
    args = ap.parse_args()

    if not args.work_dir.is_dir():
        print(json.dumps({"error": "work_dir not a directory"}), file=sys.stderr)
        return 2

    pairs = find_verdict_rounds(args.work_dir)
    rounds = []
    for n, path in pairs:
        try:
            rounds.append(load_round(path))
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            # v4.0 (archi §2.6) : un verdict.json malformé ne doit PAS crasher la
            # boucle — on retourne une décision ERROR explicite (mode safe, sortie
            # de boucle propre côté SKILL, cf. Étape 3.7). Exit 0 : la décision est
            # dans stdout, comme les autres verdicts.
            decision = {
                "decision": "ERROR",
                "reason": f"failed to load {path.name}: {e}",
                "malformed_file": path.name,
            }
            print(json.dumps({"decision": decision, "history": []},
                             indent=2, ensure_ascii=False))
            return 0

    decision = decide(rounds, args.max_iterations, args.threshold, args.plateau_delta)
    history = [{"round": i + 1, **r} for i, r in enumerate(rounds)]
    print(json.dumps({"decision": decision, "history": history},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
