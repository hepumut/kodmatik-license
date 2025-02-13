import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
import hashlib
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sys

from server.app import create_admin_user

# Yolları düzelt
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
ADMIN_DIR = os.path.join(TEMPLATE_DIR, 'admin')
DB_PATH = os.path.join(BASE_DIR, 'database.db')

app = Flask(__name__)
app.template_folder = TEMPLATE_DIR

# Veritabanı yapılandırması
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{DB_PATH}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'bilist-secret-key-2024')

# Debug'ı kapat
app.debug = False

db = SQLAlchemy(app)

# Flask-Login ayarları
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

@app.route('/api/verify-license')
def verify_license():
    """Lisans doğrulama"""
    try:
        # API anahtarı kontrolü
        api_key = request.headers.get('X-API-Key')
        if not verify_api_key(api_key):
            return jsonify({'error': 'Geçersiz API anahtarı'}), 401
            
        license_key = request.args.get('license_key')
        hardware_id = request.args.get('hardware_id')
        
        if not license_key or not hardware_id:
            return jsonify({'error': 'Eksik parametreler'}), 400
        
        license = License.query.filter_by(license_key=license_key).first()
        
        # Lisans kontrolü
        if not license:
            return jsonify({'error': 'Lisans bulunamadı'}), 404
            
        if not license.is_active:
            return jsonify({'error': 'Lisans aktif değil'}), 400
            
        if license.expiry_date < datetime.utcnow():
            # Süresi dolan lisansı deaktive et
            license.is_active = False
            db.session.commit()
            return jsonify({'error': 'Lisans süresi dolmuş'}), 400
            
        # Donanım ID kontrolü
        if license.hardware_id:
            if license.hardware_id != hardware_id:
                return jsonify({'error': 'Lisans başka bir cihazda aktif'}), 400
        else:
            # İlk aktivasyon
            return jsonify({'error': 'Lisans henüz aktive edilmemiş'}), 400
            
        # Aktivasyon sayısı kontrolü
        if license.activation_count > 3:  # Maksimum aktivasyon sayısı
            return jsonify({'error': 'Maksimum aktivasyon sayısı aşıldı'}), 400
            
        return jsonify({
            'valid': True,
            'expiry_date': license.expiry_date.isoformat(),
            'license_type': license.license_type,
            'customer_name': license.customer_name,
            'remaining_days': (license.expiry_date - datetime.utcnow()).days
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

@app.route('/api/activate-license', methods=['POST'])
def activate_license():
    """Lisans aktivasyonu"""
    try:
        api_key = request.headers.get('X-API-Key')
        if not verify_api_key(api_key):
            return jsonify({'error': 'Geçersiz API anahtarı'}), 401
            
        data = request.json
        license_key = data.get('license_key')
        hardware_id = data.get('hardware_id')
        
        if not license_key or not hardware_id:
            return jsonify({'error': 'Eksik parametreler'}), 400
        
        license = License.query.filter_by(license_key=license_key).first()
        
        # Lisans kontrolü
        if not license:
            return jsonify({'error': 'Geçersiz lisans anahtarı'}), 404
            
        if not license.is_active:
            return jsonify({'error': 'Lisans aktif değil'}), 400
            
        if license.expiry_date < datetime.utcnow():
            license.is_active = False
            db.session.commit()
            return jsonify({'error': 'Lisans süresi dolmuş'}), 400
            
        # Aktivasyon sayısı kontrolü
        if license.activation_count >= 3:
            return jsonify({'error': 'Maksimum aktivasyon sayısı aşıldı'}), 400
            
        # Donanım ID kontrolü
        if license.hardware_id and license.hardware_id != hardware_id:
            return jsonify({'error': 'Lisans başka bir cihazda aktif'}), 400
            
        # Aktivasyon işlemi
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
            'message': 'Lisans başarıyla aktive edildi',
            'expiry_date': license.expiry_date.isoformat(),
            'remaining_days': (license.expiry_date - datetime.utcnow()).days
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/license/<int:license_id>')
@login_required
def get_license_basic_details(license_id):
    """Temel lisans detaylarını getir"""
    try:
        license = License.query.get_or_404(license_id)
        return jsonify({
            'hardware_id': license.hardware_id,
            'notes': license.notes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/license-details/<int:license_id>')
@login_required
def get_license_details(license_id):
    """Detaylı lisans bilgilerini getir"""
    try:
        license = License.query.get_or_404(license_id)
        
        return jsonify({
            'license_key': license.license_key,
            'is_active': license.is_active,
            'type': license.license_type,
            'created_at': license.created_at.strftime('%d.%m.%Y'),
            'expiry_date': license.expiry_date.strftime('%d.%m.%Y'),
            'customer_name': license.customer_name,
            'customer_email': license.customer_email,
            'activation_count': license.activation_count,
            'hardware_id': license.hardware_id,
            'notes': license.notes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-license', methods=['POST'])
@login_required
def update_license():
    """Lisans süresini güncelle"""
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        duration = int(data.get('duration', 365))
        
        license = License.query.filter_by(license_key=license_key).first()
        if not license:
            return jsonify({
                'success': False,
                'error': 'Lisans bulunamadı'
            }), 404
            
        # Mevcut süreden kalan günleri hesapla
        remaining_days = (license.expiry_date - datetime.utcnow()).days
        if remaining_days < 0:
            remaining_days = 0
            
        # Yeni süreyi ekle
        license.expiry_date = datetime.utcnow() + timedelta(days=duration + remaining_days)
        license.is_active = True  # Lisansı aktif et
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Lisans süresi güncellendi',
            'new_expiry_date': license.expiry_date.strftime('%d.%m.%Y')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/delete-license', methods=['POST'])
@login_required
def delete_license():
    """Lisansı sil"""
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        
        license = License.query.filter_by(license_key=license_key).first()
        if not license:
            return jsonify({
                'success': False,
                'error': 'Lisans bulunamadı'
            }), 404
            
        # Önce aktivasyon kayıtlarını sil
        LicenseActivation.query.filter_by(license_id=license.id).delete()
        
        # Sonra lisansı sil
        db.session.delete(license)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Lisans başarıyla silindi'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
    # Güçlü ve karmaşık bir API anahtarı kullanın
    valid_api_key = 'blt_2024_f8a92b1c7d4e6p9x'  # Bu anahtarı değiştirin ve güvenli bir yerde saklayın
    return api_key == valid_api_key

# Admin panel rotaları
@app.route('/')
def index():
    """Ana sayfa yönlendirmesi"""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_licenses'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin_licenses'))
            
        return render_template('admin/login.html', error='Geçersiz kullanıcı adı veya şifre')
        
    return render_template('admin/login.html')

@app.route('/admin')
@app.route('/admin/licenses')
@login_required
def admin_licenses():
    try:
        licenses = License.query.order_by(License.created_at.desc()).all()
        
        # Lisansları template'in beklediği formata dönüştür
        formatted_licenses = []
        for license in licenses:
            formatted_licenses.append({
                'id': license.id,
                'license_key': license.license_key,
                'customer_name': license.customer_name or 'Belirtilmemiş',
                'customer_email': license.customer_email or 'Belirtilmemiş',
                'license_type': license.license_type or 'standard',
                'created_at': license.created_at,
                'expiry_date': license.expiry_date,
                'is_active': license.is_active,
                'hardware_id': license.hardware_id,
                'activation_count': license.activation_count,
                'notes': license.notes or ''
            })
        
        # İstatistikleri hesapla
        stats = {
            'total': len(licenses),
            'active': sum(1 for l in licenses if l.is_active),
            'expired': sum(1 for l in licenses if not l.is_active),
            'never_activated': sum(1 for l in licenses if not l.hardware_id)
        }
        
        return render_template('admin/licenses.html', 
                             licenses=formatted_licenses, 
                             stats=stats,
                             current_user=current_user,
                             now=datetime.utcnow())
                             
    except Exception as e:
        print(f"Template render hatası: {str(e)}")
        return f"Hata: {str(e)}", 500

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

def generate_license_key():
    return secrets.token_hex(16)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'error': 'Tüm alanları doldurun'
            }), 400
            
        # Mevcut şifreyi kontrol et
        if not current_user.check_password(current_password):
            return jsonify({
                'success': False,
                'error': 'Mevcut şifre yanlış'
            }), 400
            
        # Yeni şifreyi ayarla
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Şifre başarıyla değiştirildi'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Bu kısmı __main__ bloğunun dışına çıkaralım
with app.app_context():
    # Veritabanını oluştur
    db.create_all()
    
    # İlk admin kullanıcısını oluştur
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', is_admin=True)
        admin.set_password('bilist2024')
        db.session.add(admin)
        db.session.commit()
        print("Admin kullanıcısı oluşturuldu!")

if __name__ == '__main__':
    try:
        with app.app_context():
            # Veritabanı yoksa oluştur
            if not os.path.exists(DB_PATH):
                os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
                db.create_all()
                create_admin_user()
                print("Veritabanı oluşturuldu!")
            
        print("\nSunucu başlatılıyor...")
        print("Admin paneli: http://localhost:5000/admin/licenses")
        app.run(debug=False, port=5000)
    except Exception as e:
        print(f"Kritik hata: {str(e)}")
        sys.exit(1) 