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
El procesador de facturas es capaz de procesar facturas en archivos `.eml` o `.msg`, extraer datos de la cabecera y detalle de las facturas y almacenarlos para su posterior análisis.

## **Clases y Métodos Principales** 👩‍💻
El proyecto incluye varias clases principales y métodos:

### `InvoiceProcessor (clase)`: 
Esta es la clase principal que maneja el procesamiento de las facturas. Coordina la extracción de datos de las facturas y la generación de informes.
![InvoiceProcessor](https://github.com/czamoraflores/Invoice_processor/assets/103855330/d4650968-e23a-4bbd-8ee5-5fa3f22b68c3)

#### `process_invoices_offline`: 
Este es el método principal de la clase InvoiceProcessor. Itera sobre todos los archivos de email en un directorio especificado, extrae los datos de las facturas de cada archivo y luego guarda esos datos en una lista.

#### `_save_results_to_excel`: 
Este método toma los datos de todas las facturas procesadas y los guarda en un archivo Excel con varias hojas. Cada hoja contiene diferentes tipos de datos: datos de cabecera de la factura, datos de detalle de la factura, datos de cabecera de la orden, datos de detalle de la orden y datos extra.

#### `transform_detail_data` y `transform_header_data`: 
Estos métodos transforman los datos de las facturas en un formato que puede ser fácilmente guardado en un archivo Excel.

#### `load_column_name_mapping` y `normalize_labels`: 
Estos métodos se encargan de normalizar los nombres de las columnas en los datos de las facturas.

#### `adjust_columns_width_and_rows_height`: 
Este método ajusta el ancho de las columnas y el alto de las filas en el archivo Excel resultante para que todos los datos sean visibles y fácilmente legibles.

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
