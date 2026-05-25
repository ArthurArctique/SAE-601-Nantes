import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from pyproj import Transformer
import math
import random

# ---------------------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Observatoire Foncier Nantes",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

# Palette de zones de prix (Cyberpunk / Synthwave)
PRICE_THRESHOLDS = [100_000, 200_000, 350_000, 550_000]
PRICE_COLORS = [
    [4, 217, 255, 200],    # Cyan (< 100k)
    [104, 123, 235, 200],  # Soft Blue (100-200k)
    [171, 52, 224, 200],   # Purple (200-350k)
    [224, 30, 132, 200],   # Magenta (350-550k)
    [255, 115, 0, 200],    # Orange (> 550k)
]

def price_color(val):
    for i, thresh in enumerate(PRICE_THRESHOLDS):
        if val < thresh:
            return PRICE_COLORS[i]
    return PRICE_COLORS[-1]


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
        "c:/projet_2026/data/dpe/dpe-logements-existants-44.csv",
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
        "c:/projet_2026/data/ban/adresses-44.csv",
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
        "c:/projet_2026/data/dvf/dvf-2025-dept44.csv",
        "r", encoding="utf-8", errors="replace",
    ) as f:
        f.readline()
        for line in f:
            parts = line.rstrip("\n").split(",")
            if len(parts) < 20 or parts[20].strip() != "109":
                continue
            if parts[9].strip() != "Vente":
                continue
            extra = len(parts) - 43
            type_local_idx = 36 + extra
            type_local = (
                parts[type_local_idx].strip() if type_local_idx < len(parts) else ""
            )
            if type_local not in ("Maison", "Appartement"):
                continue

            val_raw = parts[10].strip()
            surf_raw = (
                parts[38 + extra].strip() if (38 + extra) < len(parts) else ""
            )
            pieces_raw = (
                parts[39 + extra].strip() if (39 + extra) < len(parts) else ""
            )
            code_voie = parts[15].strip() if 15 < len(parts) else ""
            date_mut = parts[8].strip() if 8 < len(parts) else ""

            # Numéro de voie : essai position 11, puis 12 si vide/nul
            no_voie = parts[11].strip()
            if no_voie in ("00", "", "0"):
                no_voie = parts[12].strip() if 12 < len(parts) else ""

            try:
                valeur = float(val_raw)
            except ValueError:
                valeur = np.nan
            try:
                surface = float(surf_raw)
            except ValueError:
                surface = np.nan
            try:
                pieces = int(float(pieces_raw))
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
    merged["color_prix"] = merged["valeur_fonciere"].apply(price_color)

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
        "c:/projet_2026/data/transport/stations-44.csv",
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
dpe_choix = st.sidebar.multiselect(
    "Etiquette DPE :",
    options=["A", "B", "C", "D", "E", "F", "G"],
    default=["A", "B", "C", "D", "E"],
)

st.sidebar.markdown("### Surface habitable")
surf_min, surf_max = st.sidebar.slider(
    "Surface (m2) :", min_value=10, max_value=400, value=(20, 200), step=5
)

st.sidebar.markdown("### Type de batiment")
types_dispo = sorted(df_dpe["type_batiment"].dropna().unique().tolist())
type_batiment_choix = st.sidebar.multiselect(
    "Type :", options=types_dispo, default=types_dispo
)

st.sidebar.markdown("### Valeur fonciere DVF")
prix_min, prix_max = st.sidebar.slider(
    "Fourchette de prix (EUR) :",
    min_value=20_000, max_value=3_000_000,
    value=(80_000, 800_000), step=10_000, format="%d EUR",
)

