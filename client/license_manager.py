import hashlib
import json
import datetime
import os
import requests

class LicenseManager:
    def __init__(self):
        self.api_url = 'http://localhost:5000/api'
        self.license_file = os.path.join(
            os.path.expanduser('~/Documents/Bilist co. OtoForm'),
            '.license'
        )
        
    def get_hardware_id(self):
        system_info = f"{os.getenv('COMPUTERNAME')}_{os.getenv('PROCESSOR_IDENTIFIER')}"
        return hashlib.sha256(system_info.encode()).hexdigest()
        
    def save_license(self, license_key):
        os.makedirs(os.path.dirname(self.license_file), exist_ok=True)
        with open(self.license_file, 'w') as f:
            json.dump({'key': license_key}, f)
            
    def load_license(self):
        try:
            with open(self.license_file, 'r') as f:
                data = json.load(f)
                return data.get('key')
        except:
            return None
            
    def verify_license(self):
        try:
            license_key = self.load_license()
            if not license_key:
                return False, "Lisans bulunamadı"
                
            response = requests.post(f'{self.api_url}/verify-license', json={
                'license_key': license_key,
                'hardware_id': self.get_hardware_id()
            })
            
            data = response.json()
            if data.get('valid'):
                return True, "Lisans geçerli"
            return False, data.get('message', "Lisans geçersiz")
            
        except Exception as e:
            return False, f"Lisans kontrolü başarısız: {str(e)}"