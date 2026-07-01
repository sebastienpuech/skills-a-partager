#!/usr/bin/env python3
"""Constantes partagées de mode-plan v4.0 — source unique (SIM-004).

Le seuil d'adoption `+0.03` est défini ICI et nulle part ailleurs. Deux décisions
distinctes le consomment avec la MÊME magnitude (data_model §5, §5bis) :
  - D1_activer_module      : adopter une techno frontière+ (best-of-N, ensemble)
  - D2_garder_agent_herite : garder un agent hérité (passe H8 d'ablation)
Toujours comparé via `gain_oriente >= SEUIL_MIN` (jamais un delta brut signé).
"""

SEUIL_MIN = 0.03
