# python version of wiringpi-php-bme280

This is a transpiled version of <a href="https://github.com/itc-lab/wiringpi-php-bme280" target="_blank">wiringpi-php-bme280</a> from php to python.  
The temperature, humidity, barometric pressure, and heat index obtained from the BME280 sensor are displayed on the Web screen.  
It also has a function to display temperature, humidity and barometric pressure on the LCD 1602A.
![bme280](https://user-images.githubusercontent.com/76575923/120967884-0efd2580-c7a3-11eb-9433-9c1f2168d01a.jpg)

## Requirements

- Python 3 - The script interpreter
- WiringPi-Python - Control Hardware features of Rasbberry Pi
- Apache 2 - The Apache HTTP Server
- mod_wsgi - Apache module which can host any Python web application
- Flask - A lightweight web application framework
- pycurl - A Python interface to libcurl

## Getting Started

日本語が読める方は、　リンク：[BME280で取得した温湿度気圧をWeb画面に表示する(python,wiringpi,apache) - ITC Engineering Blog](https://itc-engineering-blog.netlify.app/blogs/wiringpi-python-bme280)　を参考にインストールしてください。(Japanese text only)

### Install apache2 & mod_wsgi

```
apt install apache2
apt install -y libapache2-mod-wsgi-py3
```

### Install pip

```
pip3 install wiringpi
pip3 install Flask
apt install libcurl4-openssl-dev libssl-dev
pip3 install pycurl
```

### Data Logging

```
cd opt
cp -p bme280.py bme280_inc.py lcd1602_inc.py /opt/
cd /opt
chmod 755 bme280.py
./bme280.py
```

To stop

```
./bme280.py stop
```

To run automatically at startup

```
vi /etc/rc.local
```

Add `/opt/bme280.py` before `exit 0`.
```
/opt/bme280.py
exit 0
```

### Web - single node

```
cp html/bme280.html /var/www/html/
cp -r js /var/www/html/
mkdir /var/www/flask
cp py/app.wsgi /var/www/flask/
cp py/app.py /var/www/flask/
cp py/getlogdata.py /var/www/flask/
chown -R www-data:www-data /var/www/html /var/www/flask /var/log/bme280log
```

```
vi /etc/apache2/sites-available/flask_wsgi.conf
```

```
<VirtualHost *:80>
    ServerName xxx.example.com
    ServerAdmin xxx@example.com

    DocumentRoot /var/www/html

    WSGIDaemonProcess app user=www-data group=www-data threads=5
    WSGIScriptAlias /flask /var/www/flask/app.wsgi
    WSGIChunkedRequest On

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    <Directory /var/www/flask/>
        WSGIProcessGroup app
        WSGIScriptReloading On
        Require all granted
        Options FollowSymLinks
        AllowOverride All
    </Directory>
</VirtualHost>
```

```
a2ensite flask_wsgi
a2dissite 000-default
systemctl restart apache2
```

Access  
https://localhost/bme280.html

### Web - multi node

Install on a different server than the single node.

```
cp html_relay/bme280s.html html_relay/rooms.json /var/www/html/
cp -r js /var/www/html/
mkdir /var/www/flask
cp py_relay/app_relay.wsgi /var/www/flask/
cp py_relay/app_relay.py /var/www/flask/
cp py_relay/proxyproc.py /var/www/flask/
chown -R www-data:www-data /var/www/html /var/www/flask
```

Register the node(s)

```
vi /var/www/html/rooms.json
```

```
[
	{	"url": "http://192.168.2.38/", "name": "居間"		},
	{	"url": "http://192.168.2.32/", "name": "洋室１"	},
	{	"//url": "http://192.168.2.33/", "name": "洋室２"	},
	{	"//url": "http://192.168.2.34/", "name": "洋室３"	},
	{}
]
```

```
vi /etc/apache2/sites-available/flask_wsgi.conf
```

```
<VirtualHost *:80>
    ServerName xxx.example.com
    ServerAdmin xxx@example.com

    DocumentRoot /var/www/html

    WSGIDaemonProcess app_relay user=www-data group=www-data threads=5
    WSGIScriptAlias /flask /var/www/flask/app_relay.wsgi
    WSGIChunkedRequest On

    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined

    <Directory /var/www/flask/>
        WSGIProcessGroup app_relay
        WSGIApplicationGroup %{GLOBAL}
        WSGIScriptReloading On
        Require all granted
        Options FollowSymLinks
        AllowOverride All
    </Directory>
</VirtualHost>
```

```
a2ensite flask_wsgi
a2dissite 000-default
systemctl restart apache2
```

Access  
https://localhost/bme280s.html

## License

MIT
