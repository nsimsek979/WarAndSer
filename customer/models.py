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
