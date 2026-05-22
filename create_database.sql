

-- Suppression des tables existantes (ordre inverse des dépendances)
DROP TABLE IF EXISTS dvf_enriched;
DROP TABLE IF EXISTS dvf_mutations;
DROP TABLE IF EXISTS dpe_logements;
DROP TABLE IF EXISTS adresses_ban;
DROP TABLE IF EXISTS communes;
DROP TABLE IF EXISTS communes_geometrie;
DROP TABLE IF EXISTS ecoles;
DROP TABLE IF EXISTS stations_transport;
DROP TABLE IF EXISTS peb_servitudes;
DROP TABLE IF EXISTS insee_communes_2021;
DROP TABLE IF EXISTS insee_communes_2021_complet;
DROP TABLE IF EXISTS insee_communes_2023;
DROP TABLE IF EXISTS filosofi_2023_data;
DROP TABLE IF EXISTS filo2021_dec_com;
DROP TABLE IF EXISTS filo2021_dec_pauvres_com;
DROP TABLE IF EXISTS filo2021_disp_com;
DROP TABLE IF EXISTS filo2021_disp_pauvres_com;
DROP TABLE IF EXISTS filo2021_trdeciles_dec_com;
DROP TABLE IF EXISTS filo2021_trdeciles_disp_com;


-- ===========================================================================
-- 1. COMMUNES (source : admin/communes-44.geojson)
--    Fichier GeoJSON -> on extrait les propriétés et la géométrie
-- ===========================================================================
CREATE TABLE communes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code_commune    VARCHAR(5) NOT NULL UNIQUE,
    nom             VARCHAR(255) NOT NULL,
    -- La géométrie est stockée en GeoJSON texte pour compatibilité maximale
    -- Pour PostGIS, utiliser le type GEOMETRY(Polygon, 4326) à la place
    geometrie_geojson TEXT
);

-- Index pour recherche rapide par code commune
CREATE INDEX idx_communes_code ON communes(code_commune);


-- ===========================================================================
-- 2. ADRESSES BAN (source : ban/adresses-44.csv, séparateur: ;)
--    Base Adresse Nationale - département 44
-- ===========================================================================
CREATE TABLE adresses_ban (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_ban                      VARCHAR(50),
    id_fantoir                  VARCHAR(50),
    numero                      INTEGER,
    rep                         VARCHAR(20),
    nom_voie                    VARCHAR(255),
    code_postal                 VARCHAR(10),
    code_insee                  VARCHAR(5),
    nom_commune                 VARCHAR(255),
    code_insee_ancienne_commune VARCHAR(5),
    nom_ancienne_commune        VARCHAR(255),
    x                           DOUBLE,
    y                           DOUBLE,
    lon                         DOUBLE,
    lat                         DOUBLE,
    type_position               VARCHAR(50),
    alias                       VARCHAR(255),
    nom_ld                      VARCHAR(255),
    libelle_acheminement        VARCHAR(255),
    nom_afnor                   VARCHAR(255),
    source_position             VARCHAR(50),
    source_nom_voie             VARCHAR(50),
    certification_commune       INTEGER,
    cad_parcelles               TEXT
);

CREATE INDEX idx_ban_code_insee ON adresses_ban(code_insee);
CREATE INDEX idx_ban_code_postal ON adresses_ban(code_postal);
CREATE INDEX idx_ban_nom_commune ON adresses_ban(nom_commune);
CREATE INDEX idx_ban_coords ON adresses_ban(lat, lon);


