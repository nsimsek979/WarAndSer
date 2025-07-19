from django.core.management.base import BaseCommand
from customer.models import CoreBusiness
from django.db import transaction

class Command(BaseCommand):
    help = "Populates CoreBusiness with İTO faaliyet alanları data"

    def handle(self, *args, **options):
        # Faaliyet alanları extracted from İTO PDF first page
        FAALIYET_ALANLARI = [
            "Toptan Ticaret",
            "Perakende Ticaret",
            "Gıda Ürünleri ve İçecek İmalatı",
            "Tekstil Ürünleri İmalatı",
            "Giyim Eşyası İmalatı",
            "Deri ve Deri Ürünleri İmalatı",
            "Ağaç ve Mantar Ürünleri İmalatı",
            "Kağıt ve Kağıt Ürünleri İmalatı",
            "Kok Kömürü ve Rafine Edilmiş Petrol Ürünleri İmalatı",
            "Kimyasal Madde ve Ürünler İmalatı",
            "Eczacılık Ürünleri İmalatı",
            "Plastik ve Kauçuk Ürünleri İmalatı",
            "Metalik Olmayan Diğer Mineral Ürünler İmalatı",
            "Ana Metal Sanayi",
            "Fabricated Metal Products Manufacturing",
            "Bilgisayar, Elektronik ve Optik Ürünler İmalatı",
            "Elektrikli Teçhizat İmalatı",
            "Makine ve Teçhizat İmalatı",
            "Motorlu Kara Taşıtı İmalatı",
            "Diğer Ulaşım Araçları İmalatı",
            "Mobilya İmalatı",
            "Diğer İmalat",
            "Elektrik, Gaz, Buhar ve İklimlendirme Üretimi ve Dağıtımı",
            "Su Temini; Kanalizasyon, Atık Yönetimi ve İyileştirme Faaliyetleri",
            "İnşaat",
            "Motorlu Taşıtların ve Motosikletlerin Onarımı",
            "Ulaştırma ve Depolama",
            "Konaklama",
            "Yiyecek ve İçecek Hizmeti Faaliyetleri",
            "Bilgi ve İletişim",
            "Finans ve Sigorta Faaliyetleri",
            "Gayrimenkul Faaliyetleri",
            "Mesleki, Bilimsel ve Teknik Faaliyetler",
            "İdari ve Destek Hizmeti Faaliyetleri",
            "Kamu Yönetimi ve Savunma; Zorunlu Sosyal Güvenlik",
            "Eğitim",
            "İnsan Sağlığı ve Sosyal Hizmet Faaliyetleri",
            "Kültür, Sanat, Eğlence, Dinlence ve Spor",
            "Diğer Hizmet Faaliyetleri"
        ]

        try:
            with transaction.atomic():
                created_count = 0
                for faaliyet in FAALIYET_ALANLARI:
                    _, created = CoreBusiness.objects.get_or_create(name=faaliyet)
                    if created:
                        created_count += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully populated CoreBusiness model with {created_count} new faaliyet alanları. "
                        f"Total now: {CoreBusiness.objects.count()}"
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))