## §10bis. Harnais & signal de succès

Golden set de 15-20 articles couvrant les formats attendus (news, tribune, papier scientifique, article long) avec, pour chacun, un résumé de référence rédigé à la main. Un article se valide sur quatre critères binaires : (1) exactement 3 phrases, (2) aucune information absente de l'article source (zéro hallucination), (3) les 3 points saillants du référentiel sont couverts, (4) le résumé est autoportant (compréhensible sans l'article). Le juge est un LLM distinct du résumeur, avec vérification humaine par échantillon sur les premiers passages pour calibrer le juge.

**Signal de succès** : ≥ 90 % du golden set validé sur les 4 critères, dont 100 % sur le critère anti-hallucination (non négociable — une seule hallucination invalide le run). Suivi en continu : taux de conformité aux 3 phrases, taux d'hallucination, longueur moyenne, latence par article. Régression bloquante si l'un de ces indicateurs se dégrade entre deux versions.
