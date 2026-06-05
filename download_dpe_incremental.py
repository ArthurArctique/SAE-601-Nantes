import os
import csv
import json
import ssl
import urllib.request
import time

ssl._create_default_https_context = ssl._create_unverified_context

# Target CSV path
csv_path = "data/dpe/dpe-multidept.csv"
os.makedirs(os.path.dirname(csv_path), exist_ok=True)

# Columns to download
dpe_cols = ['numero_dpe', 'etiquette_dpe', 'etiquette_ges', 'annee_construction', 'date_reception_dpe', 'numero_voie_ban', 'nom_rue_ban', 'nom_commune_ban', 'code_insee_ban', 'conso_5_usages_par_m2_ep']

# List of all metropolitan departments of France (96 departments)
DEPARTEMENTS_METRO = [str(i).zfill(2) for i in range(1, 96) if i != 20] + ["2A", "2B"]
DEPARTEMENTS_METRO.sort()

def get_api_total(dept):
    url = f"https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/lines?size=1&q_mode=simple&qs=code_departement_ban:{dept}&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                data = json.loads(res.read())
                return data.get('total', 0)
        except Exception as e:
            print(f"\n[API Warning] Impossible de récupérer le total pour le {dept} (essai {attempt+1}/5) : {e}")
            time.sleep(3)
    return -1

def clean_dept_from_csv(csv_file, dept_to_remove):
    print(f"  -> Nettoyage des données partielles existantes pour le département {dept_to_remove}...")
    temp_path = csv_file + ".tmp"
    try:
        with open(csv_file, 'r', encoding='utf-8') as f_in, \
             open(temp_path, 'w', encoding='utf-8', newline='') as f_out:
            reader = csv.reader(f_in)
            writer = csv.writer(f_out)
            
            # Write header
            header = next(reader, None)
            if header:
                writer.writerow(header)
                
                # Find the index of code_insee_ban dynamically
                insee_idx = -1
                for idx, col in enumerate(dpe_cols):
                    if col == 'code_insee_ban':
                        insee_idx = idx
                        break
                
                if insee_idx != -1:
                    for row in reader:
                        if len(row) > insee_idx:
                            insee = row[insee_idx]
                            if insee and insee[:2] == dept_to_remove:
                                continue
                        writer.writerow(row)
        os.replace(temp_path, csv_file)
        print(f"  -> Nettoyage terminé avec succès.")
    except Exception as e:
        print(f"  -> [Erreur] Impossible de nettoyer le département {dept_to_remove} : {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)

# 1. Check existing records in the CSV
dept_counts = {d: 0 for d in DEPARTEMENTS_METRO}
file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0

if file_exists:
    print(f"Analyse globale du fichier {csv_path} pour compter les lignes existantes...")
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                insee = row.get('code_insee_ban')
                if insee and len(insee) >= 2:
                    dept = insee[:2]
                    if dept in dept_counts:
                        dept_counts[dept] += 1
    except Exception as e:
        print(f"Erreur d'analyse du fichier CSV : {e}. Il sera réinitialisé.")
        file_exists = False

# 2. Main loop over all metropolitan departments
select_cols = ",".join(dpe_cols)

print(f"\nDébut du traitement de {len(DEPARTEMENTS_METRO)} départements de France Métropolitaine...")

for dept in DEPARTEMENTS_METRO:
    count_csv = dept_counts.get(dept, 0)
    
    # Get total expected records from the API
    total_api = get_api_total(dept)
    if total_api == -1:
        print(f"Département {dept} : API injoignable après plusieurs tentatives. Ignoré pour l'instant.")
        continue
        
    if total_api == 0:
        print(f"Département {dept} : 0 DPE trouvés sur l'API ADEME.")
        continue
        
    # Check if the department is already complete
    if count_csv >= total_api:
        print(f"Département {dept} : Déjà complet ({count_csv}/{total_api} DPE). Ignoré.")
        continue
        
    # If incomplete (count_csv > 0 but less than total_api), clean it first
    if count_csv > 0:
        print(f"Département {dept} : Extraction incomplète ({count_csv}/{total_api} DPE). Nettoyage des lignes partielles...")
        clean_dept_from_csv(csv_path, dept)
    else:
        print(f"Département {dept} : Absent ({total_api} DPE à extraire).")
        
    # Make sure the CSV file has a header if it's new or was empty
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(dpe_cols)
            
    # Download from scratch for this department
    print(f"  -> Téléchargement DPE en cours pour le département {dept}...")
    url = f"https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/lines?size=10000&select={select_cols}&q_mode=simple&qs=code_departement_ban:{dept}&format=json"
    total_extracted = 0
    
    with open(csv_path, 'a', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        while url:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            try:
                with urllib.request.urlopen(req, timeout=30) as res:
                    data = json.loads(res.read())
                    results = data.get('results', [])
                    if results:
                        for row in results:
                            w.writerow([row.get(c, '') for c in dpe_cols])
                        total_extracted += len(results)
                    
                    print(f"    -> {total_extracted}/{total_api} DPE extraits...", end="\r", flush=True)
                    url = data.get('next')
            except Exception as e:
                print(f"\n    Erreur réseau pour le département {dept} (nouvelle tentative dans 5s) : {e}")
                time.sleep(5)
                
    print(f"\n  -> Département {dept} terminé ! Total extrait : {total_extracted} DPE.")

print("\nTraitement incrémental terminé avec succès !")