-- ===========================================================================
-- 3. DPE LOGEMENTS (source : dpe/dpe-logements-existants-44.csv, séparateur: ,)
--    Diagnostic de Performance Énergétique
-- ===========================================================================
CREATE TABLE dpe_logements (
    id                                              INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_dpe                                      VARCHAR(50) UNIQUE,
    date_derniere_modification_dpe                   DATE,
    date_visite_diagnostiqueur                       DATE,
    date_etablissement_dpe                           DATE,
    date_reception_dpe                               DATE,
    date_fin_validite_dpe                            DATE,
    numero_dpe_remplace                              VARCHAR(50),
    numero_dpe_immeuble_associe                      VARCHAR(50),
    id_rnb                                           VARCHAR(50),
    provenance_id_rnb                                VARCHAR(50),
    numero_rpls_logement                             VARCHAR(50),
    numero_immatriculation_copropriete               VARCHAR(50),
    modele_dpe                                       VARCHAR(100),
    version_dpe                                      DECIMAL(5,2),
    methode_application_dpe                          VARCHAR(100),
    etiquette_dpe                                    VARCHAR(2),
    etiquette_ges                                    VARCHAR(2),
    type_batiment                                    VARCHAR(50),
    annee_construction                               INTEGER,
    periode_construction                             VARCHAR(50),
    type_installation_chauffage                      VARCHAR(50),
    type_installation_ecs                            VARCHAR(50),
    hauteur_sous_plafond                             DECIMAL(4,2),
    nombre_appartement                               INTEGER,
    nombre_niveau_immeuble                           INTEGER,
    nombre_niveau_logement                           INTEGER,
    typologie_logement                               VARCHAR(50),
    appartement_non_visite                           INTEGER,
    surface_habitable_immeuble                       DECIMAL(10,2),
    surface_habitable_logement                       DECIMAL(10,2),
    surface_tertiaire_immeuble                       DECIMAL(10,2),
    classe_inertie_batiment                          VARCHAR(50),
    classe_altitude                                  VARCHAR(50),
    zone_climatique                                  VARCHAR(10),
    adresse_ban                                      TEXT,
    numero_voie_ban                                  VARCHAR(20),
    nom_rue_ban                                      VARCHAR(255),
    nom_commune_ban                                  VARCHAR(255),
    code_postal_ban                                  VARCHAR(10),
    code_insee_ban                                   VARCHAR(5),
    code_departement_ban                             VARCHAR(3),
    code_region_ban                                  VARCHAR(3),
    identifiant_ban                                  VARCHAR(50),
    coordonnee_cartographique_x_ban                  DECIMAL(12,2),
    coordonnee_cartographique_y_ban                  DECIMAL(12,2),
    score_ban                                        DECIMAL(4,2),
    statut_geocodage                                 VARCHAR(100),
    adresse_brut                                     TEXT,
    adresse_complete_brut                            TEXT,
    nom_commune_brut                                 VARCHAR(255),
    code_postal_brut                                 VARCHAR(10),
    numero_etage_appartement                         INTEGER,
    position_logement_dans_immeuble                  VARCHAR(100),
    nom_residence                                    VARCHAR(255),
    complement_adresse_batiment                      VARCHAR(255),
    complement_adresse_logement                      VARCHAR(255),
    indicateur_confort_ete                            VARCHAR(50),
    protection_solaire_exterieure                     VARCHAR(50),
    logement_traversant                              VARCHAR(10),
    presence_brasseur_air                            VARCHAR(10),
    inertie_lourde                                   VARCHAR(10),
    isolation_toiture                                VARCHAR(50),
    deperditions_enveloppe                           DECIMAL(10,2),
    deperditions_ponts_thermiques                    DECIMAL(10,2),
    deperditions_murs                                DECIMAL(10,2),
    deperditions_planchers_hauts                     DECIMAL(10,2),
    deperditions_planchers_bas                       DECIMAL(10,2),
    deperditions_portes                              DECIMAL(10,2),
    deperditions_baies_vitrees                       DECIMAL(10,2),
    deperditions_renouvellement_air                  DECIMAL(10,2),
    qualite_isolation_enveloppe                      VARCHAR(50),
    qualite_isolation_murs                           VARCHAR(50),
    qualite_isolation_plancher_haut_comble_amenage   VARCHAR(50),
    qualite_isolation_plancher_haut_comble_perdu     VARCHAR(50),
    qualite_isolation_plancher_haut_toit_terrasse    VARCHAR(50),
    qualite_isolation_plancher_bas                   VARCHAR(50),
    qualite_isolation_menuiseries                    VARCHAR(50),
    ubat_w_par_m2_k                                  DECIMAL(6,3),
    besoin_chauffage                                 DECIMAL(12,2),
    besoin_ecs                                       DECIMAL(12,2),
    besoin_refroidissement                           DECIMAL(12,2),
    apport_interne_saison_chauffe                    DECIMAL(12,2),
    apport_interne_saison_froide                     DECIMAL(12,2),
    apport_solaire_saison_chauffe                    DECIMAL(12,2),
    apport_solaire_saison_froide                     DECIMAL(12,2),
    conso_5_usages_ep                                DECIMAL(12,2),
    conso_5_usages_par_m2_ep                         DECIMAL(10,2),
    conso_chauffage_ep                               DECIMAL(12,2),
    conso_ecs_ep                                     DECIMAL(12,2),
    conso_refroidissement_ep                         DECIMAL(12,2),
    conso_eclairage_ep                               DECIMAL(12,2),
    conso_auxiliaires_ep                              DECIMAL(12,2),
    conso_5_usages_ef                                DECIMAL(12,2),
    conso_5_usages_par_m2_ef                         DECIMAL(10,2),
    conso_chauffage_ef                               DECIMAL(12,2),
    conso_ecs_ef                                     DECIMAL(12,2),
    conso_refroidissement_ef                         DECIMAL(12,2),
    conso_eclairage_ef                               DECIMAL(12,2),
    conso_auxiliaires_ef                              DECIMAL(12,2),
    emission_ges_5_usages                            DECIMAL(12,2),
    emission_ges_5_usages_par_m2                     DECIMAL(10,2),
    emission_ges_chauffage                           DECIMAL(12,2),
    emission_ges_ecs                                 DECIMAL(12,2),
    emission_ges_refroidissement                     DECIMAL(12,2),
    emission_ges_eclairage                           DECIMAL(12,2),
    emission_ges_auxiliaires                          DECIMAL(12,2),
    -- Énergie n°1
    type_energie_n1                                  VARCHAR(100),
    conso_5_usages_ef_energie_n1                     DECIMAL(12,2),
    conso_chauffage_ef_energie_n1                    DECIMAL(12,2),
    conso_ecs_ef_energie_n1                          DECIMAL(12,2),
    cout_total_5_usages_energie_n1                   DECIMAL(12,2),
    cout_chauffage_energie_n1                        DECIMAL(12,2),
    cout_ecs_energie_n1                              DECIMAL(12,2),
    emission_ges_5_usages_energie_n1                 DECIMAL(12,2),
    emission_ges_chauffage_energie_n1                DECIMAL(12,2),
    emission_ges_ecs_energie_n1                      DECIMAL(12,2),
    -- Énergie n°2
    type_energie_n2                                  VARCHAR(100),
    conso_5_usages_ef_energie_n2                     DECIMAL(12,2),
    conso_chauffage_ef_energie_n2                    DECIMAL(12,2),
    conso_ecs_ef_energie_n2                          DECIMAL(12,2),
    cout_total_5_usages_energie_n2                   DECIMAL(12,2),
    cout_chauffage_energie_n2                        DECIMAL(12,2),
    cout_ecs_energie_n2                              DECIMAL(12,2),
    emission_ges_5_usages_energie_n2                 DECIMAL(12,2),
    emission_ges_chauffage_energie_n2                DECIMAL(12,2),
    emission_ges_ecs_energie_n2                      DECIMAL(12,2),
    -- Énergie n°3
    type_energie_n3                                  VARCHAR(100),
    conso_5_usages_ef_energie_n3                     DECIMAL(12,2),
    conso_chauffage_ef_energie_n3                    DECIMAL(12,2),
    conso_ecs_ef_energie_n3                          DECIMAL(12,2),
    cout_total_5_usages_energie_n3                   DECIMAL(12,2),
    cout_chauffage_energie_n3                        DECIMAL(12,2),
    cout_ecs_energie_n3                              DECIMAL(12,2),
    emission_ges_5_usages_energie_n3                 DECIMAL(12,2),
    emission_ges_chauffage_energie_n3                DECIMAL(12,2),
    emission_ges_ecs_energie_n3                      DECIMAL(12,2),
    -- Coûts totaux
    cout_total_5_usages                              DECIMAL(12,2),
    cout_chauffage                                   DECIMAL(12,2),
    cout_ecs                                         DECIMAL(12,2),
    cout_refroidissement                             DECIMAL(12,2),
    cout_eclairage                                   DECIMAL(12,2),
    cout_auxiliaires                                  DECIMAL(12,2),
    -- Chauffage
    type_energie_principale_chauffage                VARCHAR(100),
    type_generateur_chauffage_principal              VARCHAR(255),
    type_installation_chauffage_n1                   VARCHAR(100),
    type_emetteur_installation_chauffage_n1          VARCHAR(255),
    configuration_installation_chauffage_n1          VARCHAR(255),
    description_installation_chauffage_n1            TEXT,
    conso_chauffage_installation_chauffage_n1        DECIMAL(12,2),
    surface_chauffee_installation_chauffage_n1       DECIMAL(10,2),
    facteur_couverture_solaire_installation_chauffage_n1 DECIMAL(5,2),
    facteur_couverture_solaire_saisi_installation_chauffage_n1 VARCHAR(50),
    type_generateur_n1_installation_n1               VARCHAR(255),
    type_energie_generateur_n1_installation_n1       VARCHAR(100),
    usage_generateur_n1_installation_n1              VARCHAR(100),
    description_generateur_chauffage_n1_installation_n1 TEXT,
    conso_chauffage_generateur_n1_installation_n1    DECIMAL(12,2),
    -- ECS (Eau Chaude Sanitaire)
    type_energie_principale_ecs                      VARCHAR(100),
    type_generateur_chauffage_principal_ecs          VARCHAR(255),
    -- Ventilation
    type_ventilation                                 VARCHAR(255),
    surface_ventilee                                 DECIMAL(10,2),
    ventilation_posterieure_2012                     INTEGER
);

