import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
import hashlib

from server.app import generate_license_key

# Yolları düzelt
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
ADMIN_DIR = os.path.join(TEMPLATE_DIR, 'admin')
DB_PATH = os.path.join(BASE_DIR, 'instance', 'licenses.db')

app = Flask(__name__)
app.template_folder = TEMPLATE_DIR

# Veritabanı yapılandırması
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{DB_PATH}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'bilist-secret-key-2024')

# Debug'ı kapat
app.debug = False

db = SQLAlchemy(app)

# Veritabanı modelleri
class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(64), unique=True, nullable=False)
    hardware_id = db.Column(db.String(64))
    expiry_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    activation_count = db.Column(db.Integer, default=0)
    license_type = db.Column(db.String(32))
    customer_name = db.Column(db.String(128))
    customer_email = db.Column(db.String(128))
    notes = db.Column(db.Text)

class LicenseActivation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    license_id = db.Column(db.Integer, db.ForeignKey('license.id'))
    hardware_id = db.Column(db.String(64))
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

# API rotaları
@app.route('/api/generate-license', methods=['POST'])
def generate_license():
    """Yeni lisans anahtarı oluştur"""
    try:
        # API anahtarı kontrolü
        api_key = request.headers.get('X-API-Key')
        if not verify_api_key(api_key):
            return jsonify({'error': 'Geçersiz API anahtarı'}), 401

        duration_days = request.json.get('duration_days', 365)
        
        # Benzersiz lisans anahtarı oluştur
        license_key = generate_unique_key()
        expiry_date = datetime.utcnow() + timedelta(days=duration_days)
        
        # Veritabanına kaydet
        license = License(
            license_key=license_key,
            expiry_date=expiry_date
        )
        db.session.add(license)
        db.session.commit()
        
        return jsonify({
            'license_key': license_key,
            'expiry_date': expiry_date.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-license', methods=['POST'])
def verify_license():
    """Lisans doğrulama"""
    try:
        license_key = request.json.get('license_key')
        hardware_id = request.json.get('hardware_id')
        
        if not license_key or not hardware_id:
            return jsonify({'error': 'Eksik parametreler'}), 400
        
        # Lisansı bul
        license = License.query.filter_by(license_key=license_key).first()
        if not license:
            return jsonify({'valid': False, 'message': 'Lisans bulunamadı'})
        
        # Aktif mi kontrol et
        if not license.is_active:
            return jsonify({'valid': False, 'message': 'Lisans deaktive edilmiş'})
        
        # Süre kontrolü
        if datetime.utcnow() > license.expiry_date:
            return jsonify({'valid': False, 'message': 'Lisans süresi dolmuş'})
        
        # Donanım ID kontrolü
        if license.hardware_id and license.hardware_id != hardware_id:
            return jsonify({'valid': False, 'message': 'Lisans başka bir cihaza ait'})
        
        # İlk aktivasyon ise donanım ID'sini kaydet
        if not license.hardware_id:
            license.hardware_id = hardware_id
            license.activation_count += 1
            
        # Aktivasyon kaydı
        activation = LicenseActivation(
            license_id=license.id,
            hardware_id=hardware_id,
            ip_address=request.remote_addr
        )
        db.session.add(activation)
        db.session.commit()
        
        return jsonify({
            'valid': True,
            'expiry_date': license.expiry_date.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deactivate-license', methods=['POST'])
def deactivate_license():
    """Lisans deaktivasyonu"""
    try:
        api_key = request.headers.get('X-API-Key')
        if not verify_api_key(api_key):
            return jsonify({'error': 'Geçersiz API anahtarı'}), 401
            
        license_key = request.json.get('license_key')
        license = License.query.filter_by(license_key=license_key).first()
        
        if not license:
            return jsonify({'error': 'Lisans bulunamadı'}), 404
            
        license.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Lisans deaktive edildi'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Yardımcı fonksiyonlar
def generate_unique_key():
    """Benzersiz lisans anahtarı oluştur"""
    while True:
        key = secrets.token_hex(16)
        formatted_key = '-'.join([key[i:i+4] for i in range(0, len(key), 4)])
        if not License.query.filter_by(license_key=formatted_key).first():
            return formatted_key

def verify_api_key(api_key):
    """API anahtarı doğrulama"""
    valid_api_key = 'your-api-key-here'  # Güvenli bir şekilde saklanmalı
    return api_key == valid_api_key

# Admin panel rotaları
@app.route('/admin/licenses')
def admin_licenses():
    """Lisans yönetim paneli"""
    licenses = License.query.all()
    return render_template('admin/licenses.html', licenses=licenses)

@app.route('/admin/create-license', methods=['POST'])
def create_license():
    try:
        print("Lisans oluşturma isteği alındı")
        print("Request headers:", dict(request.headers))
        print("Request data:", request.get_data().decode('utf-8'))
        
        if not request.is_json:
            print("Gelen istek JSON değil!")
            return jsonify({
                'success': False, 
                'error': 'JSON verisi gerekli'
            }), 400
            
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False, 
                'error': 'Geçersiz JSON verisi'
            }), 400
            
        print(f"Gelen data: {data}")
        
        # Lisans oluştur
        license = License(
            license_key=generate_license_key(),
            expiry_date=datetime.utcnow() + timedelta(days=int(data.get('duration', 365))),
            license_type=data.get('type', 'standard'),
            customer_name=data.get('customer_name', ''),
            customer_email=data.get('customer_email', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(license)
        db.session.commit()
        
        print(f"Yeni lisans oluşturuldu: {license.license_key}")
        
        return jsonify({
            'success': True,
            'license_key': license.license_key,
            'message': 'Lisans başarıyla oluşturuldu'
        })
        
    except Exception as e:
        print(f"Lisans oluşturma hatası: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=port) 