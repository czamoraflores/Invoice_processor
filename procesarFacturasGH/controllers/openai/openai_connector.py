from datetime import datetime
import openai
import time
import math
import json

from openai.error import RateLimitError
from utils.utils import Utils
from utils.MathUtils import MathUtils
from PyQt5.QtWidgets import QApplication
from controllers.invoice_processing.text_extractor import TextExtractor
from half_json.core import JSONFixer
from exceptions import OpenAIError, JSONDecodeError

# diagrams.net

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
        self.all_info = []
        
        self.categories = {
            'en': {
                'invoice': 'an email containing an invoice, which is a document detailing a transaction that has already taken place, with details about goods or services provided, their quantities, and prices. The email often includes terms like "invoice", "total amount", "due date", "payment terms"',
                'order': 'an email containing an order or purchase request, which is a document detailing a request for goods or services that is often generated before the transaction is completed. It includes product descriptions, quantities, and prices, often including terms like "order", "request", "purchase"',
                'quote': 'an email containing a quote (e.g., a document detailing a pricing proposal for goods or services, often including terms like "quote", "price", "proposal")',
                'information_request': 'an email containing a request for information (e.g., a question about a product or service, often including terms like "question", "information", "details", "inquiry")'
            },
            'es': {
                'invoice': 'un correo electrónico que contiene una factura, que es un documento que detalla una transacción ya realizada, con detalles sobre los bienes o servicios proporcionados, sus cantidades y precios. El correo electrónico a menudo incluye términos como "factura", "cantidad total", "fecha de vencimiento", "términos de pago"',
                'order': 'un correo electrónico que contiene una orden de compra o solicitud de compra, que es un documento que detalla una solicitud de bienes o servicios que a menudo se genera antes de que se complete la transacción. Incluye descripciones de productos, cantidades y precios, a menudo incluyendo términos como "orden", "solicitud", "compra"',
                'quote': 'un correo electrónico que contiene una cotización (por ejemplo, un documento que detalla una propuesta de precios para bienes o servicios, a menudo incluyendo términos como "cotización", "precio", "propuesta")',
                'information_request': 'un correo electrónico que contiene una solicitud de información (por ejemplo, una pregunta sobre un producto o servicio, a menudo incluyendo términos como "pregunta", "información", "detalles", "consulta")'
            }
        }

    def extract_data(self, n_request, email_subject, email_body, email_content ):

        if email_content:
            is_attachment_empty = not bool(email_content.strip())
        else:
            is_attachment_empty = True
        
        headeri_data = []
        detaili_data = []
        headero_data = []
        detailo_data = []


        # Texto Crudo  limpio      extraido y limpio
        text_raw     , text_clean, clean_extracted_text = self.text_processor.extract_and_clean_text(email_subject, email_body, email_content, self.openai_config["type_content"])
        #clean_extracted_text = text_clean

        max_tokens , lang , prompt_result  = self.text_processor.get_prompt_categories(clean_extracted_text, self.categories)
        if max_tokens > 4096:
            info = Utils.log_and_collect_info(self, text_raw , text_clean , clean_extracted_text , clean_extracted_text, prompt_result, 'CLASSIFI_1','CLASSIFICATION', n_request, email_subject, None     , None       , 0   , 0   ,   0   ,  max_tokens   , ''  ,  is_attachment_empty, 0  , 0  , None , False , None, None , "long_segment" )            
            self.all_info.append(info)
            return n_request, {}, {}, {}, {} , self.all_info
  
        # Clasificar el correo electrónico
        tokens , prompt_cat, text_response, logprob_value, probability_score, email_classification_ai = self.classify_email_openai_cat(max_tokens , lang , prompt_result , self.categories)
        if email_classification_ai in ["invoice", "order"] and email_content != '': 
            text_raw , text_clean, clean_extracted_text = self.text_processor.extract_and_clean_text(email_subject, email_body, email_content, 'content')
        
        split_segments = self.text_processor.split_text_into_segments(clean_extracted_text, 4096)
        unique_segments = list(set(split_segments))
        info = Utils.log_and_collect_info(self, text_raw , text_clean , unique_segments, clean_extracted_text, prompt_cat , 'CLASSIFI_1','CLASSIFICATION', n_request, email_subject, email_classification_ai,  'classification' , email_classification_ai  , 0   ,   0   , tokens       , text_response, is_attachment_empty , logprob_value, probability_score, None , True , None, probability_score, "classification")
        self.all_info.append(info)
        n_request += 1    
        id_header , label_header , header_prompt, id_detail, label_detail, detail_prompt = self.get_prompts(email_classification_ai)
        
        if len(unique_segments) <= self.openai_config['max_nrquest_openai']:
            if email_classification_ai in ["invoice", "order"]: 
                try: 
                    for segment in unique_segments:
                        try:
                            used_prompt = header_prompt
                            n_request, header_data = self.process_segment(text_raw , text_clean , clean_extracted_text , segment, header_prompt, id_header , label_header, n_request, email_subject,email_classification_ai, 'header',is_attachment_empty )                            
                            used_prompt = detail_prompt
                            n_request, detail_data = self.process_segment(text_raw , text_clean , clean_extracted_text , segment, detail_prompt, id_detail, label_detail,  n_request, email_subject,email_classification_ai, 'detail',is_attachment_empty )
                        except openai.error.OpenAIError as e:
                            Utils.append_text(self.txtEvents, f'{e}', 'brown', True)
                            time.sleep(60)
                        except json.JSONDecodeError as e:
                            error = JSONDecodeError('Invalid JSON string generated forn OpenAI:', text_clean, clean_extracted_text , segment, used_prompt, n_request, email_subject )
                            self.handle_json_error(error)

                        if email_classification_ai == "invoice":  
                            self.process_and_append_data('Invoice Number', header_data, detail_data, self.headeri_column_mapping, self.detaili_column_mapping, headeri_data, detaili_data)
                        elif email_classification_ai == "order":  
                            self.process_and_append_data('Order Number', header_data, detail_data, self.headero_column_mapping, self.detailo_column_mapping, headero_data, detailo_data)

                except Exception as e:
                    Utils.append_text(self,f'<br><font color="green">Un error desconocido ocurrió: {str(e)}</font>')
        else:           
            headeri_data = None
            detaili_data = None
            headero_data = None
            detailo_data = None

        return n_request, headeri_data, detaili_data, headero_data, detailo_data, self.all_info

    def process_segment(self, text_raw , text_clean , extract_clean_text , segment, prompt, id_prompt , label_prompt, n_request, email_subject, classify ,  segment_type,  is_attachment_empty, engine="text-davinci-003", exception_retry_count=0,low_confidence_retry_count=0, temp_data=None, temp_confidence=-1):

        
        if low_confidence_retry_count == 0:
            temp_data = None
            temp_confidence = 0
        max_tokens = Utils.get_dynamic_max_tokens(prompt + segment, 0.1)
        if max_tokens > 4096:
            info = Utils.log_and_collect_info(self, text_raw , text_clean , segment, extract_clean_text, prompt, id_prompt , label_prompt, n_request, email_subject, None                    , classify, segment_type, exception_retry_count, low_confidence_retry_count, max_tokens, ''           ,  is_attachment_empty, 0           , 0                , None           ,   False,  None             , None, "long_segment")
            self.all_info.append(info)
            return n_request, {}  # Devuelve un diccionario vacío.
        try:
            response = openai.Completion.create(
                engine=engine,
                prompt = prompt + segment,
                temperature=0,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                best_of=1,
                stop=None,
                logprobs=1
            )
            n_request += 1
            #text_response, logprob_value, probability_score = self.process_response_chatcompletion(response)
            text_response, logprob_value, probability_score = self.process_response(response)           

            # Limpia el texto
            json_text_clean = self.text_processor.clean_text_before_json(text_response )

            # Corrige el JSON inválido
            fixed_json_text = self.text_processor.fix_invalid_json(json_text_clean)

            # Carga el JSON utilizando la función load_json
            data_list = json.loads( self.text_processor.load_jsons( fixed_json_text , json_text_clean) )  
            
            # Calcula la puntuación de confianza para cada diccionario en data_list
            average_confidence = Utils.calculate_confidence(data_list)

            # Calcula el nivel de confianza
            confidence = MathUtils.calculate_confidence_score(probability_score, average_confidence)

            # Asigna las puntuaciones a cada elemento en data_list
            data_list = Utils.assign_scores(data_list, average_confidence, probability_score, confidence)

            data = {}
            if len(data_list) > 1:
                for item in data_list:
                    for key, value in item.items():
                        if key not in data:
                            data[key] = [value]  # Inicializa una lista con el primer valor
                        else:
                            data[key].append(value)  # Añade el valor a la lista existente
            elif len(data_list) == 1:
                data = data_list[0]

            if low_confidence_retry_count == 0 and probability_score < 90:
                # primer intento       
                engine = "text-davinci-003"     
                temp_data = data
                temp_confidence = probability_score 
                info = Utils.log_and_collect_info(self, text_raw , text_clean , segment, extract_clean_text, prompt, id_prompt , label_prompt, n_request, email_subject, None,                     classify, segment_type, exception_retry_count, low_confidence_retry_count, max_tokens, text_response,  is_attachment_empty, logprob_value, probability_score, fixed_json_text,   True  , average_confidence,confidence, "low_confidence")                
                self.all_info.append(info) 
                low_confidence_retry_count +=1
                return self.process_segment(text_raw , text_clean , extract_clean_text , text_clean, prompt, id_prompt , label_prompt, n_request, email_subject, classify ,  segment_type,  is_attachment_empty , engine , exception_retry_count, low_confidence_retry_count, temp_data, temp_confidence  )
            else:
                # segundo intento retorna quien tiene mayor indice confidence
                if temp_data is not None and temp_confidence > probability_score:
                    data = temp_data
                info = Utils.log_and_collect_info(self, text_raw , text_clean , segment, extract_clean_text, prompt, id_prompt , label_prompt, n_request, email_subject, None                    , classify, segment_type, exception_retry_count,low_confidence_retry_count, max_tokens, text_response,  is_attachment_empty , logprob_value, probability_score, fixed_json_text,   True, average_confidence ,confidence, "process_segment")
                self.all_info.append(info)
                return n_request, data            
        
        except openai.error.RateLimitError:
            error = RateLimitError('Excedido el límite de velocidad', text_raw, segment, prompt, email_subject, classify, segment_type,exception_retry_count,low_confidence_retry_count)     
            return self.handle_openai_error(error)     

        except openai.error.OpenAIError:
            error = OpenAIError('Error de conexión a OpenAI', text_raw, segment, prompt, email_subject, classify, segment_type, exception_retry_count,low_confidence_retry_count )     
            return self.handle_openai_error(error)     
           
        except json.JSONDecodeError as e:
            index = None  
            error_description = str(e)
            caught_error = True
            error_type = type(e).__name__
            success = False
            engine = "text-davinci-003"
            info = Utils.collect_info(text_raw,  text_clean , segment, extract_clean_text, prompt, id_prompt , label_prompt, n_request, email_subject, classify, segment_type, exception_retry_count, low_confidence_retry_count ,max_tokens, text_response , is_attachment_empty, logprob_value, probability_score, fixed_json_text, success, None , probability_score, self.tiempo , caught_error, error_type, error_description, engine )
            self.all_info.append(info)

            if classify == "invoice" and segment_type == "header":
                index = 'INVOICE_MAIN'
            elif classify == "invoice" and segment_type == "detail":
                index = 'INVOICE_DETAIL'
            elif classify == "order" and segment_type == "header":
                index = 'ORDER_MAIN'
            elif classify == "order" and segment_type == "detail":
                index = 'ORDER_DETAIL'

            # filtra la lista de prompts opcionales basándonos en el LABEL
            filtered_prompts = [prompt for prompt in self.openai_config['optional_prompts'] if prompt['LABEL'] == index]

            # Si no encuentra el prompt correcto, genera un error
            if not filtered_prompts:
                raise ValueError(f"No se encontró un prompt opcional para '{index}'")

            if index is not None and exception_retry_count < 3:
                exception_retry_count += 1

                # Si es el primer intento de manejar un error, intenta con el texto semi-limpio.
                if exception_retry_count == 1:
                    segment = text_clean
                    prompt_to_use = prompt
                    id_prompt_to_use  = id_prompt 
                    label_prompt_to_use = label_prompt
                else:
                    # Selecciona el prompt basándose en el contador de reintentos
                    retry_index = (exception_retry_count - 2) % len(filtered_prompts)
                    prompt_to_use = filtered_prompts[retry_index]['PROMPT']
                    label_prompt_to_use = filtered_prompts[retry_index]['LABEL']
                    id_prompt_to_use = filtered_prompts[retry_index]['ID']

                error = JSONDecodeError(str(e),text_raw,None,segment,prompt,email_subject,classify,segment_type,exception_retry_count,low_confidence_retry_count,fixed_json_text,n_request )     
                self.handle_json_error(error)     
                time.sleep(15)                                       
                return self.process_segment(text_raw , text_clean , extract_clean_text , segment , prompt_to_use, id_prompt_to_use , label_prompt_to_use, n_request,  email_subject,classify,segment_type, is_attachment_empty, engine , exception_retry_count,low_confidence_retry_count )
            else:
                error = JSONDecodeError(str(e))     
                self.handle_json_error(error)     
                data = {"RawResponse": fixed_json_text, "Confidence": probability_score}
            return n_request, data

    def process_and_append_data(self, document_number_key, header_data, detail_data, header_mapping, detail_mapping, header_list, detail_list):
        header_processed_data = self.invoice_processor.normalize_labels(header_data, header_mapping)       
        document_number = header_processed_data.get(document_number_key, '')
        detail_processed_data = self.invoice_processor.normalize_labels(detail_data, detail_mapping)

        if isinstance(detail_processed_data, list):
            for detail in detail_processed_data:
                detail[document_number_key] = document_number
                # Añadir la línea para calcular 'Total Line'
                detail['Total Line Calculated'] = MathUtils.calculate_total_line(self.txtEvents, detail)
        elif isinstance(detail_processed_data, dict):
            detail_processed_data[document_number_key] = document_number
            # Añadir la línea para calcular 'Total Line'
            detail_processed_data['Total Line Calculated'] = MathUtils.calculate_total_line(self.txtEvents , detail_processed_data)
        else:
            Utils.append_text(f'<font color="red">Unexpected data type for detail_processed_data.</font><br>')
        
        header_list.append(header_processed_data)
        detail_list.append(detail_processed_data)

    def process_response(self, response):
        # Extraer el texto
        text_response = response['choices'][0]['text'].strip()

        # Inicializar los valores de logprob y probability_score
        logprob_value = 0
        probability_score = 0

        # Checar si 'logprobs' y 'top_logprobs' existen y no están vacíos
        if (response['choices'][0]['logprobs'] is not None and 
            response['choices'][0]['logprobs']['top_logprobs'] is not None and 
            len(response['choices'][0]['logprobs']['top_logprobs']) > 0):  
            logprob_value = list(response['choices'][0]['logprobs']['top_logprobs'][0].values())[0]
            probability_score = round(math.exp(logprob_value) * 100, 2)  # Redondeo a 2 decimales
            logprob_value = round(logprob_value, 2) 

        return text_response, logprob_value, probability_score

    def classify_email_openai_cat(self, max_tokens , lang , prompt_result , categories):
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt_result,
            top_p=1,
            temperature=0.1,
            max_tokens=max_tokens,
            logprobs=1
        )

        text, logprob_value, probability_score = self.process_response(response)
        for category in self.categories[lang]:
            if category in response.choices[0].text.lower():
                return max_tokens, prompt_result, text, logprob_value, probability_score, category
    
        return max_tokens, prompt_result, text, logprob_value, probability_score, 'other'
    
    def get_prompts(self, email_classification_ai):
        # Mapeo entre email_classification_ai y los LABELS correspondientes
        ai_to_labels_map = {
            "invoice": ("INVOICE_MAIN", "INVOICE_DETAIL"),
            "order": ("ORDER_MAIN", "ORDER_DETAIL"),
        }

        if email_classification_ai not in ai_to_labels_map:
            return None, None, None, None, None, None
        
        main_label, detail_label = ai_to_labels_map[email_classification_ai]

        # Inicializar las indicaciones como cadenas vacías
        id_detail = ""
        label_detail = ""
        id_header = ""
        label_header = ""
        header_prompt = ""
        detail_prompt = ""

        # Busca en la lista de PROMPTS para encontrar las indicaciones correspondientes
        for prompt_dict in self.openai_config["prompts"]:
            if prompt_dict["LABEL"] == main_label:
                id_header = prompt_dict["ID"]
                label_header = prompt_dict["LABEL"]
                header_prompt = prompt_dict["PROMPT"]
                
            elif prompt_dict["LABEL"] == detail_label:
                id_detail = prompt_dict["ID"]
                label_detail = prompt_dict["LABEL"]
                detail_prompt = prompt_dict["PROMPT"]

        return id_header , label_header , header_prompt, id_detail, label_detail, detail_prompt

    def handle_openai_error(self, error):
        if error.error_type in ['Excedido el límite de velocidad', 'Error de conexión a OpenAI']:
            if error.retry_count < self.max_retry:
                Utils.append_text(self, f'<font color="green">{error.error_type}, esperando 10 segundos antes de intentarlo de nuevo.</font>')
                time.sleep(10)
                error.retry_count += 1
                return self.process_segment(error.text_raw, error.segment, error.prompt, error.n_request, error.email_subject, error.classify, error.segment_type, error.exception_retry_count)
            else:
                raise OpenAIError(f'{error.error_type}, intentos de retransmisión agotados.')
        else:
            Utils.append_text(self,'<font color="brown">{}</font><br>'.format(error.message))
            time.sleep(10)
            if error.retry_count < self.max_retry:
                error.retry_count += 1
                return self.process_segment(error.text_raw, error.segment, error.prompt, error.n_request, error.email_subject, error.classify, error.segment_type, error.exception_retry_count)
            else:
                raise OpenAIError('Intentos de retransmisión agotados.')

    def handle_json_error(self, error):
        Utils.append_text(self, f'<font color="brown">Res AI </fon><font color="green"> {str(error.n_request)}</font> - <font color="brown"> Email : </font> <font color="green"> {error.email_subject} </font> <font color="brown"> {{No procesado!}} , {error.classify} {error.segment_type} </font><br>')
        Utils.append_text(self, f'<font color="brown">- Invalid JSON string generated for OpenAI : </font><font color="blue">{error.message}</font>')
        Utils.append_text(self, f'<font color="brown">- Uncleaned body text (raw) : </font><font color="blue">{error.text_raw}</font>')
        #Utils.append_text(self, f'<font color="brown">- Text clean : </font><font color="blue">{error.text_clean}</font>')
        Utils.append_colored_text(self, [
            f'<font color="brown">- Prompt and Text send to OpenAI : </font>',
            f'<font color="blue">{error.prompt}</font>',
            f'<font color="black"> {error.segment}</font>'
        ])
        Utils.append_text(self, f'<font color="brown">- Invalid JSON string generated for OpenAI : </font><font color="blue">{error.json_error}</font>')
        Utils.append_colored_text(self, [
            f'<font color="brown">- Classify (order, invoice) : </font>',
            f'<font color="green">{error.classify}</font>',
            f'<font color="brown"> Type segment (header, detail) : </font>',
            f'<font color="green">{error.segment_type}</font>',
            f'<font color="brown"> Retry number : </font>',
            f'<font color="green">{str(error.exception_retry_count)}</font>'
            f'<font color="brown"> Low confi etry number : </font>',
            f'<font color="green">{str(error.low_confidence_retry_count)}</font><br>'
        ], new_line=True)

        QApplication.processEvents()