CREATE INDEX idx_dpe_etiquette ON dpe_logements(etiquette_dpe);
CREATE INDEX idx_dpe_code_insee ON dpe_logements(code_insee_ban);
CREATE INDEX idx_dpe_commune ON dpe_logements(nom_commune_ban);


-- ===========================================================================
-- 4. DVF MUTATIONS BRUTES (source : dvf/dvf-2025-dept44.csv, séparateur: ;)
--    Demandes de Valeurs Foncières 2025 - département 44
-- ===========================================================================
CREATE TABLE dvf_mutations (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    identifiant_document        VARCHAR(50),
    reference_document          VARCHAR(50),
    articles_cgi_1              VARCHAR(100),
    articles_cgi_2              VARCHAR(100),
    articles_cgi_3              VARCHAR(100),
    articles_cgi_4              VARCHAR(100),
    articles_cgi_5              VARCHAR(100),
    no_disposition              VARCHAR(20),
    date_mutation               DATE,
    nature_mutation             VARCHAR(50),
    valeur_fonciere             DECIMAL(15,2),
    no_voie                     VARCHAR(20),
    btq                         VARCHAR(10),
    type_de_voie                VARCHAR(10),
    code_voie                   VARCHAR(10),
    voie                        VARCHAR(255),
    code_postal                 VARCHAR(10),
    commune                     VARCHAR(255),
    code_departement            VARCHAR(3),
    code_commune                VARCHAR(3),
    prefixe_section             VARCHAR(5),
    section                     VARCHAR(5),
    no_plan                     VARCHAR(10),
    no_volume                   VARCHAR(10),
    lot_1er                     VARCHAR(20),
    surface_carrez_1er_lot      DECIMAL(10,2),
    lot_2eme                    VARCHAR(20),
    surface_carrez_2eme_lot     DECIMAL(10,2),
    lot_3eme                    VARCHAR(20),
    surface_carrez_3eme_lot     DECIMAL(10,2),
    lot_4eme                    VARCHAR(20),
    surface_carrez_4eme_lot     DECIMAL(10,2),
    lot_5eme                    VARCHAR(20),
    surface_carrez_5eme_lot     DECIMAL(10,2),
    nombre_de_lots              INTEGER,
    code_type_local             INTEGER,
    type_local                  VARCHAR(50),
    identifiant_local           VARCHAR(50),
    surface_reelle_bati         DECIMAL(10,2),
    nombre_pieces_principales   INTEGER,
    nature_culture              VARCHAR(10),
    nature_culture_speciale     VARCHAR(50),
    surface_terrain             DECIMAL(15,2)
);

