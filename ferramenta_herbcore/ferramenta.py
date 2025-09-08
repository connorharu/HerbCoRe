import json
import argparse
import os
from main_f import species_link
from interativo import interactive_mode
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

    # escolha do modo de operação
    print("\ngostaria de um passo a passo para executar os métodos da ferramenta, ou continuar sem auxílio?")
    print("[1] passo-a-passo (suporte para execução)")
    print("[2] sem auxílio (argumentos pelo terminal - se já tiver passado um comando, será executado)")

    choice = input("escolha uma opção: ").strip()

    if choice == "1":
        interactive_mode()
        return  # sai da função main() para evitar executar argparse depois

    print("ATENÇÃO: PARA EXECUTAR MÉTODOS RELACIONADOS À COLETA DE URLS E IMAGENS, DEVE-SE SEGUIR PELO [1] PASSO-A-PASSO, OU EXECUTAR POR SI PRÓPRIO O CÓDIGO NO REPOSITÓRIO INFORMADO NO README.")

    # caso queira executar sozinho, vai pro parser normal, argumentos pelo terminal
    parser = argparse.ArgumentParser(description='interface dos métodos da ferramenta')
    subparsers = parser.add_subparsers(dest="command", help="método a ser executado") # subparsers permitem que métodos utilizem de argumentos diferentes e serem chamados ou não

    metadados = subparsers.add_parser("metadata", help="metadados básicos") # cria um objeto argumentparser e descreve seu script quando alguém usa -h ou --help
    metadados.add_argument('--name', type=str, help='nome a ser identificado') # argumento --name, opcional, para a filtragem de um nome
    metadados.add_argument('--id', type=str, help='id a ser identificado')

    participants = subparsers.add_parser("participants", help="instituições participantes")

    instituition = subparsers.add_parser("instituition", help="instiuições específicas")
    instituition.add_argument('--acronym', type=str, help='sigla a ser identificada')
    instituition.add_argument('--id', type=str, help='id a ser identificado')
    instituition.add_argument('--lang', type=str, help='linguagem escolhida')

    collection = subparsers.add_parser("collection", help="coleções específicas")
    collection.add_argument('--acronym', type=str, help='sigla a ser identificada')
    collection.add_argument('--id', type=str, help='id a ser identificado')
    collection.add_argument('--lang', type=str, help='linguagem escolhida')

    dataset = subparsers.add_parser("dataset", help="conjunto de dados específicos")
    dataset.add_argument('--id', type=str, help='id a ser identificado')

    records = subparsers.add_parser("records", help="registros filtrados")
    records.add_argument('--filters', required=True, nargs='*', help="filtros no formato chave=valor (ex: família=rosas)") # nargs permite múltiplos filtros no formato chave=valor
    records.add_argument('--table', type=str, required=True, help="tabela do banco de dados")

    export = subparsers.add_parser("export", help="realiza uma consulta SQL e retorna um CSV")
    export.add_argument('--filters', required=True, nargs='*', help="filtros no formato chave=valor (ex: família=rosas)")
    export.add_argument('--table', type=str, required=True, help="tabela do banco de dados")
    export.add_argument('--columns', type=str, help="colunas que devem ser trazidas")
    export.add_argument('--output_csv_path', type=str, required=True, help="caminho para salvar o CSV")

    update = subparsers.add_parser("update", help="atualiza registros do banco baseado em parâmetros")
    update.add_argument('--filters', required=True, nargs='*', help="filtros no formato chave=valor (ex: família=rosas)")
    update.add_argument('--update_values', required=True, nargs='*', help="valores a serem atualizados no formato chave=valor (ex: estado=São Paulo familia=Piperaceae)")
    update.add_argument('--table', type=str, required=True, help="tabela do banco de dados")

    args = parser.parse_args()

    specieslink = species_link(api_key=api_key) # o usuario passa sua propria chave da API
    
    # metadados básicos
    if args.command == "metadata":
        metadata = specieslink.get_metadata(name=args.name, id=args.id) # parametro do método, por ex pede o nome da instituiçao
        if metadata: # se tiver metadados sendo requisitados
            print("\n\nmetadados básicos:\n")
            print(json.dumps(metadata, indent=4, ensure_ascii=False)) # print formatado


    # coleções e instituições participantes
    elif args.command == "participants":
        participants = specieslink.get_participants()
        if participants:
            print("\n\nparticipantes:\n")
            print(json.dumps(participants, indent=4, ensure_ascii=False)) # print formatado


    # dados de uma instituição por sigla
    elif args.command == "instituition":
        instituition = specieslink.get_institution_data(acronym=args.acronym, id=args.id, lang=args.lang)
        if instituition:
            print("\n\ninstituições específicas:\n")
            print(json.dumps(instituition, indent=4, ensure_ascii=False)) # print formatado

    # dados de uma coleção por identificador
    elif args.command == "collection":
        collection = specieslink.get_collection_data(acronym=args.acronym, id=args.id, lang=args.lang)
        if collection:
            print("\n\ncoleções específicas:\n")
            print(json.dumps(collection, indent=4, ensure_ascii=False)) # print formatado 

    # dados de um conjunto de dados com um identificador especifico
    elif args.command == "dataset":
        dataset = specieslink.get_dataset_info(id=args.id)
        if dataset:
            print("\n\nconjunto de dados específicos:\n")
            print(json.dumps(dataset, indent=4, ensure_ascii=False)) # print formatado

    # registros filtrados
    elif args.command == "records":
        filters = {} # dicionário de filtros
        for item in args.filters: # para cada filtro adicionado
            key, value = item.split('=') # divide chave e valor com = como delimitador
            filters[key] = value # adiciona o par ao dicionário

        records = specieslink.search_records(filters=filters)
        if records:
            print("\n\nregistros filtrados:\n")
            # print(json.dumps(records, indent=4, ensure_ascii=False)) # print formatado, descomente para ver no terminal. NÃO RECOMENDADO SE FOR UMA PESQUISA COM MUITOS RESULTADOS
            
            specieslink.insert_into_mysql(records, db_config, table=args.table)     

    # consulta SQL
    elif args.command == "export":
        filters = {}  # dicionário de filtros
        for item in args.filters:  # para cada filtro adicionado
            key, value = item.split('=')  # divide chave e valor com = como delimitador
            filters[key] = value  # adiciona o par ao dicionário

        specieslink.export_to_csv(filters=filters, db_config=db_config, table=args.table, columns=args.columns, output_csv_path=args.output_csv_path)

    # atualizar o banco
    elif args.command == "update":
        filters = {}  # dicionário de filtros
        for item in args.filters:  # para cada filtro adicionado
            key, value = item.split('=')  # divide chave e valor com = como delimitador
            filters[key] = value  # adiciona o par ao dicionário

        update_values = {} # valores atualizados
        for item in args.update_values:  # para cada valor a ser atualizado
            key, value = item.split('=')  # divide chave e valor com '='
            update_values[key] = value  # adiciona o par ao dicionário

        specieslink.update_records(filters=filters, update_values=update_values, db_config=db_config, table=args.table)

if __name__ == "__main__":
    main() 
