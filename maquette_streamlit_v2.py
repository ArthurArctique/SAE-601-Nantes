import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import json
import math
import random
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Observatoire Foncier Nantes",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# THÈME CLAIR / SOMBRE (toggle dans la sidebar)
# ---------------------------------------------------------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
is_dark = st.session_state.dark_mode

# Palettes dynamiques
if is_dark:
    _BG_MAIN = "#0f172a"
    _BG_SIDEBAR = "#1e293b"
    _BG_CARD = "#1e293b"
    _BORDER_CARD = "#334155"
    _TEXT_PRIMARY = "#f1f5f9"
    _TEXT_SECONDARY = "#94a3b8"
    _TEXT_MUTED = "#64748b"
    _SHADOW_CARD = "rgba(0,0,0,0.30)"
    _BORDER_SIDEBAR = "#334155"
    _SCROLLBAR = "#475569"
    _HOVER_SHADOW = "rgba(212,175,55,0.25)"
    _CHART_GRID = "#334155"
    _CHART_TEXT = "#94a3b8"
    _CHART_LINE = "#475569"
    _HEADER_BORDER = "#334155"
    _SIDEBAR_H3_BG = "#0f172a"
    _SIDEBAR_H3_TEXT = "#f1f5f9"
    _SIDEBAR_TEXT = "#e2e8f0"
else:
    _BG_MAIN = "#ffffff"
    _BG_SIDEBAR = "#f1f5f9"
    _BG_CARD = "#ffffff"
    _BORDER_CARD = "#e8e8e8"
    _TEXT_PRIMARY = "#111827"
    _TEXT_SECONDARY = "#666666"
    _TEXT_MUTED = "#aaaaaa"
    _SHADOW_CARD = "rgba(0,0,0,0.05)"
    _BORDER_SIDEBAR = "#cbd5e1"
    _SCROLLBAR = "#cccccc"
    _HOVER_SHADOW = "rgba(0,0,0,0.08)"
    _CHART_GRID = "#e2e8f0"
    _CHART_TEXT = "#64748b"
    _CHART_LINE = "#cbd5e1"
    _HEADER_BORDER = "#f0f0f0"
    _SIDEBAR_H3_BG = "#ffffff"
    _SIDEBAR_H3_TEXT = "#1e293b"
    _SIDEBAR_TEXT = "#000000"

# ---------------------------------------------------------------------------
# CSS PERSONNALISÉ DÈS LE CHARGEMENT
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
/* Animation d'apparition fluide et élégante (Fade In & Slide Up) */
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
[data-testid="column"] {{
    animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}}

/* Fond principal */
.stApp {{
    background-color: {_BG_MAIN} !important;
    transition: background-color 0.3s ease;
}}
/* Textes généraux */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp p, .stApp li, .stApp span:not(.prop-badge) {{
    color: {_TEXT_PRIMARY} !important;
}}
button[data-baseweb="tab"] p, button[data-baseweb="tab"] span {{
    color: {_TEXT_PRIMARY} !important;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: {_BG_SIDEBAR} !important;
    border-right: 1px solid {_BORDER_SIDEBAR};
    transition: background-color 0.3s ease;
}}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,
[data-testid="stSidebar"] h6,
[data-testid="stSidebar"] span {{
    color: {_SIDEBAR_TEXT} !important;
}}
[data-testid="stSidebar"] h3 {{
    background-color: {_SIDEBAR_H3_BG} !important;
    color: {_SIDEBAR_H3_TEXT} !important;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 10px {_SHADOW_CARD} !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border-left: 4px solid #d4af37 !important;
    margin-top: 20px !important;
    margin-bottom: 12px !important;
}}

/* Tags / pills */
div[data-baseweb="tag"], span[data-baseweb="tag"] {{
    background-color: #d4af37 !important;
    color: #000000 !important;
    border-radius: 4px !important;
}}
div[data-baseweb="tag"] *, span[data-baseweb="tag"] * {{
    color: #000000 !important;
    fill: #000000 !important;
}}

/* Scrollable property list */
.property-list {{
    max-height: 750px;
    overflow-y: auto;
    padding-right: 8px;
}}
.property-list::-webkit-scrollbar {{ width: 6px; }}
.property-list::-webkit-scrollbar-thumb {{
    background: {_SCROLLBAR}; border-radius: 3px;
}}

/* Property card */
.prop-card {{
    background: {_BG_CARD};
    border: 1px solid {_BORDER_CARD};
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 12px;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    font-family: 'Inter', 'Segoe UI', sans-serif;
    animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}}
