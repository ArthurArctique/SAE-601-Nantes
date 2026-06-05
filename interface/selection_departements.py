import streamlit as st
import json
import urllib.request
import ssl

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
# DONNÉES DES DÉPARTEMENTS (France métropolitaine)
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

# Options formatées pour le multiselect : "01 – Ain", "02 – Aisne", ...
OPTIONS_LABELS = {code: f"{code} – {nom}" for code, nom in DEPARTEMENTS.items()}
LABEL_TO_CODE = {v: k for k, v in OPTIONS_LABELS.items()}

# ---------------------------------------------------------------------------
# CSS PREMIUM
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

/* ─── Base ─── */
.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #eef2f7 100%) !important;
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}

/* ─── Header ─── */
.main-header {
    text-align: center;
    padding: 32px 0 8px 0;
}
.main-header h1 {
    font-size: 2.4rem !important;
    font-weight: 900 !important;
    background: linear-gradient(135deg, #1e293b, #334155);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 !important;
    letter-spacing: -0.5px;
}
.main-header p {
    font-size: 1.05rem;
    color: #64748b;
    margin-top: 6px;
}

/* ─── Carte de statistiques ─── */
.stat-row {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin: 18px 0 28px 0;
    flex-wrap: wrap;
}
.stat-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 16px 28px;
    text-align: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.04);
    min-width: 160px;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.stat-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.08);
    border-color: #d4af37;
}
.stat-number {
    font-size: 2rem;
    font-weight: 900;
    color: #1e293b;
    line-height: 1.1;
}
.stat-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 4px;
}

/* ─── Boutons d'action ─── */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 10px 24px !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    border: 1px solid #e2e8f0 !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.1) !important;
}

/* ─── Conteneur carte ─── */
.map-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 4px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.06);
    overflow: hidden;
}

/* ─── Tags sélectionnés dans le multiselect ─── */
div[data-baseweb="tag"], span[data-baseweb="tag"] {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}
div[data-baseweb="tag"] *, span[data-baseweb="tag"] * {
    color: #ffffff !important;
    fill: #ffffff !important;
}

/* ─── Section panel ─── */
.panel-title {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8;
    margin-bottom: 10px;
    padding-left: 2px;
}

/* ─── Légende carte ─── */
.map-legend {
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-top: 12px;
    flex-wrap: wrap;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    color: #475569;
}
.legend-dot {
    width: 14px;
    height: 14px;
    border-radius: 4px;
    display: inline-block;
}

/* ─── Footer ─── */
.footer-info {
    text-align: center;
    color: #94a3b8;
    font-size: 0.78rem;
    margin-top: 32px;
    padding: 16px 0;
    border-top: 1px solid #e2e8f0;
}

