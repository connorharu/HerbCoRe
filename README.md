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
Leia mais sobre o catálogo de Leipzig e o lcvplants [aqui](https://github.com/idiv-biodiversity/lcvplants). No entanto, aparenta-se que o método de instalação dos pacotes está desatualizado. Utilize o pacote ```pak``` ao invés de ```devtools```, da seguinte maneira:

```
install.packages("pak")
pak::pak("idiv-biodiversity/LCVP")
pak::pak("idiv-biodiversity/lcvplants")
```

Instale o dezoomify-rs 2.12.3 [aqui](https://github.com/lovasoa/dezoomify-rs/releases/tag/v2.12.3) - DEIXE-O NO DIRETÓRIO ferramenta_herbcore, NÃO EM downloader-specieslink-master! O mesmo deve ser feito para o diretório pipeline, caso seja utilizado.

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
Dentro da ferramenta interativa, os métodos estão distribuídos em grupos dentro desses cinco tópicos, o sexto sendo para desistir da consulta. Digitar um número diferente dos propostos retornará o mesmo menu. Por exemplo, ao digitar "1":

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

### Pipeline da ferramenta:
Siga a execução proposta no pipeline normalmente.

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
## Sobre a pasta classificador:
Código feito para a separação das imagens anteriormente obtidas em ferramenta_herbcore em tipos, como: exsicatas, imagens da planta viva e outros tipos de imagens, como aproximações do rótulo do herbário. Após a separação manual de um conjunto de treinamento, o modelo é capaz de separar o restante das imagens do acervo, permitindo que o pesquisador poupe tempo ao apenas verificar os resultados do modelo ao invés de ter que separar todas as imagens manualmente.

Ferramenta separada em dois arquivos diferentes:
- svm2.py: arquivo de código onde são descritos os métodos da ferramenta, explicados abaixo.
- svm_interativo.py: utilizado para chamar os métodos de svm2.py de forma interativa, assim como feito com ferramenta_herbcore.

## Pré-requisitos:
- Utilizar de ```requirements.txt``` para instalar os requisitos utilizando o seguinte comando:
```
pip install -r requirements.txt
```
Caso o ```requirements.txt``` já tenha sido instalado, não é necessário fazer novamente.

## Como usar a ferramenta:
Ao chamar ```python svm2.py```, ou qualquer comando da ferramenta ininterrupta, o menu no terminal perguntará se o usuário deseja acessar a ferramenta ininterrupta ou a ferramenta interativa. Caso escolha pela ferramenta ininterrupta, siga para o tópico relacionado à execução direta dos comandos, diretamente abaixo do próximo. Caso contrário:

### Ferramenta interativa (passo-a-passo):
Similarmente ao menu da ferramenta_herbcore, você pode escolher dentre opções de execução:

```
o que deseja fazer?
[1] descobrir melhores parâmetros - grid search
[2] treinar classificador
[3] testar em um dataset.npy novo (pós treino)
[4] separação de um acervo em tipos de imagens
[5] verificação da quantidade de amostras e features
```
Para o classificador, não há submenus dentro do menu principal. Acima, os tópicos listados já são os métodos disponíveis da ferramenta. Para uma melhor descrição do funcionamento de cada método, reitera-se a possibilidade de ler a seção da ferramenta ininterrupta, ou fazer ```python svm2.py NOMEDOMÉTODO -h```.

No final da execução, ele pergunta se o usuário deseja executar outro método.

```
executar outro método?
[S] sim
[N] não
```
### Ferramenta ininterrupta (execução direta):

A ferramenta te pede um conjunto de comandos pelo terminal para executar o que se pede. Caso desconheça os parâmetros necessários para a busca, você pode usar de ```-h``` e ver os comentários com ajuda adicionados. Recomenda-se ler a seção da ferramenta ininterrupta do ferramenta_herbcore, a fim de entender o funcionamento do guia de ajuda ```-h```.

### Pipeline da ferramenta:
Ainda sendo desenvolvido!

### Exemplos de uso dos comandos, na ordem dos métodos:
```python

# treinamento e teste
python svm2.py dataset_teste --arq1 imagens-saida/f1.npy --arq2 imagens-saida/f2.npy --arq3 imagens-saida/f3.npy --dir_imagens imagens-saida --kernel linear --c 0.1 --folds 5 --novo_arq1 amostragem/f1.npy --novo_arq2 amostragem/f2.npy --novo_arq3 amostragem/f3.npy --matriz 1

# apenas treinamento
python svm2.py treinamento --arq1 imagens-saida/f1.npy --arq2 imagens-saida/f2.npy --arq3 imagens-saida/f3.npy --dir_imagens imagens-saida --kernel linear --c 0.1 --folds 5 --matriz 1

# separar as imagens em subdiretórios a partir de um treinamento
python svm2.py organizar --arq1 imagens-saida/f1.npy --arq2 imagens-saida/f2.npy --arq3 imagens-saida/f3.npy --dir_origem "teste/" --dir_destino "teste-org/ --kernel linear --c 0.1"

# vetores de features extraídos
python svm2.py dimensoes --arq1 imagens-saida/f1.npy --arq2 imagens-saida/f2.npy --arq3 imagens-saida/f3.npy
```

## Agradecimentos

Deixo descrito nessa seção a minha gratidão ao [Alexandre Yuji Kajihara](https://github.com/xaaaandao), criador dos métodos contidos em downloader-specieslink-master. Com sua permissão, adicionei o seu código nessa ferramenta assim deixando-a mais completa, sem contar o auxílio recebido pelo caminho. Obrigado.
