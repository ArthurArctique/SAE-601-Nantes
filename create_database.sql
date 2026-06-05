-- ===========================================================================
-- create_database.sql
-- Structure de la base de données SAE-601 Nantes
-- Schéma en étoile : table de faits + tables de dimensions
-- ===========================================================================


-- Suppression des vues et tables existantes (ordre inverse des dépendances)
DROP VIEW IF EXISTS vue_proximites;
DROP VIEW IF EXISTS vue_dpe_commune;
DROP VIEW IF EXISTS vue_stats_commune;
DROP VIEW IF EXISTS vue_dvf_complet;

DROP TABLE IF EXISTS fait_transactions;
DROP TABLE IF EXISTS dim_ban;
DROP TABLE IF EXISTS dim_dpe;
DROP TABLE IF EXISTS dim_ecoles;
DROP TABLE IF EXISTS dim_transport;
DROP TABLE IF EXISTS dim_peb;
DROP TABLE IF EXISTS dim_insee;
DROP TABLE IF EXISTS dim_communes;


-- ===========================================================================
-- DIMENSION : COMMUNES (source : admin/communes-44.geojson)
--   Référentiel géographique des communes du département 44
--   Chargé depuis Python car nécessite un parsing GeoJSON spécifique
-- ===========================================================================
CREATE TABLE dim_communes (
    code_commune    VARCHAR(5) PRIMARY KEY,
    nom             VARCHAR(255) NOT NULL,
    geometrie_json  TEXT
);

CREATE INDEX idx_dim_communes_code ON dim_communes(code_commune);


-- ===========================================================================
-- DIMENSION : ADRESSES BAN (source : ban/adresses-44.csv)
--   Base Adresse Nationale — référentiel d'adresses global
--   Conservée pour cohérence (DPE, etc.) mais le géocodage DVF 
--   est désormais fait en amont via l'API BAN (99.8% de succès).
--   Source : 23 colonnes, sélection réduite à 9
-- ===========================================================================
CREATE TABLE dim_ban AS
SELECT
    id              AS id_ban,
    numero,
    rep,
    nom_voie,
    code_postal,
    code_insee,
    nom_commune,
    lon,
    lat
