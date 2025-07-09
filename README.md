# HerbCoRe
Catalogação do meu código sobre a HerbCoRe: uma ferramenta para seleção e filtragem de acervos de dados relacionados à plantas de herbários, com auxílio do professor André Luis Schwerz. 

## Sobre a pasta ferramenta_herbcore:
Código feito para consulta de metadados, tais como tipos, listas ou dados de coleção e/ou instituição, além de informações sobre um conjunto de dados, através de uma API do specieslink. Há possibilidade de filtrar os registros de biodiversidade para receber dados mais específicos - o retorno não possui limitação de tamanho.

Capaz de passar os dados para o MySQL, colocando os registros dentro de uma tabela para pesquisas mais profundas.

Ferramenta separada em cinco arquivos diferentes:
- config.py: configurações de usuário para uso do código (chave da API, usuário do banco, senha, host...);
- ferramenta.py: versão ininterrupta da ferramenta - execução de métodos do banco de dados/speciesLink fornecendo todos os argumentos em um único envio;
- interativo.py: versão interativa e incremental da ferramenta - execução de métodos, relacionados ao banco de dados/speciesLink/leipzig, fornecendo seus argumentos passo-a-passo;
- main_f.py: desenvolvimento dos métodos do banco de dados/speciesLink;
- sinonimos.py: versão direta da verificação dos sinônimos dos nomes científicos fornecidos a partir do [catálogo de Leipzig](https://www.nature.com/articles/s41597-020-00702-z).
- deduplicacao.py: versão direta para o método de rankeamento dos autores de nomes científicos de registros.


Utilize do crawler encontrado [aqui](https://github.com/xaaaandao/downloader-specieslink/tree/master) para conseguir as URLs e as imagens.
Leia mais sobre o catálogo de Leipzig e o lcvplants [aqui](https://github.com/idiv-biodiversity/lcvplants).

Instale o dezoomify-rs 2.12.3[aqui](https://github.com/lovasoa/dezoomify-rs/releases/tag/v2.12.3) - DEIXE-O NO DIRETÓRIO ferramenta_herbcore, NÃO EM downloader-specieslink-master!

Obtenha uma chave para a API se cadastrando no species_link [aqui](https://specieslink.net/ws/1.0/)

## Pré-requisitos:
- Utilizar de ```requirements.txt``` para instalar os requisitos utilizando o seguinte comando:
```
pip install -r requirements.txt
```

## Como usar a ferramenta:
Ao chamar ```python ferramenta.py```, ou qualquer comando da ferramenta ininterrupta, o menu no terminal perguntará se o usuário deseja acessar a ferramenta ininterrupta ou a ferramenta interativa. Caso escolha pela ferramenta ininterrupta, siga para o tópico relacionado à execução direta dos comandos, diretamente abaixo do próximo. Caso contrário:

### Ferramenta interativa (passo-a-passo):
Após a escolha pela ferramenta interativa, abre-se outro menu, com mais opções de execução:

```
bem-vindo ao modo interativo!
aqui você será guiado para escolher os métodos e passar os parâmetros necessários.

escolha um método:
[1] informações sobre os dados
[2] filtragens e consultas no banco
[3] verificação do nome científico
[4] imagens das exsicatas
[5] autores de nomes científicos confiáveis
[6] sair
```
Dentro da ferramenta interativa, os métodos estão distribuídos em grupos dentro desses quatro tópicos, o quinto sendo para desistir da consulta. Digitar um número diferente dos propostos retornará o mesmo menu. Por exemplo, ao digitar "1":

```
digite o número da opção: 1 <- número digitado no terminal
[1] metadados
[2] instituições participantes
[3] instituições específicas
[4] coleções
[5] conjuntos de dados específico
```

Cada um representa um método da ferramenta. Para uma melhor descrição do funcionamento de cada método, ler a seção da ferramenta ininterrupta, ou fazer ```python ferramenta.py NOMEDOMÉTODO -h```. Digitar um número diferente dos propostos te retornará para o menu anterior.
Se, por exemplo, digitarmos "3", ele pedirá todas as informações relacionadas à aquele método, uma por uma:
```
digite o número da opção: 3 <- número digitado no terminal
informe a sigla da coleção (obrigatório caso não fornecer ID): USP
informe o ID (obrigatório caso não fornecer sigla):    # não forneci!
informe a linguagem (opcional): en
executando specieslink.get_institution_data(acronym=USP, id=, lang=en)... # a resposta foi fornecida logo abaixo, mas como é muito longa, não coloquei aqui!
```

No final da execução, ele pergunta se o usuário deseja executar outro método. A resposta deve ser em caixa alta, como indicado na caixa do menu:

```
executar outro método?
[S] sim
[N] não
atenção: é case-sensitive
```
### Ferramenta ininterrupta (execução direta):

A ferramenta te pede um conjunto de comandos pelo terminal para executar o que se pede. Caso desconheça os parâmetros necessários para a busca, você pode usar de ```-h``` e ver os comentários com ajuda adicionados.
```python ferramenta.py -h``` lhe mostrará o seguinte:
```

interface dos métodos de ferramenta.py

positional arguments:
  {metadata,participants,instituition,collection,dataset,records}
                        método a ser executado
    metadata            metadados de espécies
    participants        instituições participantes
    instituition        instiuições específicas
    collection          coleções específicas
    dataset             conjunto de dados específicos
    records             registros filtrados
    export              realiza uma consulta SQL e retorna um CSV
    update              atualiza registros do banco baseado em parâmetros
    urls                urls a se obter através de downloader-specieslink-master
    dezoomify_rs        imagens a se obter das urls através de downloader-specieslink-master
```

```python sinonimos.py -h``` lhe mostrará o seguinte:
```
interface dos métodos para análise do nome científico

positional arguments:
  {extract,fuzzy}  método a ser executado
    extract        extrair nomes do txt em salvar em csv
    fuzzy          busca e visualização de txt fuzzy com base nos nomes do csv
    fuzzy_line     atualização no banco de dados fuzzy linha-a-linha com base nos nomes do csv
```

```python deduplicacao.py -h``` lhe mostrará o seguinte:
```
ferramenta para identificação fuzzy de taxonomistas confiáveis

positional arguments:
  {deduplicador}  método a ser executado
    deduplicador  executar o deduplicador fuzzy de nomes
```

Procurar por algo mais específico, como os parâmetros dos métodos demonstrados acima, requer que você especifique o método quando der o comando de ajuda.
Por exemplo, ```python ferramenta.py metadata -h``` lhe mostrará o seguinte:
```
usage: ferramenta.py metadata [-h] --api_key API_KEY [--name NAME] [--id ID]

options:
  -h, --help         show this help message and exit
  --name NAME        nome a ser identificado
  --id ID            id a ser identificado
```

### Exemplos de uso dos comandos, na ordem dos métodos:
```python
# exemplos de ferramenta.py:
python ferramenta.py metadata --name "Secretaria Estadual" --id "400"
python ferramenta.py participants
python ferramenta.py instituition --acronym "USP" --id "393" --lang "en"  
python ferramenta.py collection --acronym "ESA" --id "8" --lang "pt-br"
python ferramenta.py dataset --id "8"
python ferramenta.py records --filters family=piperaceae barcode="FURB38192" --table tabela_exemplo
python ferramenta.py export --filters family=piperaceae --table tabela_exemplo --colums "coluna_exemplo" --output_csv_path resultados.csv
python ferramenta.py update --filters stateprovince="São Paulo" --update_values="Santa Catarina" --table tabela_exemplo
Não há uso do comando urls e dezoomify_rs de maneira direta, somente através da ferramenta interativa, no item "[4] imagens das exsicatas". Para execução direta, recomenda-se o uso direto desse código, contido no repositório citado neste mesmo README.

# exemplos de sinonimos.py:
python sinonimos.py extract --txt teste-08-04.txt --csv aaa.csv
python sinonimos.py fuzzy --csv aaa.csv --output ccc.txt --max_distance 0.1 
python sinonimos.py fuzzy --csv aaa.csv --output ccc.txt (max_distance é opcional!)
python sinonimos.py fuzzy_line --csv teste.csv --tabela registros_biodiversidade --coluna scientificname_NOVO --status status_plantas --max_distance 0.1

# exemplos de deduplicacao.py:
python deduplicacao.py deduplicar_autores deduplicador --csv nomes2-15-06.csv --ranking 5 --similar 100 --txt nome.txt
```

## Agradecimentos

Deixo descrito nessa seção a minha gratidão ao [Alexandre Yuji Kajihara](https://github.com/xaaaandao), criador dos métodos contidos em downloader-specieslink-master. Com sua permissão, adicionei o seu código nessa ferramenta assim deixando-a mais completa, sem contar o auxílio recebido pelo caminho. Obrigado.