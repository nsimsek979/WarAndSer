"""
Django settings for gvs project.

This file automatically imports the correct settings based on environment.
"""

import os
import platform

# Detect environment
if platform.system() == 'Windows':
    # Windows development environment
    from .settings_dev import *
elif os.environ.get('DJANGO_SETTINGS_MODULE') == 'gvs.settings_prod':
    # Production environment (set by deployment script)
    from .settings_prod import *
elif os.path.exists('/etc/os-release'):
    # Linux/Ubuntu server (assume production)
    from .settings_prod import *
else:
    # Default to development
    from .settings_dev import *

