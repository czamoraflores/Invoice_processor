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
    progress_updated = pyqtSignal(int)  # Señal para actualizar el progreso
    status_updated = pyqtSignal(str)  # Señal para actualizar el estado
    current_directory = os.path.dirname(os.path.abspath(__file__))  # Directorio actual
    root_directory = os.path.abspath(os.path.join(current_directory, '..', '..'))  # Directorio raíz
    config = {}  # Configuración

    def __init__(self, invoice_retrieval_window):
        super().__init__()

        self.invoice_retrieval_window = invoice_retrieval_window  # Ventana de recuperación de facturas
        self.email = ""  # Correo electrónico
        self.password = ""  # Contraseña
        self.imap_server = ""  # Servidor IMAP

        file_imap_servers = os.path.join(self.root_directory, 'json', 'imap_servers.json')  # Archivo de servidores IMAP
        self.all_imap_servers = self.load_imap_servers(file_imap_servers)  # Carga todos los servidores IMAP

        config_file = os.path.join(self.root_directory, 'json', 'config.json')  # Archivo de configuración
        config_manager = ConfigManager(config_file)  # Gestor de configuración
        self.config = config_manager.config  # Configuración

        self.initialize_error_log_file()  # Inicializa el archivo de registro de errores

    def set_credentials(self, email: str, password: str):
        """Establece las credenciales de correo electrónico."""
        # Validar email y contraseña
        if not EmailUtils.validate_email_and_password(email, password):
            print("Correo electrónico o contraseña inválidos")
            return False

        self.email = email  # Establece el correo electrónico
        self.password = password  # Establece la contraseña
        return True

    def set_imap_server(self, provider: str):
        """Establece el servidor IMAP."""
        self.imap_server = self.all_imap_servers[provider]  # Establece el servidor IMAP

    def initialize_error_log_file(self):
        """Crea un archivo de registro de errores vacío"""
        # Crea el archivo si no existe
        if not os.path.isfile(self.config["FILE_LOGS"]):
            open(self.config["FILE_LOGS"], "w").close()

        # Si existe, lo vacía
        else:
            with open(self.config["FILE_LOGS"], "w") as err_file:
                err_file.write("")

    def log_connection_errors(self, subject: str, date:str, message):
        """Guarda los errores de correo electrónico en un archivo para inspeccionarlos más tarde."""
        header = "".join([5*'-', subject, " ", date, 5*'-', "\n"])
        
        with open(self.config["FILE_LOGS"], "a") as error_file:
            error_file.write(header)  # Escribe el encabezado
            error_file.write(message)  # Escribe el mensaje
            error_file.write("\n\n")  # Escribe dos saltos de línea

    def retrieve_attachments_from_month(self, dateStart: str, dateEnd: str):
        try:         
            if not self.imap_server or not self.email or not self.password:
                print(f"No se ha configurado el servidor de correo o las credenciales {self.imap_server}")
                return
            self.status_updated.emit("Conectando al servidor de correo...")  # Emite el estado```python
            email_utils = EmailUtils("%d/%m/%Y", "%Y-%m-%d")  # Utilidades de correo electrónico
            date_start_formatted = email_utils.convert(dateStart)  # Formatea la fecha de inicio
            date_end_formatted = email_utils.convert(dateEnd)  # Formatea la fecha de fin

            with Imbox(self.imap_server,
                    username=self.email,
                    password=self.password,
                    ssl=True,
                    ssl_context=None,
                    starttls=False) as imbox:
                
                inbox_messages_received_in_a_month = list(imbox.messages(date__gt=date_start_formatted,
                                                                    date__lt=date_end_formatted))  # Mensajes recibidos en un mes
                total_emails = len(inbox_messages_received_in_a_month)  # Total de correos electrónicos
                processed_emails = 0  # Correos electrónicos procesados
                for uid, message in inbox_messages_received_in_a_month:
                    # Crear un objeto de mensaje de correo electrónico multipart
                    email_msg = MIMEMultipart()
                    email_msg['Subject'] = message.subject  # Asunto del mensaje
                    email_msg['From'] = message.sent_from[0]["email"]  # Remitente del mensaje
                    email_msg['To'] = ", ".join([recipient["email"] for recipient in message.sent_to])  # Destinatarios del mensaje

                    # Añadir el cuerpo del mensaje al correo electrónico
                    email_body_content = email_utils.get_email_body_content(message.body)  # Contenido del cuerpo del mensaje
                    email_body = MIMEText(email_body_content)  # Cuerpo del mensaje
                    email_msg.attach(email_body)  # Adjunta el cuerpo del mensaje

                    # Añadir los archivos adjuntos al correo electrónico
                    for attachment in message.attachments:
                        filename = attachment.get('filename')  # Nombre del archivo adjunto
                        content = attachment.get('content')  # Contenido del archivo adjunto
                        mime_type, _ = mimetypes.guess_type(filename)  # Tipo MIME del archivo adjunto

                        if mime_type is None:
                            mime_type = "application/octet-stream"  # Tipo MIME por defecto

                        attached_file = MIMEApplication(content.read(), _subtype=mime_type.split('/')[-1])  # Archivo adjunto
                        attached_file.add_header('Content-Disposition', 'attachment', filename=filename)  # Añade el archivo adjunto
                        email_msg.attach(attached_file)  # Adjunta el archivo adjunto

                    # Guardar el correo electrónico en formato .eml
                    message_date = email_utils.convert_date(message.date, "%Y-%m-%d_%H-%M-%S")  # Fecha del mensaje
                    email_filename = email_utils.sanitize_filename(f"{message.subject}_{message_date}.eml")  # Nombre del archivo de correo electrónico
                    download_path = os.path.join(self.config['PATH_EMAILS_EML'] , email_filename)  # Ruta de descarga
                    with open(download_path, "wb") as fp:
                        fp.write(email_msg.as_bytes())  # Escribe el mensaje en bytes

                    processed_emails += 1  # Incrementa los correos electrónicos procesados
                    progress = int((processed_emails / total_emails) * 100)  # Progreso
                    self.progress_updated.emit(progress)  # Emite el progreso
                    self.status_updated.emit("Correos descargados")  # Emite el estado
        except Exception as e:
            message_box = QMessageBox()
            message_box.setIcon(QMessageBox.Critical)  # Icono crítico
            message_box.setText("Error en la conexión con el servidor de correo electrónico")  # Texto del mensaje
            message_box.setInformativeText(str(e))  # Texto informativo
            message_box.setWindowTitle("Error")  # Título de la ventana
            message_box.exec_()  # Ejecuta el cuadro de mensaje

    def load_imap_servers(self, filename):
        with open(filename, 'r') as file:
            all_imap_servers = json.load(file)  # Carga todos los servidores IMAP
        return all_imap_servers  # Devuelve todos los servidores IMAP

class EmailConnectorThread(QThread):
    status_updated = pyqtSignal(str)  # Señal para actualizar el estado
    def __init__(self, email_connector, date_start, date_end):
        super().__init__()
        self.email_connector = email_connector  # Conector de correo electrónico
        self.date_start = date_start  # Fecha de inicio
        self.date_end = date_end  # Fecha de fin

    def run(self):
        try:
            self.email_connector.retrieve_attachments_from_month(self.date_start, self.date_end)  # Recupera los adjuntos de un mes
        except Exception as e:
            print(f"Error en el hilo: {e}")  # Imprime el error

