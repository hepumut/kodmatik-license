import logging

logger = logging.getLogger(__name__)

class FormField:
    def __init__(self, start_x, end_x, start_y, end_y, field_type, 
                 option_type, options, format_type, field_name):
        """
        FMT dosyasındaki koordinat sistemi:
        İlk iki sayı (parts[0], parts[1]): Dikey koordinatlar (yukarıdan aşağı)
        Son iki sayı (parts[2], parts[3]): Yatay koordinatlar (soldan sağa)
        
        Örnek: 01=29=02=11=K=D=ABC...=X2=ADI=
        01-29: Dikey koordinatlar (yukarıdan aşağı)
        02-11: Yatay koordinatlar (soldan sağa)
        """
        try:
            # Koordinatları sayıya çevir
            self.start_y = int(start_y)  # Dikey başlangıç
            self.end_y = int(end_y)      # Dikey bitiş
            self.start_x = int(start_x)  # Yatay başlangıç
            self.end_x = int(end_x)      # Yatay bitiş
            
            # Koordinat kontrolü
            if (self.start_x <= 0 or self.end_x <= 0 or 
                self.start_y <= 0 or self.end_y <= 0):
                raise ValueError("Koordinatlar sıfır veya negatif olamaz")
                
            if self.start_x > self.end_x or self.start_y > self.end_y:
                raise ValueError("Başlangıç koordinatları bitiş koordinatlarından büyük olamaz")
                
        except ValueError as e:
            raise ValueError(f"Geçersiz koordinat değeri: {e}")
        
        self.field_type = field_type
        self.option_type = option_type
        self.options = options
        self.format_type = format_type
        self.field_name = field_name
        self.is_coding_area = option_type == 'D'

class FMTParser:
    def __init__(self):
        # Varsayılan değerler
        self.DEFAULT_WIDTH = 42   # Varsayılan genişlik
        self.DEFAULT_HEIGHT = 53  # Varsayılan yükseklik
        self.clear()
    
    def clear(self):
        """Tüm verileri temizle ve varsayılan grid boyutunu ayarla"""
        self.fields = []
        self.coding_areas = []
        self.non_coding_areas = []
        self.grid_size = (self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)  # (yatay, dikey)
        print(f"Grid varsayılan boyuta ayarlandı: {self.grid_size}")
    
    def parse_file(self, filename):
        """FMT dosyasını oku ve ayrıştır"""
        print("\n=== FMT DOSYASI OKUMA BAŞLADI ===")
        print(f"Dosya: {filename}")
        
        self.clear()
        print("Eski veriler temizlendi")
        
        try:
            # Dosyayı oku
            content = None
            for encoding in ['utf-8', 'cp1254', 'iso-8859-9', 'latin1']:
                try:
                    with open(filename, 'r', encoding=encoding) as file:
                        content = file.readlines()
                        print(f"Dosya {encoding} ile okundu - {len(content)} satır")
                        break
                except UnicodeDecodeError:
                    continue
            
            if not content:
                print("HATA: Dosya okunamadı!")
                return False
            
            # İlk satırı bul (grid boyutları)
            grid_found = False
            for line in content:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('=')
                if len(parts) >= 5 and parts[4] == '*':
                    try:
                        # Grid boyutlarını al
                        dikey = int(parts[0])    # Satır sayısı
                        yatay = int(parts[1])    # Sütun sayısı
                        
                        print(f"Grid boyutları bulundu: {dikey}x{yatay}")
                        self.grid_size = (yatay, dikey)  # (genişlik, yükseklik)
                        grid_found = True
                        break
                        
                    except (ValueError, IndexError) as e:
                        print(f"Grid boyutları okunamadı: {e}")
                        continue
            
            if not grid_found:
                print("HATA: Grid boyutları bulunamadı!")
                return False
            
            # Alanları işle
            for line in content:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('=')
                if len(parts) < 9 or parts[4] == '*':
                    continue
                
                try:
                    field = FormField(
                        start_x=parts[2],  # Yatay başlangıç
                        end_x=parts[3],    # Yatay bitiş
                        start_y=parts[0],  # Dikey başlangıç
                        end_y=parts[1],    # Dikey bitiş
                        field_type=parts[4],
                        option_type=parts[5],
                        options=parts[6],
                        format_type=parts[7],
                        field_name=parts[8]
                    )
                    
                    self.fields.append(field)
                    if field.is_coding_area:
                        self.coding_areas.append(field)
                    else:
                        self.non_coding_areas.append(field)
                        
                    print(f"Alan eklendi: {field.field_name}")
                    print(f"Koordinatlar: ({field.start_x}, {field.start_y}) - ({field.end_x}, {field.end_y})")
                    
                except Exception as e:
                    print(f"HATA: Alan oluşturulamadı - {e}")
                    continue
            
            print("\n=== SONUÇLAR ===")
            print(f"Grid boyutu: {self.grid_size}")
            print(f"Toplam alan sayısı: {len(self.fields)}")
            
            return True
            
        except Exception as e:
            print(f"\nKRİTİK HATA: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_grid_size(self):
        """Grid boyutlarını döndür: (yatay, dikey)"""
        return self.grid_size

    def get_coding_areas(self):
        return self.coding_areas
    
    def get_non_coding_areas(self):
        return self.non_coding_areas

    def parse_content(self, content):
        print("\nFMT içeriği ayrıştırılıyor...")
        
        # İlk satırı bul (grid boyutları)
        grid_found = False
        for line in content:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('=')
            if len(parts) >= 9 and parts[4] == '*':
                try:
                    # Grid boyutlarını al
                    dikey = int(parts[0])    # Satır sayısı
                    yatay = int(parts[1])    # Sütun sayısı
                    
                    print(f"Grid boyutları bulundu: {dikey}x{yatay}")
                    self.grid_size = (yatay, dikey)  # (genişlik, yükseklik)
                    grid_found = True
                    break
                    
                except (ValueError, IndexError) as e:
                    print(f"Grid boyutları okunamadı: {e}")
                    continue
        
        if not grid_found:
            print("UYARI: Grid boyutları bulunamadı!")
            return False
        
        # Alanları işle
        for line in content:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('=')
            if len(parts) < 9 or parts[4] == '*':
                continue
            
            try:
                field = FormField(
                    start_x=parts[2],  # Yatay başlangıç
                    end_x=parts[3],    # Yatay bitiş
                    start_y=parts[0],  # Dikey başlangıç
                    end_y=parts[1],    # Dikey bitiş
                    field_type=parts[4],
                    option_type=parts[5],
                    options=parts[6],
                    format_type=parts[7],
                    field_name=parts[8]
                )
                
                self.fields.append(field)
                if field.is_coding_area:
                    self.coding_areas.append(field)
                else:
                    self.non_coding_areas.append(field)
                    
                print(f"Alan eklendi: {field.field_name}")
                
            except Exception as e:
                print(f"Alan oluşturma hatası: {e}")
                continue
        
        print(f"\nToplam {len(self.fields)} alan işlendi")
        return True 