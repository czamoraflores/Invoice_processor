import os 

from PyQt5.QtWidgets import QGroupBox
from PyQt5.uic import loadUi

from managers.ui_manager import UIManager
from managers.translation_manager import TranslationManager
from utils.utils import Utils
from views.base_window import BaseWindow

class InvoicePromptsWindow(BaseWindow):
    def __init__(self, parent):
        super(InvoicePromptsWindow, self).__init__()       
        self.parent = parent
        self.ui_manager = UIManager(self, self.config_manager)

        ui_file = os.path.join(self.root_directory, 'views/invoice_prompts_form', 'InvoicePromptsForm.ui')
        loadUi(ui_file, self)

        self.groupBoxPrompts = self.findChild(QGroupBox, "groupBoxPrompts")

        self.ui_manager.setup_connections_txtprompts()
        self.ui_manager.setup_widgets_txtprompts()

        self.translations_manager = TranslationManager(self, self.translations_file)
        self.btnSaveParamsPrompts.clicked.connect(self.save_params)

        self.last_valid_text = ""
        self.last_valid_cursor = None

    def save_params(self):
        self.ui_manager.save_params_txtprompts() 
        self.btnSaveParamsPrompts.setEnabled(False)

    def prompt_params_changed(self):
        self.btnSaveParamsPrompts.setEnabled(True)

    def get_params_interfaz(self):
        params = {
            'prompt': self.txtPrompt.toPlainText(),
            'promptd': self.txtPromptDetailInvoice.toPlainText(),
            'prompt_order': self.txtPromptOrder.toPlainText(),
            'promptd_order': self.txtPromptDetailOrder.toPlainText(),
        }
        return params
    ##
    ## TOKENS 
    ##
    def update_token_count(self, text_box):
        prompt_text = text_box.toPlainText()
        token_count = Utils.get_dynamic_max_tokens(prompt_text)  
        return token_count

    def on_txtPrompt_textChanged(self):
        # Obtiene el texto actual en txtPrompt
        text_box = self.sender()
        prompt_text = text_box.toPlainText()

        # Cuenta los tokens en el texto actual
        token_count = self.update_token_count(text_box)

        # Si la cantidad de tokens supera el máximo permitido
        if token_count > 4096:
            # Restaura el texto en text_box al último texto válido
            text_box.blockSignals(True)
            text_box.setPlainText(self.last_valid_text)
            text_box.blockSignals(False)

            # Restaura el cursor a la posición anterior, si self.last_valid_cursor no es None
            if self.last_valid_cursor is not None:
                text_box.setTextCursor(self.last_valid_cursor)
        else:
            # Guarda el último texto válido y la posición del cursor
            self.last_valid_text = prompt_text
            self.last_valid_cursor = text_box.textCursor()

        if text_box is self.txtPrompt:
            self.txtTokensHeaderInvoice.setText(str(token_count))
        elif text_box is self.txtPromptDetailInvoice:
            self.txtTokensDetailInvoice.setText(str(token_count))
        elif text_box is self.txtPromptOrder:
            self.txtTokensHeaderOrder.setText(str(token_count))
        elif text_box is self.txtPromptDetailOrder:
            self.txtTokensDetailOrder.setText(str(token_count))


 