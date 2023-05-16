import openai
import time
import math
import json

from openai.error import RateLimitError
from utils.utils import Utils
from PyQt5.QtWidgets import QApplication

class OpenAIConnector:

    header_prompt_invoice = (
        "You are an AI trained to extract and validate specific information from invoice-related texts in both English and Spanish. "
        "Please analyze the text below and provide the results in JSON format, along with a confidence score "
        "for each extracted piece of information. The information to extract includes 'Total': value, 'Subtotal': value, 'Order Date': value, "
        "'Numbering': value, 'Buyer': value, 'Seller': value, 'Purchase Date': value, 'Country': value, 'City': value. The 'Country' and 'City' values should correspond to the same geographical region within a country. "
        "Each field in the JSON response should be formatted as 'Field': value, even if the value is null. For example, given the input text: 'Order No. 12345, Buyer: John Doe, Seller: Acme Inc., Total: $100', "
        "the expected output is: '{\"Order No\": \"12345\", \"Buyer\": \"John Doe\", \"Seller\": \"Acme Inc.\", "
        "\"Total\": \"$100\", \"Confidence\": 95}'. Please provide the response as a single JSON object without any additional text.\n\n"
        "Text:\n"
    )
            
    detail_prompt_invoice = (
        "You are an AI trained to extract and validate specific information from multiple invoice line item details in texts, in both English and Spanish. "
        "Please analyze the text below and provide the results in JSON format, along with a confidence score "
        "for each extracted piece of information. The information to extract includes 'Description': value, 'Brand': value, 'Quantity': value, "
        "'Unit of Measure': value, 'Price': value. Each field in the JSON response should be formatted as 'Field': value, even if the value is null. "
        "For example, given the input text: 'Description: BS465N70 O-Ring, Brand: Brammer, Quantity: 90, Unit of Measure: each, Price: 4.67', "
        "the expected output is: '[{\"Description\": \"BS465N70 O-Ring\", \"Brand\": \"Brammer\", \"Quantity\": 90, \"Unit of Measure\": \"each\", "
        "\"Price\": \"4.67\", \"Confidence\": 95}]'. Please provide the response as a single JSON object or array without any additional text.\n\n"
        "Text:\n"
    )

    header_prompt_order = (
        "You are an AI trained to extract and validate specific information from purchase order-related texts in both English and Spanish. "
        "Please analyze the text below and provide the results in JSON format, along with a confidence score "
        "for each extracted piece of information. The information to extract includes 'Order Number': value, 'Order Date': value, "
        "'Buyer': value, 'Seller': value, 'Country': value, 'City': value. The 'Country' and 'City' values should correspond to the same geographical region within a country. "
        "Each field in the JSON response should be formatted as 'Field': value, even if the value is null. For example, given the input text: 'Order No. 12345, Buyer: John Doe, Seller: Acme Inc.', "
        "the expected output is: '{\"Order Number\": \"12345\", \"Buyer\": \"John Doe\", \"Seller\": \"Acme Inc.\", \"Confidence\": 95}'. Please provide the response as a single JSON object without any additional text.\n\n"
        "Text:\n"
    )

    detail_prompt_order = (
        "You are an AI trained to extract and validate specific information from multiple purchase order line item details in texts, in both English and Spanish. "
        "Please analyze the text below and provide the results in JSON format, along with a confidence score "
        "for each extracted piece of information. The information to extract includes 'Description': value, 'Brand': value, 'Quantity': value, "
        "'Unit of Measure': value, 'Unit Price': value. Each field in the JSON response should be formatted as 'Field': value, even if the value is null. "
        "For example, given the input text: 'Description: BS465N70 O-Ring, Brand: Brammer, Quantity: 90, Unit of Measure: each, Unit Price: 4.67', "
        "the expected output is: '[{\"Description\": \"BS465N70 O-Ring\", \"Brand\": \"Brammer\", \"Quantity\": 90, \"Unit of Measure\": \"each\", "
        "\"Unit Price\": \"4.67\", \"Confidence\": 95}]'. Please provide the response as a single JSON object or array without any additional text.\n\n"
        "Text:\n"
    )

    def __init__(self, openai_config, translations, txtEvents, text_processor, invoice_processor):
        self.openai_config = openai_config
        self.translations = translations
        self.text_processor = text_processor
        self.invoice_processor = invoice_processor
        self.txtEvents = txtEvents
        self.headeri_column_mapping = self.translations['invoice_header_labels']
        self.detaili_column_mapping = self.translations['invoice_detail_labels']
        self.headero_column_mapping = self.translations['order_header_labels']
        self.detailo_column_mapping = self.translations['order_detail_labels']

        openai.api_key = self.openai_config['api_key']

    def extract_data(self, n_request, email_subject, email_body, email_content):

        headeri_data = []
        detaili_data = []
        headero_data = []
        detailo_data = []
        extra_data   = {}

        cl_email_subject = self.text_processor.clean_email_text( email_subject )

        if self.openai_config["type_content"] == "content":
            cl_email_content = self.text_processor.clean_email_text( email_content )
            text = cl_email_subject + " " + cl_email_content
        elif self.openai_config["type_content"] == "body":
            cl_email_body = self.text_processor.clean_email_text( email_body )
            text = cl_email_subject + " " + cl_email_body
        elif self.openai_config["type_content"] == "combined":
            text = self.text_processor.combined_clean_text( cl_email_subject , email_body, email_content )

        # Clasificar el correo electrónico
        email_classification = self.text_processor.classify_email(text)
        email_classification_ai = self.classify_email_openai_cat(text)

        split_segments = self.text_processor.split_text_into_segments(text, 4096)
        set_split_segments = set(split_segments)
        unique_segments = list(set_split_segments)

        timestamp = time.time()
        extra_data["EmailID"] = self.text_processor.generate_custom_id(self.openai_config, email_subject, timestamp)
        extra_data["EmailClassif"] = email_classification
        extra_data["EmailClassif_ai"] = email_classification_ai
        extra_data["Texto"] = text

        if email_classification_ai == "invoice":
            if not self.openai_config["prompt"].strip():
                header_prompt = self.header_prompt_invoice
            else:
                header_prompt = self.openai_config["prompt"]

            if not self.openai_config["promptd"].strip():
                detail_prompt = self.detail_prompt_invoice
            else:
                detail_prompt = self.openai_config["promptd"]

        if email_classification_ai == "order":
            if not self.openai_config["prompto"].strip():
                header_prompt = self.header_prompt_order
            else:
                header_prompt = self.openai_config["prompto"]

            if not self.openai_config["promptd_order"].strip():
                detail_prompt = self.detail_prompt_order
            else:
                detail_prompt = self.openai_config["promptd_order"]


        if email_classification_ai not in ["invoice", "order"] :
            header_prompt = ""
            detail_prompt = "" 

        extra_data["Invoice_Header_Prompt"] = self.header_prompt_invoice
        extra_data["Invoice_Detail_Prompt"] = self.detail_prompt_invoice
        extra_data["Order_Header_Prompt"] = self.header_prompt_order
        extra_data["Order_Detail_Prompt"] = self.detail_prompt_order

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
            raise ValueError(f"Unexpected email classification: {email_classification}")

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
            raise ValueError("Unexpected data type for detail_processed_data.")
        
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
            self.txtEvents.appendHtml(f'<font color="blue">Request OpenAI: {n_request} - El Email: {email_subject} {{ Ha sido procesado }}</font><br>')
            QApplication.processEvents()
            text = response['choices'][0]['text'].strip()
            if response['choices'][0]['logprobs'] is not None and response['choices'][0]['logprobs']['top_logprobs'] is not None and len(response['choices'][0]['logprobs']['top_logprobs']) > 0:
                logprob_value = list(response['choices'][0]['logprobs']['top_logprobs'][0].values())[0]
                probability_score = math.exp(logprob_value) * 100
            else:
                probability_score = 0

            # Limpia el texto
            cleaned_text = self.text_processor.clean_text_before_json(text)

            # Intenta completar el JSON truncado
            completed_json_text = self.text_processor.complete_truncated_json(cleaned_text)

            if self.text_processor.is_valid_json(completed_json_text):
                data_list = json.loads(completed_json_text) 
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
                data = {"RawResponse": text, "Confidence": 0}
                self.txtEvents.appendHtml('<font color="red">Texto no válido o vacío devuelto por la API de OpenAI.</font><br>')
                print("Response from OpenAI API:", text)

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