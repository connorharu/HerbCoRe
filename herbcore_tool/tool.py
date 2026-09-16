import json
import argparse
import os
from main_f import species_link
from interactive import interactive_mode
from config import get_config, ask_for_missing_values, save_config
from sinonimos import setup_r_environment

def main():
    config = get_config()

    if config is None or any(k not in config for k in ['api_key', 'db_user', 'db_password', 'db_host', 'db_schema', 'r_home']):
        config = ask_for_missing_values()

    setup_r_environment()

    api_key = config['api_key']
    db_config = {
        'user': config['db_user'],
        'password': config['db_password'],
        'host': config['db_host'],
        'database': config['db_schema']
    }

    print("\nwould you like a step-by-step guide to run the tool's methods, or would you prefer to proceed without assistance?")
    print("[1] step-by-step (guided execution)")
    print("[2] without assistance (terminal arguments – if a command was already provided, it will be executed)")

    choice = input("choose an option: ").strip()

    if choice == "1":
        interactive_mode()
        return

    print("ATTENTION: TO EXECUTE METHODS RELATED TO COLLECTING URLS AND IMAGES, YOU MUST FOLLOW THE [1] STEP-BY-STEP GUIDE OR RUN THE CODE YOURSELF FROM THE REPOSITORY LISTED IN THE README.")

    parser = argparse.ArgumentParser(description='interface dos métodos da ferramenta')
    subparsers = parser.add_subparsers(dest="command", help="método a ser executado") 

    metadados = subparsers.add_parser("metadata", help="basic metadata")
    metadados.add_argument('--name', type=str, help='name to be identified')
    metadados.add_argument('--id', type=str, help='id to be identified')

    participants = subparsers.add_parser("participants", help="participating instituitions")

    instituition = subparsers.add_parser("instituition", help="specific instituition")
    instituition.add_argument('--acronym', type=str, help='acronym to be identified')
    instituition.add_argument('--id', type=str, help='id to be identified')
    instituition.add_argument('--lang', type=str, help='choosen language')

    collection = subparsers.add_parser("collection", help="specific collections")
    collection.add_argument('--acronym', type=str, help='acronym to be identified')
    collection.add_argument('--id', type=str, help='id to be identified')
    collection.add_argument('--lang', type=str, help='choosen language')

    dataset = subparsers.add_parser("dataset", help="specific databases")
    dataset.add_argument('--id', type=str, help='id to be identified')

    records = subparsers.add_parser("records", help="filtered records")
    records.add_argument('--filters', required=True, nargs='*', help="filters in key=value order (example: family=piperaceae)")
    records.add_argument('--table', type=str, required=True, help="database table")

    export = subparsers.add_parser("export", help="performs an SQL query and returns a CSV")
    export.add_argument('--filters', required=True, nargs='*', help="filters in key=value order (example: family=piperaceae)")
    export.add_argument('--table', type=str, required=True, help="database table")
    export.add_argument('--columns', type=str, help="columns to retrieve")
    export.add_argument('--output_csv_path', type=str, required=True, help="output path for the CSV")

    update = subparsers.add_parser("update", help="updates database records based on parameters")
    update.add_argument('--filters', required=True, nargs='*', help="filters in key=value order (example: family=piperaceae)")
    update.add_argument('--update_values', required=True, nargs='*', help="values to be update in key=valor format (ex: stateProvince=São Paulo family=Piperaceae)")
    update.add_argument('--table', type=str, required=True, help="database table")

    args = parser.parse_args()

    specieslink = species_link(api_key=api_key) 
    
    if args.command == "metadata":
        metadata = specieslink.get_metadata(name=args.name, id=args.id) 
        if metadata:
            print("\n\nbasic metadata:\n")
            print(json.dumps(metadata, indent=4, ensure_ascii=False))


    elif args.command == "participants":
        participants = specieslink.get_participants()
        if participants:
            print("\n\nparticipants:\n")
            print(json.dumps(participants, indent=4, ensure_ascii=False)) 


    elif args.command == "instituition":
        instituition = specieslink.get_institution_data(acronym=args.acronym, id=args.id, lang=args.lang)
        if instituition:
            print("\n\nspecific instituitions:\n")
            print(json.dumps(instituition, indent=4, ensure_ascii=False)) 

    elif args.command == "collection":
        collection = specieslink.get_collection_data(acronym=args.acronym, id=args.id, lang=args.lang)
        if collection:
            print("\n\nspecific collections:\n")
            print(json.dumps(collection, indent=4, ensure_ascii=False))

    elif args.command == "dataset":
        dataset = specieslink.get_dataset_info(id=args.id)
        if dataset:
            print("\n\nspecific datasets:\n")
            print(json.dumps(dataset, indent=4, ensure_ascii=False))

    elif args.command == "records":
        filters = {}
        for item in args.filters:
            key, value = item.split('=')
            filters[key] = value

        records = specieslink.search_records(filters=filters)
        if records:
            print("\n\nfiltered records:\n")
            
            specieslink.insert_into_mysql(records, db_config, table=args.table)     

    elif args.command == "export":
        filters = {}
        for item in args.filters:
            key, value = item.split('=')
            filters[key] = value

        specieslink.export_to_csv(filters=filters, db_config=db_config, table=args.table, columns=args.columns, output_csv_path=args.output_csv_path)

    elif args.command == "update":
        filters = {}
        for item in args.filters:
            key, value = item.split('=')
            filters[key] = value

        update_values = {}
        for item in args.update_values:
            key, value = item.split('=')
            update_values[key] = value

        specieslink.update_records(filters=filters, update_values=update_values, db_config=db_config, table=args.table)

if __name__ == "__main__":
    main() 
