import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt5.QtGui import QIcon
from optik_form_app import OptikFormApp
from license_dialog import LicenseDialog
from license_manager import LicenseManager
import logging
from license_checker import LicenseChecker
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

class LicenseManager:
    def __init__(self):
        self.license_file = 'license.json'
        self.checker = LicenseChecker()
        
    def check_license(self):
        """Lisans kontrolü yap"""
        try:
            # Lisans dosyasını kontrol et
            if not os.path.exists(self.license_file):
                return self.show_license_dialog()
                
            # Mevcut lisansı oku
            with open(self.license_file, 'r') as f:
                data = json.load(f)
                license_key = data.get('license_key')
                
            # Lisansı kontrol et
            success, data = self.checker.check_license(license_key)
            if success:
                remaining_days = data.get('remaining_days', 0)
                logger.info(f"Lisans geçerli. Kalan gün: {remaining_days}")
                
                # Eğer 30 günden az kaldıysa uyarı göster ama uygulamayı başlat
                if remaining_days < 30:
                    self.show_license_dialog(remaining_days)
                    return True  # Lisans geçerli olduğu için True dön
                
                return True
            else:
                logger.warning(f"Lisans hatası: {data}")
                return self.show_license_dialog()
                
        except Exception as e:
            logger.error(f"Lisans kontrolü hatası: {e}")
            return self.show_license_dialog()
    
    def show_license_dialog(self, remaining_days=None):
        """Lisans aktivasyon penceresini göster"""
        dialog = LicenseDialog(self, remaining_days)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Eğer yeni lisans aktive edildiyse True dön
            return True
            
        # İptal edilirse False dön
        return False
        
    def save_license(self, license_key):
        """Lisans bilgisini kaydet"""
        with open(self.license_file, 'w') as f:
            json.dump({'license_key': license_key}, f)

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
        
        # Önce kayıtlı lisansı kontrol et
        if not license_manager.check_license():
            # Lisans yoksa veya geçersizse lisans dialogunu göster
            dialog = LicenseDialog(license_manager)
            if not dialog.exec_():
                logger.warning("Lisans doğrulanamadı, uygulama kapatılıyor.")
                sys.exit(1)
        
        # Lisans geçerliyse devam et
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