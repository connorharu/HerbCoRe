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
from PIL import Image
import torch
from transformers import ViTImageProcessor, ViTModel
from tensorflow.keras.applications import VGG16, ResNet50V2
from tensorflow.keras.applications.vgg16 import preprocess_input as preprocess_vgg
from tensorflow.keras.applications.resnet_v2 import preprocess_input as preprocess_resnet
import joblib