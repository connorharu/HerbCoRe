import argparse
import shutil
import traceback
import numpy as np
import torch
from PIL import Image
from pathlib import Path
from transformers import ViTImageProcessor, ViTModel

class vit_feature_extractor:
    def __init__(self, input_dir, output_dir,
                 model_name="google/vit-base-patch16-224-in21k"):
        self.input_path = Path(input_dir).resolve()
        self.output_path = Path(output_dir).resolve()
        self.images_root = self.output_path / "images"
        self.features_root = self.output_path / "features"
        self.folders = [1, 2, 3]
        self.model_name = model_name
        self.valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = None
        self.model = None

    def load_model(self):
        print(f"using {self.device}")
        self.processor = ViTImageProcessor.from_pretrained(self.model_name)
        self.model = ViTModel.from_pretrained(self.model_name).to(self.device).eval()

    def list_images(self, fold_dir):
        return sorted(p for p in fold_dir.rglob("*")
                      if p.is_file() and p.suffix.lower() in self.valid_extensions)

    def extract_image(self, img_path):
        image = Image.open(img_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        outputs = self.model(**inputs)
        return outputs.last_hidden_state[:, 0, :].cpu().numpy()  # (n, 768)

    def copy_image(self, img_path, fold_dir, img_out_dir):
        rel = img_path.relative_to(fold_dir)
        dst = img_out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(img_path, dst)

    def save_features(self, features, fold, feat_out_dir):
        fold_name = f"f{fold}"
        labels = np.full(features.shape[0], fold)
        np.save(feat_out_dir / f"{fold_name}.npy", features)
        np.savez_compressed(feat_out_dir / f"{fold_name}.npz", x=features, y=labels)
        print(f"fold {fold} - saved {features.shape} in {fold_name}.npy")

    def extract_fold(self, fold):
        fold_name = f"f{fold}"
        fold_dir = self.input_path / fold_name

        if not fold_dir.exists():
            print(f"folder {fold_dir} not found. proceeding anyways")
            return

        img_out_dir = self.images_root / fold_name
        feat_out_dir = self.features_root / fold_name
        img_out_dir.mkdir(parents=True, exist_ok=True)
        feat_out_dir.mkdir(parents=True, exist_ok=True)

        files = self.list_images(fold_dir)
        print(f"fold {fold} - {len(files)} images")

        features = []
        for img_path in files:
            try:
                cls = self.extract_image(img_path)
                # the image is copied only after its feature was extracted,
                # so images and .npy rows always match
                self.copy_image(img_path, fold_dir, img_out_dir)
                features.append(cls)
            except Exception:
                print(f"error in {img_path}:")
                traceback.print_exc()

        if not features:
            print(f"fold {fold} - no features extracted")
            return

        self.save_features(np.concatenate(features, axis=0), fold, feat_out_dir)

    def extract(self):
        if not self.input_path.exists():
            raise SystemExit(f"{self.input_path} does not exist")

        self.load_model()
        with torch.no_grad():
            for fold in self.folders:
                self.extract_fold(fold)


def main():
    parser = argparse.ArgumentParser(description="feature extraction with a pre-trained ViT")
    subparsers = parser.add_subparsers(dest="command", help="method to be executed")

    extract = subparsers.add_parser("extract", help="extracts the features of each class")
    extract.add_argument("--input", "-i", required=True, help="folder containing the f1, f2, f3 subfolders")
    extract.add_argument("--output", "-o", required=True, help="output folder for images/ and features/")
    extract.add_argument("--model_name", default="google/vit-base-patch16-224-in21k", help="ViT model from Hugging Face")

    args = parser.parse_args()

    if args.command == "extract":
        extractor = vit_feature_extractor(args.input, args.output, args.model_name)
        extractor.extract()
        print("extraction concluded")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()