# Méthode de Géocodage des Transactions DVF

Ce document explique comment nous sommes passés de **29% à 99,8%** de transactions géocodées (associées à une latitude et longitude) dans notre base de données.

## 1. Le problème initial (29% de succès)

À l'origine, le script essayait de faire correspondre (matcher) l'adresse textuelle de la transaction DVF avec l'adresse textuelle de la Base Adresse Nationale (BAN) par une **égalité stricte** dans Pandas.

**Exemple d'échec :**
* **DVF :** `48 rue gal buat nantes`
* **BAN :** `48 rue general buat nantes`

Parce que le DVF utilise beaucoup d'abréviations (gal, bd, all, imp, etc.), le texte n'était presque jamais identique, ce qui empêchait de récupérer les coordonnées pour 71% des biens vendus.

## 2. La solution : L'API Officielle BAN

Pour résoudre ce problème sans coder un dictionnaire infini d'abréviations, nous avons intégré **l'API officielle de la BAN (adresse.data.gouv.fr)**.

### Comment ça marche ?

1. **Préparation :** On extrait l'adresse normalisée (sans accents, en minuscules) et le code INSEE de chaque transaction.
2. **Batching (Envois groupés) :** L'API limite la taille des requêtes. On groupe donc nos adresses uniques par lots de 5 000.
3. **Appel API :** On envoie le fichier CSV virtuel de 5 000 adresses au point de terminaison de géocodage massif (`https://api-adresse.data.gouv.fr/search/csv/`).
4. **Récupération & Score :** L'API traite chaque ligne. Elle est capable de comprendre que "bd" veut dire "boulevard" et pardonne les légères fautes de frappe. Elle renvoie :
    * La `latitude`
    * La `longitude`
    * Un `result_score` (entre 0 et 1) qui indique la confiance de l'API.
5. **Filtrage :** On ne conserve les coordonnées que si le score de confiance est supérieur à **0.4** (pour éviter les erreurs de placement sur la mauvaise commune).

## 3. Résultats

Cette méthode permet d'obtenir un taux de géocodage exceptionnel de **99,8%**. 

Grâce à ces coordonnées exactes, le script calcule ensuite de manière fiable les distances (via la méthode mathématique `KDTree`) pour savoir si l'appartement/maison vendu est proche d'une école, d'une station de transport, ou situé dans une zone de bruit d'aéroport (PEB).
