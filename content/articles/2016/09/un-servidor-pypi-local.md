---
title: "Un servidor pypi local"
slug: "un-servidor-pypi-local"
date: 2016-09-05
categories: ['Sistemas']
tags: ['python', 'PyPI', 'wheel', 'virtualenv', 'uWSGI']
---

Cuando trabajamos con **python**, muchas veces necesitamos instalar librerías con *pip* o *easy_install*. Dependiendo de la naturaleza de nuestros proyectos, las librerías suelen variar, pero siempre solemos utilizar los mismos. En estos casos puede ser útil tenerlos cerca, cacheados en un servidor en nuestra red local, para su rápido acceso.<!--more-->

Para estos casos podemos montar un servidor exactamente igual que el de [PyPI](https://pypi.python.org/pypi), que se distribuye como una librería **python** adicional, que nos ofrece una aplicación **WSGI**.

Nuestro despliegue es bastante básico; con un solo servidor nos basta, y puede estar compartido con otros usos. El único servicio que vamos a poner es un servidor **WSGI** capaz de servir la aplicación. En nuestro caso vamos a usar **uwsgi**.

Así pues, creamos dos máquinas, una va a ser el servidor y la otra, un cliente de ejemplo que necesite los paquetes locales.

```bash
root@lxc:~# lxc-ls -f
NAME        STATE    IPV4      IPV6  AUTOSTART
----------------------------------------------
pyclient    RUNNING  10.0.0.3  -     NO
pypiserver  RUNNING  10.0.0.2  -     NO
root@lxc:~#
```

## Montando el servidor

Como decisión de diseño, he optado por instalar el paquete *pypiserver* en un *virtualenv*, para no interferir con otros paquetes que pudiera haber en el servidor.

Empezaremos creando una carpeta contenedora, en donde va a ir el *virtualenv*, la aplicación y el índice de paquetes disponibles en el servidor.

```bash
root@pypiserver:~# mkdir /opt/pypi && cd /opt/pypi
root@pypiserver:/opt/pypi#
```

Vamos a descargar *virtualenv*, sin instalarlo, para "usar y tirar". Para ello vamos a necesitar alguna herramienta para descargarlo de la red, por ejemplo, **wget**.

```bash
root@pypiserver:/opt/pypi# apt-get install -y wget
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
...
0 actualizados, 13 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 9.875 kB de archivos.
Se utilizarán 35,7 MB de espacio de disco adicional después de esta operación.
...
root@pypiserver:/opt/pypi#
```

Tanto la herramienta *virtualenv* como la herramienta *pip* que vamos a necesitar mas adelante, usan **python**. Es un buen momento para asegurar que esté instalado, y si no lo está, lo instalamos.

```bash
root@pypiserver:/opt/pypi# apt-get install -y python
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
...
0 actualizados, 12 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 4.991 kB de archivos.
Se utilizarán 21,2 MB de espacio de disco adicional después de esta operación.
...
root@pypiserver:/opt/pypi#
```
Descargamos el paquete *virtualenv* y lo descomprimimos.

```bash
root@pypiserver:/opt/pypi# wget -q https://pypi.python.org/packages/5c/79/5dae7494b9f5ed061cff9a8ab8d6e1f02db352f3facf907d9eb614fb80e9/virtualenv-15.0.2.tar.gz
root@pypiserver:/opt/pypi# tar xzf virtualenv-15.0.2.tar.gz
root@pypiserver:/opt/pypi#
```

Vamos a crear el *virtualenv* dentro de nuestra carpeta contenedora. Luego instalamos el paquete *pypiserver*, previo activado del *virtualenv*.

```bash
root@pypiserver:/opt/pypi# ./virtualenv-15.0.2/virtualenv.py env
New python executable in /opt/pypi/env/bin/python
Installing setuptools, pip, wheel...done.
root@pypiserver:/opt/pypi# . env/bin/activate
(env) root@pypiserver:/opt/pypi# pip install pypiserver
Collecting pypiserver
  Downloading pypiserver-1.1.10-py2.py3-none-any.whl (75kB)
    100% |████████████████████████████████| 81kB 632kB/s
Installing collected packages: pypiserver
Successfully installed pypiserver-1.1.10
(env) root@pypiserver:/opt/pypi# deactivate
root@pypiserver:/opt/pypi#
```

Y con esto tenemos el *virtualenv*. Si no ha habido problemas, y no lo pensamos reconstruir, es un buen momento para eliminar los *scripts* de creación del mismo.

```bash
root@pypiserver:/opt/pypi# rm -R virtualenv-15.0.2*
root@pypiserver:/opt/pypi#
```

Vamos a hacer que nuestro servidor sirva los paquetes de una carpeta *packages*, dentro de la carpeta contenedora. Como no existe esta carpeta *packages*, la creamos.

```bash
root@pypiserver:/opt/pypi# mkdir packages
root@pypiserver:/opt/pypi#
```

Y finalmente creamos una aplicación **WSGI** para poder servir nuestros paquetes. Realmente es una instancia de la aplicación que ofrece el paquete *pypiserver*, con la única diferencia que consiste en especificar la raíz de los paquetes servidos.

```bash
root@pypiserver:/opt/pypi# cat app.py
import pypiserver
app = pypiserver.app(root='/opt/pypi/packages')
root@pypiserver:/opt/pypi#
```

Lo único que queda es servir la aplicación en un servidor de nuestra preferencia. En mi caso he optado por **uwsgi**, por lo que lo instalo. Se va a usar el modo *emperor* por comodidad.

```bash
root@pypiserver:/opt/pypi# apt-get install -y uwsgi-emperor uwsgi-plugin-python
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
...
0 actualizados, 13 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 3.452 kB de archivos.
Se utilizarán 9.799 kB de espacio de disco adicional después de esta operación.
...
root@pypiserver:/opt/pypi#
```

De acuerdo con el modo *emperor*, necesitamos declarar la aplicación mediante un fichero de configuración. Con esto el *emperor* la tiene fichada y se encarga de mantenerla levantada.

```bash
root@pypiserver:/opt/pypi# cat /etc/uwsgi-emperor/vassals/pypiserver.ini
[uwsgi]
plugins = python
http-socket = :8080
master = true
workers = 2
chdir = /opt/pypi
virtualenv = /opt/pypi/env/
module = app:app
root@pypiserver:/opt/pypi#
```

## Añadiendo paquetes a nuestro servidor

Esta es la parte mas fácil de todas; basta con dejar nuestros paquetes **python** en la carpeta */opt/pypi/packages/*. Así de fácil.

El formato es cualquiera aceptado por *pip* o *easy_install*, pudiendo ser ficheros *.zip*, *.egg* o *.whl* entre otros; pueden ser descargados, compilados, o creados por nosotros mismos.

Para ver un ejemplo, voy a generar unos ficheros *.whl*, mediante el uso de *pip*. Esto nos garantiza que los tendremos cerca, pero que también van a estar ya compilados para la arquitectura concreta del servidor (presumiblemente la misma que van a usar los clientes).

```bash
root@pypiserver:~# /opt/pypi/env/bin/pip wheel -w /opt/pypi/packages/ flask mongoengine
Collecting flask
  Downloading Flask-0.11.1-py2.py3-none-any.whl (80kB)
    100% |████████████████████████████████| 81kB 599kB/s
  Saved /opt/pypi/packages/Flask-0.11.1-py2.py3-none-any.whl
Collecting mongoengine
  Downloading mongoengine-0.10.6.tar.gz (346kB)
    100% |████████████████████████████████| 348kB 560kB/s
Collecting click>=2.0 (from flask)
  Downloading click-6.6.tar.gz (283kB)
    100% |████████████████████████████████| 286kB 2.0MB/s
Collecting Werkzeug>=0.7 (from flask)
  Downloading Werkzeug-0.11.10-py2.py3-none-any.whl (306kB)
    100% |████████████████████████████████| 307kB 1.0MB/s
  Saved /opt/pypi/packages/Werkzeug-0.11.10-py2.py3-none-any.whl
Collecting Jinja2>=2.4 (from flask)
  Downloading Jinja2-2.8-py2.py3-none-any.whl (263kB)
    100% |████████████████████████████████| 266kB 2.1MB/s
  Saved /opt/pypi/packages/Jinja2-2.8-py2.py3-none-any.whl
Collecting itsdangerous>=0.21 (from flask)
  Downloading itsdangerous-0.24.tar.gz (46kB)
    100% |████████████████████████████████| 51kB 2.3MB/s
Collecting pymongo>=2.7.1 (from mongoengine)
  Downloading pymongo-3.2.2.tar.gz (504kB)
    100% |████████████████████████████████| 512kB 657kB/s
Collecting MarkupSafe (from Jinja2>=2.4->flask)
  Downloading MarkupSafe-0.23.tar.gz
Skipping flask, due to already being wheel.
Skipping Werkzeug, due to already being wheel.
Skipping Jinja2, due to already being wheel.
Building wheels for collected packages: mongoengine, click, itsdangerous, pymongo, MarkupSafe
  Running setup.py bdist_wheel for mongoengine ... done
  Stored in directory: /opt/pypi/packages
  Running setup.py bdist_wheel for click ... done
  Stored in directory: /opt/pypi/packages
  Running setup.py bdist_wheel for itsdangerous ... done
  Stored in directory: /opt/pypi/packages
  Running setup.py bdist_wheel for pymongo ... done
  Stored in directory: /opt/pypi/packages
  Running setup.py bdist_wheel for MarkupSafe ... done
  Stored in directory: /opt/pypi/packages
Successfully built mongoengine click itsdangerous pymongo MarkupSafe
root@pypiserver:~#
```

Y podemos ver que tenemos varios paquetes en la carpeta, algunos de ellos descargados ya en formato *wheel* (por ejemplo *flask*), y otros que se descargaron en formato *source* y se compilaron (por ejemplo *pymongo*).

```bash
root@pypiserver:~# ls -1 /opt/pypi/packages/
click-6.6-py2.py3-none-any.whl
Flask-0.11.1-py2.py3-none-any.whl
itsdangerous-0.24-py2-none-any.whl
Jinja2-2.8-py2.py3-none-any.whl
MarkupSafe-0.23-py2-none-any.whl
mongoengine-0.10.6-py2-none-any.whl
pymongo-3.2.2-cp27-cp27mu-linux_i686.whl
Werkzeug-0.11.10-py2.py3-none-any.whl
root@pypiserver:~#
```

## Usando el servidor desde un cliente

Ya que vamos a trabajar con **python**, aseguramos que lo tenemos instalado, o lo instalamos. Vamos a poner también la herramienta **wget** porque la vamos a necesitar.

```bash
root@pyclient:~# apt-get install -y wget python
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
...
0 actualizados, 25 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 14,9 MB de archivos.
Se utilizarán 56,9 MB de espacio de disco adicional después de esta operación.
...
root@pyclient:~#
```

Una prueba rápida: hay que ver que llegamos al servidor creado, y que este ofrece los paquetes en un formato adecuado.

```bash
root@pyclient:~# wget -qO- http://10.0.0.2:8080/simple/; echo ''
    <html>
        <head>
            <title>Simple Index</title>
        </head>
        <body>
            <h1>Simple Index</h1>
                 <a href="Flask/">Flask</a><br>
                 <a href="Jinja2/">Jinja2</a><br>
                 <a href="MarkupSafe/">MarkupSafe</a><br>
                 <a href="Werkzeug/">Werkzeug</a><br>
                 <a href="click/">click</a><br>
                 <a href="itsdangerous/">itsdangerous</a><br>
                 <a href="mongoengine/">mongoengine</a><br>
                 <a href="pymongo/">pymongo</a><br>
        </body>
    </html>

root@pyclient:~#
```

Descargamos los *scripts* de creación del *virtualenv*, tal como lo hacemos mas arriba.

```bash
root@pyclient:~# wget -q https://pypi.python.org/packages/5c/79/5dae7494b9f5ed061cff9a8ab8d6e1f02db352f3facf907d9eb614fb80e9/virtualenv-15.0.2.tar.gz
root@pyclient:~# tar xzf virtualenv-15.0.2.tar.gz
root@pyclient:~#
```

Creamos un *virtualenv* en donde instalar los paquetes y lo activamos.

```bash
root@pyclient:~# ./virtualenv-15.0.2/virtualenv.py env
New python executable in /root/env/bin/python
Installing setuptools, pip, wheel...done.
root@pyclient:~# . env/bin/activate
(env) root@pyclient:~#
```

Y lo usamos para instalar alguno de los paquetes. Es importante ver que modificamos el *index url*, para usar nuestro servidor, y que debemos indicarle que confíe en nuestro servidor.

```bash
(env) root@pyclient:~# pip install --trusted-host 10.0.0.2 -i http://10.0.0.2:8080/simple/ mongoengine
Collecting mongoengine
  Downloading http://10.0.0.2:8080/packages/mongoengine-0.10.6-py2-none-any.whl (90kB)
    100% |████████████████████████████████| 92kB 10.9MB/s
Collecting pymongo>=2.7.1 (from mongoengine)
  Downloading http://10.0.0.2:8080/packages/pymongo-3.2.2-cp27-cp27mu-linux_i686.whl (209kB)
    100% |████████████████████████████████| 215kB 9.9MB/s
Installing collected packages: pymongo, mongoengine
Successfully installed mongoengine-0.10.6 pymongo-3.2.2
(env) root@pyclient:~#
```

**TRUCO**: Podemos crear un fichero de configuración de *pip* para que esos parámetros queden ocultos.

```bash
(env) root@pyclient:~# mkdir -p /root/.config/pip/
(env) root@pyclient:~# cat /root/.config/pip/pip.conf
[global]
index-url = http://10.0.0.2:8080/simple/
trusted-host = 10.0.0.2
(env) root@pyclient:~#
```

Tras aplicar el truco, nos queda una orden *pip* bastante mas bonita, sin tantos parámetros que recordar y nos permite trabajar como la haríamos sin el servidor intermedio.

```bash
(env) root@pyclient:~# pip install flask
Collecting flask
  Downloading http://10.0.0.2:8080/packages/Flask-0.11.1-py2.py3-none-any.whl (80kB)
    100% |████████████████████████████████| 81kB 10.5MB/s
Collecting click>=2.0 (from flask)
  Downloading http://10.0.0.2:8080/packages/click-6.6-py2.py3-none-any.whl (71kB)
    100% |████████████████████████████████| 71kB 11.3MB/s
Collecting Werkzeug>=0.7 (from flask)
  Retrying (Retry(total=4, connect=None, read=None, redirect=None)) after connection broken by 'ProtocolError('Connection aborted.', error(104, 'Conexi\xc3\xb3n reinicializada por la m\xc3\xa1quina remota'))': /packages/Werkzeug-0.11.10-py2.py3-none-any.whl
  Downloading http://10.0.0.2:8080/packages/Werkzeug-0.11.10-py2.py3-none-any.whl (306kB)
    100% |████████████████████████████████| 307kB 8.3MB/s
Collecting Jinja2>=2.4 (from flask)
  Downloading http://10.0.0.2:8080/packages/Jinja2-2.8-py2.py3-none-any.whl (263kB)
    100% |████████████████████████████████| 266kB 9.0MB/s
Collecting itsdangerous>=0.21 (from flask)
  Downloading http://10.0.0.2:8080/packages/itsdangerous-0.24-py2-none-any.whl
Collecting MarkupSafe (from Jinja2>=2.4->flask)
  Downloading http://10.0.0.2:8080/packages/MarkupSafe-0.23-py2-none-any.whl
Installing collected packages: click, Werkzeug, MarkupSafe, Jinja2, itsdangerous, flask
Successfully installed Jinja2-2.8 MarkupSafe-0.23 Werkzeug-0.11.10 click-6.6 flask-0.11.1 itsdangerous-0.24
(env) root@pyclient:~#
```

Finalmente salimos del *virtualenv*.

```bash
(env) root@pyclient:~# deactivate
root@pyclient:~#
```

Como punto final, queda indicar que si el paquete no está en nuestro servidor, no pasa nada; nuestro servidor va a pasar la petición al índica *pypi* titular, de forma transparente.

```bash
root@pyclient:~# ./env/bin/pip install requests
Collecting requests
  Downloading requests-2.10.0-py2.py3-none-any.whl (506kB)
    100% |████████████████████████████████| 512kB 1.0MB/s
Installing collected packages: requests
Successfully installed requests-2.10.0
root@pyclient:~#
```

**TRUCO**: Activar un *virtualenv* solo pone su carpeta *bin* en el *PATH*. Podemos ahorrarnos comandos invocando directamente esos binarios, por ejemplo *pip*. Esto es lo que se ha hecho en el comando anterior.
