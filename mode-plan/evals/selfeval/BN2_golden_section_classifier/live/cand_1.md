## §10bis. Harnais & signal de succès

**Golden set.** Constituer un jeu figé de 60-100 tickets réels annotés à la main (catégorie attendue), stratifié par catégorie et incluant des cas ambigus et hors-périmètre. Versionné, jamais utilisé pour tuner les prompts (set de test aveugle).

**Signal de succès.** Le skill marche si, sur le golden set : accuracy globale ≥ 85 % ET aucune catégorie majeure < 70 % de rappel (pas de classe sacrifiée). Matrice de confusion inspectée à chaque run pour repérer les paires systématiquement confondues.

**Harnais exécutable.** Un script rejoue le golden set en batch et sort accuracy, précision/rappel/F1 par catégorie, matrice de confusion et la liste nominative des tickets ratés (attendu vs prédit) pour inspection directe.

**Garde-fous.** Catégorie `à_trier` obligatoire quand la confiance est basse plutôt qu'un mauvais classement forcé ; taux de `à_trier` suivi (dérive = signal d'alerte). Non-régression : le golden set repasse au vert avant toute modification de prompt ou de taxonomie.