CREATE INDEX idx_dvf_date ON dvf_mutations(date_mutation);
CREATE INDEX idx_dvf_commune ON dvf_mutations(commune);
CREATE INDEX idx_dvf_type_local ON dvf_mutations(type_local);
CREATE INDEX idx_dvf_code_postal ON dvf_mutations(code_postal);


-- ===========================================================================
-- 5. DVF ENRICHI (source : dvf/dvf_enriched_dept44.csv, séparateur: ;)
--    Données DVF enrichies par le pipeline ETL
-- ===========================================================================
CREATE TABLE dvf_enriched (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_mutation                 VARCHAR(50),
    date_mutation               DATE,
    nature_mutation             VARCHAR(50),
    prix                        DECIMAL(15,2),
    type_bien                   VARCHAR(50),
    surface                     DECIMAL(10,2),
    pieces                      INTEGER,
    prix_m2                     DECIMAL(12,2),
    adresse_normalisee          TEXT,
    code_postal                 VARCHAR(10),
    nom_commune                 VARCHAR(255),
    code_insee                  VARCHAR(5),
    lat                         DOUBLE,
    lon                         DOUBLE,
    dpe_classe                  VARCHAR(2),
    ges_classe                  VARCHAR(2),
    annee_construction          INTEGER,
    insee_mediane_revenu        DECIMAL(12,2),
    distance_ecole_m            DECIMAL(12,2),
    nom_ecole_proche            VARCHAR(255),
    distance_transport_m        DECIMAL(12,2),
    nom_transport_proche        VARCHAR(255),
    exposition_aeroport_peb     VARCHAR(255)
);

