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
# 1. CONFIGURATION
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Observatoire Foncier",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "sae601_nantes.duckdb"

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
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* No scroll */
html, body, .stApp { overflow: hidden !important; font-family: 'Inter', sans-serif !important; }
.stApp { background-color: #ffffff !important; }
.block-container { padding-top: 1rem !important; padding-bottom: 0 !important; max-width: 98% !important; }
header[data-testid="stHeader"] { display: none !important; }

/* Texte noir */
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp p,.stApp li,.stApp span:not(.prop-badge) { color: #111827 !important; }
button[data-baseweb="tab"] p, button[data-baseweb="tab"] span { color: #111827 !important; }

/* Sidebar */
[data-testid="stSidebar"] { background-color: #f8fafc !important; border-right: 1px solid #e2e8f0; }
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label,[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] h5,[data-testid="stSidebar"] span { color: #000000 !important; }
[data-testid="stSidebar"] h3 {
    background: #fff; color: #1e293b !important; padding: 8px 12px !important;
    border-radius: 8px !important; box-shadow: 0 2px 8px rgba(0,0,0,.05) !important;
    font-size: 12px !important; font-weight: 700 !important; text-transform: uppercase !important;
    letter-spacing: .5px !important; border-left: 3px solid #d4af37 !important;
    margin-top: 14px !important; margin-bottom: 8px !important;
}

/* Tags dorés */
div[data-baseweb="tag"],span[data-baseweb="tag"] { background-color: #d4af37 !important; color: #000 !important; border-radius: 4px !important; }
div[data-baseweb="tag"] *,span[data-baseweb="tag"] * { color: #000 !important; fill: #000 !important; }

/* Bouton principal */
button[data-testid="baseButton-primary"] { background-color: #1e293b !important; color: #fff !important; border: none !important; }
button[data-testid="baseButton-primary"]:hover { background-color: #d4af37 !important; color: #000 !important; }

/* Property cards */
.property-list { max-height: 68vh; overflow-y: auto; padding-right: 6px; }
.property-list::-webkit-scrollbar { width: 5px; }
.property-list::-webkit-scrollbar-thumb { background: #ccc; border-radius: 3px; }
.prop-card {
    background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 14px;
    margin-bottom: 10px; transition: all .2s ease; font-family: 'Inter', sans-serif;
}
.prop-card:hover { box-shadow: 0 6px 18px rgba(0,0,0,.06); border-color: #d4af37; transform: translateY(-1px); }
.prop-price { font-size: 18px; font-weight: 800; color: #1a1a2e; margin: 0; }
.prop-price-m2 { font-size: 12px; font-weight: 600; color: #888; margin: 0 0 4px 0; }
.prop-type { font-size: 13px; font-weight: 700; color: #333; margin: 3px 0 1px 0; }
.prop-details { font-size: 12px; color: #666; margin: 1px 0; }
.prop-date { font-size: 10px; color: #aaa; margin-top: 3px; }
.prop-badge { display: inline-block; padding: 1px 7px; border-radius: 3px; font-size: 10px; font-weight: 700; color: #fff; margin-right: 5px; }
.badge-maison { background: #e67e22; } .badge-appart { background: #3498db; }

/* Metric cards */
.metric-row { display: flex; gap: 12px; margin-bottom: 10px; }
.metric-card {
    flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 12px 16px; text-align: center;
}
.metric-card .val { font-size: 22px; font-weight: 900; color: #1e293b; }
.metric-card .lbl { font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: .5px; }

/* Chart card */
.chart-card {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 14px 18px; box-shadow: 0 2px 10px rgba(0,0,0,.03);
    border-left: 4px solid #d4af37; margin-bottom: 12px;
}
.chart-title { font-size: 16px; font-weight: 800; color: #0f172a; margin: 0 0 4px 0; }
.chart-subtitle { font-size: 12px; color: #64748b; margin: 0; line-height: 1.3; }
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
    df["color_type"] = df["type_local"].map({"Maison": [230, 126, 34, 200], "Appartement": [52, 152, 219, 200]})

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
if st.sidebar.button("Mise à jour des départements", width="stretch", type="primary"):
    st.switch_page("pages/selection_departements.py")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Localisation")

available_depts = get_depts(db_mtime)
dept_options = [f"{d} – {DEPT_NAMES.get(d, d)}" for d in available_depts]
dept_to_code = {f"{d} – {DEPT_NAMES.get(d, d)}": d for d in available_depts}

# Défaut : 44 si disponible
default_idx = next((i for i, d in enumerate(available_depts) if d == "44"), 0)
selected_dept_label = st.sidebar.selectbox("Département", dept_options, index=default_idx)
selected_dept = dept_to_code[selected_dept_label]

cities = get_cities(selected_dept, db_mtime)
default_city_idx = next((i for i, c in enumerate(cities) if c == "Nantes"), 0) if cities else 0
selected_city = st.sidebar.selectbox("Commune", cities, index=default_city_idx) if cities else None

if not selected_city:
    st.warning("Aucune commune trouvée pour ce département.")
    st.stop()

# Chargement des données
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
st.sidebar.markdown("### 🎨 Affichage")
map_style_name = st.sidebar.selectbox("Fond de carte", ["Coloré", "Clair", "Sombre"], index=0)
MAP_STYLES = {
    "Sombre": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    "Clair": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Coloré": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
}
map_style = MAP_STYLES[map_style_name]
show_transport = st.sidebar.checkbox("Afficher les stations de transport", value=False)

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

# Centre de la carte
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
    <div style='font-size:22px;font-weight:900;color:#1e293b;'>🏡 {selected_city}
        <span style='font-size:13px;font-weight:500;color:#64748b;margin-left:8px;'>{DEPT_NAMES.get(selected_dept, selected_dept)} ({selected_dept})</span>
    </div>
    <div style='font-size:12px;color:#94a3b8;'>Observatoire Foncier · SAE-601</div>
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
# TAB 1 : CARTE DES TRANSACTIONS
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
            get_text="price_label", get_size=11, get_color=[30,30,30,220],
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

        # Légende prix
        st.markdown(f"""
        <div style='display:flex;gap:16px;justify-content:center;font-size:12px;font-weight:700;margin-bottom:6px;font-family:Inter,sans-serif;color:#333;'>
            <div style='display:flex;align-items:center;gap:5px;'>
                <span style='width:10px;height:10px;background:rgb(140,140,140);border-radius:50%;display:inline-block;'></span>
                &lt; {seuil_bas:,.0f} €/m²
            </div>
            <div style='display:flex;align-items:center;gap:5px;'>
                <span style='width:10px;height:10px;background:rgb(230,190,10);border-radius:50%;display:inline-block;'></span>
                {seuil_bas:,.0f} – {seuil_haut:,.0f} €/m²
            </div>
            <div style='display:flex;align-items:center;gap:5px;'>
                <span style='width:10px;height:10px;background:rgb(220,53,69);border-radius:50%;display:inline-block;'></span>
                &gt; {seuil_haut:,.0f} €/m²
            </div>
        </div>
        """.replace(",", " "), unsafe_allow_html=True)

        st.pydeck_chart(pdk.Deck(
            map_style=map_style, initial_view_state=VS,
            layers=[layer_markers, layer_text, transport_layer],
            tooltip=tooltip,
        ), width="stretch")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 : ANALYSE DPE
# ═══════════════════════════════════════════════════════════════════════════
with tab_dpe:
    if nb_dpe == 0:
        st.info("Aucun diagnostic DPE disponible pour cette commune.")
    else:
        VS_DPE = pdk.ViewState(latitude=c_lat, longitude=c_lon, zoom=zoom, pitch=0)
        tooltip_dpe = {
            "html": (
                "<div style='font-family:Inter,sans-serif;padding:10px;background:rgba(15,20,30,.95);"
                "border-radius:8px;color:#fff;box-shadow:0 4px 20px rgba(0,0,0,.4);max-width:240px;'>"
                "<div style='font-size:10px;text-transform:uppercase;color:#7fa5c8;font-weight:700;'>DPE</div>"
                "<div style='font-size:13px;font-weight:800;color:#2ecc71;margin:4px 0;'>{adresse_fmt}</div>"
                "<div style='font-size:12px;'>Type : <b>{type_batiment}</b></div>"
                "<div style='font-size:12px;'>Surface : <b>{surface_fmt}</b></div>"
                "<div style='font-size:14px;font-weight:900;color:#f1c40f;margin-top:4px;'>DPE {etiquette_dpe}</div>"
                "</div>"
            ),
            "style": {"backgroundColor": "transparent", "border": "none"},
        }

        col_dpe1, col_dpe2 = st.columns([1, 2], gap="medium")

        with col_dpe1:
            # Répartition DPE
            dpe_counts = dpe_f["etiquette_dpe"].value_counts().reindex(["A","B","C","D","E","F","G"]).fillna(0)
            hex_colors = {"A":"#27ae60","B":"#2ecc71","C":"#a4c400","D":"#f1c40f","E":"#e67e22","F":"#d35400","G":"#c0392b"}
            fig_dpe = go.Figure(go.Bar(
                x=dpe_counts.index, y=dpe_counts.values,
                marker_color=[hex_colors[k] for k in dpe_counts.index],
                text=dpe_counts.values.astype(int), textposition="auto",
            ))
            fig_dpe.update_layout(
                title=dict(text=f"Répartition DPE – {selected_city}", font=dict(size=14, color="#1e293b")),
                margin=dict(l=30, r=10, t=40, b=30), height=350,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickfont=dict(color="#64748b")),
                yaxis=dict(showgrid=True, gridcolor="#e2e8f0", tickfont=dict(color="#64748b")),
            )
            st.plotly_chart(fig_dpe, width="stretch")

        with col_dpe2:
            # Carte DPE
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
                layers=[layer_dpe_heat, layer_dpe_dots], tooltip=tooltip_dpe,
            ), width="stretch")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 : STATISTIQUES
# ═══════════════════════════════════════════════════════════════════════════
with tab_stats:
    if nb_dvf == 0:
        st.info("Aucune donnée disponible pour les statistiques.")
    else:
        col_s1, col_s2 = st.columns(2, gap="large")

        with col_s1:
            # Distribution des prix/m²
            pm2_data = df_f["prix_m2"].dropna()
            if len(pm2_data) > 0:
                fig_hist = go.Figure(go.Histogram(
                    x=pm2_data, nbinsx=30,
                    marker_color="#3498db", marker_line_color="#2980b9", marker_line_width=1,
                ))
                fig_hist.update_layout(
                    title=dict(text="Distribution des prix au m²", font=dict(size=14, color="#1e293b")),
                    margin=dict(l=40, r=10, t=40, b=30), height=320,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(title="€/m²", showgrid=False, tickfont=dict(color="#64748b")),
                    yaxis=dict(title="Nb transactions", showgrid=True, gridcolor="#e2e8f0", tickfont=dict(color="#64748b")),
                )
                st.plotly_chart(fig_hist, width="stretch")

        with col_s2:
            # Répartition Maison / Appartement
            type_counts = df_f["type_local"].value_counts()
            if len(type_counts) > 0:
                fig_type = go.Figure(go.Pie(
                    labels=type_counts.index, values=type_counts.values,
                    marker_colors=["#3498db", "#e67e22", "#2ecc71", "#9b59b6"],
                    hole=0.45, textinfo="label+percent",
                    textfont=dict(size=13, color="#1e293b"),
                ))
                fig_type.update_layout(
                    title=dict(text="Répartition par type de bien", font=dict(size=14, color="#1e293b")),
                    margin=dict(l=10, r=10, t=40, b=10), height=320,
                    paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
                )
                st.plotly_chart(fig_type, width="stretch")

        col_s3, col_s4 = st.columns(2, gap="large")

        with col_s3:
            # Prix médian par type
            med_by_type = df_f.groupby("type_local")["prix_m2"].median().sort_values()
            if len(med_by_type) > 0:
                fig_med = go.Figure(go.Bar(
                    x=med_by_type.index, y=med_by_type.values,
                    marker_color=["#e67e22" if t == "Maison" else "#3498db" for t in med_by_type.index],
                    text=[f"{v:,.0f}".replace(",", " ") for v in med_by_type.values], textposition="auto",
                ))
                fig_med.update_layout(
                    title=dict(text="Prix médian/m² par type", font=dict(size=14, color="#1e293b")),
                    margin=dict(l=40, r=10, t=40, b=30), height=280,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, tickfont=dict(color="#64748b")),
                    yaxis=dict(showgrid=True, gridcolor="#e2e8f0", ticksuffix=" €/m²", tickfont=dict(color="#64748b")),
                )
                st.plotly_chart(fig_med, width="stretch")

        with col_s4:
            # Distribution nb pièces
            pieces_data = df_f["nb_pieces"].dropna()
            if len(pieces_data) > 0:
                pieces_counts = pieces_data.astype(int).clip(upper=6).value_counts().sort_index()
                labels = [f"{p} p." if p < 6 else "6+ p." for p in pieces_counts.index]
                fig_pcs = go.Figure(go.Bar(
                    x=labels, y=pieces_counts.values,
                    marker_color="#2ecc71",
                    text=pieces_counts.values, textposition="auto",
                ))
                fig_pcs.update_layout(
                    title=dict(text="Nombre de pièces", font=dict(size=14, color="#1e293b")),
                    margin=dict(l=40, r=10, t=40, b=30), height=280,
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(showgrid=False, tickfont=dict(color="#64748b")),
                    yaxis=dict(showgrid=True, gridcolor="#e2e8f0", tickfont=dict(color="#64748b")),
                )
                st.plotly_chart(fig_pcs, width="stretch")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 : DONNÉES BRUTES
# ═══════════════════════════════════════════════════════════════════════════
with tab_data:
    tab_d1, tab_d2 = st.tabs(["Transactions DVF", "Diagnostics DPE"])

    with tab_d1:
        cols_dvf = ["valeur_fmt", "type_local", "surface_m2", "nb_pieces", "prix_m2_fmt", "date_mutation"]
        available_cols = [c for c in cols_dvf if c in df_f.columns]
        st.dataframe(
            df_f[available_cols].rename(columns={
                "valeur_fmt": "Prix", "type_local": "Type", "surface_m2": "Surface (m²)",
                "nb_pieces": "Pièces", "prix_m2_fmt": "Prix/m²", "date_mutation": "Date",
            }).head(300),
            width="stretch", hide_index=True,
        )

    with tab_d2:
        if nb_dpe > 0:
            cols_dpe = ["adresse_fmt", "etiquette_dpe", "surface_fmt", "type_batiment"]
            available_cols_dpe = [c for c in cols_dpe if c in dpe_f.columns]
            st.dataframe(
                dpe_f[available_cols_dpe].rename(columns={
                    "adresse_fmt": "Commune", "etiquette_dpe": "DPE",
                    "surface_fmt": "Surface", "type_batiment": "Type",
                }).head(300),
                width="stretch", hide_index=True,
            )
        else:
            st.info("Aucun diagnostic DPE disponible.")

# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 : ANALYSE & ESTIMATION
# ═══════════════════════════════════════════════════════════════════════════
with tab_analyse:
    st.markdown("### Évalue ton bien immobilier")
    
    col_form, col_res = st.columns([1, 2], gap="large")
    
    with col_form:
        st.markdown("<div class='chart-card' style='margin-bottom:0;'>", unsafe_allow_html=True)
        st.markdown("<p class='chart-title'>Caractéristiques du bien</p>", unsafe_allow_html=True)
        st.markdown("<p class='chart-subtitle'>Remplis les informations pour comparer ton estimation au marché local.</p><br>", unsafe_allow_html=True)
        
        sim_prix = st.number_input("Prix de vente estimé (€)*", min_value=10000, max_value=10000000, value=250000, step=10000)
        sim_type = st.selectbox("Type de bien", ["Appartement", "Maison", "Indifférent"], index=0)
        
        col_f1, col_f2 = st.columns(2)
        sim_surf = col_f1.number_input("Surface (m²)", min_value=10, max_value=500, value=60)
        sim_surf_tol = col_f2.number_input("Tolérance surface (± %)", min_value=0, max_value=50, value=15)
        
        col_f3, col_f4 = st.columns(2)
        sim_pieces = col_f3.number_input("Nb pièces", min_value=1, max_value=20, value=3)
        sim_pieces_tol = col_f4.number_input("Tolérance pièces (±)", min_value=0, max_value=5, value=1)
        
        sim_mot_cle = st.text_input("Mot-clé adresse (Optionnel, ex: Zola, Doulon)", "")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_res:
        # Filtrage
        df_sim = df_dvf.copy()
        
        if sim_type != "Indifférent":
            df_sim = df_sim[df_sim["type_local"] == sim_type]
            
        surf_min_sim = sim_surf * (1 - sim_surf_tol / 100.0)
        surf_max_sim = sim_surf * (1 + sim_surf_tol / 100.0)
        df_sim = df_sim[df_sim["surface_m2"].between(surf_min_sim, surf_max_sim)]
        
        pieces_min = sim_pieces - sim_pieces_tol
        pieces_max = sim_pieces + sim_pieces_tol
        df_sim = df_sim[df_sim["nb_pieces"].between(pieces_min, pieces_max)]
        
        if sim_mot_cle.strip():
            df_sim = df_sim[df_sim["adresse_normalisee"].str.contains(sim_mot_cle, case=False, na=False)]
        
        nb_sim = len(df_sim)
        
        if nb_sim < 5:
            st.warning(f"⚠️ **Échantillon trop faible ({nb_sim} ventes).** Élargis tes critères de recherche (tolérance de surface, pièces, ou retire le mot-clé) pour obtenir une estimation fiable.")
        else:
            med_sim_pm2 = df_sim["prix_m2"].median()
            min_sim_pm2 = df_sim["prix_m2"].min()
            max_sim_pm2 = df_sim["prix_m2"].quantile(0.95) # Exclure les vrais extrêmes pour la jauge
            
            sim_pm2 = sim_prix / sim_surf if sim_surf > 0 else 0
            
            diff_pct = ((sim_pm2 - med_sim_pm2) / med_sim_pm2) * 100 if med_sim_pm2 > 0 else 0
            
            if diff_pct > 5:
                status_color = "#e74c3c" # Rouge (trop cher)
                status_text = f"Ton estimation est **{diff_pct:.1f}% plus élevée** que la médiane du marché ({med_sim_pm2:,.0f} €/m²) pour des biens similaires."
            elif diff_pct < -5:
                status_color = "#2ecc71" # Vert (bonne affaire)
                status_text = f"Ton estimation est **{abs(diff_pct):.1f}% moins élevée** que la médiane du marché ({med_sim_pm2:,.0f} €/m²) pour des biens similaires."
            else:
                status_color = "#f1c40f" # Jaune (dans la norme)
                status_text = f"Ton estimation est **parfaitement alignée** avec la médiane du marché ({med_sim_pm2:,.0f} €/m²) pour des biens similaires."
            
            st.markdown(f"""
            <div class='chart-card' style='border-left-color: {status_color};'>
                <p class='chart-title' style='color: {status_color};'>Résultat de l'analyse</p>
                <p class='chart-subtitle'>{status_text}</p>
                <p style='font-size: 13px; color: #64748b; margin-top: 5px;'>Basé sur <b>{nb_sim}</b> transactions historiques correspondant à tes critères.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Gauge chart Plotly
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = sim_pm2,
                title = {'text': "Prix au m² simulé (€/m²)", 'font': {'size': 14, 'color': '#1e293b'}},
                delta = {'reference': med_sim_pm2, 'increasing': {'color': "#e74c3c"}, 'decreasing': {'color': "#2ecc71"}},
                gauge = {
                    'axis': {'range': [max(0, min_sim_pm2 - 500), max_sim_pm2 + 1000], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': status_color},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, med_sim_pm2 * 0.95], 'color': "rgba(46, 204, 113, 0.2)"},
                        {'range': [med_sim_pm2 * 0.95, med_sim_pm2 * 1.05], 'color': "rgba(241, 196, 15, 0.2)"},
                        {'range': [med_sim_pm2 * 1.05, max_sim_pm2 + 1000], 'color': "rgba(231, 76, 60, 0.2)"}],
                    'threshold': {
                        'line': {'color': "black", 'width': 3},
                        'thickness': 0.75,
                        'value': med_sim_pm2}
                }
            ))
            
            fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_gauge, width="stretch")
            
            with st.expander("🗺️ Voir les biens similaires sur la carte"):
                # Carte pydeck des biens similaires
                c_lat_sim = df_sim["lat"].mean()
                c_lon_sim = df_sim["lon"].mean()
                VS_SIM = pdk.ViewState(latitude=c_lat_sim, longitude=c_lon_sim, zoom=13, pitch=0)
                
                layer_sim = pdk.Layer(
                    "ScatterplotLayer", data=df_sim, get_position="[lon, lat]",
                    get_radius=50, radius_min_pixels=5, radius_max_pixels=15,
                    get_fill_color=[52, 152, 219, 200], get_line_color=[255,255,255,200],
                    line_width_min_pixels=1, pickable=True, auto_highlight=True,
                )
                
                st.pydeck_chart(pdk.Deck(
                    map_style=map_style, initial_view_state=VS_SIM,
                    layers=[layer_sim],
                    tooltip={"text": "{adresse_normalisee}\n{valeur_fmt} | {surface_m2} m² | {prix_m2_fmt}"}
                ), width="stretch")