/* Animation d'apparition */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}
[data-testid="column"] {
    animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# CHARGEMENT DU GEOJSON DES DÉPARTEMENTS
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Chargement de la carte de France…")
def load_geojson():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.loads(res.read().decode('utf-8'))

geojson_data = load_geojson()

# Construire un dictionnaire code → feature pour accès rapide
feature_by_code = {}
for feat in geojson_data.get("features", []):
    code = feat.get("properties", {}).get("code", "")
    if code in DEPARTEMENTS:
        feature_by_code[code] = feat

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
    <h1>🗺️ Sélection des Départements</h1>
    <p>Choisissez les départements à analyser via le menu ou directement sur la carte</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# LAYOUT : Contrôles à gauche, Carte à droite
# ---------------------------------------------------------------------------
col_controls, col_map = st.columns([1, 2], gap="large")

with col_controls:
    st.markdown("<div class='panel-title'>Recherche par nom</div>", unsafe_allow_html=True)

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

    # Synchroniser multiselect → session state
    st.session_state.selected_depts = [LABEL_TO_CODE[label] for label in selected_labels]

    st.markdown("---")

    # Boutons d'action
    st.markdown("<div class='panel-title'>Actions rapides</div>", unsafe_allow_html=True)

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("✅ Tout sélectionner", use_container_width=True):
            st.session_state.selected_depts = sorted(DEPARTEMENTS.keys())
            st.rerun()
    with btn_col2:
        if st.button("🗑️ Tout désélectionner", use_container_width=True):
            st.session_state.selected_depts = []
            st.rerun()

    st.markdown("---")

    # Raccourcis régionaux
    st.markdown("<div class='panel-title'>Sélection par région</div>", unsafe_allow_html=True)

    REGIONS = {
        "🏖️ Bretagne": ["22", "29", "35", "56"],
        "🌊 Pays de la Loire": ["44", "49", "53", "72", "85"],
        "🗼 Île-de-France": ["75", "77", "78", "91", "92", "93", "94", "95"],
        "☀️ PACA": ["04", "05", "06", "13", "83", "84"],
        "🏔️ Auvergne-Rhône-Alpes": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
        "🍷 Nouvelle-Aquitaine": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"],
        "🌻 Occitanie": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"],
        "⛵ Normandie": ["14", "27", "50", "61", "76"],
        "🏰 Centre-Val de Loire": ["18", "28", "36", "37", "41", "45"],
        "🍺 Grand Est": ["08", "10", "51", "52", "54", "55", "57", "67", "68", "88"],
        "⚓ Hauts-de-France": ["02", "59", "60", "62", "80"],
        "🌿 Bourgogne-Franche-Comté": ["21", "25", "39", "58", "70", "71", "89", "90"],
        "🏝️ Corse": ["2A", "2B"],
    }

    for region_name, dept_codes in REGIONS.items():
        if st.button(region_name, use_container_width=True, key=f"region_{region_name}"):
            current = set(st.session_state.selected_depts)
            region_set = set(dept_codes)
            # Toggle : si tous sont déjà sélectionnés, on les enlève ; sinon on les ajoute
            if region_set.issubset(current):
                current -= region_set
            else:
                current |= region_set
            st.session_state.selected_depts = sorted(list(current))
            st.rerun()

# ---------------------------------------------------------------------------
# CARTE INTERACTIVE (colonne droite)
# ---------------------------------------------------------------------------
with col_map:
    import streamlit.components.v1 as components

    selected_set = set(st.session_state.selected_depts)

    # Construire le GeoJSON filtré avec les styles
    styled_features = []
    for code, feat in feature_by_code.items():
        is_selected = code in selected_set
        styled_feat = {
            "type": "Feature",
            "geometry": feat["geometry"],
            "properties": {
                "code": code,
                "nom": DEPARTEMENTS.get(code, ""),
                "selected": is_selected,
            }
        }
        styled_features.append(styled_feat)

    styled_geojson = json.dumps({
        "type": "FeatureCollection",
        "features": styled_features,
    })

    selected_json = json.dumps(list(selected_set))

    # Carte Leaflet en HTML/JS avec interaction clic
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Inter', sans-serif; background: transparent; }}
            #map {{ width: 100%; height: 620px; border-radius: 12px; }}
            .dept-tooltip {{
                background: white;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                font-weight: 600;
                color: #1e293b;
                box-shadow: 0 4px 16px rgba(0,0,0,0.12);
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            const geojsonData = {styled_geojson};
            let selectedDepts = new Set({selected_json});

            const map = L.map('map', {{
                center: [46.6, 2.5],
                zoom: 6,
                zoomControl: true,
                attributionControl: false,
            }});

            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_nolabels/{{z}}/{{x}}/{{y}}@2x.png', {{
                maxZoom: 12,
                minZoom: 5,
            }}).addTo(map);

            // Style de label
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_only_labels/{{z}}/{{x}}/{{y}}@2x.png', {{
                maxZoom: 12,
                minZoom: 5,
                pane: 'overlayPane',
            }}).addTo(map);

            function getStyle(feature) {{
                const isSelected = selectedDepts.has(feature.properties.code);
                return {{
                    fillColor: isSelected ? '#1e40af' : '#cbd5e1',
                    fillOpacity: isSelected ? 0.55 : 0.2,
                    color: isSelected ? '#1e3a8a' : '#94a3b8',
                    weight: isSelected ? 2.5 : 1,
                }};
            }}

            const geojsonLayer = L.geoJSON(geojsonData, {{
                style: getStyle,
                onEachFeature: function(feature, layer) {{
                    const code = feature.properties.code;
                    const nom = feature.properties.nom;
                    layer.bindTooltip(
                        `<b>${{code}}</b> — ${{nom}}`,
                        {{ className: 'dept-tooltip', sticky: true }}
                    );
                    layer.on('click', function() {{
                        if (selectedDepts.has(code)) {{
                            selectedDepts.delete(code);
                        }} else {{
                            selectedDepts.add(code);
                        }}
                        geojsonLayer.setStyle(getStyle);

                        // Envoyer la sélection à Streamlit
                        const sorted = Array.from(selectedDepts).sort();
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            value: sorted,
                        }}, '*');
                    }});
                    layer.on('mouseover', function(e) {{
                        e.target.setStyle({{
                            weight: 3,
                            fillOpacity: selectedDepts.has(code) ? 0.7 : 0.35,
                        }});
                    }});
                    layer.on('mouseout', function(e) {{
                        geojsonLayer.resetStyle(e.target);
                    }});
                }}
            }}).addTo(map);

            map.fitBounds(geojsonLayer.getBounds(), {{ padding: [20, 20] }});
        </script>
    </body>
    </html>
    """

    st.markdown("<div class='map-container'>", unsafe_allow_html=True)
    components.html(map_html, height=630, scrolling=False)
    st.markdown("</div>", unsafe_allow_html=True)

    # Légende
    st.markdown("""
    <div class="map-legend">
        <div class="legend-item">
            <span class="legend-dot" style="background: #1e40af; opacity: 0.7;"></span>
            Département sélectionné
        </div>
        <div class="legend-item">
            <span class="legend-dot" style="background: #cbd5e1; opacity: 0.4;"></span>
            Non sélectionné
        </div>
        <div class="legend-item">
            <span style="font-size: 0.9rem;">👆</span>
            Cliquez sur la carte pour sélectionner
        </div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# STATISTIQUES
