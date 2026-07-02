## §10bis. Harnais & signal de succès

Le harnais repose sur un **golden set** de ~15 paires CSV→JSON de référence, couvrant les cas nominaux et les pièges connus : délimiteurs alternatifs (`;`, tab), guillemets échappés et champs multi-lignes, cellules vides vs. absentes, BOM UTF-8, en-têtes dupliqués, lignes de longueur incohérente, et types ambigus. Chaque entrée associe un CSV source à sa sortie JSON normalisée attendue.

**Signal de succès** : le skill passe si, pour 100 % du golden set, le JSON produit est *strictement égal* à la référence (comparaison structurelle après parsing). Sur un CSV malformé, le skill doit renvoyer une erreur explicite (ligne/colonne fautive) plutôt qu'un JSON silencieusement corrompu.

**Garde-fous** : idempotence (re-normaliser une sortie JSON déjà produite ne la change pas) et préservation — aucune ligne perdue ni inventée. Le harnais tourne en CI sur chaque modification du parser ; toute régression sur une entrée du golden set bloque le merge.
