# Excel Import Templates

Bu dizin, Django admin panelinde veri yüklemek için kullanılacak Excel şablonlarını içerir.

## Kullanım

1. Admin paneline gidin
2. İlgili model sayfasına gidin (örneğin ItemMaster)
3. "Import" butonuna tıklayın
4. İlgili Excel şablonunu kullanarak verileri hazırlayın
5. Dosyayı yükleyin

## Şablonlar

### ItemMaster (Ana Ürünler)
**Alanlar:**
- shortcode: Ürün kısa kodu (zorunlu, benzersiz)
- name: Ürün adı
- description: Açıklama
- category: Kategori adı
- status: Durum
- brand_name: Marka adı
- stock_type: Stok tipi (Ticari/Yedek Parça)

### InventoryItem (Envanter Kalemleri)
**Alanlar:**
- item_shortcode: Ürün kısa kodu
- item_name: Ürün adı
- serial_no: Seri numarası (benzersiz)
- production_date: Üretim tarihi (YYYY-MM-DD formatında)
- in_used: Kullanımda mı (True/False)

### Category (Kategoriler)
**Alanlar:**
- category_name: Kategori adı (benzersiz)
- parent_category: Üst kategori adı (varsa)
- slug: URL dostu ad (otomatik oluşturulur)

### Brand (Markalar)
**Alanlar:**
- name: Marka adı (benzersiz)

### StockType (Stok Tipleri)
**Alanlar:**
- name: Stok tipi adı (Ticari/Yedek Parça)

### Status (Durumlar)
**Alanlar:**
- status: Durum adı

### ItemSparePart (Yedek Parça İlişkileri)
**Alanlar:**
- main_item_shortcode: Ana ürün kısa kodu
- spare_part_shortcode: Yedek parça kısa kodu

## Önemli Notlar

1. Excel dosyalarında ilk satır başlık satırı olmalı
2. Tarih alanları YYYY-MM-DD formatında olmalı
3. Boolean alanlar True/False değerleri almalı
4. Foreign key alanlar için referans verilen kaydın var olması gerekir
5. Zorunlu alanlar boş bırakılamaz
6. Import işlemi öncesinde verilerinizi yedekleyin

## Hata Durumları

Import sırasında hata alırsanız:
1. Excel dosyasının formatını kontrol edin
2. Zorunlu alanların dolu olduğundan emin olun
3. Foreign key referanslarının doğru olduğunu kontrol edin
4. Benzersiz alanların tekrar etmediğini kontrol edin
