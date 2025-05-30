sudo yum install -y gcc gcc-c++ make zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel xz xz-devel libffi-devel wget

cd /usr/src
sudo wget https://www.python.org/ftp/python/3.8.18/Python-3.8.18.tgz
sudo tar xzf Python-3.8.18.tgz
cd Python-3.8.18
sudo ./configure --enable-optimizations
sudo make altinstall

cd /var/www/summarizer
/usr/local/bin/python3.8 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cd /var/www/summarizer
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:8000 app:app

