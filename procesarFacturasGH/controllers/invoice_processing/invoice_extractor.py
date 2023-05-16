from controllers.file_processing.file_processor import FileProcessor

from controllers.invoice_processing.text_processor import TextProcessor
from controllers.openai.openai_connector import OpenAIConnector

from exceptions import InvalidFileFormatError

class InvoiceExtractor:
    def __init__(self, config, translations, openai_config, txtEvents, invoice_processor):
        self.config = config
        self.txtEvents = txtEvents
        self.translations = translations
        self.invoice_processor = invoice_processor
        self.text_processor = TextProcessor(translations)
        self.file_processor = FileProcessor(config, translations, self.text_processor)
        self.openai_connector = OpenAIConnector(openai_config, translations, txtEvents, self.text_processor, self.invoice_processor)

    def extract_data_from_file(self, n_request, file_path):
        if file_path.endswith('.msg'):
            email_subject, email_body, email_content = self.file_processor.process_msg_file(file_path)
        elif file_path.endswith('.eml'):
            email_subject, email_body, email_content = self.file_processor.process_eml_file(file_path)
        else:
            self.txtEvents.insertPlainText(f"{self.translations['ui']['InvalidFileFormatError']} {file_path}\n")

        n_request, headeri_data, detaili_data, headero_data, detailo_data, extra_data = self.openai_connector.extract_data(n_request, email_subject, email_body, email_content)
        return n_request, headeri_data, detaili_data, headero_data, detailo_data, extra_data
