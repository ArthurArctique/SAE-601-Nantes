import os
import zipfile
import gzip
import shutil
import urllib.request
import urllib.parse
import json
import csv
import ssl
import glob
import re
import pandas as pd
import numpy as np
from scipy.spatial import KDTree
import time

ssl._create_default_https_context = ssl._create_unverified_context

DEPARTEMENTS = ["44","35","69"] # Liste des départements à traiter

def download(url, path):
    print(f"Downloading {url} to {path}...")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(path, 'wb') as out:
        shutil.copyfileobj(response, out)





def run_enrichment_pipeline():
    print("=== DEBUT DE L'EXECUTION DU PIPELINE DE DONNEES ===")
    
    dvf = pd.read_csv("data/dvf/dvf-2025-multidept.csv", sep=";", low_memory=False)
    dvf = dvf[dvf['Type local'].isin(['Maison', 'Appartement'])].copy()
    
    dvf['Valeur fonciere'] = dvf['Valeur fonciere'].astype(str).str.replace(',', '.').astype(float, errors='ignore')
    dvf['Surface reelle bati'] = dvf['Surface reelle bati'].astype(str).str.replace(',', '.').astype(float, errors='ignore')
    dvf['Valeur fonciere'] = pd.to_numeric(dvf['Valeur fonciere'], errors='coerce')
    dvf['Surface reelle bati'] = pd.to_numeric(dvf['Surface reelle bati'], errors='coerce')
    dvf['Nombre pieces principales'] = pd.to_numeric(dvf['Nombre pieces principales'], errors='coerce')
    
    dvf = dvf[(dvf['Valeur fonciere'] >= 5000) & (dvf['Valeur fonciere'] <= 5000000)]
    dvf = dvf[(dvf['Surface reelle bati'] >= 5) & (dvf['Surface reelle bati'] <= 600)]
    dvf = dvf.dropna(subset=['Valeur fonciere', 'Surface reelle bati'])
    print(f"Transactions résidentielles filtrées : {len(dvf)}")
    
    def normalize_address(num, type_voie, nom_voie, commune):
        parts = []
        if pd.notna(num) and str(num).strip():
            parts.append(str(num).strip().split('.')[0].lower())
        if pd.notna(type_voie) and str(type_voie).strip():
            parts.append(str(type_voie).strip().lower())
        if pd.notna(nom_voie) and str(nom_voie).strip():
            parts.append(str(nom_voie).strip().lower())
        if pd.notna(commune) and str(commune).strip():
            parts.append(str(commune).strip().lower())
        full = " ".join(parts)
        full = re.sub(r'[^\w\s]', ' ', full)
        return " ".join(full.split())

    dvf['adresse_normalisee'] = dvf.apply(
        lambda r: normalize_address(r['No voie'], r['Type de voie'], r['Voie'], r['Commune']), axis=1
    )

    def get_insee_code(row):
        return str(row['Code commune']).strip().split('.')[0].zfill(5)

    dvf['code_insee'] = dvf.apply(get_insee_code, axis=1)

    print("Géocodage...")
    print(f"Géocodés nativement via Geo-DVF : {dvf['lat'].notna().sum()} / {len(dvf)}")
    
    print("Appariement DPE...")
    if os.path.exists("data/dpe/dpe-multidept.csv"):
        dpe = pd.read_csv("data/dpe/dpe-multidept.csv", sep=",", low_memory=False)
        dpe['adresse_normalisee'] = dpe.apply(
            lambda r: normalize_address(r.get('numero_voie_ban', ''), '', r.get('nom_rue_ban', ''), r.get('nom_commune_ban', '')), axis=1
        )
        dpe_clean = dpe.sort_values(by='date_reception_dpe', ascending=False).drop_duplicates(subset=['adresse_normalisee'])
        dpe_lookup = dpe_clean.set_index('adresse_normalisee')[['etiquette_dpe', 'etiquette_ges', 'annee_construction']].to_dict('index')
        
        def match_dpe(row):
            match = dpe_lookup.get(row['adresse_normalisee'])
            return (match['etiquette_dpe'], match['etiquette_ges'], match['annee_construction']) if match else (np.nan, np.nan, np.nan)
            
        m = dvf.apply(match_dpe, axis=1)
        dvf['dpe_classe'], dvf['ges_classe'], dvf['annee_construction'] = [x[0] for x in m], [x[1] for x in m], [x[2] for x in m]
    
    print("Indicateurs INSEE...")
    insee_path = "data/insee/insee_communes_multidept_2021.csv"
    if os.path.exists(insee_path):
        insee = pd.read_csv(insee_path, sep=";")
        insee['CODGEO'] = insee['CODGEO'].astype(str).str.zfill(5)
        insee_lookup = insee.set_index('CODGEO')['Q221'].to_dict()
        dvf['insee_mediane_revenu'] = dvf['code_insee'].map(insee_lookup)
    else:
        dvf['insee_mediane_revenu'] = np.nan
    
    print("Proximités Spatiales KDTree...")
    def to_flat(lon, lat): return (lon * 0.678 * 111139, lat * 111139)
    g_mask = dvf['lat'].notna() & dvf['lon'].notna()
    g_coords = np.array([to_flat(lo, la) for lo, la in zip(dvf.loc[g_mask, 'lon'], dvf.loc[g_mask, 'lat'])]) if g_mask.sum() > 0 else []
    
    for k, v in {'ecole': 'data/ecoles/ecoles-multidept.csv', 'transport': 'data/transport/stations-multidept.csv'}.items():
        dvf[f'distance_{k}_m'] = np.nan
        dvf[f'nom_{k}_proche'] = None
        if os.path.exists(v) and len(g_coords) > 0:
            df_pts = pd.read_csv(v, sep=";")
            if not df_pts.empty:
                pts_coords = np.array([to_flat(lo, la) for lo, la in zip(df_pts['lon'], df_pts['lat'])])
                tree = KDTree(pts_coords)
                dists, idxs = tree.query(g_coords)
                dvf.loc[g_mask, f'distance_{k}_m'] = dists
                dvf.loc[g_mask, f'nom_{k}_proche'] = df_pts['name'].iloc[idxs].values

    print("Plans d'Exposition au Bruit (PEB)...")
    dvf['exposition_aeroport_peb'] = "Hors zone de bruit"
    if os.path.exists("data/peb/peb-multidept.geojson"):
        with open("data/peb/peb-multidept.geojson", "r", encoding="utf-8") as f:
            peb_json = json.load(f)
        def is_in_poly(x, y, poly):
            n, inside, p1x, p1y = len(poly), False, poly[0][0], poly[0][1]
            for i in range(n + 1):
                p2x, p2y = poly[i % n]
                if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
                p1x, p1y = p2x, p2y
            return inside

        for feat in peb_json.get('features', []):
            geom = feat.get('geometry')
            if not geom or 'coordinates' not in geom: continue
            lbl = feat.get('properties', {}).get('nomsuplitt', 'Zone')
            g_type = geom.get('type')
            coords = geom.get('coordinates', [])
            
            def check_geom(lon, lat):
                if g_type == 'Polygon': return is_in_poly(lon, lat, coords[0])
                if g_type == 'MultiPolygon': return any(is_in_poly(lon, lat, p[0]) for p in coords)
                return False
                
            mask = dvf.apply(lambda r: check_geom(r['lon'], r['lat']) if pd.notna(r['lon']) else False, axis=1)
            dvf.loc[mask, 'exposition_aeroport_peb'] = lbl
            
    dvf['prix_m2'] = dvf['Valeur fonciere'] / dvf['Surface reelle bati']
    out_cols = ['id_mutation', 'date_mutation', 'nature_mutation', 'Valeur fonciere', 'Type local', 'Surface reelle bati', 'Nombre pieces principales', 'prix_m2', 'adresse_normalisee', 'code_postal', 'Commune', 'code_insee', 'lat', 'lon', 'dpe_classe', 'ges_classe', 'annee_construction', 'insee_mediane_revenu', 'distance_ecole_m', 'nom_ecole_proche', 'distance_transport_m', 'nom_transport_proche', 'exposition_aeroport_peb']
    dvf_out = dvf.rename(columns={'Valeur fonciere': 'prix', 'Type local': 'type_bien', 'Surface reelle bati': 'surface', 'Nombre pieces principales': 'pieces', 'Commune': 'nom_commune'})
    out_cols_renamed = ['id_mutation', 'date_mutation', 'nature_mutation', 'prix', 'type_bien', 'surface', 'pieces', 'prix_m2', 'adresse_normalisee', 'code_postal', 'nom_commune', 'code_insee', 'lat', 'lon', 'dpe_classe', 'ges_classe', 'annee_construction', 'insee_mediane_revenu', 'distance_ecole_m', 'nom_ecole_proche', 'distance_transport_m', 'nom_transport_proche', 'exposition_aeroport_peb']
    
    for c in out_cols_renamed:
        if c not in dvf_out.columns: dvf_out[c] = np.nan
        
    os.makedirs("data/dvf", exist_ok=True)
    dvf_out[out_cols_renamed].to_csv("data/dvf/dvf_enriched_multidept.csv", sep=";", index=False)
    print(">>> DVF ENRICHI SAUVEGARDE ! <<<")

