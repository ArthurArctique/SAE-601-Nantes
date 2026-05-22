import duckdb
import json
import os
import sys
import shutil

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = "sae601_nantes.duckdb"
DATA_DIR = "data"


def main():
    # Supprimer l'ancienne base et son fichier WAL s'ils existent
    for path in [DB_PATH, f"{DB_PATH}.wal"]:
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"[INFO] Ancien fichier '{path}' supprimé.")
            except Exception as e:
                print(f"[ATTENTION] Impossible de supprimer {path} : {e}")
                print("[INFO] Fermez tout logiciel (VS Code, DBeaver) utilisant la base et relancez.")
                sys.exit(1)

    # Connexion directe au fichier DuckDB final (évite les bugs d'export/import)
    con = duckdb.connect(DB_PATH)
    print(f"[INFO] Fichier DuckDB '{DB_PATH}' initialisé avec succès.\n")

    # -----------------------------------------------------------------------
    # 1. COMMUNES (GeoJSON -> table relationnelle)
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("1. Chargement des communes (GeoJSON)")
    print("=" * 60)

    geojson_path = os.path.join(DATA_DIR, "admin", "communes-44.geojson")
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    con.execute("""
        CREATE TABLE communes (
            code_commune    VARCHAR PRIMARY KEY,
            nom             VARCHAR NOT NULL,
            geometrie_type  VARCHAR,
            geometrie_json  VARCHAR
        )
    """)

    features = geojson.get("features", [])
    for feat in features:
        props = feat.get("properties", {})
        geom = feat.get("geometry")
        con.execute(
            "INSERT INTO communes VALUES (?, ?, ?, ?)",
            [
                props.get("code"),
                props.get("nom"),
                geom.get("type") if geom else None,
                json.dumps(geom) if geom else None,
            ],
        )
    print(f"   -> {len(features)} communes insérées.\n")

    # -----------------------------------------------------------------------
    # 2. ADRESSES BAN (CSV ;)
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("2. Chargement des adresses BAN")
    print("=" * 60)

    ban_path = os.path.join(DATA_DIR, "ban", "adresses-44.csv")
    con.execute(f"""
        CREATE TABLE adresses_ban AS
        SELECT * FROM read_csv('{ban_path}',
            delim = ';',
            header = true,
            auto_detect = true,
            ignore_errors = true
        )
    """)
    count = con.execute("SELECT COUNT(*) FROM adresses_ban").fetchone()[0]
    print(f"   -> {count:,} adresses insérées.\n")

    # -----------------------------------------------------------------------
    # 3. DPE LOGEMENTS (CSV ,)
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("3. Chargement des DPE logements")
    print("=" * 60)

    dpe_path = os.path.join(DATA_DIR, "dpe", "dpe-logements-existants-44.csv")
    con.execute(f"""
        CREATE TABLE dpe_logements AS
        SELECT * FROM read_csv('{dpe_path}',
            delim = ',',
            header = true,
            auto_detect = true,
            ignore_errors = true,
            quote = '"',
            strict_mode = false
        )
    """)
    count = con.execute("SELECT COUNT(*) FROM dpe_logements").fetchone()[0]
    print(f"   -> {count:,} DPE insérés.\n")

    # -----------------------------------------------------------------------
    # 4. DVF MUTATIONS BRUTES (CSV ;)
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("4. Chargement des mutations DVF brutes")
    print("=" * 60)

    dvf_path = os.path.join(DATA_DIR, "dvf", "dvf-2025-dept44.csv")
    con.execute(f"""
        CREATE TABLE dvf_mutations AS
        SELECT * FROM read_csv('{dvf_path}',
            delim = ';',
            header = true,
            auto_detect = true,
            ignore_errors = true
        )
    """)
    count = con.execute("SELECT COUNT(*) FROM dvf_mutations").fetchone()[0]
    print(f"   -> {count:,} mutations insérées.\n")

    # -----------------------------------------------------------------------
    # 5. DVF ENRICHI (CSV ;)
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("5. Chargement du DVF enrichi")
    print("=" * 60)

    dvf_enr_path = os.path.join(DATA_DIR, "dvf", "dvf_enriched_dept44.csv")
    con.execute(f"""
        CREATE TABLE dvf_enriched AS
        SELECT * FROM read_csv('{dvf_enr_path}',
            delim = ';',
            header = true,
            auto_detect = true,
            ignore_errors = true
        )
    """)
    count = con.execute("SELECT COUNT(*) FROM dvf_enriched").fetchone()[0]
    print(f"   -> {count:,} transactions enrichies insérées.\n")

    # -----------------------------------------------------------------------
    # 6. ECOLES (CSV ;)
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("6. Chargement des écoles")
    print("=" * 60)

    ecoles_path = os.path.join(DATA_DIR, "ecoles", "ecoles-44.csv")
    if os.path.exists(ecoles_path):
        con.execute(f"""
            CREATE TABLE ecoles AS
            SELECT * FROM read_csv('{ecoles_path}',
                delim = ';',
                header = true,
                auto_detect = true,
                ignore_errors = true
            )
        """)
        count = con.execute("SELECT COUNT(*) FROM ecoles").fetchone()[0]
        print(f"   -> {count:,} écoles insérées.\n")
    else:
        con.execute("CREATE TABLE ecoles (id INT, lat DOUBLE, lon DOUBLE)")
        print("   -> Fichier non trouvé, table vide créée pour les index/vues.\n")

    # -----------------------------------------------------------------------
    # 7. STATIONS TRANSPORT (CSV ;)
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("7. Chargement des stations de transport")
    print("=" * 60)

    transport_path = os.path.join(DATA_DIR, "transport", "stations-44.csv")
    if os.path.exists(transport_path):
        con.execute(f"""
            CREATE TABLE stations_transport AS
            SELECT * FROM read_csv('{transport_path}',
                delim = ';',
                header = true,
                auto_detect = true,
                ignore_errors = true
            )
        """)
        count = con.execute("SELECT COUNT(*) FROM stations_transport").fetchone()[0]
        print(f"   -> {count:,} stations insérées.\n")
    else:
        con.execute("CREATE TABLE stations_transport (id INT, lat DOUBLE, lon DOUBLE)")
        print("   -> Fichier non trouvé, table vide créée pour les index/vues.\n")

    # -----------------------------------------------------------------------
    # 8. PEB SERVITUDES (CSV ; + GeoJSON)
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("8. Chargement des PEB (CSV + GeoJSON)")
    print("=" * 60)

    # Charger depuis le CSV
    peb_csv_path = os.path.join(DATA_DIR, "peb", "peb-44.csv")
    con.execute(f"""
        CREATE TABLE peb_servitudes AS
        SELECT * FROM read_csv('{peb_csv_path}',
            delim = ';',
            header = true,
            auto_detect = true,
            ignore_errors = true
        )
    """)

    # Enrichir avec la géométrie du GeoJSON
    peb_geojson_path = os.path.join(DATA_DIR, "peb", "peb-44.geojson")
    with open(peb_geojson_path, "r", encoding="utf-8") as f:
        peb_geojson = json.load(f)

    # Ajouter la colonne géométrie
    con.execute("ALTER TABLE peb_servitudes ADD COLUMN geometrie_json VARCHAR")
    for feat in peb_geojson.get("features", []):
        props = feat.get("properties", {})
        geom = feat.get("geometry")
        gid = props.get("gid")
        if gid and geom:
            con.execute(
                "UPDATE peb_servitudes SET geometrie_json = ? WHERE gid = ?",
                [json.dumps(geom), gid],
            )

    count = con.execute("SELECT COUNT(*) FROM peb_servitudes").fetchone()[0]
    print(f"   -> {count:,} servitudes PEB insérées.\n")

    # -----------------------------------------------------------------------
    # 9. INSEE COMMUNES 2021 (CSV ;) - Consolidé
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("9. Chargement INSEE communes 2021 (consolidé)")
    print("=" * 60)

    insee_path = os.path.join(DATA_DIR, "insee", "insee_communes_44_2021.csv")
    con.execute(f"""
        CREATE TABLE insee_communes_2021 AS
        SELECT * FROM read_csv('{insee_path}',
            delim = ';',
            header = true,
            auto_detect = true,
            ignore_errors = true
        )
    """)
    count = con.execute("SELECT COUNT(*) FROM insee_communes_2021").fetchone()[0]
    print(f"   -> {count:,} communes INSEE 2021 insérées.\n")

    # -----------------------------------------------------------------------
    # 10. INSEE COMMUNES 2023 (CSV ;) - Pivoté
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("10. Chargement INSEE communes 2023 (pivoté)")
    print("=" * 60)

    insee_2023_path = os.path.join(DATA_DIR, "old_insee", "insee_communes_44_2023.csv")
    if os.path.exists(insee_2023_path):
        con.execute(f"""
            CREATE TABLE insee_communes_2023 AS
            SELECT * FROM read_csv('{insee_2023_path}',
                delim = ';',
                header = true,
                auto_detect = true,
                ignore_errors = true
            )
        """)
        count = con.execute("SELECT COUNT(*) FROM insee_communes_2023").fetchone()[0]
        print(f"   -> {count:,} communes INSEE 2023 insérées.\n")
    else:
        print("   -> Fichier non trouvé, table ignorée.\n")

    # -----------------------------------------------------------------------
    # 11. FILOSOFI 2023 BRUT (CSV ;) - Format long
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("11. Chargement FILOSOFI 2023 brut")
    print("=" * 60)

    filo_2023_path = os.path.join(DATA_DIR, "old_insee", "DS_FILOSOFI_CC_2023_data.csv")
    if os.path.exists(filo_2023_path):
        con.execute(f"""
            CREATE TABLE filosofi_2023_data AS
            SELECT * FROM read_csv('{filo_2023_path}',
                delim = ';',
                header = true,
                auto_detect = true,
                ignore_errors = true
            )
        """)
        count = con.execute("SELECT COUNT(*) FROM filosofi_2023_data").fetchone()[0]
        print(f"   -> {count:,} lignes FILOSOFI 2023 insérées.\n")
    else:
        print("   -> Fichier non trouvé, table ignorée.\n")

    # -----------------------------------------------------------------------
    # 12. FILO 2021 - Tables brutes (CSV ;)
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("12. Chargement des fichiers FILO 2021")
    print("=" * 60)

    filo_files = {
        "filo2021_dec_com":              "FILO2021_DEC_COM.csv",
        "filo2021_dec_pauvres_com":      "FILO2021_DEC_PAUVRES_COM.csv",
        "filo2021_disp_com":             "FILO2021_DISP_COM.csv",
        "filo2021_disp_pauvres_com":     "FILO2021_DISP_PAUVRES_COM.csv",
        "filo2021_trdeciles_dec_com":    "FILO2021_TRDECILES_DEC_COM.csv",
        "filo2021_trdeciles_disp_com":   "FILO2021_TRDECILES_DISP_COM.csv",
    }

    for table_name, filename in filo_files.items():
        filepath = os.path.join(DATA_DIR, "old_insee", filename)
        if os.path.exists(filepath):
            con.execute(f"""
                CREATE TABLE {table_name} AS
                SELECT * FROM read_csv('{filepath}',
                    delim = ';',
                    header = true,
                    auto_detect = true,
                    ignore_errors = true
                )
            """)
            count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            print(f"   -> {table_name}: {count:,} lignes insérées.")
        else:
            print(f"   -> {filename} non trouvé, ignoré.")

    print()

    # ===================================================================
    # MODÈLE RELATIONNEL : Ajout des contraintes et index
    # ===================================================================
    print("=" * 60)
    print("13. Mise en place du modèle relationnel")
    print("=" * 60)

    print("   Création des index...")

    # Communes
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_communes_pk ON communes(code_commune)")

    # Adresses BAN
    con.execute("CREATE INDEX IF NOT EXISTS idx_ban_code_insee ON adresses_ban(code_insee)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_ban_code_postal ON adresses_ban(code_postal)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_ban_coords ON adresses_ban(lat, lon)")

    # DPE
    con.execute("CREATE INDEX IF NOT EXISTS idx_dpe_code_insee ON dpe_logements(code_insee_ban)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_dpe_etiquette ON dpe_logements(etiquette_dpe)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_dpe_commune ON dpe_logements(nom_commune_ban)")

    # DVF mutations
    con.execute("CREATE INDEX IF NOT EXISTS idx_dvf_commune ON dvf_mutations(Commune)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_dvf_type ON dvf_mutations(\"Type local\")")
    con.execute("CREATE INDEX IF NOT EXISTS idx_dvf_date ON dvf_mutations(\"Date mutation\")")

    # DVF enrichi
    con.execute("CREATE INDEX IF NOT EXISTS idx_dvfe_code_insee ON dvf_enriched(code_insee)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_dvfe_type ON dvf_enriched(type_bien)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_dvfe_dpe ON dvf_enriched(dpe_classe)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_dvfe_coords ON dvf_enriched(lat, lon)")

    # Ecoles
    con.execute("CREATE INDEX IF NOT EXISTS idx_ecoles_coords ON ecoles(lat, lon)")

    # Stations transport
    con.execute("CREATE INDEX IF NOT EXISTS idx_stations_coords ON stations_transport(lat, lon)")

    # PEB
    con.execute("CREATE INDEX IF NOT EXISTS idx_peb_categorie ON peb_servitudes(categorie)")

    # INSEE 2021
    con.execute("CREATE INDEX IF NOT EXISTS idx_insee21_codgeo ON insee_communes_2021(CODGEO)")

    print("   -> Index créés avec succès.")

    # ===================================================================
    # VUES RELATIONNELLES
    # ===================================================================
    print("\n   Création des vues relationnelles...")

    # Vue 1 : DVF enrichi + données communales
    con.execute("""
        CREATE OR REPLACE VIEW vue_dvf_complet AS
        SELECT
            e.*,
            c.nom                   AS nom_commune_officiel,
            c.geometrie_type        AS type_geometrie_commune,
            i.Q221                  AS revenu_median_2021,
            i.GI21                  AS indice_gini_2021,
            i.PACT21                AS part_activite_2021,
            i.PPEN21                AS part_pensions_2021,
            i.PCHO21                AS part_chomage_2021
        FROM dvf_enriched e
        LEFT JOIN communes c
            ON e.code_insee = c.code_commune
        LEFT JOIN insee_communes_2021 i
            ON e.code_insee = i.CODGEO
    """)

    # Vue 2 : Statistiques par commune
    con.execute("""
        CREATE OR REPLACE VIEW vue_stats_commune AS
        SELECT
            c.code_commune,
            c.nom,
            COUNT(e.rowid)                                              AS nb_transactions,
            ROUND(AVG(e.prix), 2)                                       AS prix_moyen,
            ROUND(MEDIAN(e.prix), 2)                                    AS prix_median,
            ROUND(AVG(e.prix_m2), 2)                                    AS prix_m2_moyen,
            ROUND(AVG(e.surface), 1)                                    AS surface_moyenne,
            ROUND(AVG(e.pieces), 1)                                     AS pieces_moyennes,
            i.Q221                                                      AS revenu_median,
            i.GI21                                                      AS indice_gini,
            COUNT(CASE WHEN e.dpe_classe IN ('A','B') THEN 1 END) AS nb_dpe_ab,
            COUNT(CASE WHEN e.dpe_classe IN ('F','G') THEN 1 END) AS nb_dpe_fg
        FROM communes c
        LEFT JOIN dvf_enriched e
            ON c.code_commune = e.code_insee
        LEFT JOIN insee_communes_2021 i
            ON c.code_commune = i.CODGEO
        GROUP BY c.code_commune, c.nom, i.Q221, i.GI21
    """)

    # Vue 3 : Répartition DPE par commune
    con.execute("""
        CREATE OR REPLACE VIEW vue_dpe_par_commune AS
        SELECT
            code_insee_ban          AS code_commune,
            nom_commune_ban         AS commune,
            etiquette_dpe,
            COUNT(*)                AS nombre_logements,
            ROUND(AVG(conso_5_usages_par_m2_ep), 1) AS conso_moyenne_m2
        FROM dpe_logements
        WHERE etiquette_dpe IS NOT NULL
        GROUP BY code_insee_ban, nom_commune_ban, etiquette_dpe
        ORDER BY code_insee_ban, etiquette_dpe
    """)

    # Vue 4 : Proximité POI par transaction
    con.execute("""
        CREATE OR REPLACE VIEW vue_proximites AS
        SELECT
            e.code_insee,
            e.nom_commune,
            e.adresse_normalisee,
            e.prix,
            e.prix_m2,
            e.type_bien,
            e.dpe_classe,
            e.distance_ecole_m,
            e.nom_ecole_proche,
            e.distance_transport_m,
            e.nom_transport_proche,
            e.exposition_aeroport_peb,
            e.insee_mediane_revenu
        FROM dvf_enriched e
        WHERE e.lat IS NOT NULL AND e.lon IS NOT NULL
    """)

    print("   -> 4 vues créées avec succès.")

    # ===================================================================
    # RÉSUMÉ FINAL
    # ===================================================================
    print("\n" + "=" * 60)
    print("RÉSUMÉ DE LA BASE DE DONNÉES")
    print("=" * 60)

    tables = con.execute("""
        SELECT table_name
        FROM duckdb_tables()
        WHERE schema_name = 'main'
        ORDER BY table_name
    """).fetchall()

    print(f"\n{'Table':<35} {'Lignes':>12}")
    print("-" * 50)
    for (table_name,) in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"  {table_name:<33} {count:>12,}")

    views = con.execute("""
        SELECT view_name
        FROM duckdb_views()
        WHERE schema_name = 'main'
        ORDER BY view_name
    """).fetchall()

    print(f"\nVues créées : {len(views)}")
    for (v,) in views:
        print(f"  - {v}")

    # ===================================================================
    # SCHÉMA RELATIONNEL
    # ===================================================================
    print("\n" + "=" * 60)
    print("MODÈLE RELATIONNEL")
    print("=" * 60)
    print("")
    print("  communes (PK: code_commune)")
    print("    |")
    print("    +---> dvf_enriched (FK: code_insee)")
    print("    +---> insee_communes_2021 (FK: CODGEO)")
    print("    +---> adresses_ban (FK: code_insee)")
    print("    +---> dpe_logements (FK: code_insee_ban)")
    print("")
    print("  dvf_enriched <--- jointure spatiale ---> ecoles")
    print("  dvf_enriched <--- jointure spatiale ---> stations_transport")
    print("  dvf_enriched <--- jointure spatiale ---> peb_servitudes")
    print("")

    # Fermeture de la connexion propre (les données restent écrites sur le disque)
    con.close()
    print(f"\n[OK] Base DuckDB '{DB_PATH}' synchronisée et finalisée avec succès !")


if __name__ == "__main__":
    main()