# HerbCoRe
A cataloging of HerbCoRe: a tool for selecting and filtering plant-related datasets from herbariums, developed with the assistance of Professor André Luis Schwerz.

## About the folder ferramenta_herbcore:
Code designed to query metadata, such as types, lists, or collection and/or institution data, as well as information about a dataset, via the speciesLink API. It allows for filtering biodiversity records to retrieve more specific data, and the result set has no size limit.

Capable of transferring data to MySQL, storing records in a table for in-depth analysis.

The tool is organized into five separate files:
- config.py: user settings for running the code (API key, database username, password, host, etc.);
- ferramenta.py: non-interactive version of the tool—executes database/speciesLink methods by providing all arguments in a single submission;
- interativo.py: interactive, incremental version of the tool—executes methods related to the database, speciesLink, or Leipzig by providing arguments step-by-step;
- main_f.py: implementation of database and speciesLink methods;
- sinonimos.py: direct method for checking synonyms of provided scientific names against the [Leipzig catalogue](https://www.nature.com/articles/s41597-020-00702-z);
- deduplicacao.py: direct method for ranking the authors of scientific names found in the records.

Use the crawler found [here](https://github.com/xaaaandao/downloader-specieslink/tree/master) to obtain the URLs and images.
Read more about the Leipzig Catalogue and lcvplants [here](https://github.com/idiv-biodiversity/lcvplants). However, the package installation method appears to be outdated. Use the ```pak``` package instead of ```devtools```, as follows:

```
install.packages("pak")
pak::pak("idiv-biodiversity/LCVP")
pak::pak("idiv-biodiversity/lcvplants")
```

Install dezoomify-rs 2.12.3 [here](https://github.com/lovasoa/dezoomify-rs/releases/tag/v2.12.3) – PLACE IT IN THE ```ferramenta_herbcore``` DIRECTORY, NOT IN ```downloader-specieslink-master```! Do the same for the `pipeline` directory, if used.

Obtain an API key by registering with species_link [here](https://specieslink.net/ws/1.0/).

## Prerequisites:
- Install all of the requirements listed at ```requirements.txt``` with the following command:
```
pip install -r requirements.txt
```

## How to use the tool:
When invoking ```python ferramenta.py```, or any command of the non-interactive tool, the terminal menu will ask whether the user wishes to access the non-interactive tool or the interactive tool. If the non-interactive tool is selected, proceed to the section regarding direct command execution, located immediately below the next one. Otherwise:

### Interactive tool (step-by-step):
After selecting the interactive tool, another menu opens with further execution options:

```
welcome to the interactive mode!
here, you will be guided to choose the methods and provide the necessary parameters.

choose a method:
[1] information about the data
[2] filtering and queries in the database
[3] verification of the scientific name
[4] herbarium specimen images
[5] authors of reliable scientific names
[6] exit
```

Within the interactive tool, the methods are organized into groups under these five topics, with the sixth option allowing you to exit the consultation. Entering a number other than those listed will return the same menu. For example, entering "1":

```
enter the option number: 1 <- number entered in the terminal
[1] metadata
[2] participating institutions
[3] specific institutions
[4] collections
[5] specific datasets
```

Each one represents a method of the tool. For a better description of how each method works, read the section on the tool or run ```python ferramenta.py METHOD_NAME -h```. Entering a number other than those listed will return you to the previous menu.
If, for example, we enter "3", it will ask for all the information related to that method, one by one:
```
enter the option number: 3 <- number entered in the terminal
enter the collection acronym (required if ID is not provided): USP
enter the ID (required if acronym is not provided):    # I didn't provide one!
enter the language (optional): en
executing specieslink.get_institution_data(acronym=USP, id=, lang=en)... # the response was provided right below, but since it is very long, I didn't include it here!
```

At the end of the execution, it asks if the user wishes to run another method. The response must be in uppercase, as indicated in the menu box:

```
run another method?
[Y] yes
[N] no
note: it is case-sensitive
```
### Continuous classifier tool (direct execution):

The tool requires a set of terminal commands to perform the requested task. If you are unfamiliar with the necessary search parameters, you can use ```-h``` to view the included help information.
```python ferramenta.py -h``` will display the following:
```

ferramenta.py's methods interface:

positional arguments:
  {metadata,participants,instituition,collection,dataset,records}
                        method to be executed
    metadata            species metadata
    participants        participating instituitions
    instituition        specific instituitions
    collection          specific collections
    dataset             specific dataset
    records             filtered records
    export              performs an SQL query and returns a CSV
    update              updates database records based on parameters
    urls                urls to be retrieved via downloader-specieslink-master
    dezoomify_rs        imabes to be retrieved via downloader-specieslink-master
```

```python sinonimos.py -h``` will display the following:
```
scientific name analysis method interface

positional arguments:
  {extract,fuzzy}  method to be executed
    extract        extract names from text and save to CSV
    fuzzy          fuzzy text search and visualization based on CSV names
    fuzzy_line     line-by-line database update based on CSV names
```

```python deduplicacao.py -h``` will display the following:
```
method for the fuzzy identification of reliable taxonomists

positional arguments:
  {deduplicador}  method to be executed
    deduplicador  run the fuzzy name deduplicator
```

To look for something more specific, such as the parameters of the methods demonstrated above, you need to specify the method when issuing the help command.
For example, ```python ferramenta.py metadata -h``` will display the following:
```
usage: ferramenta.py metadata [-h] --api_key API_KEY [--name NAME] [--id ID]

options:
  -h, --help         show this help message and exit
  --name NAME        name to be identified
  --id ID            id to be identified
```

### Pipeline da ferramenta:
Follow the pipeline's execution as suggested normally.

### Examples of command usage, in the order of the methods:
```python
# examples of ferramenta.py:
python ferramenta.py metadata --name "Secretaria Estadual" --id "400"
python ferramenta.py participants
python ferramenta.py instituition --acronym "USP" --id "393" --lang "en"  
python ferramenta.py collection --acronym "ESA" --id "8" --lang "pt-br"
python ferramenta.py dataset --id "8"
python ferramenta.py records --filters family=piperaceae barcode="FURB38192" --table tabela_exemplo
python ferramenta.py export --filters family=piperaceae --table tabela_exemplo --colums "coluna_exemplo" --output_csv_path resultados.csv
python ferramenta.py update --filters stateprovince="São Paulo" --update_values="Santa Catarina" --table tabela_exemplo
The urls and dezoomify_rs commands are not used directly; they are accessed only through the interactive tool under the item "[4] herbarium specimen images." For direct execution, it is recommended to use the code found in the repository cited in this README.

# examples of sinonimos.py:
python sinonimos.py extract --txt teste-08-04.txt --csv aaa.csv
python sinonimos.py fuzzy --csv aaa.csv --output ccc.txt --max_distance 0.1 
python sinonimos.py fuzzy --csv aaa.csv --output ccc.txt (max_distance é opcional!)
python sinonimos.py fuzzy_line --csv teste.csv --tabela registros_biodiversidade --coluna scientificname_NOVO --status status_plantas --max_distance 0.1

# examples of deduplicacao.py:
python deduplicacao.py deduplicar_autores deduplicador --csv nomes2-15-06.csv --ranking 5 --similar 100 --txt nome.txt
```
## About the classificador folder:
This code was developed to categorize images previously obtained via the *herbcore* tool into types—such as herbarium specimens, images of live plants, and other imagery like close-ups of herbarium labels. After a training set is manually sorted, the model can classify the remaining images in the collection, allowing researchers to save time by simply reviewing the model's output rather than manually sorting every image.

The tool is split into two separate files:
- svm2.py: code file defining the tool's methods, which are explained below.
- svm_interativo.py: used to call the methods from svm2.py interactively, similar to how ferramenta_herbcore is used.

## Prerequisites:
- Install all of the requirements listed at ```requirements.txt``` with the following command:
```
pip install -r requirements.txt
```
If ```requirements.txt``` has already been installed, there is no need to do it again.

## How to use the classifying tool:
When invoking ```python svm2.py```, or any command for the non-interactive tool, the terminal menu will ask whether the user wishes to access the non-interactive tool or the interactive tool. If the non-interactive tool is selected, proceed to the section regarding direct command execution, located immediately below the next one. Otherwise:

### Interactive classifier tool (step-by-step):
Similar to the ferramenta_herbcore menu, you can choose from execution options:

```
what would you like to do?
[1] find optimal parameters – grid search
[2] train classifier
[3] test on a new dataset.npy (post-training)
[4] sort a collection into image types
[5] check the number of samples and features
```
For the classifier, there are no submenus within the main menu; the listed topics represent the tool's available methods. For a more detailed description of how each method works, you can either read the relevant section of the tool's documentation or run ```python svm2.py METHOD_NAME -h```.

Upon completion, the program asks if the user wishes to run another method.

```
run another method?
[Y] yes
[N] no
```
756
### Continuous classifier tool (direct execution):

The tool prompts you for a set of commands via the terminal to perform the requested operations. If you are unfamiliar with the necessary search parameters, you can use the ```-h``` flag to view the included help comments. It is recommended to read the section on the continuous tool in ferramenta_herbcore to understand how the ```-h``` help guide works.

### Classifier tool pipeline:
The tool's pipeline notebook is not designed to train or validate a model; instead, it simply categorizes herbarium images into three types: herbarium specimens (exsiccatae), labels, and live plant images. To do this, run ```separating.ipynb```, which already includes calls to the pre-trained model and scaler.

### Examples of command usage, in the order of the methods:
```python

# training and testing
python svm2.py dataset_teste --arq1 imagens-saida/f1.npy --arq2 imagens-saida/f2.npy --arq3 imagens-saida/f3.npy --dir_imagens imagens-saida --kernel linear --c 0.1 --folds 5 --novo_arq1 amostragem/f1.npy --novo_arq2 amostragem/f2.npy --novo_arq3 amostragem/f3.npy --matriz 1

# just training
python svm2.py treinamento --arq1 imagens-saida/f1.npy --arq2 imagens-saida/f2.npy --arq3 imagens-saida/f3.npy --dir_imagens imagens-saida --kernel linear --c 0.1 --folds 5 --matriz 1

# separate images into subdirectories based on a training set
python svm2.py organizar --arq1 imagens-saida/f1.npy --arq2 imagens-saida/f2.npy --arq3 imagens-saida/f3.npy --dir_origem "teste/" --dir_destino "teste-org/ --kernel linear --c 0.1"

# extracted feature vectors
python svm2.py dimensoes --arq1 imagens-saida/f1.npy --arq2 imagens-saida/f2.npy --arq3 imagens-saida/f3.npy
```

## Acknowledgments

In this section, I would like to express my gratitude to [Alexandre Yuji Kajihara](https://github.com/xaaaandao), the creator of the methods found in downloader-specieslink-master. With his permission, I incorporated his code into this tool to make it more comprehensive, not to mention the assistance he provided along the way. Thank you.
