from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor
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
        self.setFixedSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
        """)
        self.setup_ui()
        
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
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo ve başlık
        header_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_pixmap = QPixmap("icon.ico")
        logo_label.setPixmap(logo_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)
        
        title_label = QLabel("Bilist OtoForm\nLisans Aktivasyonu")
        title_font = QFont("Segoe UI", 24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1976D2;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Ayırıcı çizgi
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(line)
        
        # Bilgi metni
        info_text = """
        <div style='font-family: "Segoe UI", sans-serif;'>
            <p style='font-size: 15px; color: #424242;'>
                Bilist OtoForm'u kullanmak için geçerli bir lisans anahtarı gereklidir.
                Lisans satın almak için <a href='http://www.bilistco.com/otoform' style='color: #1976D2; text-decoration: none;'>www.bilistco.com/otoform</a> adresini ziyaret edin.
            </p>
            <p style='font-size: 16px; font-weight: bold; color: #1976D2; margin-top: 20px;'>Özellikler:</p>
            <ul style='color: #424242; font-size: 14px;'>
                <li>Optik form tasarlama ve düzenleme</li>
                <li>Otomatik form okuma ve değerlendirme</li>
                <li>Excel ve PDF raporlama</li>
                <li>Toplu form işleme</li>
                <li>Sınırsız form okuma</li>
                <li>1 yıl ücretsiz güncelleme</li>
                <li>Teknik destek</li>
            </ul>
        </div>
        """
        info_label = QLabel(info_text)
        info_label.setOpenExternalLinks(True)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Eğer kalan gün sayısı varsa göster
        if self.remaining_days is not None:
            remaining_label = QLabel(f"""
            <div style='text-align: center; background-color: #E8F5E9; padding: 10px; border-radius: 6px;'>
                <p style='color: #2E7D32; font-size: 14px; margin: 0;'>
                    <b>Lisans Durumu:</b> Aktif<br>
                    Kalan Süre: {self.remaining_days} gün
                </p>
            </div>
            """)
            layout.addWidget(remaining_label)

        # Lisans giriş alanı - sadece lisans yoksa göster
        if self.remaining_days is None:
            input_layout = QHBoxLayout()
            self.license_input = QLineEdit()
            self.license_input.setPlaceholderText("Lisans anahtarınızı girin")
            self.license_input.setMinimumHeight(45)
            input_layout.addWidget(self.license_input)
            
            activate_btn = QPushButton("Aktive Et")
            activate_btn.setMinimumHeight(45)
            activate_btn.setCursor(Qt.PointingHandCursor)
            activate_btn.clicked.connect(self.activate_license)
            activate_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 5px 30px;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #43A047;
                }
                QPushButton:pressed {
                    background-color: #388E3C;
                }
            """)
            input_layout.addWidget(activate_btn)
            layout.addLayout(input_layout)
        
        # Satın alma butonu - sadece lisans yoksa veya süresi azsa göster
        if self.remaining_days is None or self.remaining_days < 30:
            buy_btn = QPushButton("Lisans Satın Al")
            buy_btn.setMinimumHeight(45)
            buy_btn.setCursor(Qt.PointingHandCursor)
            buy_btn.clicked.connect(lambda: webbrowser.open('http://www.bilistco.com/otoform'))
            buy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 5px 30px;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1E88E5;
                }
                QPushButton:pressed {
                    background-color: #1976D2;
                }
            """)
            layout.addWidget(buy_btn)
        
        # İletişim bilgileri
        contact_label = QLabel("""
        <div style='text-align: center; font-family: "Segoe UI", sans-serif;'>
            <p style='color: #666; font-size: 13px; margin: 20px 0;'>
                <b>Destek ve İletişim</b><br>
                E-posta: info@bilistco.com<br>
                Tel: +90 505 498 51 94<br>
                <span style='font-size: 12px; color: #888;'>
                    Çalışma Saatleri: Hafta içi 09:00 - 18:00
                </span>
            </p>
        </div>
        """)
        contact_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(contact_label)
        
        self.setLayout(layout)
        
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