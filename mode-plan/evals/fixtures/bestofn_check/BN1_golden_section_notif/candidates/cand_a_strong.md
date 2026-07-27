## 10bis. Harnais & signal de succès
Golden set : 5 payloads CI de référence (build pass, build fail, payload malformé, timeout, retry).
Pour chacun une assertion binaire : message produit == message attendu (diff exact, pass/fail).
Vérifieur : une couche `verify_message.py` DISTINCTE du générateur compare la sortie au message attendu ; rejouable à chaque changement (replay déterministe, 0 LLM).
Anti-gaming : les payloads de référence sont non-gamables (le générateur n'a pas accès aux messages attendus).
Exemple : payload {status:"fail", branch:"main"} -> "❌ build cassé sur main".
