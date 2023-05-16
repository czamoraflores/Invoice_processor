import os 

from PyQt5.QtWidgets import QFileDialog, QLineEdit, QGroupBox, QStatusBar, QProgressDialog
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt

from controllers.email.email_connector import EmailConnector
from controllers.email.email_connector import EmailConnectorThread
from controllers.invoice_processing.invoice_processor import InvoiceProcessor

from views.base_window import BaseWindow

from managers.ui_manager import UIManager
from managers.translation_manager import TranslationManager

from views.invoice_prompts_form.InvoicePromptsWindow import InvoicePromptsWindow

from utils.utils import Utils
from utils.email_utils import EmailUtils

class InvoiceRetrievalWindow(BaseWindow):
    """
    Clase para la ventana de recuperación de facturas.
    """
    def __init__(self):
        """
        Inicializa la ventana y sus componentes.
        """
        super(InvoiceRetrievalWindow, self).__init__()
        self.ui_manager = UIManager(self, self.config_manager)

        ui_file = os.path.join(self.root_directory, 'views/invoice_retrieval_form', 'InvoiceRetrievalForm.ui')
        loadUi(ui_file, self)

        self.groupBoxOptions = self.findChild(QGroupBox, "groupBoxOptions")
        self.groupBoxSettings = self.findChild(QGroupBox, "groupBoxSettings")
        self.groupBoxEvents = self.findChild(QGroupBox, "groupBoxEvents")

        self.add_items_to_file_type_combo_box()  
        self.add_items_to_content_type_combo_box()
       
        self.ui_manager.setup_connections()
        self.ui_manager.setup_widgets()

        self.translations_manager = TranslationManager(self, self.translations_file)
        self.cmbLanguage.currentIndexChanged.connect(self.apply_translations_to_invoice_window)

        self.txtPathEmailsEml.setText(Utils.validate_and_update_path(self.txtPathEmailsEml.text()))
        self.txtPathEmailsMsg.setText(Utils.validate_and_update_path(self.txtPathEmailsMsg.text()))
        self.txtExportData.setText(Utils.validate_and_update_path(self.txtExportData.text()))
        self.txtTesseractPath.setText(Utils.validate_and_update_path(self.txtTesseractPath.text()))

        self.last_valid_text = ""
        self.last_valid_cursor = None

        self.statusBar = QStatusBar()     # Crear una instancia de QStatusBar
        self.setStatusBar(self.statusBar) # Establecer la barra de estado en la ventana
        self.update_status_bar("Listo")   # Establecer un mensaje inicial en la barra de estado

        self.setup_language_combo_box(self.cmbLanguage)

    def open_invoice_prompts_window(self):
        self.invoice_prompts_window = InvoicePromptsWindow(self)
        self.invoice_prompts_window.setWindowModality(Qt.ApplicationModal)  # Hace la ventana modal
        self.invoice_prompts_window.show()

    def on_params_saved(self):
        # Actualiza la barra de estado
        self.update_status_bar(self.translations[self.language_code]['ui']['savedParams'])

    def save_params(self):
        self.ui_manager.save_params() 

    #
    # CAMBIO DE RUTAS
    #
    def choose_tesseract_folder(self):
        file_filter =  self.translations[self.language_code]['ui']['tesseractExecutable']
        file_path, _ = QFileDialog.getOpenFileName(self, self.translations[self.language_code]['ui']['selectTesseract'], self.config["PATH_TESSERACT"], file_filter)
        if file_path:
            folder_path = os.path.dirname(file_path)
            self.config["PATH_TESSERACT"] = folder_path
            self.txtTesseractPath.setText(file_path)
            self.params_changed()  # Añade esta línea

    def choose_email_eml_folder(self): 
        folder_path = QFileDialog.getExistingDirectory(self, self.translations[self.language_code]['ui']['selectFolder'], self.config["PATH_EMAILS_EML"])
        if folder_path:
            self.config["PATH_EMAILS_EML"] = folder_path
            self.txtPathEmailsEml.setText(folder_path)
            self.params_changed()  # Añade esta línea

    def choose_data_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.translations[self.language_code]['ui']['selectFolder'], self.config["PATH_EXPORT_XLS"])
        if folder_path:
            self.config["PATH_EXPORT_XLS"] = folder_path
            self.txtExportData.setText(folder_path)
            self.params_changed()  # Añade esta línea

    def choose_email_msg_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, self.translations[self.language_code]['ui']['selectFolder'], self.config["PATH_EMAILS_MSG"])
        if folder_path:
            self.config["PATH_EMAILS_MSG"] = folder_path
            self.txtPathEmailsMsg.setText(folder_path)
            self.params_changed()  # Añade esta línea

    def apply_translations_to_invoice_window(self, index):
        self.language_code = self.cmbLanguage.itemData(index)
        self.translation_manager.translate_ui

    #
    # USO DE COMBOBOX
    #
    def add_items_to_file_type_combo_box(self):
        options = [".msg", ".eml"]  # Lista con las opciones de formatos de archivo
        self.cmbFileType.addItems(options)  # Agregar las opciones al comboBox
        default_file_type = self.config_manager.config["EMAIL_FILE_TYPE"]  # Establecer el tipo de archivo predeterminado según la variable de entorno
        index = self.cmbFileType.findText(default_file_type, Qt.MatchExactly)
        if index >= 0:
            self.cmbFileType.setCurrentIndex(index)

    def add_items_to_content_type_combo_box(self):
        options = ["content", "body", "combined"]  # Lista con las opciones de contenido
        self.cmbTypeContent.addItems(options)  # Agregar las opciones al comboBox
        default_content_type = self.config_manager.config["TYPE_CONTENT"]  # Establecer el tipo de contenido predeterminado según la variable de entorno
        index = self.cmbTypeContent.findText(default_content_type, Qt.MatchExactly)
        if index >= 0:
            self.cmbTypeContent.setCurrentIndex(index)

    def setup_language_combo_box(self, combo_box):
        languages = {
            "English": "en",
            "Español": "es"
            # Agrega más idiomas
        }

        for language, code in languages.items():
            combo_box.addItem(language,code)

        # Establece el idioma predeterminado (en este caso, inglés)
        default_language = "en"
        index = combo_box.findData(default_language, Qt.UserRole, Qt.MatchExactly)
        if index >= 0:
            combo_box.setCurrentIndex(index)

    def disable_inputs(self):
        #Deshabilitar todas las entradas
        self.txtEmail.setEnabled(False)
        self.txtPassword.setEnabled(False)
        self.dateStart.setEnabled(False)
        self.dateEnd.setEnabled(False)
        self.txtCodeApiKey.setEnabled(False)
        self.cmbFileType.setEnabled(False)
        self.cmbTypeContent.setEnabled(False)
        self.spMaxResp.setEnabled(False)
        self.spMaxTokens.setEnabled(False)
        self.spMaxEmails.setEnabled(False)
        self.txtPathEmails.setEnabled(False)
        self.txtPathAttachment.setEnabled(False)
        self.txtExportData.setEnabled(False)
        self.txtTesseractPath.setEnabled(False)
        self.btnSaveParams.setEnabled(False)
        self.btnSetAttachDown.setEnabled(False)
        self.btnSetPathData.setEnabled(False)
        self.btnSetPathEmails.setEnabled(False)
        self.btnSetTesseractPath.setEnabled(False)
        self.btnShowApiKey.setEnabled(False)
        self.btnShowPassEmail.setEnabled(False)

    def init_progress_dialog(self, label_text, window_title):
        progress_dialog = QProgressDialog(self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setLabelText(label_text)
        progress_dialog.setWindowTitle(window_title)
        progress_dialog.setCancelButton(None)
        progress_dialog.setRange(0, 100)
        progress_dialog.resize(300, progress_dialog.height())
        return progress_dialog
    
    def update_status_bar(self, message):
        self.statusBar.showMessage(message)

    # 
    # CUADRO DE EVENTOS
    #
    def print_results(self, results):
        for key, value in results.items():
            # Agrega un separador visual
            self.txtEvents.append("--------------------------------------------------")
            # Imprime la clave y el valor
            self.txtEvents.append(f"{key}: {value}")

    # 
    # CAMBIO DE ESTADO DE LOS MENUS
    #
    def update_actions_and_buttons(self):
        email_and_password_valid = EmailUtils.validate_email_and_password(self.txtEmail.text(), self.txtPassword.text())
        self.actionDownload_Emails.setEnabled(email_and_password_valid)
        self.actionProcess_Emails_Online.setEnabled(email_and_password_valid)
        self.actionLogin.setEnabled(email_and_password_valid) 

    def toggle_password_visibility(self, line_edit):
        if line_edit.echoMode() == QLineEdit.Normal:
            line_edit.setEchoMode(QLineEdit.Password)
        else:
            line_edit.setEchoMode(QLineEdit.Normal)

    def params_changed(self):
        self.btnSaveParams.setEnabled(True)
       
    def on_thread_finished(self):
        self.progress_dialog.setValue(100)
        self.progress_dialog.close()

    # 
    # CORE: OBTENCION DE CORREOS
    #
    def connect_and_retrieve_attachments_triggered(self):

        # Inicializar el QProgressDialog
        progress_dialog = self.init_progress_dialog(self.translations[self.language_code]['ui']['downloadingEmails'], self.translations[self.language_code]['ui']['pleaseWait'])
        progress_dialog.show()

        email = self.txtEmail.text()
        password = self.txtPassword.text()
        date_start = self.dateStart.date().toString('dd/MM/yyyy')
        date_end = self.dateEnd.date().toString('dd/MM/yyyy')

        email_connector = EmailConnector(email, password, self)
        email_connector.progress_updated.connect(progress_dialog.setValue)
        email_connector.status_updated.connect(self.update_status_bar)  # Conectar la señal status_updated

        t1 = EmailConnectorThread(email_connector, date_start, date_end)
        t1.finished.connect(progress_dialog.close)  # Cerrar el QProgressDialog cuando termine el hilo
        t1.start()

        progress_dialog.exec()  # Espera a que se cierre el diálogo
        t1.wait()  # Espera a que termine el hilo antes de cerrar la aplicación

    def offline_email_processing(self):
        params = self.get_params_interfaz()
        translations = self.translations[self.language_code]
        invoice_processor = InvoiceProcessor(params, translations, self)
        invoice_processor.process_invoices_offline()
        
    def get_params_interfaz(self):
        params = {
            'api_key': self.txtCodeApiKey.text(),
            'email': self.txtEmail.text(),
            'password': self.txtPassword.text(),
            'date_start': self.dateStart.date().toString('dd/MM/yyyy'),
            'date_end': self.dateEnd.date().toString('dd/MM/yyyy'),
            'path_emails_msg': self.txtPathEmailsMsg.text(),
            'path_emails_eml': self.txtPathEmailsEml.text(),
            'path_export_xls': self.txtExportData.text(),
            'path_proyect': self.root_directory, 
            'tesseract_path': self.txtTesseractPath.text(),
            'minimum_key_count': self.config['MINIMUM_KEY_COUNT'],
            'max_invoice': int(self.spMaxEmails.value()),
            'email_init': int(self.spInitScanEmail.value()),
            'max_nrquest_openai': int(self.spMaxResp.value()),
            'email_file_type': self.cmbFileType.currentText(),
            'type_content': self.cmbTypeContent.currentText(),
            'language': self.cmbLanguage.itemData(self.cmbLanguage.currentIndex()),
             # Text prompts
            'prompt': self.config['PROMPT'].replace('\\n', '\n'),
            'promptd': self.config['PROMPT_DETAIL'].replace('\\n', '\n'),
            'prompt_order': self.config['PROMPT_ORDER'].replace('\\n', '\n'),
            'promptd_order': self.config['PROMPT_DETAIL_ORDER'].replace('\\n', '\n'),

        }
        return params


