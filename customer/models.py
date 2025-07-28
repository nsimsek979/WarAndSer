from django.db import models
from django.utils.translation import gettext_lazy as _

class Country(models.Model):
	name = models.CharField(max_length=100, default="Türkiye")
	code = models.CharField(max_length=2, blank=True, null=True)
	flag = models.ImageField(upload_to="country_flags/", null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name

	class Meta:
		ordering = ["name"]

class City(models.Model):
	name = models.CharField(max_length=100)
	country = models.ForeignKey("Country", on_delete=models.CASCADE, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name

	class Meta:
		ordering = ["name"]

class County(models.Model):
	name = models.CharField(max_length=100)
	city = models.ForeignKey(City, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name

	class Meta:
		ordering = ["name"]

class District(models.Model):
	name = models.CharField(max_length=100)
	county = models.ForeignKey(County, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name

	class Meta:
		ordering = ["name"]

class CoreBusiness(models.Model):
	name = models.CharField(max_length=100)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name

	class Meta:
		ordering = ["name"]

class Company(models.Model):
	COMPANY_TYPE_CHOICES = [
		("main", _( "Main")),
		("distributor", _( "Distributor")),
		("enduser", _( "End User")),
	]
	name = models.CharField(max_length=100, unique=True)
	related_company = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
	tax_number = models.CharField(max_length=20, null=True, blank=True)
	company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES, null=True, blank=True)
	core_business = models.ForeignKey(CoreBusiness, on_delete=models.SET_NULL, null=True, blank=True)
	related_manager = models.ForeignKey('custom_user.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role__in': ['manager_main', 'salesmanager_main']}, related_name='managed_companies')
	email = models.EmailField(blank=True, null=True)
	telephone = models.CharField(max_length=20, blank=True, null=True)
	active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name

	def save(self, *args, **kwargs):
		"""
		Auto-assign related_manager when company is end user and has related_company
		"""
		# If company is end user and has related_company, auto-assign related_manager
		if (self.company_type == 'enduser' and 
			self.related_company and 
			self.related_company.related_manager and 
			not self.related_manager):
			self.related_manager = self.related_company.related_manager
		
		super().save(*args, **kwargs)

	class Meta:
		ordering = ["name"]
		permissions = [
			("view_all_companies", "Can view all companies"),
			("view_assigned_companies", "Can view assigned companies"),
		]

class ContactPerson(models.Model):
	company = models.ForeignKey(Company, on_delete=models.CASCADE)
	full_name = models.CharField(max_length=100)
	title = models.CharField(max_length=100, blank=True, null=True)
	email = models.EmailField(blank=True, null=True)
	telephone = models.CharField(max_length=20, blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.company.name}-{self.full_name}"

	class Meta:
		ordering = ["full_name"]

class Address(models.Model):
	company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="address")
	name = models.CharField(max_length=100, default="Merkez")
	country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
	district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
	city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
	county = models.ForeignKey(County, on_delete=models.SET_NULL, null=True, blank=True)
	zipcode = models.CharField(max_length=10, blank=True, null=True)
	address = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.company.name} - {self.name}"

	class Meta:
		ordering = ["company__name"]


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
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def clean(self):
		from django.core.exceptions import ValidationError
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
