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
    def append_text(txt_obj, text, new_line=False, process_events=True):
        if text:
            if new_line:
                text += '<br>'
            txt_obj.appendHtml(text)
            if process_events:
                QApplication.processEvents()

    @staticmethod
    def append_colored_text(txt_obj, text_list, new_line=False, process_events=True):
        text = ''
        for txt in text_list:
            if txt:
                text += txt
        if new_line:
            text += '<br>'
        if text:
            txt_obj.appendHtml(text)
            if process_events:
                QApplication.processEvents()

    @staticmethod
    def recoger_variables(**kwargs):
        # kwargs es un diccionario que contiene todas las variables que se le pasaron a la función
        all_vars = kwargs
        return all_vars
    
    @staticmethod
    def collect_info(text_raw, text_clean, segment, extract_clean_text, prompt, id_prompt , label_prompt, n_request, email_subject, classify, segment_type, exception_retry_count, low_confidence_retry_count, max_tokens, text_response, is_attachment_empty, logprob_value, probability_score, fixed_json_text, success, caught_error, error_type, error_description=None, engine="text-davinci-003"):
        if isinstance(segment, list):
            segment = ', '.join(segment)

        info = {
            "RequestNumber": n_request,
            "Classify": classify,
            "SegmentType": segment_type,
            "RetryCountExcep": exception_retry_count,
            "RetryCountLowConf":low_confidence_retry_count,
            "Success": success,
            "Tokens": max_tokens,
            "Engine": engine,
            "EmailSubject": email_subject,
            "IDPrompt": id_prompt,
            "LabelPrompt": label_prompt,
            "Prompt": prompt,
            "TextRaw": text_raw,
            "TextClean": text_clean,
            "ExtractAndCleanedText": extract_clean_text,
            "Segment": segment,
            "TextResponse": text_response,
            "AttachmentEmpty":is_attachment_empty,
            "FixedJsonText": fixed_json_text,
            "LogprobValue": logprob_value,
            "ProbabilityScore": probability_score,
            "CaughtError": caught_error,
            "ErrorType": error_type,
            "ErrorDescription": error_description

        }
        return info