# ---------------------------------------------------------------------------
n_selected = len(st.session_state.selected_depts)
n_total = len(DEPARTEMENTS)

st.markdown(f"""
<div class="stat-row">
    <div class="stat-card">
        <div class="stat-number">{n_selected}</div>
        <div class="stat-label">Départements sélectionnés</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{n_total}</div>
        <div class="stat-label">Départements disponibles</div>
    </div>
    <div class="stat-card">
        <div class="stat-number">{round(n_selected / n_total * 100)}%</div>
        <div class="stat-label">Couverture</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# RÉSUMÉ DE LA SÉLECTION
# ---------------------------------------------------------------------------
if st.session_state.selected_depts:
    with st.expander(f"📋 Détail de la sélection ({n_selected} départements)", expanded=False):
        dept_list = [f"**{code}** – {DEPARTEMENTS[code]}" for code in sorted(st.session_state.selected_depts)]
        # Afficher en colonnes
        cols = st.columns(3)
        for i, item in enumerate(dept_list):
            cols[i % 3].markdown(item)

# ---------------------------------------------------------------------------
# MISE A JOUR DE LA BASE DE DONNEES
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("<div class='panel-title'>Mise à jour de la Base de Données</div>", unsafe_allow_html=True)

if st.session_state.selected_depts:
    selected_list = sorted(st.session_state.selected_depts)
    st.write(f"Départements prêts pour l'extraction : **{', '.join(selected_list)}**")
    
    if st.button("🚀 Lancer l'extraction et la mise à jour (DuckDB)", use_container_width=True, type="primary"):
        import subprocess
        
        with st.status("Mise à jour de la base de données en cours...", expanded=True) as status:
            st.write(f"Exécution de `build_database.py {' '.join(selected_list)}`...")
            
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
                log_container.code("\\n".join(logs[-15:]), language="text")
                
            process.wait()
            
            if process.returncode == 0:
                status.update(label="Mise à jour terminée avec succès !", state="complete", expanded=False)
                st.success("La base de données DuckDB a été actualisée et les nouvelles données sont prêtes.")
                st.balloons()
            else:
                status.update(label="Erreur lors de la mise à jour.", state="error", expanded=True)
                st.error("Le script a rencontré une erreur.")
else:
    st.info("Sélectionnez au moins un département pour mettre à jour la base.")

# Footer
st.markdown("""
<div class="footer-info">
    Données cartographiques · France métropolitaine · 96 départements
</div>
""", unsafe_allow_html=True)
