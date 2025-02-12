import sys, os

# cPanel Python yolu - bu yolu cPanel'den alın
INTERP = "/home/[cpanel_kullanici_adi]/virtualenv/lisans/3.9/bin/python"

if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

from app import app as application 