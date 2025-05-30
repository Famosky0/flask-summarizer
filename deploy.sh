#!/bin/bash

# === This is meant to recommit existing project in vps while deploy_full is new project ===

# === USER CONFIGURATION ===
PROJECT_NAME=$1                         # e.g., summarizer
GITHUB_USER="famosky"
GITHUB_EMAIL="oluwafemiaderogba@gmail.com"
DOMAIN="odvas.com"
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
echo "📁 Checking Git repo status..."

# Initialize Git if not already
if [ ! -d ".git" ]; then
  git init
  git config user.name "$GITHUB_USER"
  git config user.email "$GITHUB_EMAIL"
fi

# Add and commit changes
git add .
git commit -m "🔄 Update deployment - $(date +'%Y-%m-%d %H:%M:%S')" || echo "✅ No changes to commit."

# Check if remote exists
if git remote get-url origin &>/dev/null; then
  echo "🌐 Remote 'origin' already set. Pushing updates..."
else
  echo "🌐 Remote not set. Creating and pushing new repo..."
  gh repo create "$PROJECT_NAME" --public --source=. --remote=origin --push
fi

# Automatically detect current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
git push origin "$CURRENT_BRANCH"

# === 2. Upload Project to VPS ===
echo "📤 Uploading project to VPS..."
sshpass -p "jHhX3n0N5Q8a7Shg4R" ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p $REMOTE_PATH"
sshpass -p "jHhX3n0N5Q8a7Shg4R" scp -o StrictHostKeyChecking=no -r . ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}

# === 3. VPS Setup (via SSH) ===
echo "⚙️ Setting up project on VPS..."
sshpass -p "jHhX3n0N5Q8a7Shg4R" ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} << EOF
cd ${REMOTE_PATH}

# === Check and Install Python 3.8 ===
if ! /usr/local/bin/python3.8 --version &> /dev/null; then
  echo "🐍 Installing Python 3.8..."
  yum install -y gcc gcc-c++ make zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel xz xz-devel libffi-devel wget
  cd /usr/src
  wget https://www.python.org/ftp/python/3.8.18/Python-3.8.18.tgz
  tar xzf Python-3.8.18.tgz
  cd Python-3.8.18
  ./configure --enable-optimizations
  make altinstall
else
  echo "✅ Python 3.8 already installed."
fi

# === Set up virtual environment ===
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  /usr/local/bin/python3.8 -m venv venv
else
  echo "✅ Virtual environment already exists."
fi

source venv/bin/activate
pip install --upgrade pip

# === Install pipreqs if missing ===
if ! pip show pipreqs &>/dev/null; then
  echo "📦 Installing pipreqs..."
  pip install pipreqs
else
  echo "✅ pipreqs already installed."
fi

# === Install gunicorn if missing ===
if ! pip show gunicorn &>/dev/null; then
  echo "📦 Installing gunicorn..."
  pip install gunicorn
else
  echo "✅ gunicorn already installed."
fi

# === Generate requirements file ===
pipreqs . --force

# === Restart Gunicorn ===
echo "🚀 Restarting Gunicorn..."
pkill gunicorn || echo "🔄 No existing Gunicorn process found."
nohup gunicorn -w 4 -b 127.0.0.1:8000 app:app &

# === Nginx Config ===
cat > /etc/nginx/conf.d/${PROJECT_NAME}.conf <<END
server {
    listen 80;
    server_name ${SUBDOMAIN};

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;
    }
}
END

# Reload Nginx
nginx -t && systemctl reload nginx
EOF

echo "✅ Deployed at: http://${SUBDOMAIN}"
