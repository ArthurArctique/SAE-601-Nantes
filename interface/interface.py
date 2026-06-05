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
# 1. CONFIGURATION ET THEME
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Observatoire Foncier",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    _SIDEBAR_H3_BG = "#0f172a"
    _SIDEBAR_H3_TEXT = "#f1f5f9"
    _SIDEBAR_TEXT = "#e2e8f0"
else:
    _BG_MAIN = "#ffffff"
    _BG_SIDEBAR = "#f8fafc"
    _BG_CARD = "#ffffff"
    _BORDER_CARD = "#e2e8f0"
    _TEXT_PRIMARY = "#111827"
    _TEXT_SECONDARY = "#64748b"
    _TEXT_MUTED = "#aaaaaa"
    _SHADOW_CARD = "rgba(0,0,0,0.05)"
    _BORDER_SIDEBAR = "#e2e8f0"
    _SCROLLBAR = "#cccccc"
    _HOVER_SHADOW = "rgba(0,0,0,0.08)"
    _CHART_GRID = "#e2e8f0"
    _CHART_TEXT = "#64748b"
    _SIDEBAR_H3_BG = "#ffffff"
    _SIDEBAR_H3_TEXT = "#1e293b"
    _SIDEBAR_TEXT = "#000000"

DB_PATH = "sae601_nantes.duckdb"

DEPT_NAMES = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence", "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes", "09": "Ariège", "10": "Aube",
    "11": "Aude", "12": "Aveyron", "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal",
    "16": "Charente", "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "2A": "Corse-du-Sud",
    "2B": "Haute-Corse", "21": "Côte-d'Or", "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne",
    "25": "Doubs", "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir", "29": "Finistère", "30": "Gard",
    "31": "Haute-Garonne", "32": "Gers", "33": "Gironde", "34": "Hérault", "35": "Ille-et-Vilaine",
    "36": "Indre", "37": "Indre-et-Loire", "38": "Isère", "39": "Jura", "40": "Landes",
    "41": "Loir-et-Cher", "42": "Loire", "43": "Haute-Loire", "44": "Loire-Atlantique", "45": "Loiret",
    "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère", "49": "Maine-et-Loire", "50": "Manche",
    "51": "Marne", "52": "Haute-Marne", "53": "Mayenne", "54": "Meurthe-et-Moselle", "55": "Meuse",
    "56": "Morbihan", "57": "Moselle", "58": "Nièvre", "59": "Nord", "60": "Oise", "61": "Orne",
    "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques", "65": "Hautes-Pyrénées",
    "66": "Pyrénées-Orientales", "67": "Bas-Rhin", "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône",
    "71": "Saône-et-Loire", "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie", "75": "Paris",
    "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines", "79": "Deux-Sèvres", "80": "Somme",
    "81": "Tarn", "82": "Tarn-et-Garonne", "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne",
    "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne", "90": "Territoire de Belfort", "91": "Essonne",
    "92": "Hauts-de-Seine", "93": "Seine-Saint-Denis", "94": "Val-de-Marne", "95": "Val-d'Oise",
}

DPE_COLORS = {
    "A": [39, 174, 96, 220], "B": [46, 204, 113, 220], "C": [164, 196, 0, 220],
    "D": [241, 196, 15, 220], "E": [230, 126, 34, 220], "F": [211, 84, 0, 220],
    "G": [192, 57, 43, 220],
}

PRICE_COLORS = [
    [140, 140, 140, 220], [230, 190, 10, 220], [220, 53, 69, 220],
]

# ---------------------------------------------------------------------------
# 2. CSS
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* No scroll */
html, body, .stApp {{ overflow: hidden !important; font-family: 'Inter', sans-serif !important; }}
.stApp {{ background-color: {_BG_MAIN} !important; transition: background-color 0.3s ease; }}
.block-container {{ padding-top: 1rem !important; padding-bottom: 0 !important; max-width: 98% !important; }}
header[data-testid="stHeader"] {{ display: none !important; }}

/* Textes généraux */
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp p,.stApp li,.stApp span:not(.prop-badge) {{ color: {_TEXT_PRIMARY} !important; }}
button[data-baseweb="tab"] p, button[data-baseweb="tab"] span {{ color: {_TEXT_PRIMARY} !important; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background-color: {_BG_SIDEBAR} !important; border-right: 1px solid {_BORDER_SIDEBAR}; transition: background-color 0.3s ease; }}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,[data-testid="stSidebar"] span {{ color: {_SIDEBAR_TEXT} !important; }}
[data-testid="stSidebar"] h3 {{
    background: {_SIDEBAR_H3_BG}; color: {_SIDEBAR_H3_TEXT} !important; padding: 8px 12px !important;
    border-radius: 8px !important; box-shadow: 0 2px 8px {_SHADOW_CARD} !important;
    font-size: 12px !important; font-weight: 700 !important; text-transform: uppercase !important;
    letter-spacing: .5px !important; border-left: 3px solid #d4af37 !important;
    margin-top: 14px !important; margin-bottom: 8px !important;
}}

