from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
import hashlib
import os
import sys
from flask_cors import CORS  # CORS desteği için
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Mutlak yolları belirle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
ADMIN_DIR = os.path.join(TEMPLATE_DIR, 'admin')
DB_PATH = os.path.join(BASE_DIR, 'instance', 'licenses.db')

# Flask uygulamasını oluştur
app = Flask(__name__)
app.template_folder = TEMPLATE_DIR
CORS(app)  # CORS'u etkinleştir

# Veritabanı yapılandırması
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'bilist-secret-key-2024'

# Klasörleri oluştur
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(ADMIN_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Template klasörünü kontrol et ve oluştur
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
admin_dir = os.path.join(template_dir, 'admin')

# Debug için yolları yazdır
print(f"\nKlasör yolları:")
print(f"Çalışma klasörü: {os.getcwd()}")
print(f"Template klasörü: {template_dir}")
print(f"Admin klasörü: {admin_dir}")
print(f"Template dosyası: {os.path.join(admin_dir, 'licenses.html')}")
print(f"Dosya var mı?: {os.path.exists(os.path.join(admin_dir, 'licenses.html'))}\n")

db = SQLAlchemy(app)

# Flask-Login ayarları
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Admin kullanıcı modeli
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Login route'ları
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

class License(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    license_key = db.Column(db.String(64), unique=True, nullable=False)
    hardware_id = db.Column(db.String(64))
    expiry_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    activation_count = db.Column(db.Integer, default=0)
    customer_name = db.Column(db.String(100))
    customer_email = db.Column(db.String(100))
    notes = db.Column(db.Text)
    license_type = db.Column(db.String(20), default='standard')

@app.route('/')
def index():
    return redirect(url_for('admin_licenses'))

@app.route('/admin')
@app.route('/admin/licenses')
@login_required
def admin_licenses():
    try:
        licenses = License.query.order_by(License.created_at.desc()).all()
        stats = {
            'total': len(licenses),
            'active': sum(1 for l in licenses if l.is_active),
            'expired': sum(1 for l in licenses if not l.is_active),
            'never_activated': sum(1 for l in licenses if not l.hardware_id)
        }
        return render_template('admin/licenses.html', 
                             licenses=licenses, 
                             stats=stats,
                             now=datetime.utcnow())
    except Exception as e:
        print(f"Template render hatası: {str(e)}")
        return f"Hata: {str(e)}", 500

@app.route('/admin/create-license', methods=['POST'])
@login_required
def create_license():
    try:
        data = request.get_json()
        duration = int(data.get('duration', 365))
        
        # Süresiz lisans için datetime.max kullan
        if duration == -1:
            expiry_date = datetime.max
        else:
            expiry_date = datetime.utcnow() + timedelta(days=duration)
        
        license = License(
            license_key=generate_license_key(),
            expiry_date=expiry_date,
            license_type=data.get('type', 'standard'),
            customer_name=data.get('customer_name', ''),
            customer_email=data.get('customer_email', ''),
            notes=data.get('notes', '')
        )
        
        db.session.add(license)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'license_key': license.license_key,
            'message': 'Lisans başarıyla oluşturuldu'
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

def generate_license_key():
    """Benzersiz lisans anahtarı oluştur"""
    while True:
        key = secrets.token_hex(8)
        formatted_key = '-'.join([key[i:i+4] for i in range(0, len(key), 4)])
        if not License.query.filter_by(license_key=formatted_key).first():
            return formatted_key

@app.route('/api/verify-license', methods=['POST'])
def verify_license():
    try:
        data = request.get_json()
        license_key = data.get('license_key')
        hardware_id = data.get('hardware_id')
        
        if not license_key or not hardware_id:
            return jsonify({'valid': False, 'message': 'Eksik bilgi'})
        
        license = License.query.filter_by(license_key=license_key).first()
        if not license:
            return jsonify({'valid': False, 'message': 'Lisans bulunamadı'})
            
        if not license.is_active:
            return jsonify({'valid': False, 'message': 'Lisans deaktive edilmiş'})
            
        # Süresiz lisans kontrolü (-1)
        if license.expiry_date != datetime.max and datetime.utcnow() > license.expiry_date:
            return jsonify({'valid': False, 'message': 'Lisans süresi dolmuş'})
            
        if license.hardware_id and license.hardware_id != hardware_id:
            return jsonify({'valid': False, 'message': 'Lisans başka bir cihaza ait'})
            
        if not license.hardware_id:
            license.hardware_id = hardware_id
            license.activation_count += 1
            db.session.commit()
            
        return jsonify({
            'valid': True, 
            'expiry_date': license.expiry_date.isoformat(),
            'days_left': (license.expiry_date - datetime.utcnow()).days if license.expiry_date != datetime.max else -1
        })
        
    except Exception as e:
        return jsonify({'valid': False, 'message': str(e)})

@app.route('/api/license-details/<license_key>')
def license_details(license_key):
    license = License.query.filter_by(license_key=license_key).first()
    if not license:
        return jsonify({'error': 'Lisans bulunamadı'}), 404
        
    return jsonify({
        'license_key': license.license_key,
        'hardware_id': license.hardware_id,
        'created_at': license.created_at.strftime('%Y-%m-%d %H:%M'),
        'expiry_date': license.expiry_date.strftime('%Y-%m-%d'),
        'is_active': license.is_active,
        'customer_name': license.customer_name,
        'customer_email': license.customer_email,
        'license_type': license.license_type,
        'notes': license.notes,
        'activation_count': license.activation_count
    })

@app.route('/api/deactivate-license', methods=['POST'])
def deactivate_license():
    try:
        data = request.json
        license = License.query.filter_by(license_key=data['license_key']).first()
        if not license:
            return jsonify({'success': False, 'error': 'Lisans bulunamadı'})

        license.is_active = False
        db.session.commit()
        return jsonify({'success': True, 'message': 'Lisans deaktive edildi'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete-license', methods=['POST'])
def delete_license():
    try:
        data = request.json
        license = License.query.filter_by(license_key=data['license_key']).first()
        if not license:
            return jsonify({'success': False, 'error': 'Lisans bulunamadı'})

        db.session.delete(license)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Lisans silindi'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update-license', methods=['POST'])
def update_license():
    try:
        data = request.json
        license = License.query.filter_by(license_key=data['license_key']).first()
        if not license:
            return jsonify({'success': False, 'error': 'Lisans bulunamadı'})

        # Yeni süreyi hesapla
        duration = int(data.get('duration', 365))
        if duration == -1:
            license.expiry_date = datetime.max
        else:
            # Mevcut süreden kalan günleri hesapla
            remaining_days = (license.expiry_date - datetime.utcnow()).days
            if remaining_days < 0:
                remaining_days = 0
            # Yeni süreyi ekle
            license.expiry_date = datetime.utcnow() + timedelta(days=duration + remaining_days)

        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Lisans süresi güncellendi',
            'new_expiry_date': license.expiry_date.strftime('%Y-%m-%d')
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# İlk admin kullanıcısını oluştur
def create_admin_user():
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', is_admin=True)
            admin.set_password('bilist2024')  # Güvenli bir şifre belirleyin
            db.session.add(admin)
            db.session.commit()
            print("Admin kullanıcısı oluşturuldu!")

@app.route('/admin/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_user.check_password(current_password):
            return jsonify({
                'success': False,
                'error': 'Mevcut şifre yanlış'
            }), 400
            
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Şifre başarıyla güncellendi'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    try:
        with app.app_context():
            db_path = DB_PATH
            if os.path.exists(db_path):
                try:
                    db.session.remove()
                    db.engine.dispose()
                    os.remove(db_path)
                except Exception as e:
                    print(f"Veritabanı silinirken hata: {e}")
            
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            db.create_all()
            create_admin_user()
            print("Veritabanı yeniden oluşturuldu!")
            
        print("\nSunucu başlatılıyor...")
        print("Admin paneli: http://localhost:5000/admin/licenses")
        app.run(debug=True, port=5000)
    except Exception as e:
        print(f"Kritik hata: {str(e)}")
        sys.exit(1)