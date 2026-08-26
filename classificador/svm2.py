import argparse
import random
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, confusion_matrix
from sklearn.model_selection import GridSearchCV
import glob
import os
import shutil
import pathlib
import tensorflow as tf

class inteligencia_artificial:
    def __init__(self, arq1, arq2, arq3, kernel="linear", C=1, n_splits=5, dir_imagens=None):
        self.scaler = StandardScaler()
        self.arq1 = arq1
        self.arq2 = arq2
        self.arq3 = arq3
        self.kernel = kernel
        self.C = C
        self.n_splits = n_splits
        self.svm = None
        self.X = None
        self.y = None
        self.dir_imagens = dir_imagens

    def carregar_dados(self):
        f1 = np.load(self.arq1)
        f2 = np.load(self.arq2)
        f3 = np.load(self.arq3)

        self.X = np.vstack([f1, f2, f3])  # concatena tudo
        self.y = np.array([0]*len(f1) + [1]*len(f2) + [2]*len(f3))  # f1=0, f2=1, f3=2

    def grid_search(self):
        if self.X is None or self.y is None:
            if not (self.arq1 and self.arq2 and self.arq3):
                raise ValueError("os arquivos .npy devem ser informados para executar o grid search.")
            self.carregar_dados()

        graus = [0, 1, 5] # caso kernel polinomial, controla complexidade
        cs = [0.1, 1, 10, 100, 1000] # margem de erro
        # gammas = [0.1, 1, 10] # sensibilidade
        gammas = [2e-5, 2e-3, 2e-1, "auto", "scale"]

        # kernels = ['linear', 'rbf', 'poly'] # separação entre classes (reta, curvada, muito curvada)
        param_grid = [
            {'kernel': ['linear'], 'C': cs},
            {'kernel': ['poly'], 'C': cs, 'degree': graus, 'gamma': gammas},
            {'kernel': ['rbf'], 'C': cs, 'gamma': gammas}
        ]

        model = SVC()
        gridSearch = GridSearchCV(estimator=model,param_grid=param_grid,cv=5) # cross validation de 5
        gridSearch.fit(self.X, self.y)
        print(f'a melhor escolha de parâmetros é: {gridSearch.best_estimator_}')

    def set_svm(self):
        self.svm = SVC(kernel=self.kernel, C=self.C)

    def reportar_erros(self, y_test, y_pred, test_idx, len_f1, len_f2, len_f3):
        erros = np.where(y_pred != y_test)[0] # onde a predição foi diferente do valor real

        if(erros.size > 0):
            print("amostras classificadas incorretamente:")
            for i in erros: # para cada erro
                global_idx = test_idx[i] # índice original (ordem numérica nas pastas)
                true_label = y_test[i] # rótulo real
                pred_label = y_pred[i] # rótulo predito pela svm

                # de qual classe veio a amostra
                if global_idx < len_f1: # primeira classe
                    classe_real = "f1"
                elif global_idx < len_f1 + len_f2: # segunda classe
                    classe_real = "f2"
                else: # terceira classe
                    classe_real = "f3"

                if self.dir_imagens: # diretório informado
                    pasta_classe = os.path.join(self.dir_imagens, "images", "tf.keras", classe_real) # caminho da pasta
                    arquivos = glob.glob(os.path.join(pasta_classe, "*.jpg")) # lista todos os arquivos da pasta

                    if arquivos: # encontrou arquivos
                        caminho = arquivos[global_idx % len(arquivos)]  # pega um arquivo da classe
                        print(f"  [label era {true_label} ({classe_real}) - predizeu {pred_label} (0=f1, 1=f2, 2=f3)], imagem:  {caminho}")
                    else: # não encontrou arquivos
                        print(f"  [label era {true_label} ({classe_real}) - predizeu {pred_label} (0=f1, 1=f2, 2=f3)], nenhuma imagem encontrada")
                else: # diretório não foi informado, usa posição global dentro das pastas
                    print(f"  [label era {true_label} - predizeu {pred_label} (0=f1, 1=f2, 2=f3)], sem diretório, índice {global_idx}")

    def matriz_confusao(self, y_true, y_pred, rotulos_classes=None):
        cm = confusion_matrix(y_true, y_pred)

        if rotulos_classes is None:
            # rotulos_classes = [str(i) for i in np.unique(y_true)]
            rotulos_classes = ['Exsicatas', 'Rótulos', 'Imagens vivas']

        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Greens", xticklabels=rotulos_classes, yticklabels=rotulos_classes)
        plt.xlabel("Classe prevista")
        plt.ylabel("Classe real")
        plt.title("matriz de confusão")
        plt.show()
        
        return cm

    def avaliar_modelo(self, matriz=False):
        seed = random.randint(0, 10000)
        skf = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=seed)
        f1_folds = []
    
        if self.dir_imagens is None:
            print("\ncaminho base das imagens não informado. os erros não mostrarão caminhos de arquivos.")
        else:
            print(f"\nusando diretório base das imagens: {self.dir_imagens}")

        len_f1 = np.load(self.arq1).shape[0] # tamanho pra usar em reportar_erros
        len_f2 = np.load(self.arq2).shape[0]
        len_f3 = np.load(self.arq3).shape[0]

        y_true_all = [] # pra matriz de confusão
        y_pred_all = [] 

        for fold, (train_idx, test_idx) in enumerate(skf.split(self.X, self.y), 1): # para cada fold de indice e testes dentro do range (X, y)
            X_train = self.X[train_idx] 
            X_test  = self.X[test_idx] 

            y_train = self.y[train_idx] # rótulos de classe
            y_test  = self.y[test_idx] 

            scaler = self.scaler # z-score, média 0 desvio padrãso 1
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

            self.svm.fit(X_train, y_train) # treino
            y_pred = self.svm.predict(X_test) # predição

            y_true_all.extend(y_test)
            y_pred_all.extend(y_pred)

            f1 = f1_score(y_test, y_pred, average='weighted')
            f1_folds.append(f1)
            print(f"fold {fold} teve f1_score de {f1:.4f}")

            self.reportar_erros(y_test, y_pred, test_idx, len_f1, len_f2, len_f3)

        media_f1 = np.mean(f1_folds)
        desvio_f1 = np.std(f1_folds)

        print(f"f1 média: {(media_f1):.4f}")
        print(f"desvio padrão: {np.std(f1_folds):.4f}")

        if(matriz):
            self.matriz_confusao(y_true_all, y_pred_all, rotulos_classes=["Exsicatas", "Rótulos", "Imagens vivas"])

        return media_f1, desvio_f1
    
    def prever_novo_dataset(self, arq1, arq2, arq3, matriz=False):
        f1_novo = np.load(arq1)
        f2_novo = np.load(arq2)
        f3_novo = np.load(arq3)

        X_novo = np.vstack([f1_novo, f2_novo, f3_novo])
        X_novo = self.scaler.transform(X_novo) # z-score
        y_novo = np.array([0]*len(f1_novo) + [1]*len(f2_novo) + [2]*len(f3_novo))

        y_pred_novo = self.svm.predict(X_novo)

        len_f1 = len(f1_novo) # tamanho pra usar em reportar_erros
        len_f2 = len(f2_novo)
        len_f3 = len(f3_novo)

        test_idx = np.arange(len(y_novo)) # simular global_idx

        self.reportar_erros(y_novo, y_pred_novo, test_idx, len_f1, len_f2, len_f3)
        f1 = f1_score(y_novo, y_pred_novo, average='weighted')

        if(matriz):
            self.matriz_confusao(y_novo, y_pred_novo, rotulos_classes=["Exsicatas", "Rótulos", "Imagens vivas"])

        return f1
    
    def carregar_modelo_cnn(self, nome_modelo):
        if nome_modelo == "vgg16":
            base_model = tf.keras.applications.VGG16(weights='imagenet', include_top=False, pooling='avg')
            preprocess = tf.keras.applications.vgg16.preprocess_input
        elif nome_modelo == "resnet50v2":
            base_model = tf.keras.applications.ResNet50V2(weights='imagenet', include_top=False, pooling='avg')
            preprocess = tf.keras.applications.resnet_v2.preprocess_input
        else:
            raise ValueError("escolha 'vgg16' ou 'resnet50v2'")
        
        return base_model, preprocess
        
    def organizar_imagens(self, dir_origem, dir_destino, nome_modelo, target_size=(224, 224)):
        X_scaled = self.scaler.fit_transform(self.X) # treina com os .npy
        self.svm.fit(X_scaled, self.y)

        model_cnn, preprocess_input = self.carregar_modelo_cnn(nome_modelo)

        classes_map = {0: "f1", 1: "f2", 2: "f3"} # separação das pastas f1, f2 e f3
        for folder in classes_map.values():
            os.makedirs(os.path.join(dir_destino, folder), exist_ok=True)

        extensoes = ('*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG')
        arquivos = []
        for ext in extensoes:
            arquivos.extend(pathlib.Path(dir_origem).rglob(ext))

        for arquivo in arquivos:
            img = tf.keras.preprocessing.image.load_img(arquivo, target_size=target_size) 
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            feature = model_cnn.predict(img_array, verbose=0) # extrai feature
            
            feature_scaled = self.scaler.transform(feature) # z-score
            predicao = self.svm.predict(feature_scaled)[0] # prevê
            
            pasta_escolhida = classes_map[predicao] # copia para a pasta prevista
            destino_final = os.path.join(dir_destino, pasta_escolhida, arquivo.name)
            shutil.copy(str(arquivo), destino_final)
            
            print(f" {arquivo.name} copiada para /{pasta_escolhida}")

        print(f"\norganização concluida. imagens separadas em {dir_destino}")

    def verificar_dimensoes(self):
        if self.X is not None:
            num_amostras, num_features = self.X.shape
            print(f"total de imagens (amostras) {num_amostras}")
            print(f"número de características (features) por imagem {num_features}")
        else:
            print("nenhum acervo foi carregado")

