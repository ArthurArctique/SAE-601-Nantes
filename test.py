import duckdb
import os
import json

# ===============================
# CONFIG (CHEMIN ROBUSTE)
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(BASE_DIR, "sae601_nantes.duckdb")

# ===============================
# RESET BASE
# ===============================
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

con = duckdb.connect(DB_PATH)

# ===============================
# OPTIMISATION
# ===============================
con.execute("PRAGMA threads=4;")
con.execute("PRAGMA memory_limit='4GB';")

print("🚀 Création de la base DuckDB...")

# ===============================
# 1. COMMUNES (GeoJSON)
# ===============================
print("1. Communes...")

geojson_path = os.path.join(DATA_DIR, "admin", "communes-44.geojson")

con.execute("""
CREATE TABLE communes (
    code_commune VARCHAR,
    nom VARCHAR,
    geometrie_geojson JSON
)
""")

if os.path.exists(geojson_path):
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    for feat in geojson.get("features", []):
        props = feat.get("properties", {})
        geom = feat.get("geometry")

        con.execute("""
            INSERT INTO communes VALUES (?, ?, ?)
        """, [
            props.get("code"),
            props.get("nom"),
            json.dumps(geom) if geom else None
        ])
else:
    print("⚠️ GeoJSON communes introuvable")

# ===============================
# 2. BAN
# ===============================
print("2. BAN...")

ban_path = os.path.join(DATA_DIR, "ban", "adresses-44.csv")

if os.path.exists(ban_path):
    con.execute(f"""
    CREATE TABLE adresses_ban AS
    SELECT *
    FROM read_csv_auto('{ban_path}', delim=';', sample_size=-1)
    """)
else:
    print("⚠️ BAN introuvable")

# ===============================
# 3. DPE
# ===============================
print("3. DPE...")

dpe_path = os.path.join(DATA_DIR, "dpe", "dpe-logements-existants-44.csv")

if os.path.exists(dpe_path):
    con.execute(f"""
    CREATE TABLE dpe_logements AS
    SELECT *
    FROM read_csv_auto('{dpe_path}', sample_size=-1)
    """)
else:
    print("⚠️ DPE introuvable")

# ===============================
# 4. DVF
# ===============================
print("4. DVF...")

dvf_path = os.path.join(DATA_DIR, "dvf", "dvf-2025-dept44.csv")

if os.path.exists(dvf_path):
    con.execute(f"""
    CREATE TABLE dvf_mutations AS
    SELECT *
    FROM read_csv_auto('{dvf_path}', delim=';', sample_size=-1)
    """)
else:
    print("⚠️ DVF introuvable")

# ===============================
# 5. DVF ENRICHI
# ===============================
print("5. DVF enrichi...")

dvf_enr_path = os.path.join(DATA_DIR, "dvf", "dvf_enriched_dept44.csv")

if os.path.exists(dvf_enr_path):
    con.execute(f"""
    CREATE TABLE dvf_enriched AS
    SELECT *
    FROM read_csv_auto('{dvf_enr_path}', delim=';', sample_size=-1)
    """)
else:
    print("⚠️ DVF enrichi introuvable")

# ===============================
# 6. ECOLES
# ===============================
print("6. Ecoles...")

ecoles_path = os.path.join(DATA_DIR, "ecoles", "ecoles-44.csv")

if os.path.exists(ecoles_path):
    con.execute(f"""
    CREATE TABLE ecoles AS
    SELECT *
    FROM read_csv_auto('{ecoles_path}', delim=';', sample_size=-1)
    """)
else:
    print("⚠️ Ecoles introuvables")

# ===============================
# 7. TRANSPORT
# ===============================
print("7. Transport...")

transport_path = os.path.join(DATA_DIR, "transport", "stations-44.csv")

if os.path.exists(transport_path):
    con.execute(f"""
    CREATE TABLE stations_transport AS
    SELECT *
    FROM read_csv_auto('{transport_path}', delim=';', sample_size=-1)
    """)
else:
    print("⚠️ Transport introuvable")

# ===============================
# 8. PEB (CORRIGÉ)
# ===============================
print("8. PEB...")

peb_csv_path = os.path.join(DATA_DIR, "peb", "peb-44.csv")

if os.path.exists(peb_csv_path):
    con.execute(f"""
    CREATE TABLE peb_servitudes AS
    SELECT *,
           NULL::JSON AS geometrie_geojson
    FROM read_csv_auto('{peb_csv_path}', delim=';', sample_size=-1)
    """)
else:
    print("⚠️ PEB CSV introuvable")

# Ajout géométrie GeoJSON
peb_geojson_path = os.path.join(DATA_DIR, "peb", "peb-44.geojson")

if os.path.exists(peb_geojson_path):
    with open(peb_geojson_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    for feat in geojson.get("features", []):
        gid = feat.get("properties", {}).get("gid")
        geom = json.dumps(feat.get("geometry"))

        if gid:
            con.execute("""
                UPDATE peb_servitudes
                SET geometrie_geojson = ?
                WHERE gid = ?
            """, [geom, gid])

# ===============================
# 9. INSEE 2021
# ===============================
print("9. INSEE 2021...")

insee_path = os.path.join(DATA_DIR, "insee", "insee_communes_44_2021.csv")

if os.path.exists(insee_path):
    con.execute(f"""
    CREATE TABLE insee_communes_2021 AS
    SELECT *
    FROM read_csv_auto('{insee_path}', delim=';', sample_size=-1)
    """)
else:
    print("⚠️ INSEE 2021 introuvable")

# ===============================
# 10. INSEE 2023
# ===============================
print("10. INSEE 2023...")

insee_2023_path = os.path.join(DATA_DIR, "old_insee", "insee_communes_44_2023.csv")

if os.path.exists(insee_2023_path):
    con.execute(f"""
    CREATE TABLE insee_communes_2023 AS
    SELECT *
    FROM read_csv_auto('{insee_2023_path}', delim=';', sample_size=-1)
    """)
else:
    print("⚠️ INSEE 2023 introuvable")

# ===============================
# 11. VUE FINALE
# ===============================
print("11. Vue finale...")

con.execute("""
CREATE VIEW vue_dvf_complet AS
SELECT
    e.*,
    c.nom AS nom_commune_officiel,
    i.q221 AS revenu_median
FROM dvf_enriched e
LEFT JOIN communes c ON e.code_insee = c.code_commune
LEFT JOIN insee_communes_2021 i ON e.code_insee = i.codgeo
""")

# ===============================
# 12. RESUME
# ===============================
print("\n📊 Résumé :")

tables = con.execute("""
SELECT table_name 
FROM duckdb_tables()
WHERE schema_name = 'main'
""").fetchall()

for (t,) in tables:
    count = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t:<30} {count:,}")

con.close()

print("\n✅ Base DuckDB prête sans erreur !")