st.sidebar.markdown("---")
st.sidebar.subheader("Style de carte")
map_style_name = st.sidebar.selectbox(
    "Fond de carte :",
    options=["Sombre", "Clair", "Coloré"],
    index=1,  # Par défaut "Clair" pour aller avec le thème clair
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

# ---------------------------------------------------------------------------
# 5. EN-TETE & KPI
# ---------------------------------------------------------------------------
st.title("Observatoire Foncier & Energetique – Nantes")
st.markdown(
    "Exploration des **données réelles** : DPE existants, transactions DVF 2025 "
    "géocodées via la BAN, et réseau de transport de Loire-Atlantique."
)

col1, col2, col3, col4, col5 = st.columns(5)
nb_dpe = len(df_dpe_f)
surf_med = df_dpe_f["surface_habitable_logement"].median()
dpe_mode_s = df_dpe_f["etiquette_dpe"].mode()
dpe_maj = dpe_mode_s.iloc[0] if not dpe_mode_s.empty else "N/A"
nb_dvf = len(df_dvf_f)
prix_med = df_dvf_f["valeur_fonciere"].median()

col1.metric("Logements DPE", f"{nb_dpe:,}".replace(",", " "))
col2.metric("Surface médiane", f"{surf_med:.0f} m2" if nb_dpe > 0 else "N/A")
col3.metric("DPE majoritaire", dpe_maj)
col4.metric("Ventes DVF", f"{nb_dvf:,}".replace(",", " "))
col5.metric(
    "Prix médian",
    f"{prix_med:,.0f} EUR".replace(",", " ") if nb_dvf > 0 else "N/A",
)

st.divider()

# ---------------------------------------------------------------------------
# 6. CARTOGRAPHIE PYDECK
# ---------------------------------------------------------------------------
st.subheader("Cartographie interactive (PyDeck)")

VIEW_STATE_3D = pdk.ViewState(
    latitude=47.2184, longitude=-1.5536, zoom=12.2, pitch=50, bearing=10
)
VIEW_STATE_2D = pdk.ViewState(
    latitude=47.2184, longitude=-1.5536, zoom=12.5, pitch=0, bearing=0
)

# --- Tooltip DPE ---
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

# --- Tooltip DVF prix ---
tooltip_dvf_prix = {
    "html": (
        "<div style='font-family:Inter,sans-serif;padding:12px;"
        "background:rgba(10,15,25,0.97);border-radius:10px;"
        "border:1px solid rgba(255,255,255,0.15);color:#fff;"
        "box-shadow:0 6px 30px rgba(0,0,0,.6);max-width:270px;'>"
        "<div style='font-size:10px;text-transform:uppercase;color:#7fa5c8;"
        "margin-bottom:6px;font-weight:700;'>Transaction DVF 2025</div>"
        "<div style='font-size:22px;font-weight:900;color:#2ecc71;margin-bottom:4px;'>"
        "{valeur_fmt}</div>"
        "<div style='font-size:13px;color:#f1c40f;font-weight:700;margin-bottom:8px;'>"
        "{prix_m2_fmt}</div>"
        "<hr style='border:0;height:1px;background:rgba(255,255,255,.1);margin:6px 0;'>"
        "<table style='font-size:12px;width:100%;'>"
        "<tr><td style='color:#a0aec0;'>Type :</td>"
        "<td style='font-weight:700;text-align:right;'>{type_local}</td></tr>"
        "<tr><td style='color:#a0aec0;'>Surface :</td>"
        "<td style='font-weight:700;text-align:right;'>{surface_m2} m2</td></tr>"
        "<tr><td style='color:#a0aec0;'>Pieces :</td>"
        "<td style='font-weight:700;text-align:right;'>{nb_pieces}</td></tr>"
        "<tr><td style='color:#a0aec0;'>Date vente :</td>"
        "<td style='font-weight:600;text-align:right;font-size:11px;'>{date_mutation}</td></tr>"
        "</table></div>"
    ),
    "style": {"backgroundColor": "transparent", "border": "none", "padding": "0"},
}

# Couche transport
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

if nb_dpe > 0 or nb_dvf > 0:
    tab_prix2d, tab_zones, tab_dpe2d_bat, tab_dpe2d, tab_heat = st.tabs([
        "🏠 Prix par bâtiment (DVF)",
        "🗺️ Zones de prix",
        "🏢 DPE par bâtiment",
        "⚡ Performance Énergétique",
        "🔥 Densité Énergétique",
    ])

    # =========================================================
    # ONGLET : Prix par bâtiment 2D (DVF géocodé BAN)
    # =========================================================
    with tab_prix2d:
        st.markdown("##### Prix immobiliers – Transactions DVF 2025 (géocodées via BAN)")
        st.markdown(
            "Chaque **surface colorée** représente une **vente réelle** de maison ou d'appartement à Nantes en 2025. "
            "La **couleur** indique la zone de prix :"
        )
        # Légende zones de prix
        leg = st.columns(5)
        labels = ["< 100 k EUR", "100–200 k", "200–350 k", "350–550 k", "> 550 k"]
        css_colors = ["#04d9ff", "#687beb", "#ab34e0", "#e01e84", "#ff7300"]
        for col_l, label, color in zip(leg, labels, css_colors):
            col_l.markdown(
                f"<span style='display:inline-block;width:14px;height:14px;"
                f"background:{color};border-radius:3px;margin-right:5px;'></span>{label}",
                unsafe_allow_html=True,
            )
        st.markdown("")

        if nb_dvf > 0:
            df_hm = df_dvf_f.dropna(subset=["valeur_fonciere"]).copy()
            layer_zones_prix = pdk.Layer(
                "HexagonLayer",
                data=df_hm,
                get_position="[lon, lat]",
                get_weight="valeur_fonciere",
                radius=150,
                elevation_scale=0,
                extruded=False,
                color_range=[
                    [4, 217, 255, 120],
                    [104, 123, 235, 120],
                    [171, 52, 224, 120],
                    [224, 30, 132, 120],
                    [255, 115, 0, 120],
                ],
                pickable=True,
                auto_highlight=True,
            )

            layer_dots_prix = pdk.Layer(
                "ScatterplotLayer",
                data=df_dvf_f,
                get_position="[lon, lat]",
                get_radius=8,
                radius_min_pixels=1,
                radius_max_pixels=12,
                get_fill_color="color_prix",
                pickable=True,
                auto_highlight=True,
                opacity=1.0,
            )
            st.pydeck_chart(
                pdk.Deck(
                    map_style=map_style,
                    initial_view_state=VIEW_STATE_2D,
                    layers=[layer_zones_prix, layer_dots_prix, transport_layer],
                    tooltip=tooltip_dvf_prix,
                )
            )

            # Stats rapides en bas de l'onglet
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Transactions affichées", f"{nb_dvf:,}".replace(",", " "))
            c2.metric("Prix médian", f"{df_dvf_f['valeur_fonciere'].median():,.0f} EUR".replace(",", " "))
            c3.metric("Prix/m2 médian", f"{df_dvf_f['prix_m2'].median():,.0f} EUR/m2".replace(",", " "))
            c4.metric("Surface médiane", f"{df_dvf_f['surface_m2'].median():.0f} m2")

            # Distribution des prix
            st.markdown("**Distribution des prix de vente**")
            price_dist = df_dvf_f["valeur_fonciere"].dropna()
            bins = [0, 100_000, 200_000, 350_000, 550_000, 1_000_000, 3_000_000]
            labels_b = ["<100k", "100-200k", "200-350k", "350-550k", "550k-1M", ">1M"]
            price_cat = pd.cut(price_dist, bins=bins, labels=labels_b)
            dist_df = price_cat.value_counts().reindex(labels_b).fillna(0)
            st.bar_chart(dist_df, color="#2ecc71")
        else:
            st.warning("Aucune transaction DVF ne correspond à vos filtres de prix.")

    # =========================================================
    # ONGLET : Zones de prix (Carte de chaleur par zone)
    # =========================================================
    with tab_zones:
        st.markdown("##### Zones de prix – Carte de chaleur immobilière")
        st.markdown(
            "Cette carte agrege les transactions DVF en **zones colorées** pour visualiser "
            "les quartiers les plus chers (🔴 rouge) et les plus abordables (🟢 vert). "
            "Survolez une zone pour voir le prix moyen."
        )

        if nb_dvf > 0:
            # Agrégation par Hexagones (zones)
            df_hm = df_dvf_f.dropna(subset=["prix_m2"]).copy()
            layer_zones = pdk.Layer(
                "HexagonLayer",
                data=df_hm,
                get_position="[lon, lat]",
                get_weight="prix_m2",
                radius=150,  # 150 mètres de rayon par zone (rond/hexagone)
                elevation_scale=0,
                extruded=False,
                color_range=[
                    [4, 217, 255, 120],
                    [104, 123, 235, 120],
                    [171, 52, 224, 120],
                    [224, 30, 132, 120],
                    [255, 115, 0, 120],
                ],
                pickable=True,
                auto_highlight=True,
            )

            # Couche de points (devient visible au zoom)
            layer_dots = pdk.Layer(
                "ScatterplotLayer",
                data=df_dvf_f,
                get_position="[lon, lat]",
                get_radius=8,
                radius_min_pixels=1,   # Quasi invisible quand dézoomé
                radius_max_pixels=12,  # Bien visible quand on zoom
                get_fill_color="color_prix",
                pickable=True,
                auto_highlight=True,
                opacity=1.0,
            )

            st.pydeck_chart(
                pdk.Deck(
                    map_style=map_style,
                    initial_view_state=VIEW_STATE_2D,
                    layers=[layer_zones, layer_dots, transport_layer],
                    tooltip=tooltip_dvf_prix,
                )
            )

            # Légende
            leg2 = st.columns(5)
            labels2 = ["Abordable", "Modéré", "Moyen", "Élevé", "Très cher"]
            colors2 = ["#04d9ff", "#687beb", "#ab34e0", "#e01e84", "#ff7300"]
            for col_l, label, color in zip(leg2, labels2, colors2):
                col_l.markdown(
                    f"<span style='display:inline-block;width:14px;height:14px;"
                    f"background:{color};border-radius:50%;margin-right:5px;'></span>{label}",
                    unsafe_allow_html=True,
                )

            # Stats
            c1, c2, c3 = st.columns(3)
            c1.metric("Prix/m² médian", f"{df_hm['prix_m2'].median():,.0f} EUR/m²".replace(",", " "))
            c2.metric("Prix/m² min", f"{df_hm['prix_m2'].min():,.0f} EUR/m²".replace(",", " "))
            c3.metric("Prix/m² max", f"{df_hm['prix_m2'].max():,.0f} EUR/m²".replace(",", " "))
        else:
            st.warning("Aucune transaction DVF ne correspond à vos filtres de prix.")

    # =========================================================
    # TAB : Vue 2D DPE par bâtiment
    # =========================================================
    with tab_dpe2d_bat:
        st.markdown("##### DPE par bâtiment – Couleur = Étiquette énergétique")
        st.markdown(
            "Chaque **surface colorée** est un **logement diagnostiqué**. "
            "La **couleur** correspond à l'étiquette DPE (A=vert à G=rouge)."
        )
        # Légende DPE
        leg_dpe = st.columns(7)
        dpe_labels = ["A", "B", "C", "D", "E", "F", "G"]
        dpe_css = ["#27ae60", "#2ecc71", "#a4c400", "#f1c40f", "#e67e22", "#d35400", "#c0392b"]
        for col_l, label, color in zip(leg_dpe, dpe_labels, dpe_css):
            col_l.markdown(
                f"<span style='display:inline-block;width:14px;height:14px;"
                f"background:{color};border-radius:3px;margin-right:5px;'></span>DPE {label}",
                unsafe_allow_html=True,
            )

        if nb_dpe > 0:
            df_hm = df_dpe_f.dropna(subset=["dpe_score"]).copy()
            layer_zones_dpe = pdk.Layer(
                "HexagonLayer",
                data=df_hm,
                get_position="[lon, lat]",
                get_weight="dpe_score",
                radius=150,
                elevation_scale=0,
                extruded=False,
                color_range=[
                    [192, 57, 43, 120],     # Rouge (1 = G)
                    [230, 126, 34, 120],    # Orange
                    [241, 196, 15, 120],    # Jaune
                    [164, 196, 0, 120],     # Lime
                    [39, 174, 96, 120],     # Vert (7 = A)
                ],
                pickable=True,
                auto_highlight=True,
            )

            layer_dots_dpe = pdk.Layer(
                "ScatterplotLayer",
                data=df_dpe_f,
                get_position="[lon, lat]",
                get_radius=8,
                radius_min_pixels=1,
                radius_max_pixels=12,
                get_fill_color="color_dpe",
                pickable=True,
                auto_highlight=True,
                opacity=1.0,
            )

            st.pydeck_chart(
                pdk.Deck(
                    map_style=map_style,
                    initial_view_state=VIEW_STATE_2D,
                    layers=[layer_zones_dpe, layer_dots_dpe, transport_layer],
                    tooltip=tooltip_dpe,
                )
            )
        else:
            st.warning("Aucun logement DPE ne correspond à vos filtres.")

    # =========================================================
    # TAB : Vue 2D DPE
    # =========================================================
    with tab_dpe2d:
        st.markdown("##### Répartition géographique des performances énergétiques")
        if nb_dpe > 0:
            df_hm = df_dpe_f.dropna(subset=["conso_5_usages_ep"]).copy()
            layer_zones_conso = pdk.Layer(
                "HexagonLayer",
                data=df_hm,
                get_position="[lon, lat]",
                get_weight="conso_5_usages_ep",
                radius=150,
                elevation_scale=0,
                extruded=False,
                color_range=[
                    [39, 174, 96, 120],     # Vert (faible conso)
                    [164, 196, 0, 120],
                    [241, 196, 15, 120],
                    [230, 126, 34, 120],
                    [192, 57, 43, 120],     # Rouge (forte conso)
                ],
                pickable=True,
                auto_highlight=True,
            )

            layer_dots_conso = pdk.Layer(
                "ScatterplotLayer",
                data=df_dpe_f,
                get_position="[lon, lat]",
                get_radius=8,
                radius_min_pixels=1,
                radius_max_pixels=12,
                get_fill_color="color_dpe",
                pickable=True,
                auto_highlight=True,
                opacity=1.0,
            )

            st.pydeck_chart(
                pdk.Deck(
                    map_style=map_style,
                    initial_view_state=VIEW_STATE_2D,
                    layers=[layer_zones_conso, layer_dots_conso, transport_layer],
                    tooltip=tooltip_dpe,
                )
            )

    # =========================================================
    # TAB : Heatmap densité énergétique
    # =========================================================
    with tab_heat:
        st.markdown("##### Carte de chaleur – Consommation energetique (kWh/m2/an)")
        df_heat = df_dpe_f.dropna(subset=["conso_5_usages_ep"]).copy()
        if len(df_heat) > 0:
            layer_zones_densite = pdk.Layer(
                "HexagonLayer",
                data=df_heat,
                get_position="[lon, lat]",
                get_weight="conso_5_usages_ep",
                colorAggregation='"SUM"',   # Somme de la conso = Densité !
                radius=150,
                elevation_scale=0,
                extruded=False,
                color_range=[
                    [39, 174, 96, 120],
                    [164, 196, 0, 120],
                    [241, 196, 15, 120],
                    [230, 126, 34, 120],
                    [192, 57, 43, 120],
                ],
                pickable=True,
                auto_highlight=True,
            )

            layer_dots_densite = pdk.Layer(
                "ScatterplotLayer",
                data=df_heat,
                get_position="[lon, lat]",
                get_radius=8,
                radius_min_pixels=1,
                radius_max_pixels=12,
                get_fill_color="color_dpe",
                pickable=True,
                auto_highlight=True,
                opacity=1.0,
            )

            st.pydeck_chart(
                pdk.Deck(
                    map_style=map_style,
                    initial_view_state=VIEW_STATE_2D,
                    layers=[layer_zones_densite, layer_dots_densite, transport_layer],
                    tooltip=tooltip_dpe,
                )
            )
        else:
            st.warning("Aucune donnée de consommation pour les filtres actuels.")

else:
    st.warning("Aucune donnée ne correspond à vos filtres. Elargissez les critères.")

st.divider()

# ---------------------------------------------------------------------------
# 7. TABLEAUX DE DONNÉES
# ---------------------------------------------------------------------------
st.subheader("Apercu des données brutes")

tab_t1, tab_t2, tab_t3 = st.tabs(["DPE Nantes", "DVF Nantes (geocodées)", "Stations Transport"])

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
            "type_batiment": "Type batiment",
            "periode_construction": "Periode",
            "type_energie_principale_chauffage": "Energie chauffage",
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
            "valeur_fmt": "Valeur fonciere",
            "type_local": "Type",
            "surface_m2": "Surface (m2)",
            "nb_pieces": "Pieces",
            "prix_m2_fmt": "Prix/m2",
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
# 8. PIED DE PAGE
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<small>Sources : ADEME (DPE logements existants 44) "
    "| DGFiP (DVF 2025, dept 44) "
    "| Base Adresse Nationale (geocodage) "
    "| OpenStreetMap (stations transport 44) "
    "| Projet SAE-601 – IUT Nantes</small>",
    unsafe_allow_html=True,
)