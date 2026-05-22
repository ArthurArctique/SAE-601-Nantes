import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Dashboard Immo Nantes", page_icon="🏡", layout="wide", initial_sidebar_state="expanded")

# Palette officielle pour les étiquettes DPE (Vert à Rouge épuré)
DPE_COLORS = {
    "A": [39, 174, 96, 200],    # Vert émeraude
    "B": [46, 204, 113, 200],   # Vert clair
    "C": [164, 196, 0, 200],    # Lime/Jaune-vert
    "D": [241, 196, 15, 200],   # Jaune
    "E": [230, 126, 34, 200],   # Orange
    "F": [211, 84, 0, 200],     # Orange foncé
    "G": [192, 57, 43, 200]     # Rouge
}

# --- 2. GÉNÉRATION DE DONNÉES FICTIVES ---
# On utilise cache_data pour ne générer les données qu'une seule fois au lancement
@st.cache_data
def load_dummy_data():
    np.random.seed(42)
    n_points = 2000 # Nombre de fausses transactions
    
    df = pd.DataFrame({
        'id_transaction': range(n_points),
        'lat': np.random.normal(47.2184, 0.04, n_points), # Centré autour de Nantes
        'lon': np.random.normal(-1.5536, 0.04, n_points),
        'valeur_fonciere': np.random.randint(80000, 1200000, n_points),
        'surface_m2': np.random.randint(15, 250, n_points),
        'etiquette_dpe': np.random.choice(["A", "B", "C", "D", "E", "F", "G"], n_points, p=[0.05, 0.1, 0.25, 0.3, 0.15, 0.1, 0.05]),
        'zone_bruit': np.random.choice(["Zone A (Très forte)", "Zone B (Forte)", "Zone C (Modérée)", "Zone D (Faible)", "Hors zone de bruit"], n_points)
    })
    
    # Pré-calculs esthétiques pour PyDeck
    df['color_dpe'] = df['etiquette_dpe'].map(DPE_COLORS)
    df['valeur_fonciere_formattee'] = df['valeur_fonciere'].apply(lambda x: f"{x:,.0f}".replace(",", " "))
    return df

df = load_dummy_data()

# --- 3. BARRE LATÉRALE (FILTRES INTERACTIFS) ---
st.sidebar.title("Filtres d'Analyse 🎯")
st.sidebar.markdown("Affinez votre recherche sur la métropole nantaise.")

# Filtre : Valeur Foncière
prix_min, prix_max = st.sidebar.slider(
    "Valeur Foncière (€)",
    min_value=50000, max_value=1500000,
    value=(150000, 600000), step=10000,
    format="%d €"
)

# Filtre : DPE
st.sidebar.markdown("### Performance Énergétique")
dpe_choix = st.sidebar.multiselect(
    "Filtrer par étiquette DPE :",
    options=["A", "B", "C", "D", "E", "F", "G"],
    default=["A", "B", "C", "D"]
)

# Filtre : Bruit
st.sidebar.markdown("### Nuisances Sonores")
peb_choix = st.sidebar.multiselect(
    "Filtrer par zone d'exposition au bruit :",
    options=["Zone A (Très forte)", "Zone B (Forte)", "Zone C (Modérée)", "Zone D (Faible)", "Hors zone de bruit"],
    default=["Zone C (Modérée)", "Zone D (Faible)", "Hors zone de bruit"]
)

# --- AJOUT CONTROLES CARTE ---
st.sidebar.markdown("---")
st.sidebar.subheader("Style & Affichage de la Carte 🗺️")

map_style_name = st.sidebar.selectbox(
    "Style du fond de carte :",
    options=["Sombre Premium", "Clair Épuré", "Voyager Coloré"],
    index=0
)
MAP_STYLES = {
    "Sombre Premium": "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    "Clair Épuré": "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    "Voyager Coloré": "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
}
map_style = MAP_STYLES[map_style_name]

viz_type = st.sidebar.selectbox(
    "Type de calque :",
    options=["Points DPE (Recommandé)", "Cylindres 3D (Hauteur = Prix)", "Densité (Carte de Chaleur)"],
    index=0
)

# --- 4. FILTRAGE DES DONNÉES EN DIRECT ---
df_filtre = df[
    (df['valeur_fonciere'] >= prix_min) & 
    (df['valeur_fonciere'] <= prix_max) & 
    (df['etiquette_dpe'].isin(dpe_choix)) & 
    (df['zone_bruit'].isin(peb_choix))
]

# --- 5. CORPS PRINCIPAL DU DASHBOARD ---
st.title("🏡 Observatoire Foncier & Environnemental - Nantes")
st.markdown("Maquette interactive générée avec des données 100% fictives.")

# Calcul et affichage des KPIs basés sur les données filtrées
col1, col2, col3, col4 = st.columns(4)

