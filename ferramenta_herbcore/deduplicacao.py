import argparse
import pandas as pd
from collections import defaultdict, Counter # para contar elementos e agrupar dados
from fuzzywuzzy import fuzz # para fazer comparações de similaridade entre strings

def autores_csv(csv_file):
    df = pd.read_csv(csv_file)
    return df.iloc[:, 0].dropna().astype(str).tolist() # retorna a primeira coluna como lista de strings removendo valores vazios

def deduplica_autores(authors, similares=90):
    groups = [] # armazenar nomes semelhantes
    used = set() # rastrear indices agrupados

    for i, author in enumerate(authors): # pra cada autor
        if i in used: # se ja usou esse nome
            continue
        group = [author] # grupo com o autor atual
        used.add(i) # adiciona o indice como utilizado
        for j in range(i + 1, len(authors)): # compara com os próximos autores
            if j in used: # se o nome que ele encontrou agora se parece com algum de outro grupo, evitando duplicatas
                continue
            score = fuzz.token_sort_ratio(author, authors[j]) # calcula similaridade entre o nome atual e o grupo
            if score >= similares: # se a similaridade é maior ou igual a especificada
                group.append(authors[j]) # adiciona ao grupo
                used.add(j) # marca o indice como usado
        groups.append(group) # adiciona o grupo final ao ranking de grupos a retornar
    return groups # retorna o ranking de autores

def nome_autor(group):
    # retorna o nome mais comum (ou o mais "limpo" em caso de empate)
    return Counter(group).most_common(1)[0][0]

def rankeia_autores(groups, ranking):
    freq = Counter() # dicionario contador de frequencia
    for group in groups:
        representative = nome_autor(group) # pega o nome representativo do grupo
        freq[representative] += len(group) # soma o tamanho do grupo ao contador desse nome p/ pegar quantia de ocorrencias
    return freq.most_common(ranking) # retorna os x autores mais frequentes

def deduplicacao_de_nomes(csv_file, ranking, similares):
    authors = autores_csv(csv_file)
    print(f"total de nomes lidos: {len(authors)}")

    print("iniciando deduplicação fuzzy dos autores...")
    groups = deduplica_autores(authors, similares) # agrupa nomes semelhantes
    print(f"número de grupos de autores únicos: {len(groups)}")

    top_authors = rankeia_autores(groups, ranking) # conta quantas vezes cada autor apareceu e ordena

    print(f"\ntop {ranking} autores mais frequentes (agrupados com similaridades={similares}):")
    for i, (author, count) in enumerate(top_authors, start=1):
        print(f"{i}. {author} - {count} ocorrências")

    return top_authors

def main():
    parser = argparse.ArgumentParser(description="deduplicação e ranqueamento de autores de nomes científicos.")
    subparsers = parser.add_subparsers(dest="command")

    dedup_parser = subparsers.add_parser("deduplica_autores", help="deduplicação fuzzy dos nomes de autores")
    dedup_parser.add_argument("--csv", required=True, help="arquivo CSV contendo os nomes dos autores")
    dedup_parser.add_argument("--ranking", type=int, default=5, help="número de autores mais frequentes a exibir")
    dedup_parser.add_argument("--similares", type=int, default=90, help="nomes com similaridades fuzzy (0-100%)")

    args = parser.parse_args()

    if args.command == "deduplica_autores":
        deduplicacao_de_nomes(args.csv, args.ranking, args.similares)

if __name__ == "__main__":
    main()
