import json

class ConfigManager:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_json()

    def get(self, key):
        return self.config.get(key)
    
    def set(self, key, value):
        if isinstance(value, list) and all(isinstance(i, dict) for i in value):
            # Trata el valor como una lista de diccionarios
            self.config[key] = value
        else:
            # Trata el valor como una cadena de texto
            self.config[key] = str(value)
        return self.config

    def update_config(self, config_dict):
        for key, value in config_dict.items():
            self.set(key, value)

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as file:
            json.dump(self.config, file, ensure_ascii=False, indent=2)

    def load_json(self):
        with open(self.config_file, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
        return config_data
    