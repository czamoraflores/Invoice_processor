import json

class TranslationManager:
    def __init__(self, main_window, translations_file):
        self.main_window = main_window
        self.translations_file = translations_file
        self.translations = self.load_translations()

    def load_translations(self):
        with open(self.translations_file, "r", encoding="utf-8") as file:
            translations = json.load(file)

        return translations

    def get_translations(self, lang):
        return self.translations[lang]
    
    def translate_ui(self):
        language = self.main_window.cmbLanguage.itemData(self.main_window.cmbLanguage.currentIndex())
        if language is None:
            language = "en"
        
        translations = self.get_translations(language)["ui"]
        self.main_window.update_status_bar(translations["barIni"])

        translatable_widgets = [
            self.main_window.groupBoxOptions,
            self.main_window.groupBoxSettings,
            self.main_window.groupBoxEvents
        ]

        for key, value in translations.items():
            widget = getattr(self.main_window, key, None)
            if widget:
                if key.startswith("tooltip"):
                    widget.setToolTip(value)
                elif hasattr(widget, 'setText'):
                    widget.setText(value)
                elif hasattr(widget, 'setTitle'):
                    widget.setTitle(value)
                elif hasattr(widget, 'setWindowTitle'):
                    widget.setWindowTitle(value)

        for widget in translatable_widgets:
            if widget:  # Verificación de None
                key = widget.objectName()
                widget.setTitle(translations[key])