def main():
    parser = argparse.ArgumentParser(description="treino e validação de uma svm com cross-validation")
    subparsers = parser.add_subparsers(dest="command", help="método a ser executado")

    treinamento = subparsers.add_parser("treinamento", help="treinamento do classificador")
    treinamento.add_argument("--arq1", help="caminho do arquivo .npy da classe 1")
    treinamento.add_argument("--arq2", help="caminho do arquivo .npy da classe 2")
    treinamento.add_argument("--arq3", help="caminho do arquivo .npy da classe 3")
    treinamento.add_argument("--dir_imagens", help="diretório base onde estão as imagens das classes")
    treinamento.add_argument("--kernel", default="linear", help="kernel (ex: linear, rbf, poly)")
    treinamento.add_argument("--c", type=float, default=1.0, help="margem de erro C")
    treinamento.add_argument("--folds", type=int, default=5, help="número de folds")
    treinamento.add_argument("--matriz", type=int, choices=[0, 1], default=1, help="se 1, mostra a matriz de confusão, se 0 não mostra")

    grid_search = subparsers.add_parser("grid_search", help="busca dos melhores parâmtetros para o classificador")
    grid_search.add_argument("--arq1", help="caminho do arquivo .npy da classe 1")
    grid_search.add_argument("--arq2", help="caminho do arquivo .npy da classe 2")
    grid_search.add_argument("--arq3", help="caminho do arquivo .npy da classe 3")

    dataset_teste = subparsers.add_parser("dataset_teste", help="teste do classificador com um novo dataset")
    dataset_teste.add_argument("--arq1", help="caminho do arquivo .npy da classe 1")
    dataset_teste.add_argument("--arq2", help="caminho do arquivo .npy da classe 2")
    dataset_teste.add_argument("--arq3", help="caminho do arquivo .npy da classe 3")
    dataset_teste.add_argument("--dir_imagens", help="diretório base onde estão as imagens das classes")
    dataset_teste.add_argument("--kernel", default="linear", help="kernel (ex: linear, rbf, poly)")
    dataset_teste.add_argument("--c", type=float, default=1.0, help="margem de erro C")
    dataset_teste.add_argument("--folds", type=int, default=5, help="número de folds")
    dataset_teste.add_argument("--novo_arq1", help="caminho do arquivo .npy da classe 1 a ser TESTADA")
    dataset_teste.add_argument("--novo_arq2", help="caminho do arquivo .npy da classe 2 a ser TESTADA")
    dataset_teste.add_argument("--novo_arq3", help="caminho do arquivo .npy da classe 3 a ser TESTADA")
    dataset_teste.add_argument("--matriz", type=int, choices=[0, 1], default=1, help="se 1, mostra a matriz de confusão, se 0 não mostra")

    organizar = subparsers.add_parser("organizar", help="classifica imagens soltas e as separa em pastas")
    organizar.add_argument("--arq1", required=True, help="caminho do arquivo .npy da classe 1 (treinamento)")
    organizar.add_argument("--arq2", required=True, help="caminho do arquivo .npy da classe 2 (treinamento)")
    organizar.add_argument("--arq3", required=True, help="caminho do arquivo .npy da classe 3 (treinamento)")
    organizar.add_argument("--modelo", choices=['vgg16', 'resnet50v2'], default='vgg16', help="arquitetura da CNN para extrair features - use a mesma utilizada na extração do treinamento")
    organizar.add_argument("--kernel", default="linear", help="kernel (ex: linear, rbf, poly)")
    organizar.add_argument("--c", type=float, default=1.0, help="margem de erro C")
    organizar.add_argument("--dir_origem", required=True, help="diretório onde estão as imagens misturadas")
    organizar.add_argument("--dir_destino", required=True, help="diretório de saída onde as pastas f1, f2, f3 serão criadas")

    dimensoes = subparsers.add_parser("dimensoes", help="descreve quantas amostras e quantas features tem o acervo")
    dimensoes.add_argument("--arq1", required=True, help="caminho do arquivo .npy da classe 1 (treinamento)")
    dimensoes.add_argument("--arq2", required=True, help="caminho do arquivo .npy da classe 2 (treinamento)")
    dimensoes.add_argument("--arq3", required=True, help="caminho do arquivo .npy da classe 3 (treinamento)")
    
    args = parser.parse_args()

    print("\ngostaria de executar passo a passo, ou sem auxílio?: ")
    print("[1] passo-a-passo")
    print("[2] sem auxílio")

    choice = input("escolha uma opção: ").strip()

    if choice == "1":
        from svm_interativo import interactive_mode
        interactive_mode()
        return
    elif choice == "2":
        print("\nexecutando o método pedido...")
    
    if args.command == "treinamento":
        ia = inteligencia_artificial(args.arq1, args.arq2, args.arq3, args.kernel, args.c, args.folds, args.dir_imagens)
        ia.carregar_dados()
        ia.set_svm()
        ia.avaliar_modelo(matriz=bool(args.matriz))
    elif args.command == "grid_search":
        ia = inteligencia_artificial(args.arq1, args.arq2, args.arq3)
        ia.grid_search()
    elif args.command == "dataset_teste":
        ia = inteligencia_artificial(args.arq1, args.arq2, args.arq3, args.kernel, args.c, args.folds, args.dir_imagens)
        ia.carregar_dados()
        ia.set_svm()
        ia.avaliar_modelo()

        ia.X = ia.scaler.fit_transform(ia.X)  # treinando em cima de todos os dados
        ia.svm.fit(ia.X, ia.y)
        f1_novo = ia.prever_novo_dataset(args.novo_arq1, args.novo_arq2, args.novo_arq3, matriz=bool(args.matriz))
        print(f"\nF1-score no novo dataset: {f1_novo:.4f}")
    elif args.command == "organizar":
            ia = inteligencia_artificial(args.arq1, args.arq2, args.arq3, args.kernel, args.c)
            ia.carregar_dados()
            ia.set_svm()
            ia.organizar_imagens(args.dir_origem, args.dir_destino, nome_modelo=args.modelo, target_size=(224, 224))
    elif args.command == "dimensoes":
            ia = inteligencia_artificial(args.arq1, args.arq2, args.arq3)
            ia.carregar_dados()
            ia.verificar_dimensoes()

if __name__ == "__main__":
    main()