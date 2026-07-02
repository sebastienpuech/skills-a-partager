## §10bis. Harnais & signal de succès

Le harnais s'appuie sur un **golden set** de carnets synthétiques (~30 cas) couvrant les doublons attendus : casse/accents, variantes de format (téléphone `+33 6...` vs `06...`), surnoms (« Bob » ↔ « Robert »), homonymes à **ne pas** fusionner, champs partiellement vides. Chaque cas porte un label attendu.

**Signal de succès** : on mesure la **précision** (fusions correctes) et le **rappel** (doublons détectés). Seuil de release : précision ≥ 0,95, rappel ≥ 0,85. Toute fusion irréversible passe par une **confirmation utilisateur** ; le skill n'auto-fusionne jamais en silence.

**Vérification** : rejouer le golden set à chaque modification des règles de matching (`pytest`), avec assertion sur précision/rappel et sur l'**idempotence**. Garde-fou clé : un `--dry-run` listant les fusions envisagées, plus un journal réversible permettant un rollback complet.
