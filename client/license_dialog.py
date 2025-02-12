from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox)
from license_manager import LicenseManager

class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_manager = LicenseManager()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Lisans Aktivasyonu")
        self.setMinimumWidth(400)
        layout = QVBoxLayout()
        
        # Donanım ID
        hw_id = self.license_manager.get_hardware_id()
        layout.addWidget(QLabel(f"Donanım ID: {hw_id[:16]}..."))
        
        # Lisans giriş alanı
        layout.addWidget(QLabel("Lisans Anahtarı:"))
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        layout.addWidget(self.key_input)
        
        # Aktivasyon butonu
        activate_btn = QPushButton("Aktivasyon")
        activate_btn.clicked.connect(self.activate_license)
        layout.addWidget(activate_btn)
        
        self.setLayout(layout)
        
    def activate_license(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Hata", "Lütfen lisans anahtarı girin")
            return
            
        try:
            self.license_manager.save_license(key)
            is_valid, message = self.license_manager.verify_license()
            
            if is_valid:
                QMessageBox.information(self, "Başarılı", "Lisans aktivasyonu başarılı")
                self.accept()
            else:
                QMessageBox.warning(self, "Hata", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Aktivasyon başarısız: {str(e)}")