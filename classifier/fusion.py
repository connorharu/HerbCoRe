import re
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, confusion_matrix
import random
import shutil
import torch
import tensorflow as tf
from vit import vit_feature_extractor

class feature_fusion:
    def __init__(self, vgg16_dir, resnet50v2_dir, vit_dir, output_dir="."):
        self.sources = {
            "vgg16": Path(vgg16_dir).resolve(),
            "resnet50v2": Path(resnet50v2_dir).resolve(),
            "vit": Path(vit_dir).resolve(),
        }
        self.tf_models = ["vgg16", "resnet50v2"] 
        self.output_path = Path(output_dir).resolve()
        self.features_root = self.output_path / "features"
        self.folders = [1, 2, 3]
        self.valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        self.samples = {}

    def find_feature_file(self, source_dir, fold):
        # f1.npy: vit.py structure
        # fold-1_patches-1.npy: vgg and resnet
        for name in (f"f{fold}.npy", f"fold-{fold}_patches-1.npy"):
            matches = sorted(source_dir.rglob(name))
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise ValueError(f"more than one {name} inside {source_dir}: {[str(m) for m in matches]}")
        raise FileNotFoundError(f"no feature file for f{fold} inside {source_dir}")

    def load_samples(self):
        # keeping the order of the extracted images so the concatenated features match
        for model_name in self.tf_models:
            matches = sorted(self.sources[model_name].rglob("info_samples2.csv"))
            if len(matches) != 1:
                raise FileNotFoundError(f"{model_name} expected one info_samples2.csv inside " f"{self.sources[model_name]}, but instead found {len(matches)}")
            self.samples[model_name] = pd.read_csv(matches[0], sep=";")
            print(f"{model_name} filenames order read from {matches[0]}")

    def normalize_name(self, name):
        # removing stuff after barcode name
        path = Path(name)
        stem = path.stem.split("_patch=")[0]
        return stem + path.suffix

    def get_vit_order(self, fold):
        # images are copied by vit.py in sorted order, only when the feature was extracted, so this list matches row by row the vit's .npy
        fold_dir = self.sources["vit"] / "images" / f"f{fold}"
        if not fold_dir.exists():
            raise FileNotFoundError(f"{fold_dir} not found. --vit must be the output folder of vit.py (with images/)")

        names = [self.normalize_name(p.name) for p in sorted(fold_dir.rglob("*"))
                 if p.is_file() and p.suffix.lower() in self.valid_extensions]
        if len(set(names)) != len(names):
            raise ValueError(f"fold {fold} - repeated filenames in {fold_dir}, can't match by name")
        return names

    def reorder_to_vit(self, model_name, data, fold, vit_names):
        df = self.samples[model_name]
        tf_names = [self.normalize_name(n) for n in df[df["fold"] == fold]["filename"].tolist()]

        if len(tf_names) != data.shape[0]:
            raise ValueError(f"fold {fold} - {model_name} - {data.shape[0]} rows in the .npy " f"but {len(tf_names)} filenames in info_samples2.csv")
        if len(set(tf_names)) != len(tf_names):
            raise ValueError(f"fold {fold} - {model_name} - repeated filenames, can't match by name")

        if set(tf_names) != set(vit_names):
            only_tf = sorted(set(tf_names) - set(vit_names))
            only_vit = sorted(set(vit_names) - set(tf_names))
            raise ValueError(f"fold {fold} - {model_name} - different images than the vit. " f"only in {model_name} - {only_tf} | only in vit: {only_vit}")

        if tf_names == vit_names:
            print(f"fold {fold} - {model_name} - already in the vit order")
            return data

        position = {name: i for i, name in enumerate(tf_names)}
        new_order = [position[name] for name in vit_names]
        print(f"fold {fold} - {model_name} - rows reordered to the vit order")
        return data[new_order]

    def load_fold(self, fold):
        blocks = {}
        for model_name, source_dir in self.sources.items():
            path = self.find_feature_file(source_dir, fold)
            data = np.load(path)
            if data.ndim != 2:
                raise ValueError(f"{path} has shape {data.shape}, expected (n_images, n_features)")
            print(f"fold {fold} - {model_name} - {data.shape}")
            blocks[model_name] = data

        vit_names = self.get_vit_order(fold)
        if blocks["vit"].shape[0] != len(vit_names):
            raise ValueError(f"fold {fold} - vit .npy has {blocks['vit'].shape[0]} rows " f"but {len(vit_names)} images in images/f{fold}")

        for model_name in self.tf_models:
            blocks[model_name] = self.reorder_to_vit(model_name, blocks[model_name], fold, vit_names)

        return blocks, vit_names

    def save_fold(self, fold, features):
        fold_name = f"f{fold}"
        feat_out_dir = self.features_root / fold_name
        feat_out_dir.mkdir(parents=True, exist_ok=True)

        labels = np.full(features.shape[0], fold)
        np.save(feat_out_dir / f"{fold_name}.npy", features)
        np.savez_compressed(feat_out_dir / f"{fold_name}.npz", x=features, y=labels)
        print(f"fold {fold} - saved {features.shape} in {fold_name}.npy")

    def save_info(self, dims, samples):
        rows, start = [], 0
        for model_name, dim in dims.items():
            rows.append([model_name, start, start + dim - 1, dim])
            start += dim
        df = pd.DataFrame(rows, columns=["model", "first_column", "last_column", "n_features"])
        df.to_csv(self.features_root / "info_fusion.csv", sep=";", index=False)

        pd.DataFrame(samples, columns=["filename", "fold"]).to_csv(
            self.features_root / "info_samples.csv", sep=";", index=False)

    def fuse(self):
        for model_name, source_dir in self.sources.items():
            if not source_dir.exists():
                raise SystemExit(f"{model_name} - {source_dir} does not exist")

        self.load_samples()
        self.features_root.mkdir(parents=True, exist_ok=True)
        dims = None
        samples = []

        for fold in self.folders:
            blocks, vit_names = self.load_fold(fold)
            fused = np.concatenate(list(blocks.values()), axis=1)  # (n_images, d_vgg + d_resnet + d_vit)
            self.save_fold(fold, fused)
            samples.extend([[name, fold] for name in vit_names])

            current_dims = {name: block.shape[1] for name, block in blocks.items()}
            if dims is not None and current_dims != dims:
                raise ValueError(f"fold {fold} - dimensions {current_dims} differ from previous folds {dims}")
            dims = current_dims

        self.save_info(dims, samples)

