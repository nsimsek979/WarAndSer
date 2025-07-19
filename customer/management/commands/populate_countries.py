import requests
from django.core.management.base import BaseCommand
from django.core.files import File
from io import BytesIO
from customer.models import Country
import time

class Command(BaseCommand):
    help = "Populates countries with their flags"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--retry',
            type=int,
            default=3,
            help='Number of retry attempts for failed requests'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Delay between retry attempts in seconds'
        )

    def handle(self, *args, **options):
        retry_count = options['retry']
        retry_delay = options['delay']
        
        self.stdout.write(self.style.SUCCESS("Starting country population..."))
        
        # Try with a more reliable endpoint
        api_url = "https://restcountries.com/v3.1/all?fields=name,cca2"
        
        for attempt in range(1, retry_count + 1):
            try:
                response = requests.get(
                    api_url,
                    headers={'User-Agent': 'Django Country Population/1.0'},
                    timeout=10
                )
                response.raise_for_status()
                countries_data = response.json()
                
                if not isinstance(countries_data, list):
                    raise ValueError("Unexpected API response format")
                
                self.process_countries(countries_data)
                break  # Success - exit retry loop
                
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.WARNING(
                    f"Attempt {attempt}/{retry_count} failed: {str(e)}"
                ))
                if attempt < retry_count:
                    time.sleep(retry_delay)
                else:
                    self.stdout.write(self.style.ERROR(
                        f"Failed after {retry_count} attempts. Last error: {str(e)}"
                    ))
                    # Try fallback to local data if available
                    self.try_local_fallback()
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
                break

    def process_countries(self, countries_data):
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for country_data in countries_data:
            try:
                country_name = country_data.get("name", {}).get("common", "").strip()
                country_code = country_data.get("cca2", "").lower().strip()

                if not country_name or not country_code:
                    self.stdout.write(self.style.WARNING(f"Skipping entry with missing name/code: {country_data}"))
                    fail_count += 1
                    continue

                country, created = Country.objects.get_or_create(
                    name=country_name,
                    defaults={"code": country_code}
                )

                if not created and country.flag:
                    skip_count += 1
                    continue

                flag_url = f"https://flagcdn.com/w640/{country_code}.png"
                flag_response = requests.get(flag_url, timeout=5)
                flag_response.raise_for_status()

                img_name = f"{country_code}_flag.png"
                img_content = BytesIO(flag_response.content)
                
                if country.flag:
                    country.flag.delete()
                    
                country.flag.save(img_name, File(img_content), save=True)
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"Processed {country_name}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {country_name}: {str(e)}"))
                fail_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Completed! Success: {success_count}, Skipped: {skip_count}, Failed: {fail_count}"
        ))

    def try_local_fallback(self):
        """Fallback to local country data if API fails"""
        try:
            local_countries = [
                {"name": {"common": "Turkey"}, "cca2": "tr"},
                {"name": {"common": "United States"}, "cca2": "us"},
                # Add more common countries as needed
            ]
            self.stdout.write(self.style.NOTICE("Using local fallback data"))
            self.process_countries(local_countries)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Fallback failed: {str(e)}"))