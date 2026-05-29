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

ssl._create_default_https_context = ssl._create_unverified_context

def download(url, path):
    print(f"Downloading {url} to {path}...")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(path, 'wb') as out:
        shutil.copyfileobj(response, out)

def query_overpass(query):
    for endpoint in ["https://overpass.kumi.systems/api/interpreter", "https://lz4.overpass-api.de/api/interpreter", "https://overpass.openstreetmap.fr/api/interpreter"]:
        try:
            req = urllib.request.Request(endpoint + "?data=" + urllib.parse.quote(f"[out:json][timeout:180];{query}"), headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=180) as res:
                return json.loads(res.read().decode('utf-8')).get('elements', [])
        except Exception:
            continue
    return []

def consolidate_insee():
    print("\n=== DEBUT DE LA CONSOLIDATION DES DONNEES INSEE ===")
    
    # 2021
    files_2021 = sorted(glob.glob("data/old_insee/FILO2021_*_COM.csv"))
    print(f"Fichiers 2021 trouvés : {len(files_2021)}")
    df_2021 = None
    for f in files_2021:
        print(f"Lecture de {os.path.basename(f)}...")
        df = pd.read_csv(f, sep=";", low_memory=False)
        key = df.columns[0]
        df[key] = df[key].astype(str)
        df_dept = df[df[key].str.startswith("44")].copy()
        df_dept = df_dept.set_index(key)
        if df_2021 is None:
            df_2021 = df_dept
        else:
            dup_cols = [c for c in df_dept.columns if c in df_2021.columns]
            df_dept = df_dept.drop(columns=dup_cols)
            df_2021 = df_2021.join(df_dept, how="outer")
            
    if df_2021 is not None:
        os.makedirs("data/insee", exist_ok=True)
        out_2021 = "data/insee/insee_communes_44_2021.csv"
        df_2021.to_csv(out_2021, sep=";")
        print(f"-> Succès : Fichier unique 2021 créé avec succès ! ({len(df_2021)} communes, {len(df_2021.columns)} colonnes)")
        
    # 2023
    f_2023 = "data/old_insee/DS_FILOSOFI_CC_2023_data.csv"
    if os.path.exists(f_2023):
        print(f"Lecture de {os.path.basename(f_2023)}...")
        df_2023 = pd.read_csv(f_2023, sep=";", low_memory=False)
        df_2023["GEO"] = df_2023["GEO"].astype(str)
        df_dept_2023 = df_2023[(df_2023["GEO"].str.startswith("44")) & (df_2023["GEO_OBJECT"] == "COM")].copy()
        print("Pivotage de la table du format long au format large...")
        df_pivot = df_dept_2023.pivot(index="GEO", columns="FILOSOFI_MEASURE", values="OBS_VALUE")
        out_2023 = "data/old_insee/insee_communes_44_2023.csv"
        df_pivot.to_csv(out_2023, sep=";")
        print(f"-> Succès : Fichier unique 2023 créé avec succès ! ({len(df_pivot)} communes, {len(df_pivot.columns)} colonnes)")
    print("=== FIN DE LA CONSOLIDATION AVEC SUCCÈS ===\n")

