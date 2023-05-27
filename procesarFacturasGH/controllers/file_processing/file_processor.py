
import pytesseract
import extract_msg
import pdfplumber
import os
import tempfile

from PIL import Image
from io import BytesIO

from email import policy
from email.parser import BytesParser

class FileProcessor:
    def __init__(self, config, translations, text_processor):
        self.config = config
        self.text_processor = text_processor
        pytesseract.pytesseract.tesseract_cmd = self.config['tesseract_path']

    def process_image(self, image):
        text = pytesseract.image_to_string(image)
        return text

    def process_msg_file(self, file_path):
        msg = extract_msg.Message(file_path)
        msg_subject = msg.subject
        msg_body = msg.body
        attachments = msg.attachments

        email_contents = []

        for part in attachments:
            content_type = part.mimetype
            payload = part.data

            if content_type is not None:
                if content_type.startswith("image/") or content_type == "application/pdf":
                    if content_type == "application/pdf":
                        with BytesIO(payload) as pdf_data:
                            with pdfplumber.open(pdf_data) as pdf:
                                page_texts = []
                                for page in pdf.pages:
                                    text = page.extract_text()
                                    page_texts.append(text)
                            email_content = '\n'.join(page_texts)
                            email_contents.append(email_content)
                    else:  # Procesar como imagen
                        with BytesIO(payload) as image_data:
                            with Image.open(image_data) as img:
                                content = self.process_image(img)
                                email_contents.append(content)

        combined_email_contents = '\n'.join(email_contents)

        return msg_subject, msg_body, combined_email_contents

    def process_eml_file(self, file_path):
        with open(file_path, 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)
        msg_subject = msg['subject']
        msg_body = msg.get_body(preferencelist=('plain')).get_content()
        attachments = [part for part in msg.walk() if part.get_content_maintype() == 'image' or part.get_content_type() == 'application/pdf']

        email_contents = []

        for part in attachments:
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)

            if content_type is not None:
                if content_type.startswith("image/") or content_type == "application/pdf":
                    if content_type == "application/pdf":
                        with BytesIO(payload) as pdf_data:
                            with pdfplumber.open(pdf_data) as pdf:
                                page_texts = []
                                for page in pdf.pages:
                                    text = page.extract_text()
                                    page_texts.append(text)
                            email_content = '\n'.join(page_texts)
                            email_contents.append(email_content)
                    else:  # Procesar como imagen
                        with BytesIO(payload) as image_data:
                            with Image.open(image_data) as img:
                                content = self.process_image(img)
                                email_contents.append(content)

        combined_email_contents = '\n'.join(email_contents)

        return msg_subject, msg_body, combined_email_contents

    def process_msg_file_disk(self, file_path):
        msg = extract_msg.Message(file_path)
        msg_subject = msg.subject
        msg_body = msg.body
        email_contents = []

        for attachment in msg.attachments:
            filename = attachment.longFilename
            file_extension = os.path.splitext(filename)[1].lower()
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
            temp_file.write(attachment.data)
            temp_file.close()

            if file_extension == '.pdf':
                with pdfplumber.open(temp_file.name) as pdf:
                    page_texts = []
                    for page in pdf.pages:
                        text = page.extract_text()
                        cleaned_text = self.text_processor.clean_invoice_text(text)
                        page_texts.append(cleaned_text)
                email_content = '\n'.join(page_texts)
                email_contents.append(email_content)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                with Image.open(temp_file.name) as img:
                    content = self.file_processor.process_image(img)
                    cleaned_content = [self.text_processor.clean_invoice_text(text) for text in content]
                    email_content = '\n'.join(cleaned_content)
                    email_contents.append(email_content)
                    
            os.remove(temp_file.name)

        combined_email_contents = '\n'.join(email_contents)
        return msg_subject, msg_body, combined_email_contents
    
    @staticmethod
    def download_attachments(file_path, download_folder):
        if file_path.endswith('.msg'):
            msg = extract_msg.Message(file_path)
            attachments = msg.attachments
        elif file_path.endswith('.eml'):
            with open(file_path, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)
            attachments = [part for part in msg.walk() if part.get_content_maintype() == 'image' or part.get_content_type() == 'application/pdf']
        else:
            print(f"Unknown file type: {file_path}")
            return

        for part in attachments:
            try:
                if file_path.endswith('.msg'):
                    payload = part.data
                    filename = part.longFilename or part.shortFilename
                else: # file_path.endswith('.eml')
                    payload = part.get_payload(decode=True)
                    if part.get_content_maintype() == 'multipart':
                        print("Skipping multipart message.")
                    else:
                        filename = part.get_filename()
                        if filename:  # Si el adjunto tiene un nombre de archivo
                            # Comprobar si el archivo tiene una extensión
                            if not os.path.splitext(filename)[1]:
                                print(f"Skipping file without extension: {filename}")
                                continue

                            # Crear un directorio para guardar los archivos adjuntos si no existe
                            if not os.path.exists(download_folder):
                                os.makedirs(download_folder)
                            with open(os.path.join(download_folder, filename), 'wb') as f:
                                f.write(payload)

                if filename:  # Si el adjunto tiene un nombre de archivo
                    # Crear un directorio para guardar los archivos adjuntos si no existe
                    if not os.path.exists(download_folder):
                        os.makedirs(download_folder)

                    with open(os.path.join(download_folder, filename), 'wb') as f:
                        f.write(payload)
            except Exception as e:
                print(f"Error processing part with filename {filename}: {e}")


    @staticmethod
    def process_download(emails_folder, download_folder):
        files = os.listdir(emails_folder)
        files = [f for f in files if f.endswith('.msg') or f.endswith('.eml')]

        for i, msg_file in enumerate(files):
            file_path = os.path.join(emails_folder, msg_file)
            FileProcessor.download_attachments(file_path, download_folder)
            res = extract_data(os.path.join(path, file), self.templates)

