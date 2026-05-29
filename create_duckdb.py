import duckdb
import json
import os
import sys
import re
import unicodedata

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = "sae601_nantes.duckdb"
SQL_SCHEMA_PATH = "create_database.sql"
DATA_DIR = "data"

# Mapping spécifique pour la table DVF Mutations
DVF_MUTATIONS_EXPLICIT_MAPPING = {
    'identifiant_document': '"Identifiant de document"',
    'prefixe_section': '"Prefixe de section"',
    'lot_1er': '"1er lot"',
    'surface_carrez_1er_lot': '"Surface Carrez du 1er lot"',
    'lot_2eme': '"2eme lot"',
    'surface_carrez_2eme_lot': '"Surface Carrez du 2eme lot"',
    'lot_3eme': '"3eme lot"',
    'surface_carrez_3eme_lot': '"Surface Carrez du 3eme lot"',
    'lot_4eme': '"4eme lot"',
    'surface_carrez_4eme_lot': '"Surface Carrez du 4eme lot"',
    'lot_5eme': '"5eme lot"',
    'surface_carrez_5eme_lot': '"Surface Carrez du 5eme lot"',
}

def normalize_name(s):
    """Normalise les noms des colonnes CSV pour matcher le snake_case de SQL."""
    s = s.lstrip('\ufeff')
    s = "".join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'[^a-zA-Z0-9]', '_', s)
    s = s.lower()
    s = s.strip('_')
    s = re.sub(r'_+', '_', s)
    
    # Règles spécifiques pour les préfixes numériques DVF
    if re.match(r'^\d+_', s):
        match = re.match(r'^(\d+)_(.*)$', s)
        s = f"{match.group(2)}_{match.group(1)}"
    if s == 'b_t_q':
        s = 'btq'
    return s

def get_csv_columns(con, csv_path, delim=';'):
    """Récupère le nom des colonnes d'un CSV via DuckDB DESCRIBE."""
    try:
        res = con.execute(f"DESCRIBE SELECT * FROM read_csv('{csv_path}', delim='{delim}', header=true, auto_detect=true, ignore_errors=true) LIMIT 0").fetchall()
        return [row[0] for row in res]
    except Exception as e:
        print(f"[ATTENTION] Impossible de lire les colonnes du CSV {csv_path} avec le délimiteur '{delim}': {e}")
        return []

def import_csv_table(con, table_name, csv_path, delim=';', mappings=None, decimal_separator=None, nullstr=None):
    """Importe dynamiquement un fichier CSV dans une table existante."""
    if not os.path.exists(csv_path):
        print(f"   -> [MANQUANT] Fichier {csv_path} non trouvé. Table '{table_name}' laissée vide.")
        return 0
        
    if mappings is None:
        mappings = {}
        
    # Détection automatique du délimiteur si le premier test échoue
    csv_cols_raw = get_csv_columns(con, csv_path, delim)
    if not csv_cols_raw and delim == ';':
        delim = ','  # Test du format standard international
        csv_cols_raw = get_csv_columns(con, csv_path, delim)
        
    table_cols = [row[0] for row in con.execute(f"SELECT name FROM pragma_table_info('{table_name}')").fetchall() if row[0] != 'id']
    csv_cols = {normalize_name(c): c for c in csv_cols_raw}
    
    select_list = []
    for col in table_cols:
        col_lower = col.lower()
        if col_lower in mappings:
            csv_col_name = mappings[col_lower]
            select_list.append(f"{csv_col_name} AS {col}")
        elif col_lower in csv_cols:
            select_list.append(f'"{csv_cols[col_lower]}" AS {col}')
            
    if not select_list:
        print(f"   -> [ERREUR] Aucun mapping trouvé pour la table {table_name}. Vérifiez les colonnes.")
        return 0
        
    extra_options = []
    if decimal_separator:
        extra_options.append(f"decimal_separator = '{decimal_separator}'")
    if nullstr:
        extra_options.append(f"nullstr = '{nullstr}'")
    extra_options_str = ",\n            " + ",\n            ".join(extra_options) if extra_options else ""

    con.execute(f"""
        INSERT INTO {table_name} BY NAME
        SELECT {', '.join(select_list)}
        FROM read_csv('{csv_path}',
            delim = '{delim}',
            header = true,
            auto_detect = true,
            ignore_errors = true,
            strict_mode = false{extra_options_str}
        )
    """)
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    return count

