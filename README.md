# Proyecto: Procesador de Facturas
Este proyecto es un procesador de facturas desarrollado en Python, que utiliza tecnologías de procesamiento de lenguaje natural y de inteligencia artificial para analizar y extraer datos de facturas contenidas en archivos de correo electrónico. La interfaz de usuario se ha construido con PyQt5.

# Descripción General
El procesador de facturas es capaz de procesar facturas en archivos .eml o .msg, extraer datos de la cabecera y detalle de las facturas y almacenarlos para su posterior análisis. Este proyecto incluye varias clases principales:

## InvoiceRetrievalWindow (interfaz): 
Esta es la clase de la ventana principal de la aplicación. Maneja la interfaz de usuario y coordina las acciones del usuario.

![image](https://github.com/czamoraflores/Invoice_processor/assets/103855330/870b6e11-e592-4134-b8e4-91b906d96c4e)

A continuación una descripción de las partes clave del código:

### Importaciones: 
El código importa una serie de módulos necesarios, como os para la interacción con el sistema operativo, QFileDialog para abrir cuadros de diálogo de archivos, QLineEdit para campos de entrada de texto, QGroupBox para agrupar elementos de interfaz de usuario, QStatusBar para mostrar información de estado, QProgressDialog para mostrar una barra de progreso, loadUi para cargar interfaces de usuario de archivos .ui, Qt para constantes de Qt, y varios módulos de controladores, vistas, gestores y utilidades específicos del proyecto.

### Inicialización y configuración de la ventana: 
En el método __init__, se inicializan y configuran varios elementos de la interfaz de usuario, incluyendo la carga de la interfaz de usuario desde un archivo .ui, la configuración de las traducciones, la validación y actualización de las rutas de los cuadros de texto, la configuración de la barra de estado, y la configuración de los cuadros de combinación.

### Gestión de eventos: 
Se proporcionan varios métodos para manejar los eventos de la interfaz de usuario, como abrir la ventana de indicaciones de factura (open_invoice_prompts_window), guardar parámetros (save_params), elegir carpetas para varios propósitos (choose_tesseract_folder, choose_email_eml_folder, choose_data_folder, choose_email_msg_folder), y aplicar traducciones (apply_translations_to_invoice_window).

### Manipulación de cuadros de combinación: 
Los métodos add_items_to_file_type_combo_box, add_items_to_content_type_combo_box, y setup_language_combo_box añaden elementos a los cuadros de combinación y establecen los valores por defecto.

### Gestión de la interfaz de usuario: 
Métodos como disable_inputs, init_progress_dialog, update_status_bar, print_results, update_actions_and_buttons, toggle_password_visibility, y params_changed se encargan de actualizar la interfaz de usuario en respuesta a varios eventos.

### Procesamiento de correos: 
Los métodos connect_and_retrieve_attachments_triggered y offline_email_processing se encargan de la conexión y recuperación de adjuntos de correo y del procesamiento de correos en línea y fuera de línea.

### Obtención de parámetros de la interfaz: 
El método get_params_interfaz recoge los parámetros de la interfaz de usuario para su uso en el procesamiento de correos.

## InvoicePromptsWindow (interfaz): 
Una ventana de la interfaz de usuario que permite al usuario configurar las solicitudes de facturas.

![image](https://github.com/czamoraflores/Invoice_processor/assets/103855330/a8f78c92-13ad-4a44-aadb-eb769e242083)

## EmailUtils (clase): 
Una clase de utilidad para manejar tareas comunes relacionadas con el procesamiento de correos electrónicos.

![image](https://github.com/czamoraflores/Invoice_processor/assets/103855330/f06d620c-d628-4c5e-bd81-a241dd92471e)

## Utils (clase): 
Una clase de utilidad para realizar varias tareas, como la manipulación de tokens y la gestión de archivos.

## InvoiceProcessor (clase): 
Esta es la clase principal que maneja el procesamiento de las facturas. Coordina la extracción de datos de las facturas y la generación de informes.

![image](https://github.com/czamoraflores/Invoice_processor/assets/103855330/d4650968-e23a-4bbd-8ee5-5fa3f22b68c3)

### process_invoices_offline: 
Este es el método principal de la clase InvoiceProcessor. Itera sobre todos los archivos de email en un directorio especificado, extrae los datos de las facturas de cada archivo y luego guarda esos datos en una lista.

### _save_results_to_excel: 
Este método toma los datos de todas las facturas procesadas y los guarda en un archivo Excel con varias hojas. Cada hoja contiene diferentes tipos de datos: datos de cabecera de la factura, datos de detalle de la factura, datos de cabecera de la orden, datos de detalle de la orden y datos extra.

### transform_detail_data y transform_header_data: 
Estos métodos transforman los datos de las facturas en un formato que puede ser fácilmente guardado en un archivo Excel.

### load_column_name_mapping y normalize_labels: 
Estos métodos se encargan de normalizar los nombres de las columnas en los datos de las facturas.

### adjust_columns_width_and_rows_height: 
Este método ajusta el ancho de las columnas y el alto de las filas en el archivo Excel resultante para que todos los datos sean visibles y fácilmente legibles.

# Requisitos
Para utilizar este proyecto, necesitarás lo siguiente:

Python 3.7 o superior
PyQt5
tiktoken
BeautifulSoup
dateutil
openpyxl
pandas

# Instalación
Para instalar este proyecto, sigue estos pasos:

Clona este repositorio en tu máquina local usando https://github.com/czamoraflores/REPOSITORY.git.
Navega a la carpeta del proyecto.
Instala los requisitos utilizando pip:
Copy code
pip install -r requirements.txt

# Uso
Para usar este proyecto, sigue estos pasos:

Navega a la carpeta del proyecto.
Ejecuta el script principal con el comando python main.py.

![image](https://github.com/czamoraflores/Invoice_processor/assets/103855330/5c5c1689-1ef7-4313-ba97-140e4789b988)

Aparecerá la ventana de la aplicación. Desde aquí, puedes cargar archivos de correo electrónico para el procesamiento de facturas, ajustar la configuración según tus necesidades y comenzar el proceso de extracción de facturas.

# Contribución
Las contribuciones son siempre bienvenidas. Por favor, lee el documento CONTRIBUTING.md para detalles sobre nuestro código de conducta, y el proceso de enviar pull requests.

# Licencia
Este proyecto está licenciado bajo la Licencia MIT - vea el archivo LICENSE.md para más detalles.

# Contacto
Si tienes alguna pregunta sobre este proyecto, por favor no dudes en contactar.
