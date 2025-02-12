# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],  # DLL'leri kaldırdık
    datas=[
        ('*.fmt', '.'),     # FMT dosyalarını ekle
        ('icon.ico', '.'),  # İkon dosyasını ekle
    ],
    hiddenimports=[
        'pandas', 
        'openpyxl',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        'numpy',
        'PIL',
        'PIL._imagingtk',
        'PIL._tkinter_finder'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],  # a.binaries kaldırıldı
    exclude_binaries=True,  # Binary dosyaları ayrı klasörde tut
    name='Optik Form Editörü',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # İkonu ekledik
    version='file_version_info.txt',
)

# Tüm dosyaları bir araya topla
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Optik Form Editörü',
) 