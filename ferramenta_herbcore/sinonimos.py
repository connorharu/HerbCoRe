import argparse
import os
os.environ["R_HOME"] = r"C:\\Program Files\\R\\R-4.4.2" # alterar caso nao seja o mesmo para o usuario
os.environ["PATH"] = r"C:\\Program Files\\R\\R-4.4.2\\bin\\x64" + ";" + os.environ["R_HOME"] # alterar caso nao seja o mesmo para o usuario

import re # pra mexer na string
import csv # auto-explicativo
import rpy2.robjects as robjects # mexer com r a partir do python
from rpy2.robjects.packages import importr # importar pacotes r pro python
from rpy2.robjects.vectors import StrVector # importar o vetor r

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

# busca fuzzy no R com base nos nomes do csv
def perform_lcvp_fuzzy_search(csv_file, max_distance=0.1): # distancia maxima dita qual a ''margem de erro''
    plant_names = read_plants_from_csv(csv_file) # pegando as plantas

    print(plant_names)

    r_plant_names = StrVector(plant_names) # conexão com o R, convertendo os nomes pra um vetor de R pra que ele consiga reconhecer a lista
    
    lcvp_plants = importr('lcvplants')  # importando a biblioteca lcvp_plants
    result = robjects.r['lcvp_fuzzy_search'](r_plant_names, max_distance=max_distance) # realiza a pesquisa

    # convertendo o resultado pra um dataframe do R
    result_df = robjects.r['as.data.frame'](result)
    return result_df

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

    fuzzy = subparsers.add_parser("fuzzy", help="busca fuzzy no R com base nos nomes do csv")
    fuzzy.add_argument("--csv", required=True, help="arquivo csv de entrada")
    fuzzy.add_argument("--output", required=True, help="arquivo txt de saída com resultado")
    fuzzy.add_argument("--max_distance", type=float, default=0.1, help="distância máxima para verificação fuzzy (valor recomendado: 0.1)")

    args = parser.parse_args()

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

if __name__ == "__main__":
    main()

