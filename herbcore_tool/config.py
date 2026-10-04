import os
import json

def get_config():
    if os.path.exists('config.json'):
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_config(config):
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def ask_for_missing_values():
    config = {}
    config['api_key'] = input("provide the API key: ").strip().strip('"')
    config['db_user'] = input("provide the database username: ").strip().strip('"')
    config['db_password'] = input("provide the database password: ").strip().strip('"')
    config['db_host'] = input("provide the database host (example: 127.0.0.1): ").strip().strip('"')
    config['db_schema'] = input("provide the database schema: ").strip().strip('"')
    config['r_home'] = input("provide the path to the R installation (ex: C:\\Program Files\\R\\R-4.4.2): ").strip().strip('"')

    save_config(config)
    return config
