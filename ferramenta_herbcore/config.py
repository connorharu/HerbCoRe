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
    config['api_key'] = input("informe a chave da API: ").strip().strip('"')
    config['db_user'] = input("informe o usuário do banco de dados: ").strip().strip('"')
    config['db_password'] = input("informe a senha do banco de dados: ").strip().strip('"')
    config['db_host'] = input("informe o host do banco de dados (exemplo: 127.0.0.1): ").strip().strip('"')
    config['db_schema'] = input("informe o schema do banco de dados: ").strip().strip('"')

    save_config(config)
    return config
