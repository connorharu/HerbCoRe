import json
import os
import sys
from main_f import species_link
from config import get_config, ask_for_missing_values

from synonym import extract_plants_from_txt, save_plants_to_csv, perform_lcvp_fuzzy_search, perform_lcvp_fuzzy_search_per_line, save_result_to_txt_aligned
from rpy2.robjects.packages import importr

import subprocess

from deduplicating import processing

def interactive_mode():
    print("\nwelcome to the interactive mode!")
    print("here, you will be guided to choose the methods and provide the necessary parameters.")

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
    
    while True:
        print("\nchoose a method:") 
        print("[1] information about the data")
        print("[2] filtering and queries in the database")
        print("[3] verification of the scientific name")
        print("[4] herbarium specimen images") 
        print("[5] authors of reliable scientific names")
        print("[6] exit")

        choice = input("\nenter the option number: ").strip()
        if choice == "1":
            print("[1] metadata")
            print("[2] participating institutions")
            print("[3] specific institutions")
            print("[4] collections")
            print("[5] specific datasets")

            choice2 = input("\nenter the option number: ").strip()

            if choice2 == "1":

                name = input("provide the name (optional): ").strip()
                id_ = input("provide the id (optional): ").strip()
                print(f"executing specieslink.get_metadata(name={name}, id={id_})...\n")

                metadata = specieslink.get_metadata(name=name, id=id_)
                if metadata:
                    print("basic metadata:\n")
                    print(json.dumps(metadata, indent=4, ensure_ascii=False))  # Exibe os metadados formatados
                    finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                    if finishing == "N":
                        break

            elif choice2 == "2":
                acronym = input("provide the instituition acronym (optional): ").strip()
                print(f"executing specieslink.get_institution_data(acronym={acronym})...\n")

                participants = specieslink.get_participants()
                if participants:
                    print("\n\nparticipants:\n")
                    print(json.dumps(participants, indent=4, ensure_ascii=False))
                    finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                    if finishing == "N":
                        break

            elif choice2 == "3":
                acronym = input("provide the collection acronym (mandatoty if no ID): ").strip()
                id_ = input("provide the id (mandatory if no acronym): ").strip()
                lang = input("provide language (optional): ").strip()
                print(f"executing specieslink.get_institution_data(acronym={acronym}, id={id_}, lang={lang})...\n")

                instituition = specieslink.get_institution_data(acronym=acronym, id=id_, lang=lang)
                if instituition:
                    print("\n\nspecific instituitions:\n")
                    print(json.dumps(instituition, indent=4, ensure_ascii=False))
                finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                if finishing == "N":
                    break

            elif choice2 == "4":
                acronym = input("provide the collection acronym (mandatoty if no ID): ").strip()
                id_ = input("provide the id (mandatory if no acronym): ").strip()
                lang = input("provide language (optional): ").strip()
                print(f"executing specieslink.get_collection_data(acronym={acronym}, id={id_}, lang={lang})...\n")
                
                collection = specieslink.get_collection_data(acronym=acronym, id=id_, lang=lang)
                if collection:
                    print("\n\nspecific collections:\n")
                    print(json.dumps(collection, indent=4, ensure_ascii=False))
                finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                if finishing == "N":
                    break
            
            elif choice2 == "5":
                id_ = input("provide id (mandatory): ").strip()
                print(f"executing specieslink.get_dataset_info(id={id_})...\n")

                dataset = specieslink.get_dataset_info(id=id_)
                if dataset:
                    print("\n\nspecific database:\n")
                    print(json.dumps(dataset, indent=4, ensure_ascii=False))
                finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                if finishing == "N":
                    break

        elif choice == "2":
            print("[1] filter/add records in a database")
            print("[2] SQL query")
            print("[3] SQL update")

            choice3 = input("\nenter the option number: ").strip()

            if choice3 == "1":
                filters_input = input("provide filters (key=value format, separate with a blank space: ").strip()
                table = input("provide the name of the table the records should be added to: ").strip()
                print(f"executing specieslink.search_records(filters={filters_input}, table={table})...\n")

                filters = {}
                for item in filters_input.split():
                    if '=' not in item: 
                        print(f"poorly formatted filter: {item} - use key=value")
                        return
                    else:
                        key, value = item.split('=', 1)
                        filters[key.strip()] = value.strip()

                records = specieslink.search_records(filters=filters)

                if records:
                    print(f"\n{len(records)} records found. inserting in '{table}'...")
                    specieslink.insert_into_mysql(records, db_config, table=table)
                    print("records inserted with success.")
                else:
                    print("no records found with provided filters.")

                finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                if finishing == "N":
                    break

            elif choice3 == "2":
                filters_input = input("provide filters (key=value format, separate with a blank space: ").strip()
                table = input("provide the name of the table the records should be taken from: ").strip()
                columns = input("specify the columns to return (separate with a comma, or leave blank for all): ").strip()
                output_csv_path = input("provide path for output CSV: ").strip()
                print(f"executing specieslink.export_to_csv(filters={filters_input}, table={table}, columns={columns}, output_csv_path={output_csv_path})...\n")

                filters = {}
                for item in filters_input.split():
                    if '=' not in item:  
                        print(f"poorly formatted filter: {item} - use key=value")
                        return
                    else:
                        key, value = item.split('=', 1)
                        filters[key.strip()] = value.strip()

                columns = ", ".join([col.strip() for col in columns.split(",")]) if columns else None

                specieslink.export_to_csv(filters=filters, db_config=db_config, table=table, columns=columns, output_csv_path=output_csv_path)

                finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                if finishing == "N":
                    break

            elif choice3 == "3":
                update_input = input("provide the column and the new value to update it (key=value format, separated by a blank space): ").strip()
                filters_input = input("provide the column and old value to be updated (key=value format, separated by a blank space): ").strip()
                table = input("provide the name of the table the records should be updated on: ").strip()
                print(f"executing specieslink.update_records(filters={filters_input}, update_values={update_input}, table={table})...\n")

                filters = {}
                for item in filters_input.split():
                    if '=' not in item: 
                        print(f"poorly formatted filter: {item} - use key=value")
                        return
                    else:
                        key, value = item.split('=', 1)
                        filters[key.strip()] = value.strip()

                update_values = {}
                for item in update_input.split():
                    if '=' not in item:
                        print(f"poorly formatted update value: {item} - use key=value")
                        return
                    else:
                        key, value = item.split('=', 1)
                        update_values[key.strip()] = value.strip()

                specieslink.update_records(filters=filters, update_values=update_values, db_config=db_config, table=table)

                finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                if finishing == "N":
                    break

        elif choice == "3":
            print("[1] extract names from a txt to a csv")
            print("[2] fuzzy search on R based on the names on the csv")

            choice4 = input("\nenter the option number: ").strip()

            if choice4 == "1":
                txt = input("provide the txt file with the scientific name of the plants: ").strip()
                csv = input("provide the name to be used for the output csv with the name of the plants: ").strip()
                print(f"executing synonyms.extract_plants_from_txt(--txt {txt} --csv {csv})...\n")

                extract = extract_plants_from_txt(txt)
                if extract:
                    print("\nextracting the plant names")
                    save_plants_to_csv(extract, csv)
                    print(f"result saved in {csv}\n")

                finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                if finishing == "N":
                    break

            elif choice4 == "2":
                print("[1] compare the entire CSV list at once and display the result in a txt file")
                print("[2] compare each name in the CSV separately, line by line, and save it to the database")

                choice5 = input("\nenter the option number: ").strip()

                if choice5 in ["1", "2"]:
                    csv = input("provide the name to the input csv with the scientific name of the plants: ").strip()
                    max_distance = input("provide a margin error (0.1 default): ").strip()
                    if max_distance:
                        try:
                            max_distance = float(max_distance)
                        except ValueError:
                            print("invalid margin error. defaulting to 0.1\n")
                            max_distance = 0.1
                    else:
                        max_distance = 0.1

                if choice5 == "1":
                    txt = input("provide the txt file with the Leipzig search: ").strip()
                    print(f"executing synonym.perform_lcvp_fuzzy_search(--csv {csv} --txt {txt})...\n")
                    fuzzy = perform_lcvp_fuzzy_search(csv, max_distance)
                    if fuzzy:
                        print("\nverifying with LCVP...")
                        save_result_to_txt_aligned(fuzzy, txt)
                        print(f"result saved in {txt}\n")

                    finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                    if finishing == "N":
                        break

                if choice5 == "2":
                    tabela = input("provide the name of the table with the CURRENT scientific name of the plants: ").strip()
                    coluna = input("provide the name of the PRE-CREATED column that will store the new scientific name of the plants: ").strip()
                    status = input("provide the name of the PRE-CREATED column that will store the status of the plants' CURRENT scientific name: ").strip()
                    specieslink = species_link(api_key=api_key)

                    print(f"executing synonym.perform_lcvp_fuzzy_search_per_line(--csv {csv} --tabela {tabela} --coluna {coluna} --status {status})...\n")
                    
                    fuzzy_line = perform_lcvp_fuzzy_search_per_line(
                        csv_file=csv, db_config=db_config, tabela=tabela, coluna=coluna, specieslink=specieslink, status=status, max_distance=max_distance
                    )
                    if fuzzy_line:
                        print("\nverifying with LCVP...")

                    finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                    if finishing == "N":
                        break

        if choice == "4":
            print("[1] obtaining URLs from barcodes")
            print("[2] obtain images from URLs")

            choice6 = input("\nenter the option number: ").strip()

            if choice6 == "1":
                familia = input("provide the plant family's name for saving the output file: ").strip()
                csv = input("provide the CSV parh (with the 'barcode' column): ").strip()
                try:
                    print(f"\nexecuting crawler for the family '{familia}' for collecting their URLs...\n")
                    subprocess.run([sys.executable, 'downloader-specieslink-master/main.py', '--family', familia, '--csv', csv])
                    print("\nURLs collected successfully.\n")
                except Exception as e:
                    print(f"\nan error occured while executing the crawler: {e}\n")
                finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                if finishing == "N":
                    break

            elif choice6 == "2":
                csv = input("CSV path obtained in the previous step: ").strip()
                output_imagens = input("folder for the images (will create one if not existent): ").strip()
                try:
                    print(f"\nexecuting image downloading in '{output_imagens}'...\n")
                    print("<!!!> ATTENTION: TIME CONSUMING PROCEDURE ! MIGHT LAST DAYS <!!!>")
                    subprocess.run([sys.executable, 'downloader-specieslink-master/use-dezoomify-rs.py', '--input', csv, '--output', output_imagens])
                    print("\nimage downloading successfully finished.\n")
                except Exception as e:
                    print(f"\nan error occured while downloading images: {e}\n")
                finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
                if finishing == "N":
                    break

        elif choice == "5":
            csv = input("CSV path with the author names: ").strip()
            ranking = int(input("how many of the most frequent authors do you want to display? ").strip())
            similar = int(input("fuzzy similarity (0-100%): ").strip())
            txt = input(".txt path to save the result: ").strip()

            if not ranking:
                print("invalid value for ranking, defaulting to 5.")
                ranking = 5
            if similar < 0 or similar > 100:
                print("invalid value, defaulting to 80%")
                similar = 80
            if not txt:
                print("it will be saved in deduplicating.txt")
                txt = "deduplicating.txt"

            print("\nexecuting author deduplication...\n")
            processing(csv, ranking, similar, txt)
            print("\ndeduplication successfully executed.\n")

            finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
            if finishing == "N":
                break

        elif choice == "6":
            print("leaving interactive mode...")
            break
        else:
            print("\ninvalid option, try again.")

