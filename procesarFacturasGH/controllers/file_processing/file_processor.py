import pytesseract
import extract_msg
import pdfplumber
import os
import tempfile
import fitz
from docx import Document
from docx2pdf import convert
import win32com.client as win32
import mimetypes

from PIL import Image
from io import BytesIO

from email import policy
from email.parser import BytesParser

class FileProcessor:

    def __init__(self, config, translations, text_processor):
        self.config = config  # Configuración
        self.text_processor = text_processor  # Procesador de texto
        pytesseract.pytesseract.tesseract_cmd = self.config['tesseract_path']  # Ruta de Tesseract

    def extract_text_from_pdf(self, doc):
        extracted_texts = []

        for i in range(len(doc)):
            page = doc[i]

            # Extraer texto del contenido de la página
            page_text = page.get_text()

            # Extraer texto de las imágenes
            pixmap = page.get_pixmap()
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            
            # Si la imagen no es pequeña (por ejemplo, ancho y alto mayores que un cierto umbral)
            # if image.width > 500 and image.height > 500:  
            image = self.upscale_image(image)
            image_text = pytesseract.image_to_string(image)
            # Combinar texto de las imágenes y del contenido de la página
            combined_text = image_text + page_text
            extracted_texts.append(combined_text)
            #else:
            # Si la imagen es pequeña, solo agregamos el texto de la página
            extracted_texts.append(page_text)

        return extracted_texts

    def extract_text_from_image(self, image):
        text = pytesseract.image_to_string(image)

        # Solo devuelve el texto si contiene más de 10 palabras
        if len(text.split()) > 10:
            return text
        else:
            return ""
        
    def upscale_image(self, image, scale_factor=2):
        new_size = (image.width * scale_factor, image.height * scale_factor)
        return image.resize(new_size, Image.BICUBIC)

    def process_msg_file(self, file_path):
        msg = extract_msg.Message(file_path)
        msg_subject = msg.subject
        msg_body = msg.body
        attachments = msg.attachments

        email_contents = []

        for i, part in enumerate(attachments, start=1):  # Ahora tenemos un contador para cada adjunto
            email_content = None
            content_type = part.mimetype
            if content_type is None:
                if part.longFilename is not None:
                    content_type, _ = mimetypes.guess_type(part.longFilename)
                else:
                    # Manejar el caso cuando part.longFilename es None
                    content_type = 'application/octet-stream'

            payload = part.data

            if content_type is not None:
                if content_type.startswith("image/") or content_type == "application/pdf" or content_type == "application/msword" or content_type == "application/octet-stream":
                    filename, file_extension = os.path.splitext(part.longFilename)

                    if content_type == "application/pdf" or file_extension == '.pdf':
                        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                            temp_file.write(payload)
                            temp_file_path = temp_file.name

                        try:
                            with fitz.open(temp_file_path) as doc:
                                extracted_texts = self.extract_text_from_pdf(doc)
                                email_content = 'Email Attachment {}: \n{}'.format(i, '\n'.join(extracted_texts))  # Agregamos el encabezado aquí
                                email_contents.append(email_content)
                        except Exception as e:
                            print(f"Error opening file with fitz: {e}")

                        os.remove(temp_file_path)

                    elif content_type.startswith("image/"):
                        email_content = self.process_image(payload)
                        if email_content and len(email_content.split()) > 1:
                            email_contents.append(email_content)

                    elif content_type == "application/msword" or file_extension == '.doc':
                        with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as temp_file:
                            temp_file.write(payload)
                            temp_file_path = temp_file.name

                        docx_temp_file_path = temp_file_path + ".docx"
                        doc = win32.gencache.EnsureDispatch("Word.Application")
                        doc = doc.Documents.Open(temp_file_path)
                        doc.SaveAs(docx_temp_file_path, 16)
                        doc.Close()

                        docx = Document(docx_temp_file_path)

                        extracted_texts = []
                        for element in docx.element.body:
                            if element.tag.endswith('p'):
                                for paragraph in element:
                                    if paragraph.text:
                                        extracted_texts.append(paragraph.text)
                            elif element.tag.endswith('tbl'):
                                for table in element:
                                    for row in table:
                                        for cell in row:
                                            if cell.text:
                                                extracted_texts.append(cell.text)

                        email_content = 'Email Attachment {}: \n{}'.format(i, '\n'.join(extracted_texts))  # Agregamos el encabezado aquí
                        email_contents.append(email_content)

                        os.remove(temp_file_path)
                        os.remove(docx_temp_file_path)

        combined_email_contents = '\n'.join(email_contents)

        return msg_subject, msg_body, combined_email_contents

        
    def process_image(self, payload):
        with BytesIO(payload) as image_data:
            with Image.open(image_data) as img:
                text = pytesseract.image_to_string(img, config='--psm 6')
        return text

    def process_eml_file(self, file_path):
        with open(file_path, 'rb') as f:  
            msg = BytesParser(policy=policy.default).parse(f)
        msg_subject = msg['subject']
        msg_body = msg.get_body(preferencelist=('plain')).get_content()
        attachments = [part for part in msg.iter_parts() if part.is_attachment()]  # Obtén todas las partes que son adjuntos

        email_contents = []

        for part in attachments: 
            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)

            if content_type is not None:
                # procesar si el contenido comienza con image/, es un pdf o es un stream octet 
                if content_type.startswith("image/") or content_type == "application/pdf" or content_type == "application/octet-stream":
                    # Obtenemos la extensión del archivo
                    filename = part.get_filename()
                    if filename:
                        file_extension = os.path.splitext(filename)[1]

                    # Si el contenido es un pdf o la extensión del archivo es .pdf
                    if content_type == "application/pdf" or (filename and file_extension == '.pdf'):
                        with BytesIO(payload) as pdf_data:
                            with pdfplumber.open(pdf_data) as pdf:
                                page_texts = []
                                for page in pdf.pages:
                                    text = page.extract_text()
                                    page_texts.append(text)
                            email_content = '\n'.join(page_texts)
                            email_contents.append(email_content)
                    elif content_type.startswith("image/"):
                        with BytesIO(payload) as image_data:
                            with Image.open(image_data) as img:
                                content = self.process_image(img)
                                email_contents.append(content)

        combined_email_contents = '\n'.join(email_contents)

        return msg_subject, msg_body, combined_email_contents
    
    def process_msg_file_disk(self, file_path):
        msg = extract_msg.Message(file_path)  # Extrae el mensaje del archivo
        msg_subject = msg.subject  # Asunto del mensaje
        msg_body = msg.body  # Cuerpo del mensaje
        email_contents = []  # Contenidos del correo electrónico

        for attachment in msg.attachments:  # Para cada adjunto en los adjuntos del mensaje
            filename = attachment.longFilename  # Nombre largo del adjunto
            file_extension = os.path.splitext(filename)[1].lower()  # Extensión del archivo del adjunto
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)  # Archivo temporal
            temp_file.write(attachment.data)  # Escribe los datos del adjunto en el archivo temporal
            temp_file.close()  # Cierra el archivo temporal

            if file_extension == '.pdf':  # Si la extensión del archivo es .pdf
                with pdfplumber.open(temp_file.name) as pdf:  # Abre el archivo temporal con pdfplumber
                    page_texts = []  # Textos de las páginas
                    for page in pdf.pages:  # Para cada página en las páginas del PDF
                        text = page.extract_text()  # Extrae el texto de la página
                        cleaned_text = self.text_processor.clean_invoice_text(text)  # Limpia el texto de la factura
                        page_texts.append(cleaned_text)  # Añade el texto limpio a los textos de las páginas
                email_content = '\n'.join(page_texts)  # Contenido del correo electrónico
                email_contents.append(email_content)  # Añade el contenido del correo electrónico a los contenidos del correo electrónico
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:  # Si la extensión del archivo es una imagen
                with Image.open(temp_file.name) as img:  # Abre el archivo temporal con Image
                    content = self.file_processor.process_image(img)  # Procesa la imagen
                    cleaned_content = [self.text_processor.clean_invoice_text(text) for text in content]  # Limpia el contenido
                    email_content = '\n'.join(cleaned_content)  # Contenido del correo electrónico
                    email_contents.append(email_content)  # Añade el contenido del correo electrónico a los contenidos del correo electrónico
                    
            os.remove(temp_file.name)  # Elimina el archivo temporal

        combined_email_contents = '\n'.join(email_contents)  # Contenidos del correo electrónico combinados
        return msg_subject, msg_body, combined_email_contents
    
    @staticmethod
    def download_attachments(file_path, download_folder):
        if file_path.endswith('.msg'):  # Si el archivo termina en .msg
            msg = extract_msg.Message(file_path)  # Extrae el mensaje del archivo
            attachments = msg.attachments  # Adjuntos del mensaje
        elif file_path.endswith('.eml'):  # Si el archivo termina en .eml
            with open(file_path, 'rb') as f:  # Abre el archivo en modo de lectura binaria
                msg = BytesParser(policy=policy.default).parse(f)  # Parsea el mensaje
            attachments = [part for part in msg.walk() if part.get_content_maintype() == 'image' or part.get_content_type() == 'application/pdf']  # Adjuntos del mensaje
        else:
            print(f"Unknown file type: {file_path}")  # Imprime el tipo de archivo desconocido
            return

        for part in attachments:  # Para cada parte en los adjuntos
            try:
                if file_path.endswith('.msg'):  # Si el archivo termina en .msg
                    payload = part.data  # Carga útil de la parte
                    filename = part.longFilename or part.shortFilename  # Nombre largo o corto de la parte
                else: # file_path.endswith('.eml')
                    payload = part.get_payload(decode=True)  # Carga útil de la parte
                    if part.get_content_maintype() == 'multipart':  # Si el tipo de contenido principal de la parte es 'multipart'
                        print("Skipping multipart message.")  # Imprime "Saltando mensaje multipart."
                    else:
                        filename = part.get_filename()  # Obtiene el nombre del archivo de la parte
                        if filename:  # Si el adjunto tiene un nombre de archivo
                            # Comprobar si el archivo tiene una extensión
                            if not os.path.splitext(filename)[1]:
                                print(f"Skipping file without extension: {filename}")  # Imprime "Saltando archivo sin extensión: {filename}"
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

                    with open(os.path.join(download_folder, filename), 'wb') as f:  # Abre el archivo en modo de escritura binaria
                        f.write(payload)  # Escribe la carga útil en el archivo
            except Exception as e:
                print(f"Error processing part with filename {filename}: {e}")  # Imprime el error al procesar la parte con el nombre del archivo
