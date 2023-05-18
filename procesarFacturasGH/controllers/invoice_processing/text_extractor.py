from email import message_from_string
import re

class TextExtractor:
    def __init__(self, text_processor):
        self.text_processor = text_processor

    def extract_and_clean_text(self, email_subject, email_body, email_content, type_content):
        cl_email_subject = self.text_processor.clean_text_content(email_subject)

        if type_content == "content":
            cleaned_email_content = self.text_processor.clean_objects_content(email_content)
            cl_email_content = self.text_processor.clean_text_content(cleaned_email_content)
            text = cl_email_subject + " " + cl_email_content
        elif type_content == "body":
            cl_email_body = self.text_processor.clean_email_text_body(email_body)
            text = cl_email_subject + " " + cl_email_body
        elif type_content == "combined":
            text = self.text_processor.combined_clean_text(cl_email_subject , email_body, email_content)

        return text
    
    @staticmethod
    def extract_last_email_body(raw_email):
        if "From:" not in raw_email:
            return raw_email

        split_emails = raw_email.split("From:")
        emails = [message_from_string("From:" + email) for email in split_emails[1:]]

        if not emails:
            return raw_email

        last_email = emails[-1]
        if last_email.is_multipart():
            for part in last_email.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
        else:
            body = last_email.get_payload(decode=True)

        body = body.decode('utf-8')

        return TextExtractor.extract_last_email_body(body)
    
    @staticmethod
    def extract_first_significant_email_body(raw_email):
        if "From:" not in raw_email:
            return raw_email

        split_emails = raw_email.split("From:")
        bodies = []

        # Extract all email bodies
        for i in range(1, len(split_emails)):
            email_str = "From:" + split_emails[i]
            email = message_from_string(email_str)

            body = ""
            if email.is_multipart():
                for part in email.walk():
                    if part.get_content_type() == "text/plain":
                        # Get the payload and decode it to string
                        body_bytes = part.get_payload(decode=True)
                        body = body_bytes.decode('utf-8', errors='ignore')
            else:
                # Get the payload and decode it to string
                body_bytes = email.get_payload(decode=True)
                body = body_bytes.decode('utf-8', errors='ignore')

            bodies.append(body)

        # Search for the first non-blank email body from the end
        for body in reversed(bodies):
            cleaned_body = re.sub(r'\n\s*\n', '\n', body)
            cleaned_body = re.sub(r'\s{2,}', ' ', cleaned_body)
            cleaned_body = re.sub(r'[ ]{2,}', ' ', cleaned_body)
            cleaned_body = re.sub(r'http\S+', '', cleaned_body)
            cleaned_body = re.sub(r'\S+@\S+', '', cleaned_body)
            cleaned_body = re.sub(r'\([^)]*\)', '', cleaned_body)

            # Check if the cleaned body contains any non-whitespace characters
            if re.search(r'\S', cleaned_body):
                return cleaned_body

        # If no significant bodies found, return the original text
        return raw_email
