# **Procesador de Facturas** 📚🔍
Este proyecto es un procesador de facturas desarrollado en Python, que utiliza tecnologías de procesamiento de lenguaje natural y de inteligencia artificial para analizar y extraer datos de facturas contenidas en archivos de correo electrónico. La interfaz de usuario se ha construido con PyQt5.

## Tabla de Contenidos
- [Descripción General](#descripción-general)
- [Clases y Métodos Principales](#clases-y-métodos-principales)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Contribución](#contribución)
- [Licencia](#licencia)
- [Contacto](#contacto)

## **Descripción General** 📝
El procesador de facturas es capaz de procesar facturas en archivos `.eml` o `.msg`, extraer datos de la cabecera y detalle de las facturas y almacenarlos para su posterior análisis con openAI.

## **Clases y Métodos Principales** 👩‍💻
El proyecto incluye varias clases principales y métodos:

### **1. InvoiceRetrievalWindow (Interfaz):**
Esta es la clase de la ventana principal de la aplicación. Maneja la interfaz de usuario y coordina las acciones del usuario.

   ![InvoiceRetrievalWindow UI](https://github.com/czamoraflores/Invoice_processor/assets/103855330/870b6e11-e592-4134-b8e4-91b906d96c4e)

- `__init__`: Inicializa la ventana y sus componentes. Carga las traducciones y actualiza los campos de texto con las rutas validadas.

- `open_invoice_prompts_window`: Abre la ventana de propuestas de facturas.

- `on_params_saved`: Actualiza la barra de estado cuando se guardan los parámetros.

- `save_params`: Llama al método `save_params` del gestor de la interfaz de usuario.

- Métodos para seleccionar las carpetas de archivos:
    - `choose_tesseract_folder`
    - `choose_email_eml_folder`
    - `choose_data_folder`
    - `choose_email_msg_folder`
  
- `apply_translations_to_invoice_window`: Aplica las traducciones a la interfaz de usuario de la ventana de facturas.

- Métodos para añadir elementos a los cuadros combinados (comboboxes):
    - `add_items_to_file_type_combo_box`
    - `add_items_to_content_type_combo_box`
    - `setup_language_combo_box`

- `disable_inputs`: Desactiva todas las entradas de la interfaz de usuario.

- `init_progress_dialog`: Inicializa un cuadro de diálogo de progreso.

- `update_status_bar`: Actualiza la barra de estado con un mensaje dado.

- `print_results`: Imprime los resultados en el cuadro de eventos de la interfaz de usuario.

- `update_actions_and_buttons`: Actualiza las acciones y botones en función de la validación del correo electrónico y la contraseña.

- `toggle_password_visibility`: Cambia la visibilidad de la contraseña en un campo de entrada de texto.

- `params_changed`: Habilita el botón de guardado de parámetros.

- `on_thread_finished`: Cierra el cuadro de diálogo de progreso cuando termina un hilo.

- `connect_and_retrieve_attachments_triggered`: Inicia un hilo para conectar y recuperar los adjuntos de los correos electrónicos.

- `offline_email_processing`: Procesa los correos electrónicos de forma offline utilizando la clase `InvoiceProcessor`.

- `get_params_interfaz`: Obtiene los parámetros de la interfaz de usuario para el procesamiento de facturas.

### **2. InvoicePromptsWindow (Interfaz):**
Una ventana de la interfaz de usuario que permite al usuario configurar los prompts o texto que se envian por medio de la api de openAI.

   ![InvoicePromptsWindow UI](https://github.com/czamoraflores/Invoice_processor/assets/103855330/a8f78c92-13ad-4a44-aadb-eb769e242083)

- `__init__`: Este método inicializa la ventana de indicaciones de facturas. Configura la interfaz de usuario y establece las conexiones y widgets necesarios. También conecta el botón de guardar parámetros con su correspondiente método.

- `save_params`: Guarda los parámetros de las indicaciones de facturas utilizando el método `save_params_txtprompts` de `UIManager`. Deshabilita el botón de guardar parámetros después de guardar.

- `prompt_params_changed`: Habilita el botón de guardar parámetros cuando los parámetros de las indicaciones cambian.

- `get_params_interfaz`: Obtiene los parámetros de la interfaz de usuario. Los parámetros incluyen los textos de las indicaciones para las facturas y las órdenes.

- `update_token_count`: Cuenta el número de tokens en el texto de la indicación actual. Utiliza el método `get_dynamic_max_tokens` de la clase `Utils` para hacer esto.

- `on_txtPrompt_textChanged`: Este método se activa cuando el texto en `txtPrompt` cambia. Cuenta el número de tokens en el texto actual. Si el número de tokens supera el límite permitido, restaura el texto al último texto válido y mueve el cursor a su posición anterior. También actualiza los contadores de tokens en la interfaz de usuario.

### **3. EmailUtils (Clase):**
Una clase de utilidad para manejar tareas comunes relacionadas con el procesamiento de correos electrónicos.

   ![EmailUtils](https://github.com/czamoraflores/Invoice_processor/assets/103855330/f06d620c-d628-4c5e-bd81-a241dd92471e)

- `__init__`: Este método inicializa la clase `EmailUtils` con un formato de entrada y un formato de salida.

- `convert`: Este método toma una cadena de fecha y la convierte a un objeto de fecha utilizando `datetime.strptime` con el formato de entrada establecido durante la inicialización.

- `get_email_body_content`: Este método toma el cuerpo de un mensaje y devuelve el contenido en función del tipo de datos de entrada. Si el cuerpo del mensaje es una cadena, la devuelve tal cual. Si es un diccionario, busca las claves "plain" y "html" y devuelve el contenido correspondiente. Si no es ni una cadena ni un diccionario, devuelve una cadena vacía.

- `convert_date`: Este método toma una cadena de fecha y la convierte al formato de salida especificado utilizando la función `parse` y `strftime`.

- `convert_html_to_plain_text`: Este método toma una cadena HTML y la convierte a texto sin formato utilizando la biblioteca BeautifulSoup.

- `sanitize_filename`: Este método estático recibe un nombre de archivo y elimina todos los caracteres no válidos, reemplazándolos con un guión bajo ('_').

- `validate_email_and_password`: Este método estático valida un correo electrónico y una contraseña para asegurarse de que no estén vacíos.

### **4. Utils (Clase):**
Una clase de utilidad para realizar varias tareas, como la manipulación de tokens y la gestión de archivos.

### **5. InvoiceProcessor (Clase):**
Esta es la clase principal que maneja el procesamiento de las facturas. Coordina la extracción de datos de las facturas y la generación de informes.

   ![InvoiceProcessor](https://github.com/czamoraflores/Invoice_processor/assets/103855330/d4650968-e23a-4bbd-8ee5-5fa3f22b68c3)

#### **Métodos de la Clase InvoiceProcessor:**

- `process_invoices_offline`: Este es el método principal de la clase InvoiceProcessor. Itera sobre todos los archivos de email en un directorio especificado, extrae los datos de las facturas de cada archivo y luego guarda esos datos en una lista.

- `_save_results_to_excel`: Este método toma los datos de todas las facturas procesadas y los guarda en un archivo Excel con varias hojas. Cada hoja contiene diferentes tipos de datos: datos de cabecera de la factura, datos de detalle de la factura, datos de cabecera de la orden, datos de detalle de la orden y datos extra.

- `transform_detail_data` y `transform_header_data`: Estos métodos transforman los datos de las facturas en un formato que puede ser fácilmente guardado en un archivo Excel.

- `load_column_name_mapping` y `normalize_labels`: Estos métodos se encargan de normalizar los nombres de las columnas en los datos de las facturas.

- `adjust_columns_width_and_rows_height`: Este método ajusta el ancho de las columnas y el alto de las filas en el archivo Excel resultante para que todos los datos sean visibles y fácilmente legibles.
Este formato debería funcionar bien en GitHub y proporcionar una descripción detallada de las clases y métodos principales de tu proyecto.

### **6. TextProcessor (Clase):**
Una clase de utilidad diseñada para manejar tareas comunes relacionadas con el procesamiento de texto y JSON.

- `__init__`: Inicializa la clase `TextProcessor` con un conjunto de traducciones.

- `split_text_into_segments`: Divide un texto en segmentos basándose en un número máximo de tokens.

- `is_date`: (Continuar con la descripción del método...)

## **Requisitos** 📋
Para utilizar este proyecto, necesitarás lo siguiente:

- Python 3.7 o superior
- PyQt5
- tiktoken
- BeautifulSoup
- dateutil
- openpyxl
- pandas

## **Instalación** 💻
Para instalar este proyecto, sigue estos pasos:

1. Clona este repositorio en tu máquina local usando https://github.com/czamoraflores/REPOSITORY.git.
2. Navega a la carpeta del proyecto.
3. Instala los requisitos utilizando pip:
   ```shell
   pip install -r requirements.txt
## **Uso** 🖥️
Para usar este proyecto, sigue estos pasos:

1. Navega a la carpeta del proyecto.
2. Ejecuta el script principal con el comando `python main.py`.

   ![Uso](https://github.com/czamoraflores/Invoice_processor/assets/103855330/5c5c1689-1ef7-4313-ba97-140e4789b988)

   Aparecerá la ventana de la aplicación. Desde aquí, puedes cargar archivos de correo electrónico para el procesamiento de facturas, ajustar la configuración según tus necesidades y comenzar el proceso de extracción de facturas.

## **Contribución** 🤝
Las contribuciones son siempre bienvenidas. Por favor, lee el documento `CONTRIBUTING.md` para detalles sobre nuestro código de conducta, y el proceso de enviar pull requests.

## **Licencia** 📜
Este proyecto está licenciado bajo la Licencia MIT - vea el archivo `LICENSE.md` para más detalles.

## **Contacto** ✉️
Si tienes alguna pregunta sobre este proyecto, por favor no dudes en contactar.
