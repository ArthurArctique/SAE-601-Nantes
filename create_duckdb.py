import duckdb
import json
import os
import sys

DB_PATH = "sae601_nantes.duckdb"
SQL_DIR = "."
DATA_DIR = "data"


def read_sql(filename):
    """Lit et retourne le contenu d'un fichier SQL."""
    path = os.path.join(SQL_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def split_sql_statements(sql):
    """Découpe un fichier SQL en instructions individuelles.
    Gère les ; dans les chaînes et les commentaires SQL."""
    statements = []
    current = []
    in_single_quote = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        # Commentaires en ligne : on les copie tels quels sans analyser les quotes
        if not in_single_quote and ch == '-' and i + 1 < len(sql) and sql[i + 1] == '-':
            end = sql.find('\n', i)
            if end == -1:
                current.append(sql[i:])
                break
            current.append(sql[i:end + 1])
            i = end + 1
            continue
        if ch == "'" and not in_single_quote:
            in_single_quote = True
            current.append(ch)
        elif ch == "'" and in_single_quote:
            if i + 1 < len(sql) and sql[i + 1] == "'":
                current.append("''")
                i += 1
            else:
                in_single_quote = False
            current.append(ch)
        elif ch == ";" and not in_single_quote:
            stmt = "".join(current).strip()
            if stmt:
                lines = [l for l in stmt.split("\n") if not l.strip().startswith("--")]
                if any(l.strip() for l in lines):
                    statements.append(stmt)
            current = []
        else:
            current.append(ch)
        i += 1
    stmt = "".join(current).strip()
    if stmt:
        lines = [l for l in stmt.split("\n") if not l.strip().startswith("--")]
        if any(l.strip() for l in lines):
            statements.append(stmt)
    return statements


def execute_sql_file(con, filename):
    """Exécute toutes les instructions d'un fichier SQL."""
    sql = read_sql(filename)
    statements = split_sql_statements(sql)
    for stmt in statements:
        con.execute(stmt)


def load_communes(con):
    """Charge les communes depuis le GeoJSON (nécessite du parsing Python)."""
    geojson_path = os.path.join(DATA_DIR, "admin", "communes-44.geojson")
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    rows = []
    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry")
        rows.append((
            props.get("code"),
            props.get("nom"),
            json.dumps(geom) if geom else None,
        ))
    con.executemany("INSERT INTO dim_communes VALUES (?, ?, ?)", rows)
    return len(features)


def load_peb_geometry(con):
    """Enrichit la table dim_peb avec la géométrie du GeoJSON."""
    peb_geojson_path = os.path.join(DATA_DIR, "peb", "peb-44.geojson")
    with open(peb_geojson_path, "r", encoding="utf-8") as f:
        peb_geojson = json.load(f)

    updated = 0
    for feat in peb_geojson.get("features", []):
        props = feat.get("properties", {})
        geom = feat.get("geometry")
        gid = props.get("gid")
        if gid and geom:
            con.execute(
                "UPDATE dim_peb SET geometrie_json = ? WHERE gid = ?",
                [json.dumps(geom), gid],
            )
            updated += 1
    return updated


def print_summary(con):
    """Affiche le résumé de la base de données."""
    tables = con.execute("""
        SELECT table_name
        FROM duckdb_tables()
        WHERE schema_name = 'main'
        ORDER BY table_name
    """).fetchall()

    print(f"\n{'Table':<35} {'Lignes':>12} {'Colonnes':>10}")
    print("-" * 60)
    for (table_name,) in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        cols = con.execute(f"""
            SELECT COUNT(*)
            FROM duckdb_columns()
            WHERE table_name = '{table_name}'
        """).fetchone()[0]
        print(f"  {table_name:<33} {count:>12,} {cols:>10}")

    views = con.execute("""
        SELECT view_name
        FROM duckdb_views()
        WHERE schema_name = 'main'
        ORDER BY view_name
    """).fetchall()

    print(f"\nVues créées : {len(views)}")
    for (v,) in views:
        print(f"  - {v}")

    print()
    print("  Schéma en étoile :")
    print()
    print("          dim_ban (géocodage : adresse → lat/lon)")
    print("              |")
    print("         dim_communes (PK: code_commune)")
    print("              |")
    print("  dim_insee --+------+------+-- dim_dpe")
    print("  (CODGEO)   |             |  (code_insee_ban)")
    print("              |             |")
    print("         fait_transactions")
    print("        (FK: code_insee, ...)")
    print("              |             |")
    print("  dim_ecoles -+             +- dim_transport")
    print("  (spatiale)  |                (spatiale)")
    print("              |")
    print("           dim_peb")
    print("         (spatiale)")


def main():
    # Supprimer l'ancienne base
    for path in [DB_PATH, f"{DB_PATH}.wal"]:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"[INFO] Ancien fichier '{path}' supprimé.")
            except Exception as e:
                print(f"[ERREUR] Impossible de supprimer {path} : {e}")
                print("[INFO] Fermez tout logiciel utilisant la base et relancez.")
                sys.exit(1)

    con = duckdb.connect(DB_PATH)
    print(f"[INFO] Base DuckDB '{DB_PATH}' initialisée.\n")

    # --- Étape 1 : Structure + chargement CSV (via SQL) ---
    print("=" * 60)
    print("Étape 1 : Exécution de create_database.sql")
    print("         (schéma en étoile : dimensions + table de faits)")
    print("=" * 60)
    execute_sql_file(con, "create_database.sql")
    print("   -> Tables et index créés avec succès.\n")

    # --- Étape 2 : Chargement des communes (GeoJSON, nécessite Python) ---
    print("=" * 60)
    print("Étape 2 : Chargement dim_communes (GeoJSON)")
    print("=" * 60)
    nb_communes = load_communes(con)
    print(f"   -> {nb_communes} communes insérées.\n")

    # --- Étape 3 : Enrichissement PEB avec géométrie GeoJSON ---
    print("=" * 60)
    print("Étape 3 : Enrichissement dim_peb (géométrie GeoJSON)")
    print("=" * 60)
    nb_peb = load_peb_geometry(con)
    print(f"   -> {nb_peb} géométries PEB mises à jour.\n")

    # --- Étape 4 : Création des vues (via SQL) ---
    print("=" * 60)
    print("Étape 4 : Exécution de create_views.sql")
    print("=" * 60)
    execute_sql_file(con, "create_views.sql")
    print("   -> Vues créées avec succès.\n")

    # --- Résumé final ---
    print("=" * 60)
    print("RÉSUMÉ DE LA BASE DE DONNÉES")
    print("=" * 60)
    print_summary(con)

    con.close()
    print(f"\n[OK] Base DuckDB '{DB_PATH}' finalisée avec succès !")



main()