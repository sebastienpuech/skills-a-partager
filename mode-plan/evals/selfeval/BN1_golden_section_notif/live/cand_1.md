## §10bis. Harnais & signal de succès

**Question centrale :** un build CI casse → une notification part-elle, à tous les coups, avec le bon contenu, et sans bruit sur les builds verts ?

- **Golden set d'events CI** : ~8 payloads webhook figés (`fixtures/`) couvrant vert→rouge (doit notifier), rouge→rouge (silence), rouge→vert récupération (notifier « fixé »), payload malformé (ne pas crasher), branche hors-scope (ignorer). Un test rejoue chaque fixture et assert l'action attendue.
- **Signal de succès binaire** : sur le golden set, `notifs_envoyées == notifs_attendues` (aucun faux positif sur build vert, aucun raté sur build cassé). C'est le critère de « ça marche ».
- **Contenu vérifié** : la notif contient repo, branche, n° de build et lien — assert sur ces 4 champs, pas juste sur « une notif est partie ».
- **Anti-bruit** : test de dédoublonnage (2 webhooks pour le même build → 1 seule notif) et de silence sur builds verts.
- **Bout-en-bout réel** : 1 smoke test manuel documenté (casser un build jouet → recevoir la notif sur le vrai canal) avant de déclarer déployable.
- **Observabilité** : log structuré par event (`build_id`, `decision`, `notified`) pour rejouer un raté a posteriori.