def import_eav_table(con, table_name, csv_path, delim=';', nullstr=None):
    """Pivote un fichier CSV large en format EAV (Entity-Attribute-Value)."""
    if not os.path.exists(csv_path):
        print(f"   -> [MANQUANT] Fichier {csv_path} non trouvé. Table '{table_name}' laissée vide.")
        return 0
        
    cols = get_csv_columns(con, csv_path, delim)
    if not cols:
        return 0
        
    codgeo_col = next((c for c in cols if c.upper() == 'CODGEO'), None)
    if not codgeo_col:
        codgeo_col = next((c for c in cols if c.upper() in ('GEO', 'CODGEO')), cols[0])
        
    extra_options = ["all_varchar = true"]
    if nullstr:
        extra_options.append(f"nullstr = '{nullstr}'")
    extra_options_str = ",\n                    " + ",\n                    ".join(extra_options)

    con.execute(f"""
        INSERT INTO {table_name} BY NAME
        SELECT
            "{codgeo_col}" AS codgeo,
            name AS nom_colonne,
            value::VARCHAR AS valeur
        FROM (
            UNPIVOT (
                SELECT * FROM read_csv('{csv_path}',
                    delim = '{delim}',
                    header = true,
                    auto_detect = true,
                    ignore_errors = true,
                    strict_mode = false{extra_options_str}
                )
            )
            ON COLUMNS(* EXCLUDE ("{codgeo_col}"))
            INTO
                NAME name
                VALUE value
        )
    """)
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    return count