nb_transactions = len(df_filtre)
prix_median = df_filtre['valeur_fonciere'].median() if nb_transactions > 0 else 0
surface_mediane = df_filtre['surface_m2'].median() if nb_transactions > 0 else 0
dpe_mode = df_filtre['etiquette_dpe'].mode()
dpe_majoritaire = dpe_mode.iloc[0] if nb_transactions > 0 and not dpe_mode.empty else "N/A"

col1.metric(label="Transactions correspondantes", value=f"{nb_transactions}")
col2.metric(label="Prix médian", value=f"{prix_median:,.0f} €".replace(',', ' '))
col3.metric(label="Surface médiane", value=f"{surface_mediane:.0f} m²")
col4.metric(label="DPE majoritaire", value=dpe_majoritaire)

st.divider()

# --- 6. CARTE INTERACTIVE PREMIUM (PyDeck) ---
st.subheader("Cartographie des transactions 🗺️")
st.markdown("Interagissez avec la carte : zoomez, inclinez (clic droit + glisser) et survolez les points pour analyser la métropole.")

if nb_transactions > 0:
    # 1. Définition dynamique de la couche de données en fonction du choix utilisateur
    if viz_type == "Cylindres 3D (Hauteur = Prix)":
        layer = pdk.Layer(
            'ColumnLayer',
            data=df_filtre,
            get_position='[lon, lat]',
            get_elevation='valeur_fonciere',
            elevation_scale=0.0015, # Ajusté pour que le max (1.5M€) fasse ~2250m de hauteur à l'échelle de la carte
            radius=35,
            get_fill_color='color_dpe',
            pickable=True,
            auto_highlight=True,
            extruded=True,
        )
        # Vue inclinée par défaut pour la 3D
        view_state = pdk.ViewState(latitude=47.2184, longitude=-1.5536, zoom=12.2, pitch=45, bearing=15)
        
    elif viz_type == "Points DPE (Recommandé)":
        layer = pdk.Layer(
            'ScatterplotLayer',
            data=df_filtre,
            get_position='[lon, lat]',
            get_radius=60,
            radius_min_pixels=4,
            radius_max_pixels=15,
            get_fill_color='color_dpe',
            get_line_color=[255, 255, 255, 120],
            line_width_min_pixels=1,
            pickable=True,
            auto_highlight=True
        )
        # Vue à plat classique
        view_state = pdk.ViewState(latitude=47.2184, longitude=-1.5536, zoom=12.5, pitch=0, bearing=0)
        
    else: # Carte de Chaleur
        layer = pdk.Layer(
            'HeatmapLayer',
            data=df_filtre,
            get_position='[lon, lat]',
            get_weight='valeur_fonciere',
            radius_pixels=40,
            intensity=1.2,
            threshold=0.05
        )
        # Vue à plat
        view_state = pdk.ViewState(latitude=47.2184, longitude=-1.5536, zoom=12.5, pitch=0, bearing=0)

    # Rendu final avec DeckGL et un tooltip sublime
    st.pydeck_chart(pdk.Deck(
        map_style=map_style,
        initial_view_state=view_state,
        layers=[layer],
        tooltip={
            "html": """
                <div style="font-family: 'Inter', sans-serif; padding: 12px; background: rgba(18, 22, 30, 0.95); border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; box-shadow: 0 4px 20px rgba(0,0,0,0.45); max-width: 250px;">
                    <div style="font-size: 11px; text-transform: uppercase; color: #9bb1cf; margin-bottom: 6px; font-weight: 700; letter-spacing: 0.5px;">Transaction #{id_transaction}</div>
                    <div style="font-size: 18px; font-weight: 800; color: #2ecc71; margin-bottom: 8px; display: flex; align-items: center; gap: 4px;">🏡 {valeur_fonciere_formattee} €</div>
                    <hr style="border: 0; height: 1px; background: rgba(255,255,255,0.1); margin: 8px 0;">
                    <div style="display: grid; grid-template-columns: auto auto; gap: 6px 12px; font-size: 13px;">
                        <span style="color: #a0aec0;">Surface habitable:</span> <strong style="text-align: right;">{surface_m2} m²</strong>
                        <span style="color: #a0aec0;">Classe DPE:</span> <span style="font-weight: bold; padding: 2px 8px; border-radius: 4px; background: rgba(255,255,255,0.15); text-align: center; color: #f1c40f;">{etiquette_dpe}</span>
                        <span style="color: #a0aec0;">Exposition Bruit:</span> <strong style="text-align: right; font-size: 11px; color: #e74c3c;">{zone_bruit}</strong>
                    </div>
                </div>
            """,
            "style": {"backgroundColor": "transparent", "color": "white", "padding": "0", "border": "none"}
        }
    ))
else:
    st.warning("Aucune transaction ne correspond à vos filtres. Veuillez élargir vos critères de recherche.")

# --- 7. TABLEAU DE DONNÉES ---
st.subheader("Aperçu des données tabulaires (Filtre actif)")
st.dataframe(df_filtre.head(100), use_container_width=True, hide_index=True)