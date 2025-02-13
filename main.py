import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtGui import QIcon
from optik_form_app import OptikFormApp
from license_dialog import LicenseDialog
from license_manager import LicenseManager
import logging
import json
from PyQt5.QtCore import QTimer

# Log dosyası için kullanıcının belgeler klasörünü kullan
documents_path = os.path.expanduser('~/Documents/Bilist co. OtoForm')
if not os.path.exists(documents_path):
    os.makedirs(documents_path)

log_file = os.path.join(documents_path, 'debug.log')

# Logging ayarlarını yapılandır
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        # QApplication'ı oluştur
        app = QApplication(sys.argv)
        app.setApplicationName('Bilist co. OtoForm')
        
        # Temel stil tanımlamaları
        app.setStyle('Fusion')
        
        # İkon ayarla (gecikmeli)
        QTimer.singleShot(0, lambda: set_application_icon(app))
        
        # Lisans kontrolü
        license_manager = LicenseManager()
        if not license_manager.check_license():
            dialog = LicenseDialog(license_manager)
            if not dialog.exec_():
                sys.exit(1)
        
        # Ana pencereyi oluştur
        ex = OptikFormApp()
        ex.show()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        QMessageBox.critical(None, "Kritik Hata", 
            f"Uygulama başlatılırken bir hata oluştu:\n{str(e)}")
        sys.exit(1)

def set_application_icon(app):
    """İkonu gecikmeli yükle"""
    try:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        print(f"İkon yüklenirken hata: {e}")

if __name__ == '__main__':
    main() 