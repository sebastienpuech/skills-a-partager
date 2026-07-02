# Plan — skill export-facture (extrait)

## 1. Vision
Un skill qui génère une facture PDF à partir d'une commande.

## 3. Composants
- builder.py (assemble le PDF), sender.py (envoie par mail).

## 7. Validation
- 12 factures de référence (commandes types) rejouées à chaque build ; le PDF produit est comparé octet-à-octet au PDF attendu. Un écart = échec bloquant.

## 9. Garde-fous
- timeout 10s sur la génération.
