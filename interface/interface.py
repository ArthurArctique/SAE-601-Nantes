import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import math
import random
import plotly.graph_objects as go
import duckdb
import os

# ---------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Observatoire Foncier Nantes",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS PERSONNALISÉ DÈS LE CHARGEMENT (Évite le flash sombre/clair)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* Animation d'apparition fluide et élégante (Fade In & Slide Up) */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
/* Appliquer aux conteneurs de colonnes (liste & carte) pour une entrée en douceur */
[data-testid="column"] {
    animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* Override de style pour forcer l'interface principale en blanc et la barre latérale en blanc un peu plus sombre */
.stApp {
    background-color: #ffffff !important;
}
/* Forcer les textes généraux et titres de l'application en noir */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp p, .stApp li, .stApp span:not(.prop-badge) {
    color: #111827 !important;
}
/* Forcer le texte des onglets (tabs) en noir */
button[data-baseweb="tab"] p, button[data-baseweb="tab"] span {
    color: #111827 !important;
}
[data-testid="stSidebar"] {
    background-color: #f1f5f9 !important; /* blanc un peu plus sombre (Slate 100) */
    border-right: 1px solid #cbd5e1;
}
/* Forcer les textes et titres de la barre de filtres en noir */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] h6,
[data-testid="stSidebar"] span {
    color: #000000 !important;
}

/* Style des titres de section (h3) dans la barre de filtres (rectangles arrondis blancs avec ombre) */
[data-testid="stSidebar"] h3 {
    background-color: #ffffff !important;
    color: #1e293b !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06) !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border-left: 4px solid #d4af37 !important; /* Ligne dorée premium sur le côté */
    margin-top: 20px !important;
    margin-bottom: 12px !important;
}

/* Forcer les étiquettes (pills) du multiselect en doré / gold avec texte noir et croix noire */
div[data-baseweb="tag"], span[data-baseweb="tag"] {
    background-color: #d4af37 !important;
    color: #000000 !important;
    border-radius: 4px !important;
}
div[data-baseweb="tag"] *, span[data-baseweb="tag"] * {
    color: #000000 !important;
    fill: #000000 !important;
}

/* Scrollable property list */
.property-list {
    max-height: 750px;
    overflow-y: auto;
    padding-right: 8px;
}
.property-list::-webkit-scrollbar { width: 6px; }
.property-list::-webkit-scrollbar-thumb {
    background: #ccc; border-radius: 3px;
}

