#!/bin/bash

# === USER CONFIGURATION ===
PROJECT_NAME=$1                         # e.g., summarizer
GITHUB_USER="famosky"
GITHUB_EMAIL="oluwafemiaderogba@gmail.com"
DOMAIN="odvas.com"                # your main domain
REMOTE_USER="root"
REMOTE_HOST="209.74.87.11"
REMOTE_PATH="/var/www/${PROJECT_NAME}"
SUBDOMAIN="${PROJECT_NAME}.${DOMAIN}"

# === CHECK ARGS ===
if [ -z "$PROJECT_NAME" ]; then
  echo "❌ Usage: ./deploy_full.sh <project_name>"
  exit 1
fi

# === 1. GitHub Setup ===
echo "📁 Initializing local Git repo..."
git init
git config user.name "$GITHUB_USER"
git config user.email "$GITHUB_EMAIL"
git add .
git commit -m "🚀 Initial commit"

echo "🌐 Creating and pushing to GitHub repo..."
gh repo create "$PROJECT_NAME" --public --source=. --remote=origin --push

# === 2. Upload Project to VPS ===
echo "📤 Uploading project to VPS..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p $REMOTE_PATH"
scp -r . ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}

# === 3. VPS Setup (via SSH) ===
echo "⚙️ Setting up project on VPS..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << EOF
cd ${REMOTE_PATH}
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# WSGI file
cat > wsgi.py <<END
from app import app
if __name__ == "__main__":
    app.run()
END

# Apache config
cat > /etc/apache2/sites-available/${PROJECT_NAME}.conf <<END
<VirtualHost *:80>
    ServerName ${SUBDOMAIN}
    DocumentRoot ${REMOTE_PATH}

    WSGIDaemonProcess ${PROJECT_NAME} python-home=${REMOTE_PATH}/venv python-path=${REMOTE_PATH}
    WSGIScriptAlias / ${REMOTE_PATH}/wsgi.py

    <Directory ${REMOTE_PATH}>
        Require all granted
    </Directory>

    ErrorLog \${APACHE_LOG_DIR}/${PROJECT_NAME}_error.log
    CustomLog \${APACHE_LOG_DIR}/${PROJECT_NAME}_access.log combined
</VirtualHost>
END

a2ensite ${PROJECT_NAME}.conf
systemctl reload apache2
EOF

echo "✅ Deployed at http://${SUBDOMAIN}"
