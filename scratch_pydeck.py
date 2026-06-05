import streamlit as st
import pydeck as pdk
import urllib.request
import json

st.write("PyDeck Selection Test")

@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.loads(res.read().decode('utf-8'))

data = load_geojson()

if "selected" not in st.session_state:
    st.session_state.selected = set()

# Colorer en fonction de la selection
for f in data['features']:
    if f['properties']['code'] in st.session_state.selected:
        f['properties']['fill_color'] = [212, 175, 55, 200]
    else:
        f['properties']['fill_color'] = [200, 200, 200, 80]

layer = pdk.Layer(
    "GeoJsonLayer",
    data,
    pickable=True,
    stroked=True,
    filled=True,
    extruded=False,
    get_fill_color="properties.fill_color",
    get_line_color=[0, 0, 0, 255],
    get_line_width=1000,
)

view_state = pdk.ViewState(latitude=46.5, longitude=2.5, zoom=4, bearing=0, pitch=0)

deck = pdk.Deck(layers=[layer], initial_view_state=view_state, map_style="road")

event = st.pydeck_chart(deck, on_select="rerun")
st.write(event)
