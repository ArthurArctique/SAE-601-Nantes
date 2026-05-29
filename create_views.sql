-- ===========================================================================
-- create_views.sql
-- Vues relationnelles de la base SAE-601 Nantes
-- Ces vues croisent les différentes tables pour faciliter l'analyse
-- ===========================================================================


-- Vue 1 : DVF enrichi + données communales et INSEE
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
    ON e.code_insee = i.CODGEO;


-- Vue 2 : Statistiques agrégées par commune
CREATE OR REPLACE VIEW vue_stats_commune AS
SELECT
    c.code_commune,
    c.nom,
    COUNT(e.rowid)                                          AS nb_transactions,
    ROUND(AVG(e.prix), 2)                                   AS prix_moyen,
    ROUND(MEDIAN(e.prix), 2)                                AS prix_median,
    ROUND(AVG(e.prix_m2), 2)                                AS prix_m2_moyen,
    ROUND(AVG(e.surface), 1)                                AS surface_moyenne,
    ROUND(AVG(e.pieces), 1)                                 AS pieces_moyennes,
    i.Q221                                                  AS revenu_median,
    i.GI21                                                  AS indice_gini,
    COUNT(CASE WHEN e.dpe_classe IN ('A','B') THEN 1 END)   AS nb_dpe_ab,
    COUNT(CASE WHEN e.dpe_classe IN ('F','G') THEN 1 END)   AS nb_dpe_fg
FROM communes c
LEFT JOIN dvf_enriched e
    ON c.code_commune = e.code_insee
LEFT JOIN insee_communes_2021 i
    ON c.code_commune = i.CODGEO
GROUP BY c.code_commune, c.nom, i.Q221, i.GI21;


-- Vue 3 : Répartition DPE par commune
CREATE OR REPLACE VIEW vue_dpe_commune AS
SELECT
    code_insee_ban          AS code_commune,
    nom_commune_ban         AS commune,
    etiquette_dpe,
    COUNT(*)                AS nombre_logements,
    ROUND(AVG(conso_5_usages_par_m2_ep), 1) AS conso_moyenne_m2
FROM dpe_logements
WHERE etiquette_dpe IS NOT NULL
GROUP BY code_insee_ban, nom_commune_ban, etiquette_dpe
ORDER BY code_insee_ban, etiquette_dpe;


-- Vue 4 : Proximité des points d'intérêt par transaction géocodée
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
WHERE e.lat IS NOT NULL AND e.lon IS NOT NULL;