FROM read_csv('data/ban/adresses-44.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

CREATE INDEX idx_dim_ban_code_insee ON dim_ban(code_insee);
CREATE INDEX idx_dim_ban_code_postal ON dim_ban(code_postal);
CREATE INDEX idx_dim_ban_coords ON dim_ban(lat, lon);
CREATE INDEX idx_dim_ban_voie ON dim_ban(nom_voie);


-- ===========================================================================
-- DIMENSION : DPE LOGEMENTS (source : dpe/dpe-logements-existants-44.csv)
--   Diagnostic de Performance Énergétique — colonnes utiles uniquement
--   Source : ~226 colonnes, sélection réduite à 12
-- ===========================================================================
CREATE TABLE dim_dpe AS
SELECT
    "numero_dpe",
    "etiquette_dpe",
    "etiquette_ges",
    "type_batiment",
    "annee_construction",
    "surface_habitable_logement",
    "conso_5_usages_par_m2_ep",
    "emission_ges_5_usages par_m2"      AS emission_ges_par_m2,
    "code_insee_ban",
    "nom_commune_ban",
    "code_postal_ban",
    "coordonnee_cartographique_x_ban"   AS x_ban,
    "coordonnee_cartographique_y_ban"   AS y_ban
FROM read_csv('data/dpe/dpe-logements-existants-44.csv',
    delim = ',',
    header = true,
    auto_detect = true,
    ignore_errors = true,
    quote = '"',
    strict_mode = false
);

CREATE INDEX idx_dim_dpe_etiquette ON dim_dpe(etiquette_dpe);
CREATE INDEX idx_dim_dpe_code_insee ON dim_dpe(code_insee_ban);
CREATE INDEX idx_dim_dpe_commune ON dim_dpe(nom_commune_ban);


-- ===========================================================================
-- DIMENSION : ECOLES (source : ecoles/ecoles-44.csv)
--   Écoles issues d'OpenStreetMap via Overpass API
-- ===========================================================================
CREATE TABLE dim_ecoles AS
SELECT * FROM read_csv('data/ecoles/ecoles-44.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

CREATE INDEX idx_dim_ecoles_coords ON dim_ecoles(lat, lon);


-- ===========================================================================
-- DIMENSION : STATIONS TRANSPORT (source : transport/stations-44.csv)
--   Gares et arrêts de transport issues d'OpenStreetMap via Overpass API
-- ===========================================================================
CREATE TABLE dim_transport AS
SELECT * FROM read_csv('data/transport/stations-44.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

CREATE INDEX idx_dim_transport_coords ON dim_transport(lat, lon);


-- ===========================================================================
-- DIMENSION : PEB SERVITUDES (source : peb/peb-44.csv + peb/peb-44.geojson)
--   Plans d'Exposition au Bruit — colonnes utiles uniquement
--   Source : 22 colonnes, sélection réduite à 4 + géométrie via Python
-- ===========================================================================
CREATE TABLE dim_peb AS
SELECT
    gid,
    categorie,
    nomsup,
    descriptio
FROM read_csv('data/peb/peb-44.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

ALTER TABLE dim_peb ADD COLUMN geometrie_json TEXT;

CREATE INDEX idx_dim_peb_gid ON dim_peb(gid);
CREATE INDEX idx_dim_peb_categorie ON dim_peb(categorie);


-- ===========================================================================
-- DIMENSION : INSEE COMMUNES 2021 (source : insee/insee_communes_44_2021.csv)
--   Indicateurs socio-économiques FILO 2021 — agrégats globaux uniquement
--   Source : ~1020 colonnes, sélection réduite à 14
-- ===========================================================================
CREATE TABLE dim_insee AS
SELECT
    CODGEO,
    NBMEN21,                    -- Nombre de ménages fiscaux
    NBPERS21,                   -- Nombre de personnes dans les ménages fiscaux
    NBUC21,                     -- Nombre d'unités de consommation
    Q121,                       -- 1er quartile du revenu disponible (€)
    Q221,                       -- Médiane du revenu disponible (€)
    Q321,                       -- 3e quartile du revenu disponible (€)
    Q3_Q1,                      -- Rapport interquartile (Q3/Q1)
    RD,                         -- Rapport interdécile (D9/D1)
    S80S2021,                   -- Rapport S80/S20
    GI21,                       -- Indice de Gini
    PACT21,                     -- Part des revenus d'activité (%)
    PTSA21,                     -- Part des traitements et salaires (%)
    PCHO21,                     -- Part des indemnités de chômage (%)
    PBEN21,                     -- Part des bénéfices (%)
    PPEN21,                     -- Part des pensions et retraites (%)
    PAUT21,                     -- Part des autres revenus (%)
    PMIMP21,                    -- Part des ménages fiscaux imposés (%)
    PIMPOT21                    -- Part des impôts (%)
FROM read_csv('data/insee/insee_communes_44_2021.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

CREATE INDEX idx_dim_insee_codgeo ON dim_insee(CODGEO);


-- ===========================================================================
-- TABLE DE FAITS : TRANSACTIONS IMMOBILIÈRES DVF ENRICHIES
--   (source : dvf/dvf_enriched_dept44.csv)
--   Table centrale du schéma en étoile (géocodée nativement via API BAN)
--   Chaque ligne = une transaction immobilière enrichie
--   FK : code_insee → dim_communes, dim_insee
-- ===========================================================================
CREATE TABLE fait_transactions AS
SELECT * FROM read_csv('data/dvf/dvf_enriched_dept44.csv',
    delim = ';',
    header = true,
    auto_detect = true,
    ignore_errors = true
);

CREATE INDEX idx_ft_code_insee ON fait_transactions(code_insee);
CREATE INDEX idx_ft_type_bien ON fait_transactions(type_bien);
CREATE INDEX idx_ft_dpe ON fait_transactions(dpe_classe);
CREATE INDEX idx_ft_date ON fait_transactions(date_mutation);
CREATE INDEX idx_ft_coords ON fait_transactions(lat, lon);
