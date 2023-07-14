from email import message_from_string
import re

class TextExtractor:
    """
    Esta clase se encarga de extraer el cuerpo del texto de un correo electrónico en formato raw.
    """
    def __init__(self, text_processor):
        self.text_processor = text_processor
   
    def extract_email_body(raw_email):
        # Divide el correo electrónico en segmentos con "From:", luego invierte la lista para empezar con el segmento más reciente
        split_emails = re.split("(?i)From:", raw_email)[::-1]
        email_body = None

        # Recorre cada segmento de correo electrónico comenzando desde el más reciente
        for email in split_emails:
            # Agrega "From:" al inicio de cada segmento a menos que sea el primer segmento (el original)
            email_str = "From:" + email if email != split_emails[-1] else email
            # Convierte el string de correo electrónico en un objeto de mensaje de correo electrónico
            email_message = message_from_string(email_str)

            # Verifica si el correo electrónico es multipart/alternativo (tiene partes como texto plano y HTML)
            if email_message.is_multipart():
                # Recorre cada parte del correo electrónico
                for part in email_message.walk():
                    # Si la parte es de texto plano, extrae el cuerpo del correo electrónico
                    if part.get_content_type() == "text/plain":
                        body_bytes = part.get_payload(decode=True)
                        body = body_bytes.decode('utf-8', errors='ignore')
                        # Solo considera el cuerpo del correo electrónico si tiene más de 10 palabras
                        if len(body.split()) > 10:
                            email_body = body
                            break
            else:
                # Si el correo electrónico no es multipart/alternativo, extrae el cuerpo del correo electrónico directamente
                body_bytes = email_message.get_payload(decode=True)
                body = body_bytes.decode('utf-8', errors='ignore')
                # Solo considera el cuerpo del correo electrónico si tiene más de 10 palabras
                if len(body.split()) > 10:
                    email_body = body

            # Si ya hemos encontrado un cuerpo de correo electrónico adecuado, salimos del ciclo
            if email_body:
                break
        
        # Si encontramos un cuerpo de correo electrónico adecuado, eliminamos las líneas que comienzan con "From:", "Sent:", "To:", "Subject:"
        if email_body:
            email_body = re.sub("From:.*\n", "", email_body)
            email_body = re.sub("Sent:.*\n", "", email_body)
            email_body = re.sub("To:.*\n", "", email_body)

            # Aplica transformaciones adicionales para el formato de Excel
            cleaned_body = re.sub(r'\n\s*\n', '\n', email_body)
            cleaned_body = re.sub(r'\s{2,}', ' ', cleaned_body)
            cleaned_body = re.sub(r'[ ]{2,}', ' ', cleaned_body)
            cleaned_body = re.sub(r'http\S+', '', cleaned_body)
            cleaned_body = re.sub(r'\S+@\S+', '', cleaned_body)
            cleaned_body = re.sub(r'\([^)]*\)', '', cleaned_body)

            # Eliminar caracteres no permitidos en Excel
            pattern = r'[^\x20-\x7E]'
            cleaned_body = re.sub(pattern, '', cleaned_body)

            email_body = cleaned_body

        # Si no encontramos un cuerpo de correo electrónico adecuado, nos quedamos con el correo electrónico original
        else:
            email_body = raw_email
        
        return email_body
    
    def extract_email_body_old(raw_email):
        split_emails = raw_email.split("From:")
        if len(split_emails) < 2:
            return raw_email

        email_str = "From:" + split_emails[1]
        email = message_from_string(email_str)

        body = ""
        if email.is_multipart():
            for part in email.walk():
                if part.get_content_type() == "text/plain":
                    body_bytes = part.get_payload(decode=True)
                    body = body_bytes.decode('utf-8', errors='ignore')
        else:
            body_bytes = email.get_payload(decode=True)
            body = body_bytes.decode('utf-8', errors='ignore')

        cleaned_body = re.sub(r'\n\s*\n', '\n', body)
        cleaned_body = re.sub(r'\s{2,}', ' ', cleaned_body)
        cleaned_body = re.sub(r'[ ]{2,}', ' ', cleaned_body)
        cleaned_body = re.sub(r'http\S+', '', cleaned_body)
        cleaned_body = re.sub(r'\S+@\S+', '', cleaned_body)
        cleaned_body = re.sub(r'\([^)]*\)', '', cleaned_body)

        # Eliminar caracteres no permitidos en Excel
        pattern = r'[^\x20-\x7E]'
        cleaned_body = re.sub(pattern, '', cleaned_body)

        return cleaned_body