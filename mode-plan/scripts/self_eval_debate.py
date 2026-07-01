#!/usr/bin/env python3
"""self_eval_debate.py — le self-golden-set de mode-plan v4.0 (archi §2.3).

Teste enfin les AGENTS LLM de mode-plan (pas seulement les scripts). Rejoue la
Debate Room sur des plans-graines annotés (`evals/selfeval/<case>/`) et vérifie
que les verdicts obtenus correspondent à la vérité-terrain `expected.json`.

Deux modes (contrat archi §2.3 point 2) :
  --replay : lit `recorded/<agent>.json` (déterministe, 0 LLM, CI-ready).
  --live   : lit les sorties fraîches déposées dans `<case>/live/<agent>.json`
             par la Debate Room orchestrée (budget plafonné, run nocturne).

Frontière nette (ARCH-R2-003) :
  - collect_agent_outputs() : SEULE partie qui connaît live vs replay + provenance.
  - grade() : pure, 0 I/O agent, table de dispatch FERMÉE. Réutilisée telle quelle
              par le grader-of-graders (_meta_eval.py) et par best-of-N (V2).

Usage :
  python self_eval_debate.py --replay [--dir evals/selfeval] [--case S1_no_golden_set]
  python self_eval_debate.py --live --sample 3
  python self_eval_debate.py --replay --out evals/selfeval/selfeval_report.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _normalize import norm  # noqa: E402  (source unique de normalisation)

# Racine du skill (parent de scripts/) — sert à résoudre references/adversarial/*.md
SKILL_ROOT = Path(__file__).resolve().parent.parent

# Budget du mode --live (HARN-004) : le run --live complet est réservé au nocturne.
MAX_SPAWNS = 50
TIMEOUT_TOTAL_S = 900          # 15 min
LIVE_SAMPLE_DEFAULT = 3        # sans --full, --live se limite à 3 cas échantillon

# Table de dispatch FERMÉE (data_model §1, patch SIM-002) — toute clé hors table = fail explicite.
_AGENT_RULE_KEYS = (
    frozenset({"contient_gravite", "sur_hook"}),
    frozenset({"contient_gravite"}),
    frozenset({"au_moins_une"}),
    frozenset({"aucun_trouve_sur"}),
)


class StaleFixture(Exception):
    """Le prompt d'agent a changé depuis l'enregistrement du recorded/ (ARCH-R2-002)."""


# --------------------------------------------------------------------------- #
#  Utilitaires
# --------------------------------------------------------------------------- #
def parse_json_tolerant(text: str):
    """Parse un JSON en tolérant les fences markdown et le texte autour."""
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
#  collect_agent_outputs — la SEULE frontière live/replay (ARCH-R2-003)
# --------------------------------------------------------------------------- #
def collect_agent_outputs(case_dir: Path, mode: str, agents: list[str]) -> dict:
    """Retourne {agent -> output_json brut}. Live et replay renvoient le MÊME schéma
    (celui consommé par grade()) — patch SIM-001. Vérifie la provenance en replay."""
    outputs: dict = {}
    for agent in agents:
        if mode == "replay":
            rec = case_dir / "recorded" / f"{agent}.json"
            if not rec.exists():
                raise FileNotFoundError(f"recorded manquant : {rec}")
            data = parse_json_tolerant(rec.read_text(encoding="utf-8"))
            prov = data.get("_provenance")
            if not prov or "agent_file" not in prov:
                raise StaleFixture(f"{rec} : bloc _provenance absent (ARCH-R2-002)")
            agent_file = SKILL_ROOT / prov["agent_file"]
            if not agent_file.exists():
                raise StaleFixture(f"{agent} : fichier d'agent introuvable {prov['agent_file']}")
            actual = sha256_file(agent_file)
            if actual != prov.get("agent_sha256"):
                raise StaleFixture(
                    f"{agent} : {prov['agent_file']} a changé depuis l'enregistrement "
                    f"(sha actuel {actual[:12]}… != enregistré {str(prov.get('agent_sha256'))[:12]}…) "
                    f"— re-enregistrer le recorded/ dans le même commit."
                )
            outputs[agent] = data["output"]
        else:  # live
            live = case_dir / "live" / f"{agent}.json"
            if not live.exists():
                raise FileNotFoundError(
                    f"sortie live manquante : {live} — le mode --live consomme les "
                    f"sorties déposées par la Debate Room orchestrée (skill harness)."
                )
            data = parse_json_tolerant(live.read_text(encoding="utf-8"))
            outputs[agent] = data.get("output", data)  # tolère wrapped ou brut
    return outputs


# --------------------------------------------------------------------------- #
#  Prédicats de la table fermée
# --------------------------------------------------------------------------- #
def _pred_gravite_hook(critic_out: dict, gravite: str, hook) -> bool:
    for c in critic_out.get("critiques", []):
        if c.get("gravite") == gravite and (hook is None or c.get("hook") == hook):
            return True
    return False


def _pred_au_moins_une(juge_out: dict, verdict_value: str) -> bool:
    return any(v.get("verdict") == verdict_value for v in juge_out.get("verdicts", []))


def _pred_aucun_trouve_sur(defenseur_out: dict, critique_id: str) -> bool:
    for d in defenseur_out.get("defenses", []):
        verdict_def = d.get("verdict_defense", d.get("verdict"))
        if d.get("critique_id") == critique_id and verdict_def == "TROUVÉ":
            return False
    return True


def eval_agent_rule(agent: str, rule: dict, outputs: dict):
    """Retourne (ok: bool|None, description). ok=None => erreur de config (clé hors table)."""
    out = outputs.get(agent)
    if out is None:
        return False, f"{agent} : aucune sortie collectée"
    keys = frozenset(rule.keys())
    if keys == frozenset({"contient_gravite", "sur_hook"}):
        ok = _pred_gravite_hook(out, rule["contient_gravite"], rule["sur_hook"])
        return ok, f"{agent} : contient {rule['contient_gravite']} sur {rule['sur_hook']}"
    if keys == frozenset({"contient_gravite"}):
        ok = _pred_gravite_hook(out, rule["contient_gravite"], None)
        return ok, f"{agent} : contient {rule['contient_gravite']}"
    if keys == frozenset({"au_moins_une"}):
        ok = _pred_au_moins_une(out, rule["au_moins_une"])
        return ok, f"{agent} : au_moins_une verdict == {rule['au_moins_une']}"
    if keys == frozenset({"aucun_trouve_sur"}):
        ok = _pred_aucun_trouve_sur(out, rule["aucun_trouve_sur"])
        return ok, f"{agent} : aucun TROUVÉ sur {rule['aucun_trouve_sur']}"
    return None, f"CONFIG_ERROR : clés {sorted(keys)} hors table de dispatch fermée"


def eval_should_not_fire(snf: dict, outputs: dict):
    """should_not_fire PASSE ssi l'agent ne produit AUCUNE critique dont la section
    (après norm) == la section visée — indépendamment de l'ancrage (patch SIM-006)."""
    agent = snf["agent"]
    fichier = snf.get("fichier")
    section = snf["section"]
    out = outputs.get(agent)
    if out is None:
        return False, f"{agent} : aucune sortie collectée"
    target = norm(section)
    for c in out.get("critiques", []):
        same_section = norm(c.get("section", "")) == target
        same_file = fichier is None or c.get("fichier") == fichier
        if same_section and same_file:
            return False, f"{agent} a flaggé {fichier}/{section} (faux positif)"
    return True, f"{agent} ne flag pas {fichier}/{section}"


