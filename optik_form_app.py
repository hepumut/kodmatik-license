import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QFileDialog, QLabel, QMenu, QDialog, 
                            QComboBox, QTableWidget, QTableWidgetItem, QScrollArea, QLineEdit, QTextEdit, QGridLayout, QDoubleSpinBox, QSpinBox, QCheckBox, QToolBar, QAction, QProgressDialog, QMessageBox, QStatusBar)
from PyQt5.QtCore import Qt, QPoint, QSize, QRect, QRectF, QSizeF
from PyQt5.QtGui import QPainter, QColor, QPen, QPixmap, QIcon, QImage, QFont
from PyQt5.QtPrintSupport import QPrinter
import pandas as pd
import cv2
import numpy as np
from fmt_parser import FMTParser, FormField
import json
from license_manager import LicenseManager

class OptikFormApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.fmt_data = None
        self.excel_data = False
        self.fmt_parser = None
        self.student_data = []
        self.field_mapping = {}
        self.license_manager = LicenseManager()
        
        # FMT Parser'ı başlat
        self.fmt_parser = FMTParser()
        
        self.initUI()
        self.update_license_status()
        
    def initUI(self):
        """Ana pencere arayüzünü oluştur"""
        # İkon ayarla
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Menü çubuğu
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu('Dosya')
        
        load_fmt = QAction('FMT Yükle', self)
        load_fmt.setShortcut('Ctrl+F')
        load_fmt.triggered.connect(self.load_fmt_file)
        file_menu.addAction(load_fmt)
        
        load_excel = QAction('Excel Yükle', self)
        load_excel.setShortcut('Ctrl+E')
        load_excel.triggered.connect(self.load_excel_file)
        file_menu.addAction(load_excel)
        
        load_image = QAction('Resim Yükle', self)
        load_image.setShortcut('Ctrl+I')
        load_image.triggered.connect(self.load_background_image)
        file_menu.addAction(load_image)
        
        file_menu.addSeparator()
        
        save_pdf = QAction('PDF Kaydet', self)
        save_pdf.setShortcut('Ctrl+S')
        save_pdf.triggered.connect(self.generate_optical_forms)
        file_menu.addAction(save_pdf)
        
        # Yardım menüsü
        help_menu = menubar.addMenu('Yardım')
        
        # Kullanım kılavuzu
        usage_action = QAction('Kullanım Kılavuzu', self)
        usage_action.setShortcut('F1')
        usage_action.triggered.connect(self.show_usage_guide)
        help_menu.addAction(usage_action)
        
        help_menu.addSeparator()
        
        # Hakkında
        about_action = QAction('Hakkında', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        # Araç çubuğu
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Araç çubuğu butonları
        fmt_btn = QAction('FMT Yükle', self)
        fmt_btn.triggered.connect(self.load_fmt_file)
        toolbar.addAction(fmt_btn)
        
        excel_btn = QAction('Excel Yükle', self)
        excel_btn.triggered.connect(self.load_excel_file)
        toolbar.addAction(excel_btn)
        
        image_btn = QAction('Resim Yükle', self)
        image_btn.triggered.connect(self.load_background_image)
        toolbar.addAction(image_btn)
        
        toolbar.addSeparator()
        
        # Görüntü kontrolleri
        zoom_in_btn = QAction('Yakınlaştır (+)', self)
        zoom_in_btn.setShortcut('+')
        zoom_in_btn.triggered.connect(self.increase_image_size)
        toolbar.addAction(zoom_in_btn)
        
        zoom_out_btn = QAction('Uzaklaştır (-)', self)
        zoom_out_btn.setShortcut('-')
        zoom_out_btn.triggered.connect(self.decrease_image_size)
        toolbar.addAction(zoom_out_btn)
        
        toolbar.addSeparator()
        
        # Grid kontrolleri
        grid_label = QLabel('Grid Boyutu:')
        toolbar.addWidget(grid_label)
        
        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(10, 100)
        self.grid_size_spin.setValue(30)
        self.grid_size_spin.valueChanged.connect(self.change_grid_size)
        toolbar.addWidget(self.grid_size_spin)
        
        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.scroll_area)
        
        # Form widget'ı
        self.form_widget = FormWidget(self, self.fmt_parser)
        self.scroll_area.setWidget(self.form_widget)
        
        # Durum çubuğu
        self.statusBar().showMessage('Hazır')
        
        # Pencere ayarları
        self.setWindowTitle('Optik Form Editörü')
        self.setGeometry(100, 100, 1200, 800)

        # Status bar'a lisans durumu ekle
        self.statusBar().setStyleSheet("""
            QStatusBar {
                border-top: 1px solid #ddd;
                background: #f8f9fa;
            }
        """)
        
        # Sadece bir kere lisans label'ı oluştur
        self.license_label = QLabel()
        self.license_label.setMinimumWidth(150)
        self.statusBar().addPermanentWidget(self.license_label)
        
        # Lisans durumunu güncelle
        self.update_license_status()

    def change_grid_size(self, value):
        """Grid boyutunu değiştir"""
        if hasattr(self, 'form_widget'):
            self.form_widget.scale = value
            self.form_widget.update()
            self.statusBar().showMessage(f'Grid boyutu: {value}')

    def load_fmt_file(self):
        """FMT dosyasını yükle"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, 'FMT Dosyası Seç', '', 'FMT Files (*.fmt)'
            )
            
            if filename:
                # FMT dosyasını oku
                self.fmt_parser = FMTParser()
                self.fmt_data = self.fmt_parser.parse_file(filename)
                
                if self.fmt_data:
                    print(f"FMT dosyası yüklendi: {len(self.fmt_parser.fields)} alan")
                    self.statusBar().showMessage('FMT dosyası yüklendi')
                    
                    # Form görünümünü güncelle
                    self.update_form_view()
                    
                    # Excel yüklüyse alan eşleştirme penceresini göster
                    if self.excel_data:
                        self.show_field_mapping_dialog()
                else:
                    self.statusBar().showMessage('FMT dosyası okunamadı!')
                    
        except Exception as e:
            print(f"FMT yükleme hatası: {e}")
            self.statusBar().showMessage('FMT dosyası yüklenemedi!')

    def load_excel_file(self):
        """Excel dosyasını yükle"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, 'Excel Dosyası Seç', '', 'Excel Files (*.xlsx *.xls)'
            )
            
            if filename:
                # Excel dosyasını oku
                df = pd.read_excel(filename)
                self.student_data = df.to_dict('records')
                
                if self.student_data:
                    print(f"Excel dosyası okundu: {len(self.student_data)} öğrenci")
                    self.statusBar().showMessage('Excel dosyası yüklendi')
                    self.excel_data = True
                    
                    # FMT yüklüyse alan eşleştirme penceresini göster
                    if hasattr(self, 'fmt_data') and self.fmt_data:
                        self.show_field_mapping_dialog()
                else:
                    self.statusBar().showMessage('Excel dosyası boş!')
                
        except Exception as e:
            print(f"Excel okuma hatası: {e}")
            self.statusBar().showMessage('Excel dosyası okunamadı!')

    def preview_student_data(self, student_data):
        """Öğrenci verilerini önizleme olarak göster"""
        try:
            # Form widget'ı temizle
            self.form_widget.marked_cells.clear()
            
            # Öğrenci verilerini forma işle
            self.fill_form_fields(self.form_widget, student_data)
            
            # Formu güncelle
            self.form_widget.update()
            
            # Öğrenci bilgilerini statusbar'da göster
            if 'OGRENCI_NO' in student_data and 'ADI' in student_data and 'SOYADI' in student_data:
                student_info = f"Önizleme: {student_data['OGRENCI_NO']} - {student_data['ADI']} {student_data['SOYADI']}"
                self.statusBar().showMessage(student_info)
            
        except Exception as e:
            print(f"Önizleme hatası: {e}")
            self.statusBar().showMessage('Önizleme gösterme hatası!')

    def parse_fmt_file(self, filename):
        print(f"\nFMT dosyası yükleniyor: {filename}")  # Debug için
        try:
            success = self.fmt_parser.parse_file(filename)
            if success:
                print("FMT dosyası başarıyla yüklendi")
                print(f"Grid boyutu: {self.fmt_parser.get_grid_size()}")
                print(f"Toplam alan sayısı: {len(self.fmt_parser.fields)}")
                
                self.fmt_data = True
                self.update_form_view()
            else:
                print("FMT dosyası yüklenemedi!")
                self.fmt_data = False
                
        except Exception as e:
            print(f"FMT dosyası okuma hatası: {str(e)}")
            self.fmt_data = False
    
    def update_form_view(self):
        """Form görünümünü güncelle"""
        try:
            # Eski form widget'ı varsa temizle
            if hasattr(self, 'form_widget'):
                self.form_widget.deleteLater()
            
            # Yeni form widget'ı oluştur
            self.form_widget = FormWidget(self, self.fmt_parser)
            
            # Scroll area'ya ekle
            self.scroll_area.setWidget(self.form_widget)
            
            # Widget'ı güncelle
            self.form_widget.update()
            
            print("Form görünümü güncellendi")
            
        except Exception as e:
            print(f"Form güncelleme hatası: {e}")
            self.statusBar().showMessage('Form görünümü güncellenemedi!')

    def show_field_mapping_dialog(self):
        """Alan eşleştirme penceresini göster"""
        try:
            # Alan eşleştirme penceresi
            dialog = QDialog(self)
            dialog.setWindowTitle('Alan Eşleştirme')
            layout = QVBoxLayout(dialog)
            
            # Eşleştirme tablosu
            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(['FMT Alanı', 'Excel Sütunu'])
            
            # Excel sütunları
            excel_columns = list(self.student_data[0].keys())
            
            # FMT alanları için satır ekle
            table.setRowCount(len(self.fmt_parser.fields))
            for i, field in enumerate(self.fmt_parser.fields):
                # FMT alanı
                fmt_item = QTableWidgetItem(field.field_name)
                fmt_item.setFlags(fmt_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(i, 0, fmt_item)
                
                # Excel sütunu seçici
                combo = QComboBox()
                combo.addItems([''] + excel_columns)
                if hasattr(self, 'field_mapping') and field.field_name in self.field_mapping:
                    combo.setCurrentText(self.field_mapping[field.field_name])
                table.setCellWidget(i, 1, combo)
            
            layout.addWidget(table)
            
            # Butonlar
            button_box = QHBoxLayout()
            
            save_btn = QPushButton('Kaydet')
            save_btn.clicked.connect(lambda: self.save_field_mapping(table, dialog))
            button_box.addWidget(save_btn)
            
            cancel_btn = QPushButton('İptal')
            cancel_btn.clicked.connect(dialog.reject)
            button_box.addWidget(cancel_btn)
            
            layout.addLayout(button_box)
            
            # Pencereyi göster
            dialog.exec_()
            
        except Exception as e:
            print(f"Alan eşleştirme hatası: {e}")
            self.statusBar().showMessage('Alan eşleştirme penceresi açılamadı!')

    def save_field_mapping(self, table, dialog):
        """Alan eşleştirmelerini kaydet"""
        try:
            # Eşleştirmeleri topla
            self.field_mapping = {}
            for row in range(table.rowCount()):
                fmt_field = table.item(row, 0).text()
                excel_col = table.cellWidget(row, 1).currentText()
                if excel_col:  # Boş olmayan eşleştirmeleri al
                    self.field_mapping[fmt_field] = excel_col
            
            print("Alan eşleştirmeleri:", self.field_mapping)
            
            # İlk öğrencinin verilerini önizleme olarak göster
            if self.student_data:
                first_student = self.student_data[0]
                self.form_widget.marked_cells = set()  # Önceki işaretleri temizle
                self.fill_form_fields(self.form_widget, first_student)
                self.form_widget.update()
            
            dialog.accept()
            self.statusBar().showMessage('Alan eşleştirmeleri kaydedildi')
            
        except Exception as e:
            print(f"Eşleştirme kaydetme hatası: {e}")
            self.statusBar().showMessage('Eşleştirmeler kaydedilemedi!')

    def code_excel_data(self):
        if not hasattr(self, 'field_mapping'):
            return
            
        # Her öğrenci için form oluştur
        for index, row in self.excel_df.iterrows():
            # Yeni form oluştur
            form_data = {}
            
            # Excel verilerini form alanlarına kodla
            for fmt_field, excel_col in self.field_mapping.items():
                field = next((f for f in self.fmt_parser.fields if f.field_name == fmt_field), None)
                if field and excel_col in row:
                    value = str(row[excel_col])
                    
                    # Sayısal değerler için
                    if field.options.isdigit():
                        # Sayıyı basamaklarına ayır
                        digits = [int(d) for d in str(value) if d.isdigit()]
                        form_data[fmt_field] = digits
                    
                    # Alfabetik değerler için
                    else:
                        # Değeri karakterlerine ayır ve uygun seçeneklere dönüştür
                        chars = [c for c in value.upper() if c in field.options]
                        form_data[fmt_field] = chars
            
            # Form verilerini kaydet/görüntüle
            self.process_form_data(form_data)
    
    def process_form_data(self, form_data):
        # Bu metod form verilerini işler
        # Örneğin: PDF oluşturma, görüntüleme, kaydetme vb.
        print("Form verileri:", form_data)

    def zoom_in(self):
        self.form_widget.zoom_in()

    def zoom_out(self):
        self.form_widget.zoom_out()

    def generate_optical_forms(self):
        """Tüm öğrenciler için optik formları tek PDF olarak oluştur"""
        try:
            # PDF dosya adını al
            filename, _ = QFileDialog.getSaveFileName(
                self, 'PDF Kaydet', '', 'PDF Files (*.pdf)'
            )
            
            if not filename:
                return
            
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            # Progress dialog oluştur
            progress = QProgressDialog("PDF oluşturuluyor...", "İptal", 0, len(self.student_data), self)
            progress.setWindowTitle("PDF Kaydediliyor")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            
            # PDF yazıcı ayarları
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageSize(QPrinter.A4)
            printer.setFullPage(True)
            printer.setPageMargins(0, 0, 0, 0, QPrinter.Point)
            printer.setResolution(300)
            
            # Sayfa boyutlarını al
            page_width = printer.pageRect().width()
            page_height = printer.pageRect().height()
            
            # Form widget'ını hazırla
            form = FormWidget(self, self.fmt_parser)
            form.pdf_mode = True
            form.scale = self.form_widget.scale
            form.image_scale = self.form_widget.image_scale
            form.background_image = self.form_widget.background_image
            form.grid_offset = self.form_widget.grid_offset  # Grid konumunu kopyala
            
            # Grid boyutlarını al
            grid_width, grid_height = form.get_grid_size()
            scaled_width = grid_width * form.scale * form.image_scale
            scaled_height = grid_height * form.scale * form.image_scale
            
            # Sayfaya tam sığacak şekilde ölçekle
            scale_w = page_width / scaled_width
            scale_h = page_height / scaled_height
            scale = max(scale_w, scale_h)
            
            # PDF'e çiz
            painter = QPainter()
            if painter.begin(printer):
                total = len(self.student_data)
                for i, student in enumerate(self.student_data, 1):
                    # Progress bar'ı güncelle
                    progress.setValue(i)
                    QApplication.processEvents()
                    
                    if progress.wasCanceled():
                        break
                    
                    # Öğrenci verilerini işle
                    form.marked_cells = set()
                    self.fill_form_fields(form, student)
                    
                    # Sayfaya çiz
                    painter.save()
                    painter.scale(scale, scale)
                    form.render(painter)
                    painter.restore()
                    
                    # Son sayfa değilse yeni sayfa ekle
                    if i < total:
                        printer.newPage()
                
                painter.end()
                progress.setValue(total)
                
                # Başarı mesajı göster
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Başarılı")
                msg.setText("PDF başarıyla kaydedildi!")
                msg.setInformativeText(f"Dosya konumu:\n{filename}")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
                
                self.statusBar().showMessage(f'PDF oluşturuldu: {filename}')
                print(f"PDF oluşturuldu: {filename}")
                
        except Exception as e:
            print(f"PDF oluşturma hatası: {e}")
            self.statusBar().showMessage('PDF oluşturulamadı!')
            
            # Hata mesajı göster
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Hata")
            msg.setText("PDF oluşturulurken hata oluştu!")
            msg.setInformativeText(str(e))
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def fill_form_fields(self, form_widget, student_data):
        """Öğrenci verilerini forma işle"""
        try:
            # Önceki işaretleri temizle
            form_widget.marked_cells = set()
            form_widget.marked_values = {}  # İşaretlenen değerleri sakla
            
            # Field mapping'e göre alanları doldur
            for fmt_field, excel_col in self.field_mapping.items():
                try:
                    # FMT alanını bul
                    field = next((f for f in self.fmt_parser.fields if f.field_name == fmt_field), None)
                    if not field:
                        continue
                    
                    # Öğrenci verisini al
                    if fmt_field not in student_data:
                        continue
                    
                    value = str(student_data[fmt_field]).strip()
                    if not value:
                        continue
                    
                    # Değeri sakla
                    form_widget.marked_values[fmt_field] = value
                    
                    # Alan tipine göre doldur
                    if field.options == '0123456789':  # Sayısal alan
                        # Her rakam için
                        width = field.end_x - field.start_x + 1
                        value = value[-width:]  # Son width kadar rakamı al
                        value = value.zfill(width)  # Başa sıfır ekleyerek tamamla
                        
                        for i, digit in enumerate(value):
                            try:
                                digit_val = int(digit)
                                # Grid koordinatlarını hesapla
                                x = field.start_x - 1 + i  # FMT'de 1'den başlıyor
                                y = field.start_y - 1 + digit_val  # Y koordinatı rakama göre
                                form_widget.marked_cells.add((x, y))
                            except ValueError:
                                continue
                    else:  # Metin alanı
                        # Her karakter için
                        value = value.upper()
                        width = field.end_x - field.start_x + 1
                        value = value[:width]  # Alan genişliğini aşan kısmı kes
                        
                        for i, char in enumerate(value):
                            try:
                                # Karakterin opsiyon listesindeki indeksini bul
                                option_index = field.options.index(char)
                                # Grid koordinatlarını hesapla
                                x = field.start_x - 1 + i  # X koordinatı sırayla
                                y = field.start_y - 1 + option_index  # Y koordinatı karaktere göre
                                form_widget.marked_cells.add((x, y))
                            except ValueError:
                                continue
                            
                except Exception as e:
                    print(f"Alan doldurma hatası ({fmt_field}): {e}")
                    continue
            
            # Formu güncelle
            form_widget.update()
            
        except Exception as e:
            print(f"Form doldurma hatası: {e}")

    def save_form_as_pdf(self, form, filename):
        """Formu PDF olarak kaydet"""
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        
        # A4 boyutu için (mm cinsinden)
        printer.setPageSize(QPrinter.A4)
        printer.setFullPage(True)
        
        # Sayfa kenar boşlukları
        printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
        
        # Form boyutunu sayfaya sığdır
        width, height = form.parser.get_grid_size()
        form_ratio = width / height
        
        # A4 boyutları (piksel)
        if form_ratio > 1:  # Yatay form
            printer.setOrientation(QPrinter.Landscape)
        else:  # Dikey form
            printer.setOrientation(QPrinter.Portrait)
        
        painter = QPainter()
        if painter.begin(printer):
            # Formu sayfaya sığdır
            form.render(painter)
            painter.end()
            print(f"Form PDF olarak kaydedildi: {filename}")
        else:
            print(f"PDF oluşturma hatası: {filename}")

    def load_background_image(self):
        """Optik form resmini yükle"""
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Optik Form Resmi Seç',
            '',
            'Image Files (*.png *.jpg *.jpeg *.bmp *.tiff)'
        )
        
        if filename:
            try:
                # Resmi oku
                image = cv2.imread(filename)
                if image is None:
                    raise Exception("Resim okunamadı")
                    
                # Resmi QPixmap'e çevir
                height, width = image.shape[:2]
                bytes_per_line = 3 * width
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_img)
                
                # Form widget'ını güncelle
                self.form_widget.set_background_image(pixmap)
                self.statusBar().showMessage(f'Optik form resmi yüklendi: {filename}')
                
            except Exception as e:
                print(f"Resim yükleme hatası: {e}")
                self.statusBar().showMessage('Optik form resmi yüklenemedi!')

    def increase_image_size(self):
        """Resim boyutunu artır"""
        if hasattr(self.form_widget, 'image_scale'):
            old_scale = self.form_widget.image_scale
            new_scale = min(old_scale + 0.01, self.form_widget.max_image_scale)  # 0.01 hassasiyet
            self.form_widget.image_scale = new_scale
            
            # Statusbar'da ölçeği göster
            scale_percent = round(new_scale * 100, 2)
            self.statusBar().showMessage(f'Resim boyutu: %{scale_percent}')
            
            # Widget'ı güncelle
            self.form_widget.update()

    def decrease_image_size(self):
        """Resim boyutunu azalt"""
        if hasattr(self.form_widget, 'image_scale'):
            old_scale = self.form_widget.image_scale
            new_scale = max(old_scale - 0.01, self.form_widget.min_image_scale)  # 0.01 hassasiyet
            self.form_widget.image_scale = new_scale
            
            # Statusbar'da ölçeği göster
            scale_percent = round(new_scale * 100, 2)
            self.statusBar().showMessage(f'Resim boyutu: %{scale_percent}')
            
            # Widget'ı güncelle
            self.form_widget.update()

    def update_size(self):
        """Widget boyutunu güncelle"""
        if hasattr(self, 'parser'):
            grid_width, grid_height = self.parser.get_grid_size()
            
            # Grid boyutlarını hesapla
            base_width = (grid_width * self.scale) + (self.ruler_size + self.scale) * 2
            base_height = (grid_height * self.scale) + (self.ruler_size + self.scale) * 2
            
            # Resim boyutlarını hesapla
            if self.background_image:
                img_width = int(base_width * self.image_scale)
                img_height = int(base_height * self.image_scale)
                
                # En büyük boyutu al
                width = max(base_width, img_width)
                height = max(base_height, img_height)
            else:
                width = base_width
                height = base_height
            
            # Ekstra boşluk ekle
            width += 100
            height += 100
            
            # Widget boyutunu güncelle
            self.setMinimumSize(width, height)

    def contextMenuEvent(self, event):
        """Sağ tık menüsü"""
        menu = QMenu(self)
        
        # Grid hareketleri
        grid_menu = menu.addMenu('Grid Hareketi')
        
        left = grid_menu.addAction('Sola')
        left.triggered.connect(lambda: self.move_grid(-1, 0))
        
        right = grid_menu.addAction('Sağa')
        right.triggered.connect(lambda: self.move_grid(1, 0))
        
        up = grid_menu.addAction('Yukarı')
        up.triggered.connect(lambda: self.move_grid(0, -1))
        
        down = grid_menu.addAction('Aşağı')
        down.triggered.connect(lambda: self.move_grid(0, 1))
        
        menu.addSeparator()
        
        # Görüntü işlemleri
        reset_zoom = menu.addAction('Zoom Sıfırla')
        reset_zoom.triggered.connect(self.reset_image_scale)
        
        reset_grid = menu.addAction('Grid Konumunu Sıfırla')
        reset_grid.triggered.connect(self.reset_grid_position)
        
        menu.exec_(event.globalPos())

    def reset_image_scale(self):
        """Resim ölçeğini sıfırla"""
        self.form_widget.image_scale = 1.0
        self.form_widget.update()

    def reset_grid_position(self):
        """Grid konumunu sıfırla"""
        self.form_widget.grid_offset = QPoint(0, 0)
        self.form_widget.update()

    def show_usage_guide(self):
        """Kullanım kılavuzunu göster"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Kullanım Kılavuzu")
        msg.setTextFormat(Qt.RichText)
        
        guide_text = """
        <h3>Optik Form Editörü - Kullanım Kılavuzu</h3>
        
        <b>1. FMT Dosyası Yükleme</b>
        <ul>
            <li>Menüden 'Dosya > FMT Yükle' seçin veya Ctrl+F tuşlarına basın</li>
            <li>FMT dosyasını seçin ve açın</li>
        </ul>
        
        <b>2. Excel Dosyası Yükleme</b>
        <ul>
            <li>Menüden 'Dosya > Excel Yükle' seçin veya Ctrl+E tuşlarına basın</li>
            <li>Öğrenci verilerini içeren Excel dosyasını seçin</li>
            <li>Alan eşleştirmelerini yapın</li>
        </ul>
        
        <b>3. Optik Form Resmi Yükleme</b>
        <ul>
            <li>Menüden 'Dosya > Resim Yükle' seçin veya Ctrl+I tuşlarına basın</li>
            <li>Optik form resmini seçin</li>
        </ul>
        
        <b>4. Grid Ayarları</b>
        <ul>
            <li>Yön tuşlarıyla gridi hareket ettirin</li>
            <li>+ ve - tuşlarıyla yakınlaştırıp uzaklaştırın</li>
            <li>Grid boyutunu araç çubuğundan ayarlayın</li>
        </ul>
        
        <b>5. PDF Kaydetme</b>
        <ul>
            <li>Menüden 'Dosya > PDF Kaydet' seçin veya Ctrl+S tuşlarına basın</li>
            <li>Kayıt konumunu seçin</li>
            <li>Tüm öğrenciler için optik formlar oluşturulacaktır</li>
        </ul>
        """
        
        msg.setText(guide_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def show_about_dialog(self):
        """Hakkında penceresini göster"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Hakkında")
        msg.setTextFormat(Qt.RichText)
        
        about_text = """
        <h3>Optik Form Editörü</h3>
        <p><b>Sürüm:</b> 1.0.0</p>
        <p><b>Geliştirici:</b> Bilist Yazılım</p>
        <p><b>İletişim:</b> info@bilistco.com</p>
        <br>
        <p>Bu uygulama, optik form oluşturma ve düzenleme işlemlerini 
        kolaylaştırmak için geliştirilmiştir.</p>
        <br>
        <p>Copyright © 2024 Bilist Yazılım. Tüm hakları saklıdır.</p>
        """
        
        msg.setText(about_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def update_license_status(self):
        """Lisans durumunu güncelle"""
        try:
            success, message = self.license_manager.verify_license()
            if success:
                remaining_days = int(message.split(":")[-1].strip())
                status_text = f"Aktif - {remaining_days} gün"
                status_color = "#28a745"  # Yeşil
            else:
                status_text = "Bulunamadı"
                status_color = "#dc3545"  # Kırmızı
            
            # Status bar'ı güncelle
            self.license_label.setText(f"Lisans Durumu: {status_text}")
            self.license_label.setStyleSheet(f"""
                QLabel {{
                    color: {status_color};
                    font-weight: bold;
                    padding: 2px 8px;
                    border-radius: 4px;
                    background: rgba(255, 255, 255, 0.9);
                }}
            """)
            
        except Exception as e:
            print(f"Lisans durumu güncelleme hatası: {e}")
            self.license_label.setText("Lisans Durumu: Hata")
            self.license_label.setStyleSheet("""
                QLabel {
                    color: #dc3545;
                    font-weight: bold;
                    padding: 2px 8px;
                    border-radius: 4px;
                    background: rgba(255, 255, 255, 0.9);
                }
            """)

    def show_license_info(self):
        """Detaylı lisans bilgisi göster"""
        try:
            # Lisans bilgilerini al
            if os.path.exists('license.json'):
                with open('license.json', 'r') as f:
                    data = json.load(f)
                    license_key = data.get('license_key')
                    
                checker = LicenseManager()
                success, data = checker.check_license(license_key)
                
                if success:
                    remaining_days = data.get('remaining_days', 0)
                    expiry_date = data.get('expiry_date', '')
                    license_type = data.get('license_type', 'Standart')
                    customer_name = data.get('customer_name', 'Belirtilmemiş')
                    
                    info_text = f"""
                    <h3>Lisans Bilgileri</h3>
                    <p><b>Durum:</b> Aktif</p>
                    <p><b>Kalan Süre:</b> {remaining_days} gün</p>
                    <p><b>Bitiş Tarihi:</b> {expiry_date}</p>
                    <p><b>Lisans Tipi:</b> {license_type}</p>
                    <p><b>Lisans Sahibi:</b> {customer_name}</p>
                    <br>
                    <p>Lisans yenilemek için <a href='http://www.bilistco.com/otoform'>www.bilistco.com/otoform</a> adresini ziyaret edin.</p>
                    """
                else:
                    info_text = "Lisans geçersiz veya süresi dolmuş."
            else:
                info_text = "Lisans bilgisi bulunamadı."
                
            msg = QMessageBox()
            msg.setWindowTitle("Lisans Bilgisi")
            msg.setTextFormat(Qt.RichText)
            msg.setText(info_text)
            msg.setIcon(QMessageBox.Information)
            msg.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Lisans bilgisi alınırken hata oluştu: {e}")

class FieldMappingDialog(QDialog):
    def __init__(self, parent, excel_columns, form_fields):
        super().__init__(parent)
        self.excel_columns = excel_columns
        self.form_fields = form_fields
        self.mapping = {}
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Alan Eşleştirme')
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        
        # Açıklama
        info = QLabel("Excel sütunlarını FMT alanlarıyla eşleştirin:")
        info.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Eşleştirme tablosu
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['FMT Alanı', 'Excel Sütunu'])
        self.table.setRowCount(len(self.form_fields))
        
        # Her FMT alanı için bir satır oluştur
        for i, field in enumerate(self.form_fields):
            # FMT alanı
            field_item = QTableWidgetItem(field)
            field_item.setFlags(field_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, field_item)
            
            # Excel sütun seçici
            combo = QComboBox()
            combo.addItem('Seçiniz...')
            combo.addItems(self.excel_columns)
            
            # Otomatik eşleştirme önerisi
            for col in self.excel_columns:
                if field.upper() in col.upper():
                    combo.setCurrentText(col)
                    break
            
            self.table.setCellWidget(i, 1, combo)
        
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)
        
        # Butonlar
        buttons = QHBoxLayout()
        ok_btn = QPushButton('Tamam')
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('İptal')
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)
        
        self.setLayout(layout)
    
    def get_mapping(self):
        """Eşleştirmeleri sözlük olarak döndür"""
        mapping = {}
        for row in range(self.table.rowCount()):
            fmt_field = self.table.item(row, 0).text()
            combo = self.table.cellWidget(row, 1)
            if combo.currentText() != 'Seçiniz...':
                mapping[fmt_field] = combo.currentText()
        return mapping

