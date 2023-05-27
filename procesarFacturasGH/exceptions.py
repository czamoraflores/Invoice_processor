class InvalidFileFormatError(Exception):
    def __init__(self, message):
        super().__init__(message)

class RateLimitError(Exception):
    def __init__(self, message, error_type=None, error=None, text_raw=None, segment=None, prompt=None, email_subject=None, classify=None, segment_type=None, exception_retry_count=0,low_confidence_retry_count=0):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.error = error
        self.text_raw = text_raw
        self.segment = segment
        self.prompt = prompt
        self.email_subject = email_subject
        self.classify = classify
        self.segment_type = segment_type
        self.exception_retry_count = exception_retry_count
        self.low_confidence_retry_count = low_confidence_retry_count

class APIConnectionError(Exception):
    def __init__(self, message):
        super().__init__(message)

class OpenAIError(Exception):
    def __init__(self, message, error_type=None, error=None, text_raw=None, segment=None, prompt=None, email_subject=None, classify=None, segment_type=None, exception_retry_count=0,low_confidence_retry_count=0,n_request=None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.error = error
        self.text_raw = text_raw
        self.segment = segment
        self.prompt = prompt
        self.email_subject = email_subject
        self.classify = classify
        self.segment_type = segment_type
        self.exception_retry_count = exception_retry_count
        self.low_confidence_retry_count = low_confidence_retry_count
        self.n_request = n_request

class JSONDecodeError(Exception):
    def __init__(self, message, text_raw=None, text_clean=None , segment=None, prompt=None, email_subject=None,classify=None,segment_type=None, exception_retry_count=0 , low_confidence_retry_count=0, json_error=None,n_request=None):
        super().__init__(message)
        self.message = message
        self.text_raw = text_raw
        self.text_clean = text_clean
        self.segment = segment
        self.prompt = prompt
        self.email_subject = email_subject
        self.classify = classify
        self.segment_type = segment_type
        self.exception_retry_count = exception_retry_count
        self.low_confidence_retry_count = low_confidence_retry_count
        self.json_error = json_error
        self.n_request = n_request
        
