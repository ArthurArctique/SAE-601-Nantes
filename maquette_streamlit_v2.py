import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from pyproj import Transformer
import math
import random
import plotly.graph_objects as go

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

/* Styling de l'avis de prix tout en haut */
.advisor-box {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04) !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
}
.advisor-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    flex-wrap: wrap !important;
    gap: 10px !important;
}
.advisor-project-title {
    font-size: 13px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    color: #64748b !important;
    margin: 0 !important;
}
.advisor-badge-pill {
    display: inline-block !important;
    padding: 4px 12px !important;
    border-radius: 20px !important;
    font-size: 11.5px !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
.advisor-text-desc {
    font-size: 13.5px !important;
    color: #1e293b !important;
    line-height: 1.5 !important;
    margin: 0 !important;
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


# Convertisseur Lambert93 -> WGS84
_transformer = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)

# ---------------------------------------------------------------------------
# 2. CHARGEMENT DES DONNÉES
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Chargement des données DPE (Nantes)…")
def load_dpe():
    df = pd.read_csv(
        "data/dpe/dpe-logements-existants-44.csv",
        usecols=[
            "etiquette_dpe", "etiquette_ges",
            "surface_habitable_logement",
            "adresse_ban",
            "coordonnee_cartographique_x_ban",
            "coordonnee_cartographique_y_ban",
            "nom_commune_ban", "code_postal_ban",
            "type_batiment", "periode_construction",
            "type_energie_principale_chauffage",
            "conso_5_usages_ep",
        ],
        low_memory=False,
    )
    df = df[df["nom_commune_ban"].str.upper() == "NANTES"].copy()
    df = df.dropna(subset=[
        "coordonnee_cartographique_x_ban",
        "coordonnee_cartographique_y_ban",
        "etiquette_dpe",
    ])
    lons, lats = _transformer.transform(
        df["coordonnee_cartographique_x_ban"].values,
        df["coordonnee_cartographique_y_ban"].values,
    )
    df["lat"] = lats
    df["lon"] = lons
    df = df[df["lat"].between(47.15, 47.32) & df["lon"].between(-1.65, -1.45)]
    df["color_dpe"] = df["etiquette_dpe"].map(DPE_COLORS)
    # Score numérique pour les zones DPE (Hexagones) : A=7, G=1
    df["dpe_score"] = df["etiquette_dpe"].map({"A": 7, "B": 6, "C": 5, "D": 4, "E": 3, "F": 2, "G": 1})
    df = df[df["color_dpe"].notna()]
    df["surface_habitable_logement"] = pd.to_numeric(
        df["surface_habitable_logement"], errors="coerce"
    )
    df["conso_5_usages_ep"] = pd.to_numeric(df["conso_5_usages_ep"], errors="coerce")
    df["surface_fmt"] = df["surface_habitable_logement"].apply(
        lambda x: f"{x:.0f} m2" if pd.notna(x) else "N/A"
    )
    df["conso_fmt"] = df["conso_5_usages_ep"].apply(
        lambda x: f"{x:.0f} kWh/m2/an" if pd.notna(x) else "N/A"
    )
    df["adresse_fmt"] = df["adresse_ban"].fillna("Adresse inconnue")

    # Générer les empreintes de bâtiments (polygones)
    df["building_polygon"] = [
        _make_building_polygon(
            row["lon"], row["lat"],
            type_local=row.get("type_batiment", "Appartement"),
            seed=i + 500_000,
        )
        for i, row in df.iterrows()
    ]
    return df.reset_index(drop=True)


@st.cache_data(show_spinner="Chargement du référentiel d'adresses BAN (Nantes)…")
def load_ban_nantes():
    """Charge les adresses BAN filtrées sur Nantes (code_insee 44109)."""
    df = pd.read_csv(
        "data/ban/adresses-44.csv",
        sep=";",
        usecols=["id_fantoir", "numero", "lon", "lat"],
        low_memory=False,
        dtype={"numero": str, "id_fantoir": str},
    )
    df = df[df["id_fantoir"].str.startswith("44109", na=False)].copy()
    df["code_voie"] = df["id_fantoir"].str.split("_").str[-1]
    df["no_voie"] = df["numero"].str.strip()
    df = df[["code_voie", "no_voie", "lat", "lon"]].drop_duplicates(
        subset=["code_voie", "no_voie"]
    )
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    return df.dropna(subset=["lat", "lon"]).reset_index(drop=True)


@st.cache_data(show_spinner="Chargement et géocodage des transactions DVF 2025…")
def load_dvf_geocoded():
    """
    Charge les ventes DVF Nantes (Maison/Appartement) et les géocode
    via la BAN (jointure sur code FANTOIR + numéro de voie).
    """
    rows = []
    with open(
        "data/dvf/dvf-2025-dept44.csv",
        "r", encoding="utf-8", errors="replace",
    ) as f:
        f.readline()
        for line in f:
            parts = line.rstrip("\n").split(";")
            if len(parts) < 40:
                continue
            
            # Code commune (index 19) doit être 109 pour Nantes
            if parts[19].strip() != "109":
                continue
                
            # Nature mutation (index 9) doit être Vente
            if parts[9].strip() != "Vente":
                continue
                
            # Type local (index 36)
            type_local = parts[36].strip()
            if type_local not in ("Maison", "Appartement"):
                continue

            val_raw = parts[10].strip()
            surf_raw = parts[38].strip()
            pieces_raw = parts[39].strip()
            code_voie = parts[14].strip()
            date_mut = parts[8].strip()

            # Numéro de voie : index 11, puis 12 si vide/nul
            no_voie = parts[11].strip()
            if no_voie in ("00", "", "0") and len(parts) > 12:
                no_voie = parts[12].strip()

            try:
                # Gérer le séparateur décimal français ","
                valeur = float(val_raw.replace(",", "."))
            except ValueError:
                valeur = np.nan
            try:
                # Gérer le séparateur décimal français ","
                surface = float(surf_raw.replace(",", "."))
            except ValueError:
                surface = np.nan
            try:
                pieces = int(float(pieces_raw.replace(",", ".")))
            except (ValueError, TypeError):
                pieces = np.nan

            rows.append({
                "valeur_fonciere": valeur,
                "type_local": type_local,
                "surface_m2": surface,
                "nb_pieces": pieces,
                "code_voie": code_voie,
                "no_voie": no_voie,
                "date_mutation": date_mut,
            })

    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=[
            "valeur_fonciere", "type_local", "surface_m2", "nb_pieces",
            "code_voie", "no_voie", "date_mutation"
        ])
    df["valeur_fonciere"] = pd.to_numeric(df["valeur_fonciere"], errors="coerce")
    df["surface_m2"] = pd.to_numeric(df["surface_m2"], errors="coerce")
    df = df[
        df["valeur_fonciere"].between(20_000, 5_000_000)
        & df["surface_m2"].between(10, 400)
    ].copy()
    df["no_voie"] = df["no_voie"].astype(str).str.strip()

    # Géocodage via BAN
    ban = load_ban_nantes()
    street_centroids = (
        ban.groupby("code_voie")[["lat", "lon"]].median().reset_index()
    )
    street_centroids.columns = ["code_voie", "lat_s", "lon_s"]

    merged = df.merge(ban, on=["code_voie", "no_voie"], how="left")
    merged = merged.merge(street_centroids, on="code_voie", how="left")
    merged["lat"] = merged["lat"].fillna(merged["lat_s"])
    merged["lon"] = merged["lon"].fillna(merged["lon_s"])
    merged = merged.dropna(subset=["lat", "lon"])

    # Filtrage bounding box
    merged = merged[
        merged["lat"].between(47.15, 47.32)
        & merged["lon"].between(-1.65, -1.45)
    ]

    # Pré-calculs
    merged["prix_m2"] = (merged["valeur_fonciere"] / merged["surface_m2"]).round(0)
    merged["valeur_fmt"] = merged["valeur_fonciere"].apply(
        lambda x: f"{x:,.0f} EUR".replace(",", " ") if pd.notna(x) else "N/A"
    )
    merged["prix_m2_fmt"] = merged["prix_m2"].apply(
        lambda x: f"{x:,.0f} EUR/m2".replace(",", " ") if pd.notna(x) else "N/A"
    )
    # Seuils dynamiques : terciles (33% / 66%) pour répartir en 3 groupes égaux
    prix_m2_valid = merged["prix_m2"].dropna()
    seuil_bas = prix_m2_valid.quantile(0.33)
    seuil_haut = prix_m2_valid.quantile(0.66)
    merged["color_prix"] = merged["prix_m2"].apply(
        lambda x: price_color(x, seuil_bas, seuil_haut)
    )
    # Stocker les seuils pour les légendes
    merged.attrs["seuil_bas"] = seuil_bas
    merged.attrs["seuil_haut"] = seuil_haut

    # Couleur par type de bien
    merged["color_type"] = merged["type_local"].map({
        "Maison": [230, 126, 34, 200],
        "Appartement": [52, 152, 219, 200],
    })

    # Générer les empreintes de bâtiments (polygones)
    merged["building_polygon"] = [
        _make_building_polygon(
            row["lon"], row["lat"],
            type_local=row.get("type_local", "Appartement"),
            seed=i,
        )
        for i, row in merged.iterrows()
    ]
    return merged.reset_index(drop=True)


