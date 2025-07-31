# Excel Import Templates

Bu klasördeki Excel dosyaları, Django admin panelinde veri import işlemleri için kullanılabilir.

## Kullanım Talimatları:

1. İstediğiniz template dosyasını açın
2. Dosyadaki sütun başlıklarını değiştirmeyin
3. Verilerinizi ilgili sütunlara girin
4. Dosyayı kaydedin
5. Django admin panelinde ilgili modele gidin
6. "Import" butonuna tıklayın
7. Dosyanızı seçin ve upload edin

## Template Dosyaları:

### Item Master (Ürün Yönetimi)
- item_master_status_template.xlsx - Ürün durumları
- item_master_stock_types_template.xlsx - Stok türleri  
- item_master_brands_template.xlsx - Markalar
- item_master_categories_template.xlsx - Kategoriler
- item_master_products_template.xlsx - Ana ürünler
- inventory_items_template.xlsx - Stok ürünleri
- item_spare_parts_template.xlsx - Yedek parça ilişkileri

### Customer (Müşteri Yönetimi)
- customer_countries_template.xlsx - Ülkeler
- customer_cities_template.xlsx - Şehirler
- customer_counties_template.xlsx - İlçeler
- customer_districts_template.xlsx - Mahalleler
- customer_core_business_template.xlsx - Ana iş kolları
- customer_companies_template.xlsx - Müşteri firmaları
- customer_contacts_template.xlsx - İletişim bilgileri
- customer_addresses_template.xlsx - Adresler
- customer_working_hours_template.xlsx - Çalışma saatleri

### Warranty & Services (Garanti ve Servisler)
- warranty_breakdown_categories_template.xlsx - Arıza kategorileri
- warranty_breakdown_reasons_template.xlsx - Arıza nedenleri
- warranty_installations_template.xlsx - Kurulumlar
- warranty_follow_ups_template.xlsx - Garanti takipleri
- service_follow_ups_template.xlsx - Servis takipleri
- maintenance_records_template.xlsx - Bakım kayıtları

## Önemli Notlar:

- Foreign Key (ilişki) alanları için mevcut kayıtların tam adlarını kullanın
- Tarih formatı: YYYY-MM-DD (örn: 2024-12-31)
- Boolean (doğru/yanlış) alanları için: True/False
- Boş bırakabileceğiniz alanlar template'te belirtilmiştir

## Sorun Giderme:

- Import sırasında hata alırsanız, sütun başlıklarının değişmediğinden emin olun
- Foreign Key hatalarında, referans verdiğiniz kayıtların sistemde mevcut olduğunu kontrol edin
- Tarih formatı hatalarında YYYY-MM-DD formatını kullanın
