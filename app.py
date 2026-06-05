import streamlit as st

pages = {
    "Application": [
        st.Page("interface/interface.py", title="Observatoire Foncier", icon="🏡", default=True),
    ],
    "Administration": [
        st.Page("interface/selection_departements.py", title="Mise à jour des Données", icon="⚙️"),
    ]
}

pg = st.navigation(pages)
pg.run()
