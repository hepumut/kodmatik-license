from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QMessageBox, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap
from license_manager import LicenseManager
import datetime
import webbrowser

class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_manager = LicenseManager()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Bilist co. OtoForm - Lisans Aktivasyonu")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#activateBtn {
                background-color: #4CAF50;
                color: white;
                border: none;
            }
            QPushButton#activateBtn:hover {
                background-color: #45a049;
            }
            QPushButton#cancelBtn {
                background-color: #f44336;
                color: white;
                border: none;
            }
            QPushButton#cancelBtn:hover {
                background-color: #da190b;
            }
            QPushButton#buyBtn {
                background-color: #2196F3;
                color: white;
                border: none;
            }
            QPushButton#buyBtn:hover {
                background-color: #1976D2;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Logo ve başlık
        header = QHBoxLayout()
        logo_label = QLabel()
        logo_pixmap = QPixmap("icon.ico").scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        header.addWidget(logo_label)
        
        title = QLabel("Bilist co. OtoForm\nLisans Aktivasyonu")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Bilgi mesajı
        info = QLabel(
            "Bu uygulama lisans gerektirir. Lütfen lisans anahtarınızı girin veya "
            "yeni bir lisans satın alın.\n\n"
            "• Tek bilgisayar için lisans\n"
            "• 1 yıl süreyle geçerli\n"
            "• Ücretsiz güncellemeler\n"
            "• Teknik destek"
        )
        info.setWordWrap(True)
        info.setFont(QFont("Arial", 11))
        layout.addWidget(info)
        
        # Donanım ID
        hw_id = self.license_manager.get_hardware_id()
        hw_label = QLabel(f"Donanım ID: {hw_id[:16]}...")
        hw_label.setFont(QFont("Arial", 10))
        hw_label.setStyleSheet("color: #666;")
        layout.addWidget(hw_label)
        
        # Lisans giriş alanı
        license_layout = QHBoxLayout()
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.key_input.setFont(QFont("Arial", 12))
        license_layout.addWidget(self.key_input)
        
        activate_btn = QPushButton("Aktivasyon")
        activate_btn.setObjectName("activateBtn")
        activate_btn.clicked.connect(self.activate_license)
        license_layout.addWidget(activate_btn)
        layout.addLayout(license_layout)
        
        # Butonlar
        button_layout = QHBoxLayout()
        
        buy_btn = QPushButton("Lisans Satın Al")
        buy_btn.setObjectName("buyBtn")
        buy_btn.clicked.connect(self.buy_license)
        button_layout.addWidget(buy_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("İptal")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Alt bilgi
        footer = QLabel("Teknik destek: destek@bilistco.com")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #666;")
        layout.addWidget(footer)
        
        self.setLayout(layout)
    
    def activate_license(self):
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Hata", 
                "Lütfen lisans anahtarı girin",
                QMessageBox.Ok)
            return
            
        try:
            self.license_manager.save_license(key)
            is_valid, message = self.license_manager.verify_license()
            
            if is_valid:
                QMessageBox.information(self, "Başarılı", 
                    "Lisans aktivasyonu başarılı.\n"
                    "Uygulamayı kullanmaya başlayabilirsiniz.",
                    QMessageBox.Ok)
                self.accept()
            else:
                QMessageBox.warning(self, "Hata", 
                    f"Lisans geçersiz:\n{message}\n\n"
                    "Lütfen geçerli bir lisans anahtarı girin.",
                    QMessageBox.Ok)
                
        except Exception as e:
            QMessageBox.critical(self, "Hata", 
                f"Aktivasyon başarısız:\n{str(e)}",
                QMessageBox.Ok)
    
    def buy_license(self):
        webbrowser.open('https://www.bilistco.com/otoform/satin-al') 