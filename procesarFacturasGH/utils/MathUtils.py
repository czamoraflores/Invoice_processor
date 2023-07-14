from utils.utils import Utils

class MathUtils:
   
    @staticmethod
    def calculate_total_line(txtEvents, item):
        try:
            # Si 'item' es un diccionario con 'Quantity' y 'Unit Price' como listas
            if isinstance(item.get('Quantity'), list) and isinstance(item.get('Unit Price'), list):
                total_line_values = []
                for quantity, price in zip(item.get('Quantity', []), item.get('Unit Price', [])):
                    # Intenta convertir 'Quantity' y 'Price' a float
                    quantity = MathUtils.convert_to_float(quantity)
                    price = MathUtils.convert_to_float(price)
                    total_line = round(quantity * price, 2)  # Redondeo a 2 decimales
                    total_line_values.append(total_line)
                return total_line_values
            else:
                # Si 'item' es un solo diccionario con 'Quantity' y 'Price' como claves
                quantity = MathUtils.convert_to_float(item.get('Quantity', '0'))
                price = MathUtils.convert_to_float(item.get('Unit Price', '0'))
                total_line = round(quantity * price, 2)  # Redondeo a 2 decimales
                return total_line
        except ValueError as ve:
            Utils.append_text(txtEvents, f'<font color="red">Error al convertir a float: {ve}</font><br>')
            return -1
        except Exception as e:
            Utils.append_text(txtEvents, f'<font color="red">Error desconocido: {e}</font><br>')
            return -1
    
    @staticmethod
    def convert_to_float(value):
        try:
            return float(value)  
        except ValueError:   
            return -1
        
    @staticmethod
    def calculate_confidence_score(probability_score, average_confidence):
        # Verifica si las dos variables son numéricas y existen
        if isinstance(probability_score, (int, float)) and isinstance(average_confidence, (int, float)):
            # Si average_confidence es cero o None, establece la puntuación de confianza igual a probability_score
            if average_confidence == 0 or average_confidence is None:
                confidence_score = probability_score
            else:
                # Calcula la puntuación de confianza y la redondea a 2 decimales
                confidence_score = round((probability_score + average_confidence) / 2, 2)
        else:
            # Si alguna de las variables no es numérica o no existe, establece la puntuación de confianza en None
            confidence_score = None

        return confidence_score
