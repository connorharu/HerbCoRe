import argparse
import os

def setup_r_environment():
    config = get_config()
    if not config or 'r_home' not in config:
        raise RuntimeError("invalid config: r_home wasn't defined. run tool.py first.")

    r_home = config['r_home']

    os.environ["R_HOME"] = r_home
    os.environ["PATH"] = os.path.join(r_home, "bin", "x64") + ";" + os.environ.get("PATH", "")

import re 
import csv 
import rpy2.robjects as robjects 
from rpy2.robjects.packages import importr 
from rpy2.robjects.vectors import StrVector 
import pymysql
from config import get_config, ask_for_missing_values, save_config
from main_f import species_link
from rpy2.rinterface_lib.sexp import NULLType

def extract_plants_from_txt(txt_file):
    with open(txt_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    plant_names = re.findall(r'"([^"]+)"', content)
    return plant_names

def save_plants_to_csv(plant_names, csv_file):
    with open(csv_file, 'w', encoding='utf-8') as file:
        if not plant_names:
            print("empty list\n")
            return

        for name in plant_names[:-1]: 
            file.write(f'"{name}",\n')  
        file.write(f'"{plant_names[-1]}"\n')  

def read_plants_from_csv(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        plants = [row[0].strip('"') for row in reader]
    return plants


def perform_lcvp_fuzzy_search(csv_file, max_distance=0.1): 
    plant_names = read_plants_from_csv(csv_file)

    print(plant_names)

    r_plant_names = StrVector(plant_names) 
    
    lcvp_plants = importr('lcvplants') 
    result = robjects.r['lcvp_fuzzy_search'](r_plant_names, max_distance=max_distance) 

    result_df = robjects.r['as.data.frame'](result)

    genuses = list(result_df.rx2('Input.Genus'))
    epithets = list(result_df.rx2('Input.Epitheton'))
    
    found_names = [f"{genus} {epithet}" for genus, epithet in zip(genuses, epithets)] 

    for plant_name in plant_names:
        if plant_name not in found_names:
            print(f"\n <!!!!!!> plant '{plant_name}' not found on LCVP! <!!!!!!>\n")

    return result_df


def perform_lcvp_fuzzy_search_per_line(csv_file, db_config, table, column, specieslink, status, max_distance=0.1):
    plant_names = read_plants_from_csv(csv_file)  
    lcvp_plants = importr('lcvplants') 
    updated = 0  
    unavailable = 0 
    kept = 0 

    for plant_name in plant_names: 
        print(f"processing: {plant_name}...")
        try:
            r_plant_name = StrVector([plant_name]) 
            result = robjects.r['lcvp_fuzzy_search'](r_plant_name, max_distance=max_distance)  
            result_df = robjects.r['as.data.frame'](result)  

            if isinstance(result, NULLType): 
                print(f"\n <!!!!!!> plant '{plant_name}' not found on LCVP! <!!!!!!>\n")

                status_final = 'unavailable'
                filters = {'scientificname': plant_name}
                update_values = {status: status_final} 

                specieslink.update_records(filters, update_values, db_config, table)

                unavailable += 1
                continue

            statuses = [status.strip().lower() for status in result_df.rx2('Status')] 
            output_taxa = [name.strip() for name in result_df.rx2('Output.Taxon')] 

            if 'accepted' in statuses: 
                print(f"'{plant_name}' has at least one entrance with its status as 'accepted', won't be updated")

                status_final = 'accepted'
                filters = {'scientificname': plant_name}
                update_values = {status: status_final}

                specieslink.update_records(filters, update_values, db_config, table)

                kept += 1
                continue
            elif 'synonym' in statuses: 
                status_final = 'synonym'
                idx = statuses.index('synonym') 
                new_name = output_taxa[idx]
                print(f"updating '{plant_name}' to '{new_name}' since it's status is 'synonym'")

                filters = {'scientificname': plant_name} 
                update_nomes = {column: new_name} 
                specieslink.update_records(filters, update_nomes, db_config, table)

                update_status = {status: status_final} 
                specieslink.update_records(filters, update_status, db_config, table)

                updated += 1
                continue
            elif 'unresolved' in statuses: 
                status_final = 'unresolved'
                filters = {'scientificname': plant_name}
                update_values = {status: status_final}

                specieslink.update_records(filters, update_values, db_config, table)

                print(f"'{plant_name}'s status isn't neither'synonym' nor 'accepted', it will be ignored")
                kept += 1

        except Exception as e:
            print(f"error while processing '{plant_name}': {e}")

    print(f"\ntotal of updated names: {updated} | names not found: {unavailable} | kept names: {kept}")

def save_result_to_txt_aligned(result_df, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        columns = list(result_df.colnames) 
        
        max_widths = [max(len(col), max(len(str(val)) for val in result_df[i])) for i, col in enumerate(columns)]
        
        header = '  '.join(col.ljust(max_widths[i]) for i, col in enumerate(columns))
        file.write(header + '\n') 
        file.write('-' * len(header) + '\n')  

        rows = [list(row) for row in zip(*[result_df[i] for i in range(len(columns))])]
        
        for row in rows:
            formatted_row = '  '.join(str(val).ljust(max_widths[i]) for i, val in enumerate(row))
            file.write(formatted_row + '\n')

def main():
    parser = argparse.ArgumentParser(description='scientific name analysis method interface')
    subparsers = parser.add_subparsers(dest='command', help='method to be executed')    

    extract = subparsers.add_parser("extract", help="extract names from text and save to CSV")
    extract.add_argument("--txt", dest="txt_file", required=True, help="input txt file")
    extract.add_argument("--csv", dest="csv", required=True, help="output txt file")

    fuzzy = subparsers.add_parser("fuzzy", help="fuzzy text search and visualization based on CSV names")
    fuzzy.add_argument("--csv", required=True, help="input csv file")
    fuzzy.add_argument("--output", required=True, help="output txt result file")
    fuzzy.add_argument("--max_distance", type=float, default=0.1, help="max distance for fuzzy calculating (reccomended value: 1.0)")

    fuzzy_line = subparsers.add_parser("fuzzy_line", help="line-by-line database update based on CSV names")
    fuzzy_line.add_argument("--csv", required=True, help="input csv file")
    fuzzy_line.add_argument("--max_distance", type=float, default=0.1, help="max distance for fuzzy calculating (reccomended value: 1.0)")
    fuzzy_line.add_argument("--table", required=True, help="database table's name")
    fuzzy_line.add_argument("--column", required=True, help="name of the new PRE-CREATED column that will store the new scientific name of the plants")
    fuzzy_line.add_argument("--status", required=True, help="name of the PRE-CREATED column that will store the status of the plants' CURRENT scientific name")

    args = parser.parse_args()

    config = get_config()

    if config is None or any(k not in config for k in ['api_key', 'db_user', 'db_password', 'db_host', 'db_schema']):
        config = ask_for_missing_values()

    api_key = config['api_key']
    db_config = {
        'user': config['db_user'],
        'password': config['db_password'],
        'host': config['db_host'],
        'database': config['db_schema']
    }

    specieslink = species_link(api_key=api_key)

    if args.command == "extract":
        print("\nextracting plant names")
        extract = extract_plants_from_txt(args.txt_file)
        save_plants_to_csv(extract, args.csv)
        print(f"result saved in {args.csv}\n")

    elif args.command == "fuzzy":
        print("\nexecuting fuzzy search on R")
        fuzzy = perform_lcvp_fuzzy_search(args.csv, max_distance=args.max_distance)
        save_result_to_txt_aligned(fuzzy, args.output)
        print(f"result saved in {args.output}\n")

    elif args.command == "fuzzy_line":
        print("\nexecuting fuzzy line-by-line search on R")

        fuzzy_line = perform_lcvp_fuzzy_search_per_line(
            csv_file=args.csv,
            db_config=db_config,
            table=args.table,
            column=args.column,
            specieslink=specieslink,
            status=args.status,
            max_distance=args.max_distance
        )
        
        print(f"\nresults saved in '{args.column}' column from '{args.table}' table")

if __name__ == "__main__":
    main()