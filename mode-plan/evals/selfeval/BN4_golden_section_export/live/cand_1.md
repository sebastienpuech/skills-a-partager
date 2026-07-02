## §10bis. Harnais & signal de succès

**Golden set** : 8-12 CSV d'entrée figés dans `tests/fixtures/` (avec en-têtes, sans en-têtes, séparateurs `,`/`;`/`\t`, cellules vides, guillemets échappés, accents/UTF-8, doublons de colonnes, gros fichier) + le JSON attendu pour chacun. Un test pytest compare la sortie octet-pour-octet (ou via `json.loads` + égalité de structure).

**Signal de succès (vert = ça marche)** :
- Chaque JSON produit est valide (`json.loads` sans exception) et conforme au schéma cible (clés normalisées, types inférés cohérents).
- Round-trip : re-parser le JSON redonne les mêmes lignes/valeurs que le CSV source (aucune perte, aucun décalage de colonne).
- Cas limites du golden set passent tous (séparateur détecté, UTF-8 préservé, cellules vides → `null` explicite).

**Rouge (échec détectable)** : exception non gérée, décalage de colonnes, encodage cassé (accents en mojibake), ou diff non vide contre un fichier attendu. `pytest tests/ -q` doit sortir 0 ; toute régression casse le CI.
