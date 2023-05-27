import json
import re
import dateutil.parser
import email
#import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
from controllers.invoice_processing.text_extractor import TextExtractor
from utils.utils import Utils

#nltk.download('punkt')
#nltk.download('wordnet')
#nltk.download('stopwords')

from langdetect import detect
from sklearn.feature_extraction.text import CountVectorizer

class TextProcessor:   
    def __init__(self,  translations):
        self.translations = translations

    #
    # SPLIT TEXTO
    #
    def split_text_into_segments(self, text, segment_length):
        segments = []
        for i in range(0, len(text), segment_length):
            segment = text[i:i+segment_length]
            if segment not in segments:
                segments.append(segment)
        return segments


    def get_prompt_categories(self, email, categories):

        # Detecta el idioma del correo electrónico
        language = self.detect_language(email)

        # Construye un prompt con las categorías en el idioma detectado
        categories_prompt = ', '.join([f'"{cat}"' for cat in categories[language].values()])
        if language == 'en':
            prompt = f"Please classify this email into one of the following categories: {categories_prompt} or something else. The email says:"
        else:
            prompt = f"Por favor clasifica este correo electrónico en una de las siguientes categorías: {categories_prompt} o algo más. El correo electrónico dice:"

        # Calcula el número de tokens para la respuesta
        prompt_result = prompt + " " + email
        max_tokens = Utils.get_dynamic_max_tokens(prompt  + " " +  email,0.1)

        return max_tokens , language , prompt_result 

    #
    # MANEJO DE FECHAS
    #
    @staticmethod
    def is_date(value):
        if not isinstance(value, str):
            return False

        try:
            dateutil.parser.parse(value)
            return True
        except ValueError:
            return False
        
    @staticmethod
    def homologate_date(value):
        parsed_date = dateutil.parser.parse(value)
        return parsed_date.strftime('%d/%m/%Y')

    #
    # DETECTAR LENGUAJE
    #
    def detect_language(self, text, full_name=False):
        try:
            detected_language = detect(text)
            if detected_language == 'es' or detected_language == 'en':
                if full_name:
                    language_full_name = {
                        'en': 'english',
                        'es': 'spanish',
                    }.get(detected_language, 'english') 
                    return language_full_name
                else:
                    return detected_language
            else:
                return 'english' if full_name else 'en'
        except:
            return 'english' if full_name else 'en'

    #
    # CONSOLIDAR DATA
    #
    def consolidate_invoice_data(self, header_invoice_data, detail_invoice_data):
        consolidated_data = {}

        # Consolidate header data
        for key, value in header_invoice_data.items():
            if self.is_date(value):
                value = self.homologate_date(value)

            if key not in consolidated_data or not consolidated_data[key]:
                consolidated_data[key] = value
            elif value:
                if key in ["Confidence", "total", "subtotal"]:
                    consolidated_data[key] = max(consolidated_data[key], value)
                else:
                    consolidated_data[key] = value

        # Consolidate detail data
        consolidated_data["Detail"] = []
        for detail_item in detail_invoice_data:
            if isinstance(detail_item, dict):  # verificar si detail_item es un diccionario
                consolidated_item = {}
                for key, value in detail_item.items():
                    if self.is_date(value):
                        value = self.homologate_date(value)

                    if key not in consolidated_item or not consolidated_item[key]:
                        consolidated_item[key] = value
                    elif value:
                        if key in ["Confidence", "Price", "Amount"]:
                            consolidated_item[key] = max(consolidated_item[key], value)
                        else:
                            consolidated_item[key] = value
                consolidated_data["Detail"].append(consolidated_item)
        return consolidated_data
       
    def is_valid_json(self, json_string):
        try:
            if json_string is None:
                return False

            if json_string.strip().startswith("{") and json_string.strip().endswith("}"):
                json_string = "[" + json_string + "]"
            elif not (json_string.strip().startswith("[") and json_string.strip().endswith("]")):
                # Si no es un objeto JSON ni una lista JSON válida, devuelve False
                return False

            json_obj = json.loads(json_string)
            return isinstance(json_obj, list) and all(isinstance(item, dict) for item in json_obj)
        except ValueError as e:
            print("Error al validar JSON:", e)
            return False
    #
    # FORMATO JSON
    #
    def clean_text_before_json_old(self, text):
        text = text.replace("\n", " ")
        text = text.replace('\\"', '"')
        text = text.replace("N/A", '""') 
        text = text.replace('"null"', '""')
        text = text.replace('null', '""')

        while len(text) > 0 and not (text[0].isalnum() or text[0] == "{" or text[0] == "["):
            text = text[1:]

        start_idx = text.find("{")
        if text[start_idx-1] == "[":
            start_idx = start_idx - 1
        if start_idx == -1:
            start_idx = text.find("[")
            if start_idx == -1:
                return text
        text = text[start_idx:]
        if text[0] == "{":
            text = "[" + text + "]"

        last_two_chars = text[-2:]
        compressed_chars = "".join(last_two_chars.split())       
        if compressed_chars == ']]':
            text = text[:-1]

        return text

    def clean_text_before_json(self, text):
        text = text.replace("\n", " ").replace('\\"', '"')
        text = text.replace("N/A", '""').replace('"null"', '""').replace('null', '""')

        while len(text) > 0 and not (text[0].isalnum() or text[0] in "{["):
            text = text[1:]

        start_idx = text.find("{")
        if start_idx == -1 or (start_idx > 0 and text[start_idx-1] == "["):
            start_idx -= 1
        if start_idx == -1:
            start_idx = text.find("[")
        if start_idx == -1:
            return text
        text = text[start_idx:]

        if text[0] == "{":
            text = "[" + text + "]"
        if "".join(text[-2:].split()) == ']]':
            text = text[:-1]

        return text

    def fix_invalid_json(self, json_string):
        # Reemplaza los casos de números entre comillas con espacios
        json_string = re.sub(r'"\s*(\d+)', r'\1', json_string)
        json_string = re.sub(r'(\d+)\s*"', r'\1', json_string)
        
        # Encuentra todos los casos donde el valor no está entre comillas
        json_string = re.sub(r',\s*}', '}', json_string)

        # Encuentra todos los valores de cadena
        pattern = re.compile(r'"[^"]*"')
        matches = pattern.findall(json_string)

        # Para cada coincidencia, escapar las comillas dobles dentro de las cadenas
        for match in matches:
            # Quita las comillas dobles del principio y del final
            stripped_match = match[1:-1]
            # Escapa las comillas dobles que quedan
            escaped_match = stripped_match.replace('"', '\\"')
            # Reemplaza la coincidencia en la cadena JSON
            json_string = json_string.replace(stripped_match, escaped_match)

        # Elimina las comillas dobles anidadas
        json_string = self.remove_nested_quotes(json_string)

        # Encuentra todos los casos donde el valor no está entre comillas
        pattern = re.compile(r':\s*([^"\s\]\},]+)')
        matches = pattern.findall(json_string)

        # Para cada coincidencia, comprueba si es un número, true, false, null. Si no, lo pone entre comillas
        for match in matches:
            if f'"{match}"' not in json_string:  # comprueba si la coincidencia ya está entre comillas
                try:
                    float(match)
                    if f": {match}" in json_string:
                        json_string = json_string.replace(f": {match}", f': "{match}"')
                except ValueError:
                    if match in ['true', 'false', 'null'] and f": {match}" in json_string:
                        json_string = json_string.replace(f": {match}", f': "{match}"')

        return json_string

    def remove_nested_quotes(self, text):
        result = ""
        quote_open = False
        for char in text:
            if char == '"':
                if not quote_open:
                    quote_open = True
                else:
                    quote_open = False
                result += char
            elif char != '"' or (char == '"' and text[result.rfind('"', 0, len(result) - 1):].find(':') == -1):
                result += char
        return result

    def fix_json(self, s):
        while True:
            try:
                result = json.loads(s)   # try to parse...
                return s
                break                    # parsing worked -> exit loop
            except Exception as e:
                # "Expecting , delimiter: line 34 column 54 (char 1158)"
                # position of unexpected character after '"'
                unexp = int(re.findall(r'\(char (\d+)\)', str(e))[0])
                # position of unescaped '"' before that
                unesc = s.rfind(r'"', 0, unexp)
                s = s[:unesc] + r'\"' + s[unesc+1:]
                # position of correspondig closing '"' (+2 for inserted '\')
                closg = s.find(r'"', unesc + 2)
                s = s[:closg] + r'\"' + s[closg+1:]
        return s


    #
    # LIMPIAR MARCAS DE AGUA Y HEADERS EN ADJUNTOS
    #
    @staticmethod
    def remove_watermark(text):
        watermark_pattern = re.compile(r'(\bWatermark\b)|(\bMarca de agua\b)', re.IGNORECASE)
        cleaned_text = re.sub(watermark_pattern, '', text)
        return cleaned_text

    @staticmethod
    def remove_header_footer(text):
        # Asume que los encabezados y pies de página están separados por líneas horizontales
        horizontal_line_pattern = re.compile(r'-{3,}|\*{3,}|_{3,}')
        sections = re.split(horizontal_line_pattern, text)
        if len(sections) > 1:
            cleaned_text = '\n'.join(sections[1:-1])
        else:
            cleaned_text = text
        return cleaned_text
      
    @staticmethod
    def clean_objects_attachment(text):
        text = TextProcessor.remove_watermark(text)
        text = TextProcessor.remove_header_footer(text)
        return text

    #
    # LIMPIAR TEXTO
    #
    def extract_first_email_body(self, text):
        #body = TextExtractor.extract_last_email_body(text)
        body = TextExtractor.extract_first_significant_email_body(text)
        signature_start = re.search(r'\S+@\S+|\d{2,}', body)
        if signature_start is not None:
            body = body[:signature_start.start()]
        return body

    def clean_text(self, text):
        # Eliminar caracteres no deseados como espacios en blanco adicionales, saltos de línea, etc.
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(r'[ ]{2,}', ' ', text)       
        # Eliminar URLs
        text = re.sub(r'http\S+', '', text)
        # Eliminar correos electrónicos
        text = re.sub(r'\S+@\S+', '', text)
        # Eliminar contenido entre paréntesis
        text = re.sub(r'\([^)]*\)', '', text)
        # Eliminar caracteres no permitidos en Excel
        pattern = r'[^\x20-\x7E]'
        text = re.sub(pattern, '', text)
        return text

    def process_content(self, subject, content):
        raw_text = subject
        if content.strip():
            raw_text += "\n\n" + content
        clean_text = self.clean_text(raw_text)
        cleaned_and_extracted_text = ""
        if clean_text.strip():
            cleaned_and_extracted_text = self.clean_objects_attachment(clean_text)
        return raw_text, clean_text, cleaned_and_extracted_text

    def process_body(self, subject, body):
        raw_text = subject
        if body.strip():
            raw_text += "\n\n" + body
        clean_text = self.clean_text(raw_text)
        cleaned_and_extracted_text = ""
        if clean_text.strip():
            cleaned_and_extracted_text = TextExtractor.extract_email_body(clean_text)
        return raw_text, clean_text, cleaned_and_extracted_text

    def process_combined(self, subject, body, content):
        extracted_content = self.clean_objects_attachment(content)
        # Texto Crudo
        raw_text = subject
        if body.strip():
            raw_text += "\n\n" + body
        if extracted_content.strip():
            raw_text += "\n\n" + extracted_content
        # Texto limipio
        clean_text = self.clean_text(raw_text)
        # Texto limipio y extraido
        extracted_body = TextExtractor.extract_email_body(body)
        text_extracted = subject
        if extracted_body.strip():
            text_extracted += "\n\n" + extracted_body
        if extracted_content.strip():
            text_extracted += "\n\n" + extracted_content 
        cleaned_and_extracted_text = self.clean_text(text_extracted)
        return raw_text, clean_text, cleaned_and_extracted_text

    def extract_and_clean_text(self, subject, body, content, type_content):
        if type_content == "body":
            return self.process_body(subject, body, content)
        elif type_content == "content":
            return self.process_content(subject, body, content)
        elif type_content == "combined":
            return self.process_combined(subject, body, content)
        else:
            raise ValueError(f"Unrecognized content type: {type_content}")
    
    def clean_prompt(self, prompt):
        cleaned_prompt = prompt.replace('\n', ' ').replace('\r', '')
        cleaned_prompt = ' '.join(cleaned_prompt.split())
        return cleaned_prompt  

    #
    # GENERADORES DE IDS Y CODIGOS
    #
    @staticmethod
    def generate_custom_id(config, email_subject, timestamp):
        id_parts = []

        # Añadir dos primeros caracteres del tipo de contenido
        content_type_code = config['type_content']
        id_parts.append(content_type_code)

        # Añadir el número de solicitudes máximas de OpenAI como string
        max_requests_code = str(config['max_nrquest_openai'])
        id_parts.append(max_requests_code)

        # Añadir la cantidad mínima de palabras clave como string
        min_key_count_code = str(config['minimum_key_count'])
        id_parts.append(min_key_count_code)

        # Añadir un código basado en el asunto del correo electrónico
        email_subject_code = TextProcessor.generate_email_subject_code(email_subject)
        id_parts.append(email_subject_code)

        # Añadir una representación numérica del timestamp
        timestamp_code = str(int(timestamp)).zfill(10)[-5:]
        id_parts.append(timestamp_code)

        # Unir las partes del ID y devolver el resultado
        custom_id = "-".join(id_parts)
        return custom_id

    @staticmethod
    def generate_email_subject_code(email_subject):
        # Tomar las primeras palabras del asunto y unirlas
        words = email_subject.split()[:4]
        code = "".join(words)

        # Limitar el código a 10 caracteres
        return code[:20]

