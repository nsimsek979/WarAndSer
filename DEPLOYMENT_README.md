# WarAndSer - Warranty and Services Management System

## Environment Setup

This project uses environment-specific settings to handle different configurations for Windows development and Ubuntu production.

### Development (Windows)
The system automatically detects Windows and uses development settings:
- SQLite database
- DEBUG = True  
- Email backend = console
- No SSL requirements

### Production (Ubuntu Server)
The system automatically detects Linux/Ubuntu and uses production settings:
- PostgreSQL database
- DEBUG = False
- SMTP email backend
- SSL security enabled

## Setup Instructions

### Windows Development
1. Clone the repository
2. Install requirements: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Create superuser: `python manage.py createsuperuser`
5. Run server: `python manage.py runserver`

### Ubuntu Production Setup
1. Clone the repository
2. Copy environment file: `cp .env.example .env`
3. Edit `.env` file with your production values:
   ```bash
   DB_NAME=warandser_db
   DB_USER=warandser_user
   DB_PASSWORD=your-secure-password
   SECRET_KEY=your-50-char-secret-key
   ALLOWED_HOSTS=your-domain.com,your-server-ip
   ```
4. Install requirements: `pip install -r requirements.txt`
5. Install PostgreSQL and create database
6. Run migrations: `python manage.py migrate`
7. Collect static files: `python manage.py collectstatic`
8. Setup web server (Nginx + Gunicorn)

## Settings Files Structure
- `settings.py` - Main settings file (auto-detects environment)
- `settings_base.py` - Shared settings for all environments
- `settings_dev.py` - Windows development settings
- `settings_prod.py` - Ubuntu production settings
- `.env.example` - Template for production environment variables

## Git Workflow
The settings system ensures that:
- Development settings stay on Windows
- Production settings stay on Ubuntu
- Only shared base settings are committed to git
- Environment-specific secrets are not committed (.env files ignored)

## Mobile Scanner Fix
Fixed mobile installation scanner camera issues:
- Removed conflicting video elements
- Html5Qrcode now creates its own video element
- Added proper CSS styling for camera preview
