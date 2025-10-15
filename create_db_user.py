#!/usr/bin/env python
import os
import django
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gvs.settings_iis_prod')
django.setup()

# Database bilgileri
DB_HOST = '10.114.16.4'
DB_PORT = '5432'
DB_NAME = 'warandser_db'
DB_USER = 'postgres'  # Admin user
DB_PASSWORD = 'Konnektom123*'  # Admin password

NEW_USER = 'warandser_user'
NEW_PASSWORD = 'Konnektom123*'

try:
    # PostgreSQL'e admin olarak bağlan
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database='postgres'  # Default database
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    print("✅ PostgreSQL admin bağlantısı başarılı!")

    # User oluştur
    cursor.execute(f"CREATE USER {NEW_USER} WITH PASSWORD '{NEW_PASSWORD}';")
    print(f"✅ User '{NEW_USER}' oluşturuldu!")

    # Database oluştur
    cursor.execute(f"CREATE DATABASE {DB_NAME} OWNER {NEW_USER};")
    print(f"✅ Database '{DB_NAME}' oluşturuldu!")

    # İzinleri ver
    cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {NEW_USER};")
    print(f"✅ İzinler verildi!")

    # Test bağlantısı
    test_conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=NEW_USER,
        password=NEW_PASSWORD,
        database=DB_NAME
    )
    print(f"✅ Yeni user ile bağlantı testi başarılı!")

    cursor.close()
    conn.close()
    test_conn.close()

except psycopg2.Error as e:
    print(f"❌ PostgreSQL hatası: {e}")
except Exception as e:
    print(f"❌ Genel hata: {e}")
