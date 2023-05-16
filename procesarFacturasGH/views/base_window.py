import os
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt

from managers.config_manager import ConfigManager
from managers.translation_manager import TranslationManager

class BaseWindow(QMainWindow):
    def __init__(self):
        super(BaseWindow, self).__init__()

        # Cargar las configuraciones y traducciones
        self.root_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.translations_file = os.path.join(self.root_directory, 'json\\translations.json')
        self.config_file = os.path.join(self.root_directory, 'json\\config.json')

        self.translation_manager = TranslationManager(self, self.translations_file)
        self.translations = self.translation_manager.load_translations()

        self.config_manager = ConfigManager(self.config_file)
        self.config = self.config_manager.config

        self.language_code = self.translations["default_language"]

    def setup_language_combo_box(self, combo_box):
        languages = {
            "English": "en",
            "Español": "es"
            # Agrega más idiomas
        }

        for language, code in languages.items():
            combo_box.addItem(language, code)

        # Establece el idioma predeterminado (en este caso, inglés)
        default_language = "en"
        index = combo_box.findData(default_language, Qt.UserRole, Qt.MatchExactly)
        if index >= 0:
            combo_box.setCurrentIndex(index)


