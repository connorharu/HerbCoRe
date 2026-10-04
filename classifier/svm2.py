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

class artificial_inteligence:
    def __init__(self, arq1, arq2, arq3, kernel="linear", C=1, n_splits=5, dir_images=None):
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
        self.dir_images = dir_images

    def load_data(self):
        f1 = np.load(self.arq1)
        f2 = np.load(self.arq2)
        f3 = np.load(self.arq3)

        self.X = np.vstack([f1, f2, f3]) 
        self.y = np.array([0]*len(f1) + [1]*len(f2) + [2]*len(f3))  

    def grid_search(self):
        if self.X is None or self.y is None:
            if not (self.arq1 and self.arq2 and self.arq3):
                raise ValueError("to execute the grid search you must provide the .npy files.")
            self.load_data()

        graus = [0, 1, 5] 
        cs = [0.1, 1, 10, 100, 1000] 
        gammas = [2e-5, 2e-3, 2e-1, "auto", "scale"]

        param_grid = [
            {'kernel': ['linear'], 'C': cs},
            {'kernel': ['poly'], 'C': cs, 'degree': graus, 'gamma': gammas},
            {'kernel': ['rbf'], 'C': cs, 'gamma': gammas}
        ]

        model = SVC()
        gridSearch = GridSearchCV(estimator=model,param_grid=param_grid,cv=5) 
        gridSearch.fit(self.X, self.y)
        print(f'the better choice of parameters is: {gridSearch.best_estimator_}')

    def set_svm(self):
        self.svm = SVC(kernel=self.kernel, C=self.C)

    def report_errors(self, y_test, y_pred, test_idx, len_f1, len_f2, len_f3):
        erros = np.where(y_pred != y_test)[0]

        if(erros.size > 0):
            print("samples classified incorrectly:")
            for i in erros:
                global_idx = test_idx[i]
                true_label = y_test[i] 
                pred_label = y_pred[i]

                if global_idx < len_f1: 
                    real_class = "f1"
                elif global_idx < len_f1 + len_f2: 
                    real_class = "f2"
                else:
                    real_class = "f3"

                if self.dir_images: 
                    class_folder = os.path.join(self.dir_images, "images", "tf.keras", real_class) 
                    files = glob.glob(os.path.join(class_folder, "*.jpg"))

                    if files: 
                        caminho = files[global_idx % len(files)]  
                        print(f"  [true label was {true_label} ({real_class}) - predicted {pred_label} (0=f1, 1=f2, 2=f3)], image:  {caminho}")
                    else:
                        print(f"  [true label was {true_label} ({real_class}) - predicted {pred_label} (0=f1, 1=f2, 2=f3)], no image found")
                else: 
                    print(f"  [true label was {true_label} - predicted {pred_label} (0=f1, 1=f2, 2=f3)], no folder, index {global_idx}")

    def confusion_matrixx(self, y_true, y_pred, class_labels=None):
        cm = confusion_matrix(y_true, y_pred)

        if class_labels is None:
            class_labels = ['Exsiccatae', 'Labels', 'Live plants']

        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Greens", xticklabels=class_labels, yticklabels=class_labels)
        plt.xlabel("Predicted class")
        plt.ylabel("True class")
        plt.title("Confusion matrix")
        plt.show()
        
        return cm

    def assess_model(self, matrix=False):
        seed = random.randint(0, 10000)
        skf = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=seed)
        f1_folds = []
    
        if self.dir_images is None:
            print("\nbase image folder not provided. mistakes won't show file paths.")
        else:
            print(f"\nusing image directory: {self.dir_images}")

        len_f1 = np.load(self.arq1).shape[0]
        len_f2 = np.load(self.arq2).shape[0]
        len_f3 = np.load(self.arq3).shape[0]

        y_true_all = [] 
        y_pred_all = [] 

        for fold, (train_idx, test_idx) in enumerate(skf.split(self.X, self.y), 1): 
            X_train = self.X[train_idx] 
            X_test  = self.X[test_idx] 

            y_train = self.y[train_idx] 
            y_test  = self.y[test_idx] 

            scaler = self.scaler 
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)

            self.svm.fit(X_train, y_train) 
            y_pred = self.svm.predict(X_test) 

            y_true_all.extend(y_test)
            y_pred_all.extend(y_pred)

            f1 = f1_score(y_test, y_pred, average='weighted')
            f1_folds.append(f1)
            print(f"fold {fold}'s f1_score was {f1:.4f}")

            self.report_errors(y_test, y_pred, test_idx, len_f1, len_f2, len_f3)

        media_f1 = np.mean(f1_folds)
        desvio_f1 = np.std(f1_folds)

        print(f"average d1: {(media_f1):.4f}")
        print(f"standard deviation: {np.std(f1_folds):.4f}")

        if(matrix):
            self.confusion_matrixx(y_true_all, y_pred_all, class_labels=["Exsiccatae", "Labels", "Live plants"])

        return media_f1, desvio_f1
    
    def predict_new_dataset(self, arq1, arq2, arq3, matrix=False):
        new_f1 = np.load(arq1)
        new_f2 = np.load(arq2)
        new_f3 = np.load(arq3)

        X_new = np.vstack([new_f1, new_f2, new_f3])
        X_new = self.scaler.transform(X_new) 
        y_new = np.array([0]*len(new_f1) + [1]*len(new_f2) + [2]*len(new_f3))

        y_pred_new = self.svm.predict(X_new)

        len_f1 = len(new_f1)
        len_f2 = len(new_f2)
        len_f3 = len(new_f3)

        test_idx = np.arange(len(y_new)) 

        self.report_errors(y_new, y_pred_new, test_idx, len_f1, len_f2, len_f3)
        f1 = f1_score(y_new, y_pred_new, average='weighted')

        if(matrix):
            self.confusion_matrixx(y_new, y_pred_new, class_labels=["Exsiccatae", "Labels", "Live plants"])

        return f1
    
    def load_cnn_model(self, model_name):
        if model_name == "vgg16":
            base_model = tf.keras.applications.VGG16(weights='imagenet', include_top=False, pooling='avg')
            preprocess = tf.keras.applications.vgg16.preprocess_input
        elif model_name == "resnet50v2":
            base_model = tf.keras.applications.ResNet50V2(weights='imagenet', include_top=False, pooling='avg')
            preprocess = tf.keras.applications.resnet_v2.preprocess_input
        else:
            raise ValueError("choose 'vgg16' or 'resnet50v2'")
        
        return base_model, preprocess
        
    def organize_images(self, origin_dir, destiny_dir, model_name, target_size=(224, 224)):
        X_scaled = self.scaler.fit_transform(self.X)
        self.svm.fit(X_scaled, self.y)

        model_cnn, preprocess_input = self.load_cnn_model(model_name)

        classes_map = {0: "f1", 1: "f2", 2: "f3"} 
        for folder in classes_map.values():
            os.makedirs(os.path.join(destiny_dir, folder), exist_ok=True)

        extensions = ('*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG')
        files = []
        for ext in extensions:
            files.extend(pathlib.Path(origin_dir).rglob(ext))

        for file in files:
            img = tf.keras.preprocessing.image.load_img(file, target_size=target_size) 
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)

            feature = model_cnn.predict(img_array, verbose=0) 
            
            feature_scaled = self.scaler.transform(feature)
            prediction = self.svm.predict(feature_scaled)[0] 
            
            choosen_folder = classes_map[prediction] 
            final_dir = os.path.join(destiny_dir, choosen_folder, file.name)
            shutil.copy(str(file), final_dir)
            
            print(f" {file.name} copied to /{choosen_folder}")

        print(f"\norganizing concluded. images separated in {destiny_dir}")

    def verify_dimensions(self):
        if self.X is not None:
            num_amostras, num_features = self.X.shape
            print(f"total images (samples) {num_amostras}")
            print(f"number of features per image {num_features}")
        else:
            print("no database was provided")

