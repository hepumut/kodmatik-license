from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QFrame, QWidget, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor, QPainter
import webbrowser
import json
import os
from datetime import datetime

class LicenseDialog(QDialog):
    def __init__(self, license_manager, remaining_days=None, parent=None):
        super().__init__(parent)
        self.license_manager = license_manager
        self.remaining_days = remaining_days
        self.license_file = os.path.join(
            os.path.expanduser('~/Documents/Bilist co. OtoForm'),
            '.license'
        )
        
        # Önce kayıtlı lisansı kontrol et
        if self.check_saved_license():
            self.accept()
            return
            
        self.setWindowTitle("Bilist OtoForm - Lisans Yönetimi")
        self.setFixedSize(600, 600)
        
        # Ana layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # İçerik widget'ı (ScrollArea olmadan)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(15)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Arka plan ve stiller
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
                background: transparent;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QPushButton#activateBtn {
                background-color: #4CAF50;
                color: white;
                padding: 5px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#activateBtn:hover {
                background-color: #45a049;
            }
            QPushButton#buyBtn {
                background-color: #2196F3;
                color: white;
                padding: 5px 20px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#buyBtn:hover {
                background-color: #1E88E5;
            }
        """)
        
        self.setup_ui(content_widget)
        
        # Widget'ı doğrudan ana layout'a ekle
        self.main_layout.addWidget(content_widget)
        
    def check_saved_license(self):
        """Kayıtlı lisansı kontrol et"""
        try:
            if os.path.exists(self.license_file):
                with open(self.license_file, 'r') as f:
                    data = json.load(f)
                    license_key = data.get('license_key')
                    
                    # Lisansı kontrol et
                    success, response = self.license_manager.checker.check_license(license_key)
                    if success:
                        remaining_days = response.get('remaining_days', 0)
                        if remaining_days > 0:
                            # Eğer 30 günden az kaldıysa uyarı göster
                            if remaining_days < 30:
                                QMessageBox.warning(self, 
                                    "Lisans Uyarısı",
                                    f"Lisans sürenizin bitmesine {remaining_days} gün kaldı.\n"
                                    "Lisansınızı yenilemek için lütfen bizimle iletişime geçin.",
                                    QMessageBox.Ok)
                            return True
                            
                    # Lisans geçersizse dosyayı sil
                    os.remove(self.license_file)
                    
            return False
            
        except Exception as e:
            print(f"Lisans kontrolü hatası: {e}")
            return False
            
    def save_license(self, license_key):
        """Lisans anahtarını kaydet"""
        try:
            # Klasörü oluştur
            os.makedirs(os.path.dirname(self.license_file), exist_ok=True)
            
            # Lisans bilgilerini kaydet
            with open(self.license_file, 'w') as f:
                json.dump({
                    'license_key': license_key,
                    'created_at': datetime.now().isoformat()
                }, f)
                
        except Exception as e:
            print(f"Lisans kaydetme hatası: {e}")
    
    def setup_ui(self, parent):
        # Logo ve başlık
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        logo_label = QLabel()
        logo_pixmap = QPixmap("icon.ico")
        logo_label.setPixmap(logo_pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)
        
        title_label = QLabel("Bilist OtoForm\nLisans Aktivasyonu")
        title_font = QFont("Segoe UI", 20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1976D2;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.content_layout.addLayout(header_layout)
        
        # Ayırıcı çizgi
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0;")
        self.content_layout.addWidget(line)
        
        # Bilgi metni
        info_label = QLabel()
        info_label.setTextFormat(Qt.RichText)
        info_label.setOpenExternalLinks(True)
        info_label.setWordWrap(True)
        info_label.setText("""
        <div style='font-family: "Segoe UI", sans-serif;'>
            <p style='font-size: 15px; color: #424242;'>
                Bilist OtoForm'u kullanmak için geçerli bir lisans anahtarı gereklidir.
                Lisans satın almak için <a href='http://www.bilistco.com/otoform' style='color: #1976D2; text-decoration: none;'>www.bilistco.com/otoform</a> adresini ziyaret edin.
            </p>
            <p style='font-size: 16px; font-weight: bold; color: #1976D2; margin-top: 20px;'>Özellikler:</p>
            <ul style='color: #424242; font-size: 14px;'>
                <li>Optik form tasarlama ve düzenleme</li>
                <li>Excel ile öğrenci verisi yükleme</li>
                <li>PDF olarak kaydedebilme</li>
            </ul>
        </div>
        """)
        self.content_layout.addWidget(info_label)
        
        # Lisans giriş alanı
        input_layout = QHBoxLayout()
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Lisans anahtarınızı girin")
        self.license_input.setMinimumHeight(45)
        input_layout.addWidget(self.license_input)
        
        activate_btn = QPushButton("Aktive Et")
        activate_btn.setObjectName("activateBtn")
        activate_btn.setMinimumHeight(45)
        activate_btn.setCursor(Qt.PointingHandCursor)
        activate_btn.clicked.connect(self.activate_license)
        input_layout.addWidget(activate_btn)
        
        self.content_layout.addLayout(input_layout)
        
        # Satın alma butonu
        buy_btn = QPushButton("Lisans Satın Al")
        buy_btn.setObjectName("buyBtn")
        buy_btn.setMinimumHeight(45)
        buy_btn.setCursor(Qt.PointingHandCursor)
        buy_btn.clicked.connect(lambda: webbrowser.open('http://www.bilistco.com/otoform'))
        self.content_layout.addWidget(buy_btn)
        
        # İletişim bilgileri
        contact_label = QLabel()
        contact_label.setAlignment(Qt.AlignCenter)
        contact_label.setText("""
        <div style='text-align: center; font-family: "Segoe UI", sans-serif;'>
            <p style='color: #666; font-size: 12px; margin: 10px 0;'>
                <b>Destek ve İletişim</b><br>
                E-posta: info@bilistco.com<br>
                Tel: +90 505 498 51 94<br>
                <span style='font-size: 11px; color: #888;'>
                    Çalışma Saatleri: Hafta içi 09:00 - 18:00
                </span>
            </p>
        </div>
        """)
        self.content_layout.addWidget(contact_label)
        
    def activate_license(self):
        """Lisans aktivasyonu"""
        license_key = self.license_input.text().strip()
        if not license_key:
            QMessageBox.warning(self, "Hata", 
                              "Lütfen lisans anahtarı girin!", 
                              QMessageBox.Ok)
            return
            
        success, data = self.license_manager.checker.activate_license(license_key)
        if success:
            # Lisansı kaydet
            self.save_license(license_key)
            QMessageBox.information(self, "Başarılı", 
                                  "Lisans başarıyla aktive edildi!", 
                                  QMessageBox.Ok)
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", 
                              f"Lisans aktivasyon hatası: {data}", 
                              QMessageBox.Ok) 