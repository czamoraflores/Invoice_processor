import os
import json
import pandas as pd

from controllers.invoice_processing.invoice_extractor import InvoiceExtractor
from extract_msg.exceptions import InvalidFileFormatError
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment

class InvoiceProcessor:
    def __init__(self, params, translations, window_instance):
        self.config = params
        self.translations = translations
        self.txtEvents = window_instance.txtEvents

        if ( self.config['email_file_type'] == '.eml' ):
            self.emails_folder = self.config[ 'path_emails_eml' ]
        else:
            self.emails_folder = self.config[ 'path_emails_msg' ]

        self.openai_config = {
            'api_key': self.config['api_key'],
            'type_content': self.config['type_content'],
            'prompt_start': self.config['prompt'],
            'prompt_startd': self.config['promptd'],
            'prompt_starto': self.config['prompt_order'],
            'prompt_startd_order': self.config['promptd_order'],
            'minimum_key_count': self.config['minimum_key_count'],
            'max_nrquest_openai': self.config['max_nrquest_openai'],
            'email_init': self.config['email_init'],
        }

    def process_invoices_offline(self):
        self.txtEvents.clear()
        invoice_extractor = InvoiceExtractor(self.config, self.translations, self.openai_config, self.txtEvents, self)
        all_header = []
        all_detail = []
        all_headero = []
        all_detailo = []
        all_extrad = []
        n_request = 0
        start_at_email = self.config.get('email_init', 0)
        max_invoice = self.config.get('max_invoice', -1)

        files = os.listdir(self.emails_folder)
        files = [f for f in files if f.endswith('.msg') or f.endswith('.eml')]

        for i, msg_file in enumerate(files[start_at_email:]):
            if 0 <= max_invoice <= i:
                break
            try:
                file_path = os.path.join(self.emails_folder, msg_file)
                n_request, headeri_data, detaili_data, headero_data, detailo_data, extra_data = invoice_extractor.extract_data_from_file(n_request, file_path)

                for header_item in headeri_data:
                    transformed_header_data = InvoiceProcessor.transform_header_data(header_item)
                    all_header.append(transformed_header_data)

                for detail_item in detaili_data:
                    transformed_detail_data = InvoiceProcessor.transform_detail_data(detail_item)
                    all_detail.extend(transformed_detail_data)

                for header_item in headero_data:
                    transformed_headero_data = InvoiceProcessor.transform_header_data(header_item)
                    all_headero.append(transformed_headero_data)

                for detail_item in detailo_data:
                    transformed_detailo_data = InvoiceProcessor.transform_detail_data(detail_item)
                    all_detailo.extend(transformed_detailo_data)

                all_extrad.append(extra_data)

            except InvalidFileFormatError:
                self.txtEvents.insertPlainText(f"{self.translations['ui']['err1']} {msg_file}\n")

        # Guardar los resultados en un archivo de Excel
        self._save_results_to_excel(all_header, all_detail, all_headero, all_detailo, all_extrad)
        

    def _save_results_to_excel(self, all_header_data, all_detail_data,all_headero_data, all_detailo_data, all_extra_data):
        # Crear un archivo de Excel con múltiples hojas
        output_file_path = os.path.join(self.config['path_export_xls'], 'result.xlsx')

        # Inicializar DataFrames vacíos para almacenar todos los datos de cabecera, detalles y extra
        all_header_df = pd.DataFrame()
        all_detail_df = pd.DataFrame()
        all_headero_df = pd.DataFrame()
        all_detailo_df = pd.DataFrame()
        all_extra_df = pd.DataFrame()

        header_order = self.translations['invoice_header_order']
        detail_order = self.translations['invoice_detail_order']
        headero_order = self.translations['order_header_order']
        detailo_order = self.translations['order_detail_order']

        # Iterar sobre cada factura en la cabecera individualmente
        for header_data in all_header_data:
            # Crear un DataFrame de pandas con los datos y las columnas
            df_header = pd.DataFrame([header_data])

            # Añadir los nuevos datos al DataFrame acumulativo de cabecera
            all_header_df = pd.concat([all_header_df, df_header])

        # Iterar sobre cada orden en la cabecera individualmente
        for headero_data in all_headero_data:
            # Crear un DataFrame de pandas con los datos y las columnas
            df_headero = pd.DataFrame([headero_data])

            # Añadir los nuevos datos al DataFrame acumulativo de cabecera
            all_headero_df = pd.concat([all_headero_df, df_headero])

        # Iterar sobre cada detalle individualmente
        for detail_data in all_detail_data:
            df_detail = pd.DataFrame([detail_data])

            # Añadir los nuevos datos al DataFrame acumulativo de detalles
            all_detail_df = pd.concat([all_detail_df, df_detail])

        # Iterar sobre cada detalle de una orden individualmente
        for detailo_data in all_detailo_data:
            df_detailo = pd.DataFrame([detailo_data])

            # Añadir los nuevos datos al DataFrame acumulativo de detalles
            all_detailo_df = pd.concat([all_detailo_df, df_detailo])

        # Si all_extra_data es un diccionario, convertirlo en una lista de un solo elemento
        if isinstance(all_extra_data, dict):
            all_extra_data = [all_extra_data]

        # Iterar sobre cada conjunto de datos extra individualmente
        for extra_data in all_extra_data:
            df_extra = pd.DataFrame([extra_data])

            # Añadir los nuevos datos al DataFrame acumulativo de datos extra
            all_extra_df = pd.concat([all_extra_df, df_extra])

        # Crear una lista de las columnas que están tanto en all_header_df como en header_order
        cols_to_include_header = [col for col in header_order if col in all_header_df.columns]
        all_header_df = all_header_df[cols_to_include_header]

        cols_to_include_headero = [col for col in headero_order if col in all_headero_df.columns]
        all_headero_df = all_headero_df[cols_to_include_headero]

        # Crear una lista de las columnas que están tanto en all_detail_df como en detail_order
        cols_to_include_detail = [col for col in detail_order if col in all_detail_df.columns]
        all_detail_df = all_detail_df[cols_to_include_detail]

        cols_to_include_detailo = [col for col in detailo_order if col in all_detailo_df.columns]
        all_detailo_df = all_detailo_df[cols_to_include_detailo]

        # Escribir los DataFrames acumulativos en Excel
        try:
            with pd.ExcelWriter(output_file_path) as writer:
                all_header_df.to_excel(writer, sheet_name='Inv Header Dat', index=False)
                all_detail_df.to_excel(writer, sheet_name='Inv Detail Dat', index=False)
                all_headero_df.to_excel(writer, sheet_name='Ord Header Dat', index=False)
                all_detailo_df.to_excel(writer, sheet_name='Ord Detail Dat', index=False)
                all_extra_df.to_excel(writer, sheet_name='Extra Data', index=False)
        except PermissionError:
            self.txtEvents.insertPlainText(f"Error: No se pudo escribir en el archivo '{output_file_path}'. Verifica que el archivo no esté abierto en otra aplicación y que tengas permisos de escritura.\n")

        # Si no hubo errores de permisos, ajusta las columnas y las filas
        else:
            self.adjust_columns_width_and_rows_height(output_file_path)
            

    @staticmethod
    def transform_detail_data(detail_data):
        transformed_data = []
        keys = detail_data.keys()

        # Verificar si hay al menos un elemento que sea una lista antes de calcular el valor máximo
        if any(isinstance(value, list) for value in detail_data.values()):
            max_length = max(len(value) for value in detail_data.values() if isinstance(value, list))
        else:
            # Si no hay listas en los valores, devolver un objeto con los valores de entrada
            return [detail_data]

        for i in range(max_length):
            item = {}
            for key in keys:
                if isinstance(detail_data[key], list):
                    if i < len(detail_data[key]):
                        value = detail_data[key][i]

                        # Redondear valores numéricos a dos decimales
                        if key in ['Quantity', 'Price', 'Total Line', 'Confidence'] and isinstance(value, (int, float)):
                            value = round(value, 2)

                        item[key] = value
                    else:
                        item[key] = None
                else:
                    item[key] = detail_data[key]
            transformed_data.append(item)

        return transformed_data     
   
    @staticmethod
    def transform_header_data(header_data):
        transformed_data = {}
        keys = header_data.keys()

        for key in keys:
            if isinstance(header_data[key], list):
                for i, value in enumerate(header_data[key]):
                    transformed_data[f"{key}_{i + 1}"] = value
            else:
                transformed_data[key] = header_data[key]

        return transformed_data


    @staticmethod
    def load_column_name_mapping(json_filepath):
        with open(json_filepath, "r") as file:
            column_name_mapping = json.load(file)
        return column_name_mapping

    @staticmethod
    def normalize_labels(data, label_mapping):
        if isinstance(data, list):
            return [InvoiceProcessor.normalize_labels(item, label_mapping) for item in data]
        elif isinstance(data, dict):
            normalized_data = {}
            for key, value in data.items():
                normalized_key = None
                for normalized_column, possible_columns in label_mapping.items():
                    if key in possible_columns:
                        normalized_key = normalized_column
                        break
                if normalized_key is not None:
                    normalized_data[normalized_key] = value
                else:
                    normalized_data[key] = value
            return normalized_data
        else:
            raise ValueError("Invalid data type. Expected a dict or list of dicts.")



    def adjust_columns_width_and_rows_height(self, path):
        # Cargar el libro de trabajo
        book = load_workbook(path)
        
        for index, sheet in enumerate(book.worksheets):
            # Iterar sobre las columnas
            for column in sheet.columns:
                max_length = 0
                column = [cell for cell in column]
                # Encontrar el largo máximo en la columna
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                # Ajustar el ancho de la columna al máximo encontrado (con un mínimo y un máximo)
                adjusted_width = (max_length + 2) if max_length > 0 else 10
                adjusted_width = min(50, max(10, adjusted_width))  # Ajustar al rango 10-50
                sheet.column_dimensions[get_column_letter(column[0].column)].width = adjusted_width

            # Si es la última hoja, ajustar el alto de las filas y el texto
            if index == len(book.worksheets) - 1:
                # Ajustar el alto de las filas en la última hoja
                for row in sheet.iter_rows(min_row = 2):
                    sheet.row_dimensions[row[0].row].height = 200

                # Ajustar el texto en la última hoja
                for row in sheet.iter_rows():
                    for cell in row:
                        # Alinear las tres primeras columnas de manera centrada
                        if cell.column <= 3:
                            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                        
                        elif 3 < cell.column <= 8:
                            cell.alignment = Alignment(vertical="top", wrap_text=True)
                        # Ajustar las celdas en todas las otras columnas solo tienen ajuste de texto
                        else:
                            cell.alignment = Alignment(wrap_text=True)
                    
        # Guardar el libro con los cambios
        book.save(path)

