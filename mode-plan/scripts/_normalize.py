#!/usr/bin/env python3
"""Fonction de normalisation canonique de mode-plan v4.0 (archi §2.1, ARCH-003).

UNE SEULE source de normalisation dans tout le repo. Importée par
`align_critiques.py` (dedup de sections), `verify_citations.py` (ancrage des
citations) et `self_eval_debate.py` (comparaison de sections should-not-fire).

Interdit de redéfinir une normalisation ailleurs — le critic-simulateur flague
tout doublon (règle de fer : « une seule fonction de normalisation »).

Spec exacte (archi §2.1, SIM-004), appliquée dans cet ordre :
    1. lower()
    2. NFKD + suppression des diacritiques (é→e, ç→c)
    3. apostrophes typographiques ’ ‘ → ' ; guillemets « » " " → "
    4. collapse tout whitespace (\\s+) en une espace, strip
    5. retire la ponctuation terminale de citation … . , ; :
"""
from __future__ import annotations

import re
import sys
import unicodedata

# Étape 3 — apostrophes et guillemets typographiques → ASCII.
_APOSTROPHES = {
    "’": "'",  # ’ right single quote
    "‘": "'",  # ‘ left single quote
    "ʼ": "'",  # ʼ modifier letter apostrophe
    "´": "'",  # ´ acute accent standalone
    "`": "'",  # ` grave accent standalone
}
_QUOTES = {
    "«": '"',  # « guillemet ouvrant
    "»": '"',  # » guillemet fermant
    "“": '"',  # " left double quote
    "”": '"',  # " right double quote
    "„": '"',  # „ low double quote
    "‟": '"',  # ‟ high reversed double quote
}
_TYPO = {**_APOSTROPHES, **_QUOTES}

# Étape 5 — ponctuation terminale de citation (+ whitespace) retirée en fin.
# Après NFKD, l'ellipse … (U+2026) est décomposée en trois points, couverte par '.'.
_TRAILING = " \t\r\n….,;:"

_WS_RE = re.compile(r"\s+")


def norm(s: str) -> str:
    """Normalise une chaîne pour comparaison robuste (voir spec module)."""
    if s is None:
        return ""
    # 1. lower
    s = s.lower()
    # 2. NFKD + suppression des diacritiques (marques combinantes)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # 3. apostrophes / guillemets typographiques → ASCII
    for k, v in _TYPO.items():
        s = s.replace(k, v)
    # 4. collapse whitespace
    s = _WS_RE.sub(" ", s).strip()
    # 5. retire la ponctuation terminale de citation
    s = s.rstrip(_TRAILING)
    return s


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("usage: _normalize.py [texte...]  — imprime norm() de chaque argument")
        sys.exit(0)
    for arg in sys.argv[1:]:
        print(repr(norm(arg)))
