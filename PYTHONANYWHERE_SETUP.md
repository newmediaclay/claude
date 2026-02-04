# PythonAnywhere Setup Guide

## 1. Create PythonAnywhere Account
- Go to https://www.pythonanywhere.com
- Sign up for a free "Beginner" account (or paid for custom domain)

## 2. Upload Your Code
Option A - Git (recommended):
```bash
# In PythonAnywhere Bash console:
git clone https://github.com/newmediaclay/claude.git
cd claude
pip install --user -r requirements.txt
```

Option B - Manual upload:
- Go to Files tab
- Upload web.py, requirements.txt, and data/deals.json

## 3. Set Up Web App
1. Go to **Web** tab
2. Click **Add a new web app**
3. Choose **Manual configuration** (not Flask)
4. Select **Python 3.10** (or latest)

## 4. Configure WSGI
1. Click on the **WSGI configuration file** link
2. Delete all contents and paste:

```python
import sys
import os

project_home = '/home/YOUR_USERNAME/claude'  # Change this!
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Environment variables
os.environ['SENDGRID_API_KEY'] = 'SG.your-api-key-here'
os.environ['NOTIFICATION_EMAIL'] = 'your-email@example.com'
os.environ['FROM_EMAIL'] = 'noreply@yourdomain.com'
os.environ['APP_URL'] = 'https://YOUR_USERNAME.pythonanywhere.com'
os.environ['DIGEST_SECRET'] = 'generate-a-random-string-here'

from web import app as application
```

3. Save the file

## 5. Set Up SendGrid
1. Go to https://sendgrid.com and create free account
2. Go to Settings → API Keys → Create API Key
3. Choose "Restricted Access" with only "Mail Send" permission
4. Copy the key (starts with `SG.`) and add to WSGI file

## 6. Custom Domain (Optional)
If you have a paid account:
1. Go to **Web** tab → **Add a new domain**
2. Enter: `sales.clayschossow.com`
3. Add CNAME record in your DNS:
   - Name: `sales`
   - Value: `YOUR_USERNAME.pythonanywhere.com`

## 7. Set Up Daily Email Digest
1. Go to **Tasks** tab
2. Create a new **Scheduled task**
3. Set time (e.g., 8:00 AM UTC = 3:00 AM EST)
4. Command:
```bash
curl "https://YOUR_USERNAME.pythonanywhere.com/send-digest?key=YOUR_DIGEST_SECRET"
```

## 8. Test Everything
1. Reload your web app (Web tab → Reload button)
2. Visit your URL
3. Test the digest endpoint manually:
   ```
   https://YOUR_USERNAME.pythonanywhere.com/send-digest?key=YOUR_DIGEST_SECRET
   ```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| SENDGRID_API_KEY | Your SendGrid API key | SG.xxxxx |
| NOTIFICATION_EMAIL | Where to send digest emails | clay@example.com |
| FROM_EMAIL | Sender email address | noreply@yourdomain.com |
| APP_URL | Your app's public URL | https://sales.clayschossow.com |
| DIGEST_SECRET | Secret key for digest endpoint | random-string-123 |

## Troubleshooting

**App not loading?**
- Check the error log in Web tab
- Make sure paths in WSGI file are correct

**Emails not sending?**
- Verify SendGrid API key is correct
- Check that FROM_EMAIL domain is verified in SendGrid
- Test the /send-digest endpoint manually

**Data not persisting?**
- Make sure data/deals.json exists and is writable
- Check file permissions in Files tab
