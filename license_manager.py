import hashlib
import json
import datetime
from cryptography.fernet import Fernet
import os
import requests
import base64
from license_checker import LicenseChecker

class LicenseManager:
    def __init__(self):
        self.license_file = os.path.join(
            os.path.expanduser('~/Documents/Bilist co. OtoForm'),
            '.license'
        )
        self.checker = LicenseChecker()
    
    def check_license(self):
        """Lisansı kontrol et"""
        try:
            if not os.path.exists(self.license_file):
                return False, "Lisans bulunamadı"
            
            with open(self.license_file, 'r') as f:
                data = json.load(f)
                license_key = data.get('license_key')
                
                # Lisansı kontrol et
                success, response = self.checker.check_license(license_key)
                if not success:
                    return False, "Lisans doğrulanamadı"
                
                remaining_days = response.get('remaining_days', 0)
                if remaining_days <= 0:
                    # Lisans süresini kontrol et ama dosyayı silme
                    return False, "Lisans süresi dolmuş"
                
                return True, f"Lisans geçerli. Kalan gün: {remaining_days}"
                
        except Exception as e:
            print(f"Lisans kontrolü hatası: {e}")
            return False, f"Lisans kontrolü başarısız: {str(e)}"
    
    def save_license(self, license_key):
        """Lisans anahtarını kaydet"""
        try:
            # Klasörü oluştur
            os.makedirs(os.path.dirname(self.license_file), exist_ok=True)
            
            # Lisans bilgilerini kaydet
            with open(self.license_file, 'w') as f:
                json.dump({
                    'license_key': license_key,
                    'created_at': datetime.datetime.now().isoformat()
                }, f)
                
            return True
        except Exception as e:
            print(f"Lisans kaydetme hatası: {e}")
            return False

    def get_license_info(self):
        """Mevcut lisans bilgilerini getir"""
        try:
            if os.path.exists(self.license_file):
                with open(self.license_file, 'r') as f:
                    data = json.load(f)
                    license_key = data.get('license_key')
                    
                    success, response = self.checker.check_license(license_key)
                    if success:
                        return response
                        
            return None
        except Exception as e:
            print(f"Lisans bilgisi alma hatası: {e}")
            return None

    def get_hardware_id(self):
        """Benzersiz donanım ID'si oluştur"""
        system_info = f"{os.getenv('COMPUTERNAME')}_{os.getenv('PROCESSOR_IDENTIFIER')}"
        return hashlib.sha256(system_info.encode()).hexdigest()
    
    def verify_license(self):
        """Lisansı kontrol et ve durum mesajı döndür"""
        try:
            if not os.path.exists(self.license_file):
                return False, "Lisans bulunamadı"
            
            with open(self.license_file, 'r') as f:
                data = json.load(f)
                license_key = data.get('license_key')
                if not license_key:
                    return False, "Geçersiz lisans dosyası"
            
            success, response = self.checker.check_license(license_key)
            if not success:
                return False, "Lisans doğrulanamadı"
            
            remaining_days = response.get('remaining_days', 0)
            if remaining_days <= 0:
                try:
                    os.remove(self.license_file)
                except:
                    pass
                return False, "Lisans süresi dolmuş"
            
            return True, f"Lisans geçerli. Kalan gün: {remaining_days}"
            
        except Exception as e:
            print(f"Lisans kontrolü hatası: {e}")  # Hata logla
            return False, f"Lisans kontrolü başarısız: {str(e)}" 