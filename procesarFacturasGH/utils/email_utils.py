import re

from datetime import datetime
from dateutil.parser import parse

from bs4 import BeautifulSoup

class EmailUtils:
    def __init__(self, input_format: str, output_format: str):
        self.input_format = input_format
        self.output_format = output_format

    def convert(self, date_string: str):
        date_obj = datetime.strptime(date_string, self.input_format)
        return date_obj.date()  # Devuelve un objeto de fecha en lugar de una cadena de texto

    def get_email_body_content(self, message_body):
        if isinstance(message_body, str):
            return message_body
        elif isinstance(message_body, dict):
            plain_text = message_body.get("plain", None)
            html_text = message_body.get("html", None)

            # Prioriza el texto sin formato, si está disponible, de lo contrario, utiliza el texto HTML
            if plain_text:
                return plain_text[0] if plain_text else ""
            elif html_text:
                return html_text[0] if html_text else ""
            else:
                return ""
        else:
            return ""
    
    def convert_date(self, date_string, output_format):
        date_obj = parse(date_string)
        return date_obj.strftime(output_format)
    
    def convert_html_to_plain_text(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text()
    
    @staticmethod
    def sanitize_filename(filename):
        invalid_chars = r'[<>:"/\\|?*]'
        return re.sub(invalid_chars, '_', filename)
    
    @staticmethod
    def validate_email_and_password(email, password):
        if not email or not password:
            return False
        return True