.prop-card:hover {{
    box-shadow: 0 10px 25px {_HOVER_SHADOW} !important;
    border-color: #d4af37 !important;
    transform: translateY(-2px) !important;
}}
.prop-price {{
    font-size: 20px;
    font-weight: 800;
    color: {_TEXT_PRIMARY};
    margin: 0;
}}
.prop-price-m2 {{
    font-size: 13px;
    font-weight: 600;
    color: {_TEXT_SECONDARY};
    margin: 0 0 6px 0;
}}
.prop-type {{
    font-size: 14px;
    font-weight: 700;
    color: {_TEXT_PRIMARY};
    margin: 4px 0 2px 0;
}}
.prop-details {{
    font-size: 12.5px;
    color: {_TEXT_SECONDARY};
    margin: 2px 0;
    line-height: 1.5;
}}
.prop-date {{
    font-size: 11px;
    color: {_TEXT_MUTED};
    margin-top: 4px;
}}
.prop-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    margin-right: 6px;
}}
.badge-maison {{ background: #e67e22; }}
.badge-appart {{ background: #3498db; }}

/* Header bar style */
.seloger-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 2px solid {_HEADER_BORDER};
    margin-bottom: 16px;
    background: transparent;
}}
.seloger-count {{
    font-size: 18px;
    font-weight: 800;
    color: {_TEXT_PRIMARY} !important;
}}

/* Chart cards */
.chart-card {{
    background: {_BG_CARD} !important;
    border: 1px solid {_BORDER_CARD} !important;
    border-radius: 12px !important;
    padding: 20px 24px !important;
    box-shadow: 0 4px 20px {_SHADOW_CARD} !important;
    margin-bottom: 24px !important;
    border-left: 5px solid #d4af37 !important;
}}
.chart-title {{
    font-size: 18px !important;
    font-weight: 800 !important;
    color: {_TEXT_PRIMARY} !important;
    margin: 0 0 6px 0 !important;
    padding: 0 !important;
}}
.chart-subtitle {{
    font-size: 13px !important;
    color: {_TEXT_SECONDARY} !important;
    margin: 0 0 16px 0 !important;
    line-height: 1.4 !important;
}}

/* Advisor box */
.advisor-box {{
    background: {_BG_CARD} !important;
    border: 1px solid {_BORDER_CARD} !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    margin-bottom: 20px !important;
    box-shadow: 0 4px 15px {_SHADOW_CARD} !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
}}
.advisor-header {{
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    flex-wrap: wrap !important;
    gap: 10px !important;
}}
.advisor-project-title {{
    font-size: 13px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    color: {_TEXT_SECONDARY} !important;
    margin: 0 !important;
}}
.advisor-badge-pill {{
    display: inline-block !important;
    padding: 4px 12px !important;
    border-radius: 20px !important;
    font-size: 11.5px !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}}
.advisor-text-desc {{
    font-size: 13.5px !important;
    color: {_TEXT_PRIMARY} !important;
    line-height: 1.5 !important;
    margin: 0 !important;
}}
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


# ---------------------------------------------------------------------------
# 2. CHARGEMENT DES DONNÉES (Parquet pré-traités – ultra-rapide)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Chargement des données DPE…")
def load_dpe():
    """Charge le Parquet DPE pré-traité (déjà filtré Nantes, coordonnées WGS84)."""
    df = pd.read_parquet("data/parquet/dpe_nantes.parquet")
    # Reconstituer les colonnes dérivées (couleurs RGBA, polygones)
    df["color_dpe"] = df["etiquette_dpe"].map(DPE_COLORS)
    df["building_polygon"] = df["building_polygon_json"].apply(json.loads)
    return df


@st.cache_data(show_spinner="Chargement des transactions DVF…")
def load_dvf_geocoded():
    """Charge le Parquet DVF pré-traité (déjà géocodé via BAN)."""
    df = pd.read_parquet("data/parquet/dvf_nantes.parquet")
    # Reconstituer les colonnes de listes Python depuis le JSON
    df["color_prix"] = df["color_prix_json"].apply(json.loads)
    df["color_type"] = df["color_type_json"].apply(json.loads)
    df["building_polygon"] = df["building_polygon_json"].apply(json.loads)
    # Charger les seuils de prix
    with open("data/parquet/dvf_seuils.json", "r") as f:
        seuils = json.load(f)
    df.attrs["seuil_bas"] = seuils["seuil_bas"]
    df.attrs["seuil_haut"] = seuils["seuil_haut"]
    return df


@st.cache_data(show_spinner="Chargement des stations de transport…")
def load_transport():
    """Charge le Parquet transport pré-traité."""
    return pd.read_parquet("data/parquet/transport_nantes.parquet")


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
st.sidebar.subheader("Apparence")

# Toggle thème sombre / clair
if st.sidebar.button(
    "Mode Sombre" if not is_dark else "Mode Clair",
    key="theme_toggle",
    use_container_width=True,
):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

st.sidebar.markdown("")
map_style_name = st.sidebar.selectbox(
    "Fond de carte :",
    options=["Sombre", "Clair", "Coloré"],
    index=0 if is_dark else 2,
)
MAP_STYLES = {
    "Sombre": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    "Clair": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Coloré": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
}
map_style = MAP_STYLES[map_style_name]

choix_transport = st.sidebar.selectbox(
    "Afficher le réseau ferré (tram/train) :",
    options=["Non", "Oui"],
    index=0
)
show_transport = (choix_transport == "Oui")

chart_theme_name = st.sidebar.selectbox(
    "Couleur des graphiques :",
    options=["Bleu & Vert", "Doré & Bronze", "Rouge & Corail", "Violet & Rose"],
    index=0
)
CHART_THEMES = {
    "Bleu & Vert": {"Appartement": "#3498db", "Maison": "#2ecc71"},
    "Doré & Bronze": {"Appartement": "#d4af37", "Maison": "#a05a2c"},
    "Rouge & Corail": {"Appartement": "#e74c3c", "Maison": "#e67e22"},
    "Violet & Rose": {"Appartement": "#9b59b6", "Maison": "#e84393"}
}
chart_theme = CHART_THEMES[chart_theme_name]
color_appart = chart_theme["Appartement"]
color_maison = chart_theme["Maison"]

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
        f"<span class='advisor-project-title'>Avis d'équité de prix (Est-ce un bon prix ?)</span>"
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
        f"<span class='advisor-project-title'>Observatoire Décisionnel Nantes (Business Intelligence)</span>"
        f"<span class='advisor-badge-pill' style='background-color: #d4af37 !important;'>Projet SAE-601</span>"
        f"</div>"
        f"<p class='advisor-text-desc'>{welcome_text}</p>"
        f"</div>"
    )
    st.markdown(advisor_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 5.5 BARRE DE RECHERCHE PAR ADRESSE & ANALYSE DÉTAILLÉE
# ---------------------------------------------------------------------------
# Initialiser le compteur de clé si nécessaire
if "search_key_counter" not in st.session_state:
    st.session_state.search_key_counter = 0

# Rassembler toutes les adresses uniques existantes
addresses_dvf = set(df_dvf["adresse_fmt"].dropna().unique())
addresses_dpe = set(df_dpe["adresse_fmt"].dropna().unique())
all_addresses_list = sorted(list(addresses_dvf.union(addresses_dpe)))

st.markdown("""
<div style='margin-top: 10px; margin-bottom: 5px;'>
    <h3 style='margin: 0; font-size: 16px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; border-left: 4px solid #d4af37; padding-left: 8px;'>Recherche Immobilière par Adresse</h3>
</div>
""", unsafe_allow_html=True)

selected_addr = st.selectbox(
    "Saisissez ou sélectionnez une adresse à Nantes pour obtenir une analyse détaillée :",
    options=[""] + all_addresses_list,
    index=0,
    placeholder="Ex: 10 RUE DE VERDUN",
    key=f"search_addr_input_{st.session_state.search_key_counter}",
    label_visibility="collapsed"
)

if selected_addr != "":
    # --- BOUTON DE RETOUR ---
    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("<- Revenir à la vue globale", key="btn_close_search", use_container_width=True):
            st.session_state.search_key_counter += 1
            st.query_params.clear()
            st.rerun()

    # --- COLLECTE ET INTERPOLATION DES DONNÉES SPATIALES ---
    rows_dpe = df_dpe[df_dpe["adresse_fmt"] == selected_addr]
    rows_dvf = df_dvf[df_dvf["adresse_fmt"] == selected_addr]

    # Déterminer la position géographique
    if not rows_dvf.empty:
        lat = rows_dvf.iloc[0]["lat"]
        lon = rows_dvf.iloc[0]["lon"]
        exact_dvf = True
    elif not rows_dpe.empty:
        lat = rows_dpe.iloc[0]["lat"]
        lon = rows_dpe.iloc[0]["lon"]
        exact_dvf = False
    else:
        lat, lon = 47.2184, -1.5536
        exact_dvf = False

    # 1. Données DPE (exactes ou par voisin le plus proche)
    is_interpolated_dpe = False
    dpe_dist = 0.0
    if not rows_dpe.empty:
        dpe_record = rows_dpe.iloc[0]
    else:
        is_interpolated_dpe = True
        distances_dpe = np.sqrt(((df_dpe["lat"] - lat) * 111.32)**2 + ((df_dpe["lon"] - lon) * 80.0)**2) * 1000.0
        closest_dpe_idx = distances_dpe.idxmin()
        dpe_dist = distances_dpe.loc[closest_dpe_idx]
        dpe_record = df_dpe.loc[closest_dpe_idx]

    # 2. Données DVF (médiane locale du quartier)
    distances_dvf = np.sqrt(((df_dvf["lat"] - lat) * 111.32)**2 + ((df_dvf["lon"] - lon) * 80.0)**2) * 1000.0
    df_dvf_with_dist = df_dvf.copy()
    df_dvf_with_dist["dist_m"] = distances_dvf
    df_neighbors = df_dvf_with_dist[df_dvf_with_dist["adresse_fmt"] != selected_addr]
    
    if not df_neighbors.empty:
        closest_15 = df_neighbors.sort_values("dist_m").head(15)
        median_local_prix_m2 = closest_15["prix_m2"].median()
    else:
        closest_15 = pd.DataFrame()
        median_local_prix_m2 = 0.0

    # 3. Données Transport (réseau ferré à moins de 1km)
    distances_transport = np.sqrt(((df_transport["lat"] - lat) * 111.32)**2 + ((df_transport["lon"] - lon) * 80.0)**2) * 1000.0
    df_trans_local = df_transport.copy()
    df_trans_local["dist_m"] = distances_transport
    df_trans_local = df_trans_local[df_trans_local["dist_m"] <= 1000.0].sort_values("dist_m")
    df_trans_local = df_trans_local.drop_duplicates(subset=["name"])

    # Type de bâtiment
    b_type = "Appartement"
    if not rows_dvf.empty:
        b_type = rows_dvf.iloc[0]["type_local"]
    elif pd.notna(dpe_record.get("type_batiment")):
        if "maison" in str(dpe_record["type_batiment"]).lower():
            b_type = "Maison"

    # Médiane globale Nantes pour ce type
    df_nantes_type = df_dvf[df_dvf["type_local"] == b_type]
    median_nantes_prix_m2 = df_nantes_type["prix_m2"].median() if not df_nantes_type.empty else 2600.0

    # Prix de vente du bien ou estimation locale
    if not rows_dvf.empty:
        building_prix_m2 = rows_dvf.iloc[0]["prix_m2"]
        price_label = "Vente historique"
        has_actual_price = True
    else:
        building_prix_m2 = median_local_prix_m2
        price_label = "Estimation locale"
        has_actual_price = False

    # --- RENDU DE LA FICHE D'ANALYSE DÉTAILLÉE ---
    st.markdown(f"""
    <div style='background: {_BG_CARD}; padding: 20px 24px; border-radius: 12px; border: 1px solid {_BORDER_CARD}; margin-top: 16px; margin-bottom: 24px; border-left: 6px solid #d4af37; box-shadow: 0 4px 15px {_SHADOW_CARD};'>
        <h2 style='margin: 0 0 6px 0; color: {_TEXT_PRIMARY}; font-size: 23px;'>Fiche d'Analyse Immobilière Détaillée</h2>
        <p style='margin: 0; color: #d4af37; font-size: 18px; font-weight: 700;'>{selected_addr}</p>
        <p style='margin: 4px 0 0 0; color: {_TEXT_SECONDARY}; font-size: 12.5px;'>Coordonnées : {lat:.5f}, {lon:.5f} · Nantes Métropole · Type dominant : {b_type}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 3], gap="large")

    # === COLONNE GAUCHE : DPE & Caractéristiques ===
    with col1:
        st.markdown("#### Performance Énergétique")
        
        # Dessin de la frise DPE
        letters = ["A", "B", "C", "D", "E", "F", "G"]
        colors = {
            "A": "#009E5F", "B": "#34B34A", "C": "#BACF11",
            "D": "#FEE900", "E": "#FBBD08", "F": "#F47D22", "G": "#EB1C24"
        }
        
        selected_letter = str(dpe_record.get("etiquette_dpe", "D")).upper()
        
        frise_html = "<div style='display: flex; flex-direction: column; gap: 5px; font-family: \"Inter\", sans-serif; margin-bottom: 16px;'>"
        for letter in letters:
            color = colors[letter]
            is_selected = (letter == selected_letter)
            border_style = "border: 2px solid #ffffff; box-shadow: 0 0 8px rgba(0,0,0,0.25); transform: scale(1.02); opacity: 1.0;" if is_selected else "opacity: 0.5;"
            badge_text = "CE BIEN" if is_selected else ""
            if is_selected and is_interpolated_dpe:
                badge_text = "ESTIMÉ (VOISIN)"
                
            active_indicator = f"<span style='background: #ffffff; color: #111827; font-weight: 900; padding: 2px 8px; border-radius: 4px; font-size: 10px; margin-left: auto; box-shadow: 0 1px 3px rgba(0,0,0,0.15);'>{badge_text}</span>" if is_selected else ""
            
            frise_html += f"<div style='display: flex; align-items: center; background-color: {color}; color: #ffffff; padding: 6px 12px; border-radius: 6px; font-weight: 800; font-size: 13px; {border_style}'><span>CLASSE {letter}</span>{active_indicator}</div>"
        frise_html += "</div>"
        st.markdown(frise_html, unsafe_allow_html=True)
        
        if is_interpolated_dpe:
            st.caption(f"ℹ️ Aucun diagnostic DPE exact à cette adresse. Caractéristiques basées sur le bâtiment voisin le plus proche à {dpe_dist:.0f} m.")
            
        # Caractéristiques techniques
        st.markdown("##### Détails du Diagnostic")
        conso = dpe_record.get("conso_fmt", "N/A")
        ges = dpe_record.get("etiquette_ges", "N/A")
        chauffage = dpe_record.get("type_energie_principale_chauffage", "N/A")
        construction = dpe_record.get("periode_construction", "N/A")
        
        st.markdown(f"<table style='width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 20px;'>"
                    f"<tr style='border-bottom: 1px solid {_BORDER_CARD};'><td style='padding: 6px 0; color: {_TEXT_SECONDARY};'>Consommation 5 usages</td><td style='padding: 6px 0; text-align: right; font-weight: bold;'>{conso}</td></tr>"
                    f"<tr style='border-bottom: 1px solid {_BORDER_CARD};'><td style='padding: 6px 0; color: {_TEXT_SECONDARY};'>Émissions de GES</td><td style='padding: 6px 0; text-align: right; font-weight: bold; color: #ff6b6b;'>Classe {ges}</td></tr>"
                    f"<tr style='border-bottom: 1px solid {_BORDER_CARD};'><td style='padding: 6px 0; color: {_TEXT_SECONDARY};'>Énergie chauffage</td><td style='padding: 6px 0; text-align: right; font-weight: bold;'>{chauffage}</td></tr>"
                    f"<tr style='border-bottom: 1px solid {_BORDER_CARD};'><td style='padding: 6px 0; color: {_TEXT_SECONDARY};'>Époque de construction</td><td style='padding: 6px 0; text-align: right; font-weight: bold;'>{construction}</td></tr>"
                    f"</table>", unsafe_allow_html=True)

        # --- CALCUL ET RENDER DU SCORE D'ÉCO-ATTRACTIVITÉ SPATIALE ---
        # 1. Calcul de la partie DPE
        dpe_letter = str(dpe_record.get("etiquette_dpe", "D")).upper()
        dpe_map = {"A": 7, "B": 6, "C": 5, "D": 4, "E": 3, "F": 2, "G": 1}
        dpe_score_val = dpe_map.get(dpe_letter, 4)
        points_dpe = ((dpe_score_val - 1) / 6.0) * 50.0

        # 2. Calcul de la partie Transport
        if not df_trans_local.empty:
            closest_dist_m = df_trans_local.iloc[0]["dist_m"]
            if closest_dist_m <= 100.0:
                points_trans = 50.0
            elif closest_dist_m >= 1000.0:
                points_trans = 0.0
            else:
                points_trans = 50.0 * (1.0 - (closest_dist_m - 100.0) / 900.0)
        else:
            closest_dist_m = None
            points_trans = 0.0

        # 3. Score total
        eco_score = float(np.clip(points_dpe + points_trans, 0.0, 100.0))

        # 4. Verdicts & colorations adaptatives (sans emojis)
        if eco_score >= 80.0:
            verdict = "Pépite Verte"
            verdict_desc = "Ce bien immobilier présente une isolation remarquable couplée à une excellente accessibilité aux transports durables. C'est un logement à très faible impact carbone."
            verdict_color = "#009E5F"
            verdict_bg = "rgba(0, 158, 95, 0.08)"
        elif eco_score >= 60.0:
            verdict = "Éco-Performance Satisfaisante"
            verdict_desc = "Un très bon équilibre entre la performance thermique et l'accès au réseau ferré. Le confort de vie est assuré et la mobilité douce est facilitée."
            verdict_color = "#BACF11"
            verdict_bg = "rgba(186, 207, 17, 0.08)"
        elif eco_score >= 40.0:
            verdict = "Éco-Performance Moyenne"
            verdict_desc = "Le bien se situe dans la moyenne. Des pistes d'amélioration sont envisageables, soit au niveau de l'isolation thermique (DPE), soit de la connectivité ferroviaire."
            verdict_color = "#FBBD08"
            verdict_bg = "rgba(251, 189, 8, 0.08)"
        else:
            verdict = "Performance Environnementale Faible"
            verdict_desc = "La performance globale est à optimiser. Ce logement est énergivore et/ou éloigné du réseau de transport ferré. Des travaux de rénovation thermique ou l'usage de modes de transport alternatifs sont préconisés."
            verdict_color = "#F47D22"
            verdict_bg = "rgba(244, 125, 34, 0.08)"

        st.markdown("##### Score d'Éco-Attractivité")

        # 5. Jauge Plotly Premium
        fig_eco = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = eco_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {
                'text': "<b>Score d'Éco-Attractivité</b>",
                'font': {'size': 14, 'color': _TEXT_PRIMARY, 'family': '"Inter", sans-serif'}
            },
            number = {
                'font': {'size': 28, 'color': verdict_color, 'family': '"Inter", sans-serif'},
                'suffix': " / 100"
            },
            gauge = {
                'axis': {
                    'range': [0, 100],
                    'tickwidth': 1,
                    'tickcolor': _CHART_TEXT,
                    'tickfont': {'color': _CHART_TEXT, 'size': 10}
                },
                'bar': {'color': "#d4af37", 'thickness': 0.25},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 1,
                'bordercolor': _BORDER_CARD,
                'steps': [
                    {'range': [0, 40], 'color': "rgba(244, 125, 34, 0.15)"},
                    {'range': [40, 60], 'color': "rgba(251, 189, 8, 0.15)"},
                    {'range': [60, 80], 'color': "rgba(186, 207, 17, 0.15)"},
                    {'range': [80, 100], 'color': "rgba(0, 158, 95, 0.15)"}
                ]
            }
        ))

        fig_eco.update_layout(
            margin=dict(l=15, r=15, t=40, b=15),
            height=160,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig_eco, use_container_width=True, config={'displayModeBar': False})

        # 6. Rendu HTML de la Fiche Descriptive (non-indented multiline HTML formatting)
        verdict_html = (
            f"<div style='background: {verdict_bg}; border: 1px solid {verdict_color}44; "
            f"border-left: 5px solid {verdict_color}; border-radius: 8px; padding: 12px 14px; "
            f"font-family: \"Inter\", sans-serif; margin-bottom: 20px; box-shadow: 0 2px 6px {_SHADOW_CARD};'>"
            f"<div style='font-size: 13px; font-weight: 800; color: {verdict_color}; margin-bottom: 6px;'>"
            f"{verdict.upper()}"
            f"</div>"
            f"<div style='font-size: 12px; line-height: 1.5; color: {_TEXT_PRIMARY}; margin-bottom: 10px;'>"
            f"{verdict_desc}"
            f"</div>"
            f"<div style='display: flex; justify-content: space-between; font-size: 11px; border-top: 1px solid {verdict_color}22; padding-top: 8px;'>"
            f"<span style='color: {_TEXT_SECONDARY};'>Performance DPE : <b>{points_dpe:.1f} / 50</b></span>"
            f"<span style='color: {_TEXT_SECONDARY};'>Réseau ferré : <b>{points_trans:.1f} / 50</b></span>"
            f"</div>"
            f"</div>"
        )
        st.markdown(verdict_html, unsafe_allow_html=True)

    # === COLONNE DROITE : Valorisation & Comparatif ===
    with col2:
        st.markdown("#### Analyse Comparative de Marché (Prix/m²)")
        
        # Graphique Plotly de comparaison
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            y=["Médiane Ville", "Médiane Quartier", price_label],
            x=[median_nantes_prix_m2, median_local_prix_m2, building_prix_m2],
            orientation='h',
            marker=dict(
                color=['#cbd5e1', '#2ecc71', '#d4af37'],
                line=dict(color='#ffffff', width=1)
            ),
            text=[f"{median_nantes_prix_m2:,.0f} €/m²", f"{median_local_prix_m2:,.0f} €/m²", f"{building_prix_m2:,.0f} €/m²"],
            textposition='auto',
            textfont=dict(color='#111827', weight='bold', size=11),
            showlegend=False
        ))
        fig_comp.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=160,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, visible=False),
            yaxis=dict(tickfont=dict(color=_TEXT_PRIMARY, size=12, weight='bold'))
        )
        st.plotly_chart(fig_comp, use_container_width=True, config={'displayModeBar': False})
        
        # Affichage des transactions réelles ou de l'estimation
        if has_actual_price:
            st.markdown("##### Ventes enregistrées à cette adresse")
            for _, row in rows_dvf.iterrows():
                val_fonc = row.get("valeur_fonciere", 0)
                surf = row.get("surface_m2", 0)
                pcs = row.get("nb_pieces", 0)
                date_m = row.get("date_mutation", "")
                
                st.markdown(f"<div style='background: {_BG_CARD}; padding: 12px 16px; border: 1px solid {_BORDER_CARD}; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 2px 6px {_SHADOW_CARD};'>"
                            f"<div style='display: flex; justify-content: space-between; align-items: center;'>"
                            f"<span style='font-size: 16px; font-weight: bold; color: {_TEXT_PRIMARY};'>{val_fonc:,.0f} €</span>"
                            f"<span style='font-size: 12.5px; font-weight: bold; color: #d4af37;'>{row['prix_m2']:,.0f} €/m²</span>"
                            f"</div>"
                            f"<div style='font-size: 12px; color: {_TEXT_SECONDARY}; margin-top: 4px;'>"
                            f"{b_type} · {surf:.0f} m² · {int(pcs)} pièces · Vente du {date_m}"
                            f"</div>"
                            f"</div>".replace(",", " "), unsafe_allow_html=True)
        else:
            st.info(f"Aucune vente enregistrée à cette adresse depuis 2024. Estimation locale médiane : **{median_local_prix_m2:,.0f} €/m²**.")

        # Tableau des 5 ventes les plus proches
        if not closest_15.empty:
            st.markdown("##### Les 5 ventes les plus proches (Micro-marché)")
            df_closest_5 = closest_15.head(5)[["adresse_fmt", "type_local", "surface_m2", "nb_pieces", "valeur_fonciere", "prix_m2", "dist_m"]]
            df_show = df_closest_5.rename(columns={
                "adresse_fmt": "Adresse",
                "type_local": "Type",
                "surface_m2": "Surface",
                "valeur_fonciere": "Prix de vente",
                "prix_m2": "Prix/m²",
                "dist_m": "Distance"
            })
            df_show["Surface"] = df_show["Surface"].apply(lambda x: f"{x:.0f} m²" if pd.notna(x) else "")
            df_show["Prix de vente"] = df_show["Prix de vente"].apply(lambda x: f"{x:,.0f} €".replace(",", " ") if pd.notna(x) else "")
            df_show["Prix/m²"] = df_show["Prix/m²"].apply(lambda x: f"{x:,.0f} €/m²".replace(",", " ") if pd.notna(x) else "")
            df_show["Distance"] = df_show["Distance"].apply(lambda x: f"{x:.0f} m")
            
            st.dataframe(df_show, hide_index=True, use_container_width=True)

    # === SECTION DU BAS : Transports & Mini-carte ===
    st.markdown("---")
    col_map_loc, col_trans_loc = st.columns([3, 2], gap="large")
    
    with col_map_loc:
        st.markdown("#### Cartographie Locale & Environnement")
        
        # Halo de surbrillance doré
        df_center = pd.DataFrame([{"lat": lat, "lon": lon}])
        layer_search_halo = pdk.Layer(
            "ScatterplotLayer",
            data=df_center,
            get_position="[lon, lat]",
            get_radius=22,
            radius_min_pixels=14,
            radius_max_pixels=35,
            get_fill_color=[212, 175, 55, 130],
            get_line_color=[255, 255, 255, 255],
            line_width_min_pixels=2,
        )
        layer_search_center = pdk.Layer(
            "ScatterplotLayer",
            data=df_center,
            get_position="[lon, lat]",
            get_radius=6,
            radius_min_pixels=5,
            radius_max_pixels=12,
            get_fill_color=[255, 215, 0, 255],
            get_line_color=[255, 255, 255, 255],
            line_width_min_pixels=2,
        )
        
        # Ventes proches
        layer_sales_local = pdk.Layer(
            "ScatterplotLayer",
            data=closest_15 if not closest_15.empty else pd.DataFrame(),
            get_position="[lon, lat]",
            get_radius=15,
            radius_min_pixels=5,
            radius_max_pixels=14,
            get_fill_color="color_prix",
            get_line_color=[255, 255, 255, 180],
            line_width_min_pixels=1,
            pickable=True,
        )
        
        # Transports locaux (déjà calculés en haut de la fiche d'analyse)
        pass
        
        layer_trans_local = pdk.Layer(
            "ScatterplotLayer",
            data=df_trans_local if not df_trans_local.empty else pd.DataFrame(),
            get_position="[lon, lat]",
            get_radius=18,
            radius_min_pixels=4,
            radius_max_pixels=12,
            get_fill_color=[52, 152, 219, 220],
            get_line_color=[255, 255, 255, 160],
            line_width_min_pixels=1,
            pickable=True,
        )
        
        view_state_local = pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=16,
            pitch=0,
            bearing=0
        )
        
        tooltip_local = {
            "html": (
                "<div style='font-family:Inter,sans-serif;padding:8px;"
                "background:#fff;border-radius:6px;color:#111827;"
                "box-shadow:0 2px 10px rgba(0,0,0,.15);font-size:12px;'>"
                "<b>{adresse_fmt}</b><br>"
                "{valeur_fmt}<br>"
                "{prix_m2_fmt}<br>"
                "{surface_m2} m² · {nb_pieces} pièces"
                "</div>"
            ),
            "style": {"backgroundColor": "transparent", "border": "none", "padding": "0"},
        }
        
        st.pydeck_chart(
            pdk.Deck(
                map_style=map_style,
                initial_view_state=view_state_local,
                layers=[layer_search_halo, layer_search_center, layer_sales_local, layer_trans_local],
                tooltip=tooltip_local
            ),
            use_container_width=True
        )

    with col_trans_loc:
        st.markdown("#### Réseau Ferré à Proximité (< 1km)")
        
        if not df_trans_local.empty:
            trans_html = "<div style='display: flex; flex-direction: column; gap: 8px; margin-top: 10px;'>"
            for _, station in df_trans_local.iterrows():
                name = station["name"]
                dist = station["dist_m"]
                r_type = station["railway_type"]
                badge_bg = "#3498db" if "tram" in str(r_type).lower() else "#9b59b6"
                
                trans_html += (
                    f"<div style='background: {_BG_CARD}; border: 1px solid {_BORDER_CARD}; border-left: 5px solid {badge_bg}; border-radius: 8px; padding: 10px 14px; display: flex; align-items: center; gap: 10px; box-shadow: 0 1px 4px {_SHADOW_CARD};'>"
                    f"<div style='flex: 1;'>"
                    f"<div style='font-weight: 800; font-size: 13px; color: {_TEXT_PRIMARY};'>{name}</div>"
                    f"<div style='font-size: 11px; color: {_TEXT_SECONDARY};'>{r_type.upper()} · à {dist:.0f} mètres</div>"
                    f"</div>"
                    f"</div>"
                )
            trans_html += "</div>"
            st.markdown(trans_html, unsafe_allow_html=True)
        else:
            st.info("Aucune station du réseau ferré (tram/train) à moins de 1 kilomètre de cette adresse.")

    # === SECTION DU BAS 2 : Simulateur de Financement ===
    st.markdown("---")
    st.markdown("#### Simulateur de Financement & Mensualités de Crédit")
    
    # Détermination du prix de base pour l'adresse
    if not rows_dvf.empty:
        base_price = float(rows_dvf.iloc[0]["valeur_fonciere"])
    else:
        default_surf = dpe_record.get("surface_habitable_logement", 70.0)
        if pd.isna(default_surf) or default_surf <= 0:
            default_surf = 70.0
        base_price = float(building_prix_m2 * default_surf)
    
    base_price = float(round(base_price / 5000.0) * 5000.0)
    if base_price < 10000.0:
        base_price = 150000.0
        
    col_sim_in, col_sim_out = st.columns([1, 1], gap="large")
    
    with col_sim_in:
        sim_price = st.number_input(
            "Prix du bien (EUR) :",
            min_value=10000.0,
            max_value=5000000.0,
            value=base_price,
            step=5000.0,
            key=f"sim_price_{selected_addr}"
        )
        
        default_apport = float(min(round(sim_price * 0.15 / 5000.0) * 5000.0, sim_price))
        sim_apport = st.number_input(
            "Apport personnel (EUR) :",
            min_value=0.0,
            max_value=sim_price,
            value=default_apport,
            step=5000.0,
            key=f"sim_apport_{selected_addr}"
        )
        
        sim_duree = st.slider(
            "Durée de l'emprunt (années) :",
            min_value=5,
            max_value=30,
            value=20,
            step=1,
            key=f"sim_duree_{selected_addr}"
        )
        
        sim_taux = st.slider(
            "Taux d'intérêt fixe (%) :",
            min_value=0.1,
            max_value=10.0,
            value=3.7,
            step=0.1,
            key=f"sim_taux_{selected_addr}"
        )
        
    with col_sim_out:
        montant_emprunt = max(0.0, sim_price - sim_apport)
        if montant_emprunt == 0.0:
            mensualite = 0.0
            cout_credit = 0.0
        else:
            if sim_taux == 0.0:
                mensualite = montant_emprunt / (sim_duree * 12.0)
            else:
                monthly_rate = (sim_taux / 100.0) / 12.0
                nb_months = sim_duree * 12
                mensualite = montant_emprunt * (monthly_rate * (1.0 + monthly_rate)**nb_months) / ((1.0 + monthly_rate)**nb_months - 1.0)
            cout_credit = (mensualite * sim_duree * 12.0) - montant_emprunt
            
        frais_notaire = sim_price * 0.075
        
        mens_str = f"{mensualite:,.0f}".replace(",", " ")
        emprunt_str = f"{montant_emprunt:,.0f}".replace(",", " ")
        cout_str = f"{cout_credit:,.0f}".replace(",", " ")
        notaire_str = f"{frais_notaire:,.0f}".replace(",", " ")
        
        sim_card_html = (
            f"<div style='background: {_BG_CARD}; border: 1px solid {_BORDER_CARD}; "
            f"border-left: 5px solid #d4af37; border-radius: 8px; padding: 20px 24px; "
            f"box-shadow: 0 4px 10px {_SHADOW_CARD}; height: 100%; display: flex; "
            f"flex-direction: column; justify-content: center; font-family: \"Inter\", sans-serif;'>"
            f"<div style='font-size: 11px; font-weight: 800; color: {_TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;'>Mensualité Estimée</div>"
            f"<div style='font-size: 28px; font-weight: 900; color: #d4af37; margin-bottom: 16px;'>{mens_str} € / mois</div>"
            f"<div style='font-size: 13px; color: {_TEXT_PRIMARY}; margin-bottom: 8px;'>Montant emprunté : <b>{emprunt_str} €</b></div>"
            f"<div style='font-size: 13px; color: {_TEXT_PRIMARY}; margin-bottom: 8px;'>Coût du crédit : <b>{cout_str} €</b></div>"
            f"<div style='font-size: 13px; color: {_TEXT_PRIMARY}; margin-bottom: 8px;'>Frais de notaire est. (7.5%) : <b>{notaire_str} €</b></div>"
            f"<div style='font-size: 10px; color: {_TEXT_MUTED}; margin-top: 14px; line-height: 1.3;'>Calcul indicatif hors assurance emprunteur. Taux nominal annuel fixe de {sim_taux:.2f}%.</div>"
            f"</div>"
        )
        st.markdown(sim_card_html, unsafe_allow_html=True)

    # === SECTION DU BAS 3 : Analyses Avancées ===
    st.markdown("---")
    col_radar, col_hist = st.columns([1, 1], gap="large")
    
    with col_radar:
        st.markdown("#### Radar d'Attractivité Multicritères")
        
        # 1. Calculs des scores des axes
        # Axe 1 : Budget (Prix au m² compétitif)
        if building_prix_m2 > 0:
            score_budget = float(np.clip(100.0 * (median_nantes_prix_m2 / building_prix_m2), 10.0, 100.0))
        else:
            score_budget = 50.0
            
        # Axe 2 : Énergie (Confort thermique DPE)
        score_energie = float(np.clip(points_dpe * 2.0, 0.0, 100.0))
        
        # Axe 3 : Transports (Accessibilité réseau ferré)
        score_transport = float(np.clip(points_trans * 2.0, 0.0, 100.0))
        
        # Axe 4 : Espace (Surface du logement par rapport au quartier)
        if not closest_15.empty:
            median_local_surface = closest_15["surface_m2"].median()
        else:
            median_local_surface = 0.0
            
        default_surf = dpe_record.get("surface_habitable_logement", 70.0)
        if pd.isna(default_surf) or default_surf <= 0:
            default_surf = 70.0
            
        if median_local_surface > 0:
            score_espace = float(np.clip(50.0 + (default_surf - median_local_surface) * 2.0, 10.0, 100.0))
        else:
            score_espace = 70.0
            
        categories = ["Budget", "Confort Énergie", "Accès Transport", "Espace Habitable"]
        scores = [score_budget, score_energie, score_transport, score_espace]
        
        # Fermer la boucle du radar
        categories_closed = categories + [categories[0]]
        scores_closed = scores + [scores[0]]
        
        # 2. Dessiner le radar avec Plotly (avec une couleur RGBA transparente valide)
        radar_fill_map = {
            "#009E5F": "rgba(0, 158, 95, 0.25)",
            "#BACF11": "rgba(186, 207, 17, 0.25)",
            "#FBBD08": "rgba(251, 189, 8, 0.25)",
            "#F47D22": "rgba(244, 125, 34, 0.25)"
        }
        radar_fillcolor = radar_fill_map.get(verdict_color, "rgba(212, 175, 55, 0.25)")
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=scores_closed,
            theta=categories_closed,
            fill='toself',
            fillcolor=radar_fillcolor,
            line=dict(color=verdict_color, width=2),
            marker=dict(color=verdict_color, size=6),
            showlegend=False
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(color=_CHART_TEXT, size=9),
                    gridcolor=_CHART_GRID,
                    linecolor=_CHART_GRID
                ),
                angularaxis=dict(
                    tickfont=dict(color=_TEXT_PRIMARY, size=11, weight='bold'),
                    gridcolor=_CHART_GRID
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(l=40, r=40, t=30, b=30),
            height=300,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_radar, use_container_width=True, config={'displayModeBar': False})
        
    with col_hist:
        st.markdown("#### Évolution Historique des Ventes (2025)")
        
        # 1. Extraction et formatage des données temporelles
        # Local (1 km)
        distances_all = np.sqrt(((df_dvf["lat"] - lat) * 111.32)**2 + ((df_dvf["lon"] - lon) * 80.0)**2) * 1000.0
        df_dvf_1k = df_dvf[distances_all <= 1000.0].copy()
        
        df_dvf_1k["date_dt"] = pd.to_datetime(df_dvf_1k["date_mutation"], format="%d/%m/%Y", errors="coerce")
        df_dvf_1k = df_dvf_1k.dropna(subset=["date_dt"])
        df_dvf_1k = df_dvf_1k.sort_values("date_dt")
        
        MONTH_MAP = {
            1: "Jan", 2: "Fév", 3: "Mar", 4: "Avr", 5: "Mai", 6: "Juin",
            7: "Juil", 8: "Août", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Déc"
        }
        
        df_dvf_1k["Mois_Num"] = df_dvf_1k["date_dt"].dt.month
        df_dvf_1k["Mois"] = df_dvf_1k["Mois_Num"].map(MONTH_MAP)
        
        df_trend_local = df_dvf_1k.groupby(["Mois_Num", "Mois"])["prix_m2"].median().reset_index().sort_values("Mois_Num")
        
        # Global (Nantes)
        df_dvf_all = df_dvf.copy()
        df_dvf_all["date_dt"] = pd.to_datetime(df_dvf_all["date_mutation"], format="%d/%m/%Y", errors="coerce")
        df_dvf_all = df_dvf_all.dropna(subset=["date_dt"])
        df_dvf_all["Mois_Num"] = df_dvf_all["date_dt"].dt.month
        df_dvf_all["Mois"] = df_dvf_all["Mois_Num"].map(MONTH_MAP)
        
        df_trend_global = df_dvf_all.groupby(["Mois_Num", "Mois"])["prix_m2"].median().reset_index().sort_values("Mois_Num")
        
        # 2. Dessiner le graphique linéaire comparatif
        fig_trend = go.Figure()
        
        if not df_trend_global.empty:
            fig_trend.add_trace(go.Scatter(
                x=df_trend_global["Mois"],
                y=df_trend_global["prix_m2"],
                mode='lines+markers',
                name='Moyenne Ville (Nantes)',
                line=dict(color='#94a3b8', width=2, dash='dash'),
                marker=dict(color='#94a3b8', size=5)
            ))
            
        if not df_trend_local.empty:
            fig_trend.add_trace(go.Scatter(
                x=df_trend_local["Mois"],
                y=df_trend_local["prix_m2"],
                mode='lines+markers',
                name='Micro-Quartier (1 km)',
                line=dict(color='#d4af37', width=3),
                marker=dict(color='#d4af37', size=6)
            ))
            
        fig_trend.update_layout(
            margin=dict(l=40, r=20, t=20, b=40),
            height=300,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=False,
                tickfont=dict(color=_CHART_TEXT, size=10)
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=_CHART_GRID,
                tickfont=dict(color=_CHART_TEXT, size=10),
                ticksuffix=' €/m²'
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1.0,
                font=dict(color=_TEXT_PRIMARY, size=10)
            )
        )
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

    st.stop()

# Initialiser l'état d'agrandissement de la carte si nécessaire
if "map_expanded" not in st.session_state:
    st.session_state.map_expanded = False

# En-tête style SeLoger avec bouton d'agrandissement
col_head_title, col_head_btn = st.columns([3, 1])
with col_head_title:
    st.markdown(
        f"<div class='seloger-header' style='border-bottom: none; margin-bottom: 0;'>"
        f"<span class='seloger-count'>"
        f"{nb_dvf:,} transactions immobilières – Nantes, disponibles sur la carte"
        f"</span></div>".replace(",", " "),
        unsafe_allow_html=True,
    )
with col_head_btn:
    btn_label = "Réduire la carte" if st.session_state.map_expanded else "Agrandir la carte"
    if st.button(btn_label, key="btn_toggle_map_size", use_container_width=True):
        st.session_state.map_expanded = not st.session_state.map_expanded
        st.rerun()

st.markdown("<hr style='margin-top: 0; margin-bottom: 16px; border-color: rgba(0,0,0,0.1);'>", unsafe_allow_html=True)

# ── Layout principal adaptatif ──
if st.session_state.map_expanded:
    col_list = None
    col_map = st.container()
else:
    col_list, col_map = st.columns([2, 3], gap="medium")

# === COLONNE GAUCHE : Liste des biens ===
if not st.session_state.map_expanded:
    with col_list:
        if selected_row is not None:
            # Bouton élégant de retour à la liste complète
            if st.button("<- Voir tous les biens", key="btn_reset_selection"):
                st.query_params.clear()
                st.rerun()
                
            st.markdown("#### Bien sélectionné")
            
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
            st.markdown("#### 5 Biens les plus similaires (Prix & Lieu)")
            
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
# 7. ANALYSE DPE (uniquement si aucun bien n'est sélectionné)
# ---------------------------------------------------------------------------
if selected_row is None:
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
        st.markdown("##### DPE par bâtiment – Couleur = Étiquette énergétique")
        
        # Initialiser le filtre de carte DPE si nécessaire
        if "selected_dpe_map_filter" not in st.session_state:
            st.session_state.selected_dpe_map_filter = None
            
        leg_dpe = st.columns(7)
        dpe_labels = ["A", "B", "C", "D", "E", "F", "G"]
        dpe_css = ["#27ae60", "#2ecc71", "#a4c400", "#f1c40f", "#e67e22", "#d35400", "#c0392b"]
        
        for col_l, label, color in zip(leg_dpe, dpe_labels, dpe_css):
            # Petit badge de couleur centré au-dessus du bouton
            col_l.markdown(
                f"<div style='text-align: center; margin-bottom: 4px;'>"
                f"<span style='display:inline-block;width:12px;height:12px;background:{color};border-radius:50%;'></span>"
                f"</div>",
                unsafe_allow_html=True
            )
            is_active = (st.session_state.selected_dpe_map_filter == label)
            btn_type = "primary" if is_active else "secondary"
            if col_l.button(f"DPE {label}", key=f"btn_dpe_map_filter_{label}", type=btn_type, use_container_width=True):
                if is_active:
                    st.session_state.selected_dpe_map_filter = None
                else:
                    st.session_state.selected_dpe_map_filter = label
                st.rerun()
                
        # Filtrer dynamiquement les données selon le bouton DPE sélectionné
        df_dots_dpe = df_dpe_f.copy()
        if st.session_state.selected_dpe_map_filter is not None:
            df_dots_dpe = df_dots_dpe[df_dots_dpe["etiquette_dpe"] == st.session_state.selected_dpe_map_filter]
            st.caption(f"Filtre actif : Affichage uniquement des bâtiments de classe {st.session_state.selected_dpe_map_filter}. Re-cliquez sur le bouton pour tout afficher.")
            
        df_hm = df_dots_dpe.dropna(subset=["dpe_score"]).copy()
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
            "ScatterplotLayer", data=df_dots_dpe,
            get_position="[lon, lat]", get_radius=8,
            radius_min_pixels=1, radius_max_pixels=12,
            get_fill_color="color_dpe", pickable=True, auto_highlight=True, opacity=1.0,
        )
        st.pydeck_chart(pdk.Deck(
            map_style=map_style, initial_view_state=VIEW_STATE_2D,
            layers=[layer_zones_dpe, layer_dots_dpe], tooltip=tooltip_dpe,
        ))
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
    line=dict(color=color_appart, width=3, shape='spline'),
    marker=dict(size=8, color=color_appart, line=dict(color='#ffffff', width=1.5))
))
fig_prices.add_trace(go.Scatter(
    x=df_prices["Année"], y=df_prices["Maison"],
    mode='lines+markers', name='Maison',
    line=dict(color=color_maison, width=3, shape='spline'),
    marker=dict(size=8, color=color_maison, line=dict(color='#ffffff', width=1.5))
))
fig_prices.update_layout(
    margin=dict(l=40, r=20, t=10, b=40),
    height=320,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color=_TEXT_PRIMARY)),
    xaxis=dict(
        showgrid=False,
        tickmode='linear',
        tickfont=dict(color=_CHART_TEXT),
        linecolor=_CHART_LINE
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor=_CHART_GRID,
        ticksuffix=' €/m²',
        tickfont=dict(color=_CHART_TEXT),
        linecolor=_CHART_LINE
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
        name='Maison', marker_color=color_maison
    ))
    fig_age.add_trace(go.Bar(
        x=periods, y=[0.5, 10, 23, 53, 16],
        name='Appartement', marker_color=color_appart
    ))
    fig_age.update_layout(
        barmode='group',
        margin=dict(l=40, r=20, t=10, b=40),
        height=280,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(color=_TEXT_PRIMARY)),
        xaxis=dict(showgrid=False, tickfont=dict(color=_CHART_TEXT)),
        yaxis=dict(showgrid=True, gridcolor=_CHART_GRID, ticksuffix='%', tickfont=dict(color=_CHART_TEXT))
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
        marker_color=color_appart,
        showlegend=False
    ))
    fig_typo.update_layout(
        margin=dict(l=40, r=20, t=10, b=40),
        height=280,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(color=_CHART_TEXT)),
        yaxis=dict(showgrid=True, gridcolor=_CHART_GRID, ticksuffix='%', tickfont=dict(color=_CHART_TEXT))
    )
    st.plotly_chart(fig_typo, use_container_width=True)