class FormWidget(QWidget):
    def __init__(self, parent, parser):
        super().__init__(parent)
        self.parser = parser
        self.scale = 30
        self.min_scale = 10
        self.max_scale = 100
        self.ruler_size = 30
        self.image_scale = 1.0
        self.min_image_scale = 0.1
        self.max_image_scale = 5.0
        self.grid_offset = QPoint(0, 0)
        self.background_image = None
        self.marked_cells = set()
        
        # Varsayılan grid boyutları
        self.default_grid_width = 30
        self.default_grid_height = 40
        
        # Grid boyutlarını ayarla
        if self.parser:
            self.grid_width, self.grid_height = self.parser.get_grid_size()
        else:
            self.grid_width = self.default_grid_width
            self.grid_height = self.default_grid_height
        
        # Widget boyutunu ayarla
        self.update_size()
        
        # Mouse takibi için
        self.setMouseTracking(True)
        self.hover_pos = None
        self.resizing = False
        self.resize_start_pos = None
        self.resize_start_size = None
        self.resize_handle_size = 15
        
        # Klavye odağı için
        self.setFocusPolicy(Qt.StrongFocus)

    def get_grid_size(self):
        """Grid boyutlarını al"""
        if self.parser:
            self.grid_width, self.grid_height = self.parser.get_grid_size()
        return self.grid_width, self.grid_height

    def update_size(self):
        """Widget boyutunu güncelle"""
        # Grid boyutlarını güncelle
        self.grid_width, self.grid_height = self.get_grid_size()
        
        # Grid boyutlarını hesapla
        base_width = (self.grid_width * self.scale) + (self.ruler_size + self.scale) * 2
        base_height = (self.grid_height * self.scale) + (self.ruler_size + self.scale) * 2
        
        # Resim boyutlarını hesapla
        if self.background_image:
            img_width = int(base_width * self.image_scale)
            img_height = int(base_height * self.image_scale)
            
            # En büyük boyutu al
            width = max(base_width, img_width)
            height = max(base_height, img_height)
        else:
            width = base_width
            height = base_height
        
        # Ekstra boşluk ekle
        width += 100
        height += 100
        
        # Widget boyutunu güncelle
        self.setMinimumSize(width, height)

    def wheelEvent(self, event):
        """Mouse tekerleği ile zoom"""
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            old_scale = self.scale
            
            # Daha hassas zoom için 1 birimlik değişim
            if delta > 0 and self.scale < self.max_scale:
                self.scale += 1
            elif delta < 0 and self.scale > self.min_scale:
                self.scale -= 1
            
            # Resmi grid ile orantılı olarak ölçekle
            if self.background_image:
                scale_ratio = self.scale / old_scale
                self.image_scale *= scale_ratio
            
            self.update_size()
            self.update()
            event.accept()
        else:
            event.ignore()
    
    def keyPressEvent(self, event):
        """Klavye tuşlarını yakala - sadece grid hareketi için"""
        # Yön tuşları için adım miktarı
        step = 1  # Hassas hareket için 1 piksel
        
        if event.key() == Qt.Key_Left:
            self.grid_offset.setX(self.grid_offset.x() - step)
            self.update()
            event.accept()
        
        elif event.key() == Qt.Key_Right:
            self.grid_offset.setX(self.grid_offset.x() + step)
            self.update()
            event.accept()
        
        elif event.key() == Qt.Key_Up:
            self.grid_offset.setY(self.grid_offset.y() - step)
            self.update()
            event.accept()
        
        elif event.key() == Qt.Key_Down:
            self.grid_offset.setY(self.grid_offset.y() + step)
            self.update()
            event.accept()
        
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.background_image:
            if self.is_on_resize_handle(event.pos()):
                self.resizing = True
                self.resize_start_pos = event.pos()
                self.resize_start_size = self.background_image.size()
                self.setCursor(Qt.SizeFDiagCursor)
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.resizing and self.background_image:
            # Mouse hareketi ile ölçek değişimini hesapla
            delta = event.pos() - self.resize_start_pos
            scale_change = delta.x() / 200.0  # Hassasiyet ayarı
            
            # Yeni ölçeği hesapla
            new_scale = max(min(self.resize_start_scale + scale_change, 
                              self.max_image_scale), 
                          self.min_image_scale)
            
            # Ölçeği güncelle
            self.image_scale = new_scale
            self.update()
            return
            
        # Normal mouse hareketi
        if self.background_image and self.is_on_resize_handle(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        
        # Orijinal mouse takibi
        x = (event.x() - self.ruler_size - self.scale) // self.scale
        y = (event.y() - self.ruler_size - self.scale) // self.scale
        
        # Grid boyutlarını al
        width, height = self.parser.get_grid_size()
        
        # Geçerli grid alanı içinde mi kontrol et
        if 0 <= x < width and 0 <= y < height:
            self.hover_pos = (x, y)
            # Mouse'un üzerinde olduğu alanı bul
            self.hover_field = None
            for field in self.parser.fields:
                if (field.start_x - 1 <= x <= field.end_x - 1 and 
                    field.start_y - 1 <= y <= field.end_y - 1):
                    self.hover_field = field
                    break
        else:
            self.hover_pos = None
            self.hover_field = None
        
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Grid boyutlarını al
        grid_width, grid_height = self.get_grid_size()
        
        # PDF modu için kenar boşluklarını sıfırla
        ruler = self.ruler_size if not hasattr(self, 'pdf_mode') else 0
        edge = self.scale if not hasattr(self, 'pdf_mode') else 0
        
        # Beyaz arkaplan çiz
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        # Normal modda resim çiz
        if not hasattr(self, 'pdf_mode'):
            if self.background_image:
                image_x = ruler + edge
                image_y = ruler + edge
                
                base_width = grid_width * self.scale
                base_height = grid_height * self.scale
                
                scaled_width = int(base_width * self.image_scale)
                scaled_height = int(base_height * self.image_scale)
                
                scaled_pixmap = self.background_image.scaled(
                    scaled_width,
                    scaled_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                painter.drawPixmap(image_x, image_y, scaled_pixmap)
            
            # Grid çizgileri
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            
            # Yatay çizgiler
            for y in range(grid_height + 1):
                y_pos = y * self.scale + ruler + edge + self.grid_offset.y()
                painter.drawLine(
                    ruler + edge + self.grid_offset.x(), y_pos,
                    ruler + edge + grid_width * self.scale + self.grid_offset.x(), y_pos
                )
            
            # Dikey çizgiler
            for x in range(grid_width + 1):
                x_pos = x * self.scale + ruler + edge + self.grid_offset.x()
                painter.drawLine(
                    x_pos, ruler + edge + self.grid_offset.y(),
                    x_pos, ruler + edge + grid_height * self.scale + self.grid_offset.y()
                )
            
            # FMT alanlarını çiz
            if self.parser and self.parser.fields:
                painter.setPen(QPen(QColor(100, 100, 100)))
                for field in self.parser.fields:
                    # Alan sınırlarını çiz
                    x = (field.start_x - 1) * self.scale + ruler + edge + self.grid_offset.x()
                    y = (field.start_y - 1) * self.scale + ruler + edge + self.grid_offset.y()
                    width = (field.end_x - field.start_x + 1) * self.scale
                    height = (field.end_y - field.start_y + 1) * self.scale
                    
                    painter.drawRect(x, y, width, height)
                    painter.drawText(x, y - 5, field.field_name)
        
        # İşaretli hücreleri ve değerleri çiz (hem normal mod hem PDF için)
        if self.marked_cells and hasattr(self, 'marked_values'):
            # Her alan için değerleri yaz
            for field_name, value in self.marked_values.items():
                field = next((f for f in self.parser.fields if f.field_name == field_name), None)
                if field and value:
                    # Değeri kutulara yaz
                    painter.setPen(QPen(QColor(0, 0, 0)))
                    font = painter.font()
                    font.setPointSize(int(self.scale * 0.4))
                    painter.setFont(font)
                    
                    # Her karakter için
                    for i, char in enumerate(str(value)):
                        x = (field.start_x + i - 1) * self.scale + ruler + edge + self.grid_offset.x()
                        y = (field.start_y - 2) * self.scale + ruler + edge + self.grid_offset.y()
                        
                        # Karakteri ortala
                        rect = QRectF(x, y, self.scale, self.scale)
                        painter.drawText(rect, Qt.AlignCenter, char)
        
            # İşaretlemeleri çiz
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0))
            
            for x, y in self.marked_cells:
                cell_x = x * self.scale + ruler + edge + self.grid_offset.x()
                cell_y = y * self.scale + ruler + edge + self.grid_offset.y()
                
                mark_size = int(self.scale * 0.7)
                mark_x = cell_x + (self.scale - mark_size) // 2
                mark_y = cell_y + (self.scale - mark_size) // 2
                
                painter.drawEllipse(mark_x, mark_y, mark_size, mark_size)
    
    def draw_area(self, painter, area):
        """Alan tipine göre çizim yap"""
        x_start = area.start_x - 1
        x_end = area.end_x - 1
        y_start = area.start_y - 1
        y_end = area.end_y - 1
        
        # Alan için daireleri çiz
        painter.setPen(QPen(QColor('black'), 1))
        painter.setBrush(Qt.NoBrush)
        
        # Her hücre için daire ve metin çiz
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                # Daire çizimi
                center_x = int(x * self.scale + self.scale/2)
                center_y = int(y * self.scale + self.scale/2)
                diameter = int(self.scale * 0.8)
                
                left = int(center_x - diameter/2)
                top = int(center_y - diameter/2)
                
                painter.drawEllipse(left, top, diameter, diameter)
                
                # Metin çizimi
                try:
                    if area.options == '0123456789':
                        text = str(y - y_start)
                    elif area.options in ['ABCD', 'ABCDE']:
                        option_index = y - y_start
                        if option_index < len(area.options):
                            text = area.options[option_index]
                        else:
                            continue
                    else:
                        # Diğer seçenek tipleri için
                        option_index = y - y_start
                        if option_index < len(area.options):
                            text = area.options[option_index]
                        else:
                            continue
                    
                    # Metni çiz
                    text_rect = QRect(left, top, diameter, diameter)
                    painter.drawText(text_rect, Qt.AlignCenter, text)
                    
                except Exception as e:
                    print(f"Metin çizim hatası: {e}")
                    continue
    
    def draw_hover_effect(self, painter):
        if self.hover_pos:
            x, y = self.hover_pos
            
            # Hover dairesini çiz
            painter.setPen(QPen(QColor('red'), 2))
            painter.setBrush(Qt.NoBrush)
            
            center_x = int(x * self.scale + self.scale/2)
            center_y = int(y * self.scale + self.scale/2)
            diameter = int(self.scale * 0.8)
            
            left = int(center_x - diameter/2)
            top = int(center_y - diameter/2)
            painter.drawEllipse(left, top, diameter, diameter)
            
            # Bilgi metni için arka planı temizle
            painter.resetTransform()  # Koordinat sistemini sıfırla
            
            # Bilgi metni için arka plan
            text_rect = QRect(
                self.ruler_size + 10,  # Sol kenardan boşluk
                10,  # Üst kenardan boşluk
                self.width() - self.ruler_size - 20,  # Genişlik
                30  # Yükseklik
            )
            
            # Bilgi metnini hazırla
            info_text = f"Koordinat: ({x+1}, {y+1})"
            if self.hover_field:
                info_text += f" | Alan: {self.hover_field.field_name}"
                if self.hover_field.is_coding_area:
                    info_text += " (Kodlanacak Alan)"
                else:
                    info_text += " (Kodlanmayacak Alan)"
                info_text += f" | Seçenekler: {self.hover_field.options}"
            
            # Arka plan ve metin çizimi
            painter.fillRect(text_rect, QColor(255, 255, 255, 240))  # Yarı saydam beyaz arka plan
            painter.setPen(QPen(QColor('black'), 1))
            painter.drawRect(text_rect)
            painter.drawText(text_rect, Qt.AlignCenter, info_text)
    
    def draw_rulers(self, painter):
        width, height = self.parser.get_grid_size()
        
        # Cetvel arka planı
        painter.fillRect(0, 0, self.width(), self.ruler_size, QColor('#f0f0f0'))
        painter.fillRect(0, 0, self.ruler_size, self.height(), QColor('#f0f0f0'))
        
        # Yatay cetvel (sütun numaraları)
        painter.setPen(QPen(QColor('black'), 1))
        for x in range(width):
            x_pos = x * self.scale + self.ruler_size + self.scale
            if x % 5 == 0:  # Her 5 birimde bir sayı göster
                painter.drawText(x_pos - 5, self.ruler_size - 5, str(x + 1))
            painter.drawLine(x_pos, 0, x_pos, self.ruler_size)
        
        # Dikey cetvel (satır numaraları)
        for y in range(height):
            y_pos = y * self.scale + self.ruler_size + self.scale
            if y % 5 == 0:  # Her 5 birimde bir sayı göster
                painter.drawText(2, y_pos + 12, str(y + 1))
            painter.drawLine(0, y_pos, self.ruler_size, y_pos)
        
        # Cetvel çerçevesi
        painter.setPen(QPen(QColor('black'), 1))
        painter.drawRect(0, 0, self.width(), self.ruler_size)
        painter.drawRect(0, 0, self.ruler_size, self.height())
    
    def show_context_menu(self, pos):
        if self.current_selection:
            menu = QMenu(self)
            
            coding_action = menu.addAction("Kodlanacak Alan")
            non_coding_action = menu.addAction("Kodlanmayacak Alan")
            
            action = menu.exec_(self.mapToGlobal(pos))
            
            if action == coding_action:
                start_x, end_x, start_y, end_y = self.current_selection
                field = FormField(
                    start_x=start_x,
                    end_x=end_x,
                    start_y=start_y,
                    end_y=end_y,
                    field_type='K',  # Varsayılan tip
                    option_type='D',  # Kodlanacak alan
                    options='0123456789',  # Varsayılan seçenekler
                    format_type='X2',  # Varsayılan format
                    field_name='Yeni Alan'  # Varsayılan isim
                )
                self.parser.coding_areas.append(field)
                self.current_selection = None
                self.update()
            
            elif action == non_coding_action:
                start_x, end_x, start_y, end_y = self.current_selection
                field = FormField(
                    start_x=start_x,
                    end_x=end_x,
                    start_y=start_y,
                    end_y=end_y,
                    field_type='K',
                    option_type='Y',  # Kodlanmayacak alan
                    options='ABCDE',
                    format_type='X2',
                    field_name='Yeni Alan'
                )
                self.parser.non_coding_areas.append(field)
                self.current_selection = None
                self.update()

    def set_background_image(self, pixmap):
        """Arka plan resmini ayarla"""
        self.background_image = pixmap
        self.update()
    
    def move_grid(self, dx, dy):
        """Grid'i ve işaretli noktaları hareket ettir"""
        self.grid_offset += QPoint(dx, dy)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.background_image:
            if self.is_on_resize_handle(event.pos()):
                self.resizing = True
                self.resize_start_pos = event.pos()
                self.resize_start_size = self.background_image.size()
                self.setCursor(Qt.SizeFDiagCursor)
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.resizing:
            self.resizing = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
    
    def is_on_resize_handle(self, pos):
        """Mouse'un herhangi bir resize handle üzerinde olup olmadığını kontrol et"""
        if not self.background_image:
            return False
        
        # Resmin konumu ve boyutları
        image_x = self.ruler_size + self.scale
        image_y = self.ruler_size + self.scale
        scaled_width = self.grid_width * self.scale
        scaled_height = self.grid_height * self.scale
        
        # Köşe tutamaclarının konumları
        corners = [
            (image_x + scaled_width - self.resize_handle_size, image_y + scaled_height - self.resize_handle_size),  # Sağ alt
            (image_x + scaled_width - self.resize_handle_size, image_y),  # Sağ üst
            (image_x, image_y + scaled_height - self.resize_handle_size),  # Sol alt
            (image_x, image_y)  # Sol üst
        ]
        
        # Her tutamacı kontrol et
        for x, y in corners:
            handle_rect = QRect(x, y, self.resize_handle_size, self.resize_handle_size)
            if handle_rect.contains(pos):
                return True
        
        return False

    def zoom_in(self):
        """Yakınlaştırma"""
        if self.scale < self.max_scale:
            # Eski ölçeği sakla
            old_scale = self.scale
            
            # Grid ölçeğini artır
            self.scale += 2
            
            # Resmi grid ile orantılı olarak büyüt
            if self.background_image:
                # Ölçek değişim oranı
                scale_ratio = self.scale / old_scale
                # Resim ölçeğini güncelle
                self.image_scale *= scale_ratio
            
            self.update_size()
            self.update()

    def zoom_out(self):
        """Uzaklaştırma"""
        if self.scale > self.min_scale:
            # Eski ölçeği sakla
            old_scale = self.scale
            
            # Grid ölçeğini azalt
            self.scale -= 2
            
            # Resmi grid ile orantılı olarak küçült
            if self.background_image:
                # Ölçek değişim oranı
                scale_ratio = self.scale / old_scale
                # Resim ölçeğini güncelle
                self.image_scale *= scale_ratio
            
            self.update_size()
            self.update()

def main():
    app = QApplication(sys.argv)
    ex = OptikFormApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 