class late_fusion(feature_fusion):
    def __init__(self, vgg16_dir, resnet50v2_dir, vit_dir, kernel, C, n_splits=5, tiebreak="vit"):
        super().__init__(vgg16_dir, resnet50v2_dir, vit_dir)
        self.kernel = kernel
        self.C = C
        self.n_splits = n_splits
        self.tiebreak = tiebreak
        self.class_names = ["Exsiccatae", "Labels", "Live plants"]

    def load_all(self):
        self.load_samples() # from feature_fusion

        X_parts = {} # per model one list, with its own matrix per class
        for model_name in self.sources:
            X_parts[model_name] = []
        y = []
        filenames = []

        for fold in self.folders:
            blocks, vit_names = self.load_fold(fold)
            for model_name, block in blocks.items():
                X_parts[model_name].append(block)
            n_images = len(vit_names)
            labels = [fold - 1] * n_images

            y.extend(labels)
            filenames.extend(vit_names)

        X = {}
        for model_name, parts in X_parts.items(): # stacking matrices f1, f2, and f3 of each model
            X[model_name] = np.vstack(parts)

        return X, np.array(y), filenames

    def vote(self, predictions):
        # predictions: (n_models, n_samples), one row of predicted classes per model
        model_names = list(self.sources)
        tiebreak_idx = model_names.index(self.tiebreak)
        n_classes = len(self.folders)
        n_samples = predictions.shape[1]

        result = np.zeros(n_samples, dtype=int)
        ties = []

        for j in range(n_samples):
            votes = predictions[:, j] # the votes of the models for the image j
            counts = np.bincount(votes, minlength=n_classes) # how many votes each class got
            max_votes = counts.max()
            winners = np.flatnonzero(counts == max_votes)

            if len(winners) == 1:
                result[j] = winners[0]
            else:
                # tie
                tied_prediction = predictions[tiebreak_idx, j]
                if tied_prediction in winners:
                    result[j] = tied_prediction
                else:
                    result[j] = winners[0]

                ties.append((j, votes, result[j]))

        return result, ties

    def assess(self, X, y, filenames):
        model_names = list(self.sources)
        seed = random.randint(0, 1000)
        # seed = 823 # testing
        skf = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=seed)
        print(f"\nseed: {seed}\n")

        # every sample is tested once, so these hold the out-of-fold predictions
        out_of_fold = {}
        for name in model_names:
            out_of_fold[name] = np.zeros(len(y), dtype=int)
        out_of_fold["vote"] = np.zeros(len(y), dtype=int)

        f1_per_split = {} # f1 for each split, for each model and vote
        for name in out_of_fold:
            f1_per_split[name] = []

        total_ties = 0

        # rows are aligned (same image in the same row)
        for split, (train_idx, test_idx) in enumerate(skf.split(X[model_names[0]], y), 1):
            predictions = []

            for name in model_names:
                X_train = X[name][train_idx]
                X_test = X[name][test_idx]
                y_train = y[train_idx]

                scaler = StandardScaler()
                X_train = scaler.fit_transform(X_train)
                X_test = scaler.transform(X_test)

                svm = SVC(kernel=self.kernel, C=self.C)
                svm.fit(X_train, y_train)
                y_pred = svm.predict(X_test)

                predictions.append(y_pred)

            predictions = np.array(predictions)
            voted, ties = self.vote(predictions)
            n_ties = len(ties)
            total_ties += n_ties

            for name, pred in zip(model_names, predictions):
                out_of_fold[name][test_idx] = pred
            out_of_fold["vote"][test_idx] = voted

            all_names = model_names + ["vote"]
            all_predictions = list(predictions) + [voted]

            line = []
            for name, pred in zip(all_names, all_predictions):
                f1 = f1_score(y[test_idx], pred, average='weighted')
                f1_per_split[name].append(f1)
                line.append(f"{name} {f1:.4f}")
            print(f"split {split} - f1: " + " / ".join(line) + f" / ties: {n_ties}")

            for j, votes, chosen_class in ties:
                image_idx = test_idx[j]  # position of the image in the whole dataset
                true_class = y[image_idx]

                votes_text = []
                for name, vote in zip(model_names, votes):
                    votes_text.append(f"{name} f{vote + 1}")

                if chosen_class == true_class:
                    outcome = "correct"
                else:
                    outcome = "wrong"

                print(f"  tie - {filenames[image_idx]} (true was f{true_class + 1}) - "
                      + " / ".join(votes_text)
                      + f" - vote f{chosen_class + 1} by {self.tiebreak} ({outcome})")

        print("\naverage f1 (standard deviation):")
        for name, values in f1_per_split.items():
            average = np.mean(values)
            deviation = np.std(values)
            print(f"  {name}: {average:.4f} ({deviation:.4f})")
        print(f"samples decided by tie-break ({self.tiebreak}) - {total_ties} of {len(y)}")

        return out_of_fold

    def show_matrix(self, y, y_pred):
        import matplotlib.pyplot as plt
        import seaborn as sns

        cm = confusion_matrix(y, y_pred)
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Greens", xticklabels=self.class_names, yticklabels=self.class_names)
        plt.xlabel("Predicted class")
        plt.ylabel("True class")
        plt.title("Confusion matrix (voting)")
        plt.show()

    def train_final_models(self, X, y):
        scalers = {}
        svms = {}

        for name in self.sources:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X[name])

            svm = SVC(kernel=self.kernel, C=self.C)
            svm.fit(X_scaled, y)

            scalers[name] = scaler
            svms[name] = svm

        return scalers, svms

    def load_extractors(self, origin_dir, destiny_dir):
        extractors = {}

        vgg_model = tf.keras.applications.VGG16(weights='imagenet', include_top=False, pooling='avg')
        vgg_preprocess = tf.keras.applications.vgg16.preprocess_input
        extractors["vgg16"] = (vgg_model, vgg_preprocess)

        resnet_model = tf.keras.applications.ResNet50V2(weights='imagenet', include_top=False, pooling='avg')
        resnet_preprocess = tf.keras.applications.resnet_v2.preprocess_input
        extractors["resnet50v2"] = (resnet_model, resnet_preprocess)

        vit_extractor = vit_feature_extractor(origin_dir, destiny_dir)
        vit_extractor.load_model()
        extractors["vit"] = vit_extractor

        return extractors

    def extract_features(self, file, extractors, target_size):
        features = {}

        img = tf.keras.preprocessing.image.load_img(file, target_size=target_size)
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)

        for name in ("vgg16", "resnet50v2"):
            model, preprocess_input = extractors[name]
            prepared = preprocess_input(img_array.copy())
            features[name] = model.predict(prepared, verbose=0)  # (1, n_features)

        with torch.no_grad():
            features["vit"] = extractors["vit"].extract_image(file)

        return features

    def organize_images(self, origin_dir, destiny_dir, target_size=(224, 224)):
        model_names = list(self.sources)
        classes_map = {0: "f1", 1: "f2", 2: "f3"}

        X, y, filenames = self.load_all()
        scalers, svms = self.train_final_models(X, y)

        extractors = self.load_extractors(origin_dir, destiny_dir)

        for folder in classes_map.values():
            (Path(destiny_dir) / folder).mkdir(parents=True, exist_ok=True)

        files = sorted(p for p in Path(origin_dir).rglob("*") if p.is_file() and p.suffix.lower() in self.valid_extensions)
        print(f"\n{len(files)} images to organize\n")

        for file in files:
            features = self.extract_features(file, extractors, target_size)

            predictions = []
            for name in model_names:
                if features[name].shape[1] != X[name].shape[1]:
                    raise ValueError(f"{name} - the new image has {features[name].shape[1]} features, but the training has {X[name].shape[1]}. use the same size and model of the training extraction")

                features_scaled = scalers[name].transform(features[name])
                prediction = svms[name].predict(features_scaled)[0]
                predictions.append(prediction)

            # vote expects (n_models, n_samples), here there is only one sample
            predictions = np.array(predictions).reshape(len(model_names), 1)
            voted, ties = self.vote(predictions)
            chosen_class = voted[0]

            votes_text = []
            for name, prediction in zip(model_names, predictions[:, 0]):
                votes_text.append(f"{name} f{prediction + 1}")

            chosen_folder = classes_map[chosen_class]
            final_path = Path(destiny_dir) / chosen_folder / file.name
            shutil.copy(str(file), final_path)

            tie_text = f" - tie, decided by {self.tiebreak}" if ties else ""
            print(f" {file.name} copied to /{chosen_folder} ({' / '.join(votes_text)}){tie_text}")

        print(f"\norganizing concluded. images separated in {destiny_dir}")

    def run(self, matrix=False):
        for model_name, source_dir in self.sources.items():
            if not source_dir.exists():
                raise SystemExit(f"{model_name} - {source_dir} does not exist")

        X, y, filenames = self.load_all()
        out_of_fold = self.assess(X, y, filenames)

        if matrix:
            self.show_matrix(y, out_of_fold["vote"])

