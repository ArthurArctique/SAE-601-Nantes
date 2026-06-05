-- ===========================================================================
-- create_views.sql
-- Vues relationnelles de la base SAE-601 Nantes
-- Ces vues croisent la table de faits avec les dimensions
-- ===========================================================================


-- Vue 1 : Transaction enrichie + nom commune officiel + indicateurs INSEE
CREATE OR REPLACE VIEW vue_dvf_complet AS
SELECT
    ft.*,
    c.nom                   AS nom_commune_officiel,
    i.Q221                  AS revenu_median_2021,
    i.GI21                  AS indice_gini_2021,
    i.PACT21                AS part_activite_2021,
    i.PPEN21                AS part_pensions_2021,
    i.PCHO21                AS part_chomage_2021
FROM fait_transactions ft
LEFT JOIN dim_communes c
    ON ft.code_insee = c.code_commune
LEFT JOIN dim_insee i
    ON ft.code_insee = i.CODGEO;


-- Vue 2 : Statistiques agrégées par commune
CREATE OR REPLACE VIEW vue_stats_commune AS
SELECT
    c.code_commune,
    c.nom,
    COUNT(ft.rowid)                                          AS nb_transactions,
    ROUND(AVG(ft.prix), 2)                                   AS prix_moyen,
    ROUND(MEDIAN(ft.prix), 2)                                AS prix_median,
    ROUND(AVG(ft.prix_m2), 2)                                AS prix_m2_moyen,
    ROUND(AVG(ft.surface), 1)                                AS surface_moyenne,
    ROUND(AVG(ft.pieces), 1)                                 AS pieces_moyennes,
    i.Q221                                                   AS revenu_median,
    i.GI21                                                   AS indice_gini,
    COUNT(CASE WHEN ft.dpe_classe IN ('A','B') THEN 1 END)   AS nb_dpe_ab,
    COUNT(CASE WHEN ft.dpe_classe IN ('F','G') THEN 1 END)   AS nb_dpe_fg
FROM dim_communes c
LEFT JOIN fait_transactions ft
    ON c.code_commune = ft.code_insee
LEFT JOIN dim_insee i
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
FROM dim_dpe
WHERE etiquette_dpe IS NOT NULL
GROUP BY code_insee_ban, nom_commune_ban, etiquette_dpe
ORDER BY code_insee_ban, etiquette_dpe;


-- Vue 4 : Proximité des points d'intérêt par transaction géocodée
CREATE OR REPLACE VIEW vue_proximites AS
SELECT
    ft.code_insee,
    ft.nom_commune,
    ft.adresse_normalisee,
    ft.prix,
    ft.prix_m2,
    ft.type_bien,
    ft.dpe_classe,
    ft.distance_ecole_m,
    ft.nom_ecole_proche,
    ft.distance_transport_m,
    ft.nom_transport_proche,
    ft.exposition_aeroport_peb,
    ft.insee_mediane_revenu
FROM fait_transactions ft
WHERE ft.lat IS NOT NULL AND ft.lon IS NOT NULL;
