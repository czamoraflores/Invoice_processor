from datetime import datetime
import time
import tiktoken
import os
import re
from PyQt5.QtWidgets import QApplication

class Utils:

    @staticmethod
    def get_dynamic_max_tokens(text, margin_percentage=0):
        tokens = Utils.num_tokens_from_string(text, "gpt2")
        total_tokens = int(tokens * (1 + margin_percentage))  
        return max(total_tokens, 150)

    @staticmethod
    def num_tokens_from_string(string, encoding_name):
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens
    
    @staticmethod
    def is_valid_file_path(file_path: str) -> bool:
        return os.path.isfile(file_path)

    @staticmethod
    def is_valid_directory_path(directory_path: str) -> bool:
        return os.path.isdir(directory_path)
    
    @staticmethod
    def validate_and_update_path(path: str) -> str:
        if path.strip() == "":
            return path  
        if not (Utils.is_valid_directory_path(path) or os.path.isfile(path)):
            raise ValueError(f"Invalid directory path: {path}")
        updated_path = path
        return updated_path
    
    def validate_openai_api_key(api_key):
        # La API key de OpenAI debe comenzar con 'sk-', seguido de 32 caracteres alfanuméricos
        pattern = re.compile(r'^sk-[a-zA-Z0-9]{32,60}$')
        if not api_key or not pattern.match(api_key):
            raise ValueError("Invalid API Key", "The OpenAI API key is invalid. Please check it and try again.")
            return False
        return True

    @staticmethod
    def validate_paths(paths):
        for path in paths:
            if not os.path.exists(path):
                return False
        return True
    
    @staticmethod
    def validate_file(file_path):
        if not os.path.isfile(file_path):
            return False
        return True

    @staticmethod    
    def handle_classification(self, n_request, email_subject, email_classification_ai):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Formato: Año-Mes-Día Hora:Minuto:Segundo
        Utils.append_text(self.txtEvents, f'<font color="brown">Res AI </fon><font color="green"> {str(n_request-1)}</font> - <font color="brown"> Email : </font> <font color="green"> {email_subject} </font> - <font color="brown"> Classification : </font> <font color="green"> {email_classification_ai} </font> <font color="brown"> Timestamp : </font> <font color="green">{current_time}</font><br>')



    @staticmethod
    def calculate_confidence(data):

        if isinstance(data, list):
            total_confidence = 0
            for item in data:
                received_fields = [field for field in item]
                empty_fields = [field for field in received_fields if not item[field] or (isinstance(item[field], (int, float)) and item[field] <= 0)]
                confidence_score = (len(received_fields) - len(empty_fields)) / len(received_fields) * 100
                confidence_score = round(min(100, confidence_score), 2)  # Redondeo a 2 decimales
                item['ScoreFill'] = confidence_score
                total_confidence += confidence_score
            average_confidence = round(total_confidence / len(data), 2)  # Redondeo a 2 decimales
        else:
            received_fields = [field for field in data]
            empty_fields = [field for field in received_fields if not data[field] or (isinstance(data[field], (int, float)) and data[field] <= 0)]
            confidence_score = (len(received_fields) - len(empty_fields)) / len(received_fields) * 100
            confidence_score = round(min(100, confidence_score), 2)  # Redondeo a 2 decimales
            data['ScoreFill'] = confidence_score
            average_confidence = confidence_score

        return average_confidence

    @staticmethod
    def assign_scores(data_list, average_confidence, probability_score, confidence_score):
        for item in data_list:
            item["ScoreFill"] = average_confidence
            item["ScoreConfidence"] = probability_score
            item["Confidence"] = confidence_score
        return data_list

    @staticmethod
    def recoger_variables(**kwargs):
        # kwargs es un diccionario que contiene todas las variables que se le pasaron a la función
        all_vars = kwargs
        return all_vars
    
    @staticmethod
    def append_text(openai_connector, text, new_line=False, process_events=True):
        if text:
            if new_line:
                text += '<br>'
            openai_connector.txtEvents.appendHtml(text)
            if process_events:
                QApplication.processEvents()

    @staticmethod
    def append_colored_text(openai_connector, text_list, new_line=False, process_events=True):
        text = ''
        for txt in text_list:
            if txt:
                text += txt
        if new_line:
            text += '<br>'
        if text:
            openai_connector.txtEvents.appendHtml(text)
            if process_events:
                QApplication.processEvents()            

    @staticmethod
    def log_and_collect_info(openai_connector  , text_raw , text_clean , segment, extract_clean_text, prompt, id_prompt , label_prompt, n_request, email_subject, email_classification_ai, classify, segment_type, exception_retry_count, low_confidence_retry_count, max_tokens, text_response, is_attachment_empty, logprob_value, probability_score, fixed_json_text, success, average_confidence, confidence, log_type ):
        t = time.time() - openai_connector.invoice_processor.tiempo_ini  # Obtiene el tiempo transcurrido
        openai_connector.tiempo = round(t,2)

        current_time = datetime.now().strftime("%H:%M:%S")
 
        if log_type == 'classification':
            Utils.append_text(openai_connector, f'<font color="brown">Res AI </fon><font color="green"> {str(n_request-1)}</font> - <font color="brown"> Email : </font> <font color="green"> {email_subject} </font> - <font color="brown"> Classification : </font> <font color="green"> {email_classification_ai} </font> <font color="brown"> Time : </font> <font color="green">{current_time}</font><br>')
        elif log_type == 'process_segment':
            Utils.append_text(openai_connector, f'<font color="brown">Res AI </fon><font color="green"> {str(n_request-1)}</font> - <font color="brown"> Email : </font> <font color="green"> {email_subject} </font> <font color="brown"> {{Process!}} , {classify} {segment_type}</font> <font color="brown"> Time : </font> <font color="green">{current_time}</font><br>')
        elif log_type == 'long_segment':
            Utils.append_text(openai_connector, f'<font color="brown">Res AI </fon><font color="green"> {str(n_request-1)}</font> - <font color="brown"> Email : </font> <font color="green"> {email_subject} </font> <font color="brown"> El segmento es demasiado largo, {str(max_tokens)} No procesado! </font>')
        elif log_type == 'low_confidence':
            Utils.append_text(openai_connector, f'<font color="brown">Res AI </fon><font color="green"> {str(n_request-1)}</font> - <font color="brown"> Email : </font> <font color="green"> {email_subject} </font> <font color="brown"> Low Confidence, retry! </font> <font color="brown"> Time : </font> <font color="green">{current_time}</font><br>')
        else:
            Utils.append_text(openai_connector,f'<font color="brown">Res AI </fon><font color="green"> {str(n_request-1)}</font> - <font color="brown"> Email : </font> <font color="green"> {email_subject} </font> <font color="brown"> El segmento es demasiado largo, {str(max_tokens)} No procesado2! </font>')

        return Utils.collect_info(text_raw, text_clean, segment, extract_clean_text, prompt, id_prompt, label_prompt, n_request, email_subject, classify, segment_type, exception_retry_count,low_confidence_retry_count, max_tokens, text_response, is_attachment_empty, logprob_value, probability_score, fixed_json_text, success, average_confidence , confidence, openai_connector.tiempo)
    
    @staticmethod
    def collect_info(text_raw, text_clean, segment, extract_clean_text, prompt, id_prompt , label_prompt, n_request, email_subject, classify, segment_type, exception_retry_count, low_confidence_retry_count, max_tokens, text_response, is_attachment_empty, logprob_value, probability_score, fixed_json_text, success, average_confidence , confidence,  tiempo, caught_error=None, error_type=None,  error_description=None, engine="text-davinci-003"):
        if isinstance(segment, list):
            segment = ', '.join(segment)

        info = {
            "ReqNum": n_request,
            "Classify": classify,
            "SegmentType": segment_type,
            "RetrCountExcep": exception_retry_count,
            "RetrCountLowConf":low_confidence_retry_count,
            "Success": success,
            "Tokens": max_tokens,
            "Seconds": tiempo,
            "LProbValue": logprob_value,
            "ProbScore": probability_score,
            "ScoreFill": average_confidence,
            "Confidence": confidence,
            "AttachEmpty":is_attachment_empty,
            
            "IDPrompt": id_prompt,
            "LabelPrompt": label_prompt,
            "FixedJsonText": fixed_json_text,
            "CaughtError": caught_error,
            "ErrorType": error_type,
            "ErrorDescription": error_description,

            "TextResponse": text_response,
            "Engine": engine,
            "MailSubj": email_subject,
            "Prompt": prompt,
            "TextRaw": text_raw,
            "TextClean": text_clean,
            "ExtAndCleanText": extract_clean_text,
            "Segment": segment,

        }
        return info