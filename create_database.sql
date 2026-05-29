-- ===========================================================================
-- create_database.sql
-- Structure de la base de données SAE-601 Nantes
-- Schéma relationnel : tables, index et vues
-- ===========================================================================


-- Suppression des tables existantes (ordre inverse des dépendances)
DROP VIEW IF EXISTS vue_proximites;
DROP VIEW IF EXISTS vue_dpe_commune;
DROP VIEW IF EXISTS vue_stats_commune;
DROP VIEW IF EXISTS vue_dvf_complet;

DROP TABLE IF EXISTS dvf_enriched;
DROP TABLE IF EXISTS dvf_mutations;
DROP TABLE IF EXISTS dpe_logements;
DROP TABLE IF EXISTS adresses_ban;
DROP TABLE IF EXISTS ecoles;
DROP TABLE IF EXISTS stations_transport;
DROP TABLE IF EXISTS peb_servitudes;
DROP TABLE IF EXISTS insee_communes_2021;
DROP TABLE IF EXISTS communes;


-- ===========================================================================
-- 1. COMMUNES (source : admin/communes-44.geojson)
--    Chargé depuis Python car nécessite un parsing JSON spécifique
-- ===========================================================================
CREATE TABLE communes (
    code_commune    VARCHAR(5) PRIMARY KEY,
    nom             VARCHAR(255) NOT NULL,
    geometrie_type  VARCHAR(50),
    geometrie_json  TEXT
);

CREATE INDEX idx_communes_code ON communes(code_commune);


-- ===========================================================================
-- 2. ADRESSES BAN (source : ban/adresses-44.csv, séparateur: ;)
--    Base Adresse Nationale - département 44
-- ===========================================================================
CREATE TABLE adresses_ban AS
SELECT * FROM read_csv('data/ban/adresses-44.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

CREATE INDEX idx_ban_code_insee ON adresses_ban(code_insee);
CREATE INDEX idx_ban_code_postal ON adresses_ban(code_postal);
CREATE INDEX idx_ban_coords ON adresses_ban(lat, lon);


-- ===========================================================================
-- 3. DPE LOGEMENTS (source : dpe/dpe-logements-existants-44.csv, séparateur: ,)
--    Diagnostic de Performance Énergétique
-- ===========================================================================
CREATE TABLE dpe_logements AS
SELECT * FROM read_csv('data/dpe/dpe-logements-existants-44.csv',
    delim = ',',
    header = true,
    auto_detect = true,
    ignore_errors = true,
    quote = '"',
    strict_mode = false
);

CREATE INDEX idx_dpe_etiquette ON dpe_logements(etiquette_dpe);
CREATE INDEX idx_dpe_code_insee ON dpe_logements(code_insee_ban);
CREATE INDEX idx_dpe_commune ON dpe_logements(nom_commune_ban);


-- ===========================================================================
-- 4. DVF MUTATIONS BRUTES (source : dvf/dvf-2025-dept44.csv, séparateur: ;)
--    Demandes de Valeurs Foncières 2025 - département 44
-- ===========================================================================
CREATE TABLE dvf_mutations AS
SELECT * FROM read_csv('data/dvf/dvf-2025-dept44.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

CREATE INDEX idx_dvf_date ON dvf_mutations("Date mutation");
CREATE INDEX idx_dvf_commune ON dvf_mutations("Commune");
CREATE INDEX idx_dvf_type_local ON dvf_mutations("Type local");


-- ===========================================================================
-- 5. DVF ENRICHI (source : dvf/dvf_enriched_dept44.csv, séparateur: ;)
--    Données DVF enrichies par le pipeline recreate_data.py
-- ===========================================================================
CREATE TABLE dvf_enriched AS
SELECT * FROM read_csv('data/dvf/dvf_enriched_dept44.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

CREATE INDEX idx_dvfe_code_insee ON dvf_enriched(code_insee);
CREATE INDEX idx_dvfe_type ON dvf_enriched(type_bien);
CREATE INDEX idx_dvfe_dpe ON dvf_enriched(dpe_classe);
CREATE INDEX idx_dvfe_coords ON dvf_enriched(lat, lon);


-- ===========================================================================
-- 6. ECOLES (source : ecoles/ecoles-44.csv, séparateur: ;)
--    Écoles issues d'OpenStreetMap via Overpass API
-- ===========================================================================
CREATE TABLE ecoles AS
SELECT * FROM read_csv('data/ecoles/ecoles-44.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

CREATE INDEX idx_ecoles_coords ON ecoles(lat, lon);


-- ===========================================================================
-- 7. STATIONS TRANSPORT (source : transport/stations-44.csv, séparateur: ;)
--    Gares et arrêts de transport issues d'OpenStreetMap
-- ===========================================================================
CREATE TABLE stations_transport AS
SELECT * FROM read_csv('data/transport/stations-44.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

CREATE INDEX idx_stations_coords ON stations_transport(lat, lon);


-- ===========================================================================
-- 8. PEB SERVITUDES (source : peb/peb-44.csv, séparateur: ;)
--    Plans d'Exposition au Bruit - servitudes aéronautiques
--    La géométrie GeoJSON est ajoutée depuis Python
-- ===========================================================================
CREATE TABLE peb_servitudes AS
SELECT * FROM read_csv('data/peb/peb-44.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

ALTER TABLE peb_servitudes ADD COLUMN geometrie_json TEXT;

CREATE INDEX idx_peb_categorie ON peb_servitudes(categorie);


-- ===========================================================================
-- 9. INSEE COMMUNES 2021 (source : insee/insee_communes_44_2021.csv, séparateur: ;)
--    Données consolidées FILO 2021 - indicateurs par commune dept 44
-- ===========================================================================
CREATE TABLE insee_communes_2021 AS
SELECT * FROM read_csv('data/insee/insee_communes_44_2021.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

CREATE INDEX idx_insee21_codgeo ON insee_communes_2021(CODGEO);