CREATE INDEX idx_dvf_enr_commune ON dvf_enriched(nom_commune);
CREATE INDEX idx_dvf_enr_code_insee ON dvf_enriched(code_insee);
CREATE INDEX idx_dvf_enr_type_bien ON dvf_enriched(type_bien);
CREATE INDEX idx_dvf_enr_dpe ON dvf_enriched(dpe_classe);
CREATE INDEX idx_dvf_enr_coords ON dvf_enriched(lat, lon);


-- ===========================================================================
-- 6. ECOLES (source : ecoles/ecoles-44.csv, séparateur: ;)
--    Écoles issues d'OpenStreetMap via Overpass API
-- ===========================================================================
CREATE TABLE ecoles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    osm_id          BIGINT,
    type            VARCHAR(20),
    lat             DOUBLE,
    lon             DOUBLE,
    name            VARCHAR(255),
    city            VARCHAR(255),
    postcode        VARCHAR(10),
    amenity         VARCHAR(50)
);

CREATE INDEX idx_ecoles_coords ON ecoles(lat, lon);
CREATE INDEX idx_ecoles_city ON ecoles(city);


-- ===========================================================================
-- 7. STATIONS TRANSPORT (source : transport/stations-44.csv, séparateur: ;)
--    Gares et arrêts de transport issues d'OpenStreetMap
-- ===========================================================================
CREATE TABLE stations_transport (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    osm_id          BIGINT,
    lat             DOUBLE,
    lon             DOUBLE,
    name            VARCHAR(255),
    railway_type    VARCHAR(50),
    operator        VARCHAR(255),
    network         VARCHAR(255),
    uic_ref         VARCHAR(50)
);

CREATE INDEX idx_stations_coords ON stations_transport(lat, lon);
CREATE INDEX idx_stations_type ON stations_transport(railway_type);


