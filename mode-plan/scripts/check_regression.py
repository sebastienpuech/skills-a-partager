#!/usr/bin/env python3
"""
check_regression.py — Anti-régression entre versions de patches

Quand mode-plan applique une nouvelle vague de patches (v1.2, v1.3...),
ce script vérifie qu'aucune nouvelle critique ne contredit ou ne re-flag
un patch déjà appliqué dans une version précédente.

Heuristiques :
- Pour chaque nouveau patch, extraire ses mots-clés (>3 caractères, hors stopwords)
- Comparer avec les sections vN-1 du même fichier
- Si overlap > 50% des mots-clés ET fichier+section identiques → alerte
- Si un patch v1.2 supprime/contredit une décision v1.1 → alerte (heuristique négation)

Usage:
    python3 check_regression.py <project_dir>

Exit codes:
    0 = pas de régression détectée
    1 = régression(s) détectée(s) (détails sur stdout en JSON)
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_FILES = ["spec_produit.md", "archi.md", "data_model.md"]

STOPWORDS_FR = {
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "ou", "à",
    "au", "aux", "ce", "cette", "ces", "que", "qui", "dans", "pour", "par",
    "avec", "sans", "sur", "sous", "est", "sont", "être", "avoir", "fait",
    "faire", "doit", "doivent", "peut", "peuvent", "pas", "plus", "moins",
    "très", "tres", "tout", "tous", "toute", "toutes", "leur", "leurs",
    "son", "sa", "ses", "notre", "votre", "nos", "vos", "il", "elle",
    "ils", "elles", "on", "nous", "vous", "je", "tu", "se", "ne",
}

STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "by", "with",
    "without", "at", "as", "is", "are", "be", "been", "being", "was", "were",
    "this", "that", "these", "those", "it", "its", "which", "who", "whom",
    "from", "into", "than", "then", "but", "not", "no", "any", "all", "each",
    "must", "should", "can", "could", "will", "would", "may", "might", "shall",
    "have", "has", "had", "do", "does", "did", "one", "more", "less", "over",
}

NEGATION_MARKERS = [
    r"\bpas\b", r"\bjamais\b", r"\baucun\b", r"\baucune\b",
    r"\bsans\b", r"\bni\b", r"\bplus\s+de\b",
    # EN (v4.0)
    r"\bnot\b", r"\bnever\b", r"\bno\b", r"\bnone\b", r"\bwithout\b",
]

# Marqueurs de langue : accents/mots FR fréquents vs mots EN fréquents.
_FR_MARKERS = re.compile(r"[àâäéèêëïîôöùûüçœæ]|\b(le|la|les|des|une|est|pour|avec|dans|patch|verdict)\b", re.IGNORECASE)
_EN_MARKERS = re.compile(r"\b(the|and|of|to|with|patch|verdict|section|must|should)\b", re.IGNORECASE)


def detect_language(text: str) -> str:
    """Heuristique légère FR/EN (v4.0, archi §2.6). Défaut FR (langue historique)."""
    fr = len(_FR_MARKERS.findall(text))
    en = len(_EN_MARKERS.findall(text))
    return "en" if en > fr else "fr"


def stopwords_for(lang: str) -> set[str]:
    return STOPWORDS_EN if lang == "en" else STOPWORDS_FR


def parse_patch_sections(content: str) -> list[dict]:
    """Extract patch sections from a file (## Patches stratégiques vX.Y blocks)."""
    sections = []
    # Match "## Patches stratégiques v1.2" headers
    pattern = re.compile(
        r"##\s+Patches stratégiques\s+v(\d+\.\d+)(.*?)(?=##\s+Patches stratégiques\s+v\d+\.\d+|\Z)",
        re.DOTALL,
    )
    for match in pattern.finditer(content):
        version = match.group(1)
        body = match.group(2).strip()
        # Each patch within is a "### Patch [...] — [...]" block
        patch_pattern = re.compile(
            r"###\s+Patch[^\n]*\n(.*?)(?=###\s+Patch|\Z)",
            re.DOTALL,
        )
        patches = []
        for pm in patch_pattern.finditer(body):
            patches.append(pm.group(0).strip())
        sections.append({
            "version": version,
            "patches": patches,
        })
    return sections


def keywords_of(text: str, lang: str | None = None) -> set[str]:
    """Extract meaningful keywords from a text (lowercased, no stopwords).
    v4.0 : stopwords choisis selon la langue détectée (FR/EN)."""
    if lang is None:
        lang = detect_language(text)
    stop = stopwords_for(lang)
    words = re.findall(r"\b[a-zàâäéèêëïîôöùûüçœæ]{4,}\b", text.lower())
    return {w for w in words if w not in stop}


def has_negation(text: str) -> bool:
    """Crude check if text contains negation."""
    lower = text.lower()
    return any(re.search(p, lower) for p in NEGATION_MARKERS)


def check_file(path: Path) -> list[dict]:
    """Check one file for regression patterns. Return list of alerts."""
    if not path.is_file():
        return []
    content = path.read_text(encoding="utf-8")
    sections = parse_patch_sections(content)
    if len(sections) < 2:
        return []  # Need at least 2 versions to compare

    alerts = []
    # Compare last version against all previous
    latest = sections[-1]
    previous = sections[:-1]

    for new_patch in latest["patches"]:
        new_kw = keywords_of(new_patch)
        if len(new_kw) < 3:
            continue
        for prev_section in previous:
            for prev_patch in prev_section["patches"]:
                prev_kw = keywords_of(prev_patch)
                if not prev_kw:
                    continue
                overlap = new_kw & prev_kw
                overlap_ratio = len(overlap) / min(len(new_kw), len(prev_kw))

                if overlap_ratio >= 0.50 and len(overlap) >= 3:
                    # High overlap : same topic touched twice
                    same_polarity = has_negation(new_patch) == has_negation(prev_patch)
                    alert_type = "REPEAT" if same_polarity else "CONTRADICTION"
                    alerts.append({
                        "type": alert_type,
                        "file": path.name,
                        "new_version": latest["version"],
                        "prev_version": prev_section["version"],
                        "overlap_keywords": sorted(overlap)[:8],
                        "overlap_ratio": round(overlap_ratio, 2),
                        "new_patch_snippet": new_patch[:200],
                        "prev_patch_snippet": prev_patch[:200],
                        "message": (
                            f"Patch v{latest['version']} reflagged topic "
                            f"already patched in v{prev_section['version']} "
                            f"({'same polarity' if same_polarity else 'OPPOSITE polarity — possible regression'})"
                        ),
                    })
    return alerts


# Gravité des alertes : une contradiction (polarité opposée = régression probable)
# prime sur un simple re-flag du même sujet.
_SEVERITY_RANK = {"CONTRADICTION": 0, "REPEAT": 1}


def main() -> int:
    ap = argparse.ArgumentParser(description="Anti-regression for mode-plan patches")
    ap.add_argument("project_dir", type=Path)
    ap.add_argument("--max-alerts", type=int, default=20,
                    help="v4.0: cap des alertes retournées, triées par gravité (défaut 20)")
    args = ap.parse_args()

    if not args.project_dir.is_dir():
        print(json.dumps({"error": f"not a directory: {args.project_dir}"}),
              file=sys.stderr)
        return 2

    # Fail-closed (audit 2026-07-03, CODE-003) : un fichier requis ABSENT n'est pas
    # « zéro régression » — statut dédié MISSING_FILES, jamais un PASS silencieux.
    missing = [f for f in REQUIRED_FILES if not (args.project_dir / f).is_file()]
    if missing:
        print(json.dumps({"status": "MISSING_FILES", "project": str(args.project_dir),
                          "missing": missing,
                          "note": "0 fichier analysé ≠ 0 régression — fournir les fichiers "
                                  "requis ou corriger project_dir."},
                         indent=2, ensure_ascii=False))
        return 2

    all_alerts = []
    for fname in REQUIRED_FILES:
        path = args.project_dir / fname
        all_alerts.extend(check_file(path))

    # v4.0 (archi §2.6) : trier par gravité (CONTRADICTION avant REPEAT), puis par
    # overlap décroissant, et capper. On NE PERD PAS silencieusement : le nombre
    # d'alertes tronquées est explicite (H5 : pas de troncature muette).
    total_alerts = len(all_alerts)
    all_alerts.sort(key=lambda a: (_SEVERITY_RANK.get(a["type"], 9), -a.get("overlap_ratio", 0)))
    truncated = max(0, total_alerts - args.max_alerts)
    shown = all_alerts[:args.max_alerts]

    report = {
        "project": str(args.project_dir),
        "files_checked": REQUIRED_FILES,
        "alerts_count": total_alerts,
        "alerts_shown": len(shown),
        "alerts_truncated": truncated,
        "max_alerts": args.max_alerts,
        "alerts": shown,
        "status": "PASS" if not all_alerts else "FAIL",
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not all_alerts else 1


if __name__ == "__main__":
    sys.exit(main())
