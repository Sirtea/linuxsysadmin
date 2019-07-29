---
title: "Creando un entorno escalable (III)"
slug: "creando-un-entorno-escalable-3"
date: 2016-03-14
categories: ['Sistemas']
tags: ['linux', 'debian', 'jessie', 'WSGI', 'uWSGI', 'python', 'virtualenv', 'firehol']
series: "Creando un entorno escalable"
---

En el artículo anterior de esta serie montamos el cluster de la base de datos que íbamos a necesitar para las aplicaciones que conformaban este entorno de ejemplo. Ahora que tenemos la base de datos, falta poner los servidores de aplicaciones que sirven nuestras aplicaciones y que usan el cluster.<!--more-->

Las aplicaciones que pretendemos servir son aplicaciones hechas en **python**, siguiendo el protocolo **WSGI**. Para ir rápidos, ambas utilizan el *framework* **bottle**. En realidad, nos sirve cualquier *framework* que construya aplicaciones **WSGI** estándares, de acuerdo al protocolo. Estas aplicaciones se conectan a la base de datos antes creadas para resolver las peticiones, mediante el *driver* de **mongodb**.

Desde el punto de vista de entrada al servidor, ambas aplicaciones se van a servir mediante el protocolo **HTTP** en puerto TCP 8080. Hay muchos servidores que sirven aplicaciones **WSGI**, por ejemplo, **Apache mod_wsgi**, **gunicorn** o **uWSGI**. De hecho hay docenas de ellos, casi todos capaces de servir aplicaciones **WSGI** en un puerto cualquiera TCP.

En este caso, usaremos un servidor de aplicaciones **uWSGI** que, aunque es un poco mas complicado que **gunicorn** (y menos que **mod_wsgi**), me tiene enamorado. Destaco especialmente el modo de funcionamiento *emperador* y la capacidad de usar un *virtualenv* distinto para cada aplicación servida. De hecho, puede servir diferentes lenguajes y/o versiones, una por cada aplicación.

## Instalar el servidor de aplicaciones

Este paso se repite en las máquinas *backend1*, *backend2* y  *backoffice*; aunque cada una va a servir una aplicación distinta, el servidor de aplicaciones es el mismo. En puntos posteriores pondremos y activaremos las aplicaciones.

El servidor **uWSGI** está disponible en los repositorios oficiales de *Debian Jessie*. Vamos a instalarlo con un *init script* que levante un emperador y le vamos a añadir el *plugin* para servir **python** (en la versión 2.7, según podemos ver).

```bash
root@backend1:~# apt-get install uwsgi-emperor uwsgi-plugin-python
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes extras:
  file libexpat1 libffi6 libjansson4 libmagic1 libmatheval1 libpgm-5.1-0 libpython2.7 libpython2.7-minimal libpython2.7-stdlib
  libsodium13 libsqlite3-0 libxml2 libyaml-0-2 libzmq3 mime-support sgml-base uwsgi-core xml-core
Paquetes sugeridos:
  sgml-base-doc nginx-full cherokee libapache2-mod-proxy-uwsgi libapache2-mod-uwsgi libapache2-mod-ruwsgi uwsgi-plugins-all
  uwsgi-extra python-uwsgidecorators debhelper
Se instalarán los siguientes paquetes NUEVOS:
  file libexpat1 libffi6 libjansson4 libmagic1 libmatheval1 libpgm-5.1-0 libpython2.7 libpython2.7-minimal libpython2.7-stdlib
  libsodium13 libsqlite3-0 libxml2 libyaml-0-2 libzmq3 mime-support sgml-base uwsgi-core uwsgi-emperor uwsgi-plugin-python
  xml-core
0 actualizados, 21 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 6.608 kB de archivos.
Se utilizarán 25,9 MB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
root@backend1:~#
```