@st.cache_data(show_spinner="Chargement des stations de transport…")
def load_transport():
    df = pd.read_csv(
        "data/transport/stations-44.csv",
        sep=";", encoding="utf-8",
    )
    df = df.dropna(subset=["lat", "lon"])
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df[df["lat"].between(47.15, 47.32) & df["lon"].between(-1.65, -1.45)]
    return df.reset_index(drop=True)


# Chargement
df_dpe = load_dpe()
df_dvf = load_dvf_geocoded()
df_transport = load_transport()

# ---------------------------------------------------------------------------
# 3. BARRE LATÉRALE – FILTRES
# ---------------------------------------------------------------------------
st.sidebar.title("Filtres d'Analyse")
st.sidebar.markdown("Affinez votre exploration de la métropole nantaise.")

st.sidebar.markdown("### Performance Energetique (DPE)")
with st.sidebar.expander("Choisir les étiquettes DPE...", expanded=False):
    select_all_dpe = st.checkbox("Tout cocher (DPE)", value=False, key="dpe_all_cb")
    dpe_options = ["A", "B", "C", "D", "E", "F", "G"]
    dpe_choix = []
    for opt in dpe_options:
        # Par défaut, coche A à E si "Tout cocher" est décoché
        default_val = select_all_dpe or (opt in ["A", "B", "C", "D", "E"])
        checked = st.checkbox(f"DPE {opt}", value=default_val, key=f"dpe_opt_{opt}")
        if checked:
            dpe_choix.append(opt)

