# §10bis. Harnais & signal de succès

Le skill produit un **rapport de fusion déterministe** : liste des paires détectées, action proposée (fusionner / ignorer), champ gagnant par contact fusionné. C'est cet artefact qu'on mesure.

**Golden set** : 30-50 listes de contacts annotées à la main (doublons vrais/faux étiquetés), couvrant les cas durs — variantes de casse et d'accents, formats de téléphone, surnoms, homonymes à ne PAS fusionner, entrées partielles.

**Métriques cibles** : précision ≥ 0.98 sur les fusions (un faux positif détruit des données) et rappel ≥ 0.90 sur la détection. On track précision/rappel/F1 par catégorie de doublon, pour repérer les régressions localisées.

**Garde-fou** : zéro fusion silencieuse — toute fusion est réversible et journalisée ; en dessous du seuil de confiance, le skill propose au lieu de décider. Le harnais échoue le run si une seule fusion touche deux contacts marqués « homonymes distincts » (faux positif = échec bloquant).
