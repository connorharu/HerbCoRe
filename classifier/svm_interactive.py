import argparse
import random
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score
from sklearn.model_selection import GridSearchCV
from svm2 import artificial_inteligence

def interactive_mode():
    while True:
        print("\nwhat do you wish to do?")
        print("[1] find optimal parameters – grid search")
        print("[2] train classifier")
        print("[3] test on a new dataset.npy (post-training)")
        print("[4] sort a collection into image types")
        print("[5] check the number of samples and features")

        choice2 = input("choose an option ").strip()

        if choice2 == "1":
            arq1 = input("\ninform the name of the first .npy feature file: ").strip()
            arq2 = input("inform the name of the second .npy feature file: ").strip()
            arq3 = input("inform the name of the therd .npy feature file: ").strip()
            grid = artificial_inteligence(arq1, arq2, arq3)
            grid.grid_search()

            finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
            if finishing == "N":
                break
        elif choice2 == "2":
            arq1 = input("\ninform the path of class 1's .npy file: ").strip()
            arq2 = input("\ninform the path of class 2's .npy file: ").strip()
            arq3 = input("\ninform the path of class 3's .npy file: ").strip()
            dir_images = input("base path for images (if empty, returns index): ").strip() or None
            kernel = input("kernel (ex: linear, rbf, poly): ").strip()
            c = float(input("C margin: "))
            folds = int(input("fold numbers: "))

            ia = artificial_inteligence(arq1, arq2, arq3, kernel, c, folds, dir_images)
            ia.load_data()
            ia.set_svm()

            show_matrix = input("do you wish to see the confusion matrix?\n[Y] yes\n[N] no\n ").strip().upper() == "Y"
            ia.assess_model(matrix=show_matrix)

            finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
            if finishing == "N":
                break
        elif choice2 == "3":
            arq1 = input("\ninform the path of class 1's .npy file: ").strip()
            arq2 = input("\ninform the path of class 2's .npy file: ").strip()
            arq3 = input("\ninform the path of class 3's .npy file: ").strip()
            dir_images = input("base path for images (if empty, returns index): ").strip() or None
            kernel = input("kernel (ex: linear, rbf, poly): ").strip()
            c = float(input("C margin: "))
            folds = int(input("fold numbers: "))

            ia = artificial_inteligence(arq1, arq2, arq3, kernel, c, folds, dir_images)
            ia.load_data()
            ia.set_svm()
            ia.assess_model()

            ia.X = ia.scaler.fit_transform(ia.X)
            ia.svm.fit(ia.X, ia.y)

            n_arq1 = input("\ninform the name of the first NEW .npy file of features to be TESTED: ").strip()
            n_arq2 = input("\ninform the name of the second NEW .npy file of features to be TESTED: ").strip()
            n_arq3 = input("\ninform the name of the third NEW .npy file of features to be TESTED: ").strip()
            show_matrix = input("do you wish to see the confusion matrix?\n[Y] yes\n[N] no\n ").strip().upper() == "Y"
            
            f1_new = ia.predict_new_dataset(n_arq1, n_arq2, n_arq3, matrix=show_matrix)
            print(f"\nF1-score on the new dataset: {f1_new:.4f}")

            finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
            if finishing == "N":
                break
        elif choice2 == "4":
            arq1 = input("\ninform the path of class 1's .npy file (training from before): ").strip()
            arq2 = input("\ninform the path of class 2's .npy file (training from before): ").strip()
            arq3 = input("\ninform the path of class 3's .npy file (training from before): ").strip()
            origin_dir = input("directory with the images to be organized: ").strip()
            destiny_dir = input("output directory (where to create f1, f2, f3): ").strip()
            kernel = input("kernel (ex: linear, rbf, poly): ").strip() or "linear"
            c = float(input("C margin: ") or 1.0)
            model = input("CNN model (vgg16 ou resnet50v2 - use the same from the training): ").strip() or "vgg16"

            ia = artificial_inteligence(arq1, arq2, arq3, kernel, c)
            ia.load_data()
            ia.set_svm()
            
            ia.organize_images(origin_dir, destiny_dir, name_model=model, target_size=(224,224))

            finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
            if finishing == "N":
                break
        elif choice2 == "5":
            arq1 = input("\ninform the path of class 1's .npy file (training from before): ").strip()
            arq2 = input("\ninform the path of class 2's .npy file (training from before): ").strip()
            arq3 = input("\ninform the path of class 3's .npy file (training from before): ").strip()
            ia = artificial_inteligence(arq1, arq2, arq3)
            ia.load_data()
            ia.verify_dimensions()

            finishing = input("\nexecute another method?\n[Y] yes\n[N] no\n").strip().upper()
            if finishing == "N":
                break
        else:
            print("\ninvalid option, try again.")