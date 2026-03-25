import json
import os
import sys
import mysql.connector as mysql_conn
import matplotlib.pyplot as plt
from io import StringIO
import pandas as pd
import tempfile
import os
import subprocess
import shutil

diretorio = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(diretorio)
ferramenta_path = os.path.join(parent_dir, 'ferramenta_herbcore')
if ferramenta_path not in sys.path:
    sys.path.append(ferramenta_path)

from config import get_config, ask_for_missing_values
from main_f import species_link
from sinonimos import extract_plants_from_txt, save_plants_to_csv, perform_lcvp_fuzzy_search, perform_lcvp_fuzzy_search_per_line, save_result_to_txt_aligned
from rpy2.robjects.packages import importr
from deduplicacao import processar

__all__ = [
    'json', 'os', 'sys', 'mysql_conn', 'plt', 'pd', 'tempfile', 
    'subprocess', 'StringIO', 'configurar', 'species_link',
    'extract_plants_from_txt', 'processar', 'perform_lcvp_fuzzy_search_per_line', 'shutil'
]

def configurar():
    config = get_config()

    if config is None or any(k not in config for k in ['api_key', 'db_user', 'db_password', 'db_host', 'db_schema']):
        config = ask_for_missing_values()

    api_key = config['api_key']
    db_config = {
        'user': config['db_user'],
        'password': config['db_password'],
        'host': config['db_host'],
        'database': config['db_schema']
    }
    specieslink = species_link(api_key=api_key)

    return specieslink, db_config