# --------------------------------------------------------------------------- #
#  grade() — PURE, 0 I/O agent (ARCH-R2-003)
# --------------------------------------------------------------------------- #
def grade(case_id: str, expected: dict, outputs: dict) -> dict:
    regles = []
    config_error = False
    for agent, rule in expected.get("expected_verdicts", {}).items():
        ok, desc = eval_agent_rule(agent, rule, outputs)
        if ok is None:
            config_error = True
            regles.append({"agent": agent, "regle": desc, "ok": False, "config_error": True})
        else:
            regles.append({"agent": agent, "regle": desc, "ok": ok})

    snf_results = []
    for snf in expected.get("should_not_fire", []):
        ok, desc = eval_should_not_fire(snf, outputs)
        snf_results.append({
            "agent": snf["agent"], "fichier": snf.get("fichier"),
            "section": snf["section"], "ok": ok, "fired": not ok, "desc": desc,
        })

    should_fire = bool(expected.get("expected_verdicts"))
    verdicts_ok = all(r["ok"] for r in regles)
    snf_ok = all(r["ok"] for r in snf_results)
    passed = (not config_error) and verdicts_ok and snf_ok

    result = {
        "case_id": case_id,
        "should_fire": should_fire,
        "fired": verdicts_ok if should_fire else False,
        "pass": passed,
        "regles": regles,
        "should_not_fire": snf_results,
    }
    if not passed:
        traces = [r["regle"] for r in regles if not r["ok"]]
        traces += [r["desc"] for r in snf_results if not r["ok"]]
        result["trace"] = "; ".join(traces)
    return result


