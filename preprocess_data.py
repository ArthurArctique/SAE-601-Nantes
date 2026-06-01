"""
preprocess_data.py
==================
Script de pré-traitement à exécuter UNE SEULE FOIS.
Lit les CSV bruts (DPE, DVF, BAN, Transport), filtre sur Nantes,
pré-calcule toutes les colonnes dérivées (coordonnées, polygones, couleurs…)
et sauvegarde le tout en Parquet dans data/parquet/.

Usage :
    python preprocess_data.py
"""

import os
import json
import math
import random
import time

import numpy as np
import pandas as pd
from pyproj import Transformer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.join("data", "parquet")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Convertisseur Lambert93 -> WGS84
_transformer = Transformer.from_crs("EPSG:2154", "EPSG:4326", always_xy=True)

# Palette DPE
DPE_COLORS = {
    "A": [39, 174, 96, 220],
    "B": [46, 204, 113, 220],
    "C": [164, 196, 0, 220],
    "D": [241, 196, 15, 220],
    "E": [230, 126, 34, 220],
    "F": [211, 84, 0, 220],
    "G": [192, 57, 43, 220],
}

PRICE_COLORS = [
    [140, 140, 140, 220],
    [230, 190, 10, 220],
    [220, 53, 69, 220],
]


def price_color(prix_m2, seuil_bas, seuil_haut):
    if pd.isna(prix_m2):
        return [120, 120, 120, 100]
    if prix_m2 < seuil_bas:
        return PRICE_COLORS[0]
    elif prix_m2 < seuil_haut:
        return PRICE_COLORS[1]
    else:
        return PRICE_COLORS[2]


# ---------------------------------------------------------------------------
# Vectorized building polygon generation (NumPy)
# ---------------------------------------------------------------------------
def make_building_polygons_vectorized(lons, lats, types, seed_offset=0):
    """
    Génère les polygones de bâtiments pour tout un DataFrame d'un coup,
    en utilisant NumPy au lieu d'une boucle Python.
    Retourne une liste de listes de coordonnées (format JSON-sérialisable).
    """
    n = len(lons)
    # Seeds reproductibles basés sur les coordonnées
    seeds = (np.abs(lons * 1e6) + np.abs(lats * 1e6) + seed_offset).astype(np.int64)

    # Dimensions selon le type
    is_maison = np.array([t == "Maison" for t in types])

    # Générer des dimensions pseudo-aléatoires
    rng = np.random.RandomState(42)
    w_m = np.where(is_maison,
                   rng.uniform(8, 14, n),
                   rng.uniform(14, 25, n))
    h_m = np.where(is_maison,
                   rng.uniform(10, 16, n),
                   rng.uniform(20, 40, n))

    # Conversion mètres -> degrés
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * np.cos(np.radians(lats))
    dw = (w_m / 2) / m_per_deg_lon
    dh = (h_m / 2) / m_per_deg_lat

    # Rotation aléatoire
    angles = rng.uniform(0, math.pi, n)
    cos_a = np.cos(angles)
    sin_a = np.sin(angles)

    # 4 coins du rectangle (avant rotation)
    corners_x = np.array([-1, 1, 1, -1], dtype=np.float64)
    corners_y = np.array([-1, -1, 1, 1], dtype=np.float64)

    polygons = []
    for i in range(n):
        cx = corners_x * dw[i]
        cy = corners_y * dh[i]
        rx = cx * cos_a[i] - cy * sin_a[i] + lons[i]
        ry = cx * sin_a[i] + cy * cos_a[i] + lats[i]
        poly = [[float(rx[j]), float(ry[j])] for j in range(4)]
        poly.append(poly[0])  # fermer le ring
        polygons.append(poly)

    return polygons


# ---------------------------------------------------------------------------
# 1. Transport (le plus simple, fait en premier)
# ---------------------------------------------------------------------------
def preprocess_transport():
    print("▶ Transport…")
    t0 = time.time()

    df = pd.read_csv("data/transport/stations-44.csv", sep=";", encoding="utf-8")
    df = df.dropna(subset=["lat", "lon"])
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df[df["lat"].between(47.15, 47.32) & df["lon"].between(-1.65, -1.45)]
    df = df.reset_index(drop=True)

    out = os.path.join(OUTPUT_DIR, "transport_nantes.parquet")
    df.to_parquet(out, index=False)
    print(f"  ✔ {len(df)} stations → {out} ({time.time()-t0:.1f}s)")
    return df


