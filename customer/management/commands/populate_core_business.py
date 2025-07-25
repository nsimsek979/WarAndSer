# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from customer.models import CoreBusiness
from django.db import transaction
import sys
import os

class Command(BaseCommand):
    help = "Populates CoreBusiness with ITO meslek gruplari and comprehensive core business data"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing CoreBusiness data before populating',
        )

    def handle(self, *args, **options):
        # ITO Meslek Gruplari ve Kapsamli Core Business Listesi
        CORE_BUSINESS_DATA = [
            # A - TARIM, ORMANCILIK VE BALIKCILIK
            "Bitkisel Uretim",
            "Hayvancilik",
            "Karma Tarim (Bitkisel ve Hayvansal Uretim)",
            "Tarimsal Destekleyici Hizmetler ve Hasat Sonrasi Faaliyetler",
            "Avcilik ve Ilgili Hizmet Faaliyetleri",
            "Ormancilik ve Tomrukculuk",
            "Balikcilik",
            "Su Urunleri Yetistiriciligi",
            
            # B - MADENCILIK VE TAS OCAKCILIGI
            "Komur ve Linyit Cikarimi",
            "Ham Petrol ve Dogal Gaz Cikarimi",
            "Metal Cevheri Madenciligi",
            "Diger Madencilik ve Tas Ocakciligi",
            "Madenciligi Destekleyici Hizmet Faaliyetleri",
            
            # C - IMALAT
            "Gida Urunleri Imalati",
            "Icecek Imalati",
            "Tutun Urunleri Imalati",
            "Tekstil Urunleri Imalati",
            "Giyim Esyasi Imalati",
            "Deri ve Ilgili Urunlerin Imalati",
            "Agac ve Agac Urunleri Imalati (Mobilya Haric)",
            "Kagit ve Kagit Urunleri Imalati",
            "Kayitli Medyanin Basilmasi ve Cogaltilmasi",
            "Kok Komuru ve Rafine Edilmis Petrol Urunleri Imalati",
            "Kimyasal Madde ve Urunlerin Imalati",
            "Temel Eczacilik Urunleri ve Eczaciliga Iliskin Malzemelerin Imalati",
            "Kaucuk ve Plastik Urunlerin Imalati",
            "Diger Metalik Olmayan Mineral Urunlerin Imalati",
            "Ana Metal Sanayii",
            "Makine ve Ekipman Haric Fabrikasyon Metal Urunlerin Imalati",
            "Bilgisayar, Elektronik ve Optik Urunlerin Imalati",
            "Elektrikli Techizat Imalati",
            "Baska Yerde Siniflandirilmamis Makine ve Ekipman Imalati",
            "Motorlu Kara Tasiti, Treyler (Romork) ve Yari Treyler (Yari Romork) Imalati",
            "Diger Ulasim Araclarinin Imalati",
            "Mobilya Imalati",
            "Diger Imalatlar",
            "Makine ve Ekipmanin Kurulumu ve Onarimi",
            
            # D - ELEKTRIK, GAZ, BUHAR VE IKLIMLENDIRME URETIMI VE DAGITIMI
            "Elektrik Enerjisi Uretimi, Iletimi ve Dagitimi",
            "Gaz Uretimi ve Dagitimi",
            "Buhar ve Iklimlendirme Temini",
            
            # E - SU TEMINI; KANALIZASYON, ATIK YONETIMI VE IYILESTIRME FAALIYETLERI
            "Su Toplama, Aritma ve Dagitimi",
            "Kanalizasyon",
            "Atik Toplama, Isleme ve Bertaraf Faaliyetleri",
            "Maddi Degerin Kazanilmasi Faaliyetleri",
            "Iyilestirme Faaliyetleri ve Diger Atik Yonetimi Hizmetleri",
            
            # F - INSAAT
            "Bina Insaati",
            "Bina Disi Yapilarin Insaati",
            "Ozel Insaat Faaliyetleri",
            
            # G - TOPTAN VE PERAKENDE TICARET
            "Motorlu Kara Tasitlarinin ve Motosikletlerin Toptan ve Perakende Ticareti ile Onarimi",
            "Motorlu Kara Tasitlari ve Motosikletler Haric Toptan Ticaret",
            "Motorlu Kara Tasitlari ve Motosikletler Haric Perakende Ticaret",
            
            # H - ULASTIRMA VE DEPOLAMA
            "Kara Tasimaciligi ve Boru Hatti Tasimaciligi",
            "Su Yolu Tasimaciligi",
            "Hava Yolu Tasimaciligi",
            "Depolama ve Tasimaciligi Destekleyici Faaliyetler",
            "Posta ve Kurye Faaliyetleri",
            
            # I - KONAKLAMA VE YIYECEK HIZMETI FAALIYETLERI
            "Konaklama",
            "Yiyecek ve Icecek Hizmeti Faaliyetleri",
            
            # J - BILGI VE ILETISIM
            "Yayincilik Faaliyetleri",
            "Sinema Filmi, Video ve Televizyon Programi Yapımciligi, Ses Kaydi ve Muzik Yayimlama Faaliyetleri",
            "Programcilik ve Yayincilik Faaliyetleri",
            "Telekomünikasyon",
            "Bilgisayar Programlama, Danismanlık ve Ilgili Faaliyetler",
            "Bilgi Hizmeti Faaliyetleri",
            
            # K - FINANS VE SIGORTA FAALIYETLERI
            "Finansal Hizmet Faaliyetleri (Sigorta ve Emeklilik Fonlari Haric)",
            "Sigorta, Reassurans ve Emeklilik Fonlari (Zorunlu Sosyal Guvenlik Haric)",
            "Finansal Hizmetlere Yardimci Faaliyetler",
            
            # L - GAYRIMENKUL FAALIYETLERI
            "Gayrimenkul Faaliyetleri",
            
            # M - MESLEKI, BILIMSEL VE TEKNIK FAALIYETLER
            "Hukuk ve Muhasebe Faaliyetleri",
            "Is Yonetimi ve Yonetim Danismanligi Faaliyetleri",
            "Mimarlik ve Muhendislik Faaliyetleri; Teknik Test ve Analiz",
            "Bilimsel Arastirma ve Gelistirme",
            "Reklamcilik ve Pazar Arastirmasi",
            "Diger Mesleki, Bilimsel ve Teknik Faaliyetler",
            "Veterinerlik Hizmetleri",
            
            # N - IDARI VE DESTEK HIZMETI FAALIYETLERI
            "Kiralama ve Leasing Faaliyetleri",
            "Istihdam Faaliyetleri",
            "Seyahat Acentesi, Tur Operatoru ve Diger Rezervasyon Hizmetleri ve Ilgili Faaliyetler",
            "Guvenlik ve Sorusturma Faaliyetleri",
            "Bina ve Cevre Duzenleme Faaliyetleri",
            "Buro Yonetimi ve Buyou Destekleyici Faaliyetler",
            
            # O - KAMU YONETIMI VE SAVUNMA; ZORUNLU SOSYAL GUVENLIK
            "Kamu Yonetimi ve Savunma; Zorunlu Sosyal Guvenlik",
            
            # P - EGITIM
            "Egitim",
            
            # Q - INSAN SAGLIGI VE SOSYAL HIZMET FAALIYETLERI
            "Insan Sagligi Hizmetleri",
            "Yatili Bakim Faaliyetleri",
            "Barinacak Yer Saglayamayan Sosyal Hizmetler",
            
            # R - KULTUR, SANAT, EGLENCE, DINLENCE VE SPOR
            "Yaratici, Sanat ve Eglence Faaliyetleri",
            "Kutuphane, Arsiv, Muze ve Diger Kulturel Faaliyetler",
            "Kumar ve Musterek Bahis Faaliyetleri",
            "Spor Faaliyetleri ile Eglence ve Dinlence Faaliyetleri",
            
            # S - DIGER HIZMET FAALIYETLERI
            "Uye Olunan Kuruluslarin Faaliyetleri",
            "Bilgisayar, Kisisel Esya ve Ev Esyalarinin Onarimi",
            "Diger Kisisel Hizmet Faaliyetleri",
            
            # T - HANE HALKLARININ ISVEREN OLARAK FAALIYETLERI
            "Ev Ici Personel Calistiran Hanehalkları Faaliyetleri",
            "Hanehalkları Tarafindan Kendi Kullanimlarına Yonelik Mal ve Hizmet Uretim Faaliyetleri",
            
            # OZEL SEKTORLER - TURKIYE'YE OZGU
            "Kompresor ve Hava Sistemleri",
            "Endustriyel Makine Servisi",
            "Teknik Danismanlık",
            "Ithalat ve Ihracat",
            "E-Ticaret",
            "Dijital Pazarlama",
            "Lojistik ve Kargo",
            "Turizm ve Rehberlik",
            "Cevre ve Temizlik Hizmetleri",
            "Guvenlik Sistemleri",
            "Enerji ve Yenilenebilir Enerji",
            "Bioteknoloji",
            "Yazilim Gelistirme",
            "Oyun Gelistirme",
            "Fintech",
            "Insurtech",
            "Startup ve Girisimcilik",
            "Danismanlık Hizmetleri",
            "Insan Kaynaklari",
            "Proje Yonetimi"
        ]

        try:
            # Set encoding to UTF-8 for Turkish characters
            if sys.stdout.encoding != 'utf-8':
                sys.stdout.reconfigure(encoding='utf-8')
                
            if options['clear']:
                deleted_count = CoreBusiness.objects.count()
                CoreBusiness.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(f"Deleted {deleted_count} existing CoreBusiness records.")
                )

            with transaction.atomic():
                created_count = 0
                updated_count = 0
                
                for business_name in CORE_BUSINESS_DATA:
                    business, created = CoreBusiness.objects.get_or_create(name=business_name)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                total_count = CoreBusiness.objects.count()
                
                # Use simple ASCII messages to avoid encoding issues
                success_message = (
                    f"Successfully processed CoreBusiness data:\n"
                    f"  - Created: {created_count} new entries\n"
                    f"  - Already existed: {updated_count} entries\n"
                    f"  - Total CoreBusiness records: {total_count}\n"
                    f"  - Based on ITO meslek gruplari and comprehensive business categories"
                )
                
                self.stdout.write(self.style.SUCCESS(success_message))

        except Exception as e:
            error_message = f"Error populating CoreBusiness data: {str(e)}"
            self.stdout.write(self.style.ERROR(error_message))