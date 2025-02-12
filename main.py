import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from optik_form_app import OptikFormApp
from license_dialog import LicenseDialog
from license_manager import LicenseManager
import logging

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

def check_license():
    """Lisans kontrolü yap"""
    try:
        license_manager = LicenseManager()
        is_valid, message = license_manager.verify_license()
        
        if not is_valid:
            # Lisans penceresi göster
            dialog = LicenseDialog()
            if dialog.exec_() == QMessageBox.Accepted:
                # Lisans girildi, tekrar kontrol et
                return check_license()
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Lisans kontrolü hatası: {str(e)}")
        QMessageBox.critical(None, "Hata", 
            "Lisans kontrolü sırasında bir hata oluştu.\n"
            f"Hata: {str(e)}")
        return False

def main():
    try:
        # QApplication'ı en başta oluştur
        app = QApplication(sys.argv)
        app.setApplicationName('Bilist co. OtoForm')
        
        # İkon ayarla
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # Lisans kontrolünü en başta yap
        if not check_license():
            logger.warning("Lisans doğrulanamadı, uygulama kapatılıyor.")
            sys.exit(1)
            
        logger.info("Lisans doğrulandı, uygulama başlatılıyor...")
        
        # Ana pencereyi oluştur
        ex = OptikFormApp()
        logger.info("Ana pencere oluşturuldu")
        ex.show()
        
        # Uygulamayı başlat
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Kritik hata: {str(e)}", exc_info=True)
        QMessageBox.critical(None, "Kritik Hata", 
            f"Uygulama başlatılırken bir hata oluştu:\n{str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 