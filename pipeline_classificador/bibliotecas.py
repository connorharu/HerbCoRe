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
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
import joblib