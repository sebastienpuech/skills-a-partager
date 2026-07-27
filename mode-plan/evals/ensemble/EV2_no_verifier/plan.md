# Plan — skill résumé-réunion (extrait)

## 1. Vision
Un skill qui transforme un transcript de réunion en compte-rendu structuré.

## 3. Composants
- transcriber.py (audio→texte), summarizer.py (texte→CR).

## 6. Signal de succès
- 8 transcripts de référence avec un CR attendu ; on génère le CR pour chacun.

## 9. Garde-fous
- limite de 2000 tokens en entrée.
