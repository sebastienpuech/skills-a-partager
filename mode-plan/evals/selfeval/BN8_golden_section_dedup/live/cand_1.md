## §10bis. Harnais & signal de succès

**Golden set** : ~15 listes de contacts annotées à la main (paires vrai-doublon / faux-doublon connues), incluant les cas durs : homonymes distincts, même personne sous variantes (surnom, nom marital, e-mail pro vs perso, tel avec/sans +33), accents et casse. Chaque cas porte le verdict attendu (fusionner / garder séparés).

**Métriques** : précision et rappel sur les paires. Le seuil bloquant est la **précision** (une fusion erronée détruit des données) — viser précision ≥ 0,99, rappel ≥ 0,90. Toute fusion à faible confiance est signalée pour revue, jamais appliquée en silence.

**Vérification** : `pytest` rejoue le golden set et échoue si un faux-positif apparaît ou si le rappel régresse. Test d'idempotence : relancer le dédup sur une sortie déjà nettoyée ne fusionne plus rien.

**Garde-fou** : sortie réversible (log des fusions) permettant d'annuler ; zéro perte de champ à la fusion.
