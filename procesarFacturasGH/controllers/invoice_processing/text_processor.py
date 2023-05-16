import json
import re
import dateutil.parser
#import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer
#nltk.download('punkt')
#nltk.download('wordnet')
#nltk.download('stopwords')

from langdetect import detect
from sklearn.feature_extraction.text import CountVectorizer

class TextProcessor:   
    def __init__(self,  translations):
        self.translations = translations

    @staticmethod
    def split_text_into_segments(text, max_tokens):

        tokens = text.split()
        segments = []
        current_segment = []

        for token in tokens:
            current_segment.append(token)
            if len(" ".join(current_segment)) > max_tokens:
                segments.append(" ".join(current_segment[:-1]))
                current_segment = [token]

        if current_segment:
            segments.append(" ".join(current_segment))

        return segments

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

    def clean_invalid_json(self, json_string, max_attempts=10):
        for _ in range(max_attempts):
            try:
                json.loads(json_string)
                return json_string
            except json.JSONDecodeError as e:
                pos = int(re.findall(r'\(char (\d+)\)', str(e))[0])
                corrected_string = json_string[:pos] + '"' + json_string[pos:] if json_string[pos-1] != '"' else json_string
                json_string = corrected_string
        print(f"Could not correct JSON string after {max_attempts} attempts")
        print(f"Error position: {pos}")
        print(f"JSON string: {json_string}")
        raise ValueError("Could not correct JSON string after {} attempts".format(max_attempts))
           
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
    
    def clean_text_before_json(self, text):
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
        return text

    def complete_truncated_json(self, json_string):
        # Convierte el string a un objeto JSON
        try:
            json_obj = json.loads(json_string)
            # Si el JSON se carga correctamente y no está vacío, no hace nada
            if json_obj:
                return json_string
        except json.JSONDecodeError:
            # Si hay un error al convertir, probablemente el último objeto está truncado.
            pass

        # Encuentra el último objeto completo en la cadena JSON
        last_obj_end = json_string.rfind("}")

        # Intenta convertir el JSON truncado
        try:
            json_string = json_string[:last_obj_end+1]
            #if not json_string.endswith('"}'):
            #    json_string += '"'
            if not json_string.endswith('}]'):
                json_string += ']'
            json_obj = json.loads(json_string)
        except json.JSONDecodeError:
            # Si todavía existe un error, devuelve None
            return None

        # Verifica si json_obj es una lista y tiene al menos un objeto
        if isinstance(json_obj, list) and json_obj:
            # Obtiene los campos del primer objeto de la lista
            fields = list(json_obj[0].keys())

            # Determina cuál es el último campo válido en el objeto truncado
            last_field_match = re.search('"([^"]*)":', json_string[last_obj_end:])
            if last_field_match is not None:
                last_field = last_field_match.group(1)
                last_field_index = fields.index(last_field)
            else:
                # Si no se encontró ningún campo válido, asume que todos los campos están truncados
                last_field_index = -1

            # Completam el último objeto con campos vacíos
            for field in fields[last_field_index+1:]:
                json_obj[-1][field] = '""'
        else:
            # Si json_obj no es una lista o está vacío, no hace nada
            pass

        # Convierrte el objeto JSON de vuelta a una cadena
        completed_json_string = json.dumps(json_obj)

        return completed_json_string
    
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
    
    def detect_language(self, text, full_name=False):
        try:
            detected_language = detect(text)
            if detected_language == 'es' or detected_language == 'en':
                if full_name:
                    language_full_name = {
                        'en': 'english',
                        'es': 'spanish',
                        # Añadir aquí más idiomas 
                    }.get(detected_language, 'english')  # inglés idioma por defecto
                    return language_full_name
                else:
                    return detected_language
            else:
                return 'english' if full_name else 'en'
        except:
            return 'english' if full_name else 'en'
   
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
        
    @staticmethod
    def clean_invoice_text(text):
        text = TextProcessor.remove_watermark(text)
        text = TextProcessor.remove_header_footer(text)
        return text


    def classify_email(self, text):
        text = text.lower()
        language = self.detect_language(text, True)

        # Agrega preprocesamiento de texto
        stop_words = set(stopwords.words(language))
        lemmatizer = WordNetLemmatizer()

        word_tokens = word_tokenize(text)
        filtered_text = [lemmatizer.lemmatize(w) for w in word_tokens if not w in stop_words and w.isalnum()]

        # Palabras clave para cada categoría en diferentes idiomas
        keywords = {
            'es': {
                'invoice': [label.lower() for label in self.translations["invoice_header_labels"]["Total"] + self.translations["invoice_header_labels"]["Subtotal"]],
                'order': [label.lower() for label in self.translations["order_header_labels"]["Order Number"] + self.translations["order_detail_labels"]["Item"]],
                'price_request': self.translations["email_categories"]["keywords"]["price_request"],
                'informative': self.translations["email_categories"]["keywords"]["informative"],
                'unrelated': self.translations["email_categories"]["keywords"]["unrelated"]
            },
            'en': {
                'invoice': [label.lower() for label in self.translations["invoice_header_labels"]["Total"] + self.translations["invoice_header_labels"]["Subtotal"]],
                'order': [label.lower() for label in self.translations["order_header_labels"]["Order Number"] + self.translations["order_detail_labels"]["Item"]],
                'price_request': self.translations["email_categories"]["keywords"]["price_request"],
                'informative': self.translations["email_categories"]["keywords"]["informative"],
                'unrelated': self.translations["email_categories"]["keywords"]["unrelated"]
            }
        }

        categories = keywords.get(language, keywords['en'])

        # Usa CountVectorizer para considerar n-grams
        vectorizer = CountVectorizer(ngram_range=(1, 3))  # Considera n-grams de tamaño 1 a 3
        # Ajusta y transforma el texto del correo electrónico
        text_vector = vectorizer.fit_transform([' '.join(filtered_text)]).toarray()

        for category, category_keywords in categories.items():
            # Aplana la lista de palabras clave
            flat_category_keywords = [item for sublist in category_keywords for item in sublist]

            # Transforma las palabras clave de la categoría
            keyword_vector = vectorizer.transform(flat_category_keywords).toarray()

            # Comprueba si alguna de las palabras clave de la categoría está en el texto
            if any(keyword in text_vector for keyword in keyword_vector):
                return self.translations["email_categories"]["classification"][category]

        # Si no se encontró ninguna coincidencia, clasificar como 'other'
        return self.translations["email_categories"]["classification"]["other"]
    
    def clean_email_text(self, text):
        if text == "":
            return text  

        # Elimina saltos de línea innecesarios y espacios en blanco adicionales
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r'\s{2,}', ' ', text)
        text = re.sub(r'[ ]{2,}', ' ', text)
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'\([^)]*\)', '', text)

        # Eliminar la firma del correo electrónico
        signature_regex = re.compile(r'--\s*\n.*', re.DOTALL)
        text = re.sub(signature_regex, '', text)

        # Extraer el último correo electrónico en una cadena de correos electrónicos
        if "From:" in text:
            emails = text.split("From:")
            text = emails[-1]

        # Eliminar los campos CC y otros campos no deseados
        cc_regex = re.compile(r'\n[Cc]{2}:.*\n')
        text = re.sub(cc_regex, '\n', text)

        # Conservar solo el campo 'To:'
        text_lines = text.split("\n")
        to_line = ""
        for line in text_lines:
            if line.startswith("To:"):
                to_line = line
                break
        text = to_line + "\n" + "\n".join(text_lines)

        # Limpiar información de archivos adjuntos REVISAR
        attachment_regex = re.compile(r'\.(?:jpg|jpeg|png|gif|bmp|pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|7z|txt)', re.IGNORECASE)
        text = re.sub(attachment_regex, '', text)

        # Detectar el idioma del texto
        lang = detect(text)

        return text

    def combined_clean_text(self, cl_email_subject, email_body, email_content):
        # Limpia el email_body (texto del correo) y el email_content (texto del adjunto) 
        cl_email_body = self.clean_email_text(email_body) if email_body else ""
        cl_email_content = self.clean_email_text(email_content) if email_content else ""

        # Fusiona cl_email_subject, cl_email_body y cl_email_content sin duplicados
        cl_email_combined = cl_email_subject + "\n" + cl_email_body + "\n" + "".join(line for line in cl_email_content.splitlines(True) if line.strip() not in (cl_email_subject + cl_email_body))
            
        return cl_email_combined

    def clean_prompt(self, prompt):
        cleaned_prompt = prompt.replace('\n', ' ').replace('\r', '')
        cleaned_prompt = ' '.join(cleaned_prompt.split())
        return cleaned_prompt
    