# ---------------------------------------------------------------------------
# 2. BAN (référentiel d'adresses – utilisé pour géocoder DVF)
# ---------------------------------------------------------------------------
def preprocess_ban():
    print("▶ BAN (105 Mo)…")
    t0 = time.time()

    df = pd.read_csv(
        "data/ban/adresses-44.csv",
        sep=";",
        usecols=["id_fantoir", "numero", "nom_voie", "lon", "lat"],
        low_memory=False,
        dtype={"numero": str, "id_fantoir": str, "nom_voie": str},
    )
    df = df[df["id_fantoir"].str.startswith("44109", na=False)].copy()
    df["code_voie"] = df["id_fantoir"].str.split("_").str[-1]
    df["no_voie"] = df["numero"].str.strip()
    df = df[["code_voie", "no_voie", "nom_voie", "lat", "lon"]].drop_duplicates(
        subset=["code_voie", "no_voie"]
    )
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)

    print(f"  ✔ {len(df)} adresses BAN Nantes filtrées ({time.time()-t0:.1f}s)")
    return df


# ---------------------------------------------------------------------------
# 3. DVF (transactions immobilières) + géocodage via BAN
# ---------------------------------------------------------------------------
def preprocess_dvf(ban):
    print("▶ DVF + géocodage…")
    t0 = time.time()

    # Lecture vectorisée avec Pandas au lieu du parsing ligne par ligne
    df_raw = pd.read_csv(
        "data/dvf/dvf-2025-dept44.csv",
        sep=";",
        usecols=[
            "Code commune", "Nature mutation", "Type local",
            "Valeur fonciere", "Surface reelle bati",
            "Nombre pieces principales", "Code voie",
            "Date mutation", "No voie", "B/T/Q",
        ],
        dtype=str,
        low_memory=False,
    )

    # Filtrage vectorisé (Nantes = commune 109, Vente, Maison/Appartement)
    df_raw.columns = df_raw.columns.str.strip()
    df_raw = df_raw[df_raw["Code commune"].str.strip() == "109"]
    df_raw = df_raw[df_raw["Nature mutation"].str.strip() == "Vente"]
    df_raw = df_raw[df_raw["Type local"].str.strip().isin(["Maison", "Appartement"])]

    # Convertir les valeurs numériques (séparateur décimal français)
    df_raw["valeur_fonciere"] = pd.to_numeric(
        df_raw["Valeur fonciere"].str.strip().str.replace(",", "."), errors="coerce"
    )
    df_raw["surface_m2"] = pd.to_numeric(
        df_raw["Surface reelle bati"].str.strip().str.replace(",", "."), errors="coerce"
    )
    df_raw["nb_pieces"] = pd.to_numeric(
        df_raw["Nombre pieces principales"].str.strip().str.replace(",", "."), errors="coerce"
    ).apply(lambda x: int(x) if pd.notna(x) else np.nan)

    df_raw["type_local"] = df_raw["Type local"].str.strip()
    df_raw["code_voie"] = df_raw["Code voie"].str.strip()
    df_raw["date_mutation"] = df_raw["Date mutation"].str.strip()

    # Numéro de voie
    df_raw["no_voie"] = df_raw["No voie"].str.strip()
    mask_no_voie_bad = df_raw["no_voie"].isin(["00", "", "0", None]) | df_raw["no_voie"].isna()
    df_raw.loc[mask_no_voie_bad, "no_voie"] = df_raw.loc[mask_no_voie_bad, "B/T/Q"].str.strip()

    df = df_raw[["valeur_fonciere", "type_local", "surface_m2", "nb_pieces",
                  "code_voie", "no_voie", "date_mutation"]].copy()

    # Filtrage de plausibilité
    df = df[
        df["valeur_fonciere"].between(20_000, 5_000_000)
        & df["surface_m2"].between(10, 400)
    ].copy()
    df["no_voie"] = df["no_voie"].astype(str).str.strip()

    # Géocodage via BAN
    street_centroids = (
        ban.groupby("code_voie")[["lat", "lon"]].median().reset_index()
    )
    street_centroids.columns = ["code_voie", "lat_s", "lon_s"]

    street_names = (
        ban.groupby("code_voie")["nom_voie"].first().reset_index()
    )
    street_names.columns = ["code_voie", "nom_voie_s"]

    merged = df.merge(ban, on=["code_voie", "no_voie"], how="left")
    merged = merged.merge(street_centroids, on="code_voie", how="left")
    merged = merged.merge(street_names, on="code_voie", how="left")

    merged["lat"] = merged["lat"].fillna(merged["lat_s"])
    merged["lon"] = merged["lon"].fillna(merged["lon_s"])
    merged["nom_voie"] = merged["nom_voie"].fillna(merged["nom_voie_s"])
    merged = merged.dropna(subset=["lat", "lon"])

    # Bounding box
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

    # Format adresse
    def format_address(row):
        no = str(row["no_voie"]).strip()
        street = str(row["nom_voie"]).strip()
        if not no or no == "nan" or no == "None" or no == "0" or no == "00":
            return street.upper()
        return f"{no} {street}".upper()
    merged["adresse_fmt"] = merged.apply(format_address, axis=1)

    # Seuils de prix (terciles)
    prix_m2_valid = merged["prix_m2"].dropna()
    seuil_bas = float(prix_m2_valid.quantile(0.33))
    seuil_haut = float(prix_m2_valid.quantile(0.66))

    merged["color_prix"] = merged["prix_m2"].apply(
        lambda x: price_color(x, seuil_bas, seuil_haut)
    )
    merged["color_type"] = merged["type_local"].map({
        "Maison": [230, 126, 34, 200],
        "Appartement": [52, 152, 219, 200],
    })

    # Polygones vectorisés
    merged = merged.reset_index(drop=True)
    polygons = make_building_polygons_vectorized(
        merged["lon"].values, merged["lat"].values,
        merged["type_local"].values, seed_offset=0
    )
    merged["building_polygon_json"] = [json.dumps(p) for p in polygons]

    # Sérialiser les colonnes de listes en JSON pour Parquet
    merged["color_prix_json"] = merged["color_prix"].apply(json.dumps)
    merged["color_type_json"] = merged["color_type"].apply(json.dumps)

    # Garder seulement les colonnes nécessaires (sans les listes Python)
    cols_keep = [
        "valeur_fonciere", "type_local", "surface_m2", "nb_pieces",
        "code_voie", "no_voie", "date_mutation",
        "lat", "lon", "prix_m2",
        "valeur_fmt", "prix_m2_fmt", "adresse_fmt",
        "building_polygon_json", "color_prix_json", "color_type_json",
    ]
    out_df = merged[cols_keep].reset_index(drop=True)

    out = os.path.join(OUTPUT_DIR, "dvf_nantes.parquet")
    out_df.to_parquet(out, index=False)

    # Sauvegarder les seuils dans un fichier JSON séparé
    seuils = {"seuil_bas": seuil_bas, "seuil_haut": seuil_haut}
    with open(os.path.join(OUTPUT_DIR, "dvf_seuils.json"), "w") as f:
        json.dump(seuils, f)

    print(f"  ✔ {len(out_df)} transactions → {out} ({time.time()-t0:.1f}s)")
    print(f"    Seuils prix/m² : bas={seuil_bas:.0f}, haut={seuil_haut:.0f}")
    return out_df


