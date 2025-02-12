import os

# Yolları düzelt
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
ADMIN_DIR = os.path.join(TEMPLATE_DIR, 'admin')
DB_PATH = os.path.join(BASE_DIR, 'instance', 'licenses.db')

# Debug'ı kapat
app.debug = False

# Host ve port ayarlarını güncelle
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000) 