# Tanker Stowage Plan Uygulaması

Tanker gemilerinde çalışan kargo zabitlerine yardımcı olmak üzere geliştirilmiş yükleme planı (stowage plan) uygulaması.

## Özellikler

- **Gemi Profili Yönetimi:** Geminin tank sayısını ve hacimlerini bir kez girerek saklayabilme
- **Yükleme Talebi Girişi:** Birden fazla yük çeşidi ve alıcı bilgisi ile yükleme talepleri oluşturma
- **Otomatik Optimizasyon:** Gelen yükleme taleplerini geminin tank kapasiteleriyle karşılaştırarak en optimum yükleme planını oluşturma
- **Plan Arşivleme:** Başarıyla oluşturulmuş planları kaydedip gerektiğinde geri yükleme

## Kurulum

1. Python 3.8 veya üzeri sürümün yüklü olduğundan emin olun
2. Gerekli bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

## Kullanım

Uygulamayı çalıştırmak için:
```bash
python main.py
```

## Teknolojiler

- Python 3.8+
- PyQt6
- JSON (veri saklama)

