import argparse
import pandas as pd
from rapidfuzz import fuzz # outra biblioteca fuzzy
from collections import Counter # contagem de frequencia
import re

def limpar_nome(nome): # tirar nomes NULL, espaços extras etc
    if pd.isna(nome):
        return None # retorna None se o valor for nulo
    nome = nome.strip() # remove espaços nas pontas
    nome = re.sub(r"\s+", " ", nome)  # remove múltiplos espaços
    return nome if nome else None # se string vazia, retorna None

def extrair_nomes_individuais(nome):
    if not nome:
        return [] # se nao tiver nome nao adiciona
    return [n.strip() for n in re.split(r"[;&]", nome)] # separa e limpa nomes separados por ; ou &

def agrupar_nomes(nomes, similar): # agrupar nomes por similaridade fuzzy
    grupos = [] # grupos com os autores

    for nome in nomes: # para cada nome na lista de nomes
        if not nome: # se for nulo, pula
            continue

        nomes_individuais = extrair_nomes_individuais(nome) # divide nomes em partes caso tenha ; ou &
        grupo_ids = set() # se um nome pertencer a um certo grupo, vai ser marcado nessa variavel

        for nome_ind in nomes_individuais: # para cada pedaço de nome
            for i, grupo in enumerate(grupos): # percorre cada grupo no indice i
                if any(fuzz.token_sort_ratio(nome_ind, membro_ind) >= similar # se encontrar similaridade suficiente
                       for membro in grupo # para cada membro (simples ou composto)
                       for membro_ind in extrair_nomes_individuais(membro)): # para cada membro de um possível nome composto
                    grupo_ids.add(i) # marca como grupo compativel

        if grupo_ids: # se encontrou grupos compativeis com o nome testado
            novo_grupo = set([nome]) # cria novo grupo contendo esse nome
            for gid in sorted(grupo_ids, reverse=True): # para cada grupo compatível
                novo_grupo.update(grupos[gid]) # adiciona os nomes do grupo atual
                del grupos[gid] # remove o grupo antigo da lista principal
            grupos.append(list(novo_grupo)) # adiciona grupo unificado
        else: # caso nao tenha grupo similar
            grupos.append([nome]) # cria o novo grupo com esse nome

    return grupos

def salvar_grupos_txt(grupos, todos_nomes, txt): # salva grupos detalhadamente dentro do txt
    contador = Counter(todos_nomes) # conta todas as ocorrencias originais

    with open(txt, 'w', encoding='utf-8') as f:
        for grupo in grupos: # para cada grupo
            total = sum(contador[n] for n in grupo) # soma as ocorrencias de grupos
            f.write(f"{grupo[0]} : {total} ocorrência(s)\n") # cabeçalho do grupo, ex: Pessoa: 1 ocorrência(s)
            for nome in sorted(grupo, key=lambda n: -contador[n]): # ordena nomes por numero de ocorrencias decrescente
                oc = contador[nome] # numero de ocorrencias desse nome
                f.write(f"  - {nome} ({oc})\n") # escreve nome e contagem
                for _ in range(oc):
                    f.write(f"     - {nome}\n") # lista cada ocorrencia do nome
            f.write("\n") # branco entre grupos

def processar(csv_path, ranking, similar, txt): # chama tudo
    df = pd.read_csv(csv_path) # le o csv com os nomes
    todos_nomes = df['identifiedby'].dropna().map(limpar_nome).dropna().tolist() # remove nulos e espaços extras, vira lista

    simples = []
    compostos = []

    # para cada nome na lista todos_nomes
    for n in todos_nomes:
        # verifica se o nome tem ; ou &
        if re.search(r"[;&]", n):
            # se tiver, é nome composto, adiciona na lista compostos
            compostos.append(n)
        else:
            # se não tiver, é nome simples, adiciona na lista simples
            simples.append(n)

    # lista de duplicatas
    compostos_unicos = list(dict.fromkeys(compostos)) # <-- usando dicionario pra manter valores unicos

    # agrupa fuzzy somente os simples
    grupos_simples = agrupar_nomes(simples, similar)

    # associa compoostos aos grupos correspondentes
    grupos = [] # lista final de grupos
    for grupo in grupos_simples: # para cada grupo com somente nomes individuais
        membros = set(grupo) # converte a lista de nomes em um conjunto set

        compostos_do_grupo = [ # com os nomes compostos do grupo
            comp for comp in compostos_unicos # para cada nome composto do grupo
            if any( # se ele bater com algum dos nomes simples, adiciona em compostos_unicos
                m in extrair_nomes_individuais(comp) 
                for m in membros
            )
        ]
        grupos.append(grupo + compostos_do_grupo) # adiciona compostos ao grupo

    # ordenando grupos por qtde de ocorrencias
    contador = Counter(todos_nomes)
    grupos_ordenados = sorted(
        grupos,
        key=lambda g: sum(contador[n] for n in g), # dado um grupo g (lista de nomes), soma as contagens de cada nome em contador e retorna essa soma para ordenar
        reverse=True
    )

    salvar_grupos_txt(grupos_ordenados, todos_nomes, txt) # salva o txt

    # imprime os mais frequentes
    mais_frequentes = [
        (grp[0], sum(contador[n] for n in grp))
        for grp in grupos_ordenados
    ]
    print(f"\n\ntop {ranking} taxonomistas mais frequentes:\n")
    for i, (nome, count) in enumerate(mais_frequentes[:ranking], 1):
        print(f"{i}. {nome} -> {count} ocorrência(s)")

def main():
    parser = argparse.ArgumentParser(description="agrupamento fuzzy de nomes de identificadores taxonômicos")
    parser.add_argument('--csv', type=str, required=True, help='caminho para o CSV com os autores')
    parser.add_argument('--ranking', type=int, default=10, help='numero de taxonomistas mais frequentes')
    parser.add_argument('--similar', type=int, default=60, help='similaridade fuzzy (0-100)')
    parser.add_argument('--txt', type=str, default='grupos_taxonomistas.txt', help='arquivo de saída para os grupos')

    args = parser.parse_args()
    processar(args.csv, args.ranking, args.similar, args.txt)

if __name__ == "__main__":
    main()
