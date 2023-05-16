import os
import json
import mimetypes

from PyQt5.QtCore import QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QMessageBox
from imbox import Imbox
from collections import namedtuple

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from utils.email_utils import EmailUtils
from managers.config_manager import ConfigManager

DateScope = namedtuple("DateScope", "begin, end")

class EmailConnector(QObject):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)  # Nueva señal
    current_directory = os.path.dirname(os.path.abspath(__file__))
    root_directory = os.path.abspath(os.path.join(current_directory, '..', '..'))
    config = {}

    def __init__(self, email: str, password: str, invoice_retrieval_window, provider='gmail'):
        super().__init__()
        
        invoice_retrieval_window = invoice_retrieval_window

        # Validar email y contraseña
        if not EmailUtils.validate_email_and_password(email, password):
            print("Correo electrónico o contraseña inválidos")
            return None
        
        imap_servers_file = os.path.join(self.root_directory, 'json', 'imap_servers.json')
        imap_servers = load_imap_servers(imap_servers_file)

        config_file = os.path.join(self.root_directory, 'json', 'config.json')
        config_manager = ConfigManager(config_file)
        self.config = config_manager.config

        if provider not in imap_servers:
            print(f"Unsupported email provider: {provider}")
            return None

        self.mail_server = imap_servers[provider]
        self.email = email
        self.password = password

        self.initialize_error_log_file()

    def initialize_error_log_file(self):
        """Create empty error log file"""
        # Create file if it doesn't exist
        if not os.path.isfile(self.config["FILE_LOGS"]):
            open(self.config["FILE_LOGS"], "w").close()

        # Make it empty otherwise
        else:
            with open(self.config["FILE_LOGS"], "w") as err_file:
                err_file.write("")

    def log_connection_errors(self, subject: str, date:str, message):
        """Save email erros into a file to inspect errors later on."""
        header = "".join([5*'-', subject, " ", date, 5*'-', "\n"])
        
        with open(self.config["FILE_LOGS"], "a") as error_file:
            error_file.write(header)
            error_file.write(message)
            error_file.write("\n\n")

    def retrieve_attachments_from_month(self, dateStart: str, dateEnd: str):
        try:
            self.status_updated.emit("Conectando al servidor de correo...")
            email_utils = EmailUtils("%d/%m/%Y", "%Y-%m-%d")
            date_start_formatted = email_utils.convert(dateStart)
            date_end_formatted = email_utils.convert(dateEnd)
            with Imbox(self.mail_server,
                    username=self.email,
                    password=self.password,
                    ssl=True,
                    ssl_context=None,
                    starttls=False) as imbox:
                inbox_messages_received_in_a_month = list(imbox.messages(date__gt=date_start_formatted,
                                                                    date__lt=date_end_formatted))
                total_emails = len(inbox_messages_received_in_a_month)
                processed_emails = 0
                for uid, message in inbox_messages_received_in_a_month:
                    # Crear un objeto de mensaje de correo electrónico multipart
                    email_msg = MIMEMultipart()
                    email_msg['Subject'] = message.subject
                    email_msg['From'] = message.sent_from[0]["email"]
                    email_msg['To'] = ", ".join([recipient["email"] for recipient in message.sent_to])

                    # Añadir el cuerpo del mensaje al correo electrónico
                    email_body_content = email_utils.get_email_body_content(message.body)
                    email_body = MIMEText(email_body_content)
                    email_msg.attach(email_body)
                    # Añadir los archivos adjuntos al correo electrónico
                    for attachment in message.attachments:
                        filename = attachment.get('filename')
                        content = attachment.get('content')
                        mime_type, _ = mimetypes.guess_type(filename)

                        if mime_type is None:
                            mime_type = "application/octet-stream"

                        attached_file = MIMEApplication(content.read(), _subtype=mime_type.split('/')[-1])
                        attached_file.add_header('Content-Disposition', 'attachment', filename=filename)
                        email_msg.attach(attached_file)

                    # Guardar el correo electrónico en formato .eml
                    message_date = email_utils.convert_date(message.date, "%Y-%m-%d_%H-%M-%S")
                    #message_date = email_utils.convert_date(message.date, input_format="%Y-%m-%d", output_format="%Y-%m-%d_%H-%M-%S")
                    email_filename = email_utils.sanitize_filename(f"{message.subject}_{message_date}.eml")
                    download_path = os.path.join(self.config['PATH_EMAILS_EML'] , email_filename)
                    with open(download_path, "wb") as fp:
                        fp.write(email_msg.as_bytes())

                    processed_emails += 1
                    progress = int((processed_emails / total_emails) * 100)
                    self.progress_updated.emit(progress)
                    self.status_updated.emit("Correos descargados")
        except Exception as e:
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Critical)
            message_box.setText("Error en la conexión con el servidor de correo electrónico")
            message_box.setInformativeText(str(e))
            message_box.setWindowTitle("Error")
            message_box.exec_()

class EmailConnectorThread(QThread):
    status_updated = pyqtSignal(str)  # Nueva señal
    def __init__(self, email_connector, date_start, date_end):
        super().__init__()
        self.email_connector = email_connector
        self.date_start = date_start
        self.date_end = date_end

    def run(self):
        self.email_connector.retrieve_attachments_from_month(self.date_start, self.date_end)

def load_imap_servers(filename):
    with open(filename, 'r') as file:
         imap_servers = json.load(file)
    return imap_servers