-- ===========================================================================
-- 8. PEB SERVITUDES (source : peb/peb-44.csv + peb/peb-44.geojson, séparateur: ;)
--    Plans d'Exposition au Bruit - servitudes aéronautiques
--    Les données GeoJSON sont intégrées dans la même table
-- ===========================================================================
CREATE TABLE peb_servitudes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    gid             INTEGER,
    gpu_doc_id      VARCHAR(64),
    gpu_status      VARCHAR(50),
    gpu_timestamp   TIMESTAMP,
    partition_sup   VARCHAR(100),
    idsup           VARCHAR(50),
    idgest          VARCHAR(50),
    nomsup          VARCHAR(255),
    nomsuplitt      TEXT,
    categorie       VARCHAR(10),
    idintgest       VARCHAR(100),
    descriptio      TEXT,
    datemaj         VARCHAR(20),
    echnum          INTEGER,
    validegest      VARCHAR(5),
    obsvalidat      TEXT,
    estabroge       VARCHAR(5),
    modeprod        VARCHAR(50),
    quiprod         VARCHAR(50),
    docsource       VARCHAR(100),
    nomreg          VARCHAR(255),
    urlreg          TEXT,
    -- Géométrie issue du GeoJSON (peut être NULL si geometry est null dans le fichier)
    geometrie_geojson TEXT
);

CREATE INDEX idx_peb_categorie ON peb_servitudes(categorie);
CREATE INDEX idx_peb_nomsup ON peb_servitudes(nomsup);


-- ===========================================================================
-- 9. INSEE COMMUNES 2021 (source : insee/insee_communes_44_2021.csv, séparateur: ;)
--    Données consolidées FILO 2021 - indicateurs par commune dept 44
--    Table simplifiée avec les indicateurs principaux
-- ===========================================================================
CREATE TABLE insee_communes_2021 (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codgeo          VARCHAR(5) NOT NULL UNIQUE,
    -- Données globales de la commune
    nbmen21         INTEGER,        -- Nombre de ménages
    nbpers21        INTEGER,        -- Nombre de personnes
    nbuc21          DECIMAL(10,1),  -- Nombre d'unités de consommation
    pmimp21         DECIMAL(5,1),   -- Part des ménages imposés (%)
    q121            DECIMAL(12,2),  -- 1er quartile du revenu
    q221            DECIMAL(12,2),  -- Médiane du revenu
    q321            DECIMAL(12,2),  -- 3ème quartile du revenu
    q3_q1           DECIMAL(12,2),  -- Écart interquartile
    d121            DECIMAL(12,2),  -- 1er décile
    d221            DECIMAL(12,2),  -- 2ème décile
    d321            DECIMAL(12,2),  -- 3ème décile
    d421            DECIMAL(12,2),  -- 4ème décile
    d621            DECIMAL(12,2),  -- 6ème décile
    d721            DECIMAL(12,2),  -- 7ème décile
    d821            DECIMAL(12,2),  -- 8ème décile
    d921            DECIMAL(12,2),  -- 9ème décile
    rd              DECIMAL(5,1),   -- Rapport interdécile D9/D1
    s80s2021        DECIMAL(5,1),   -- Rapport S80/S20
    gi21            DECIMAL(6,3),   -- Indice de Gini
    pact21          DECIMAL(5,1),   -- Part des revenus d'activité (%)
    ptsa21          DECIMAL(5,1),   -- Part des traitements et salaires (%)
    pcho21          DECIMAL(5,1),   -- Part des allocations chômage (%)
    pben21          DECIMAL(5,1),   -- Part des prestations sociales (%)
    ppen21          DECIMAL(5,1),   -- Part des pensions et retraites (%)
    paut21          DECIMAL(5,1)    -- Part des autres revenus (%)
    -- Note : les colonnes par tranche d'âge (AGE1-AGE6), taille ménage (TME1-TME5),
    -- occupation logement (TOL1-TOL2), durée logement (TLD2-TLD3),
    -- type ménage (TYM1-TYM6), occupation principale (OPR1-OPR5)
    -- sont très nombreuses (~600+). Elles sont stockées dans la table brute ci-dessous.
);

CREATE INDEX idx_insee_2021_codgeo ON insee_communes_2021(codgeo);


-- ===========================================================================
-- 10. INSEE COMMUNES 2021 - TABLE BRUTE COMPLÈTE
--     Pour stocker toutes les ~600 colonnes du fichier consolidé
-- ===========================================================================
CREATE TABLE insee_communes_2021_complet (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codgeo          VARCHAR(5) NOT NULL,
    nom_colonne     VARCHAR(50) NOT NULL,
    valeur          TEXT,
    UNIQUE(codgeo, nom_colonne)
);

