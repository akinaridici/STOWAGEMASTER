# Kurulum Talimatları

## Python Kurulumu

1. Python'u indirin: https://www.python.org/downloads/
2. Kurulum sırasında **"Add Python to PATH"** seçeneğini işaretleyin.
3. Kurulumu tamamlayın.

## Bağımlılıkları Yükleme

Python kurulumundan sonra PowerShell veya Command Prompt'u yeniden açın ve şu komutu çalıştırın:

```powershell
python -m pip install -r requirements.txt
```

Alternatif olarak, eğer `python` komutu çalışmazsa:

```powershell
python3 -m pip install -r requirements.txt
```

veya

```powershell
py -m pip install -r requirements.txt
```

## Uygulamayı Çalıştırma

Bağımlılıklar yüklendikten sonra:

```powershell
python main.py
```

veya

```powershell
python3 main.py
```

veya

```powershell
py main.py
```

## Sorun Giderme

### "pip is not recognized" hatası
- Python'un PATH'e eklendiğinden emin olun
- `python -m pip` komutunu kullanın (doğrudan `pip` yerine)

### "python is not recognized" hatası
- Python'u yeniden yükleyin ve "Add to PATH" seçeneğini işaretleyin
- PowerShell'i yeniden başlatın
- `py` launcher'ı deneyin: `py -m pip install -r requirements.txt`