/* Property card */
.prop-card {
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    font-family: 'Inter', 'Segoe UI', sans-serif;
    animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.prop-card:hover {
    box-shadow: 0 10px 25px rgba(0,0,0,0.08) !important;
    border-color: #d4af37 !important;
    transform: translateY(-2px) !important; /* Léger soulèvement moderne */
}
.prop-price {
    font-size: 20px;
    font-weight: 800;
    color: #1a1a2e;
    margin: 0;
}
.prop-price-m2 {
    font-size: 13px;
    font-weight: 600;
    color: #888;
    margin: 0 0 6px 0;
}
.prop-type {
    font-size: 14px;
    font-weight: 700;
    color: #333;
    margin: 4px 0 2px 0;
}
.prop-details {
    font-size: 12.5px;
    color: #666;
    margin: 2px 0;
    line-height: 1.5;
}
.prop-date {
    font-size: 11px;
    color: #aaa;
    margin-top: 4px;
}
.prop-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    margin-right: 6px;
}
.badge-maison { background: #e67e22; }
.badge-appart { background: #3498db; }

/* Header bar style */
.seloger-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 2px solid #f0f0f0;
    margin-bottom: 16px;
    background: transparent;
}
.seloger-count {
    font-size: 18px;
    font-weight: 800;
    color: #000000 !important; /* Texte noir! */
}

/* Style des conteneurs de graphiques de synthèse (cards blancs premiums avec ombre) */
.chart-card {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 20px 24px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
    margin-bottom: 24px !important;
    border-left: 5px solid #d4af37 !important; /* Liseré doré de signature */
}
.chart-title {
    font-size: 18px !important;
    font-weight: 800 !important;
    color: #0f172a !important;
    margin: 0 0 6px 0 !important;
    padding: 0 !important;
}
.chart-subtitle {
    font-size: 13px !important;
    color: #64748b !important;
    margin: 0 0 16px 0 !important;
    line-height: 1.4 !important;
}
</style>
""", unsafe_allow_html=True)


# Palette DPE officielle
DPE_COLORS = {
    "A": [39, 174, 96, 220],
    "B": [46, 204, 113, 220],
    "C": [164, 196, 0, 220],
    "D": [241, 196, 15, 220],
    "E": [230, 126, 34, 220],
    "F": [211, 84, 0, 220],
    "G": [192, 57, 43, 220],
}

# Palette de prix par m² : Gris pur (peu cher) → Jaune (modéré) → Rouge (cher)
PRICE_COLORS = [
    [140, 140, 140, 220],   # Gris pur — tiers inférieur (peu cher)
    [230, 190, 10, 220],    # Jaune — tiers moyen (moyennement cher)
    [220, 53, 69, 220],     # Rouge — tiers supérieur (cher)
]

def price_color(prix_m2, seuil_bas, seuil_haut):
    """Retourne la couleur d'un bâtiment selon son prix au m² (terciles)."""
    if pd.isna(prix_m2):
        return [120, 120, 120, 100]
    if prix_m2 < seuil_bas:
        return PRICE_COLORS[0]
    elif prix_m2 < seuil_haut:
        return PRICE_COLORS[1]
    else:
        return PRICE_COLORS[2]


def _make_building_polygon(lon, lat, type_local="Appartement", seed=None):
    """
    Génère un polygone rectangulaire réaliste simulant l'empreinte au sol
    d'un bâtiment à partir d'un point (lon, lat).
    - Maison        : ~10×12 m  (emprise individuelle)
    - Appartement   : ~18×30 m  (emprise de l'immeuble)
    Orientation pseudo-aléatoire basée sur la position pour reproduire
    le tissu urbain.
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random(int(abs(lon * 1e6) + abs(lat * 1e6)))

    if type_local == "Maison":
        w_m = rng.uniform(8, 14)   # largeur en mètres
        h_m = rng.uniform(10, 16)  # profondeur en mètres
    else:  # Appartement / immeuble
        w_m = rng.uniform(14, 25)
        h_m = rng.uniform(20, 40)

    # Conversion mètres -> degrés (approximation à la latitude de Nantes ~47.2°)
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(lat))
    dw = (w_m / 2) / m_per_deg_lon
    dh = (h_m / 2) / m_per_deg_lat

    # Rotation aléatoire du rectangle (0 à 180°)
    angle = rng.uniform(0, math.pi)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    corners = [(-dw, -dh), (dw, -dh), (dw, dh), (-dw, dh)]
    polygon = []
    for cx, cy in corners:
        rx = cx * cos_a - cy * sin_a + lon
        ry = cx * sin_a + cy * cos_a + lat
        polygon.append([rx, ry])
    polygon.append(polygon[0])  # fermer le ring
    return polygon


# ---------------------------------------------------------------------------
# 2. CHARGEMENT DES DONNÉES (DuckDB)
# ---------------------------------------------------------------------------

DB_PATH = "sae601_nantes.duckdb"


@st.cache_data(show_spinner="Chargement des départements disponibles…")
def get_available_depts(_db_mtime):
    """Liste les départements présents dans la base DuckDB."""
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("""
        SELECT DISTINCT SUBSTRING(CAST(code_insee AS VARCHAR), 1, 2) AS dept
        FROM fait_transactions
        ORDER BY dept
    """).df()
    con.close()
    return df["dept"].tolist()


DEPT_NAMES = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron",
    "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal", "16": "Charente",
    "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "2A": "Corse-du-Sud",
    "2B": "Haute-Corse", "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse",
    "24": "Dordogne", "25": "Doubs", "26": "Drôme", "27": "Eure",
    "28": "Eure-et-Loir", "29": "Finistère", "30": "Gard", "31": "Haute-Garonne",
    "32": "Gers", "33": "Gironde", "34": "Hérault", "35": "Ille-et-Vilaine",
    "36": "Indre", "37": "Indre-et-Loire", "38": "Isère", "39": "Jura",
    "40": "Landes", "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire",
    "44": "Loire-Atlantique", "45": "Loiret", "46": "Lot", "47": "Lot-et-Garonne",
    "48": "Lozère", "49": "Maine-et-Loire", "50": "Manche", "51": "Marne",
    "52": "Haute-Marne", "53": "Mayenne", "54": "Meurthe-et-Moselle", "55": "Meuse",
    "56": "Morbihan", "57": "Moselle", "58": "Nièvre", "59": "Nord",
    "60": "Oise", "61": "Orne", "62": "Pas-de-Calais", "63": "Puy-de-Dôme",
    "64": "Pyrénées-Atlantiques", "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales",
    "67": "Bas-Rhin", "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône",
    "71": "Saône-et-Loire", "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie",
    "75": "Paris", "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines",
    "79": "Deux-Sèvres", "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne",
    "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne",
    "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne", "90": "Territoire de Belfort",
    "91": "Essonne", "92": "Hauts-de-Seine", "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne", "95": "Val-d'Oise",
}


@st.cache_data(show_spinner="Connexion à la base DuckDB et chargement des données…")
def load_data(dept_filter, _db_mtime):
    """Charge les données depuis DuckDB, filtrées par département(s)."""
    if not os.path.exists(DB_PATH):
        st.error(f"Base de données introuvable : {DB_PATH}. Veuillez d'abord mettre à jour les départements.")
        st.stop()

    con = duckdb.connect(DB_PATH, read_only=True)

    # Construire le filtre SQL pour les départements sélectionnés
    placeholders = ", ".join([f"'{d}'" for d in dept_filter])
    dept_where = f"SUBSTRING(CAST(code_insee AS VARCHAR), 1, 2) IN ({placeholders})"

    # 1. Transactions DVF
    df_dvf = con.execute(f"""
        SELECT
            prix AS valeur_fonciere,
            type_bien AS type_local,
            surface AS surface_m2,
            pieces AS nb_pieces,
            lat, lon,
            prix_m2,
            dpe_classe, ges_classe,
            date_mutation,
            nom_commune
        FROM fait_transactions
        WHERE lat IS NOT NULL AND lon IS NOT NULL
          AND prix BETWEEN 20000 AND 5000000
          AND surface BETWEEN 10 AND 400
          AND {dept_where}
    """).df()

    # Pré-calculs DVF
    df_dvf["valeur_fmt"] = df_dvf["valeur_fonciere"].apply(
        lambda x: f"{x:,.0f} EUR".replace(",", " ") if pd.notna(x) else "N/A"
    )
    df_dvf["prix_m2_fmt"] = df_dvf["prix_m2"].apply(
        lambda x: f"{x:,.0f} EUR/m2".replace(",", " ") if pd.notna(x) else "N/A"
    )
    df_dvf["price_label"] = df_dvf["valeur_fonciere"].apply(
        lambda x: f"{x/1000:,.0f}k €".replace(",", " ") if pd.notna(x) and x >= 1000 else (
            f"{x:,.0f} €".replace(",", " ") if pd.notna(x) else ""
        )
    )

    prix_m2_valid = df_dvf["prix_m2"].dropna()
    if len(prix_m2_valid) > 0:
        seuil_bas = float(prix_m2_valid.quantile(0.33))
        seuil_haut = float(prix_m2_valid.quantile(0.66))
    else:
        seuil_bas, seuil_haut = 3000.0, 4500.0

    df_dvf["color_prix"] = df_dvf["prix_m2"].apply(
        lambda x: price_color(x, seuil_bas, seuil_haut)
    )
    df_dvf["color_type"] = df_dvf["type_local"].map({
        "Maison": [230, 126, 34, 200],
        "Appartement": [52, 152, 219, 200],
    })

    # Génération des polygones de bâtiments (itertuples ~10x plus rapide qu'iterrows)
    polygons = []
    for row in df_dvf.itertuples():
        polygons.append(_make_building_polygon(
            row.lon, row.lat,
            type_local=getattr(row, "type_local", "Appartement"),
            seed=row.Index,
        ))
    df_dvf["building_polygon"] = polygons

    # 2. DPE (basé sur les transactions ayant un DPE connu)
    df_dpe = df_dvf[df_dvf["dpe_classe"].notna()].copy()
    df_dpe = df_dpe.rename(columns={
        "dpe_classe": "etiquette_dpe",
        "ges_classe": "etiquette_ges",
        "surface_m2": "surface_habitable_logement",
        "type_local": "type_batiment",
    })
    df_dpe["color_dpe"] = df_dpe["etiquette_dpe"].map(DPE_COLORS)
    df_dpe["dpe_score"] = df_dpe["etiquette_dpe"].map(
        {"A": 7, "B": 6, "C": 5, "D": 4, "E": 3, "F": 2, "G": 1}
    )
    df_dpe["conso_5_usages_ep"] = 8 - df_dpe["dpe_score"]
    df_dpe = df_dpe.dropna(subset=["color_dpe"])
    df_dpe["surface_fmt"] = df_dpe["surface_habitable_logement"].apply(
        lambda x: f"{x:.0f} m2" if pd.notna(x) else "N/A"
    )
    df_dpe["conso_fmt"] = "N/A"
    df_dpe["adresse_fmt"] = df_dpe["nom_commune"].fillna("Adresse inconnue")
    # Réutiliser les polygones de dvf au lieu de les recalculer
    # (la colonne building_polygon existe déjà via le .copy())

    # 3. Transports
    df_transport = con.execute(f"""
        SELECT lat, lon, name, railway_type
        FROM dim_transport
        WHERE lat IS NOT NULL AND lon IS NOT NULL
    """).df()

    con.close()
    return df_dpe, df_dvf, df_transport, seuil_bas, seuil_haut


# ── Détection des départements disponibles dans la base ──
if not os.path.exists(DB_PATH):
    st.error("⚠️ Base de données introuvable. Rendez-vous dans 'Mise à jour des départements' pour la créer.")
    st.stop()

db_mtime = os.path.getmtime(DB_PATH)
available_depts = get_available_depts(db_mtime)

# ---------------------------------------------------------------------------
# 3. BARRE LATÉRALE – FILTRES
# ---------------------------------------------------------------------------
st.sidebar.markdown("### ⚙️ Base de Données")
if st.sidebar.button("Mise à jour des départements", width="stretch", type="primary"):
    st.switch_page("pages/selection_departements.py")
st.sidebar.markdown("---")

# ── Filtre Départements ──
st.sidebar.markdown("### 🗺️ Départements")
dept_labels = [f"{d} – {DEPT_NAMES.get(d, d)}" for d in available_depts]
label_to_dept = {f"{d} – {DEPT_NAMES.get(d, d)}": d for d in available_depts}

selected_dept_labels = st.sidebar.multiselect(
    "Départements à afficher",
    options=dept_labels,
    default=dept_labels,  # Tous sélectionnés par défaut
    label_visibility="collapsed",
)
selected_depts = tuple(sorted([label_to_dept[l] for l in selected_dept_labels]))

if not selected_depts:
    st.warning("Veuillez sélectionner au moins un département dans la barre latérale.")
    st.stop()

# ── Chargement des données pour les départements sélectionnés ──
df_dpe, df_dvf, df_transport, seuil_bas, seuil_haut = load_data(selected_depts, db_mtime)

st.sidebar.markdown("---")
st.sidebar.title("Filtres d'Analyse")
st.sidebar.markdown("Affinez votre exploration des données immobilières.")

st.sidebar.markdown("### Performance Energetique (DPE)")
with st.sidebar.expander("Choisir les étiquettes DPE...", expanded=False):
    select_all_dpe = st.checkbox("Tout cocher (DPE)", value=False, key="dpe_all_cb")
    dpe_options = ["A", "B", "C", "D", "E", "F", "G"]
    dpe_choix = []
    for opt in dpe_options:
        default_val = select_all_dpe or (opt in ["A", "B", "C", "D", "E"])
        checked = st.checkbox(f"DPE {opt}", value=default_val, key=f"dpe_opt_{opt}")
        if checked:
            dpe_choix.append(opt)

st.sidebar.markdown("### Surface habitable (m²)")
col_surf1, col_surf2 = st.sidebar.columns(2)
surf_min = col_surf1.number_input("Min :", min_value=10, max_value=400, value=20, step=5)
surf_max = col_surf2.number_input("Max :", min_value=10, max_value=400, value=200, step=5)

st.sidebar.markdown("### Type de batiment")
types_dispo = sorted(df_dpe["type_batiment"].dropna().unique().tolist()) if len(df_dpe) > 0 else ["Appartement", "Maison"]
with st.sidebar.expander("Choisir les types...", expanded=False):
    select_all_types = st.checkbox("Tout cocher (Types)", value=True, key="types_all_cb")
    type_batiment_choix = []
    for opt in types_dispo:
        checked = st.checkbox(opt, value=select_all_types, key=f"type_opt_{opt}")
        if checked:
            type_batiment_choix.append(opt)

st.sidebar.markdown("### Valeur foncière DVF (EUR)")
col_prix1, col_prix2 = st.sidebar.columns(2)
prix_min = col_prix1.number_input("Prix Min :", min_value=10_000, max_value=5_000_000, value=80_000, step=10_000)
prix_max = col_prix2.number_input("Prix Max :", min_value=10_000, max_value=5_000_000, value=800_000, step=10_000)

st.sidebar.markdown("### Densité d'affichage")
max_points = st.sidebar.slider(
    "Nombre max de biens sur la carte :",
    min_value=10,
    max_value=800,
    value=150,
    step=10,
)

st.sidebar.markdown("---")
st.sidebar.subheader("Style de carte")
map_style_name = st.sidebar.selectbox(
    "Fond de carte :",
    options=["Sombre", "Clair", "Coloré"],
    index=2,
)
MAP_STYLES = {
    "Sombre": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    "Clair": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Coloré": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
}
map_style = MAP_STYLES[map_style_name]

choix_transport = st.sidebar.selectbox(
    "Afficher les stations (tram/train) :",
    options=["Non", "Oui"],
    index=0
)
show_transport = (choix_transport == "Oui")

# ---------------------------------------------------------------------------
# 4. FILTRAGE EN DIRECT
# ---------------------------------------------------------------------------
df_dpe_f = df_dpe[
    df_dpe["etiquette_dpe"].isin(dpe_choix)
    & df_dpe["surface_habitable_logement"].between(surf_min, surf_max)
    & df_dpe["type_batiment"].isin(type_batiment_choix)
]

df_dvf_f = df_dvf[
    df_dvf["valeur_fonciere"].between(prix_min, prix_max)
]

# Limitation du nombre de points à afficher
df_dvf_f = df_dvf_f.head(max_points)

# Gestion de la sélection d'un bien via les paramètres de requête
selected_id = st.query_params.get("selected_id")
selected_idx = None
selected_row = None

if selected_id is not None:
    try:
        selected_idx = int(selected_id)
        # S'assurer que le bien sélectionné est dans le dataset filtré
        if selected_idx in df_dvf_f.index:
            selected_row = df_dvf_f.loc[selected_idx]
    except ValueError:
        pass

# ---------------------------------------------------------------------------
# 5. CHARGEMENT ET CALCULS FINIS (Le CSS a été injecté au début pour fluidité)
# ---------------------------------------------------------------------------

nb_dpe = len(df_dpe_f)
nb_dvf = len(df_dvf_f)

# ---------------------------------------------------------------------------
# 6. VUE PRINCIPALE – STYLE SELOGER (Liste + Carte)
# ---------------------------------------------------------------------------

# En-tête style SeLoger
st.markdown(
    f"<div class='seloger-header'>"
    f"<span class='seloger-count'>"
    f"{nb_dvf:,} transactions immobilières – Nantes, disponibles sur la carte"
    f"</span></div>".replace(",", " "),
    unsafe_allow_html=True,
)

# ── Layout principal : Liste à gauche, Carte à droite ──
col_list, col_map = st.columns([2, 3], gap="medium")

# === COLONNE GAUCHE : Liste des biens ===
with col_list:
    # Tri
    tri_option = st.selectbox(
        "Tri par :",
        ["Prix croissant", "Prix décroissant", "Prix/m² croissant",
         "Prix/m² décroissant", "Surface croissante", "Surface décroissante"],
        index=1,
        label_visibility="collapsed",
    )
    tri_map = {
        "Prix croissant": ("valeur_fonciere", True),
        "Prix décroissant": ("valeur_fonciere", False),
        "Prix/m² croissant": ("prix_m2", True),
        "Prix/m² décroissant": ("prix_m2", False),
        "Surface croissante": ("surface_m2", True),
        "Surface décroissante": ("surface_m2", False),
    }
    sort_col, sort_asc = tri_map[tri_option]
    df_sorted = df_dvf_f.sort_values(sort_col, ascending=sort_asc).head(80)

    # Générer les cartes HTML sans retours à la ligne ni indentations pour éviter les blocs de code markdown brut
    cards_html = "<div class='property-list'>"
    for idx, row in df_sorted.iterrows():
        type_local = row.get("type_local", "")
        badge_cls = "badge-maison" if type_local == "Maison" else "badge-appart"

        valeur = row.get("valeur_fonciere", 0)
        prix_m2_val = row.get("prix_m2", 0)
        surface = row.get("surface_m2", 0)
        pieces = row.get("nb_pieces", "")
        date_mut = row.get("date_mutation", "")

        val_str = f"{valeur:,.0f} €".replace(",", " ") if pd.notna(valeur) else "N/A"
        pm2_str = f"{prix_m2_val:,.0f} €/m²".replace(",", " ") if pd.notna(prix_m2_val) else ""
        surf_str = f"{surface:.0f} m²" if pd.notna(surface) else ""
        pcs_str = f"{int(pieces)} pièce{'s' if pieces > 1 else ''}" if pd.notna(pieces) and pieces > 0 else ""

        details_parts = [s for s in [surf_str, pcs_str] if s]
        details_str = " · ".join(details_parts)

        # Style de surbrillance si la carte est cliquée/sélectionnée (doré / gold)
        is_selected = (idx == selected_idx)
        card_style = "border: 2px solid #d4af37; box-shadow: 0 4px 16px rgba(212, 175, 55, 0.35); background: #fdfdfd;" if is_selected else ""

        # Construction sur une seule ligne continue pour immuniser contre le bug du markdown code block
        card_html = (
            f"<a href='?selected_id={idx}' target='_self' style='text-decoration: none; color: inherit;'>"
            f"<div class='prop-card' style='{card_style}'>"
            f"<p class='prop-price'>{val_str}</p>"
            f"<p class='prop-price-m2'>{pm2_str}</p>"
            f"<p class='prop-type'>"
            f"<span class='prop-badge {badge_cls}'>{type_local}</span>"
            f" {type_local} à vendre"
            f"</p>"
            f"<p class='prop-details'>{details_str}</p>"
            f"<p class='prop-date'>Vente du {date_mut}</p>"
            f"</div>"
            f"</a>"
        )
        cards_html += card_html
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

# === COLONNE DROITE : Carte avec marqueurs rouges ===
with col_map:
    # Recentrage dynamique sur le bien sélectionné ou sur le centre des données
    if selected_row is not None:
        VIEW_STATE_SL = pdk.ViewState(
            latitude=selected_row["lat"],
            longitude=selected_row["lon"],
            zoom=15,
            pitch=0,
            bearing=0
        )
    else:
        # Centrage automatique sur les données filtrées
        if len(df_dvf_f) > 0:
            center_lat = df_dvf_f["lat"].mean()
            center_lon = df_dvf_f["lon"].mean()
            # Zoom adapté à l'étendue des données
            lat_range = df_dvf_f["lat"].max() - df_dvf_f["lat"].min()
            if lat_range < 0.05:
                auto_zoom = 14
            elif lat_range < 0.2:
                auto_zoom = 12
            elif lat_range < 1.0:
                auto_zoom = 10
            elif lat_range < 3.0:
                auto_zoom = 8
            else:
                auto_zoom = 6
        else:
            center_lat, center_lon, auto_zoom = 47.2184, -1.5536, 12
        VIEW_STATE_SL = pdk.ViewState(
            latitude=center_lat, longitude=center_lon, zoom=auto_zoom, pitch=0, bearing=0
        )

    # Les labels de prix sont déjà pré-calculés dans load_data()
    df_map = df_dvf_f

    # Halo de surbrillance pour le point sélectionné (gros cercle doré brillant en arrière-plan)
    layer_selected = pdk.Layer(
        "ScatterplotLayer",
        data=pd.DataFrame([selected_row]) if selected_row is not None else pd.DataFrame(),
        get_position="[lon, lat]",
        get_radius=110,
        radius_min_pixels=18,
        radius_max_pixels=35,
        get_fill_color=[212, 175, 55, 145],  # Doré (gold) transparent pour l'effet de halo
        get_line_color=[255, 255, 255, 255],
        line_width_min_pixels=2,
        pickable=False,
    )

    # Marqueurs de couleur selon le prix (cercles)
    layer_markers = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position="[lon, lat]",
        get_radius=40,
        radius_min_pixels=6,
        radius_max_pixels=16,
        get_fill_color="color_prix",
        get_line_color=[255, 255, 255, 225],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
    )

    # Labels de prix au-dessus des marqueurs
    layer_text = pdk.Layer(
        "TextLayer",
        data=df_map,
        get_position="[lon, lat]",
        get_text="price_label",
        get_size=12,
        get_color="color_prix",
        get_angle=0,
        get_text_anchor='"middle"',
        get_alignment_baseline='"bottom"',
        get_pixel_offset="[0, -14]",
        font_family='"Inter", "Segoe UI", sans-serif',
        font_weight=700,
        pickable=False,
    )

    # Couche transport (optionnelle)
    transport_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_transport if show_transport else pd.DataFrame(),
        get_position="[lon, lat]",
        get_radius=80,
        radius_min_pixels=5,
        radius_max_pixels=18,
        get_fill_color=[52, 152, 219, 220],
        get_line_color=[255, 255, 255, 160],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
    )

    tooltip_map = {
        "html": (
            "<div style='font-family:Inter,sans-serif;padding:10px 14px;"
            "background:#fff;border-radius:8px;color:#1a1a2e;"
            "box-shadow:0 4px 20px rgba(0,0,0,.15);max-width:260px;"
            "border:1px solid #e0e0e0;'>"
            "<div style='font-size:18px;font-weight:900;color:#1a1a2e;'>"
            "{valeur_fmt}</div>"
            "<div style='font-size:12px;color:#888;margin-bottom:6px;'>"
            "{prix_m2_fmt}</div>"
            "<hr style='border:0;height:1px;background:#eee;margin:6px 0;'>"
            "<div style='font-size:13px;font-weight:700;'>{type_local}</div>"
            "<div style='font-size:12px;color:#666;'>"
            "{surface_m2} m² · {nb_pieces} pièces</div>"
            "<div style='font-size:11px;color:#aaa;margin-top:4px;'>"
            "Vente du {date_mutation}</div>"
            "</div>"
        ),
        "style": {"backgroundColor": "transparent", "border": "none", "padding": "0"},
    }

    # Légende explicative des prix (texte en noir et police Inter)
    seuil_bas_val = seuil_bas
    seuil_haut_val = seuil_haut
    st.markdown(
        f"""
        <div style='display: flex; gap: 20px; justify-content: center; font-size: 13px; font-weight: 700; margin-bottom: 12px; font-family: "Inter", "Segoe UI", sans-serif; color: #000000;'>
            <div style='display: flex; align-items: center; gap: 6px;'>
                <span style='display: inline-block; width: 12px; height: 12px; background: rgb(140, 140, 140); border-radius: 50%; border: 1px solid rgba(0,0,0,0.15);'></span>
                <span style='color: #000000;'>Peu cher (&lt; {seuil_bas_val:,.0f} €/m²)</span>
            </div>
            <div style='display: flex; align-items: center; gap: 6px;'>
                <span style='display: inline-block; width: 12px; height: 12px; background: rgb(230, 190, 10); border-radius: 50%; border: 1px solid rgba(0,0,0,0.15);'></span>
                <span style='color: #000000;'>Moyen ({seuil_bas_val:,.0f} - {seuil_haut_val:,.0f} €/m²)</span>
            </div>
            <div style='display: flex; align-items: center; gap: 6px;'>
                <span style='display: inline-block; width: 12px; height: 12px; background: rgb(220, 53, 69); border-radius: 50%; border: 1px solid rgba(0,0,0,0.15);'></span>
                <span style='color: #000000;'>Cher (&gt; {seuil_haut_val:,.0f} €/m²)</span>
            </div>
        </div>
        """.replace(",", " "),
        unsafe_allow_html=True
    )

    st.pydeck_chart(
        pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
            initial_view_state=VIEW_STATE_SL,
            layers=[layer_selected, layer_markers, layer_text, transport_layer],
            tooltip=tooltip_map,
        ),
        width="stretch",
    )


# Stats résumé sous la carte
st.markdown("")
c1, c2, c3, c4 = st.columns(4)
surf_med = df_dpe_f["surface_habitable_logement"].median()
prix_med = df_dvf_f["valeur_fonciere"].median()
c1.metric("Transactions DVF", f"{nb_dvf:,}".replace(",", " "))
c2.metric("Prix médian", f"{prix_med:,.0f} €".replace(",", " ") if nb_dvf > 0 else "N/A")
c3.metric("Prix/m² médian", f"{df_dvf_f['prix_m2'].median():,.0f} €/m²".replace(",", " ") if nb_dvf > 0 else "N/A")
c4.metric("Surface médiane", f"{df_dvf_f['surface_m2'].median():.0f} m²" if nb_dvf > 0 else "N/A")

st.divider()

# ---------------------------------------------------------------------------
# 7. ANALYSE DPE (Onglets secondaires)
# ---------------------------------------------------------------------------
st.subheader("Analyse Énergétique (DPE)")

VIEW_STATE_2D = pdk.ViewState(
    latitude=center_lat if len(df_dvf_f) > 0 else 47.2184,
    longitude=center_lon if len(df_dvf_f) > 0 else -1.5536,
    zoom=auto_zoom if len(df_dvf_f) > 0 else 12.5,
    pitch=0, bearing=0
)

# Tooltip DPE
tooltip_dpe = {
    "html": (
        "<div style='font-family:Inter,sans-serif;padding:12px;"
        "background:rgba(15,20,30,0.95);border-radius:10px;"
        "border:1px solid rgba(255,255,255,0.12);color:#fff;"
        "box-shadow:0 4px 24px rgba(0,0,0,.5);max-width:280px;'>"
        "<div style='font-size:10px;text-transform:uppercase;color:#7fa5c8;"
        "margin-bottom:6px;font-weight:700;'>Diagnostic DPE</div>"
        "<div style='font-size:14px;font-weight:800;color:#2ecc71;margin-bottom:6px;'>"
        "{adresse_fmt}</div>"
        "<hr style='border:0;height:1px;background:rgba(255,255,255,.1);margin:6px 0;'>"
        "<table style='font-size:12px;width:100%;'>"
        "<tr><td style='color:#a0aec0;'>Type :</td>"
        "<td style='font-weight:700;text-align:right;'>{type_batiment}</td></tr>"
        "<tr><td style='color:#a0aec0;'>Surface :</td>"
        "<td style='font-weight:700;text-align:right;'>{surface_fmt}</td></tr>"
        "<tr><td style='color:#a0aec0;'>Etiquette DPE :</td>"
        "<td style='font-weight:800;text-align:right;color:#f1c40f;'>{etiquette_dpe}</td></tr>"
        "<tr><td style='color:#a0aec0;'>Conso. 5 usages :</td>"
        "<td style='font-weight:700;text-align:right;color:#e74c3c;'>{conso_fmt}</td></tr>"
        "<tr><td style='color:#a0aec0;'>Periode construction :</td>"
        "<td style='font-weight:600;text-align:right;font-size:11px;'>{periode_construction}</td></tr>"
        "</table></div>"
    ),
    "style": {"backgroundColor": "transparent", "border": "none", "padding": "0"},
}

if nb_dpe > 0:
    tab_dpe_bat, tab_dpe_perf, tab_dpe_heat = st.tabs([
        "DPE par bâtiment",
        "Performance Énergétique",
        "Densité Énergétique",
    ])

    with tab_dpe_bat:
        st.markdown("##### DPE par bâtiment – Couleur = Étiquette énergétique")
        leg_dpe = st.columns(7)
        dpe_labels = ["A", "B", "C", "D", "E", "F", "G"]
        dpe_css = ["#27ae60", "#2ecc71", "#a4c400", "#f1c40f", "#e67e22", "#d35400", "#c0392b"]
        for col_l, label, color in zip(leg_dpe, dpe_labels, dpe_css):
            col_l.markdown(
                f"<span style='display:inline-block;width:14px;height:14px;"
                f"background:{color};border-radius:3px;margin-right:5px;'></span>DPE {label}",
                unsafe_allow_html=True,
            )
        df_hm = df_dpe_f.dropna(subset=["dpe_score"])
        layer_zones_dpe = pdk.Layer(
            "HeatmapLayer", data=df_hm,
            get_position="[lon, lat]", get_weight="dpe_score",
            radiusPixels=80, intensity=1.2, threshold=0.05,
            color_range=[
                [192, 57, 43], [230, 126, 34], [241, 196, 15],
                [164, 196, 0], [39, 174, 96],
            ],
            pickable=False, opacity=0.6,
        )
        layer_dots_dpe = pdk.Layer(
            "ScatterplotLayer", data=df_dpe_f,
            get_position="[lon, lat]", get_radius=8,
            radius_min_pixels=1, radius_max_pixels=12,
            get_fill_color="color_dpe", pickable=True, auto_highlight=True, opacity=1.0,
        )
        st.pydeck_chart(pdk.Deck(
            map_style=map_style, initial_view_state=VIEW_STATE_2D,
            layers=[layer_zones_dpe, layer_dots_dpe], tooltip=tooltip_dpe,
        ))

    with tab_dpe_perf:
        st.markdown("##### Répartition géographique des performances énergétiques")
        if nb_dpe > 0:
            df_hm = df_dpe_f.dropna(subset=["conso_5_usages_ep"])
            layer_conso = pdk.Layer(
                "HeatmapLayer", data=df_hm,
                get_position="[lon, lat]", get_weight="conso_5_usages_ep",
                radiusPixels=80, intensity=1.2, threshold=0.05,
                color_range=[
                    [39, 174, 96], [164, 196, 0], [241, 196, 15],
                    [230, 126, 34], [192, 57, 43],
                ],
                pickable=False, opacity=0.6,
            )
            layer_dots_conso = pdk.Layer(
                "ScatterplotLayer", data=df_dpe_f,
                get_position="[lon, lat]", get_radius=8,
                radius_min_pixels=1, radius_max_pixels=12,
                get_fill_color="color_dpe", pickable=True, auto_highlight=True, opacity=1.0,
            )
            st.pydeck_chart(pdk.Deck(
                map_style=map_style, initial_view_state=VIEW_STATE_2D,
                layers=[layer_conso, layer_dots_conso], tooltip=tooltip_dpe,
            ))

    with tab_dpe_heat:
        st.markdown("##### Carte de chaleur – Consommation energetique (kWh/m²/an)")
        df_heat = df_dpe_f.dropna(subset=["conso_5_usages_ep"])
        if len(df_heat) > 0:
            layer_densite = pdk.Layer(
                "HeatmapLayer", data=df_heat,
                get_position="[lon, lat]", get_weight="conso_5_usages_ep",
                aggregation='"SUM"', radiusPixels=80, intensity=1.2, threshold=0.05,
                color_range=[
                    [39, 174, 96], [164, 196, 0], [241, 196, 15],
                    [230, 126, 34], [192, 57, 43],
                ],
                pickable=False, opacity=0.6,
            )
            layer_dots_d = pdk.Layer(
                "ScatterplotLayer", data=df_heat,
                get_position="[lon, lat]", get_radius=8,
                radius_min_pixels=1, radius_max_pixels=12,
                get_fill_color="color_dpe", pickable=True, auto_highlight=True, opacity=1.0,
            )
            st.pydeck_chart(pdk.Deck(
                map_style=map_style, initial_view_state=VIEW_STATE_2D,
                layers=[layer_densite, layer_dots_d], tooltip=tooltip_dpe,
            ))
        else:
            st.warning("Aucune donnée de consommation pour les filtres actuels.")
else:
    st.info("Aucun logement DPE ne correspond à vos filtres.")

st.divider()

# ---------------------------------------------------------------------------
# 8. TABLEAUX DE DONNÉES
# ---------------------------------------------------------------------------
st.subheader("Données brutes")

tab_t1, tab_t2, tab_t3 = st.tabs(["DPE Nantes", "DVF Nantes (géocodées)", "Stations Transport"])

with tab_t1:
    cols_dpe_show = [
        "adresse_fmt", "etiquette_dpe", "surface_fmt",
        "type_batiment", "conso_fmt",
    ]
    st.dataframe(
        df_dpe_f[cols_dpe_show].rename(columns={
            "adresse_fmt": "Adresse",
            "etiquette_dpe": "DPE",
            "surface_fmt": "Surface",
            "type_batiment": "Type bâtiment",
            "conso_fmt": "Conso. 5 usages",
        }).head(200),
        use_container_width=True,
        hide_index=True,
    )

with tab_t2:
    cols_dvf_show = [
        "valeur_fmt", "type_local", "surface_m2",
        "nb_pieces", "prix_m2_fmt", "date_mutation",
    ]
    st.dataframe(
        df_dvf_f[cols_dvf_show].rename(columns={
            "valeur_fmt": "Valeur foncière",
            "type_local": "Type",
            "surface_m2": "Surface (m²)",
            "nb_pieces": "Pièces",
            "prix_m2_fmt": "Prix/m²",
            "date_mutation": "Date vente",
        }).head(200),
        width="stretch",
        hide_index=True,
    )

with tab_t3:
    st.dataframe(
        df_transport[["name", "railway_type", "lat", "lon"]].rename(columns={
            "name": "Station",
            "railway_type": "Type",
            "lat": "Latitude",
            "lon": "Longitude",
        }),
        width="stretch",
        hide_index=True,
    )

# ---------------------------------------------------------------------------
# 8.5 GRAPHIQUES DE SYNTHÈSE DU MARCHÉ
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("Graphiques de Synthèse du Marché")

# 1. Graphique Prix Immobiliers (Plein écran)
st.markdown(
    """
    <div class='chart-card'>
        <p class='chart-title'>Prix immobiliers</p>
        <p class='chart-subtitle'>Le prix médian des appartements est de 2 608 €/m² en 2025, en hausse de 39% depuis 2014. Le prix médian des maisons est de 2 576 €/m² en 2025, en hausse de 29% depuis 2014. 6 319 ventes ont été enregistrées sur la période.</p>
    </div>
    """,
    unsafe_allow_html=True
)

df_prices = pd.DataFrame({
    "Année": [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
    "Appartement": [1880, 1950, 2150, 1800, 2180, 1980, 2250, 2330, 2450, 2520, 2480, 2608],
    "Maison": [2000, 2050, 2100, 2050, 2000, 2110, 2280, 2560, 2850, 2780, 2650, 2576]
})

fig_prices = go.Figure()
fig_prices.add_trace(go.Scatter(
    x=df_prices["Année"], y=df_prices["Appartement"],
    mode='lines+markers', name='Appartement',
    line=dict(color='#3498db', width=3, shape='spline'),
    marker=dict(size=8, color='#3498db', line=dict(color='#ffffff', width=1.5))
))
fig_prices.add_trace(go.Scatter(
    x=df_prices["Année"], y=df_prices["Maison"],
    mode='lines+markers', name='Maison',
    line=dict(color='#2ecc71', width=3, shape='spline'),
    marker=dict(size=8, color='#2ecc71', line=dict(color='#ffffff', width=1.5))
))
fig_prices.update_layout(
    margin=dict(l=40, r=20, t=10, b=40),
    height=320,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color='#111827')),
    xaxis=dict(
        showgrid=False,
        tickmode='linear',
        tickfont=dict(color='#64748b'),
        linecolor='#cbd5e1'
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor='#e2e8f0',
        ticksuffix=' €/m²',
        tickfont=dict(color='#64748b'),
        linecolor='#cbd5e1'
    )
)
st.plotly_chart(fig_prices, width="stretch")

# 2. Graphiques Âge du parc et Typologie (2 colonnes)
col_g1, col_g2 = st.columns(2, gap="large")

with col_g1:
    st.markdown(
        """
        <div class='chart-card'>
            <p class='chart-title'>Âge du parc immobilier</p>
            <p class='chart-subtitle'>Le parc immobilier est majoritairement construit 1970–1990 (32%). 20% des logements datent d'après 2010.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    periods = ["avant 1945", "1945-1970", "1970-1990", "1990-2010", "après 2010"]
    fig_age = go.Figure()
    fig_age.add_trace(go.Bar(
        x=periods, y=[1, 18, 34, 29, 22],
        name='Maison', marker_color='#2ecc71'
    ))
    fig_age.add_trace(go.Bar(
        x=periods, y=[0.5, 10, 23, 53, 16],
        name='Appartement', marker_color='#3498db'
    ))
    fig_age.update_layout(
        barmode='group',
        margin=dict(l=40, r=20, t=10, b=40),
        height=280,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(color='#111827')),
        xaxis=dict(showgrid=False, tickfont=dict(color='#64748b')),
        yaxis=dict(showgrid=True, gridcolor='#e2e8f0', ticksuffix='%', tickfont=dict(color='#64748b'))
    )
    st.plotly_chart(fig_age, width="stretch")

