# Proyecto: Procesador de Facturas
Este proyecto es un procesador de facturas desarrollado en Python, que utiliza tecnologías de procesamiento de lenguaje natural y de inteligencia artificial para analizar y extraer datos de facturas contenidas en archivos de correo electrónico. La interfaz de usuario se ha construido con PyQt5.

# Descripción General
El procesador de facturas es capaz de procesar facturas en archivos .eml o .msg, extraer datos de la cabecera y detalle de las facturas y almacenarlos para su posterior análisis. Este proyecto incluye varias clases principales:

## InvoiceRetrievalWindow: Esta es la clase de la ventana principal de la aplicación. Maneja la interfaz de usuario y coordina las acciones del usuario.
## InvoicePromptsWindow: Una ventana de la interfaz de usuario que permite al usuario configurar las solicitudes de facturas.
## EmailUtils: Una clase de utilidad para manejar tareas comunes relacionadas con el procesamiento de correos electrónicos.
## Utils: Una clase de utilidad para realizar varias tareas, como la manipulación de tokens y la gestión de archivos.
## InvoiceProcessor: Esta es la clase principal que maneja el procesamiento de las facturas. Coordina la extracción de datos de las facturas y la generación de informes.

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
Aparecerá la ventana de la aplicación. Desde aquí, puedes cargar archivos de correo electrónico para el procesamiento de facturas, ajustar la configuración según tus necesidades y comenzar el proceso de extracción de facturas.

# Contribución
Las contribuciones son siempre bienvenidas. Por favor, lee el documento CONTRIBUTING.md para detalles sobre nuestro código de conducta, y el proceso de enviar pull requests.

# Licencia
Este proyecto está licenciado bajo la Licencia MIT - vea el archivo LICENSE.md para más detalles.

# Contacto
Si tienes alguna pregunta sobre este proyecto, por favor no dudes en contactar.
