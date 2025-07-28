from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class Country(models.Model):
	name = models.CharField(max_length=100, default="Türkiye", verbose_name=_("Country Name"))
	code = models.CharField(max_length=2, blank=True, null=True, verbose_name=_("Country Code"))
	flag = models.ImageField(upload_to="country_flags/", null=True, blank=True, verbose_name=_("Flag"))
	created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
	updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

	def __str__(self):
		return self.name

	class Meta:
		ordering = ["name"]
		verbose_name = _("Country")
		verbose_name_plural = _("Countries")

class City(models.Model):
	name = models.CharField(max_length=100, verbose_name=_("City Name"))
	country = models.ForeignKey("Country", on_delete=models.CASCADE, null=True, verbose_name=_("Country"))
	created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
	updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

	def __str__(self):
		return self.name

	class Meta:
		ordering = ["name"]
		verbose_name = _("City")
		verbose_name_plural = _("Cities")

class County(models.Model):
	name = models.CharField(max_length=100, verbose_name=_("County Name"))
	city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name=_("City"))
	created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
	updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

	def __str__(self):
		return self.name

	class Meta:
		ordering = ["name"]
		verbose_name = _("County")
		verbose_name_plural = _("Counties")

class District(models.Model):
	name = models.CharField(max_length=100, verbose_name=_("District Name"))
	county = models.ForeignKey(County, on_delete=models.CASCADE, verbose_name=_("County"))
	created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
	updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

	def __str__(self):
		return self.name

	class Meta:
		ordering = ["name"]
		verbose_name = _("District")
		verbose_name_plural = _("Districts")

class CoreBusiness(models.Model):
	name = models.CharField(max_length=100, verbose_name=_("Business Name"))
	created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
	updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

	def __str__(self):
		return self.name

	class Meta:
		ordering = ["name"]
		verbose_name = _("Core Business")
		verbose_name_plural = _("Core Businesses")

class Company(models.Model):
	COMPANY_TYPE_CHOICES = [
		("main", _( "Main")),
		("distributor", _( "Distributor")),
		("enduser", _( "End User")),
	]
	name = models.CharField(max_length=100, unique=True, verbose_name=_("Company Name"))
	related_company = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Related Company"))
	tax_number = models.CharField(max_length=20, null=True, blank=True, verbose_name=_("Tax Number"))
	company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES, null=True, blank=True, verbose_name=_("Company Type"))
	core_business = models.ForeignKey(CoreBusiness, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Core Business"))
	related_manager = models.ForeignKey('custom_user.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role__in': ['manager_main', 'salesmanager_main']}, related_name='managed_companies', verbose_name=_("Related Manager"))
	email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))
	telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Telephone"))
	active = models.BooleanField(default=True, verbose_name=_("Active"))
	created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
	updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

	def __str__(self):
		return self.name

	class Meta:
		ordering = ["name"]
		verbose_name = _("Company")
		verbose_name_plural = _("Companies")
		permissions = [
			("view_all_companies", "Can view all companies"),
			("view_assigned_companies", "Can view assigned companies"),
		]

class ContactPerson(models.Model):
	company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name=_("Company"))
	full_name = models.CharField(max_length=100, verbose_name=_("Full Name"))
	title = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Title"))
	email = models.EmailField(blank=True, null=True, verbose_name=_("Email"))
	telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Telephone"))
	created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
	updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

	def __str__(self):
		return f"{self.company.name}-{self.full_name}"

	class Meta:
		ordering = ["full_name"]
		verbose_name = _("Contact Person")
		verbose_name_plural = _("Contact Persons")

class Address(models.Model):
	company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="address", verbose_name=_("Company"))
	name = models.CharField(max_length=100, default="Merkez", verbose_name=_("Name"))
	country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Country"))
	district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("District"))
	city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("City"))
	county = models.ForeignKey(County, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("County"))
	zipcode = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Zip Code"))
	address = models.TextField(verbose_name=_("Address"))
	created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
	updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

	def __str__(self):
		return f"{self.company.name} - {self.name}"

	class Meta:
		ordering = ["company__name"]
		verbose_name = _("Address")
		verbose_name_plural = _("Addresses")


class WorkingHours(models.Model):
	"""
	Model to store customer working hours for calculating service and warranty periods.
	Calculates weekly working hours based on daily hours and weekend work status.
	"""
	customer = models.OneToOneField(
		Company, 
		on_delete=models.CASCADE, 
		related_name='working_hours',
		verbose_name=_("Customer")
	)
	daily_working_hours = models.PositiveSmallIntegerField(
		default=8,
		verbose_name=_("Daily Working Hours"),
		help_text=_("Maximum 24 hours per day")
	)
	working_on_saturday = models.BooleanField(
		default=False,
		verbose_name=_("Working on Saturday")
	)
	working_on_sunday = models.BooleanField(
		default=False,
		verbose_name=_("Working on Sunday")
	)
	created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
	updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

	def clean(self):
		if self.daily_working_hours > 24:
			raise ValidationError({
				'daily_working_hours': _('Daily working hours cannot exceed 24 hours.')
			})
		if self.daily_working_hours < 1:
			raise ValidationError({
				'daily_working_hours': _('Daily working hours must be at least 1 hour.')
			})

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)

	@property
	def weekly_working_hours(self):
		"""
		Calculate total weekly working hours.
		Formula: (daily_hours * 5 weekdays) + (saturday_hours) + (sunday_hours)
		"""
		weekdays_hours = self.daily_working_hours * 5  # Monday to Friday
		saturday_hours = self.daily_working_hours if self.working_on_saturday else 0
		sunday_hours = self.daily_working_hours if self.working_on_sunday else 0
		
		return weekdays_hours + saturday_hours + sunday_hours

	def get_working_days_per_week(self):
		"""
		Get number of working days per week.
		"""
		days = 5  # Monday to Friday
		if self.working_on_saturday:
			days += 1
		if self.working_on_sunday:
			days += 1
		return days

	def __str__(self):
		return f"{self.customer.name} - {self.daily_working_hours}h/day ({self.weekly_working_hours}h/week)"

	class Meta:
		verbose_name = _("Working Hours")
		verbose_name_plural = _("Working Hours")
		ordering = ["customer__name"]