CREATE INDEX idx_insee_2021c_codgeo ON insee_communes_2021_complet(codgeo);
CREATE INDEX idx_insee_2021c_colonne ON insee_communes_2021_complet(nom_colonne);


-- ===========================================================================
-- 11. INSEE COMMUNES 2023 (source : old_insee/insee_communes_44_2023.csv, séparateur: ;)
--     Données FILOSOFI 2023 pivotées - indicateurs par commune dept 44
-- ===========================================================================
CREATE TABLE insee_communes_2023 (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    geo             VARCHAR(5) NOT NULL UNIQUE,
    -- Revenus disponibles
    d1_sl           DECIMAL(12,2),  -- 1er décile niveau de vie
    d2_sl           DECIMAL(12,2),
    d3_sl           DECIMAL(12,2),
    d4_sl           DECIMAL(12,2),
    d6_sl           DECIMAL(12,2),
    d7_sl           DECIMAL(12,2),
    d8_sl           DECIMAL(12,2),
    d9_sl           DECIMAL(12,2),
    gi_sl           DECIMAL(6,3),   -- Indice de Gini
    iqr_sl          DECIMAL(12,2),  -- Écart interquartile
    ir_d9_d1_sl     DECIMAL(5,1),   -- Rapport interdécile
    med_sl          DECIMAL(12,2),  -- Médiane
    pr_md60         DECIMAL(5,1),   -- Taux de pauvreté à 60%
    q1_sl           DECIMAL(12,2),  -- 1er quartile
    q3_sl           DECIMAL(12,2),  -- 3ème quartile
    s80s20_sl       DECIMAL(5,1),   -- Rapport S80/S20
    -- Part des revenus
    s_dir_tax_di    DECIMAL(12,2),  -- Impôts directs
    s_ei_di         DECIMAL(12,2),  -- Revenus d'activité indépendants
    s_ei_di_n_sal   DECIMAL(12,2),
    s_ei_di_sal     DECIMAL(12,2),
    s_ei_di_une     DECIMAL(12,2),
    s_inc_ass_di    DECIMAL(12,2),  -- Allocations chômage et assurance
    s_ret_pen_di    DECIMAL(12,2),  -- Pensions et retraites
    s_soc_ben_di    DECIMAL(12,2),  -- Prestations sociales
    s_soc_ben_di_fam_ben DECIMAL(12,2),
    s_soc_ben_di_hou_ben DECIMAL(12,2),
    s_soc_ben_di_min_soc DECIMAL(12,2)
);

CREATE INDEX idx_insee_2023_geo ON insee_communes_2023(geo);


-- ===========================================================================
-- 12. FILOSOFI 2023 DATA BRUT (source : old_insee/DS_FILOSOFI_CC_2023_data.csv, séparateur: ;)
--     Données brutes au format long (mesure, commune, valeur)
-- ===========================================================================
CREATE TABLE filosofi_2023_data (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    filosofi_measure VARCHAR(100),
    geo             VARCHAR(10),
    geo_object      VARCHAR(10),
    unit_measure    VARCHAR(20),
    conf_status     VARCHAR(10),
    obs_status      VARCHAR(10),
    unit_mult       INTEGER,
    time_period     VARCHAR(10),
    obs_value       DECIMAL(15,5)
);

CREATE INDEX idx_filo2023_geo ON filosofi_2023_data(geo);
CREATE INDEX idx_filo2023_measure ON filosofi_2023_data(filosofi_measure);
CREATE INDEX idx_filo2023_geo_obj ON filosofi_2023_data(geo_object);


-- ===========================================================================
-- 13. FILO 2021 - Tables brutes (source : old_insee/FILO2021_*.csv, séparateur: ;)
--     Structure EAV (Entity-Attribute-Value) pour ces tables très larges
-- ===========================================================================

-- FILO2021_DEC_COM : Revenus déclarés par commune
CREATE TABLE filo2021_dec_com (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codgeo          VARCHAR(5) NOT NULL,
    nom_colonne     VARCHAR(50) NOT NULL,
    valeur          TEXT,
    UNIQUE(codgeo, nom_colonne)
);

