# Modèle Conceptuel de Données — SAE-601 Nantes

## Schéma en étoile

```mermaid
erDiagram
    DIM_COMMUNES {
        VARCHAR code_commune PK
        VARCHAR nom
        TEXT geometrie_json
    }

    DIM_BAN {
        VARCHAR id_ban PK
        INTEGER numero
        VARCHAR rep
        VARCHAR nom_voie
        VARCHAR code_postal
        VARCHAR code_insee FK
        VARCHAR nom_commune
        DOUBLE lon
        DOUBLE lat
    }

    DIM_DPE {
        VARCHAR numero_dpe PK
        VARCHAR etiquette_dpe
        VARCHAR etiquette_ges
        VARCHAR type_batiment
        INTEGER annee_construction
        DECIMAL surface_habitable_logement
        DECIMAL conso_5_usages_par_m2_ep
        DECIMAL emission_ges_par_m2
        VARCHAR code_insee_ban FK
        VARCHAR nom_commune_ban
        VARCHAR code_postal_ban
        DECIMAL x_ban
        DECIMAL y_ban
    }

    FAIT_TRANSACTIONS {
        VARCHAR id_mutation PK
        DATE date_mutation
        VARCHAR nature_mutation
        DECIMAL prix
        VARCHAR type_bien
        DECIMAL surface
        INTEGER pieces
        DECIMAL prix_m2
        VARCHAR adresse_normalisee
        VARCHAR code_postal
        VARCHAR nom_commune
        VARCHAR code_insee FK
        DOUBLE lat
        DOUBLE lon
        VARCHAR dpe_classe
        VARCHAR ges_classe
        INTEGER annee_construction
        DECIMAL insee_mediane_revenu
        DECIMAL distance_ecole_m
        VARCHAR nom_ecole_proche
        DECIMAL distance_transport_m
        VARCHAR nom_transport_proche
        VARCHAR exposition_aeroport_peb
    }

    DIM_ECOLES {
        BIGINT osm_id PK
        VARCHAR type
        DOUBLE lat
        DOUBLE lon
        VARCHAR name
        VARCHAR city
        VARCHAR postcode
        VARCHAR amenity
    }

    DIM_TRANSPORT {
        BIGINT osm_id PK
        DOUBLE lat
        DOUBLE lon
        VARCHAR name
        VARCHAR railway_type
        VARCHAR operator
        VARCHAR network
        VARCHAR uic_ref
    }

    DIM_PEB {
        INTEGER gid PK
        VARCHAR categorie
        VARCHAR nomsup
        TEXT descriptio
        TEXT geometrie_json
    }

    DIM_INSEE {
        VARCHAR CODGEO PK
        INTEGER NBMEN21 "Nb menages"
        INTEGER NBPERS21 "Nb personnes"
        DECIMAL NBUC21 "Nb unites conso"
        DECIMAL Q121 "1er quartile revenu"
        DECIMAL Q221 "Revenu median"
        DECIMAL Q321 "3e quartile revenu"
        DECIMAL GI21 "Indice de Gini"
        DECIMAL PACT21 "Part activite"
        DECIMAL PTSA21 "Part salaires"
        DECIMAL PCHO21 "Part chomage"
        DECIMAL PBEN21 "Part benefices"
        DECIMAL PPEN21 "Part pensions"
        DECIMAL PAUT21 "Part autres"
        DECIMAL PMIMP21 "Part menages imposes"
        DECIMAL PIMPOT21 "Part impots"
    }

    DIM_COMMUNES ||--o{ DIM_BAN : "code_commune = code_insee"
    DIM_COMMUNES ||--o{ FAIT_TRANSACTIONS : "code_commune = code_insee"
    DIM_COMMUNES ||--o{ DIM_DPE : "code_commune = code_insee_ban"
    DIM_COMMUNES ||--|| DIM_INSEE : "code_commune = CODGEO"
    DIM_BAN }o--o| FAIT_TRANSACTIONS : "geocodage adresse"
    FAIT_TRANSACTIONS }o--o| DIM_ECOLES : "proximite spatiale"
    FAIT_TRANSACTIONS }o--o| DIM_TRANSPORT : "proximite spatiale"
    FAIT_TRANSACTIONS }o--o| DIM_PEB : "intersection spatiale"
```

## Vues relationnelles

```mermaid
flowchart LR
    subgraph Dimensions
        B[dim_ban]
        C[dim_communes]
        I[dim_insee]
        D[dim_dpe]
    end

    subgraph Faits
        FT[fait_transactions]
    end

    subgraph Vues
        V1[vue_dvf_complet]
        V2[vue_stats_commune]
        V3[vue_dpe_commune]
        V4[vue_proximites]
    end

    FT --> V1
    C --> V1
    I --> V1

    C --> V2
    FT --> V2
    I --> V2

    D --> V3

    FT --> V4
```

## Description des vues

| Vue | Description | Jointures |
|-----|-------------|-----------|
| `vue_dvf_complet` | Chaque transaction enrichie du nom commune officiel et des indicateurs INSEE (revenu médian, Gini, parts de revenus) | `fait_transactions` ← `dim_communes` ← `dim_insee` |
| `vue_stats_commune` | Statistiques agrégées par commune : prix moyen/médian, surface moyenne, répartition DPE A-B vs F-G | `dim_communes` ← `fait_transactions` ← `dim_insee` |
| `vue_dpe_commune` | Répartition des étiquettes DPE par commune avec consommation moyenne au m² | `dim_dpe` groupé par commune |
| `vue_proximites` | Distances aux écoles, transports et exposition PEB pour chaque transaction géocodée | `fait_transactions` filtré sur `lat IS NOT NULL` |

## Types de relations

| Relation | Type | Clé de jointure | Description |
|----------|------|-----------------|-------------|
| dim_communes → dim_ban | 1:N | `code_commune` = `code_insee` | Chaque commune contient des milliers d'adresses BAN |
| dim_communes → fait_transactions | 1:N | `code_commune` = `code_insee` | Chaque commune contient plusieurs transactions |
| dim_communes → dim_dpe | 1:N | `code_commune` = `code_insee_ban` | Chaque commune contient plusieurs diagnostics |
| dim_communes → dim_insee | 1:1 | `code_commune` = `CODGEO` | Un jeu d'indicateurs par commune |
| dim_ban → fait_transactions | Géocodage | Appariement adresse textuelle | L'adresse DVF est cherchée dans la BAN pour obtenir lat/lon |
| fait_transactions ↔ dim_ecoles | Spatiale | KDTree (lat, lon) | Distance au point le plus proche |
| fait_transactions ↔ dim_transport | Spatiale | KDTree (lat, lon) | Distance au point le plus proche |
| fait_transactions ↔ dim_peb | Spatiale | Intersection polygone | Détection si la transaction est dans une zone PEB |
