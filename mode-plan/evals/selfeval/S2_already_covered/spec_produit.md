# spec — widget-notif v2 (skill)
## Vision
Un skill qui envoie une notif quand un build casse.
## Signal de succès
- Golden set: 3 payloads CI (pass / fail / malformé) -> message attendu asserté (assertion binaire).
## Persona
Dev solo, déclenchement auto sur webhook CI.
## Fonctions
1. Parser le payload CI. 2. Formatter un message. 3. Envoyer sur Slack.
