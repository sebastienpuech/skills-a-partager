# Archi
foo.

---

## Patches stratégiques v1.1

### Patch MAJEUR — gestion erreur réseau
**Diagnostic** : timeouts réseau non gérés sur appels externes.
**Modification** : ajouter retry exponentiel sur tous les appels HTTP avec cap à 3 tentatives.

---

## Patches stratégiques v1.2

### Patch MAJEUR — gestion erreur réseau
**Diagnostic** : le retry exponentiel introduit trop de latence sur les appels critiques.
**Modification** : supprimer le retry exponentiel, utiliser un circuit-breaker à la place.
