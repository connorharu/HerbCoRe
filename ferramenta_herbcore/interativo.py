import json
import os
import sys
from main_f import species_link
from config import get_config, ask_for_missing_values

from sinonimos import extract_plants_from_txt, save_plants_to_csv, perform_lcvp_fuzzy_search, save_result_to_txt_aligned
from rpy2.robjects.packages import importr
# stats = importr('stats')

def interactive_mode():
    print("\nbem-vindo ao modo interativo!")
    print("aqui você será guiado para escolher os métodos e passar os parâmetros necessários.")

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
        print("\nescolha um método:") 
        print("[1] informações sobre os dados")
        print("[2] filtragens e consultas no banco")
        print("[3] verificação do nome científico")
        print("[4] imagens das exsicatas") # TO-DO
        print("[5] sair") 

        choice = input("\ndigite o número da opção: ").strip()

        if choice == "1":
            print("[1] metadados")
            print("[2] instituições participantes")
            print("[3] instituições específicas")
            print("[4] coleções")
            print("[5] conjuntos de dados específico")

            choice2 = input("\ndigite o número da opção: ").strip()

            if choice2 == "1":

                name = input("informe o nome (opcional): ").strip()
                id_ = input("informe o ID (opcional): ").strip()
                print(f"executando specieslink.get_metadata(name={name}, id={id_})...\n")

                metadata = specieslink.get_metadata(name=name, id=id_)
                if metadata:
                    print("metadados básicos:\n")
                    print(json.dumps(metadata, indent=4, ensure_ascii=False))  # exibe os metadados formatados
                    finalizar = input("\nexecutar outro método?\n[S] sim\n[N] não\natenção: é case-sensitive\n").strip()
                    if finalizar == "N":
                        break

            elif choice2 == "2":
                acronym = input("informe a sigla da instituição (opcional): ").strip()
                print(f"executando specieslink.get_institution_data(acronym={acronym})...\n")

                participants = specieslink.get_participants()
                if participants:
                    print("\n\nparticipantes:\n")
                    print(json.dumps(participants, indent=4, ensure_ascii=False))
                    finalizar = input("\nexecutar outro método?\n[S] sim\n[N] não\natenção: é case-sensitive\n").strip()
                    if finalizar == "N":
                        break

            elif choice2 == "3":
                acronym = input("informe a sigla da coleção (obrigatório caso não fornecer ID): ").strip()
                id_ = input("informe o ID (obrigatório caso não fornecer sigla): ").strip()
                lang = input("informe a linguagem (opcional): ").strip()
                print(f"executando specieslink.get_institution_data(acronym={acronym}, id={id_}, lang={lang})...\n")

                instituition = specieslink.get_institution_data(acronym=acronym, id=id_, lang=lang)
                if instituition:
                    print("\n\ninstituições específicas:\n")
                    print(json.dumps(instituition, indent=4, ensure_ascii=False))
                finalizar = input("\nexecutar outro método?\n[S] sim\n[N] não\natenção: é case-sensitive\n").strip()
                if finalizar == "N":
                    break

            elif choice2 == "4":
                acronym = input("informe a sigla da coleção (obrigatório caso não fornecer ID): ").strip()
                id_ = input("informe o ID (obrigatório caso não fornecer sigla): ").strip()
                lang = input("informe a linguagem (opcional): ").strip()
                print(f"executando specieslink.get_collection_data(acronym={acronym}, id={id_}, lang={lang})...\n")
                
                collection = specieslink.get_collection_data(acronym=acronym, id=id_, lang=lang)
                if collection:
                    print("\n\ncoleções específicas:\n")
                    print(json.dumps(collection, indent=4, ensure_ascii=False))
                finalizar = input("\nexecutar outro método?\n[S] sim\n[N] não\natenção: é case-sensitive\n").strip()
                if finalizar == "N":
                    break
            
            elif choice2 == "5":
                id_ = input("informe o ID (obrigatório): ").strip()
                print(f"executando specieslink.get_dataset_info(id={id_})...\n")

                dataset = specieslink.get_dataset_info(id=id_)
                if dataset:
                    print("\n\nconjunto de dados específicos:\n")
                    print(json.dumps(dataset, indent=4, ensure_ascii=False))
                finalizar = input("\nexecutar outro método?\n[S] sim\n[N] não\natenção: é case-sensitive\n").strip()
                if finalizar == "N":
                    break

        elif choice == "2":
            print("[1] filtragem/adição de registros em banco de dados")
            print("[2] consulta SQL")
            print("[3] atualizar valor SQL")

            choice3 = input("\ndigite o número da opção: ").strip()

            if choice3 == "1":
                filters_input = input("informe os filtros (formato chave=valor, separados por espaço): ").strip()
                table = input("informe o nome da tabela onde os registros devem ser inseridos: ").strip()
                print(f"executando specieslink.search_records(filters={filters_input}, table={table})...\n")

                filters = {}
                for item in filters_input.split():
                    if '=' not in item: # não está formatado
                        print(f"filtro mal formatado: {item} - use chave=valor")
                        return
                    else:
                        key, value = item.split('=', 1)
                        filters[key.strip()] = value.strip()

                records = specieslink.search_records(filters=filters)

                if records:
                    print(f"\n{len(records)} registros encontrados. inserindo na tabela '{table}'...")
                    specieslink.insert_into_mysql(records, db_config, table=table)
                    print("registros inseridos com sucesso.")
                else:
                    print("nenhum registro encontrado com os filtros fornecidos.")

                finalizar = input("\nexecutar outro método?\n[S] sim\n[N] não\natenção: é case-sensitive\n").strip()
                if finalizar == "N":
                    break

            elif choice3 == "2":
                filters_input = input("informe os filtros (formato chave=valor, separados por espaço): ").strip()
                table = input("informe o nome da tabela de onde os registros serão retirados: ").strip()
                columns = input("informe as colunas que quer retornar (separadas por vírgula, ou deixe em branco para todas): ").strip()
                output_csv_path = input("informe o caminho completo para salvar o arquivo CSV: ").strip()
                print(f"executando specieslink.export_to_csv(filters={filters_input}, table={table}, columns={columns}, output_csv_path={output_csv_path})...\n")

                filters = {}
                for item in filters_input.split():
                    if '=' not in item:  # não está formatado
                        print(f"filtro mal formatado: {item} - use chave=valor")
                        return
                    else:
                        key, value = item.split('=', 1)
                        filters[key.strip()] = value.strip()

                # formatar columns?
                columns = ", ".join([col.strip() for col in columns.split(",")]) if columns else None

                specieslink.export_to_csv(filters=filters, db_config=db_config, table=table, columns=columns, output_csv_path=output_csv_path)

                finalizar = input("\nexecutar outro método?\n[S] sim\n[N] não\natenção: é case-sensitive\n").strip()
                if finalizar == "N":
                    break

            elif choice3 == "3":
                update_input = input("informe o campo e o valor novo a atualizar (formato chave=valor, separados por espaço): ").strip()
                filters_input = input("informe o campo e o valor antigo a ser atualizado (formato chave=valor, separados por espaço): ").strip()
                table = input("informe o nome da tabela de onde os registros serão atualizados: ").strip()
                print(f"executando specieslink.update_records(filters={filters_input}, update_values={update_input}, table={table})...\n")

                filters = {}
                for item in filters_input.split():
                    if '=' not in item: # não está formatado
                        print(f"filtro mal formatado: {item} - use chave=valor")
                        return
                    else:
                        key, value = item.split('=', 1)
                        filters[key.strip()] = value.strip()

                update_values = {}
                for item in update_input.split():
                    if '=' not in item: # não está formatado
                        print(f"valor de atualização mal formatado: {item} - use chave=valor")
                        return
                    else:
                        key, value = item.split('=', 1)
                        update_values[key.strip()] = value.strip()

                specieslink.update_records(filters=filters, update_values=update_values, db_config=db_config, table=table)

                finalizar = input("\nexecutar outro método?\n[S] sim\n[N] não\natenção: é case-sensitive\n").strip()
                if finalizar == "N":
                    break

        elif choice == "3":
            print("[1] extrair nomes do txt em salvar em csv")
            print("[2] busca fuzzy no R com base nos nomes do csv")

            choice4 = input("\ndigite o número da opção: ").strip()

            if choice4 == "1":
                txt = input("informe o arquivo txt de entrada com o nome científico das plantas: ").strip()
                csv = input("informe o nome para o arquivo csv de saída com o nome científico das plantas: ").strip()
                print(f"executando sinonimos.extract_plants_from_txt(--txt {txt} --csv {csv})...\n")

                extract = extract_plants_from_txt(txt)
                if extract:
                    print("\nextraindo o nome das plantas")
                    save_plants_to_csv(extract, csv)
                    print(f"resultado salvo em {csv}\n")

                finalizar = input("\nexecutar outro método?\n[S] sim\n[N] não\natenção: é case-sensitive\n").strip()
                if finalizar == "N":
                    break

            elif choice4 == "2":
                csv = input("informe o nome para o arquivo csv de entrada com o nome científico das plantas: ").strip()
                txt = input("informe o arquivo txt de saída com a pesquisa no Leipzig: ").strip()
                max_distance = input("informe a margem de erro máxima para erros gramaticais e afina (padrão 0.1): ").strip()
                if max_distance:
                    try:
                        max_distance = float(max_distance)
                        print(f"executando sinonimos.perform_lcvp_fuzzy_search(--csv {csv} --txt {txt} --max_distance {max_distance})...\n")
                    except ValueError:
                        print("valor inválido para margem de erro. usando valor padrão de 0.1\n")
                        max_distance = 0.1
                else:
                    max_distance = 0.1
                    print(f"executando sinonimos.perform_lcvp_fuzzy_search(--csv {csv} --txt {txt})...\n")

                fuzzy = perform_lcvp_fuzzy_search(csv, max_distance)
                if fuzzy:
                    print("\nverificando com o LCVP...")
                    save_result_to_txt_aligned(fuzzy, txt)
                    print(f"resultado salvo em {txt}\n")

                finalizar = input("\nexecutar outro método?\n[S] sim\n[N] não\natenção: é case-sensitive\n").strip()
                if finalizar == "N":
                   break

        elif choice == "4":
            # TO-DO
            break

        elif choice == "5":
            print("saindo do modo interativo...")
            break
        else:
            print("\nopção inválida, tente novamente.")