Y con esto ya tenemos el servidor de aplicaciones en funcionamiento. Las instancias se declaran con un fichero de configuración en */etc/uwsgi-emperor/vassals/*, que haremos mas adelante.

## Consideraciones de seguridad

Estas aplicaciones usarán el *driver* **pymongo** para conectar a las instancias de **mongodb**. Para eso hay que habilitar el tráfico relativo (de los servidores de aplicaciones a los de mongodb, por el puerto TCP 27017).

En nuestro caso, como estamos trabajando con **LXC**, lo haremos desde el *host*, mediante la modificación de las reglas de *firehol*.

```bash
root@lxc:~# cat /etc/firehol/firehol.conf
mongo_servers="10.0.0.5 10.0.0.6 10.0.0.7"
app_servers="10.0.0.3 10.0.0.4 10.0.0.5"
...  
router internal inface lxc0 outface lxc0
...  
      route custom mongodb tcp/27017 default accept src "$app_servers" dst "$mongo_servers"
...  
root@lxc:~#
```

No os olvidéis de reiniciar el servicio *firehol*.

## Instalando las aplicaciones

Este punto se hace en los tres servidores que sirven aplicaciones (*backend1*, *backend2* y *backoffice*).

Las aplicaciones de ejemplo que vamos a usar las podéis encontrar en [este enlace](/downloads/shop.tar.gz). Debo admitir que no son bonitas, pero para esta demostración, nos valen.

Descomprimimos el fichero comprimido con las dos aplicaciones.

```bash
root@backend1:~# tar xzf shop.tar.gz
root@backend1:~#
```

Esta es la estructura que queda tras descomprimir:

```bash
root@backend1:~# tree
.
├── shop
│   ├── requirements.txt
│   ├── shop_admin
│   │   ├── app.py
│   │   └── views
│   │       ├── index.tpl
│   │       ├── product_form.tpl
│   │       └── product_list.tpl
│   └── shop_api
│       └── app.py
└── shop.tar.gz

4 directories, 7 files
root@backend1:~#
```

Esta estructura tiene las dos aplicaciones. Cada tipo de servidor usará solo una por simplicidad, así que borraremos la que no se utilice, de acuerdo al tipo de servidor.

En resumen, vamos a poner la carpeta *shop* en */opt/*, y vamos a poner dentro el *virtualenv* con las librerías necesarias.

Como buena *praxis*, vamos a instalar las librerías en un *virtualenv* dedicado por aplicación. Para ello necesitamos la herramienta, que puede salir del repositorio oficial o lo podemos descargar, para usarlo y desecharlo posteriormente. Podemos encontrar el paquete en [este enlace](https://pypi.python.org/packages/source/v/virtualenv/virtualenv-14.0.6.tar.gz#md5=a035037925c82990a7659ecf8764bcdb)

Lo descomprimimos y lo dejamos ahí, para que los puntos específicos para cada servidor lo usen a su antojo.

```bash
root@backend1:~# tar xzf virtualenv-14.0.6.tar.gz
root@backend1:~#
```

El *script* de creación del *virtualenv* se ejecuta con **python**; así que también lo necesitamos.

```
root@backend1:~# apt-get install python
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes extras:
  libpython-stdlib python-minimal python2.7 python2.7-minimal
Paquetes sugeridos:
  python-doc python-tk python2.7-doc binutils binfmt-support
Se instalarán los siguientes paquetes NUEVOS:
  libpython-stdlib python python-minimal python2.7 python2.7-minimal
0 actualizados, 5 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 1.854 kB de archivos.
Se utilizarán 5.131 kB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
..
root@backend1:~#
```

Veamos ahora los puntos específicos por tipo de aplicación.

### Aplicación de backend: la API pública

Este punto se ejecuta solamente en los *backends* (*backend1* y *backend2*).

Eliminamos la aplicación de administración, que no se usa en los *backends*.

```bash
root@backend1:~# rm -R shop/shop_admin/
root@backend1:~#
```

Así nos queda la carpeta:

```bash
root@backend1:~# tree shop
shop
├── requirements.txt
└── shop_api
    └── app.py

1 directory, 2 files
root@backend1:~#
```

Copiamos la carpeta a */opt/* que va a ser su emplazamiento habitual.

```bash
root@backend1:~# cp -R shop/ /opt/
root@backend1:~#
```

Vamos a trabajar ya desde la carpeta contenedora del proyecto.

```bash
root@backend1:~# cd /opt/shop/
root@backend1:/opt/shop#
```

El siguiente paso es crear el conjunto de librerías necesarias, construyendo un *virtualenv* con las librerías. 

```bash
root@backend1:/opt/shop# /root/virtualenv-14.0.6/virtualenv.py env
New python executable in /opt/shop/env/bin/python
Installing setuptools, pip, wheel...done.
root@backend1:/opt/shop#
```

Activamos el entorno virtual para instalar las librerías declaradas en el fichero *requirements.txt*. Luego salimos del entorno.

```bash
root@backend1:/opt/shop# . env/bin/activate
(env) root@backend1:/opt/shop# pip install -r requirements.txt
Collecting bottle==0.12.9 (from -r requirements.txt (line 1))
...
Installing collected packages: bottle, pymongo
Successfully installed bottle-0.12.9 pymongo-3.2
(env) root@backend1:/opt/shop# deactivate
root@backend1:/opt/shop#
```

Y para evitarnos problemas de permisos, uniformizamos el propietario de la carpeta:

```bash
root@backend1:~# chown -R www-data:www-data /opt/shop/
root@backend1:~#
```

Con todo lo necesario para levantar la aplicación, la declaramos como *vasallo* del *emperador*; el mismo **emperador** va a levantar un proceso para servir esa configuración.

```bash
root@backend1:/opt/shop# cat /etc/uwsgi-emperor/vassals/shop_api.ini
[uwsgi]
plugin = python
http-socket = 0.0.0.0:8080
master = true
workers = 2
virtualenv = /opt/shop/env
chdir = /opt/shop/shop_api
module = app:app
root@backend1:/opt/shop#
```

Y podemos comprobar que todo funciona como debe haciendo una petición a la **API**.

```bash
root@backend1:~# curl -i http://localhost:8080/products/
HTTP/1.1 200 OK
Content-Length: 3
Content-Type: application/json
Backend: backend1

[]
root@backend1:~#
```

### Aplicación de backoffice: la interfaz de administración

Este punto aplica solamente a la máquina *backoffice*.

El proceso es análogo al de los *backends*; quitamos la aplicación que no vamos a utilizar.

```bash
root@backoffice:~# rm -R shop/shop_api/
root@backoffice:~#
```
Así nos queda la carpeta:

```bash
root@backoffice:~# tree shop
shop
├── requirements.txt
└── shop_admin
    ├── app.py
    └── views
        ├── index.tpl
        ├── product_form.tpl
        └── product_list.tpl

2 directories, 5 files
root@backoffice:~#
```

La transferimos a la carpeta */opt/*.

```bash
root@backoffice:~# cp -R shop/ /opt/
root@backoffice:~#
```

Nos situamos en la carpeta contenedora:

```bash
root@backoffice:~# cd /opt/shop/
root@backoffice:/opt/shop#
```

Creamos el *virtualenv* en la carpeta contenedora.

```bash
root@backoffice:/opt/shop# /root/virtualenv-14.0.6/virtualenv.py env
New python executable in /opt/shop/env/bin/python
Installing setuptools, pip, wheel...done.
root@backoffice:/opt/shop#
```

Y le instalamos las librerías necesarias, declaradas en el fichero *requirements.txt*.

```bash
root@backoffice:/opt/shop# . env/bin/activate
(env) root@backoffice:/opt/shop# pip install -r requirements.txt
Collecting bottle==0.12.9 (from -r requirements.txt (line 1))
...
Installing collected packages: bottle, pymongo
Successfully installed bottle-0.12.9 pymongo-3.2
(env) root@backoffice:/opt/shop# deactivate
root@backoffice:/opt/shop#
```

Actualizamos el propietario de la aplicación **WSGI**.

```bash
root@backoffice:/opt/shop# chown -R www-data:www-data /opt/shop/
root@backoffice:/opt/shop#
```

Y creamos el fichero de configuración del *vasallo*, para que lo levante el *emperador*, quedando así:

```bash
root@backoffice:/opt/shop# cat /etc/uwsgi-emperor/vassals/shop_admin.ini
[uwsgi]
plugin = python
http-socket = 0.0.0.0:8080
master = true
workers = 2
virtualenv = /opt/shop/env
chdir = /opt/shop/shop_admin
module = app:app
root@backoffice:/opt/shop#
```

Y comprobamos que obtenemos la página web que se espera:

```bash
root@backoffice:~# curl -i http://localhost:8080/
HTTP/1.1 200 OK
Content-Length: 33
Content-Type: text/html; charset=UTF-8

<a href="/products">Products</a>
root@backoffice:~#
```

Y con esto hemos acabado con las aplicaciones. Nuevamente, todo lo que queda en la carpeta */root/* es desechable.

En el siguiente artículo vamos a montar el *proxy*/balanceador que va a actuar como fachada de todo el sistema.
