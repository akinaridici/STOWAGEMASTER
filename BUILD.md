# EXE Oluşturma Rehberi

Bu uygulamayı Windows executable (.exe) dosyasına dönüştürmek için PyInstaller kullanılıyor.

## Hızlı Başlangıç

### Otomatik Yöntem (Önerilen)

1. **Build script'i çalıştırın:**
   ```bash
   build_exe.bat
   ```
   
   Bu script otomatik olarak:
   - Gerekli paketleri yükler
   - EXE dosyasını oluşturur
   - Sonuçları `dist` klasörüne koyar

2. **EXE dosyasını bulun:**
   - `dist\TankerStowagePlan.exe`

### Manuel Yöntem

1. **Gerekli paketleri yükleyin:**
   ```bash
   pip install -r requirements-build.txt
   ```

2. **PyInstaller ile EXE oluşturun:**
   ```bash
   pyinstaller --name="TankerStowagePlan" --onefile --windowed --add-data "storage;storage" main.py
   ```

3. **Sonuç:**
   - EXE dosyası: `dist\TankerStowagePlan.exe`

## Gelişmiş Seçenekler

### Icon Eklemek

EXE dosyasına bir icon eklemek isterseniz:

```bash
pyinstaller --name="TankerStowagePlan" --onefile --windowed --icon=icon.ico --add-data "storage;storage" main.py
```

### Tek Klasör (One-Folder) Modu

Daha hızlı başlatma için (daha fazla dosya):

```bash
pyinstaller --name="TankerStowagePlan" --windowed --add-data "storage;storage" main.py
```

Bu durumda tüm dosyaları `dist\TankerStowagePlan\` klasöründen kopyalamanız gerekir.

## Sorun Giderme

### "Module not found" Hatası

PyInstaller bazen bazı modülleri bulamaz. Bunları ekleyin:

```bash
pyinstaller --hidden-import=MODULE_NAME ...
```

### "Storage klasörü bulunamadı" Hatası

EXE dosyasını çalıştırırken storage klasörü aynı dizinde olmalı. EXE'yi bir yere kopyaladığınızda storage klasörünü de kopyalayın.

### EXE Çok Büyük

PyInstaller tüm PyQt6 kütüphanesini dahil eder (~50-100 MB). Bu normaldir.

## Dosya Yapısı

```
stowage_master/
├── main.py                    # Ana dosya
├── build_exe.bat              # Build script
├── requirements-build.txt     # Build için gerekli paketler
├── dist/                      # Oluşturulan EXE (build sonrası)
│   └── TankerStowagePlan.exe
└── build/                     # Geçici build dosyaları
```

## Notlar

- İlk build işlemi biraz uzun sürebilir (2-5 dakika)
- EXE dosyası yaklaşık 50-100 MB olabilir (PyQt6 dahil)
- Windows Defender veya antivirüs yazılımı ilk çalıştırmada uyarı verebilir (normal)

