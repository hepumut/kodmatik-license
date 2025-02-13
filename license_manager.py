import hashlib
import json
import datetime
from cryptography.fernet import Fernet
import os
import requests
import base64

class LicenseManager:
    def __init__(self):
        self.license_file = os.path.join(
            os.path.expanduser('~/Documents/Bilist co. OtoForm'),
            '.license'
        )
        self.checker = LicenseChecker()
    
    def check_license(self):
        """Lisans kontrolü yap"""
        try:
            # Lisans dosyasını kontrol et
            if not os.path.exists(self.license_file):
                return False
                
            # Mevcut lisansı oku
            with open(self.license_file, 'r') as f:
                data = json.load(f)
                license_key = data.get('license_key')
                
            # Lisansı kontrol et
            success, response = self.checker.check_license(license_key)
            if success:
                remaining_days = response.get('remaining_days', 0)
                if remaining_days > 0:
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
        """Lisansı kontrol et"""
        try:
            if not os.path.exists(self.license_file):
                return False, "Lisans bulunamadı"
            
            with open(self.license_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            license_data = json.loads(decrypted_data)
            
            # Donanım ID kontrolü
            if license_data['hardware_id'] != self.get_hardware_id():
                return False, "Lisans başka bir cihaza ait"
            
            # Süre kontrolü
            expiry_date = datetime.datetime.fromisoformat(license_data['expiry_date'])
            if datetime.datetime.now() > expiry_date:
                return False, "Lisans süresi dolmuş"
            
            # Online doğrulama
            try:
                response = requests.post('http://localhost:5000/api/verify-license', json={
                    'license_key': license_data['key'],
                    'hardware_id': license_data['hardware_id']
                })
                data = response.json()
                if not data.get('valid'):
                    return False, data.get('message', "Lisans doğrulanamadı")
            except:
                # Sunucuya erişilemezse offline modda devam et
                pass
            
            return True, "Lisans geçerli"
            
        except Exception as e:
            return False, f"Lisans kontrolü başarısız: {str(e)}" 