CREATE INDEX idx_filo_dec_codgeo ON filo2021_dec_com(codgeo);

-- FILO2021_DEC_PAUVRES_COM : Revenus déclarés des ménages pauvres par commune
CREATE TABLE filo2021_dec_pauvres_com (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codgeo          VARCHAR(5) NOT NULL,
    nom_colonne     VARCHAR(50) NOT NULL,
    valeur          TEXT,
    UNIQUE(codgeo, nom_colonne)
);

CREATE INDEX idx_filo_dec_p_codgeo ON filo2021_dec_pauvres_com(codgeo);

-- FILO2021_DISP_COM : Revenus disponibles par commune
CREATE TABLE filo2021_disp_com (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codgeo          VARCHAR(5) NOT NULL,
    nom_colonne     VARCHAR(50) NOT NULL,
    valeur          TEXT,
    UNIQUE(codgeo, nom_colonne)
);

CREATE INDEX idx_filo_disp_codgeo ON filo2021_disp_com(codgeo);

-- FILO2021_DISP_PAUVRES_COM : Revenus disponibles des ménages pauvres par commune
CREATE TABLE filo2021_disp_pauvres_com (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codgeo          VARCHAR(5) NOT NULL,
    nom_colonne     VARCHAR(50) NOT NULL,
    valeur          TEXT,
    UNIQUE(codgeo, nom_colonne)
);

CREATE INDEX idx_filo_disp_p_codgeo ON filo2021_disp_pauvres_com(codgeo);

-- FILO2021_TRDECILES_DEC_COM : Tranches de déciles des revenus déclarés
CREATE TABLE filo2021_trdeciles_dec_com (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codgeo          VARCHAR(5) NOT NULL,
    nom_colonne     VARCHAR(50) NOT NULL,
    valeur          TEXT,
    UNIQUE(codgeo, nom_colonne)
);

CREATE INDEX idx_filo_trdec_codgeo ON filo2021_trdeciles_dec_com(codgeo);

-- FILO2021_TRDECILES_DISP_COM : Tranches de déciles des revenus disponibles
CREATE TABLE filo2021_trdeciles_disp_com (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codgeo          VARCHAR(5) NOT NULL,
    nom_colonne     VARCHAR(50) NOT NULL,
    valeur          TEXT,
    UNIQUE(codgeo, nom_colonne)
);

CREATE INDEX idx_filo_trdisp_codgeo ON filo2021_trdeciles_disp_com(codgeo);


-- ===========================================================================
-- VUES UTILES
-- ===========================================================================

-- Vue : Résumé DVF enrichi avec données communales
CREATE VIEW vue_dvf_complet AS
SELECT
    e.*,
    c.nom AS nom_commune_officiel,
    i.q221 AS revenu_median_commune,
    i.gi21 AS gini_commune,
    i.pact21 AS part_activite_commune
FROM dvf_enriched e
LEFT JOIN communes c ON e.code_insee = c.code_commune
LEFT JOIN insee_communes_2021 i ON e.code_insee = i.codgeo;

-- Vue : Statistiques par commune
CREATE VIEW vue_stats_commune AS
SELECT
    c.code_commune,
    c.nom,
    COUNT(e.id) AS nb_transactions,
    AVG(e.prix) AS prix_moyen,
    AVG(e.prix_m2) AS prix_m2_moyen,
    AVG(e.surface) AS surface_moyenne,
    i.q221 AS revenu_median
FROM communes c
LEFT JOIN dvf_enriched e ON c.code_commune = e.code_insee
LEFT JOIN insee_communes_2021 i ON c.code_commune = i.codgeo
GROUP BY c.code_commune, c.nom, i.q221;

-- Vue : Répartition DPE par commune
CREATE VIEW vue_dpe_commune AS
SELECT
    code_insee_ban AS code_commune,
    nom_commune_ban AS commune,
    etiquette_dpe,
    COUNT(*) AS nombre_logements
FROM dpe_logements
WHERE etiquette_dpe IS NOT NULL
GROUP BY code_insee_ban, nom_commune_ban, etiquette_dpe;