def main():
    # Nettoyage des anciennes instances
    for path in [DB_PATH, f"{DB_PATH}.wal"]:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"[INFO] Ancien fichier '{path}' supprimé.")
            except Exception as e:
                print(f"[ATTENTION] Impossible de supprimer {path} : {e}")
                print("[INFO] Fermez DBeaver ou VS Code et relancez le script.")
                sys.exit(1)

    # Lecture et transformation du schéma SQL
    if not os.path.exists(SQL_SCHEMA_PATH):
        print(f"[ERREUR] Le fichier schéma {SQL_SCHEMA_PATH} n'existe pas.")
        sys.exit(1)
        
    with open(SQL_SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql_schema = f.read()

    def replace_table(match):
        table_name = match.group(1)
        body = match.group(2)
        id_pattern = re.compile(r"\bid\s+INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", re.IGNORECASE)
        if id_pattern.search(body):
            seq_name = f"seq_{table_name}"
            seq_sql = f"CREATE SEQUENCE IF NOT EXISTS {seq_name};\n"
            new_body = id_pattern.sub(f"id INTEGER DEFAULT nextval('{seq_name}') PRIMARY KEY", body)
            return f"{seq_sql}CREATE TABLE {table_name} ({new_body});"
        return match.group(0)

    table_pattern = re.compile(r"CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);", re.DOTALL | re.IGNORECASE)
    transformed_schema = table_pattern.sub(replace_table, sql_schema)

    # Connexion à DuckDB
    con = duckdb.connect(DB_PATH)
    print(f"[INFO] Fichier DuckDB '{DB_PATH}' initialisé.\n")

    try:
        con.execute("PRAGMA checkpoint_threshold='10GB';")
        con.execute("BEGIN TRANSACTION;")
        con.execute(transformed_schema)
        
        # 1. COMMUNES
        print("=" * 60)
        print("1. Chargement des communes (GeoJSON)")
        print("=" * 60)
        geojson_path = os.path.join(DATA_DIR, "admin", "communes-44.geojson")
        if os.path.exists(geojson_path):
            with open(geojson_path, "r", encoding="utf-8") as f:
                geojson = json.load(f)
            features = geojson.get("features", [])
            for feat in features:
                props = feat.get("properties", {})
                geom = feat.get("geometry")
                con.execute(
                    "INSERT INTO communes (code_commune, nom, geometrie_geojson) VALUES (?, ?, ?)",
                    [props.get("code"), props.get("nom"), json.dumps(geom) if geom else None]
                )
            print(f"   -> {len(features)} communes insérées.\n")
        else:
            print(f"   -> Fichier {geojson_path} non trouvé.\n")

        # 2. ADRESSES BAN
        print("=" * 60)
        print("2. Chargement des adresses BAN")
        print("=" * 60)
        ban_path = os.path.join(DATA_DIR, "ban", "adresses-44.csv")
        count = import_csv_table(con, "adresses_ban", ban_path, delim=';', mappings={'id_ban': 'id'})
        print(f"   -> {count:,} adresses insérées.\n")

        # 3. DPE LOGEMENTS
        print("=" * 60)
        print("3. Chargement des DPE logements")
        print("=" * 60)
        dpe_path = os.path.join(DATA_DIR, "dpe", "dpe-logements-existants-44.csv")
        count = import_csv_table(con, "dpe_logements", dpe_path, delim=',')
        print(f"   -> {count:,} DPE insérés.\n")

        # 4. DVF MUTATIONS BRUTES
        print("=" * 60)
        print("4. Chargement des mutations DVF brutes")
        print("=" * 60)
        dvf_path = os.path.join(DATA_DIR, "dvf", "dvf-2025-dept44.csv")
        count = import_csv_table(con, "dvf_mutations", dvf_path, delim=';', mappings=DVF_MUTATIONS_EXPLICIT_MAPPING)
        print(f"   -> {count:,} mutations insérées.\n")

        # 5. DVF ENRICHI
        print("=" * 60)
        print("5. Chargement du DVF enrichi")
        print("=" * 60)
        dvf_enr_path = os.path.join(DATA_DIR, "dvf", "dvf_enriched_dept44.csv")
        count = import_csv_table(con, "dvf_enriched", dvf_enr_path, delim=';')
        print(f"   -> {count:,} transactions enrichies insérées.\n")

        # 6. ECOLES (Vérification intelligente du délimiteur intégrée)
        print("=" * 60)
        print("6. Chargement des écoles")
        print("=" * 60)
        ecoles_path = os.path.join(DATA_DIR, "ecoles", "ecoles-44.csv")
        count = import_csv_table(con, "ecoles", ecoles_path, delim=';')
        print(f"   -> {count:,} écoles insérées.\n")

        # 7. STATIONS TRANSPORT (Vérification intelligente du délimiteur intégrée)
        print("=" * 60)
        print("7. Chargement des stations de transport")
        print("=" * 60)
        transport_path = os.path.join(DATA_DIR, "transport", "stations-44.csv")
        count = import_csv_table(con, "stations_transport", transport_path, delim=';')
        print(f"   -> {count:,} stations insérées.\n")

        # 8. PEB SERVITUDES
        print("=" * 60)
        print("8. Chargement des PEB (CSV + GeoJSON)")
        print("=" * 60)
        peb_csv_path = os.path.join(DATA_DIR, "peb", "peb-44.csv")
        count = import_csv_table(con, "peb_servitudes", peb_csv_path, delim=';', mappings={'partition_sup': '"partition"'})
        
        peb_geojson_path = os.path.join(DATA_DIR, "peb", "peb-44.geojson")
        if os.path.exists(peb_geojson_path):
            with open(peb_geojson_path, "r", encoding="utf-8") as f:
                peb_geojson = json.load(f)
            for feat in peb_geojson.get("features", []):
                props = feat.get("properties", {})
                geom = feat.get("geometry")
                gid = props.get("gid")
                if gid and geom:
                    con.execute(
                        "UPDATE peb_servitudes SET geometrie_geojson = ? WHERE gid = ?",
                        [json.dumps(geom), gid],
                    )
        print(f"   -> {count:,} servitudes PEB insérées et géométries mappées.\n")

        # 9. INSEE COMMUNES 2021
        print("=" * 60)
        print("9. Chargement INSEE communes 2021")
        print("=" * 60)
        insee_path = os.path.join(DATA_DIR, "insee", "insee_communes_44_2021.csv")
        count = import_csv_table(con, "insee_communes_2021", insee_path, delim=';', decimal_separator=',', nullstr='s')
        print(f"   -> {count:,} communes INSEE 2021 insérées.\n")

        # 10. INSEE COMMUNES 2021 COMPLET (EAV)
        print("=" * 60)
        print("10. Chargement INSEE communes 2021 complet (EAV)")
        print("=" * 60)
        count = import_eav_table(con, "insee_communes_2021_complet", insee_path, delim=';', nullstr='s')
        print(f"   -> {count:,} lignes EAV générées.\n")

        # 11. INSEE COMMUNES 2023
        print("=" * 60)
        print("11. Chargement INSEE communes 2023")
        print("=" * 60)
        insee_2023_path = os.path.join(DATA_DIR, "old_insee", "insee_communes_44_2023.csv")
        count = import_csv_table(con, "insee_communes_2023", insee_2023_path, delim=';')
        print(f"   -> {count:,} communes INSEE 2023 insérées.\n")

        # 12. FILOSOFI 2023 BRUT
        print("=" * 60)
        print("12. Chargement FILOSOFI 2023 brut")
        print("=" * 60)
        filo_2023_path = os.path.join(DATA_DIR, "old_insee", "DS_FILOSOFI_CC_2023_data.csv")
        count = import_csv_table(con, "filosofi_2023_data", filo_2023_path, delim=';')
        print(f"   -> {count:,} lignes FILOSOFI 2023 insérées.\n")

        # 13. FILO 2021 - Pivot EAV
        print("=" * 60)
        print("13. Chargement des fichiers FILO 2021 (EAV)")
        print("=" * 60)
        filo_files = {
            "filo2021_dec_com":             "FILO2021_DEC_COM.csv",
            "filo2021_dec_pauvres_com":      "FILO2021_DEC_PAUVRES_COM.csv",
            "filo2021_disp_com":            "FILO2021_DISP_COM.csv",
            "filo2021_disp_pauvres_com":     "FILO2021_DISP_PAUVRES_COM.csv",
            "filo2021_trdeciles_dec_com":    "FILO2021_TRDECILES_DEC_COM.csv",
            "filo2021_trdeciles_disp_com":   "FILO2021_TRDECILES_DISP_COM.csv",
        }
        for table_name, filename in filo_files.items():
            filepath = os.path.join(DATA_DIR, "old_insee", filename)
            count = import_eav_table(con, table_name, filepath, delim=';', nullstr='s')
            print(f"   -> {table_name}: {count:,} lignes EAV insérées.")
        print()

        con.execute("COMMIT;")
        print("[OK] Transaction validée avec succès.\n")

    except Exception as e:
        con.execute("ROLLBACK;")
        print(f"[ERREUR CRITIQUE] Annulation des chargements (ROLLBACK) suite à : {e}")
        con.close()
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Résumé et Métriques finalisées
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES OBJETS CHARGÉS DANS DUCKDB")
    print("=" * 60)

    tables = con.execute("SELECT table_name FROM duckdb_tables() WHERE schema_name = 'main' ORDER BY table_name").fetchall()
    print(f"\n{'Table cible SQL':<35} {'Lignes injectées':>15}")
    print("-" * 55)
    for (table_name,) in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"  {table_name:<33} {count:>15,}")

    views = con.execute("SELECT view_name FROM duckdb_views() WHERE schema_name = 'main' ORDER BY view_name").fetchall()
    print(f"\nVues fonctionnelles créées : {len(views)}")
    for (v,) in views:
        print(f"  - {v}")

    con.close()
    print(f"\n[OK] Base DuckDB '{DB_PATH}' disponible et synchronisée !")

if __name__ == "__main__":
    main()