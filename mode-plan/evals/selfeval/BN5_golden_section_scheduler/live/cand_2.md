## §10bis. Harnais & signal de succès

**Signal de succès (mesurable) :** un rappel programmé à T se déclenche à T ± 60 s, une seule fois, avec le texte exact fourni, même si le bot a redémarré entre-temps.

**Golden set :** ~10 cas figés couvrant l'heure absolue, le délai relatif, le récurrent, le fuseau/heure d'été, le passé immédiat et l'ambigu. Chaque cas fige : entrée utilisateur → `run_at` normalisé + texte + récurrence.

**Vérification :**
- *Parsing* : test unitaire entrée langage naturel → `run_at`, avec un `now` gelé (freezegun) pour rendre les délais relatifs déterministes.
- *Déclenchement* : injecter un rappel à `now + 2 s`, avancer l'horloge, asserter qu'une notification et une seule part.
- *Persistance* : créer un rappel, tuer puis relancer le process, vérifier qu'il se déclenche toujours.

**Garde-fous :** idempotence (un rappel honoré est marqué `done`), pas de rafale au redémarrage après veille, confirmation de l'heure interprétée à la création.
