# archi — webhook-relay
## Composants
- receiver.py, dispatcher.py
## Garde-fous
- signature HMAC vérifiée, rate-limit 100/s, dead-letter queue après 3 échecs (section PROPRE).
