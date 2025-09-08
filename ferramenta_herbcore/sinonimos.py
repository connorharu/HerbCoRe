import argparse
import os

def setup_r_environment():
    config = get_config()
    if not config or 'r_home' not in config:
        raise RuntimeError("Configuração inválida: r_home não foi definido. Rode ferramenta.py primeiro.")

    r_home = config['r_home']

    os.environ["R_HOME"] = r_home
    os.environ["PATH"] = os.path.join(r_home, "bin", "x64") + ";" + os.environ.get("PATH", "")

import re # pra mexer na string
import csv # auto-explicativo
import rpy2.robjects as robjects # mexer com r a partir do python
from rpy2.robjects.packages import importr # importar pacotes r pro python
from rpy2.robjects.vectors import StrVector # importar o vetor r
import pymysql
from config import get_config, ask_for_missing_values, save_config
from main_f import species_link
from rpy2.rinterface_lib.sexp import NULLType

# le txt e extrai o nome das plantas
def extract_plants_from_txt(txt_file):
    with open(txt_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # extraindo plantas entre as aspas
    plant_names = re.findall(r'"([^"]+)"', content)
    return plant_names

# salva a lista de plantas em um arquivo CSV
def save_plants_to_csv(plant_names, csv_file):
    with open(csv_file, 'w', encoding='utf-8') as file:
        if not plant_names:
            print("lista vazia\n")
            return
        # escrevendo cada planta no formato com vírgula e quebra de linha após cada uma
        for name in plant_names[:-1]: # pra todos os nomes menos o ultimo
            file.write(f'"{name}",\n')  # para todos, coloca vírgula e quebra de linha
        file.write(f'"{plant_names[-1]}"\n')  # menos pro ultimo, que é so quebra de linha

# lê os nomes das plantas do csv
def read_plants_from_csv(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        # remove aspas e extrai os nomes das plantas
        plants = [row[0].strip('"') for row in reader]
    return plants

# busca fuzzy por lista no R com base nos nomes do csv e mostra o resultado em um txt
def perform_lcvp_fuzzy_search(csv_file, max_distance=0.1): # distancia maxima dita qual a ''margem de erro''
    plant_names = read_plants_from_csv(csv_file) # pegando as plantas

    print(plant_names)

    r_plant_names = StrVector(plant_names) # conexão com o R, convertendo os nomes pra um vetor de R pra que ele consiga reconhecer a lista
    
    lcvp_plants = importr('lcvplants')  # importando a biblioteca lcvp_plants
    result = robjects.r['lcvp_fuzzy_search'](r_plant_names, max_distance=max_distance) # realiza a pesquisa

    # convertendo o resultado pra um dataframe do R
    result_df = robjects.r['as.data.frame'](result)

    genuses = list(result_df.rx2('Input.Genus'))
    epithets = list(result_df.rx2('Input.Epitheton'))
    
    nomes_encontrados = [f"{genus} {epithet}" for genus, epithet in zip(genuses, epithets)] # nome das plantas completo

    for plant_name in plant_names:
        if plant_name not in nomes_encontrados: # existe a planta?
            print(f"\n <!!!!!!> planta '{plant_name}' não encontrada no LCVP! <!!!!!!>\n")

    return result_df

# pesquisa fuzzy linha-a-linha que somente atualiza o banco, nao demonstra em txt
def perform_lcvp_fuzzy_search_per_line(csv_file, db_config, tabela, coluna, specieslink, status, max_distance=0.1):
    plant_names = read_plants_from_csv(csv_file)  # pegando as plantas
    lcvp_plants = importr('lcvplants')  # importando a biblioteca lcvp_plants
    atualizados = 0  # qtde plantas que vão atualizar o nome
    indisponiveis = 0 # qtde plantas nao encontradas no LCVP
    mantidos = 0 # qtde plantas com nomes mantidos

    for plant_name in plant_names: # p/ cada nome distinto
        print(f"processando: {plant_name}...")
        try:
            r_plant_name = StrVector([plant_name]) # conexão com o R, convertendo os nomes pra um vetor de R pra que ele consiga reconhecer a lista
            result = robjects.r['lcvp_fuzzy_search'](r_plant_name, max_distance=max_distance)  # realiza a pesquisa
            result_df = robjects.r['as.data.frame'](result)   # convertendo o resultado pra um dataframe do R

            if isinstance(result, NULLType): # se o resultado da pesquisa nao está no LCVP
                print(f"<!!!!!!> planta '{plant_name}' não encontrada no LCVP! <!!!!!!>")

                status_final = 'indisponivel'
                filters = {'scientificname': plant_name}
                update_values = {status: status_final} # salvar status em um campo separado

                specieslink.update_records(filters, update_values, db_config, tabela)

                indisponiveis += 1
                continue

            # extrai todas as colunas relevantes como listas de strings
            statuses = [status.strip().lower() for status in result_df.rx2('Status')] # [status_a, status_b...]
            output_taxa = [name.strip() for name in result_df.rx2('Output.Taxon')] # [nome_a, nome_b...]
            # save_result_to_txt_per_line_aligned(result_df, output)

            if 'accepted' in statuses: # se tem alguma instancia onde esse nome é aceito
                print(f"'{plant_name}' tem pelo menos uma entrada com status 'accepted', não será atualizado")

                status_final = 'accepted'
                filters = {'scientificname': plant_name}
                update_values = {status: status_final}

                specieslink.update_records(filters, update_values, db_config, tabela)

                mantidos += 1
                continue
            elif 'synonym' in statuses: # caso tenha alguma instancia de sinonimo, quando nao tem aceito
                status_final = 'synonym'
                idx = statuses.index('synonym')  # pega o primeiro synonym
                novo_nome = output_taxa[idx] # pega o nome na mesma posiçao do status synonym encontrado que estiver o nome
                print(f"atualizando '{plant_name}' para '{novo_nome}' por ter status 'synonym'")

                filters = {'scientificname': plant_name} # para todos os nomes do banco iguais ao da planta sendo analisada
                update_nomes = {coluna: novo_nome} # atualizar para esse valor alem do status
                specieslink.update_records(filters, update_nomes, db_config, tabela)

                update_status = {status: status_final} # salvar status em um campo separado
                specieslink.update_records(filters, update_status, db_config, tabela)

                atualizados += 1
                continue
            elif 'unresolved' in statuses: # nao tem nem sinonimo nem aceito
                status_final = 'unresolved'
                filters = {'scientificname': plant_name}
                update_values = {status: status_final} # salvar status em um campo separado

                specieslink.update_records(filters, update_values, db_config, tabela)

                print(f"'{plant_name}' não possui status 'synonym' e nenhuma instância 'accepted', ignorado")
                mantidos += 1

        except Exception as e:
            print(f"erro ao processar '{plant_name}': {e}")

    print(f"\ntotal de nomes atualizados: {atualizados} | nomes não encontrados: {indisponiveis} | nomes mantidos: {mantidos}")

# salva o resultado do R em um arquivo TXT com alinhamento visual
def save_result_to_txt_aligned(result_df, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        columns = list(result_df.colnames) # extraindo as colunas do data frame R e converte pra uma lista do python
        
        # pra cada coluna, pega o seu nome e o dado de maior valor, e o tamanho da coluna vai ser determinado por qual for maior entre os dois
        max_widths = [max(len(col), max(len(str(val)) for val in result_df[i])) for i, col in enumerate(columns)]
        
        # pra cada coluna, ajusta o tamanho do dado pro valor do tamanho da coluna max_width, preenchendo com ' ' se precisar
        header = '  '.join(col.ljust(max_widths[i]) for i, col in enumerate(columns))
        file.write(header + '\n') # escreve o cabeçalho e quebra a linha
        file.write('-' * len(header) + '\n')  # linha separadora com o tamanho do cabeçalho pra separar das respostas
        
        # convertendo o data frame do R pra ser iterável no python
        rows = [list(row) for row in zip(*[result_df[i] for i in range(len(columns))])]
        # acessa os dados de cada coluna do df, e zip cria uma tupla com os dados de cada coluna.
        # list converte cada tupla em uma lista, criando uma lista de listas - uma lista de linhas
        
        for row in rows:
            # converte o valor em string, e ajusta o valor da coluna pro seu tamanho máximo
            # depois junta os valores ajustados com '  ' de espaçamento entre eles
            formatted_row = '  '.join(str(val).ljust(max_widths[i]) for i, val in enumerate(row))
            file.write(formatted_row + '\n')

def main():
    parser = argparse.ArgumentParser(description='interface dos métodos para análise do nome científico')
    subparsers = parser.add_subparsers(dest='command', help='método a ser executado')    

    extract = subparsers.add_parser("extract", help="extrair nomes do txt em salvar em csv")
    extract.add_argument("--txt", dest="txt_file", required=True, help="arquivo txt de entrada")
    extract.add_argument("--csv", dest="csv", required=True, help="arquivo txt de saída")

    fuzzy = subparsers.add_parser("fuzzy", help="busca e visualização de txt fuzzy com base nos nomes do csv")
    fuzzy.add_argument("--csv", required=True, help="arquivo csv de entrada")
    fuzzy.add_argument("--output", required=True, help="arquivo txt de saída com resultado")
    fuzzy.add_argument("--max_distance", type=float, default=0.1, help="distância máxima para verificação fuzzy (valor recomendado: 0.1)")

    fuzzy_line = subparsers.add_parser("fuzzy_line", help="atualização no banco de dados fuzzy linha-a-linha com base nos nomes do csv")
    fuzzy_line.add_argument("--csv", required=True, help="arquivo csv de entrada")
    fuzzy_line.add_argument("--max_distance", type=float, default=0.1, help="distância máxima para verificação fuzzy (valor recomendado: 0.1)")
    fuzzy_line.add_argument("--tabela", required=True, help="nome da tabela no banco de dados")
    fuzzy_line.add_argument("--coluna", required=True, help="nome da nova coluna PRÉ-CRIADA para armazenar o nome atualizado")
    fuzzy_line.add_argument("--status", required=True, help="nome da nova coluna PRÉ-CRIADA para armazenar o status do nome original")

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

    # extrair nomes do txt em salvar em csv
    if args.command == "extract":
        print("\nextraindo o nome das plantas")
        extract = extract_plants_from_txt(args.txt_file)
        save_plants_to_csv(extract, args.csv)
        print(f"resultado salvo em {args.csv}\n")

    # busca fuzzy no R com base nos nomes do csv
    elif args.command == "fuzzy":
        print("\nexecutando busca fuzzy no R")
        fuzzy = perform_lcvp_fuzzy_search(args.csv, max_distance=args.max_distance)
        save_result_to_txt_aligned(fuzzy, args.output)
        print(f"resultado salvo em: {args.output}\n")

    # busca fuzzy linha-a-linha no R com base nos nomes do csv
    elif args.command == "fuzzy_line":
        print("\nexecutando busca fuzzy linha a linha no R")

        fuzzy_line = perform_lcvp_fuzzy_search_per_line(
            csv_file=args.csv,
            db_config=db_config,
            tabela=args.tabela,
            coluna=args.coluna,
            specieslink=specieslink,
            status=args.status,
            max_distance=args.max_distance
        )
        
        print(f"\nresultados salvos na coluna '{args.coluna}' da tabela '{args.tabela}'")

if __name__ == "__main__":
    main()