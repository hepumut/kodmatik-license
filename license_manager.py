import hashlib
import json
import datetime
from cryptography.fernet import Fernet
import os
import requests
import base64

class LicenseManager:
    def __init__(self):
        # Güvenli bir şifreleme anahtarı oluştur
        self.key = base64.urlsafe_b64encode(b'bilistotoform2024secretkeylicense12345'[:32].ljust(32, b'0'))
        self.cipher_suite = Fernet(self.key)
        self.license_file = os.path.join(
            os.path.expanduser('~/Documents/Bilist co. OtoForm'),
            '.license'
        )
    
    def get_hardware_id(self):
        """Benzersiz donanım ID'si oluştur"""
        system_info = f"{os.getenv('COMPUTERNAME')}_{os.getenv('PROCESSOR_IDENTIFIER')}"
        return hashlib.sha256(system_info.encode()).hexdigest()
    
    def save_license(self, license_key):
        """Lisans anahtarını kaydet"""
        try:
            # Lisans verilerini hazırla
            license_data = {
                'key': license_key,
                'hardware_id': self.get_hardware_id(),
                'expiry_date': (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat(),
                'created_at': datetime.datetime.now().isoformat()
            }
            
            # Verileri şifrele
            encrypted_data = self.cipher_suite.encrypt(
                json.dumps(license_data).encode()
            )
            
            # Klasörü oluştur (yoksa)
            os.makedirs(os.path.dirname(self.license_file), exist_ok=True)
            
            # Lisans dosyasını kaydet
            with open(self.license_file, 'wb') as f:
                f.write(encrypted_data)
                
        except Exception as e:
            raise Exception(f"Lisans kaydedilemedi: {str(e)}")
    
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