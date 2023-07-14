import json
import re
import dateutil.parser

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy
from controllers.invoice_processing.text_extractor import TextExtractor
from utils.utils import Utils
from langdetect import detect

nlp = spacy.load('en_core_web_sm')

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
        language = self.detect_language(email)
        categories_prompt = ', '.join([f'"{cat}"' for cat in categories[language]])
        if language == 'en':
            prompt = f"Please classify this email into one of the following categories: {categories_prompt} or other. The email says:"
        else:
            prompt = f"Por favor clasifica este correo electrónico en una de las siguientes categorías: {categories_prompt} u otro. El correo electrónico dice:"
        prompt_result = prompt + " " + email
        max_tokens = Utils.get_dynamic_max_tokens(prompt  + " " +  email , 0.1)

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

    #
    # FORMATO JSON
    #
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

    def load_jsons(self,fixed_json_text,json_text_clean ):
        try:
            json.loads(fixed_json_text)
        except json.JSONDecodeError:
            return json_text_clean
        return fixed_json_text
    
    def clean_text_before_json(self, text):
        text = text.replace("\n", " ").replace('\\"', '"')
        text = text.replace("N/A", '""').replace('"null"', '""').replace('null', '""')
        text = text.replace("'", "\"")
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


    #
    # LIMPIAR MARCAS DE AGUA Y HEADERS EN ADJUNTOS
    #
    def remove_paragraphs(self, text, min_length):
        doc = nlp(text)
        cleaned_text = ''
        
        for sent in doc.sents:
            # Si la sentencia tiene menos de min_length palabras, añádela al texto limpio
            if len(sent) < min_length:
                cleaned_text += sent.text + ' '
        return cleaned_text

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
        text = TextProcessor.remove_header_footer(text)
        return text

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
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        # Eliminar correos electrónicos
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
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
        # Limpiamos los objetos de los adjuntos primero
        extracted_content = self.clean_objects_attachment(content)

        # Creamos el texto crudo y aplicamos separacion de contenido
        raw_text = "Subject Email: " + subject
        if body.strip():
            raw_text += "\n\nBody Email: " + body
        if extracted_content.strip():
            raw_text += "\n\nAttachments Email: " + extracted_content

        # Limpiamos parrafos de los adjuntos 40 palabras el promedio de un parrafo
        extracted_content = self.remove_paragraphs(extracted_content, 40)

        # Texto extraído 
        extracted_text = "Subject Email: " + subject
        extracted_body = TextExtractor.extract_email_body(body)
        if extracted_body.strip():
            extracted_text +=  extracted_body
        if extracted_content.strip():
            extracted_text += extracted_content 

        # Texto limpio con separacion de contenido
        clean_text = "Subject Email: " + self.clean_text(subject)
        clean_body = self.clean_text(body)
        clean_content = self.clean_text(extracted_content)
        if clean_body.strip():
            clean_text += "\n\nBody Email: " + clean_body
        if clean_content.strip():
            clean_text += "\n\nAttachments Email: " + clean_content

        # Texto extraido y limpio con separacion de contenido
        clean_extracted_text = "Subject Email: " + self.clean_text(subject)
        clean_extracted_body = self.clean_text(extracted_body)
        clean_extracted_content = self.clean_text(extracted_content)
        if clean_extracted_body.strip():
            clean_extracted_text += "\n\nBody Email: " + clean_extracted_body
        if clean_extracted_content.strip():
            clean_extracted_text += "\n\nAttachments Email: " + clean_extracted_content

        return raw_text, clean_text, clean_extracted_text

    def extract_and_clean_text(self, subject, body, content, type_content):
        if type_content == "body":
            return self.process_body(subject, body, content)
        elif type_content == "content":
            return self.process_content(subject, content)
        elif type_content == "combined":
            return self.process_combined(subject, body, content)
        else:
            raise ValueError(f"Unrecognized content type: {type_content}")
    
    def clean_prompt(self, prompt):
        cleaned_prompt = prompt.replace('\n', ' ').replace('\r', '')
        cleaned_prompt = ' '.join(cleaned_prompt.split())
        return cleaned_prompt  


    @staticmethod
    def generate_email_subject_code(email_subject):
        # Tomar las primeras palabras del asunto y unirlas
        words = email_subject.split()[:4]
        code = "".join(words)

        # Limitar el código a 10 caracteres
        return code[:20]
