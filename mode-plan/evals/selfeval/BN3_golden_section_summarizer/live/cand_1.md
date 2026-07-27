## §10bis. Harnais & signal de succès

**Golden set** : 12-15 articles de presse variés (dépêche AFP factuelle, tribune d'opinion, long-format enquête, brève sportive, article scientifique vulgarisé) chacun apparié à un résumé de référence rédigé à la main.

**Signal de succès (par résumé produit)** :
- Contient exactement 3 phrases (assertion automatisable : `count == 3`).
- Couvre les faits saillants du référence (qui/quoi/quand) — vérifié par un LLM-juge notant la couverture sur 5, seuil ≥ 4.
- Zéro affirmation absente de l'article (test anti-hallucination : le juge signale toute info non ancrée dans le source).
- Longueur totale ≤ 80 mots, registre neutre (pas d'opinion ajoutée sur une dépêche factuelle).

**Passe/échec global** : le skill est validé si ≥ 90 % du golden set passe les 4 assertions ci-dessus, dont 100 % sur la contrainte « 3 phrases » (non négociable, automatisable sans juge).
