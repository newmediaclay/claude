# PythonAnywhere WSGI Configuration
# Copy this content to your WSGI configuration file on PythonAnywhere
# (Web tab -> WSGI configuration file)

import sys
import os

# Add your project directory to the path
project_home = '/home/YOUR_USERNAME/claude'  # Change YOUR_USERNAME
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables (or set these in PythonAnywhere's Web tab)
os.environ['SENDGRID_API_KEY'] = 'your-sendgrid-api-key'
os.environ['NOTIFICATION_EMAIL'] = 'clay@clayschossow.com'
os.environ['FROM_EMAIL'] = 'noreply@clayschossow.com'
os.environ['APP_URL'] = 'https://sales.clayschossow.com'
os.environ['DIGEST_SECRET'] = 'your-secret-key-here'  # Generate a random string

from web import app as application