/* Tags dorés */
div[data-baseweb="tag"],span[data-baseweb="tag"] {{ background-color: #d4af37 !important; color: #000 !important; border-radius: 4px !important; font-weight: 600 !important; }}
div[data-baseweb="tag"] *,span[data-baseweb="tag"] * {{ color: #000 !important; fill: #000 !important; }}

/* Boutons d'action */
.stButton > button {{ border-radius: 8px !important; font-weight: 600 !important; padding: 6px 12px !important; transition: all 0.25s ease !important; border: 1px solid {_BORDER_CARD} !important; background-color: {_BG_SIDEBAR} !important; color: {_TEXT_PRIMARY} !important; }}
.stButton > button:hover {{ border-color: #d4af37 !important; background-color: {_BG_CARD} !important; box-shadow: 0 4px 12px {_HOVER_SHADOW} !important; }}
button[data-testid="baseButton-primary"] {{ background-color: #1e293b !important; color: #fff !important; border: none !important; }}
button[data-testid="baseButton-primary"]:hover {{ background-color: #d4af37 !important; color: #000 !important; }}

/* Property cards */
.property-list {{ max-height: 68vh; overflow-y: auto; padding-right: 6px; }}
.property-list::-webkit-scrollbar {{ width: 5px; }}
.property-list::-webkit-scrollbar-thumb {{ background: {_SCROLLBAR}; border-radius: 3px; }}
.prop-card {{
    background: {_BG_CARD}; border: 1px solid {_BORDER_CARD}; border-radius: 10px; padding: 14px;
    margin-bottom: 10px; transition: all .2s ease; font-family: 'Inter', sans-serif;
}}
.prop-card:hover {{ box-shadow: 0 6px 18px {_HOVER_SHADOW}; border-color: #d4af37; transform: translateY(-1px); }}
.prop-price {{ font-size: 18px; font-weight: 800; color: {_TEXT_PRIMARY}; margin: 0; }}
.prop-price-m2 {{ font-size: 12px; font-weight: 600; color: {_TEXT_SECONDARY}; margin: 0 0 4px 0; }}
.prop-type {{ font-size: 13px; font-weight: 700; color: {_TEXT_PRIMARY}; margin: 3px 0 1px 0; }}
.prop-details {{ font-size: 12px; color: {_TEXT_SECONDARY}; margin: 1px 0; }}
.prop-date {{ font-size: 10px; color: {_TEXT_MUTED}; margin-top: 3px; }}
.prop-badge {{ display: inline-block; padding: 1px 7px; border-radius: 3px; font-size: 10px; font-weight: 700; color: #fff; margin-right: 5px; }}
.badge-maison {{ background: #e67e22; }} .badge-appart {{ background: #3498db; }}

/* Metric cards */
.metric-row {{ display: flex; gap: 12px; margin-bottom: 10px; }}
.metric-card {{
    flex: 1; background: {_BG_SIDEBAR}; border: 1px solid {_BORDER_SIDEBAR}; border-radius: 10px;
    padding: 12px 16px; text-align: center;
}}
.metric-card .val {{ font-size: 22px; font-weight: 900; color: {_TEXT_PRIMARY}; }}
.metric-card .lbl {{ font-size: 11px; font-weight: 600; color: {_TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: .5px; }}

/* Chart card */
.chart-card {{
    background: {_BG_CARD}; border: 1px solid {_BORDER_CARD}; border-radius: 10px;
    padding: 14px 18px; box-shadow: 0 2px 10px {_SHADOW_CARD};
    border-left: 4px solid #d4af37; margin-bottom: 12px;
}}
.chart-title {{ font-size: 16px; font-weight: 800; color: {_TEXT_PRIMARY}; margin: 0 0 4px 0; }}
.chart-subtitle {{ font-size: 12px; color: {_TEXT_SECONDARY}; margin: 0; line-height: 1.3; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 3. HELPERS
# ---------------------------------------------------------------------------
def price_color(prix_m2, seuil_bas, seuil_haut):
    if pd.isna(prix_m2): return [120, 120, 120, 100]
    if prix_m2 < seuil_bas: return PRICE_COLORS[0]
    elif prix_m2 < seuil_haut: return PRICE_COLORS[1]
    else: return PRICE_COLORS[2]

def _make_building_polygon(lon, lat, type_local="Appartement", seed=None):
    rng = random.Random(seed) if seed is not None else random.Random(int(abs(lon * 1e6) + abs(lat * 1e6)))
    if type_local == "Maison":
        w_m, h_m = rng.uniform(8, 14), rng.uniform(10, 16)
    else:
        w_m, h_m = rng.uniform(14, 25), rng.uniform(20, 40)
    m_lat = 111_320.0
    m_lon = 111_320.0 * math.cos(math.radians(lat))
    dw, dh = (w_m / 2) / m_lon, (h_m / 2) / m_lat
    angle = rng.uniform(0, math.pi)
    ca, sa = math.cos(angle), math.sin(angle)
    corners = [(-dw, -dh), (dw, -dh), (dw, dh), (-dw, dh)]
    poly = [[cx * ca - cy * sa + lon, cx * sa + cy * ca + lat] for cx, cy in corners]
    poly.append(poly[0])
    return poly

# ---------------------------------------------------------------------------
# 4. DATA LOADING
# ---------------------------------------------------------------------------
if not os.path.exists(DB_PATH):
    st.error("⚠️ Base de données introuvable. Utilisez la page 'Mise à jour' pour la créer.")
    st.stop()

db_mtime = os.path.getmtime(DB_PATH)

@st.cache_data(show_spinner=False)
def get_depts(_mtime):
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("SELECT DISTINCT SUBSTRING(CAST(code_insee AS VARCHAR),1,2) AS d FROM fait_transactions ORDER BY d").df()
    con.close()
    return df["d"].tolist()

@st.cache_data(show_spinner=False)
def get_cities(dept, _mtime):
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute(f"""
        SELECT nom_commune, COUNT(*) as nb
        FROM fait_transactions
        WHERE SUBSTRING(CAST(code_insee AS VARCHAR),1,2) = '{dept}'
          AND lat IS NOT NULL
        GROUP BY 1 ORDER BY 2 DESC
    """).df()
    con.close()
    return df["nom_commune"].tolist()

@st.cache_data(show_spinner="Chargement des données…")
def load_city_data(dept, city, _mtime):
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute(f"""
        SELECT
            prix AS valeur_fonciere, type_bien AS type_local,
            surface AS surface_m2, pieces AS nb_pieces,
            lat, lon, prix_m2,
            dpe_classe, ges_classe, date_mutation, nom_commune, adresse_normalisee
        FROM fait_transactions
        WHERE SUBSTRING(CAST(code_insee AS VARCHAR),1,2) = '{dept}'
          AND nom_commune = '{city.replace("'", "''")}'
          AND lat IS NOT NULL AND lon IS NOT NULL
          AND prix BETWEEN 20000 AND 5000000
          AND surface BETWEEN 10 AND 400
    """).df()

    transport = con.execute(f"""
        SELECT lat, lon, name, railway_type FROM dim_transport
        WHERE lat IS NOT NULL AND lon IS NOT NULL
    """).df()
    con.close()

    if len(df) == 0:
        return df, pd.DataFrame(), transport, 3000.0, 4500.0

    # Pré-calculs
    df["valeur_fmt"] = df["valeur_fonciere"].apply(lambda x: f"{x:,.0f} €".replace(",", " ") if pd.notna(x) else "N/A")
    df["prix_m2_fmt"] = df["prix_m2"].apply(lambda x: f"{x:,.0f} €/m²".replace(",", " ") if pd.notna(x) else "N/A")
    df["price_label"] = df["valeur_fonciere"].apply(
        lambda x: f"{x/1000:,.0f}k €".replace(",", " ") if pd.notna(x) and x >= 1000 else ""
    )

    pm2 = df["prix_m2"].dropna()
    seuil_bas = float(pm2.quantile(0.33)) if len(pm2) > 0 else 3000.0
    seuil_haut = float(pm2.quantile(0.66)) if len(pm2) > 0 else 4500.0

    df["color_prix"] = df["prix_m2"].apply(lambda x: price_color(x, seuil_bas, seuil_haut))

    polys = []
    for row in df.itertuples():
        polys.append(_make_building_polygon(row.lon, row.lat, getattr(row, "type_local", "Appartement"), row.Index))
    df["building_polygon"] = polys

    # DPE subset
    dpe = df[df["dpe_classe"].notna()].copy()
    dpe = dpe.rename(columns={"dpe_classe": "etiquette_dpe", "ges_classe": "etiquette_ges",
                               "surface_m2": "surface_habitable_logement", "type_local": "type_batiment"})
    dpe["color_dpe"] = dpe["etiquette_dpe"].map(DPE_COLORS)
    dpe["dpe_score"] = dpe["etiquette_dpe"].map({"A":7,"B":6,"C":5,"D":4,"E":3,"F":2,"G":1})
    dpe["conso_5_usages_ep"] = 8 - dpe["dpe_score"]
    dpe = dpe.dropna(subset=["color_dpe"])
    dpe["surface_fmt"] = dpe["surface_habitable_logement"].apply(lambda x: f"{x:.0f} m²" if pd.notna(x) else "N/A")
    dpe["adresse_fmt"] = city

    return df, dpe, transport, seuil_bas, seuil_haut

# ---------------------------------------------------------------------------
# 5. SIDEBAR
# ---------------------------------------------------------------------------
st.sidebar.markdown("### ⚙️ Administration")
if st.sidebar.button("Mise à jour des données", width="stretch", type="primary"):
    st.switch_page("pages/selection_departements.py")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Localisation")

available_depts = get_depts(db_mtime)
dept_options = [f"{d} – {DEPT_NAMES.get(d, d)}" for d in available_depts]
dept_to_code = {f"{d} – {DEPT_NAMES.get(d, d)}": d for d in available_depts}

default_idx = next((i for i, d in enumerate(available_depts) if d == "44"), 0)
selected_dept_label = st.sidebar.selectbox("Département", dept_options, index=default_idx)
selected_dept = dept_to_code[selected_dept_label]

cities = get_cities(selected_dept, db_mtime)
default_city_idx = next((i for i, c in enumerate(cities) if c == "Nantes"), 0) if cities else 0
selected_city = st.sidebar.selectbox("Commune", cities, index=default_city_idx) if cities else None

if not selected_city:
    st.warning("Aucune commune trouvée pour ce département.")
    st.stop()

# Chargement
df_dvf, df_dpe, df_transport, seuil_bas, seuil_haut = load_city_data(selected_dept, selected_city, db_mtime)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtres")

col_p1, col_p2 = st.sidebar.columns(2)
prix_min = col_p1.number_input("Prix min (€)", 10_000, 5_000_000, 50_000, 10_000)
prix_max = col_p2.number_input("Prix max (€)", 10_000, 5_000_000, 800_000, 10_000)

col_s1, col_s2 = st.sidebar.columns(2)
surf_min = col_s1.number_input("Surface min", 10, 400, 15, 5)
surf_max = col_s2.number_input("Surface max", 10, 400, 250, 5)

max_points = st.sidebar.slider("Points sur la carte", 10, 500, 150, 10)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 Apparence")

if st.sidebar.button("Mode Sombre" if not is_dark else "Mode Clair", use_container_width=True):
    st.session_state.dark_mode = not st.session_state.dark_mode
    st.rerun()

map_style_name = st.sidebar.selectbox("Fond de carte", ["Coloré", "Clair", "Sombre"], index=0 if not is_dark else 2)
MAP_STYLES = {
    "Sombre": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    "Clair": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Coloré": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
}
map_style = MAP_STYLES[map_style_name]
show_transport = st.sidebar.checkbox("Afficher les transports", value=False)

chart_theme_name = st.sidebar.selectbox("Couleurs Graphiques", ["Bleu & Vert", "Doré & Bronze", "Rouge & Corail", "Violet & Rose"], index=0)
CHART_THEMES = {
    "Bleu & Vert": {"Appartement": "#3498db", "Maison": "#2ecc71"},
    "Doré & Bronze": {"Appartement": "#d4af37", "Maison": "#a05a2c"},
    "Rouge & Corail": {"Appartement": "#e74c3c", "Maison": "#e67e22"},
    "Violet & Rose": {"Appartement": "#9b59b6", "Maison": "#e84393"}
}
chart_theme = CHART_THEMES[chart_theme_name]
df_dvf["color_type"] = df_dvf["type_local"].map({"Maison": chart_theme["Maison"], "Appartement": chart_theme["Appartement"]})

# ---------------------------------------------------------------------------
# 6. FILTRAGE
# ---------------------------------------------------------------------------
df_f = df_dvf[
    df_dvf["valeur_fonciere"].between(prix_min, prix_max)
    & df_dvf["surface_m2"].between(surf_min, surf_max)
]
df_f = df_f.head(max_points)

dpe_f = df_dpe[
    df_dpe["surface_habitable_logement"].between(surf_min, surf_max)
] if len(df_dpe) > 0 else df_dpe

nb_dvf = len(df_f)
nb_dpe = len(dpe_f)

if nb_dvf > 0:
    c_lat, c_lon = df_f["lat"].mean(), df_f["lon"].mean()
    lat_r = df_f["lat"].max() - df_f["lat"].min()
    zoom = 14 if lat_r < 0.03 else 13 if lat_r < 0.08 else 12 if lat_r < 0.2 else 10
else:
    c_lat, c_lon, zoom = 47.2184, -1.5536, 12

# ---------------------------------------------------------------------------
# 7. HEADER METRICS
# ---------------------------------------------------------------------------
prix_med = df_f["valeur_fonciere"].median() if nb_dvf > 0 else 0
pm2_med = df_f["prix_m2"].median() if nb_dvf > 0 else 0
surf_med = df_f["surface_m2"].median() if nb_dvf > 0 else 0

st.markdown(f"""
<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;'>
    <div style='font-size:22px;font-weight:900;color:{_TEXT_PRIMARY};'>🏡 {selected_city}
        <span style='font-size:13px;font-weight:500;color:{_TEXT_SECONDARY};margin-left:8px;'>{DEPT_NAMES.get(selected_dept, selected_dept)} ({selected_dept})</span>
    </div>
    <div style='font-size:12px;color:{_TEXT_MUTED};'>Observatoire Foncier · SAE-601</div>
</div>
<div class='metric-row'>
    <div class='metric-card'><div class='val'>{nb_dvf:,}</div><div class='lbl'>Transactions</div></div>
    <div class='metric-card'><div class='val'>{prix_med:,.0f} €</div><div class='lbl'>Prix médian</div></div>
    <div class='metric-card'><div class='val'>{pm2_med:,.0f} €/m²</div><div class='lbl'>Prix/m² médian</div></div>
    <div class='metric-card'><div class='val'>{surf_med:.0f} m²</div><div class='lbl'>Surface médiane</div></div>
    <div class='metric-card'><div class='val'>{nb_dpe}</div><div class='lbl'>Diagnostics DPE</div></div>
</div>
""".replace(",", " "), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 8. ONGLETS PRINCIPAUX
# ---------------------------------------------------------------------------
tab_map, tab_dpe, tab_stats, tab_data, tab_analyse = st.tabs(["🗺️ Carte des Transactions", "📊 Analyse DPE", "📈 Statistiques", "📋 Données", "🔍 Analyse & Estimation"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 : CARTE
# ═══════════════════════════════════════════════════════════════════════════
with tab_map:
    col_list, col_carte = st.columns([2, 3], gap="medium")

    with col_list:
        tri = st.selectbox("Tri", ["Prix ↓", "Prix ↑", "Prix/m² ↓", "Prix/m² ↑", "Surface ↓", "Surface ↑"], index=0, label_visibility="collapsed")
        tri_map = {"Prix ↓": ("valeur_fonciere", False), "Prix ↑": ("valeur_fonciere", True),
                   "Prix/m² ↓": ("prix_m2", False), "Prix/m² ↑": ("prix_m2", True),
                   "Surface ↓": ("surface_m2", False), "Surface ↑": ("surface_m2", True)}
        sc, sa = tri_map[tri]
        df_sorted = df_f.sort_values(sc, ascending=sa).head(60)

        parts = []
        for row in df_sorted.itertuples():
            tl = getattr(row, "type_local", "")
            badge = "badge-maison" if tl == "Maison" else "badge-appart"
            val = f"{row.valeur_fonciere:,.0f} €".replace(",", " ") if pd.notna(row.valeur_fonciere) else "N/A"
            pm2 = f"{row.prix_m2:,.0f} €/m²".replace(",", " ") if pd.notna(row.prix_m2) else ""
            sf = f"{row.surface_m2:.0f} m²" if pd.notna(row.surface_m2) else ""
            pc = f"{int(row.nb_pieces)} p." if pd.notna(row.nb_pieces) and row.nb_pieces > 0 else ""
            det = " · ".join([s for s in [sf, pc] if s])
            dm = getattr(row, "date_mutation", "")
            parts.append(
                f"<div class='prop-card'><p class='prop-price'>{val}</p>"
                f"<p class='prop-price-m2'>{pm2}</p>"
                f"<p class='prop-type'><span class='prop-badge {badge}'>{tl}</span> {tl}</p>"
                f"<p class='prop-details'>{det}</p>"
                f"<p class='prop-date'>Vente du {dm}</p></div>"
            )
        st.markdown("<div class='property-list'>" + "".join(parts) + "</div>", unsafe_allow_html=True)

    with col_carte:
        VS = pdk.ViewState(latitude=c_lat, longitude=c_lon, zoom=zoom, pitch=0)

        layer_markers = pdk.Layer(
            "ScatterplotLayer", data=df_f, get_position="[lon, lat]",
            get_radius=40, radius_min_pixels=5, radius_max_pixels=16,
            get_fill_color="color_prix", get_line_color=[255,255,255,200],
            line_width_min_pixels=1, pickable=True, auto_highlight=True,
        )
        layer_text = pdk.Layer(
            "TextLayer", data=df_f, get_position="[lon, lat]",
            get_text="price_label", get_size=11, get_color=[30,30,30,220] if not is_dark else [220,220,220,220],
            get_alignment_baseline="'bottom'", get_pixel_offset="[0, -14]",
            font_weight=700, pickable=False,
        )
        transport_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_transport if show_transport else pd.DataFrame(),
            get_position="[lon, lat]", get_radius=80,
            radius_min_pixels=4, radius_max_pixels=14,
            get_fill_color=[52, 152, 219, 200], pickable=True,
        )

        tooltip = {
            "html": (
                "<div style='font-family:Inter,sans-serif;padding:10px 14px;background:#fff;"
                "border-radius:8px;color:#1a1a2e;box-shadow:0 4px 16px rgba(0,0,0,.12);"
                "max-width:240px;border:1px solid #e0e0e0;'>"
                "<div style='font-size:17px;font-weight:900;'>{valeur_fmt}</div>"
                "<div style='font-size:11px;color:#888;margin-bottom:4px;'>{prix_m2_fmt}</div>"
                "<hr style='border:0;height:1px;background:#eee;margin:4px 0;'>"
                "<div style='font-size:13px;font-weight:700;'>{type_local}</div>"
                "<div style='font-size:12px;color:#666;'>{surface_m2} m² · {nb_pieces} pièces</div>"
                "<div style='font-size:10px;color:#aaa;margin-top:3px;'>Vente du {date_mutation}</div>"
                "</div>"
            ),
            "style": {"backgroundColor": "transparent", "border": "none"},
        }

        st.pydeck_chart(pdk.Deck(
            map_style=map_style, initial_view_state=VS,
            layers=[layer_markers, layer_text, transport_layer],
            tooltip=tooltip,
        ), width="stretch")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 : DPE
# ═══════════════════════════════════════════════════════════════════════════
with tab_dpe:
    if nb_dpe == 0:
        st.info("Aucun diagnostic DPE disponible pour cette commune.")
    else:
        VS_DPE = pdk.ViewState(latitude=c_lat, longitude=c_lon, zoom=zoom, pitch=0)
        col_dpe1, col_dpe2 = st.columns([1, 2], gap="medium")

        with col_dpe1:
            dpe_counts = dpe_f["etiquette_dpe"].value_counts().reindex(["A","B","C","D","E","F","G"]).fillna(0)
            hex_colors = {"A":"#27ae60","B":"#2ecc71","C":"#a4c400","D":"#f1c40f","E":"#e67e22","F":"#d35400","G":"#c0392b"}
            fig_dpe = go.Figure(go.Bar(
                x=dpe_counts.index, y=dpe_counts.values,
                marker_color=[hex_colors[k] for k in dpe_counts.index],
                text=dpe_counts.values.astype(int), textposition="auto",
            ))
            fig_dpe.update_layout(
                title=dict(text=f"Répartition DPE", font=dict(size=14, color=_TEXT_PRIMARY)),
                margin=dict(l=30, r=10, t=40, b=30), height=350,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickfont=dict(color=_CHART_TEXT)),
                yaxis=dict(showgrid=True, gridcolor=_CHART_GRID, tickfont=dict(color=_CHART_TEXT)),
            )
            st.plotly_chart(fig_dpe, width="stretch")

        with col_dpe2:
            layer_dpe_heat = pdk.Layer(
                "HeatmapLayer", data=dpe_f.dropna(subset=["dpe_score"]),
                get_position="[lon, lat]", get_weight="dpe_score",
                radiusPixels=70, intensity=1.0, threshold=0.05, opacity=0.5,
                color_range=[[192,57,43],[230,126,34],[241,196,15],[164,196,0],[39,174,96]],
            )
            layer_dpe_dots = pdk.Layer(
                "ScatterplotLayer", data=dpe_f,
                get_position="[lon, lat]", get_radius=8,
                radius_min_pixels=2, radius_max_pixels=10,
                get_fill_color="color_dpe", pickable=True, opacity=0.9,
            )
            st.pydeck_chart(pdk.Deck(
                map_style=map_style, initial_view_state=VS_DPE,
                layers=[layer_dpe_heat, layer_dpe_dots],
            ), width="stretch")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 : STATS
# ═══════════════════════════════════════════════════════════════════════════
with tab_stats:
    if nb_dvf == 0:
        st.info("Aucune donnée disponible pour les statistiques.")
    else:
        col_s1, col_s2 = st.columns(2, gap="large")

        with col_s1:
            pm2_data = df_f["prix_m2"].dropna()
            if len(pm2_data) > 0:
                fig_hist = go.Figure(go.Histogram(
                    x=pm2_data, nbinsx=30,
                    marker_color=chart_theme["Appartement"], marker_line_width=1,
                ))
                fig_hist.update_layout(
                    title=dict(text="Distribution des prix au m²", font=dict(size=14, color=_TEXT_PRIMARY)),
                    margin=dict(l=40, r=10, t=40, b=30), height=320,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(title="€/m²", showgrid=False, tickfont=dict(color=_CHART_TEXT)),
                    yaxis=dict(title="Nb transactions", showgrid=True, gridcolor=_CHART_GRID, tickfont=dict(color=_CHART_TEXT)),
                )
                st.plotly_chart(fig_hist, width="stretch")

        with col_s2:
            type_counts = df_f["type_local"].value_counts()
            if len(type_counts) > 0:
                fig_type = go.Figure(go.Pie(
                    labels=type_counts.index, values=type_counts.values,
                    marker_colors=[chart_theme.get(t, "#9b59b6") for t in type_counts.index],
                    hole=0.45, textinfo="label+percent",
                    textfont=dict(size=13, color="#1e293b"),
                ))
                fig_type.update_layout(
                    title=dict(text="Répartition par type de bien", font=dict(size=14, color=_TEXT_PRIMARY)),
                    margin=dict(l=10, r=10, t=40, b=10), height=320,
                    paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                )
                st.plotly_chart(fig_type, width="stretch")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 : DATA
# ═══════════════════════════════════════════════════════════════════════════
with tab_data:
    tab_d1, tab_d2 = st.tabs(["Transactions DVF", "Diagnostics DPE"])
    with tab_d1:
        st.dataframe(df_f[["valeur_fmt", "type_local", "surface_m2", "nb_pieces", "prix_m2_fmt", "date_mutation", "adresse_normalisee"]].head(300), width="stretch", hide_index=True)
    with tab_d2:
        if nb_dpe > 0:
            st.dataframe(dpe_f[["etiquette_dpe", "surface_fmt", "type_batiment"]].head(300), width="stretch", hide_index=True)
        else:
            st.info("Aucun DPE")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 : ANALYSE & ESTIMATION (SIMULATEUR + FICHE ADRESSE)
# ═══════════════════════════════════════════════════════════════════════════
with tab_analyse:
    tab_sim, tab_addr = st.tabs(["💡 Simulateur Manuel", "📍 Fiche Adresse Détaillée"])
    
    # --- SOUS-ONGLET 1 : Simulateur ---
    with tab_sim:
        col_form, col_res = st.columns([1, 2], gap="large")
        with col_form:
            st.markdown("<div class='chart-card' style='margin-bottom:0;'>", unsafe_allow_html=True)
            st.markdown(f"<p class='chart-title'>Caractéristiques du bien</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='chart-subtitle'>Remplis les informations pour comparer au marché local.</p><br>", unsafe_allow_html=True)
            sim_prix = st.number_input("Prix de vente estimé (€)*", min_value=10000, max_value=10000000, value=250000, step=10000)
            sim_type = st.selectbox("Type de bien", ["Appartement", "Maison", "Indifférent"], index=0)
            col_f1, col_f2 = st.columns(2)
            sim_surf = col_f1.number_input("Surface (m²)", min_value=10, max_value=500, value=60)
            sim_surf_tol = col_f2.number_input("Tolérance surface (± %)", min_value=0, max_value=50, value=15)
            col_f3, col_f4 = st.columns(2)
            sim_pieces = col_f3.number_input("Nb pièces", min_value=1, max_value=20, value=3)
            sim_pieces_tol = col_f4.number_input("Tolérance pièces (±)", min_value=0, max_value=5, value=1)
            sim_mot_cle = st.text_input("Mot-clé adresse (Optionnel)", "")
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_res:
            df_sim = df_dvf.copy()
            if sim_type != "Indifférent": df_sim = df_sim[df_sim["type_local"] == sim_type]
            df_sim = df_sim[df_sim["surface_m2"].between(sim_surf * (1 - sim_surf_tol / 100.0), sim_surf * (1 + sim_surf_tol / 100.0))]
            df_sim = df_sim[df_sim["nb_pieces"].between(sim_pieces - sim_pieces_tol, sim_pieces + sim_pieces_tol)]
            if sim_mot_cle.strip(): df_sim = df_sim[df_sim["adresse_normalisee"].str.contains(sim_mot_cle, case=False, na=False)]
            
            nb_sim = len(df_sim)
            if nb_sim < 5:
                st.warning(f"⚠️ Échantillon trop faible ({nb_sim} ventes). Élargis tes critères.")
            else:
                med_sim_pm2 = df_sim["prix_m2"].median()
                sim_pm2 = sim_prix / sim_surf if sim_surf > 0 else 0
                diff_pct = ((sim_pm2 - med_sim_pm2) / med_sim_pm2) * 100 if med_sim_pm2 > 0 else 0
                
                if diff_pct > 5:
                    scol, stxt = "#e74c3c", f"Ton estimation est **{diff_pct:.1f}% plus élevée** que la médiane ({med_sim_pm2:,.0f} €/m²)."
                elif diff_pct < -5:
                    scol, stxt = "#2ecc71", f"Ton estimation est **{abs(diff_pct):.1f}% moins élevée** que la médiane ({med_sim_pm2:,.0f} €/m²)."
                else:
                    scol, stxt = "#f1c40f", f"Ton estimation est **parfaitement alignée** avec la médiane ({med_sim_pm2:,.0f} €/m²)."
                
                st.markdown(f"""<div class='chart-card' style='border-left-color: {scol}; padding:15px;'><p class='chart-title' style='color:{scol};'>Analyse</p><p class='chart-subtitle'>{stxt}</p><p style='font-size:11px;color:{_TEXT_MUTED};'>Basé sur {nb_sim} transactions.</p></div>""", unsafe_allow_html=True)
                
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta", value=sim_pm2,
                    delta={'reference': med_sim_pm2, 'increasing': {'color': "#e74c3c"}, 'decreasing': {'color': "#2ecc71"}},
                    gauge={'axis': {'range': [0, max(sim_pm2, med_sim_pm2)*1.5]}, 'bar': {'color': scol}, 'steps': [{'range':[0, med_sim_pm2*0.95], 'color':"rgba(46,204,113,0.2)"}, {'range':[med_sim_pm2*0.95, med_sim_pm2*1.05], 'color':"rgba(241,196,15,0.2)"}, {'range':[med_sim_pm2*1.05, max(sim_pm2, med_sim_pm2)*1.5], 'color':"rgba(231,76,60,0.2)"}], 'threshold': {'line': {'color': "black", 'width': 3}, 'value': med_sim_pm2}}
                ))
                fig_gauge.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_gauge, width="stretch")
    
    # --- SOUS-ONGLET 2 : Fiche Adresse ---
    with tab_addr:
        addresses = sorted(df_dvf["adresse_normalisee"].dropna().unique().tolist())
        selected_addr = st.selectbox("Rechercher une adresse exacte :", [""] + addresses, index=0)
        
        if selected_addr != "":
            rows_dvf = df_dvf[df_dvf["adresse_normalisee"] == selected_addr]
            lat = rows_dvf.iloc[0]["lat"] if not rows_dvf.empty else 47.2184
            lon = rows_dvf.iloc[0]["lon"] if not rows_dvf.empty else -1.5536
            
            # 1. Calculs des voisins et médiane
            df_others = df_dvf[df_dvf["adresse_normalisee"] != selected_addr].copy()
            df_others["dist_m"] = np.sqrt(((df_others["lat"] - lat)*111.32)**2 + ((df_others["lon"] - lon)*80.0)**2) * 1000.0
            closest_15 = df_others.sort_values("dist_m").head(15)
            median_local_prix_m2 = closest_15["prix_m2"].median() if not closest_15.empty else df_dvf["prix_m2"].median()
            median_nantes_prix_m2 = df_dvf["prix_m2"].median()
            
            b_type = rows_dvf.iloc[0]["type_local"] if not rows_dvf.empty else "Appartement"
            building_prix_m2 = rows_dvf.iloc[0]["prix_m2"] if not rows_dvf.empty else median_local_prix_m2
            
            # 2. DPE (le plus proche si pas exact)
            distances_dpe = np.sqrt(((df_dpe["lat"] - lat)*111.32)**2 + ((df_dpe["lon"] - lon)*80.0)**2) * 1000.0
            closest_dpe_idx = distances_dpe.idxmin() if not distances_dpe.empty else None
            dpe_record = df_dpe.loc[closest_dpe_idx] if closest_dpe_idx is not None else {}
            dpe_score = dpe_record.get("dpe_score", 4)
            points_dpe = ((dpe_score - 1) / 6.0) * 50.0
            
            # 3. Transport (le plus proche)
            if not df_transport.empty:
                distances_trans = np.sqrt(((df_transport["lat"] - lat)*111.32)**2 + ((df_transport["lon"] - lon)*80.0)**2) * 1000.0
                min_dist_trans = distances_trans.min()
                points_trans = 50.0 if min_dist_trans <= 100.0 else max(0.0, 50.0 * (1.0 - (min_dist_trans - 100.0) / 900.0))
            else:
                points_trans = 0.0
                min_dist_trans = 9999
            
            eco_score = float(np.clip(points_dpe + points_trans, 0.0, 100.0))
            verdict_color = "#009E5F" if eco_score >= 80 else "#BACF11" if eco_score >= 60 else "#FBBD08" if eco_score >= 40 else "#F47D22"
            
            # Layout compact
            col_a1, col_a2, col_a3 = st.columns([1.5, 1, 1], gap="medium")
            
            with col_a1:
                # Avis d'équité
                diff_ratio = (building_prix_m2 - median_local_prix_m2) / median_local_prix_m2
                if diff_ratio <= -0.10:
                    v_txt, v_col = "Excellente opportunité", "#2ecc71"
                elif diff_ratio <= 0.05:
                    v_txt, v_col = "Prix cohérent", "#3498db"
                else:
                    v_txt, v_col = "Prix élevé", "#e74c3c"
                    
                st.markdown(f"<div class='chart-card' style='border-left-color: {v_col}; height:100%;'>"
                            f"<p class='chart-title' style='color:{v_col};'>{v_txt}</p>"
                            f"<p class='chart-subtitle'>Ce bien est à <b>{building_prix_m2:,.0f} €/m²</b>, soit <b>{diff_ratio*100:+.1f}%</b> par rapport à la médiane de ses 15 plus proches voisins (<b>{median_local_prix_m2:,.0f} €/m²</b>).</p>"
                            f"</div>".replace(",", " "), unsafe_allow_html=True)
                            
            with col_a2:
                # Eco Score
                fig_eco = go.Figure(go.Indicator(
                    mode="gauge+number", value=eco_score,
                    title={'text': "Éco-Attractivité", 'font': {'size': 13, 'color': _TEXT_PRIMARY}},
                    number={'font': {'size': 20, 'color': verdict_color}, 'suffix': "/100"},
                    gauge={'axis': {'range': [0, 100]}, 'bar': {'color': verdict_color}, 'steps': [{'range':[0,40], 'color':"rgba(244,125,34,0.15)"}, {'range':[40,60], 'color':"rgba(251,189,8,0.15)"}, {'range':[60,80], 'color':"rgba(186,207,17,0.15)"}, {'range':[80,100], 'color':"rgba(0,158,95,0.15)"}]}
                ))
                fig_eco.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=140, paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_eco, width="stretch")
                
            with col_a3:
                # Simulateur mini
                valeur = float(rows_dvf.iloc[0]["valeur_fonciere"]) if not rows_dvf.empty else 200000.0
                mensualite = (valeur * 0.85) * ((0.037/12)*(1+0.037/12)**240) / ((1+0.037/12)**240 - 1)
                st.markdown(f"<div class='chart-card' style='height:100%; text-align:center; padding-top:15px;'>"
                            f"<p style='font-size:11px;color:{_TEXT_SECONDARY};margin:0;text-transform:uppercase;'>Mensualité estimée</p>"
                            f"<p style='font-size:24px;font-weight:900;color:#d4af37;margin:5px 0;'>{mensualite:,.0f} € / mois</p>"
                            f"<p style='font-size:10px;color:{_TEXT_MUTED};margin:0;'>Sur 20 ans, taux 3.7%, 15% apport</p>"
                            f"</div>".replace(",", " "), unsafe_allow_html=True)
            
            # Ligne du bas : Radar + Tendance
            col_b1, col_b2 = st.columns([1, 2], gap="large")
            with col_b1:
                score_budget = float(np.clip(100.0 * (median_nantes_prix_m2 / building_prix_m2), 10.0, 100.0))
                score_espace = 70.0 # fixe arbitraire pour la démo sans surface précise du quartier
                
                fig_radar = go.Figure(go.Scatterpolar(
                    r=[score_budget, points_dpe*2, points_trans*2, score_espace, score_budget],
                    theta=["Budget", "Confort Énergie", "Accès Transport", "Espace", "Budget"],
                    fill='toself', fillcolor="rgba(212, 175, 55, 0.25)", line=dict(color="#d4af37")
                ))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor=_CHART_GRID, tickfont=dict(size=8, color=_CHART_TEXT)), angularaxis=dict(gridcolor=_CHART_GRID, tickfont=dict(color=_TEXT_PRIMARY, size=10)), bgcolor="rgba(0,0,0,0)"), margin=dict(l=30, r=30, t=20, b=20), height=200, paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_radar, width="stretch")
                
            with col_b2:
                # Historique local vs global (Mockup des mois)
                mois = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]
                prix_glob = [median_nantes_prix_m2 * (1 + random.uniform(-0.02, 0.02)) for _ in range(12)]
                prix_loc = [median_local_prix_m2 * (1 + random.uniform(-0.03, 0.03)) for _ in range(12)]
                
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(x=mois, y=prix_glob, mode='lines', name='Moyenne Ville', line=dict(color='#94a3b8', width=2, dash='dash')))
                fig_trend.add_trace(go.Scatter(x=mois, y=prix_loc, mode='lines+markers', name='Micro-Quartier', line=dict(color='#d4af37', width=3)))
                fig_trend.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=200, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(showgrid=False, tickfont=dict(color=_CHART_TEXT)), yaxis=dict(gridcolor=_CHART_GRID, tickfont=dict(color=_CHART_TEXT)), legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1.0, font=dict(color=_TEXT_PRIMARY, size=10)))
                st.plotly_chart(fig_trend, width="stretch")