st.sidebar.markdown("### Surface habitable (m²)")
col_surf1, col_surf2 = st.sidebar.columns(2)
surf_min = col_surf1.number_input("Min :", min_value=10, max_value=400, value=20, step=5)
surf_max = col_surf2.number_input("Max :", min_value=10, max_value=400, value=200, step=5)

st.sidebar.markdown("### Type de batiment")
types_dispo = sorted(df_dpe["type_batiment"].dropna().unique().tolist())
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
max_points_choice = st.sidebar.select_slider(
    "Nombre max de biens sur la carte :",
    options=[50, 100, 200, 500, 1000, "Max"],
    value=200,
    key="max_points_slider"
)

st.sidebar.markdown("---")
st.sidebar.subheader("Style de carte")
map_style_name = st.sidebar.selectbox(
    "Fond de carte :",
    options=["Sombre", "Clair", "Coloré"],
    index=2,  # Par défaut "Coloré"
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
].copy()

df_dvf_f = df_dvf[
    df_dvf["valeur_fonciere"].between(prix_min, prix_max)
].copy()

# Limitation du nombre de points à afficher
if max_points_choice != "Max":
    df_dvf_f = df_dvf_f.head(max_points_choice)


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

# --- AJOUT DE L'AVIS D'ÉQUITÉ DE PRIX TOUT EN HAUT DE L'UI ---
if selected_row is not None:
    # 1. Calculer la distance géographique avec les autres biens du référentiel
    df_others_all = df_dvf.copy()
    df_others_all["dist_km"] = np.sqrt(
        ((df_others_all["lat"] - selected_row["lat"]) * 111.32) ** 2 +
        ((df_others_all["lon"] - selected_row["lon"]) * 80.0) ** 2
    )
    # Exclure le bien sélectionné lui-même
    df_others_all = df_others_all[df_others_all.index != selected_idx]
    
    if not df_others_all.empty:
        # Prendre les 15 biens les plus proches
        closest_15 = df_others_all.sort_values("dist_km").head(15)
        median_local_prix_m2 = closest_15["prix_m2"].median()
    else:
        median_local_prix_m2 = selected_row["prix_m2"]
        
    prix_m2_bien = selected_row["prix_m2"]
    diff_ratio = (prix_m2_bien - median_local_prix_m2) / median_local_prix_m2
    
    # Choix du verdict, de la couleur et de la description en fonction de l'écart à la médiane locale
    if diff_ratio <= -0.12:
        verdict = "Excellente opportunité"
        badge_color = "#2ecc71"  # Vert émeraude
        border_color = "#2ecc71"
        desc_text = (
            f"Ce bien est proposé à <strong>{prix_m2_bien:,.0f} €/m²</strong>, soit "
            f"<strong>{-diff_ratio*100:.1f}% de moins</strong> que la médiane locale de ses 15 plus proches voisins géographiques "
            f"(<strong>{median_local_prix_m2:,.0f} €/m²</strong>). Au vu de sa localisation et de ses caractéristiques, ce bien représente "
            f"une opportunité particulièrement attractive et sous-évaluée par rapport au micro-marché environnant."
        ).replace(",", " ")
    elif diff_ratio <= 0.05:
        verdict = "Prix cohérent"
        badge_color = "#3498db"  # Bleu
        border_color = "#3498db"
        desc_text = (
            f"Ce bien est proposé à <strong>{prix_m2_bien:,.0f} €/m²</strong>, ce qui est "
            f"<strong>très proche (-/{max(0, diff_ratio*100):.1f}%)</strong> de la médiane locale de ses 15 plus proches voisins géographiques "
            f"(<strong>{median_local_prix_m2:,.0f} €/m²</strong>). Le prix reflète fidèlement la valeur de marché réelle de sa micro-localisation "
            f"et de ses prestations."
        ).replace(",", " ")
    else:
        verdict = "Prix élevé"
        badge_color = "#e74c3c"  # Rouge/Corail
        border_color = "#e74c3c"
        desc_text = (
            f"Ce bien est proposé à <strong>{prix_m2_bien:,.0f} €/m²</strong>, soit "
            f"<strong>{diff_ratio*100:.1f}% de plus</strong> que la médiane locale de ses 15 plus proches voisins géographiques "
            f"(<strong>{median_local_prix_m2:,.0f} €/m²</strong>). À moins que des caractéristiques exceptionnelles du bien "
            f"(rénovation haut de gamme, exposition exceptionnelle, grand jardin) ne le justifient, ce prix se situe au-dessus de la tendance du quartier."
        ).replace(",", " ")

    # Rendu HTML de l'avis de prix
    advisor_html = (
        f"<div class='advisor-box' style='border-left: 5px solid {border_color} !important;'>"
        f"<div class='advisor-header'>"
        f"<span class='advisor-project-title'>💡 Avis d'équité de prix (Est-ce un bon prix ?)</span>"
        f"<span class='advisor-badge-pill' style='background-color: {badge_color} !important;'>{verdict}</span>"
        f"</div>"
        f"<p class='advisor-text-desc'>{desc_text}</p>"
        f"</div>"
    )
    st.markdown(advisor_html, unsafe_allow_html=True)