if __name__ == '__main__':
    import time
    start_time_global = time.time()
    for d in ["data/dvf", "data/ban", "data/dpe", "data/insee", "data/admin", "data/transport", "data/ecoles", "data/peb"]:
        os.makedirs(d, exist_ok=True)

    # 1. Geo-DVF (Données pré-géocodées)
    start_time_local = time.time()
    dfs = []
    for dept in DEPARTEMENTS:
        print(f"Téléchargement Geo-DVF pour le département {dept}...")
        url_dvf = f"https://files.data.gouv.fr/geo-dvf/latest/csv/2025/departements/{dept}.csv.gz"
        try:
            df_dept = pd.read_csv(url_dvf, low_memory=False)
            dfs.append(df_dept)
        except Exception as e:
            print(f"Erreur téléchargement Geo-DVF pour {dept}: {e}")
            
    if dfs:
        dvf_total = pd.concat(dfs, ignore_index=True)
        rename_map = {
            'valeur_fonciere': 'Valeur fonciere',
            'type_local': 'Type local',
            'surface_reelle_bati': 'Surface reelle bati',
            'nombre_pieces_principales': 'Nombre pieces principales',
            'adresse_numero': 'No voie',
            'adresse_nom_voie': 'Voie',
            'nom_commune': 'Commune',
            'code_departement': 'Code departement',
            'code_commune': 'Code commune',
            'latitude': 'lat',
            'longitude': 'lon'
        }
        dvf_total.rename(columns=rename_map, inplace=True)
        dvf_total['Type de voie'] = '' 
        
        dvf_total.to_csv("data/dvf/dvf-2025-multidept.csv", sep=';', index=False)
        print(f"-> Geo-DVF OK : {len(dvf_total)} transactions.")
    else:
        print("Erreur: Aucun département téléchargé pour DVF.")

    print(f'\n[Timer] Etape 1 terminée en {time.time() - start_time_local:.2f} secondes.')
    # 2. BAN (téléchargement par département)
    start_time_local = time.time()
    ban_out = open("data/ban/adresses-multidept.csv", 'w', encoding='utf-8')
    header_written = False
    for dept in DEPARTEMENTS:
        gz_ban = f"data/ban/adresses-{dept}.csv.gz"
        try:
            download(f"https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-{dept}.csv.gz", gz_ban)
            with gzip.open(gz_ban, 'rt', encoding='utf-8') as f_in:
                if not header_written:
                    ban_out.write(f_in.readline())
                    header_written = True
                else:
                    f_in.readline()
                shutil.copyfileobj(f_in, ban_out)
            os.remove(gz_ban)
        except Exception as e:
            print(f"Erreur téléchargement BAN pour {dept}: {e}")
    ban_out.close()

    print(f'\n[Timer] Etape 2 terminée en {time.time() - start_time_local:.2f} secondes.')
    # 3. DPE (DuckDB + Hugging Face)
    start_time_local = time.time()
    import duckdb

    csv_path = "data/dpe/dpe-multidept.csv"
    url_hf = "https://huggingface.co/datasets/ArthurArctique/DPE_France/resolve/main/dpe-multidept.csv"
    
    print(f"Téléchargement et filtrage des données DPE depuis Hugging Face pour les départements : {DEPARTEMENTS}...")
    
    dept_list = "','".join(DEPARTEMENTS)
    
    query = f"""
        COPY (
            SELECT * 
            FROM read_csv_auto('{url_hf}', header=true, all_varchar=true)
            WHERE SUBSTR(code_insee_ban, 1, 2) IN ('{dept_list}')
        ) TO '{csv_path}' (HEADER, DELIMITER ',');
    """
    
    try:
        duckdb.sql(query)
        print("-> Téléchargement et filtrage DPE terminés avec succès !")
    except Exception as e:
        print(f"Erreur lors du traitement DPE avec DuckDB : {e}")

    print(f'\n[Timer] Etape 3 terminée en {time.time() - start_time_local:.2f} secondes.')
    # 4. INSEE (Streaming en mémoire)
    import io
    start_time_local = time.time()
    
    # 2021
    print("Téléchargement et filtrage INSEE 2021 en mémoire...")
    url_2021 = "https://www.insee.fr/fr/statistiques/fichier/7756855/indic-struct-distrib-revenu-2021-COMMUNES_csv.zip"
    req_2021 = urllib.request.Request(url_2021, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req_2021) as res:
            with zipfile.ZipFile(io.BytesIO(res.read())) as z:
                df_2021 = None
                useful_cols = {'CODGEO', 'NBMEN21', 'Q221', 'GI21', 'PACT21', 'PCHO21', 'PPEN21'}
                for fname in [f for f in z.namelist() if f.endswith('.csv') and 'COM' in f]:
                    with z.open(fname) as f:
                        cols = pd.read_csv(f, sep=";", nrows=0).columns
                    usecols = [c for c in cols if c in useful_cols or c == cols[0]]
                    df = pd.read_csv(z.open(fname), sep=";", usecols=usecols, low_memory=False)
                    key = df.columns[0]
                    df[key] = df[key].astype(str).str.zfill(5)
                    df_dept = df[df[key].str.startswith(tuple(DEPARTEMENTS))].copy()
                    df_dept = df_dept.set_index(key)
                    if df_2021 is None:
                        df_2021 = df_dept
                    else:
                        dup_cols = [c for c in df_dept.columns if c in df_2021.columns]
                        df_dept = df_dept.drop(columns=dup_cols)
                        df_2021 = df_2021.join(df_dept, how="outer")
                
                if df_2021 is not None and not df_2021.empty:
                    os.makedirs("data/insee", exist_ok=True)
                    df_2021.to_csv("data/insee/insee_communes_multidept_2021.csv", sep=";")
                    print(f"-> INSEE 2021 OK ({len(df_2021)} communes extraites à la volée).")
    except Exception as e:
        print(f"Erreur INSEE 2021: {e}")

    # Fin INSEE 2021

    print(f'\n[Timer] Etape 4 terminée en {time.time() - start_time_local:.2f} secondes.')
    # 5. Communes GeoJSON
    start_time_local = time.time()
    download("https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson", "data/admin/communes-france.geojson")
    with open("data/admin/communes-france.geojson", "r", encoding="utf-8") as f:
        communes_json = json.load(f)
    communes_json['features'] = [f for f in communes_json.get('features', []) if str(f.get('properties', {}).get('code', ''))[:2] in DEPARTEMENTS]
    with open("data/admin/communes-multidept.geojson", "w", encoding="utf-8") as f:
        json.dump(communes_json, f)

    print(f'\n[Timer] Etape 5 terminée en {time.time() - start_time_local:.2f} secondes.')
    # 6. Ecoles & Transport (Bases Officielles Data.gouv)
    start_time_local = time.time()
    print("Téléchargement des Ecoles (Annuaire officiel)...")
    url_ecoles = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-annuaire-education/exports/csv?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"
    try:
        df_ecoles = pd.read_csv(url_ecoles, sep=';', low_memory=False)
        df_ecoles = df_ecoles.dropna(subset=['Position'])
        df_ecoles['lat'] = df_ecoles['Position'].apply(lambda x: float(str(x).split(',')[0]) if ',' in str(x) else np.nan)
        df_ecoles['lon'] = df_ecoles['Position'].apply(lambda x: float(str(x).split(',')[1]) if ',' in str(x) else np.nan)
        df_ecoles = df_ecoles[df_ecoles['Code département'].astype(str).str.zfill(2).isin(DEPARTEMENTS)]
        
        df_ecoles_out = pd.DataFrame({
            'osm_id': df_ecoles['Identifiant de l\'établissement'],
            'type': df_ecoles['Type d\'établissement'],
            'lat': df_ecoles['lat'],
            'lon': df_ecoles['lon'],
            'name': df_ecoles['Nom de l\'établissement'],
            'city': df_ecoles['Nom de la commune'],
            'postcode': df_ecoles['Code postal'],
            'amenity': 'school'
        })
        os.makedirs("data/ecoles", exist_ok=True)
        df_ecoles_out.to_csv("data/ecoles/ecoles-multidept.csv", sep=';', index=False)
        print(f"-> Ecoles OK : {len(df_ecoles_out)} établissements.")
    except Exception as e:
        print(f"Erreur écoles: {e}")

    print("Téléchargement des Transports (Arrêts France)...")
    try:
        req = urllib.request.Request("https://www.data.gouv.fr/api/1/datasets/arrets-de-transport-en-france/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read())
            url_transports = [r['url'] for r in data['resources'] if 'csv' in r['format'].lower()][0]
            
        df_trans = pd.read_csv(url_transports, low_memory=False)
        df_trans = df_trans.dropna(subset=['stop_lat', 'stop_lon'])
        
        if os.path.exists("data/admin/communes-multidept.geojson"):
            import json
            from shapely.geometry import Point, shape
            with open("data/admin/communes-multidept.geojson", 'r') as f:
                communes = json.load(f)
            polys = [shape(feat['geometry']) for feat in communes.get('features', []) if feat.get('geometry')]
            
            if polys:
                print("  Filtrage spatial des arrêts de transport en cours...")
                minx = min([p.bounds[0] for p in polys])
                miny = min([p.bounds[1] for p in polys])
                maxx = max([p.bounds[2] for p in polys])
                maxy = max([p.bounds[3] for p in polys])
                
                df_trans = df_trans[
                    (df_trans['stop_lon'] >= minx) & (df_trans['stop_lon'] <= maxx) &
                    (df_trans['stop_lat'] >= miny) & (df_trans['stop_lat'] <= maxy)
                ]
                
                from shapely.strtree import STRtree
                tree = STRtree(polys)
                def in_poly(lon, lat):
                    pt = Point(lon, lat)
                    return len(tree.query(pt)) > 0
                mask = df_trans.apply(lambda r: in_poly(r['stop_lon'], r['stop_lat']), axis=1)
                df_trans = df_trans[mask]
        
        df_trans_out = pd.DataFrame({
            'osm_id': df_trans['stop_id'],
            'lat': df_trans['stop_lat'],
            'lon': df_trans['stop_lon'],
            'name': df_trans['stop_name'],
            'railway_type': 'station',
            'operator': '',
            'network': '',
            'uic_ref': ''
        })
        os.makedirs("data/transport", exist_ok=True)
        df_trans_out.to_csv("data/transport/stations-multidept.csv", sep=';', index=False)
        print(f"-> Transports OK : {len(df_trans_out)} arrêts.")
    except Exception as e:
        print(f"Erreur transports: {e}")

    print(f'\n[Timer] Etape 6 terminée en {time.time() - start_time_local:.2f} secondes.')
    # 7. PEB
    start_time_local = time.time()
    peb_features = []
    for dept in DEPARTEMENTS:
        params = {'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature', 'typeNames': 'wfs_sup:servitude', 'outputFormat': 'application/json', 'cql_filter': f"categorie='T5' AND partition LIKE '%_{dept}_%'"}
        req = urllib.request.Request("https://data.geopf.fr/wfs/ows?" + urllib.parse.urlencode(params))
        try:
            with urllib.request.urlopen(req) as res:
                peb_features.extend(json.loads(res.read().decode('utf-8')).get('features', []))
        except Exception as e:
            print(f"PEB non trouvé ou erreur pour {dept}: {e}")
            
    peb_geojson = {"type": "FeatureCollection", "features": peb_features}
    with open("data/peb/peb-multidept.geojson", 'w', encoding='utf-8') as f:
        json.dump(peb_geojson, f)
        
    if peb_features:
        headers = sorted(list({k for feat in peb_features for k in feat.get('properties', {}).keys()}))
        with open("data/peb/peb-multidept.csv", 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(headers)
            for feat in peb_features:
                w.writerow([feat.get('properties', {}).get(h, '') for h in headers])
    else:
        with open("data/peb/peb-multidept.csv", 'w', newline='', encoding='utf-8') as f:
            f.write("gid;categorie;nomsup\n")

    print(f'\n[Timer] Etape 7 terminée en {time.time() - start_time_local:.2f} secondes.')
    # 8. In-Process Consolidation & Enrichment
    start_time_local = time.time()
    run_enrichment_pipeline()
    print(f'\n[Timer] Etape 8 terminée en {time.time() - start_time_local:.2f} secondes.')
    print("Done!")
    print(f'[Timer] Temps total global d\'exécution: {time.time() - start_time_global:.2f} secondes.')