def main():
    parser = argparse.ArgumentParser(description="train and validation of a svm with cross validation")
    subparsers = parser.add_subparsers(dest="command", help="method to be executed")

    training = subparsers.add_parser("training", help="classifier training")
    training.add_argument("--arq1", help="path for class 1's .npy file")
    training.add_argument("--arq2", help="path for class 2's .npy file")
    training.add_argument("--arq3", help="path for class 3's .npy file")
    training.add_argument("--dir_images", help="base directory with the class images")
    training.add_argument("--kernel", default="linear", help="kernel (ex: linear, rbf, poly)")
    training.add_argument("--c", type=float, default=1.0, help="C margin")
    training.add_argument("--folds", type=int, default=5, help="fold numbers")
    training.add_argument("--matrix", type=int, choices=[0, 1], default=1, help="if 1, shows confusion matrix, if 0, doesn't")

    grid_search = subparsers.add_parser("grid_search", help="search for the best parameters for the classifier")
    grid_search.add_argument("--arq1", help="path for class 1's .npy file")
    grid_search.add_argument("--arq2", help="path for class 2's .npy file")
    grid_search.add_argument("--arq3", help="path for class 3's .npy file")

    testing_dataset = subparsers.add_parser("testing_dataset", help="testing the classifier with a new dataset")
    testing_dataset.add_argument("--arq1", help="path for class 1's .npy file")
    testing_dataset.add_argument("--arq2", help="path for class 2's .npy file")
    testing_dataset.add_argument("--arq3", help="path for class 3's .npy file")
    testing_dataset.add_argument("--dir_images", help="base directory with the class images")
    testing_dataset.add_argument("--kernel", default="linear", help="kernel (ex: linear, rbf, poly)")
    testing_dataset.add_argument("--c", type=float, default=1.0, help="C margin")
    testing_dataset.add_argument("--folds", type=int, default=5, help="fold numbers")
    testing_dataset.add_argument("--novo_arq1", help="path for the new class 1's .npy file to be tested")
    testing_dataset.add_argument("--novo_arq2", help="path for the new class 2's .npy file to be tested")
    testing_dataset.add_argument("--novo_arq3", help="path for the new class 3's .npy file to be tested")
    testing_dataset.add_argument("--matrix", type=int, choices=[0, 1], default=1, help="if 1, shows confusion matrix, if 0, doesn't")

    organize = subparsers.add_parser("organize", help="classifies images and organizes the classes in folders")
    organize.add_argument("--arq1", required=True, help="path for class 1's .npy file (training)")
    organize.add_argument("--arq2", required=True, help="path for class 2's .npy file (training)")
    organize.add_argument("--arq3", required=True, help="path for class 3's .npy file (training)")
    organize.add_argument("--model", choices=['vgg16', 'resnet50v2'], default='vgg16', help="CNN architecture for extracting features - use the same one used in the training extraction")
    organize.add_argument("--kernel", default="linear", help="kernel (ex: linear, rbf, poly)")
    organize.add_argument("--c", type=float, default=1.0, help="C margin")
    organize.add_argument("--origin_dir", required=True, help="folder with the mixed classes")
    organize.add_argument("--destiny_dir", required=True, help="output directory where the organized f1, f2, f3 classes will be placed")

    dimensions = subparsers.add_parser("dimensions", help="describes how many samples and features the dataset has")
    dimensions.add_argument("--arq1", required=True, help="path for class 1's .npy file (training)")
    dimensions.add_argument("--arq2", required=True, help="path for class 2's .npy file (training)")
    dimensions.add_argument("--arq3", required=True, help="path for class 3's .npy file (training)")
    
    args = parser.parse_args()

    print("\nwould you like to execute step-by-step, or without help?: ")
    print("[1] step-by-step")
    print("[2] without help")

    choice = input("choose an option: ").strip()

    if choice == "1":
        from svm_interactive import interactive_mode
        interactive_mode()
        return
    elif choice == "2":
        print("\nexecuting the requested method...")
    
    if args.command == "training":
        ia = artificial_inteligence(args.arq1, args.arq2, args.arq3, args.kernel, args.c, args.folds, args.dir_images)
        ia.load_data()
        ia.set_svm()
        ia.assess_model(matrix=bool(args.matrix))
    elif args.command == "grid_search":
        ia = artificial_inteligence(args.arq1, args.arq2, args.arq3)
        ia.grid_search()
    elif args.command == "testing_dataset":
        ia = artificial_inteligence(args.arq1, args.arq2, args.arq3, args.kernel, args.c, args.folds, args.dir_images)
        ia.load_data()
        ia.set_svm()
        ia.assess_model()

        ia.X = ia.scaler.fit_transform(ia.X)  
        ia.svm.fit(ia.X, ia.y)
        new_f1 = ia.predict_new_dataset(args.novo_arq1, args.novo_arq2, args.novo_arq3, matrix=bool(args.matrix))
        print(f"\nF1-score on the new dataset: {new_f1:.4f}")
    elif args.command == "organize":
            ia = artificial_inteligence(args.arq1, args.arq2, args.arq3, args.kernel, args.c)
            ia.load_data()
            ia.set_svm()
            ia.organize_images(args.origin_dir, args.destiny_dir, model_name=args.model, target_size=(224, 224))
    elif args.command == "dimensions":
            ia = artificial_inteligence(args.arq1, args.arq2, args.arq3)
            ia.load_data()
            ia.verify_dimensions()

if __name__ == "__main__":
    main()