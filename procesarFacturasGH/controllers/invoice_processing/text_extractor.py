from email import message_from_string
import re

class TextExtractor:
    def __init__(self, text_processor):
        self.text_processor = text_processor
   
    @staticmethod
    def extract_email_body_old(raw_email):
        if "From:" not in raw_email:
            return raw_email

        # Divide el correo electrónico por las líneas "From:"
        split_emails = raw_email.split("From:")

        # El primer correo electrónico en la lista debería ser el más reciente
        most_recent_email_str = "From:" + split_emails[1]

        email = message_from_string(most_recent_email_str)

        body = ""
        if email.is_multipart():
            for part in email.walk():
                if part.get_content_type() == "text/plain":
                    # Get the payload and decode it to string
                    body_bytes = part.get_payload(decode=True)
                    body = body_bytes.decode('utf-8', errors='ignore')
        else:
            # Get the payload and decode it to string
            body_bytes = email.get_payload(decode=True)
            body = body_bytes.decode('utf-8', errors='ignore')

        # Clean the body
        cleaned_body = re.sub(r'\n\s*\n', '\n', body)
        cleaned_body = re.sub(r'\s{2,}', ' ', cleaned_body)
        cleaned_body = re.sub(r'[ ]{2,}', ' ', cleaned_body)
        cleaned_body = re.sub(r'http\S+', '', cleaned_body)
        cleaned_body = re.sub(r'\S+@\S+', '', cleaned_body)
        cleaned_body = re.sub(r'\([^)]*\)', '', cleaned_body)
        # Eliminar caracteres no permitidos en Excel
        pattern = r'[^\x20-\x7E]'
        cleaned_body = re.sub(pattern, '', cleaned_body)

        # Check if the cleaned body contains any non-whitespace characters
        if re.search(r'\S', cleaned_body):
            return cleaned_body

        # If no significant bodies found, return the original text
        return raw_email

    def extract_email_body(raw_email):
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