else:
    # Rendu du message par défaut (Explications du projet de Business Intelligence)
    welcome_text = (
        "Étant donné un prix, une localisation et un ensemble de caractéristiques immobilières, ce bien est-il évalué à son juste prix ? "
        "L'objectif de cette plateforme décisionnelle de Business Intelligence est d'accompagner les acheteurs, vendeurs et professionnels "
        "en croisant de multiples sources de données publiques : historique des transactions (DVF), diagnostics de performance "
        "énergétique (DPE), zones d'exposition au bruit, contexte socio-économique et proximité des réseaux de transports en commun. "
        "<strong>Cliquez sur un bien sur la carte ou dans la liste pour obtenir une analyse d'équité en temps réel.</strong>"
    )
    advisor_html = (
        f"<div class='advisor-box' style='border-left: 5px solid #d4af37 !important;'>"
        f"<div class='advisor-header'>"
        f"<span class='advisor-project-title'>💡 Observatoire Décisionnel Nantes (Business Intelligence)</span>"
        f"<span class='advisor-badge-pill' style='background-color: #d4af37 !important;'>Projet SAE-601</span>"
        f"</div>"
        f"<p class='advisor-text-desc'>{welcome_text}</p>"
        f"</div>"
    )
    st.markdown(advisor_html, unsafe_allow_html=True)

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
    if selected_row is not None:
        # Bouton élégant de retour à la liste complète
        if st.button("⬅ Voir tous les biens", key="btn_reset_selection"):
            st.query_params.clear()
            st.rerun()
            
        st.markdown("#### 📍 Bien sélectionné")
        
        # Générer la carte HTML du bien sélectionné
        type_local = selected_row.get("type_local", "")
        badge_cls = "badge-maison" if type_local == "Maison" else "badge-appart"
        
        valeur = selected_row.get("valeur_fonciere", 0)
        prix_m2_val = selected_row.get("prix_m2", 0)
        surface = selected_row.get("surface_m2", 0)
        pieces = selected_row.get("nb_pieces", "")
        date_mut = selected_row.get("date_mutation", "")
        
        val_str = f"{valeur:,.0f} €".replace(",", " ") if pd.notna(valeur) else "N/A"
        pm2_str = f"{prix_m2_val:,.0f} €/m²".replace(",", " ") if pd.notna(prix_m2_val) else ""
        surf_str = f"{surface:.0f} m²" if pd.notna(surface) else ""
        pcs_str = f"{int(pieces)} pièce{'s' if pieces > 1 else ''}" if pd.notna(pieces) and pieces > 0 else ""
        
        details_parts = [s for s in [surf_str, pcs_str] if s]
        details_str = " · ".join(details_parts)
        
        card_style = "border: 2px solid #d4af37; box-shadow: 0 4px 16px rgba(212, 175, 55, 0.45); background: #fafafa;"
        selected_card_html = (
            f"<div class='prop-card' style='{card_style}'>"
            f"<p class='prop-price'>{val_str}</p>"
            f"<p class='prop-price-m2'>{pm2_str}</p>"
            f"<p class='prop-type'><span class='prop-badge {badge_cls}'>{type_local}</span></p>"
            f"<p class='prop-details'>{details_str}</p>"
            f"<p class='prop-date'>Vente du {date_mut}</p>"
            f"</div>"
        )
        st.markdown(selected_card_html, unsafe_allow_html=True)
        
        # Section des 5 biens similaires recommandés
        st.markdown("#### ✨ 5 Biens les plus similaires (Prix & Lieu)")
        
        # Filtrer le dataset pour exclure le bien sélectionné et calculer les scores
        df_others = df_dvf_f[df_dvf_f.index != selected_idx].copy()
        if not df_others.empty:
            # Distance géographique approximative en kilomètres
            df_others["dist_km"] = np.sqrt(
                ((df_others["lat"] - selected_row["lat"]) * 111.32) ** 2 +
                ((df_others["lon"] - selected_row["lon"]) * 80.0) ** 2
            )
            # Différence relative de prix au m²
            df_others["price_diff_pct"] = (df_others["prix_m2"] - selected_row["prix_m2"]).abs() / max(selected_row["prix_m2"], 1)
            # Score de similarité combiné (50% distance, 50% prix)
            df_others["similarity_score"] = (df_others["dist_km"] / 2.0) + (df_others["price_diff_pct"] * 1.5)
            # Sélectionner les 5 biens les plus similaires
            df_similar = df_others.sort_values("similarity_score").head(5)
        else:
            df_similar = pd.DataFrame()
            
        # Générer les cartes HTML des biens similaires
        cards_html = "<div class='property-list'>"
        for idx, row in df_similar.iterrows():
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
            
            card_html = (
                f"<a href='?selected_id={idx}' target='_self' style='text-decoration: none; color: inherit;'>"
                f"<div class='prop-card' style=''>"
                f"<p class='prop-price'>{val_str}</p>"
                f"<p class='prop-price-m2'>{pm2_str}</p>"
                f"<p class='prop-type'><span class='prop-badge {badge_cls}'>{type_local}</span></p>"
                f"<p class='prop-details'>{details_str}</p>"
                f"<p class='prop-date'>Vente du {date_mut}</p>"
                f"</div>"
                f"</a>"
            )
            cards_html += card_html
        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)
        
    else:
        # Tri de la liste complète des biens
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

        # Générer les cartes HTML de tous les biens sans retours à la ligne ni indentations
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

            card_html = (
                f"<a href='?selected_id={idx}' target='_self' style='text-decoration: none; color: inherit;'>"
                f"<div class='prop-card' style=''>"
                f"<p class='prop-price'>{val_str}</p>"
                f"<p class='prop-price-m2'>{pm2_str}</p>"
                f"<p class='prop-type'><span class='prop-badge {badge_cls}'>{type_local}</span></p>"
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
    # Recentrage dynamique sur le bien sélectionné si disponible
    if selected_row is not None:
        VIEW_STATE_SL = pdk.ViewState(
            latitude=selected_row["lat"],
            longitude=selected_row["lon"],
            zoom=15,
            pitch=0,
            bearing=0
        )
    else:
        VIEW_STATE_SL = pdk.ViewState(
            latitude=47.2184, longitude=-1.5536, zoom=12, pitch=0, bearing=0
        )

    # Préparer les labels de prix pour les marqueurs
    df_map = df_dvf_f.copy()
    df_map["price_label"] = df_map["valeur_fonciere"].apply(
        lambda x: f"{x/1000:,.0f}k €".replace(",", " ") if pd.notna(x) and x >= 1000 else (
            f"{x:,.0f} €".replace(",", " ") if pd.notna(x) else ""
        )
    )

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
    seuil_bas = df_dvf.attrs.get("seuil_bas", 3000)
    seuil_haut = df_dvf.attrs.get("seuil_haut", 4500)
    st.markdown(
        f"""
        <div style='display: flex; gap: 20px; justify-content: center; font-size: 13px; font-weight: 700; margin-bottom: 12px; font-family: "Inter", "Segoe UI", sans-serif; color: #000000;'>
            <div style='display: flex; align-items: center; gap: 6px;'>
                <span style='display: inline-block; width: 12px; height: 12px; background: rgb(140, 140, 140); border-radius: 50%; border: 1px solid rgba(0,0,0,0.15);'></span>
                <span style='color: #000000;'>Peu cher (&lt; {seuil_bas:,.0f} €/m²)</span>
            </div>
            <div style='display: flex; align-items: center; gap: 6px;'>
                <span style='display: inline-block; width: 12px; height: 12px; background: rgb(230, 190, 10); border-radius: 50%; border: 1px solid rgba(0,0,0,0.15);'></span>
                <span style='color: #000000;'>Moyen ({seuil_bas:,.0f} - {seuil_haut:,.0f} €/m²)</span>
            </div>
            <div style='display: flex; align-items: center; gap: 6px;'>
                <span style='display: inline-block; width: 12px; height: 12px; background: rgb(220, 53, 69); border-radius: 50%; border: 1px solid rgba(0,0,0,0.15);'></span>
                <span style='color: #000000;'>Cher (&gt; {seuil_haut:,.0f} €/m²)</span>
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
        use_container_width=True,
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
    latitude=47.2184, longitude=-1.5536, zoom=12.5, pitch=0, bearing=0
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
        df_hm = df_dpe_f.dropna(subset=["dpe_score"]).copy()
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
            df_hm = df_dpe_f.dropna(subset=["conso_5_usages_ep"]).copy()
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
        df_heat = df_dpe_f.dropna(subset=["conso_5_usages_ep"]).copy()
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
        "type_batiment", "periode_construction",
        "type_energie_principale_chauffage", "conso_fmt",
    ]
    st.dataframe(
        df_dpe_f[cols_dpe_show].rename(columns={
            "adresse_fmt": "Adresse",
            "etiquette_dpe": "DPE",
            "surface_fmt": "Surface",
            "type_batiment": "Type bâtiment",
            "periode_construction": "Période",
            "type_energie_principale_chauffage": "Énergie chauffage",
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
        use_container_width=True,
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
        use_container_width=True,
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
st.plotly_chart(fig_prices, use_container_width=True)

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
    st.plotly_chart(fig_age, use_container_width=True)

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
    st.plotly_chart(fig_typo, use_container_width=True)


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