def run_enrichment_pipeline():
    print("=== DEBUT DE L'EXECUTION DU PIPELINE DE DONNEES ===")
    
    # 1. Load DVF
    print("--- Étape 1 : Chargement et filtrage DVF ---")
    dvf = pd.read_csv("data/dvf/dvf-2025-dept44.csv", sep=";", low_memory=False)
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
    
    # 2. Geocoding via API BAN (api-adresse.data.gouv.fr)
    print("--- Étape 2 : Géocodage via l'API BAN (batch) ---")

    def normalize_address(num, type_voie, nom_voie, commune):
        parts = []
        if pd.notna(num) and str(num).strip():
            num_str = str(num).strip().split('.')[0]
            parts.append(num_str.lower())
        if pd.notna(type_voie) and str(type_voie).strip():
            parts.append(str(type_voie).strip().lower())
        if pd.notna(nom_voie) and str(nom_voie).strip():
            parts.append(str(nom_voie).strip().lower())
        if pd.notna(commune) and str(commune).strip():
            parts.append(str(commune).strip().lower())
        full = " ".join(parts)
        full = re.sub(r'[^\w\s]', ' ', full)
        return " ".join(full.split())

    print("Normalisation des adresses DVF...")
    dvf['adresse_normalisee'] = dvf.apply(
        lambda r: normalize_address(r['No voie'], r['Type de voie'], r['Voie'], r['Commune']), axis=1
    )

    # Construction du code_insee en amont (nécessaire pour l'API BAN)
    def get_insee_code(row):
        dept = str(row['Code departement']).strip().split('.')[0].zfill(2)
        comm = str(row['Code commune']).strip().split('.')[0].zfill(3)
        return dept + comm

    dvf['code_insee'] = dvf.apply(get_insee_code, axis=1)

    # Géocodage batch via l'API BAN
    import io
    import time

    def geocode_batch_api(df, batch_size=5000):
        """Géocode un DataFrame via l'API BAN en mode batch CSV.
        L'API accepte un CSV avec colonnes 'adresse' et 'citycode',
        et retourne un CSV enrichi avec latitude, longitude, result_score."""

        results_lat = np.full(len(df), np.nan)
        results_lon = np.full(len(df), np.nan)
        results_score = np.full(len(df), np.nan)

        # Préparer les adresses uniques pour éviter les doublons
        unique_addrs = df[['adresse_normalisee', 'code_insee']].drop_duplicates()
        print(f"  Adresses uniques à géocoder : {len(unique_addrs)}")

        geocoded_cache = {}
        total_batches = (len(unique_addrs) + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, len(unique_addrs))
            batch = unique_addrs.iloc[start:end]

            # Construire le CSV à envoyer
            csv_buffer = io.StringIO()
            csv_buffer.write("adresse,citycode\n")
            for _, row in batch.iterrows():
                addr = str(row['adresse_normalisee']).replace('"', '""')
                code = str(row['code_insee'])
                csv_buffer.write(f'"{addr}",{code}\n')

            csv_data = csv_buffer.getvalue().encode('utf-8')

            # Appel API batch
            boundary = '----FormBoundary' + str(int(time.time()))
            body = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="data"; filename="addresses.csv"\r\n'
                f'Content-Type: text/csv\r\n\r\n'
            ).encode('utf-8') + csv_data + (
                f'\r\n--{boundary}\r\n'
                f'Content-Disposition: form-data; name="columns"\r\n\r\nadresse\r\n'
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="citycode"\r\n\r\ncitycode\r\n'
                f'--{boundary}--\r\n'
            ).encode('utf-8')

            url = "https://api-adresse.data.gouv.fr/search/csv/"
            req = urllib.request.Request(url, data=body, method='POST')
            req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
            req.add_header('User-Agent', 'SAE-601-Nantes/1.0')

            retries = 3
            for attempt in range(retries):
                try:
                    with urllib.request.urlopen(req, timeout=120) as response:
                        result_csv = response.read().decode('utf-8')

                    reader = csv.DictReader(io.StringIO(result_csv))
                    for row in reader:
                        addr = row.get('adresse', '')
                        lat = row.get('latitude', '')
                        lon = row.get('longitude', '')
                        score = row.get('result_score', '0')

                        try:
                            score_f = float(score)
                        except (ValueError, TypeError):
                            score_f = 0.0

                        if lat and lon and score_f >= 0.4:
                            geocoded_cache[addr] = (float(lat), float(lon), score_f)

                    break  # Succès
                except Exception as e:
                    if attempt < retries - 1:
                        print(f"  [RETRY {attempt+1}] Erreur batch {batch_idx+1}: {e}")
                        time.sleep(2 ** (attempt + 1))
                    else:
                        print(f"  [ERREUR] Batch {batch_idx+1} échoué après {retries} tentatives: {e}")

            if (batch_idx + 1) % 2 == 0 or batch_idx == total_batches - 1:
                print(f"  Batch {batch_idx+1}/{total_batches} — cache: {len(geocoded_cache)} adresses géocodées")

            # Rate limiting
            time.sleep(0.5)

        # Appliquer le cache aux résultats
        for i, (_, row) in enumerate(df.iterrows()):
            addr = row['adresse_normalisee']
            if addr in geocoded_cache:
                results_lat[i], results_lon[i], results_score[i] = geocoded_cache[addr]

        return results_lat, results_lon, results_score

    print("Envoi des adresses à l'API BAN (batch)...")
    lats, lons, scores = geocode_batch_api(dvf)
    dvf['lat'] = lats
    dvf['lon'] = lons

    geocoded_count = dvf['lat'].notna().sum()
    print(f"Transactions géocodées : {geocoded_count} / {len(dvf)} ({geocoded_count/len(dvf)*100:.1f}%)")
    
    # 3. DPE
    print("--- Étape 3 : Appariement avec la base DPE ---")
    dpe = pd.read_csv("data/dpe/dpe-logements-existants-44.csv", sep=",", low_memory=False)
    dpe['adresse_normalisee'] = dpe.apply(
        lambda r: normalize_address(r.get('numero_voie_ban', ''), '', r.get('nom_rue_ban', ''), r.get('nom_commune_ban', '')), axis=1
    )
    dpe_clean = dpe.sort_values(by='date_reception_dpe', ascending=False).drop_duplicates(subset=['adresse_normalisee'])
    dpe_lookup = dpe_clean.set_index('adresse_normalisee')[['etiquette_dpe', 'etiquette_ges', 'annee_construction']].to_dict('index')
    
    def match_dpe(row):
        addr = row['adresse_normalisee']
        if addr in dpe_lookup:
            match = dpe_lookup[addr]
            return match['etiquette_dpe'], match['etiquette_ges'], match['annee_construction']
        return np.nan, np.nan, np.nan
        
    dpe_matches = dvf.apply(match_dpe, axis=1)
    dvf['dpe_classe'] = [m[0] for m in dpe_matches]
    dvf['ges_classe'] = [m[1] for m in dpe_matches]
    dvf['annee_construction'] = [m[2] for m in dpe_matches]
    
    dpe_count = dvf['dpe_classe'].notna().sum()
    print(f"Transactions appariées au DPE : {dpe_count} / {len(dvf)} ({dpe_count/len(dvf)*100:.2f}%)")
    
    # 4. INSEE Income
    print("--- Étape 4 : Chargement des indicateurs communaux INSEE ---")
    insee = pd.read_csv("data/insee/insee_communes_44_2021.csv", sep=";")
    insee['CODGEO'] = insee['CODGEO'].astype(str)
    insee_lookup = insee.set_index('CODGEO')['Q221'].to_dict()
    
    # (code_insee a déjà été créé à l'étape 2)
    dvf['insee_mediane_revenu'] = dvf['code_insee'].map(insee_lookup)
    
    # 5. KDTree POIs
    print("--- Étape 5 : Calcul des proximités spatiales (KDTree) ---")
    schools = pd.read_csv("data/ecoles/ecoles-44.csv", sep=";")
    stations = pd.read_csv("data/transport/stations-44.csv", sep=";")
    
    def to_flat_coords(lon, lat):
        return (lon * 0.678 * 111139, lat * 111139)
        
    geocoded_mask = dvf['lat'].notna() & dvf['lon'].notna()
    geo_df = dvf[geocoded_mask].copy()
    geo_coords = np.array([to_flat_coords(lon, lat) for lon, lat in zip(geo_df['lon'], geo_df['lat'])]) if len(geo_df) > 0 else np.array([])
    
    dvf['distance_ecole_m'] = np.nan
    dvf['nom_ecole_proche'] = None
    dvf['distance_transport_m'] = np.nan
    dvf['nom_transport_proche'] = None

    if len(schools) > 0 and len(geo_coords) > 0:
        schools_coords = np.array([to_flat_coords(lon, lat) for lon, lat in zip(schools['lon'], schools['lat'])])
        schools_tree = KDTree(schools_coords)
        sch_dists, sch_idxs = schools_tree.query(geo_coords)
        dvf.loc[geocoded_mask, 'distance_ecole_m'] = sch_dists
        dvf.loc[geocoded_mask, 'nom_ecole_proche'] = schools['name'].iloc[sch_idxs].values
        
    if len(stations) > 0 and len(geo_coords) > 0:
        stations_coords = np.array([to_flat_coords(lon, lat) for lon, lat in zip(stations['lon'], stations['lat'])])
        stations_tree = KDTree(stations_coords)
        sta_dists, sta_idxs = stations_tree.query(geo_coords)
        dvf.loc[geocoded_mask, 'distance_transport_m'] = sta_dists
        dvf.loc[geocoded_mask, 'nom_transport_proche'] = stations['name'].iloc[sta_idxs].values
    
    # 6. Noise PEB
    print("--- Étape 6 : Détection spatiale des Plans d'Exposition au Bruit (PEB) ---")
    dvf['exposition_aeroport_peb'] = "Hors zone de bruit"
    
    with open("data/peb/peb-44.geojson", "r", encoding="utf-8") as f:
        peb_geojson = json.load(f)
        
    def is_in_polygon(x, y, poly):
        n = len(poly)
        inside = False
        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def is_in_geojson_geom(lon, lat, geom):
        g_type = geom.get('type')
        coords = geom.get('coordinates', [])
        if g_type == 'Polygon':
            return is_in_polygon(lon, lat, coords[0])
        elif g_type == 'MultiPolygon':
            for poly in coords:
                if is_in_polygon(lon, lat, poly[0]):
                    return True
        return False

    for feat in peb_geojson.get('features', []):
        geom = feat.get('geometry')
        if not geom or 'coordinates' not in geom:
            continue
        props = feat.get('properties', {})
        nomsup = props.get('nomsup', 'Aéroport')
        nom_literal = props.get('nomsuplitt', 'Zone de bruit')
        
        print(f"Vérification spatiale pour : {nom_literal} ({nomsup})...")
        is_inside = dvf.apply(
            lambda r: is_in_geojson_geom(r['lon'], r['lat'], geom) if pd.notna(r['lon']) and pd.notna(r['lat']) else False,
            axis=1
        )
        dvf.loc[is_inside, 'exposition_aeroport_peb'] = nom_literal
        
    print(f"Nombre de transactions identifiées dans un PEB : {dvf['exposition_aeroport_peb'].ne('Hors zone de bruit').sum()} / {len(dvf)}")
    
    # 7. Save
    print("--- Étape 7 : Enregistrement du jeu enrichi ---")
    dvf['prix_m2'] = dvf['Valeur fonciere'] / dvf['Surface reelle bati']
    
    dvf_out = dvf.rename(columns={
        'Valeur fonciere': 'prix',
        'Type local': 'type_bien',
        'Surface reelle bati': 'surface',
        'Nombre pieces principales': 'pieces'
    })
    
    out_cols = [
        'id_mutation', 'date_mutation', 'nature_mutation', 'prix', 'type_bien', 'surface', 'pieces',
        'prix_m2', 'adresse_normalisee', 'code_postal', 'Commune', 'code_insee', 'lat', 'lon',
        'dpe_classe', 'ges_classe', 'annee_construction', 'insee_mediane_revenu',
        'distance_ecole_m', 'nom_ecole_proche', 'distance_transport_m', 'nom_transport_proche',
        'exposition_aeroport_peb'
    ]
    
    for col in out_cols:
        if col not in dvf_out.columns:
            dvf_out[col] = np.nan
            
    dvf_out = dvf_out[out_cols].rename(columns={'Commune': 'nom_commune'})
    
    os.makedirs("data/dvf", exist_ok=True)
    dvf_out.to_csv("data/dvf/dvf_enriched_dept44.csv", sep=";", index=False)
    print(f">>> SUCCÈS : Base de données enrichie enregistrée ! ({len(dvf_out)} lignes)")
    print("=== FIN DE L'EXECUTION ===\n")

