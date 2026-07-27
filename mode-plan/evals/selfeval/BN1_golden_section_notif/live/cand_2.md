## §10bis. Harnais & signal de succès

**Signal de succès** : à chaque build CI qui échoue, une notification part dans les 60 s ; aucun build vert ne déclenche de notification (zéro faux positif). Un accusé d'envoi (statut 2xx du canal de notification) confirme la remise.

**Golden set** : un jeu de ~10 webhooks CI enregistrés (succès, échec, `cancelled`, `timed_out`, re-run, payload malformé) rejoués contre le skill ; on vérifie qu'exactement les statuts d'échec produisent une notification, avec le bon lien vers le run.

**Vérification** : test d'intégration bout-en-bout (webhook simulé → notification capturée sur un canal de test), plus un smoke test manuel déclenchant un vrai échec de build sur une branche jetable.

**Garde-fous** : déduplication (un seul message par run, pas de spam sur re-tries) ; anti-boucle si l'envoi de la notification échoue ; log horodaté de chaque décision (envoyé / ignoré / erreur) pour l'observabilité et le diagnostic des faux négatifs.
