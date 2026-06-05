import streamlit as st
import json
import urllib.request
import ssl
import folium
from streamlit_folium import st_folium

ssl._create_default_https_context = ssl._create_unverified_context

# ---------------------------------------------------------------------------
# CONFIGURATION DE LA PAGE
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Sélection des Départements",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# DONNÉES DES DÉPARTEMENTS
# ---------------------------------------------------------------------------
DEPARTEMENTS = {
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

OPTIONS_LABELS = {code: f"{code} – {nom}" for code, nom in DEPARTEMENTS.items()}
LABEL_TO_CODE = {v: k for k, v in OPTIONS_LABELS.items()}

# ---------------------------------------------------------------------------
# CSS PREMIUM (DA Unifiée avec interface.py)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* Hide global scrollbar to enforce "no-scroll" feel */
body {
    overflow: hidden;
}

/* ─── Base ─── */
.stApp {
    background-color: #ffffff !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}

/* Forcer les textes en noir */
.stApp h1, .stApp h2, .stApp p, .stApp span:not(.prop-badge) {
    color: #111827 !important;
}

/* ─── Header Compact ─── */
.main-header {
    text-align: left;
    padding: 0 0 10px 0;
    margin-top: -40px;
}
.main-header h1 {
    font-size: 1.8rem !important;
    font-weight: 900 !important;
    background: linear-gradient(135deg, #1e293b, #334155);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 !important;
}
.main-header p {
    font-size: 0.95rem;
    color: #64748b !important;
    margin-top: 2px;
}

/* ─── Boutons d'action ─── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 6px 12px !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #f8fafc !important;
    color: #1e293b !important;
}
.stButton > button:hover {
    border-color: #d4af37 !important;
    background-color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.15) !important;
}
/* Bouton principal (Mise à jour DB) */
button[data-testid="baseButton-primary"] {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border: none !important;
}
button[data-testid="baseButton-primary"]:hover {
    background-color: #d4af37 !important;
    color: #000000 !important;
    transform: translateY(-2px) !important;
}

/* ─── Conteneur carte ─── */
.map-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 2px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    overflow: hidden;
}

/* ─── Tags sélectionnés dans le multiselect (DA Dorée) ─── */
div[data-baseweb="tag"], span[data-baseweb="tag"] {
    background-color: #d4af37 !important;
    color: #000000 !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
}
div[data-baseweb="tag"] *, span[data-baseweb="tag"] * {
    color: #000000 !important;
    fill: #000000 !important;
}

/* ─── Section panel ─── */
.panel-title {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #64748b;
    margin-bottom: 8px;
    padding-left: 2px;
    border-left: 3px solid #d4af37;
    padding-left: 8px;
}

/* Animation d'apparition */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}
[data-testid="column"] {
    animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* Ajustements pour réduire l'espace et éviter le scroll */
.block-container {
    padding-top: 3rem !important;
    padding-bottom: 0 !important;
    max-width: 95% !important;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# CHARGEMENT DU GEOJSON DES DÉPARTEMENTS
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Chargement de la carte…")
def load_geojson():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.loads(res.read().decode('utf-8'))

geojson_data = load_geojson()

# Filtrer uniquement les départements gérés
filtered_features = [f for f in geojson_data.get("features", []) if f.get("properties", {}).get("code", "") in DEPARTEMENTS]
geojson_data["features"] = filtered_features

# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------
if "selected_depts" not in st.session_state:
    st.session_state.selected_depts = []

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🗺️ Extraction & Préparation des Données</h1>
    <p>Sélectionnez les départements pour construire la base de données DuckDB. Le fond de carte OSM est interactif.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# LAYOUT : Contrôles à gauche, Carte à droite (Proportions adaptées pour No-Scroll)
# ---------------------------------------------------------------------------
col_controls, col_map = st.columns([1, 1.8], gap="medium")

with col_controls:
    st.markdown("<div class='panel-title'>Recherche</div>", unsafe_allow_html=True)

    # Menu déroulant multiselect
    all_labels = [OPTIONS_LABELS[code] for code in sorted(DEPARTEMENTS.keys())]
    current_labels = [OPTIONS_LABELS[code] for code in st.session_state.selected_depts if code in OPTIONS_LABELS]

    selected_labels = st.multiselect(
        "Départements",
        options=all_labels,
        default=current_labels,
        placeholder="Tapez un nom ou un numéro…",
        label_visibility="collapsed",
    )

    new_selection = [LABEL_TO_CODE[label] for label in selected_labels]
    if new_selection != st.session_state.selected_depts:
        st.session_state.selected_depts = new_selection
        st.rerun()

    st.markdown("<div class='panel-title' style='margin-top:10px;'>Raccourcis Régionaux</div>", unsafe_allow_html=True)

    REGIONS = {
        "Bretagne": ["22", "29", "35", "56"],
        "Pays de la Loire": ["44", "49", "53", "72", "85"],
        "Île-de-France": ["75", "77", "78", "91", "92", "93", "94", "95"],
        "PACA": ["04", "05", "06", "13", "83", "84"],
        "Auvergne-Rhône-Alpes": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
        "Nouvelle-Aquitaine": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"],
        "Occitanie": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"],
        "Normandie": ["14", "27", "50", "61", "76"],
    }

    # Affichage compact des boutons régionaux
    for chunk in [list(REGIONS.items())[i:i+3] for i in range(0, len(REGIONS), 3)]:
        cols = st.columns(3)
        for idx, (region_name, dept_codes) in enumerate(chunk):
            with cols[idx]:
                if st.button(region_name, use_container_width=True):
                    current = set(st.session_state.selected_depts)
                    region_set = set(dept_codes)
                    if region_set.issubset(current):
                        current -= region_set
                    else:
                        current |= region_set
                    st.session_state.selected_depts = sorted(list(current))
                    st.rerun()

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Tout vider", use_container_width=True):
            st.session_state.selected_depts = []
            st.rerun()
    with btn_col2:
        if st.button("Tout sélectionner", use_container_width=True):
            st.session_state.selected_depts = sorted(DEPARTEMENTS.keys())
            st.rerun()

    # ---------------------------------------------------------------------------
    # MISE A JOUR DE LA BASE DE DONNEES
    # ---------------------------------------------------------------------------
    st.markdown("<div class='panel-title' style='margin-top:20px;'>Base de Données DuckDB</div>", unsafe_allow_html=True)

    n_selected = len(st.session_state.selected_depts)
    st.write(f"**{n_selected}** départements sélectionnés.")

    if st.session_state.selected_depts:
        selected_list = sorted(st.session_state.selected_depts)
        
        if st.button("🚀 Lancer l'extraction et la mise à jour", use_container_width=True, type="primary"):
            import subprocess
            
            with st.status("Mise à jour de la base de données en cours...", expanded=True) as status:
                cmd = ["python3", "database/build_database.py"] + selected_list
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                log_container = st.empty()
                logs = []
                for line in process.stdout:
                    logs.append(line.strip())
                    log_container.code("\\n".join(logs[-10:]), language="text") # Compacté pour éviter le scroll
                    
                process.wait()
                
                if process.returncode == 0:
                    status.update(label="Mise à jour terminée avec succès !", state="complete", expanded=False)
                    st.success("Données actualisées et prêtes.")
                    st.balloons()
                else:
                    status.update(label="Erreur lors de la mise à jour.", state="error", expanded=True)
                    st.error("Le script a rencontré une erreur.")
    else:
        st.info("Sélectionnez au moins un département pour mettre à jour la base.")

# ---------------------------------------------------------------------------
# CARTE INTERACTIVE FOLIUM (colonne droite)
# ---------------------------------------------------------------------------
with col_map:
    st.markdown("<div class='map-container'>", unsafe_allow_html=True)
    
    # Centre et zoom adaptés pour un affichage compact
    m = folium.Map(location=[46.5, 2.5], zoom_start=5, tiles="OpenStreetMap", control_scale=True)
    
    # Style en fonction de la sélection
    def style_function(feature):
        code = feature['properties']['code']
        is_selected = code in st.session_state.selected_depts
        return {
            'fillColor': '#d4af37' if is_selected else '#e2e8f0', # Gold DA
            'color': '#000000' if is_selected else '#94a3b8',
            'weight': 1.5 if is_selected else 1,
            'fillOpacity': 0.6 if is_selected else 0.3
        }

    def highlight_function(feature):
        return {
            'weight': 2.5,
            'color': '#111827',
            'fillOpacity': 0.8
        }

    folium.GeoJson(
        geojson_data,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['code', 'nom'],
            aliases=['Département:', 'Nom:'],
            style=("background-color: white; color: #111827; font-family: Inter; font-weight: 600; padding: 4px; border-radius: 4px;")
        )
    ).add_to(m)

    # Affichage de la carte et récupération du clic
    # Utilisation d'une hauteur réduite pour tenir sur un seul écran
    st_data = st_folium(
        m,
        width="100%",
        height=520,
        returned_objects=["last_active_drawing"],
        key="folium_map"
    )

    # Logique de synchronisation bidirectionnelle
    if st_data and st_data.get("last_active_drawing"):
        clicked_code = st_data["last_active_drawing"]["properties"]["code"]
        current = st.session_state.selected_depts
        if clicked_code in current:
            current.remove(clicked_code)
        else:
            current.append(clicked_code)
        st.session_state.selected_depts = sorted(current)
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