def main():
    parser = argparse.ArgumentParser(description="early fusion of features from different models")
    subparsers = parser.add_subparsers(dest="command", help="method to be executed")

    fuse = subparsers.add_parser("fuse", help="concatenates the features of vgg16, resnet50v2 and vit")
    fuse.add_argument("--vgg16", required=True, help="folder with the vgg16 features")
    fuse.add_argument("--resnet50v2", required=True, help="folder with the resnet50v2 features")
    fuse.add_argument("--vit", required=True, help="folder with the vit features")
    fuse.add_argument("--output", "-o", required=True, help="output folder for the fused features")

    late = subparsers.add_parser("late", help="late fusion, one svm per model, final class by majority vote")
    late.add_argument("--vgg16", required=True, help="folder with the vgg16 features")
    late.add_argument("--resnet50v2", required=True, help="folder with the resnet50v2 features")
    late.add_argument("--vit", required=True, help="folder with the vit features")
    late.add_argument("--kernel", default="linear", help="kernel (ex: linear, rbf, poly)")
    late.add_argument("--c", type=float, default=1.0, help="C margin")
    late.add_argument("--splits", type=int, default=5, help="number of cross validation splits")
    late.add_argument("--tiebreak", choices=["vgg16", "resnet50v2", "vit"], default="vit", help="model that decides when all models disagree")
    late.add_argument("--matrix", type=int, choices=[0, 1], default=1, help="if 1, shows confusion matrix, if 0, doesn't")

    organize = subparsers.add_parser("organize", help="late fusion, classifies new images by majority vote and copies them to f1, f2, f3")
    organize.add_argument("--vgg16", required=True, help="folder with the vgg16 training features")
    organize.add_argument("--resnet50v2", required=True, help="folder with the resnet50v2 training features")
    organize.add_argument("--vit", required=True, help="folder with the vit training features")
    organize.add_argument("--origin_dir", required=True, help="folder with the mixed images")
    organize.add_argument("--destiny_dir", required=True, help="output directory where the organized f1, f2, f3 classes will be placed")
    organize.add_argument("--kernel", default="linear", help="kernel (ex: linear, rbf, poly)")
    organize.add_argument("--c", type=float, default=1.0, help="C margin")
    organize.add_argument("--tiebreak", choices=["vgg16", "resnet50v2", "vit"], default="vit", help="model that decides when all models disagree")
    organize.add_argument("--height", type=int, default=224, help="image height used in the training extraction of vgg16 and resnet50v2")
    organize.add_argument("--width", type=int, default=224, help="image width used in the training extraction of vgg16 and resnet50v2")

    args = parser.parse_args()

    if args.command == "fuse":
        fusion = feature_fusion(args.vgg16, args.resnet50v2, args.vit, args.output)
        fusion.fuse()
        print("\nearly fusion concluded\n")
    elif args.command == "late":
        fusion = late_fusion(args.vgg16, args.resnet50v2, args.vit, kernel=args.kernel, C=args.c, n_splits=args.splits, tiebreak=args.tiebreak)
        fusion.run(matrix=bool(args.matrix))
        print("\nlate fusion concluded\n")
    elif args.command == "organize":
        fusion = late_fusion(args.vgg16, args.resnet50v2, args.vit, kernel=args.kernel, C=args.c, tiebreak=args.tiebreak)
        fusion.organize_images(args.origin_dir, args.destiny_dir, target_size=(args.height, args.width))
        print("\nlate fusion organizing concluded\n")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()