with col_g2:
    st.markdown(
        """
        <div class='chart-card'>
            <p class='chart-title'>Typologie des appartements</p>
            <p class='chart-subtitle'>Les 2 pièces dominent le marché des appartements (33%), suivis des 3 pièces (33%).</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    typos = ["Studio", "2 pièces", "3 pièces", "4 pièces", "5+ pièces"]
    shares = [22, 33, 33, 10, 2]
    fig_typo = go.Figure()
    fig_typo.add_trace(go.Bar(
        x=typos, y=shares,
        marker_color='#3498db',
        showlegend=False
    ))
    fig_typo.update_layout(
        margin=dict(l=40, r=20, t=10, b=40),
        height=280,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(color='#64748b')),
        yaxis=dict(showgrid=True, gridcolor='#e2e8f0', ticksuffix='%', tickfont=dict(color='#64748b'))
    )
    st.plotly_chart(fig_typo, width="stretch")


# ---------------------------------------------------------------------------
# 9. PIED DE PAGE
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<small>Sources : ADEME (DPE logements existants 44) "
    "| DGFiP (DVF 2025, dept 44) "
    "| Base Adresse Nationale (géocodage) "
    "| OpenStreetMap (stations transport 44) "
    "| Projet SAE-601 – IUT Nantes</small>",
    unsafe_allow_html=True,
)