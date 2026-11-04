import re
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

class feature_fusion:
    def __init__(self, vgg16_dir, resnet50v2_dir, vit_dir, output_dir):
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

def main():
    parser = argparse.ArgumentParser(description="early fusion of features from different models")
    subparsers = parser.add_subparsers(dest="command", help="method to be executed")

    fuse = subparsers.add_parser("fuse", help="concatenates the features of vgg16, resnet50v2 and vit")
    fuse.add_argument("--vgg16", required=True, help="folder with the vgg16 features")
    fuse.add_argument("--resnet50v2", required=True, help="folder with the resnet50v2 features")
    fuse.add_argument("--vit", required=True, help="folder with the vit features")
    fuse.add_argument("--output", "-o", required=True, help="output folder for the fused features")

    args = parser.parse_args()

    if args.command == "fuse":
        fusion = feature_fusion(args.vgg16, args.resnet50v2, args.vit, args.output)
        fusion.fuse()
        print("fusion concluded")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
