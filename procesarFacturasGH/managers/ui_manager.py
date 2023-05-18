from PyQt5.QtCore import QDate
from PyQt5.QtCore import pyqtSignal , QObject 
from utils.utils import Utils

class UIManager(QObject):
    saved = pyqtSignal()

    def __init__(self, main_window, config_manager):
        super().__init__()
        self.main_window = main_window
        self.config_manager = config_manager
        self.config = config_manager.config

    def set_current_window(self, window):
        self.main_window = window

    def save_params(self):       

        self.config_manager.set('EMAIL', self.main_window.txtEmail.text())
        self.config_manager.set('PASSWORD', self.main_window.txtPassword.text())
        self.config_manager.set('API_KEY', self.main_window.txtCodeApiKey.text())
        self.config_manager.set('EMAIL_FILE_TYPE', self.main_window.cmbFileType.currentText())
        self.config_manager.set('MAX_EMAILS', str(self.main_window.spMaxEmails.value()))
        self.config_manager.set('EMAIL_INIT', str(self.main_window.spInitScanEmail.value()))
        self.config_manager.set('MAX_NREQUEST_OPENAI', str(self.main_window.spMaxResp.value()))
        self.config_manager.set('PATH_EMAILS_EML', str(self.main_window.txtPathEmailsEml.text()))
        self.config_manager.set('PATH_EMAILS_MSG', self.main_window.txtPathEmailsMsg.text())
        self.config_manager.set('PATH_TESSERACT', self.main_window.txtTesseractPath.text())
        self.config_manager.set('PATH_EXPORT_XLS', self.main_window.txtExportData.text())
        self.config_manager.set('TYPE_CONTENT', self.main_window.cmbTypeContent.currentText())

        # Actualizar el diccionario de configuración con los cambios
        updated_config = self.config_manager.config

        # Guardar las configuraciones en el archivo config.json
        self.config_manager.save_config()
        
        self.main_window.btnSaveParams.setEnabled(False)
        self.config = updated_config
        self.saved.emit()

    def save_params_txtprompts(self):  

        # Reemplazar '\n' con '\\n' en el prompt antes de guardarlo en la configuración
        prompt = self.main_window.txtPrompt.toPlainText()
        prompt = prompt.replace('\n', '\\n')
        promptd = self.main_window.txtPromptDetailInvoice.toPlainText()
        promptd = promptd.replace('\n', '\\n')

        prompto = self.main_window.txtPromptOrder.toPlainText()
        prompto = prompto.replace('\n', '\\n')
        promptd_order = self.main_window.txtPromptDetailOrder.toPlainText()
        promptd_order = promptd_order.replace('\n', '\\n')

        self.config_manager.set('PROMPT', prompt)
        self.config_manager.set('PROMPT_DETAIL', promptd)
        self.config_manager.set('PROMPT_ORDER', prompto)
        self.config_manager.set('PROMPT_DETAIL_ORDER', promptd_order)

        # Actualizar el diccionario de configuración con los cambios
        updated_config = self.config_manager.config

        # Guardar las configuraciones en el archivo config.json
        self.config_manager.save_config()
        
        self.main_window.btnSaveParamsPrompts.setEnabled(False)
        self.config = updated_config
        self.saved.emit()

    def setup_widgets(self):
        """
        Configura los widgets de la ventana.
        """
       
        self.main_window.dateStart.setDate(QDate.currentDate())
        self.main_window.dateEnd.setDate(QDate.currentDate())

        self.main_window.spMaxResp.setValue(int(self.config.get("MAX_NREQUEST_OPENAI")))
        self.main_window.spMaxEmails.setValue(int(self.config.get("MAX_EMAILS")))
        self.main_window.spInitScanEmail.setValue(int(self.config.get("EMAIL_INIT")))
        self.main_window.txtEmail.setText(self.config.get("EMAIL"))
        self.main_window.txtPassword.setText(self.config.get("PASSWORD"))
        self.main_window.txtCodeApiKey.setText(self.config.get("API_KEY"))
        self.main_window.txtTesseractPath.setText(self.config.get("PATH_TESSERACT"))
        self.main_window.txtPathEmailsMsg.setText(self.config.get("PATH_EMAILS_MSG"))
        self.main_window.txtPathEmailsEml.setText(self.config.get("PATH_EMAILS_EML"))
        self.main_window.txtExportData.setText(self.config.get("PATH_EXPORT_XLS"))
        self.main_window.btnSaveParams.setEnabled(False)


    def setup_widgets_txtprompts(self):
        # Reemplazar '\\n' con '\n' en el prompt antes de asignarlo al QPlainTextEdit
        prompt = self.config.get("PROMPT")
        prompt = prompt.replace('\\n', '\n')
        promptd = self.config.get("PROMPT_DETAIL")
        promptd = promptd.replace('\\n', '\n')

        prompto = self.config.get("PROMPT_ORDER")
        prompto = prompto.replace('\\n', '\n')
        promptd_order = self.config.get("PROMPT_DETAIL_ORDER")
        promptd_order = promptd_order.replace('\\n', '\n')
        
        self.main_window.txtPrompt.setPlainText(prompt)
        self.main_window.txtPromptDetailInvoice.setPlainText(promptd)
        self.main_window.txtPromptOrder.setPlainText(prompto)
        self.main_window.txtPromptDetailOrder.setPlainText(promptd_order)

        self.main_window.btnSaveParamsPrompts.setEnabled(False)

    def setup_connections_txtprompts(self):
        # Conecta las señales de cambio de texto para los prompts
        self.main_window.txtPrompt.textChanged.connect(lambda: [self.main_window.prompt_params_changed(), self.main_window.on_txtPrompt_textChanged()])
        self.main_window.txtPromptDetailInvoice.textChanged.connect(lambda: [self.main_window.prompt_params_changed(), self.main_window.on_txtPrompt_textChanged()])
        self.main_window.txtPromptOrder.textChanged.connect(lambda: [self.main_window.prompt_params_changed(), self.main_window.on_txtPrompt_textChanged()])
        self.main_window.txtPromptDetailOrder.textChanged.connect(lambda: [self.main_window.prompt_params_changed(), self.main_window.on_txtPrompt_textChanged()])
        
    def setup_connections(self):
        self.main_window.spMaxResp.valueChanged.connect(self.main_window.params_changed)
        self.main_window.spMaxEmails.valueChanged.connect(self.main_window.params_changed)
        self.main_window.spInitScanEmail.valueChanged.connect(self.main_window.params_changed)

        self.main_window.txtEmail.textChanged.connect(self.main_window.params_changed)
        self.main_window.txtPassword.textChanged.connect(self.main_window.params_changed)
        self.main_window.txtCodeApiKey.textChanged.connect(self.main_window.params_changed)
        self.main_window.cmbFileType.currentIndexChanged.connect(self.main_window.params_changed)
        self.main_window.cmbTypeContent.currentIndexChanged.connect(self.main_window.params_changed)
        self.main_window.cmbLanguage.currentIndexChanged.connect(self.apply_translations_to_invoice_window)
        self.main_window.cmbImapServers.currentIndexChanged.connect(self.main_window.on_imap_server_changed)

        self.main_window.btnSetPathEmailsEml.clicked.connect(self.main_window.choose_email_eml_folder)
        self.main_window.btnSetPathData.clicked.connect(self.main_window.choose_data_folder)
        self.main_window.btnSetPathEmailsMsg.clicked.connect(self.main_window.choose_email_msg_folder)
        self.main_window.btnSetTesseractPath.clicked.connect(self.main_window.choose_tesseract_folder)
        self.main_window.btnSaveParams.clicked.connect(self.main_window.save_params)
        self.main_window.btnShowApiKey.clicked.connect(lambda: self.main_window.toggle_password_visibility(self.main_window.txtCodeApiKey))
        self.main_window.btnShowPassEmail.clicked.connect(lambda: self.main_window.toggle_password_visibility(self.main_window.txtPassword))
        self.main_window.btnPrompts.clicked.connect(self.main_window.open_invoice_prompts_window)

        self.main_window.actionDownload_Emails.triggered.connect(self.main_window.connect_and_retrieve_attachments_triggered)
        self.main_window.actionProcess_Emails_Offline.triggered.connect(self.main_window.offline_email_processing)

        self.main_window.txtEmail.textChanged.connect(self.main_window.update_actions_and_buttons)
        self.main_window.txtPassword.textChanged.connect(self.main_window.update_actions_and_buttons)

        self.main_window.txtPathEmailsEml.textChanged.connect(lambda: Utils.validate_and_update_path(self.main_window.txtPathEmailsEml.text()))
        self.main_window.txtPathEmailsMsg.textChanged.connect(lambda: Utils.validate_and_update_path(self.main_window.txtPathEmailsMsg.text()))
        self.main_window.txtExportData.textChanged.connect(lambda: Utils.validate_and_update_path(self.main_window.txtExportData.text()))
        self.main_window.txtTesseractPath.textChanged.connect(lambda: Utils.validate_and_update_path(self.main_window.txtTesseractPath.text()))

        self.saved.connect(self.main_window.on_params_saved)
        
    def apply_translations_to_invoice_window(self, index):
        self.main_window.translations_manager.translate_ui()       

