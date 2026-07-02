## §10bis. Harnais & signal de succès

**Signal de succès (métrique nord).** Le skill marche si, sur les 20 derniers builds cassés, ≥ 95 % ont déclenché une notification en < 60 s après l'échec CI, et 0 notification n'a été émise sur un build vert (zéro faux positif toléré, car un faux positif tue la confiance dans l'alerte).

**Golden set.** 15–20 cas figés rejoués à chaque modif : builds rouges francs (tests KO, compile KO), builds verts, cas-limites (build annulé, timeout, flaky re-run passé au 2ᵉ essai, run encore *in progress*). Attendu annoté par cas : notifier / ne pas notifier / attendre. Le golden set vit dans le repo du skill et sert de non-régression.

**Vérification.** Chaque cas rejoué compare la décision du skill (notifie / silence) à l'attendu ; on mesure précision (pas de fausse alerte) et rappel (pas d'échec manqué), plus la latence détection→notif. Un run est un échec de suite si un seul faux positif apparaît.

**Garde-fous.** Dédup (une seule notif par build_id, pas de spam sur re-runs), anti-flaky (attendre le statut final, pas les états transitoires), et fallback silencieux si l'API CI est injoignable (on log, on ne notifie pas à tort).

**Observabilité.** Journaliser chaque décision (build_id, statut CI, notifié o/n, latence) pour rejouer les ratés et enrichir le golden set quand un vrai cas passe entre les mailles.
