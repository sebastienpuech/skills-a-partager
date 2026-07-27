# Data Model — [Nom du projet]

> Entités, contrats, schéma. À lire en parallèle de `archi.md`.
> Pour un skill multi-agent, ce fichier peut contenir le golden set des cas d'usage à la place du schéma DB.

---

## 1. Entités principales

### Entité [Nom1]
**Rôle** : ...
**Source de vérité** : [DB / fichier / API externe]

| Champ | Type | Obligatoire | Notes |
|-------|------|-------------|-------|
| id | uuid | oui | clé primaire |
| ... | ... | ... | ... |

**Relations** :
- 1-N vers [Entité2]
- N-1 vers [Entité3]

**Cycle de vie** : [comment elle est créée / mise à jour / supprimée]

### Entité [Nom2]
[Idem.]

## 2. Schéma de base de données (si applicable)

```sql
-- Ou pointer vers une migration alembic / prisma / autre
CREATE TABLE ...
```

## 3. Contrats d'API (si applicable)

### Endpoint [POST /api/resource]
**Input** :
```json
{ "field": "type" }
```
**Output succès** :
```json
{ "field": "type" }
```
**Erreurs possibles** : ...

## 4. Contrats inter-agents (si applicable)

### Message [Type1]
```json
{
  "from": "agent_name",
  "to": "agent_name",
  "payload": { ... }
}
```

## 5. Données externes consommées

### Source [Nom de l'API ou MCP]
- Endpoints utilisés : ...
- Auth : ...
- Rate limits : ...
- Données mises en cache localement : ...

## 6. Migrations / évolutions du schéma

- Outil utilisé : [alembic / prisma / autre]
- Convention de naming : ...
- Réversibilité requise : oui/non

## 7. Volumes attendus

- [Entité 1] : ~N records à terme
- [Entité 2] : ~N records / jour
- Impact sur le choix DB / hosting : ...

## 8. Sensibilité données

- PII présentes : oui/non
- Encryption at rest : oui/non
- Backup strategy : ...

---

*Dernière màj : [date].*