if __name__ == '__main__':
    for d in ["data/dvf", "data/ban", "data/dpe", "data/insee", "data/old_insee", "data/admin", "data/transport", "data/ecoles", "data/peb"]:
        os.makedirs(d, exist_ok=True)

    # 1. DVF 2025
    zip_dvf = "data/dvf/valeursfoncieres-2025.txt.zip"
    download("https://static.data.gouv.fr/resources/demandes-de-valeurs-foncieres/20260405-002321/valeursfoncieres-2025.txt.zip", zip_dvf)
    with zipfile.ZipFile(zip_dvf, 'r') as z:
        txt_name = [name for name in z.namelist() if name.lower().endswith('.txt')][0]
        z.extract(txt_name, "data/dvf")
    txt_path = f"data/dvf/{txt_name}"
    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as infile, \
         open("data/dvf/dvf-2025-dept44.csv", 'w', encoding='utf-8') as outfile:
        header = infile.readline()
        outfile.write(header.replace('|', ';'))
        for line in infile:
            parts = line.split('|')
            if len(parts) > 18 and parts[18] == '44':
                outfile.write(line.replace('|', ';'))
    os.remove(zip_dvf)
    os.remove(txt_path)

    # 2. BAN 44
    gz_ban = "data/ban/adresses-44.csv.gz"
    download("https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-44.csv.gz", gz_ban)
    with gzip.open(gz_ban, 'rb') as f_in, open("data/ban/adresses-44.csv", 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.remove(gz_ban)

    # 3. DPE 44
    download("https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/lines?size=10000&q=44000&format=csv", "data/dpe/dpe-logements-existants-44.csv")

    # 4. INSEE 2021 & 2023
    zip_2021 = "data/old_insee/indic-struct-distrib-revenu-2021-COMMUNES_csv.zip"
    download("https://www.insee.fr/fr/statistiques/fichier/7756855/indic-struct-distrib-revenu-2021-COMMUNES_csv.zip", zip_2021)
    with zipfile.ZipFile(zip_2021, 'r') as z:
        z.extractall("data/old_insee")
    os.remove(zip_2021)

    zip_2023 = "data/old_insee/FILOSOFI_CC_csv.zip"
    download("https://www.insee.fr/fr/statistiques/fichier/8984752/FILOSOFI_CC_csv.zip", zip_2023)
    with zipfile.ZipFile(zip_2023, 'r') as z:
        z.extractall("data/old_insee")
    os.remove(zip_2023)

    # 5. GeoJSON Communes
    download("https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements/44-loire-atlantique/communes-44-loire-atlantique.geojson", "data/admin/communes-44.geojson")

    # 6. Ecoles OSM
    elements = query_overpass('(node["amenity"="school"](46.85,-2.55,47.65,-0.92);way["amenity"="school"](46.85,-2.55,47.65,-0.92););out center;')
    with open("data/ecoles/ecoles-44.csv", 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['osm_id', 'type', 'lat', 'lon', 'name', 'city', 'postcode', 'amenity'])
        for e in elements:
            lat = e.get('lat') if e.get('type') == 'node' else e.get('center', {}).get('lat')
            lon = e.get('lon') if e.get('type') == 'node' else e.get('center', {}).get('lon')
            w.writerow([e.get('id'), e.get('type'), lat, lon, e.get('tags', {}).get('name', ''), e.get('tags', {}).get('addr:city', ''), e.get('tags', {}).get('addr:postcode', ''), e.get('tags', {}).get('amenity', 'school')])

    # 7. Transport OSM
    elements = query_overpass('(node["railway"="station"](46.85,-2.55,47.65,-0.92);node["railway"="halt"](46.85,-2.55,47.65,-0.92);node["railway"="tram_stop"](46.85,-2.55,47.65,-0.92););out;')
    with open("data/transport/stations-44.csv", 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['osm_id', 'lat', 'lon', 'name', 'railway_type', 'operator', 'network', 'uic_ref'])
        for e in elements:
            w.writerow([e.get('id'), e.get('lat'), e.get('lon'), e.get('tags', {}).get('name', ''), e.get('tags', {}).get('railway', ''), e.get('tags', {}).get('operator', ''), e.get('tags', {}).get('network', ''), e.get('tags', {}).get('uic_ref', '')])

    # 8. PEB
    params = {'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature', 'typeNames': 'wfs_sup:servitude', 'outputFormat': 'application/json', 'cql_filter': "categorie='T5' AND partition LIKE '%_44_%'"}
    req = urllib.request.Request("https://data.geopf.fr/wfs/ows?" + urllib.parse.urlencode(params))
    with urllib.request.urlopen(req) as res:
        geojson = json.loads(res.read().decode('utf-8'))
    with open("data/peb/peb-44.geojson", 'w', encoding='utf-8') as f:
        json.dump(geojson, f)
    features = geojson.get('features', [])
    if features:
        headers = sorted(list({k for feat in features for k in feat.get('properties', {}).keys()}))
        with open("data/peb/peb-44.csv", 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(headers)
            for feat in features:
                w.writerow([feat.get('properties', {}).get(h, '') for h in headers])

    # 9. In-Process Consolidation & Enrichment
    consolidate_insee()
    run_enrichment_pipeline()
    print("Done!")
