import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtGui import QIcon
from optik_form_app import OptikFormApp
from license_dialog import LicenseDialog
from license_manager import LicenseManager
import logging
import json

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
        # QApplication'ı en başta oluştur
        app = QApplication(sys.argv)
        app.setApplicationName('Bilist co. OtoForm')
        
        # İkon ayarla
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # Lisans kontrolünü en başta yap
        license_manager = LicenseManager()
        success, message = license_manager.verify_license()
        
        if not success:
            logger.warning(f"Lisans kontrolü başarısız: {message}")
            # Lisans dialogunu göster
            dialog = LicenseDialog(license_manager)
            if not dialog.exec_():
                logger.warning("Lisans doğrulanamadı, uygulama kapatılıyor.")
                sys.exit(1)
            
            # Dialog kapandıktan sonra tekrar kontrol et
            success, message = license_manager.verify_license()
            if not success:
                logger.error(f"Lisans hala geçersiz: {message}")
                QMessageBox.critical(None, "Lisans Hatası", message)
                sys.exit(1)
        
        logger.info(f"Lisans durumu: {message}")
        
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