from views.invoice_retrieval_form.InvoiceRetrievalWindow import InvoiceRetrievalWindow
from PyQt5.QtWidgets import QApplication
import sys

class AppController: 
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = InvoiceRetrievalWindow()

    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())