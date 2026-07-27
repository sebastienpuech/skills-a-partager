# §10bis. Harnais & signal de succès

Le skill traduit correctement si, sur un **golden set de 20-30 paires anglais→français** (registres variés), la sortie est jugée fidèle et naturelle. Métrique principale : **taux de traductions acceptables**, cible ≥ 90 %. Chaque paire porte une traduction de référence et 1-2 pièges attendus (faux-ami, idiome, accord/genre) que la sortie doit éviter.

Vérification à deux niveaux : (1) **automatique** — texte de sortie 100 % français (pas de segment anglais résiduel, ratio de mots hors-lexique-FR), longueur plausible, ponctuation française préservée ; (2) **jugement LLM-as-judge** sur fidélité + naturel, note ≥ 4/5.

Signaux d'échec à tracer : anglicismes résiduels, contresens sur faux-amis, sur-traduction, registre décalé. Un échec sur un piège documenté bloque la validation. Le golden set est versionné et rejoué à chaque modification du prompt (non-régression).