# --------------------------------------------------------------------------- #
#  Orchestration
# --------------------------------------------------------------------------- #
def discover_cases(root: Path, only: str | None) -> list[Path]:
    """Un dossier contenant expected.json = un cas ; sinon, ses sous-dossiers cas
    (hors ceux préfixés '_' : _meta, _holdout). --case filtre par nom."""
    root = Path(root)
    if (root / "expected.json").exists():
        cases = [root]
    else:
        cases = [
            d for d in sorted(root.iterdir())
            if d.is_dir() and not d.name.startswith("_") and (d / "expected.json").exists()
        ]
    if only:
        cases = [c for c in cases if c.name == only]
    return cases


def run_case(case_dir: Path, mode: str) -> dict:
    expected = parse_json_tolerant((case_dir / "expected.json").read_text(encoding="utf-8"))
    case_id = expected.get("case_id", case_dir.name)

    has_gradable = bool(expected.get("expected_verdicts")) or bool(expected.get("should_not_fire"))
    if expected.get("graded_by") and not has_gradable:
        return {
            "case_id": case_id, "skipped": True,
            "reason": f"graded_by {expected['graded_by']} — hors périmètre self_eval_debate",
        }

    agents = expected.get("agents_requis", [])
    try:
        outputs = collect_agent_outputs(case_dir, mode, agents)
    except StaleFixture as e:
        return {"case_id": case_id, "pass": False, "error": "STALE_FIXTURE", "trace": str(e)}
    except (FileNotFoundError, KeyError) as e:
        return {"case_id": case_id, "pass": False, "error": "MISSING_RECORDED", "trace": str(e)}
    return grade(case_id, expected, outputs)


def build_report(cases: list[Path], mode: str, suite: str, sample: int | None) -> dict:
    graded, skipped = [], []
    processed = cases
    if mode == "live" and sample is not None:
        processed = cases[:sample]  # budget (HARN-004)

    for case_dir in processed:
        r = run_case(case_dir, mode)
        (skipped if r.get("skipped") else graded).append(r)

    total = len(graded)
    passed = sum(1 for r in graded if r.get("pass"))
    failed = total - passed
    score_capability = round(passed / total, 4) if total else 0.0

    report = {
        "mode": mode,
        "suite": suite,
        "total": total,
        "passed": passed,
        "failed": failed,
        "cases": graded,
        "skipped_cases": skipped,
        "score_capability": score_capability,
        "score_regression": 1.0 if suite == "regression" and failed == 0 else None,
    }
    if mode == "live" and sample is not None and len(cases) > sample:
        report["budget"] = {
            "max_spawns": MAX_SPAWNS, "timeout_total_s": TIMEOUT_TOTAL_S,
            "sample": sample, "note": f"{len(cases) - sample} cas non joués (budget) — --full pour tout",
        }
    return report


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="self-golden-set de mode-plan v4.0 (archi §2.3)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--replay", action="store_true", help="rejoue recorded/ (déterministe, défaut)")
    mode.add_argument("--live", action="store_true", help="lit live/ (run orchestré, budget plafonné)")
    ap.add_argument("--dir", default=str(SKILL_ROOT / "evals" / "selfeval"), help="racine des cas")
    ap.add_argument("--case", default=None, help="ne jouer qu'un cas (nom du dossier)")
    ap.add_argument("--suite", default="capability", choices=["capability", "regression"])
    ap.add_argument("--sample", type=int, default=LIVE_SAMPLE_DEFAULT, help="cap de cas en --live")
    ap.add_argument("--full", action="store_true", help="--live sans cap d'échantillon")
    ap.add_argument("--out", default=None, help="chemin du selfeval_report.json (défaut: <dir>/selfeval_report.json)")
    args = ap.parse_args()

    run_mode = "live" if args.live else "replay"
    sample = None if (run_mode == "replay" or args.full) else args.sample

    cases = discover_cases(Path(args.dir), args.case)
    if not cases:
        print(json.dumps({"error": "NO_CASES", "dir": args.dir, "case": args.case}, ensure_ascii=False))
        return 1

    report = build_report(cases, run_mode, args.suite, sample)

    out_path = Path(args.out) if args.out else Path(args.dir) / "selfeval_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(
        f"[self_eval_debate] {run_mode}/{args.suite} : "
        f"{report['passed']}/{report['total']} pass, "
        f"{len(report['skipped_cases'])} skipped, score_capability={report['score_capability']} "
        f"-> {out_path}",
        file=sys.stderr,
    )
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
