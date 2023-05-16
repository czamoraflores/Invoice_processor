import tiktoken
import os

class Utils:
    @staticmethod
    def get_dynamic_max_tokens(text, base_tokens=150, extra_tokens=0, margin_percentage=0):
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