import openai
import time
import math
import json

from openai.error import RateLimitError
from utils.utils import Utils
from PyQt5.QtWidgets import QApplication
from controllers.invoice_processing.text_extractor import TextExtractor
from half_json.core import JSONFixer

class OpenAIConnector:

    def __init__(self, openai_config, translations, txtEvents, text_processor, invoice_processor):
        self.openai_config = openai_config
        self.translations = translations
        self.text_processor = text_processor
        self.text_extractor = TextExtractor(text_processor)
        self.invoice_processor = invoice_processor
        self.txtEvents = txtEvents
        self.headeri_column_mapping = self.translations['invoice_header_labels']
        self.detaili_column_mapping = self.translations['invoice_detail_labels']
        self.headero_column_mapping = self.translations['order_header_labels']
        self.detailo_column_mapping = self.translations['order_detail_labels']
        self.jsonfixer = JSONFixer()
     
        openai.api_key = self.openai_config['api_key']

    def extract_data(self, n_request, email_subject, email_body, email_content):

        headeri_data = []
        detaili_data = []
        headero_data = []
        detailo_data = []
        extra_data   = {}

        text = self.text_extractor.extract_and_clean_text(email_subject, email_body, email_content, self.openai_config["type_content"])
        text_crude = self.text_processor.clean_text_content(email_subject + " " + email_body + " " + email_content)
        # Clasificar el correo electrónico
        email_classification = self.text_processor.classify_email(text)
        email_classification_ai = self.classify_email_openai_cat(text)

        header_prompt, detail_prompt = self.get_prompts(email_classification_ai)

        split_segments = self.text_processor.split_text_into_segments(text, 4096)
        unique_segments = list(set(split_segments))

        timestamp = time.time()
        extra_data["EmailID"] = self.text_processor.generate_custom_id(self.openai_config, email_subject, timestamp)
        extra_data["EmailClassif"] = email_classification
        extra_data["EmailClassif_ai"] = email_classification_ai
        extra_data["TextoClean"] = text
        extra_data["TextoCrude"] = text_crude

        extra_data["Invoice_Header_Prompt"] = self.openai_config["prompt_start"]
        extra_data["Invoice_Detail_Prompt"] = self.openai_config["prompt_startd"]
        extra_data["Order_Header_Prompt"] = self.openai_config["prompt_starto"]
        extra_data["Order_Detail_Prompt"] = self.openai_config["prompt_startd_order"]

        if len(unique_segments) <= self.openai_config['max_nrquest_openai']:
            if email_classification_ai in ["invoice", "order"]:  
                for segment in unique_segments:
                    n_request, header_data = self.process_segment(segment, header_prompt, n_request, email_subject)
                    n_request, detail_data = self.process_segment(segment, detail_prompt, n_request, email_subject)

                    if email_classification_ai == "invoice":  
                        self.process_and_append_data(email_classification_ai, header_data, detail_data, self.headeri_column_mapping, self.detaili_column_mapping, headeri_data, detaili_data)
                    elif email_classification_ai == "order":  
                        self.process_and_append_data(email_classification_ai, header_data, detail_data, self.headero_column_mapping, self.detailo_column_mapping, headero_data, detailo_data)
        else:
            headeri_data = None
            detaili_data = None
            headero_data = None
            detailo_data = None

        return n_request, headeri_data, detaili_data, headero_data, detailo_data, extra_data

    def process_and_append_data(self, email_classification, header_data, detail_data, header_mapping, detail_mapping, header_list, detail_list):
        header_processed_data = self.invoice_processor.normalize_labels(header_data, header_mapping)
        
        if email_classification == 'invoice':
            document_number_key = 'Invoice Number'
        elif email_classification == 'order':
            document_number_key = 'Order Number'
        else:
            self.txtEvents.appendHtml(f'<font color="red">Unexpected email classification: {email_classification}</font><br>')
            QApplication.processEvents()

        document_number = header_processed_data.get(document_number_key, '')

        detail_processed_data = self.invoice_processor.normalize_labels(detail_data, detail_mapping)



        if isinstance(detail_processed_data, list):
            for detail in detail_processed_data:
                detail[document_number_key] = document_number
                # Añadir la línea para calcular 'Total Line'
                detail['Total Line'] = self.calculate_total_line(detail)
        elif isinstance(detail_processed_data, dict):
            detail_processed_data[document_number_key] = document_number
            # Añadir la línea para calcular 'Total Line'
            detail_processed_data['Total Line'] = self.calculate_total_line(detail_processed_data)
        else:
            self.txtEvents.appendHtml(f'<font color="red">Unexpected data type for detail_processed_data.</font><br>')
            QApplication.processEvents()
        
        header_list.append(header_processed_data)
        detail_list.append(detail_processed_data)

    def process_data(self, data, column_mapping, id_number, id_key):
        processed_data = self.invoice_processor.normalize_labels(data, column_mapping)
        if isinstance(processed_data, list):  # Si es una lista de diccionarios
            for detail in processed_data:
                detail[id_key] = id_number
        elif isinstance(processed_data, dict):  # Si es un único diccionario
            processed_data[id_key] = id_number
        else:
            self.txtEvents.appendHtml(f'<font color="red">Unexpected data type for {id_key} data.</font><br>')
            QApplication.processEvents()

    def process_segment(self, segment, prompt, n_request, email_subject):
        max_tokens = Utils.get_dynamic_max_tokens(prompt + segment, 0.1)
        try:
            response = openai.Completion.create(
                engine="text-davinci-002",
                prompt=prompt + segment,
                temperature=0,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0.5,
                presence_penalty=0.5,
                best_of=1,
                stop=None,
                logprobs=1
            )
            n_request += 1
            self.txtEvents.appendHtml(f'<font color="blue">Request OpenAI: {n_request} - El Email: {email_subject} {{ Ha sido procesado }}</font>')
            QApplication.processEvents()
            text = response['choices'][0]['text'].strip()
            if response['choices'][0]['logprobs'] is not None and response['choices'][0]['logprobs']['top_logprobs'] is not None and len(response['choices'][0]['logprobs']['top_logprobs']) > 0:
                logprob_value = list(response['choices'][0]['logprobs']['top_logprobs'][0].values())[0]
                probability_score = math.exp(logprob_value) * 100
            else:
                probability_score = 0

            # Limpia el texto
            cleaned_text = self.text_processor.clean_text_before_json(text)
            # Corrige el JSON inválido
            fixed_json_text = self.text_processor.fix_invalid_json(cleaned_text)
            all_fixed = self.jsonfixer.fix(fixed_json_text)
            #completed_json_text = self.text_processor.complete_truncated_json(fixed_json_text)

            if all_fixed.success == True:
                data_list = json.loads(all_fixed.line) 
                # Asignar la puntuación de confianza a cada elemento 
                for item in data_list:
                    item["Confidence"] = probability_score
                # Procesar y combinar la información de data_list en un formato similar al header_response
                data = {}
                if len(data_list) > 1:
                    for item in data_list:
                        for key, value in item.items():
                            if key not in data:
                                data[key] = [value]  # Inicializa una lista con el primer valor
                            else:
                                data[key].append(value)  # Añade el valor a la lista existente
                else:
                    data = data_list[0]

            else:
                data = {"RawResponse": all_fixed.line, "Confidence": 0}
                self.txtEvents.appendHtml(f'<font color="red">Texto no válido o vacío devuelto por la API de OpenAI {all_fixed.line}.</font><br>')

            return n_request, data
        
        except openai.error.RateLimitError:
            self.txtEvents.appendHtml('<font color="brown">Excedido el límite de velocidad, esperando 60 segundos antes de intentarlo de nuevo.</font><br>')
            QApplication.processEvents()
            time.sleep(60)
            return self.process_segment(segment, prompt, n_request, email_subject)

        except openai.error.APIConnectionError:
            self.txtEvents.appendHtml('<font color="brown">Error de conexión a OpenAI, esperando 60 segundos antes de intentarlo de nuevo.</font><br>')
            QApplication.processEvents()
            time.sleep(60)
            return self.process_segment(segment, prompt, n_request, email_subject)
 
    def classify_email_openai_cat(self, email):
        categories = {
            'en': {
                'invoice': 'an email containing an invoice (e.g., a document detailing a transaction, such as the goods or services provided, their quantities, and prices, often including terms like "invoice", "total amount", "due date")',
                'order': 'an email containing an order or purchase request (e.g., a document detailing a request for goods or services, including product descriptions, quantities, and prices, often including terms like "order", "request", "purchase")',
                'complaint': 'an email containing a complaint (e.g., a statement expressing dissatisfaction with a product or service, often including terms like "problem", "issue", "not satisfied", "complaint")',
                'information_request': 'an email containing a request for information (e.g., a question about a product or service, often including terms like "question", "information", "details")'
            },
            'es': {
                'invoice': 'un correo electrónico que contiene una factura (por ejemplo, un documento que detalla una transacción, como los bienes o servicios proporcionados, sus cantidades y precios, a menudo incluyendo términos como "factura", "cantidad total", "fecha de vencimiento")',
                'order': 'un correo electrónico que contiene una orden de compra (por ejemplo, un documento que detalla una solicitud de bienes o servicios, incluyendo descripciones de productos, cantidades y precios, a menudo incluyendo términos como "orden", "solicitud", "compra")',
                'complaint': 'un correo electrónico que contiene una queja (por ejemplo, una declaración expresando insatisfacción con un producto o servicio, a menudo incluyendo términos como "problema", "asunto", "no satisfecho", "queja")',
                'information_request': 'un correo electrónico que contiene una solicitud de información (por ejemplo, una pregunta sobre un producto o servicio, a menudo incluyendo términos como "pregunta", "información", "detalles")'
            }
        }

        # Detecta el idioma del correo electrónico
        language = self.text_processor.detect_language(email)

        # Construye un prompt con las categorías en el idioma detectado
        categories_prompt = ', '.join([f'"{cat}"' for cat in categories[language].values()])
        if language == 'en':
            prompt = f"Please classify this email into one of the following categories: {categories_prompt} or something else. The email says: '{email}'."
        else:
            prompt = f"Por favor clasifica este correo electrónico en una de las siguientes categorías: {categories_prompt} o algo más. El correo electrónico dice: '{email}'."

        # Calcula el número de tokens para la respuesta
        response_tokens = Utils.get_dynamic_max_tokens(prompt + email,0.1)

        # Pregunta al modelo de OpenAI que clasifique el correo electrónico en una de las categorías
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=prompt,
            temperature=0.5,
            max_tokens=response_tokens
        )

        # Comprueba si la respuesta del modelo coincide con alguna de las descripciones de categoría
        for category, description in categories[language].items():
            if description.split(' (')[0] in response.choices[0].text.lower(): # Asegúrate de solo comparar la parte relevante de la descripción
                return category

        # Si el modelo no pudo clasificar el correo electrónico, retorna 'other'
        return 'other'
    
    def calculate_total_line(self, item):
        try:
            # Si 'item' es un diccionario con 'Quantity' y 'Unit Price' como listas
            if isinstance(item.get('Quantity'), list) and isinstance(item.get('Unit Price'), list):
                total_line_values = []
                for quantity, price in zip(item.get('Quantity', []), item.get('Unit Price', [])):
                    # Intenta convertir 'Quantity' y 'Price' a float
                    quantity = self.convert_to_float(quantity)
                    price = self.convert_to_float(price)
                    total_line = round(quantity * price, 2)  # Redondeo a 2 decimales
                    total_line_values.append(total_line)
                return total_line_values
            else:
                # Si 'item' es un solo diccionario con 'Quantity' y 'Price' como claves
                quantity = self.convert_to_float(item.get('Quantity', '0'))
                price = self.convert_to_float(item.get('Unit Price', '0'))
                total_line = round(quantity * price, 2)  # Redondeo a 2 decimales
                return total_line
        except ValueError as ve:
            self.txtEvents.appendHtml(f'<font color="red">Error al convertir a float: {ve}</font><br>')
            QApplication.processEvents()
            return -1
        except Exception as e:
            self.txtEvents.appendHtml(f'<font color="red">Error desconocido: {e}</font><br>')
            QApplication.processEvents()
            return -1
        
    def convert_to_float(self, value):
        try:
            return float(value)  
        except ValueError:   
            return -1

    def get_prompts(self, email_classification_ai):
        header_prompt = ""
        detail_prompt = ""

        if email_classification_ai == "invoice":
            header_prompt = self.openai_config["prompt_start"]
            detail_prompt = self.openai_config["prompt_startd"]
        elif email_classification_ai == "order":
            header_prompt = self.openai_config["prompt_starto"]
            detail_prompt = self.openai_config["prompt_startd_order"]

        return header_prompt, detail_prompt