import os
import zipfile
import gzip
import shutil
import urllib.request
import urllib.parse
import json
import csv
import ssl
import re
import pandas as pd
import numpy as np
from scipy.spatial import KDTree
import time
import duckdb
import sys

# Contourner les problèmes de certificats SSL sur certains environnements (macOS)
ssl._create_default_https_context = ssl._create_unverified_context

DB_PATH = "sae601_nantes.duckdb"

def download_in_memory(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return response.read()

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

def table_exists(con, table_name):
    return con.execute(f"SELECT COUNT(*) FROM duckdb_tables() WHERE table_name='{table_name}' AND schema_name='main'").fetchone()[0] > 0

def create_or_insert(con, table_name, df):
    con.register('temp_df', df)
    if table_exists(con, table_name):
        con.execute(f"INSERT INTO {table_name} SELECT * FROM temp_df")
    else:
        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_df")
    con.unregister('temp_df')

def main():
    start_time_global = time.time()
    
    # Récupération des départements demandés en arguments (ou 44 par défaut)
    target_depts = sys.argv[1:] if len(sys.argv) > 1 else ["44"]
    target_depts = [d.zfill(2) for d in target_depts]

    print("=== INITIALISATION DUCKDB ===")
    con = duckdb.connect(DB_PATH)
    con.execute("INSTALL httpfs; LOAD httpfs;")
    print(f"Connexion à la base {DB_PATH} établie.")

    # Vérifier les départements déjà existants dans la base
    existing_depts = []
    if table_exists(con, "dim_communes"):
        try:
            res = con.execute("SELECT DISTINCT SUBSTR(code_commune, 1, 2) FROM dim_communes WHERE code_commune IS NOT NULL").fetchall()
            existing_depts = [r[0] for r in res if r[0]]
        except Exception:
            pass

    print(f"Départements déjà en base : {existing_depts}")
    
    # Calculer ceux qui manquent
    missing_depts = [d for d in target_depts if d not in existing_depts]
    if not missing_depts:
        print(f"\n[SUCCÈS] Tous les départements demandés ({target_depts}) sont DÉJÀ dans la base !")
        print("Fin du script, aucune donnée téléchargée.")
        con.close()
        return

    DEPARTEMENTS = missing_depts
    print(f"\n---> Démarrage de l'extraction pour les départements manquants : {DEPARTEMENTS}\n")

    # 1. DPE (via DuckDB HTTP direct)
    print("=== 1. EXTRACTION DPE (DuckDB direct) ===")
    url_hf = "https://huggingface.co/datasets/ArthurArctique/DPE_France/resolve/main/dpe-multidept.csv"
    dept_list = "','".join(DEPARTEMENTS)
    
    query_dpe_select = f"""
        SELECT
            "numero_dpe",
            "etiquette_dpe",
            "etiquette_ges",
            "annee_construction",
            "date_reception_dpe",
            "numero_voie_ban",
            "nom_rue_ban",
            "nom_commune_ban",
            "code_insee_ban",
            "conso_5_usages_par_m2_ep"
        FROM read_csv_auto('{url_hf}', header=true, all_varchar=true)
        WHERE SUBSTR(code_insee_ban, 1, 2) IN ('{dept_list}')
    """
    try:
        if table_exists(con, "dim_dpe"):
            con.execute(f"INSERT INTO dim_dpe {query_dpe_select}")
        else:
            con.execute(f"CREATE TABLE dim_dpe AS {query_dpe_select}")
            con.execute("CREATE INDEX idx_dim_dpe_etiquette ON dim_dpe(etiquette_dpe)")
            con.execute("CREATE INDEX idx_dim_dpe_code_insee ON dim_dpe(code_insee_ban)")
        print(f"DPE mis à jour pour {DEPARTEMENTS}.")
    except Exception as e:
        print(f"Erreur DPE DuckDB: {e}.")

    # Récupération du référentiel DPE ENTIER pour l'enrichissement (y compris ceux déjà en base pour éviter des erreurs)
    dpe_df = con.execute(f"SELECT numero_voie_ban, nom_rue_ban, nom_commune_ban, etiquette_dpe, etiquette_ges, annee_construction FROM dim_dpe WHERE SUBSTR(code_insee_ban, 1, 2) IN ('{dept_list}')").df()
    if not dpe_df.empty:
        dpe_df['adresse_normalisee'] = dpe_df.apply(
            lambda r: normalize_address(r.get('numero_voie_ban', ''), '', r.get('nom_rue_ban', ''), r.get('nom_commune_ban', '')), axis=1
        )
        dpe_lookup = dpe_df.drop_duplicates(subset=['adresse_normalisee']).set_index('adresse_normalisee')[['etiquette_dpe', 'etiquette_ges', 'annee_construction']].to_dict('index')
    else:
        dpe_lookup = {}
    del dpe_df
    print("Référentiel DPE en mémoire pour enrichissement.\n")


    # 2. BAN (Mémoire -> DuckDB)
    print("=== 2. EXTRACTION BAN ===")
    ban_dfs = []
    for dept in DEPARTEMENTS:
        print(f"  -> {dept}...")
        try:
            url_ban = f"https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-{dept}.csv.gz"
            df_ban = pd.read_csv(url_ban, sep=";", compression="gzip", low_memory=False, 
                                 usecols=['id', 'numero', 'rep', 'nom_voie', 'code_postal', 'code_insee', 'nom_commune', 'lon', 'lat'])
            ban_dfs.append(df_ban)
        except Exception as e:
            print(f"Erreur BAN pour {dept}: {e}")
            
    if ban_dfs:
        ban_total = pd.concat(ban_dfs, ignore_index=True)
        ban_total.rename(columns={'id': 'id_ban'}, inplace=True)
        create_or_insert(con, "dim_ban", ban_total)
        if not table_exists(con, "dim_ban"): # won't happen but safe
            con.execute("CREATE INDEX idx_dim_ban_code_insee ON dim_ban(code_insee)")
        del ban_total
        del ban_dfs
    print("Table dim_ban mise à jour.\n")


    # 3. INSEE (Mémoire -> DuckDB)
    import io
    print("=== 3. EXTRACTION INSEE ===")
    url_2021 = "https://www.insee.fr/fr/statistiques/fichier/7756855/indic-struct-distrib-revenu-2021-COMMUNES_csv.zip"
    df_insee = None
    insee_lookup = {}
    try:
        req_2021 = urllib.request.Request(url_2021, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_2021) as res:
            with zipfile.ZipFile(io.BytesIO(res.read())) as z:
                useful_cols = {'CODGEO', 'NBMEN21', 'NBPERS21', 'NBUC21', 'Q121', 'Q221', 'Q321', 'Q3_Q1', 'RD', 'S80S2021', 'GI21', 'PACT21', 'PTSA21', 'PCHO21', 'PBEN21', 'PPEN21', 'PAUT21', 'PMIMP21', 'PIMPOT21'}
                for fname in [f for f in z.namelist() if f.endswith('.csv') and 'COM' in f]:
                    with z.open(fname) as f:
                        cols = pd.read_csv(f, sep=";", nrows=0).columns
                    usecols = [c for c in cols if c in useful_cols or c == cols[0]]
                    df = pd.read_csv(z.open(fname), sep=";", usecols=usecols, low_memory=False)
                    key = df.columns[0]
                    df[key] = df[key].astype(str).str.zfill(5)
                    df_dept = df[df[key].str.startswith(tuple(DEPARTEMENTS))].copy()
                    df_dept = df_dept.set_index(key)
                    if df_insee is None:
                        df_insee = df_dept
                    else:
                        dup_cols = [c for c in df_dept.columns if c in df_insee.columns]
                        df_dept = df_dept.drop(columns=dup_cols)
                        df_insee = df_insee.join(df_dept, how="outer")
                        
        if df_insee is not None and not df_insee.empty:
            df_insee = df_insee.reset_index().rename(columns={'index': 'CODGEO', df_insee.index.name: 'CODGEO'})
            create_or_insert(con, "dim_insee", df_insee)
            try: con.execute("CREATE INDEX idx_dim_insee_codgeo ON dim_insee(CODGEO)")
            except: pass
            insee_lookup = df_insee.set_index('CODGEO')['Q221'].to_dict()
    except Exception as e:
        print(f"Erreur INSEE: {e}")
    print("Table dim_insee mise à jour.\n")


    # 4. COMMUNES (GeoJSON -> DuckDB & mémoire pour spatial)
    print("=== 4. EXTRACTION COMMUNES ===")
    url_communes = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/communes.geojson"
    features = []
    polys = []
    rows_com = []
    try:
        communes_json = json.loads(download_in_memory(url_communes).decode('utf-8'))
        from shapely.geometry import shape
        for f in communes_json.get('features', []):
            code = str(f.get('properties', {}).get('code', ''))
            if code[:2] in DEPARTEMENTS:
                features.append(f)
                geom = f.get("geometry")
                rows_com.append((code, f.get('properties', {}).get('nom', ''), json.dumps(geom) if geom else None))
                if geom:
                    polys.append(shape(geom))
    except Exception as e:
        print(f"Erreur communes: {e}")
                
    if not table_exists(con, "dim_communes"):
        con.execute("CREATE TABLE dim_communes (code_commune VARCHAR, nom VARCHAR, geometrie_json TEXT)")
        con.execute("CREATE INDEX idx_dim_communes_code ON dim_communes(code_commune)")
        
    if rows_com:
        con.executemany("INSERT INTO dim_communes VALUES (?, ?, ?)", rows_com)
    print("Table dim_communes mise à jour.\n")


    # 5. ECOLES
    print("=== 5. EXTRACTION ECOLES ===")
    url_ecoles = "https://data.education.gouv.fr/api/explore/v2.1/catalog/datasets/fr-en-annuaire-education/exports/csv?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"
    try:
        df_ecoles = pd.read_csv(url_ecoles, sep=';', low_memory=False)
        df_ecoles = df_ecoles.dropna(subset=['position'])
        df_ecoles['lat'] = df_ecoles['position'].apply(lambda x: float(str(x).split(',')[0]) if ',' in str(x) else np.nan)
        df_ecoles['lon'] = df_ecoles['position'].apply(lambda x: float(str(x).split(',')[1]) if ',' in str(x) else np.nan)
        df_ecoles = df_ecoles[df_ecoles['Code_departement'].astype(str).str.zfill(2).isin(DEPARTEMENTS)]
        if not df_ecoles.empty:
            df_ecoles_out = pd.DataFrame({
                'osm_id': df_ecoles['Identifiant_de_l_etablissement'],
                'type': df_ecoles['Type_etablissement'],
                'lat': df_ecoles['lat'],
                'lon': df_ecoles['lon'],
                'name': df_ecoles['Nom_etablissement'],
                'city': df_ecoles['Nom_commune'],
                'postcode': df_ecoles['Code_postal'],
                'amenity': 'school'
            })
            create_or_insert(con, "dim_ecoles", df_ecoles_out)
        else:
            df_ecoles_out = pd.DataFrame()
    except Exception as e:
        print(f"Erreur écoles: {e}")
        df_ecoles_out = pd.DataFrame()
    print("Table dim_ecoles mise à jour.\n")


    # 6. TRANSPORT
    print("=== 6. EXTRACTION TRANSPORTS ===")
    try:
        req = urllib.request.Request("https://www.data.gouv.fr/api/1/datasets/arrets-de-transport-en-france/", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read())
            url_transports = [r['url'] for r in data['resources'] if 'csv' in r['format'].lower()][0]
            
        df_trans = pd.read_csv(url_transports, low_memory=False)
        df_trans = df_trans.dropna(subset=['stop_lat', 'stop_lon'])
        
        if polys:
            from shapely.strtree import STRtree
            from shapely.geometry import Point
            tree = STRtree(polys)
            minx = min([p.bounds[0] for p in polys])
            miny = min([p.bounds[1] for p in polys])
            maxx = max([p.bounds[2] for p in polys])
            maxy = max([p.bounds[3] for p in polys])
            
            df_trans = df_trans[
                (df_trans['stop_lon'] >= minx) & (df_trans['stop_lon'] <= maxx) &
                (df_trans['stop_lat'] >= miny) & (df_trans['stop_lat'] <= maxy)
            ]
            def in_poly(lon, lat):
                pt = Point(lon, lat)
                return len(tree.query(pt)) > 0
            mask = df_trans.apply(lambda r: in_poly(r['stop_lon'], r['stop_lat']), axis=1)
            df_trans = df_trans[mask]
            
        if not df_trans.empty:
            df_trans_out = pd.DataFrame({
                'osm_id': df_trans['stop_id'],
                'lat': df_trans['stop_lat'],
                'lon': df_trans['stop_lon'],
                'name': df_trans['stop_name'],
                'railway_type': 'station'
            })
            create_or_insert(con, "dim_transport", df_trans_out)
        else:
            df_trans_out = pd.DataFrame()
    except Exception as e:
        print(f"Erreur transports: {e}")
        df_trans_out = pd.DataFrame()
    print("Table dim_transport mise à jour.\n")


    # 7. PEB
    print("=== 7. EXTRACTION PEB ===")
    peb_features = []
    for dept in DEPARTEMENTS:
        params = {'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature', 'typeNames': 'wfs_sup:servitude', 'outputFormat': 'application/json', 'cql_filter': f"categorie='T5' AND partition LIKE '%_{dept}_%'"}
        req = urllib.request.Request("https://data.geopf.fr/wfs/ows?" + urllib.parse.urlencode(params))
        try:
            with urllib.request.urlopen(req) as res:
                peb_features.extend(json.loads(res.read().decode('utf-8')).get('features', []))
        except Exception as e:
            pass
    
    rows_peb = []
    for feat in peb_features:
        props = feat.get('properties', {})
        geom = feat.get('geometry')
        rows_peb.append((
            props.get('gid', ''),
            props.get('categorie', ''),
            props.get('nomsup', ''),
            props.get('descriptio', ''),
            json.dumps(geom) if geom else None
        ))
        
    if not table_exists(con, "dim_peb"):
        con.execute("CREATE TABLE dim_peb (gid VARCHAR, categorie VARCHAR, nomsup VARCHAR, descriptio VARCHAR, geometrie_json TEXT)")
        con.execute("CREATE INDEX idx_dim_peb_gid ON dim_peb(gid)")
        
    if rows_peb:
        con.executemany("INSERT INTO dim_peb VALUES (?, ?, ?, ?, ?)", rows_peb)
    print("Table dim_peb mise à jour.\n")


    # 8. DVF (Mémoire -> Enrichissement -> DuckDB)
    print("=== 8. EXTRACTION ET ENRICHISSEMENT DVF ===")
    dvf_dfs = []
    for dept in DEPARTEMENTS:
        print(f"  -> {dept}...")
        try:
            url_dvf = f"https://files.data.gouv.fr/geo-dvf/latest/csv/2025/departements/{dept}.csv.gz"
            df_dept = pd.read_csv(url_dvf, low_memory=False)
            dvf_dfs.append(df_dept)
        except Exception as e:
            print(f"Erreur Geo-DVF pour {dept}: {e}")
            
    if dvf_dfs:
        dvf = pd.concat(dvf_dfs, ignore_index=True)
        rename_map = {
            'valeur_fonciere': 'prix',
            'type_local': 'type_bien',
            'surface_reelle_bati': 'surface',
            'nombre_pieces_principales': 'pieces',
            'adresse_numero': 'No voie',
            'adresse_nom_voie': 'Voie',
            'nom_commune': 'nom_commune',
            'code_departement': 'Code departement',
            'code_commune': 'Code commune',
            'latitude': 'lat',
            'longitude': 'lon'
        }
        dvf.rename(columns=rename_map, inplace=True)
        dvf['Type de voie'] = ''
        
        dvf = dvf[dvf['type_bien'].isin(['Maison', 'Appartement'])].copy()
        dvf['prix'] = dvf['prix'].astype(str).str.replace(',', '.').astype(float, errors='ignore')
        dvf['surface'] = dvf['surface'].astype(str).str.replace(',', '.').astype(float, errors='ignore')
        dvf['prix'] = pd.to_numeric(dvf['prix'], errors='coerce')
        dvf['surface'] = pd.to_numeric(dvf['surface'], errors='coerce')
        dvf['pieces'] = pd.to_numeric(dvf['pieces'], errors='coerce')
        
        dvf = dvf[(dvf['prix'] >= 5000) & (dvf['prix'] <= 5000000)]
        dvf = dvf[(dvf['surface'] >= 5) & (dvf['surface'] <= 600)]
        dvf = dvf.dropna(subset=['prix', 'surface'])
        
        dvf['adresse_normalisee'] = dvf.apply(
            lambda r: normalize_address(r['No voie'], r['Type de voie'], r['Voie'], r['nom_commune']), axis=1
        )
        
        def get_insee_code(row):
            return str(row['Code commune']).strip().split('.')[0].zfill(5)
        dvf['code_insee'] = dvf.apply(get_insee_code, axis=1)

        # Appariement DPE
        def match_dpe(row):
            match = dpe_lookup.get(row['adresse_normalisee'])
            return (match['etiquette_dpe'], match['etiquette_ges'], match['annee_construction']) if match else (np.nan, np.nan, np.nan)
        m = dvf.apply(match_dpe, axis=1)
        dvf['dpe_classe'], dvf['ges_classe'], dvf['annee_construction'] = [x[0] for x in m], [x[1] for x in m], [x[2] for x in m]

        # Appariement INSEE
        dvf['insee_mediane_revenu'] = dvf['code_insee'].map(insee_lookup)
        
        # KDTree Ecoles et Transport
        def to_flat(lon, lat): return (lon * 0.678 * 111139, lat * 111139)
        g_mask = dvf['lat'].notna() & dvf['lon'].notna()
        g_coords = np.array([to_flat(lo, la) for lo, la in zip(dvf.loc[g_mask, 'lon'], dvf.loc[g_mask, 'lat'])]) if g_mask.sum() > 0 else []
        
        for k, df_pts in {'ecole': df_ecoles_out, 'transport': df_trans_out}.items():
            dvf[f'distance_{k}_m'] = np.nan
            dvf[f'nom_{k}_proche'] = None
            if not df_pts.empty and len(g_coords) > 0:
                pts_coords = np.array([to_flat(lo, la) for lo, la in zip(df_pts['lon'], df_pts['lat'])])
                tree = KDTree(pts_coords)
                dists, idxs = tree.query(g_coords)
                dvf.loc[g_mask, f'distance_{k}_m'] = dists
                dvf.loc[g_mask, f'nom_{k}_proche'] = df_pts['name'].iloc[idxs].values

        # PEB
        dvf['exposition_aeroport_peb'] = "Hors zone de bruit"
        if peb_features:
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
                
            for feat in peb_features:
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

        dvf['prix_m2'] = dvf['prix'] / dvf['surface']
        
        # Insertion finale de la table de faits
        out_cols = ['id_mutation', 'date_mutation', 'nature_mutation', 'prix', 'type_bien', 'surface', 'pieces', 'prix_m2', 'adresse_normalisee', 'code_postal', 'nom_commune', 'code_insee', 'lat', 'lon', 'dpe_classe', 'ges_classe', 'annee_construction', 'insee_mediane_revenu', 'distance_ecole_m', 'nom_ecole_proche', 'distance_transport_m', 'nom_transport_proche', 'exposition_aeroport_peb']
        for c in out_cols:
            if c not in dvf.columns: dvf[c] = np.nan
        dvf_out = dvf[out_cols].copy()
        
        create_or_insert(con, "fait_transactions", dvf_out)
        try:
            con.execute("CREATE INDEX idx_ft_code_insee ON fait_transactions(code_insee)")
            con.execute("CREATE INDEX idx_ft_type_bien ON fait_transactions(type_bien)")
            con.execute("CREATE INDEX idx_ft_dpe ON fait_transactions(dpe_classe)")
        except:
            pass # indexes already exist
        
    print("Table fait_transactions mise à jour avec succès.\n")

    # 9. VUES SQL
    print("=== 9. RE-CREATION DES VUES SQL ===")
    if os.path.exists("database/create_views.sql"):
        with open("database/create_views.sql", "r", encoding="utf-8") as f:
            sql_views = f.read()
        statements = []
        current = ""
        for line in sql_views.split('\n'):
            if line.strip().startswith('--'): continue
            current += " " + line
            if ';' in current:
                parts = current.split(';')
                statements.append(parts[0] + ';')
                current = parts[1] if len(parts) > 1 else ""
                
        for stmt in statements:
            if stmt.strip():
                try: con.execute(stmt)
                except Exception as e: print(f"Erreur vue : {e}")
        print("Vues actualisées.\n")

    # Affichage du résumé
    print("=" * 60)
    print("RÉSUMÉ DE LA BASE DE DONNÉES")
    print("=" * 60)
    tables = con.execute("SELECT table_name FROM duckdb_tables() WHERE schema_name = 'main' ORDER BY table_name").fetchall()
    for (table_name,) in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"  {table_name:<33} {count:>12,} lignes")

    con.close()
    
    print(f"\n[Terminé] Process complet en {time.time() - start_time_global:.2f} secondes.")
    print(f"Base de données : {DB_PATH}")

if __name__ == '__main__':
    main()
