# SAE 2026 — Analyse du marché immobilier français

## Mise en place de l'environnement

1. **Ouvrir un terminal** à la racine du projet et créer l'environnement virtuel :
```bash
python -m venv .venv
```

2. **Activer l'environnement virtuel** :
- Sur **Windows** (PowerShell) :
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- Sur **Windows** (Invite de commandes / CMD) :
  ```cmd
  .venv\Scripts\activate.bat
  ```
- Sur **macOS/Linux** :
  ```bash
  source .venv/bin/activate
  ```

3. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```
*(Utiliser de préférence la version de Python indiquée dans le fichier `.python-version`)*

## Lancer l'application

Une fois l'environnement activé et les dépendances installées, lancez l'application Streamlit avec la commande suivante :
```bash
streamlit run interface/interface.py
```
Cela ouvrira automatiquement l'Observatoire Immobilier dans votre navigateur Web.

##  Objectif
Développer un outil décisionnel permettant de répondre à la question :
**Un bien immobilier est-il au bon prix (prix équitable) ?**

L’analyse portera potentiellement sur :
- la Loire-Atlantique
- et potentiellement l’ensemble de la France

---

##  Idées d’analyse
- Identifier les zones à forte et faible valeur immobilière (ex : Nantes : quartiers riches vs quartiers populaires)
- Zoomer à une échelle locale pour détecter des anomalies de prix
- Comparer un bien avec son environnement (biens similaires)
- Détecter les biens surévalués ou sous-évalués

---


Sources potentielles :
- OpenStreetMap
- Données immobilières (DVF, Immobilier, etc.)

---

##  Indicateurs envisagés


---

##  Base de données
- DOCDB

---

##  Outils décisionnels
- Streamlit (visualisation et interface utilisateur)