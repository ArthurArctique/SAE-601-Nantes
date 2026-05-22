#!/usr/bin/env python3
import os
import zipfile
import gzip
import shutil
import urllib.request
import urllib.parse
import json
import csv
import subprocess
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def download(url, path):
    print(f"Downloading {url} to {path}...")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(path, 'wb') as out:
        shutil.copyfileobj(response, out)

def query_overpass(query):
    for endpoint in ["https://overpass.kumi.systems/api/interpreter", "https://lz4.overpass-api.de/api/interpreter", "https://overpass.openstreetmap.fr/api/interpreter"]:
        try:
            req = urllib.request.Request(endpoint + "?data=" + urllib.parse.quote(f"[out:json][timeout:180];{query}"), headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=180) as res:
                return json.loads(res.read().decode('utf-8')).get('elements', [])
        except Exception:
            continue
    return []

if __name__ == '__main__':
    for d in ["data/dvf", "data/ban", "data/dpe", "data/insee", "data/old_insee", "data/admin", "data/transport", "data/ecoles", "data/peb"]:
        os.makedirs(d, exist_ok=True)

    # 1. DVF 2025
    zip_dvf = "data/dvf/valeursfoncieres-2025.txt.zip"
    download("https://static.data.gouv.fr/resources/demandes-de-valeurs-foncieres/20260405-002321/valeursfoncieres-2025.txt.zip", zip_dvf)
    with zipfile.ZipFile(zip_dvf, 'r') as z:
        txt_name = [name for name in z.namelist() if name.lower().endswith('.txt')][0]
        z.extract(txt_name, "data/dvf")
    txt_path = f"data/dvf/{txt_name}"
    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as infile, \
         open("data/dvf/dvf-2025-dept44.csv", 'w', encoding='utf-8') as outfile:
        header = infile.readline()
        outfile.write(header.replace('|', ','))
        for line in infile:
            parts = line.split('|')
            if len(parts) > 18 and parts[18] == '44':
                outfile.write(line.replace('|', ','))
    os.remove(zip_dvf)
    os.remove(txt_path)

    # 2. BAN 44
    gz_ban = "data/ban/adresses-44.csv.gz"
    download("https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-44.csv.gz", gz_ban)
    with gzip.open(gz_ban, 'rb') as f_in, open("data/ban/adresses-44.csv", 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.remove(gz_ban)

    # 3. DPE 44
    download("https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/lines?size=10000&q=44000&format=csv", "data/dpe/dpe-logements-existants-44.csv")

    # 4. INSEE 2021 & 2023
    zip_2021 = "data/old_insee/indic-struct-distrib-revenu-2021-COMMUNES_csv.zip"
    download("https://www.insee.fr/fr/statistiques/fichier/7756855/indic-struct-distrib-revenu-2021-COMMUNES_csv.zip", zip_2021)
    with zipfile.ZipFile(zip_2021, 'r') as z:
        z.extractall("data/old_insee")
    os.remove(zip_2021)

    zip_2023 = "data/old_insee/FILOSOFI_CC_csv.zip"
    download("https://www.insee.fr/fr/statistiques/fichier/8984752/FILOSOFI_CC_csv.zip", zip_2023)
    with zipfile.ZipFile(zip_2023, 'r') as z:
        z.extractall("data/old_insee")
    os.remove(zip_2023)

    # 5. GeoJSON Communes
    download("https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements/44-loire-atlantique/communes-44-loire-atlantique.geojson", "data/admin/communes-44.geojson")

    # 6. Ecoles OSM
    elements = query_overpass('(node["amenity"="school"](46.85,-2.55,47.65,-0.92);way["amenity"="school"](46.85,-2.55,47.65,-0.92););out center;')
    with open("data/ecoles/ecoles-44.csv", 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['osm_id', 'type', 'lat', 'lon', 'name', 'city', 'postcode', 'amenity'])
        for e in elements:
            lat = e.get('lat') if e.get('type') == 'node' else e.get('center', {}).get('lat')
            lon = e.get('lon') if e.get('type') == 'node' else e.get('center', {}).get('lon')
            w.writerow([e.get('id'), e.get('type'), lat, lon, e.get('tags', {}).get('name', ''), e.get('tags', {}).get('addr:city', ''), e.get('tags', {}).get('addr:postcode', ''), e.get('tags', {}).get('amenity', 'school')])

    # 7. Transport OSM
    elements = query_overpass('(node["railway"="station"](46.85,-2.55,47.65,-0.92);node["railway"="halt"](46.85,-2.55,47.65,-0.92);node["railway"="tram_stop"](46.85,-2.55,47.65,-0.92););out;')
    with open("data/transport/stations-44.csv", 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['osm_id', 'lat', 'lon', 'name', 'railway_type', 'operator', 'network', 'uic_ref'])
        for e in elements:
            w.writerow([e.get('id'), e.get('lat'), e.get('lon'), e.get('tags', {}).get('name', ''), e.get('tags', {}).get('railway', ''), e.get('tags', {}).get('operator', ''), e.get('tags', {}).get('network', ''), e.get('tags', {}).get('uic_ref', '')])

    # 8. PEB
    params = {'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature', 'typeNames': 'wfs_sup:servitude', 'outputFormat': 'application/json', 'cql_filter': "categorie='T5' AND partition LIKE '%_44_%'"}
    req = urllib.request.Request("https://data.geopf.fr/wfs/ows?" + urllib.parse.urlencode(params))
    with urllib.request.urlopen(req) as res:
        geojson = json.loads(res.read().decode('utf-8'))
    with open("data/peb/peb-44.geojson", 'w', encoding='utf-8') as f:
        json.dump(geojson, f)
    features = geojson.get('features', [])
    if features:
        headers = sorted(list({k for feat in features for k in feat.get('properties', {}).keys()}))
        with open("data/peb/peb-44.csv", 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(headers)
            for feat in features:
                w.writerow([feat.get('properties', {}).get(h, '') for h in headers])

    # 9. Consolidation
    subprocess.run(["python3", "IA Files/merge_insee.py"], check=True)
    subprocess.run(["python3", "IA Files/pipeline.py"], check=True)
    subprocess.run(["python3", "ETL.py"], check=True)
    print("Done!")