# ---------------------------------------------------------------------------
# 4. DPE (diagnostics de performance énergétique)
# ---------------------------------------------------------------------------
def preprocess_dpe():
    print("▶ DPE…")
    t0 = time.time()

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

    # Conversion Lambert93 -> WGS84
    lons, lats = _transformer.transform(
        df["coordonnee_cartographique_x_ban"].values,
        df["coordonnee_cartographique_y_ban"].values,
    )
    df["lat"] = lats
    df["lon"] = lons
    df = df[df["lat"].between(47.15, 47.32) & df["lon"].between(-1.65, -1.45)]

    # Score numérique DPE
    df["dpe_score"] = df["etiquette_dpe"].map(
        {"A": 7, "B": 6, "C": 5, "D": 4, "E": 3, "F": 2, "G": 1}
    )
    df = df[df["dpe_score"].notna()]

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

    # Polygones vectorisés
    df = df.reset_index(drop=True)
    types_bat = df["type_batiment"].fillna("Appartement").values
    # Mapper les types DPE aux types attendus par le générateur de polygones
    types_mapped = np.where(
        np.isin(types_bat, ["maison", "Maison"]), "Maison", "Appartement"
    )
    polygons = make_building_polygons_vectorized(
        df["lon"].values, df["lat"].values,
        types_mapped, seed_offset=500_000
    )
    df["building_polygon_json"] = [json.dumps(p) for p in polygons]

    # Colonnes à garder
    cols_keep = [
        "etiquette_dpe", "etiquette_ges",
        "surface_habitable_logement",
        "adresse_ban",
        "nom_commune_ban", "code_postal_ban",
        "type_batiment", "periode_construction",
        "type_energie_principale_chauffage",
        "conso_5_usages_ep",
        "lat", "lon",
        "dpe_score",
        "surface_fmt", "conso_fmt", "adresse_fmt",
        "building_polygon_json",
    ]
    out_df = df[cols_keep].reset_index(drop=True)

    out = os.path.join(OUTPUT_DIR, "dpe_nantes.parquet")
    out_df.to_parquet(out, index=False)
    print(f"  ✔ {len(out_df)} diagnostics → {out} ({time.time()-t0:.1f}s)")
    return out_df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  Pré-traitement des données – Observatoire Foncier Nantes")
    print("=" * 60)
    t_total = time.time()

    preprocess_transport()
    ban = preprocess_ban()
    preprocess_dvf(ban)
    preprocess_dpe()

    print("=" * 60)
    print(f"  ✅ Terminé en {time.time()-t_total:.1f}s")
    print(f"  Fichiers Parquet dans : {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)
