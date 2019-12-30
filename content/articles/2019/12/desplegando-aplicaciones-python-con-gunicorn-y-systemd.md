---
title: "Desplegando aplicaciones Python con Gunicorn y Systemd"
slug: "desplegando-aplicaciones-python-con-gunicorn-y-systemd"
date: "2019-12-30"
categories: ['Sistemas']
tags: ['python', 'gunicorn', 'systemd']
---

Hay veces en las que queremos desplegar de forma rápida una aplicación escrita
en **python**. En algunos casos, instalar un servidor de aplicaciones para
gestionar una sola aplicación nos puede parecer exagerado; así que instalamos
el servidor de aplicaciones **gunicorn** en el mismo *virtualenv* y relegamos
la gestión del proceso a *systemd*.
<!--more-->

## Estado inicial

Supongamos que tenemos una aplicación escrita en **python 3**; como pretendo
agilizar, voy a utilizar un ejemplo muy simple, con sus dependencias:

```bash
gerard@server:~$ cat app.py 
import bottle
from bottle import Bottle

app = Bottle()

@app.get('/')
def index():
    return 'Hello world!'
gerard@server:~$ 
```

```bash
gerard@server:~$ cat requirements.txt 
bottle==0.12.18
gerard@server:~$ 
```

Para instalar las librerías necesarias vamos a necesitar alguna herramienta,
como por ejemplo, **easy_install** o **pip**. Como me gusta aislar mis aplicaciones
entre sí, voy a utilizar un *virtualenv*, que ya las lleva ambas por defecto.

```bash
gerard@server:~$ sudo apt install python3-venv
...
gerard@server:~$ 
```

## Preparando nuestra aplicación

Lo primero que necesitamos es desplegar la aplicación y sus librerías en algún sitio;
Para ser ordenados, voy a crear una carpeta contenedora en `/srv/`, desde la que
vamos a trabajar de ahora en adelante.

```bash
gerard@server:/srv$ sudo install -o gerard -g gerard hello -d
gerard@server:/srv$ cd hello/
gerard@server:/srv/hello$ 
```

Por decisión de diseño, vamos a poner el fichero `requirements.txt` en esta carpeta,
y lo vamos a hacer convivir con una carpeta `app/` que contenga la aplicación y
con el *virtualenv* que incluya las librerías y el servidor **gunicorn**.

```bash
gerard@server:/srv/hello$ cp ~/requirements.txt .
gerard@server:/srv/hello$ mkdir app
gerard@server:/srv/hello$ cp ~/app.py app/
gerard@server:/srv/hello$ python3 -m venv env
gerard@server:/srv/hello$ 
```

Si lo hemos hecho bien, tendremos una estructura de esta forma:

```bash
gerard@server:/srv/hello$ tree -L 2
.
├── app
│   └── app.py
├── env
│   ├── bin
│   ├── include
│   ├── lib
│   ├── lib64 -> lib
│   ├── pyvenv.cfg
│   └── share
└── requirements.txt

7 directories, 3 files
gerard@server:/srv/hello$ 
```

El *virtualenv* debe contener las librerías de aplicación (que salen del fichero
`requirements.txt`) y el servidor de aplicaciones elegido, en este caso, **gunicorn**:

```bash
gerard@server:/srv/hello$ ./env/bin/pip install -r requirements.txt 
...
Successfully installed bottle-0.12.18
gerard@server:/srv/hello$ 
```

```bash
gerard@server:/srv/hello$ ./env/bin/pip install gunicorn
...
Successfully installed gunicorn-20.0.4
gerard@server:/srv/hello$ 
```

## Levantando la aplicación

Llegados a este punto, es tan fácil como invocar `gunicorn` para levantar la
aplicación. Como no queremos hacerlo a mano, lo vamos a delegar a un gestor de
procesos cualquiera; en este caso, se eligió utilizar el **init** del sistema,
que por tratarse de una **Debian 10**, es **systemd**.

Ya hemos escrito [algunos artículos sobre **systemd**][1], y no vamos a reiterar
en como se escriben. Solo es necesario indicar el comando a ejecutar y algunas
directivas que le den un contexto, por ejemplo el usuario o la carpeta de
ejecución.

La clave de todo esto es que **gunicorn** verá las librerías **python** que
tenga instaladas en su propio *virtualenv*; podemos elegir el *virtualenv* de
este binario **gunicorn** haciendo lo mismo que el *script* `activate`: poner
la carpeta `bin/` del *virtualenv* en el *path*, o en su defecto, indicando
el *path* completo a **gunicorn**.

```bash
gerard@server:/srv/hello$ cat /etc/systemd/system/hello.service
[Service]
DynamicUser=yes
WorkingDirectory=/srv/hello/app
ExecStart=/srv/hello/env/bin/gunicorn --bind 0.0.0.0:8080 app:app

[Install]
WantedBy=multi-user.target
gerard@server:/srv/hello$ 
```

**TRUCO**: Esta aplicación no escribe nada en el disco; por ello se ha decidido
ejecutarlo con un usuario *random*, cortesía de la directiva `DynamicUser`. Esto
hará que el *uid* del usuario que ejecuta **gunicorn** sea aleatorio (y no tendremos
problemas de permisos de escritura).

A partir de aquí, nuestra aplicación es un servicio más de los que gestiona
el servidor; basta con utilizar `systemctl` y `journalctl` para operarlo a
nuestra voluntad:

```bash
gerard@server:/srv/hello$ sudo systemctl enable hello
Created symlink /etc/systemd/system/multi-user.target.wants/hello.service → /etc/systemd/system/hello.service.
gerard@server:/srv/hello$ 
```

```bash
gerard@server:/srv/hello$ sudo systemctl start hello
gerard@server:/srv/hello$ 
```

Podemos comprobar que el servicio ejecuta con un simple `ps`, revisando si el
puerto 8080 está levantado o directamente haciendo alguna petición HTTP estándar:

```bash
gerard@server:/srv/hello$ ps faux | grep hello | grep -v grep
61895     3124  0.1  6.5  31416 15436 ?        Ss   16:29   0:00 /srv/hello/env/bin/python3 /srv/hello/env/bin/gunicorn --bind 0.0.0.0:8080 app:app
61895     3127  0.0  8.6  34492 20436 ?        S    16:29   0:00  \_ /srv/hello/env/bin/python3 /srv/hello/env/bin/gunicorn --bind 0.0.0.0:8080 app:app
gerard@server:/srv/hello$ 
```

```bash
gerard@server:/srv/hello$ ss -lnt | grep 8080
LISTEN    0         128                0.0.0.0:8080             0.0.0.0:*       
gerard@server:/srv/hello$ 
```

```bash
gerard@server:/srv/hello$ curl http://localhost:8080/ ; echo ''
Hello world!
gerard@server:/srv/hello$ 
```

También podemos inspeccionar los *logs*, por cortesía de `journalctl`:

```bash
gerard@server:/srv/hello$ sudo journalctl -u hello
-- Logs begin at Wed 2019-12-04 15:54:40 CET, end at Wed 2019-12-04 16:33:15 CET. --
dic 04 16:29:20 server systemd[1]: Started hello.service.
dic 04 16:29:21 server gunicorn[3124]: [2019-12-04 16:29:21 +0100] [3124] [INFO] Starting gunicorn 20.0.4
dic 04 16:29:21 server gunicorn[3124]: [2019-12-04 16:29:21 +0100] [3124] [INFO] Listening at: http://0.0.0.0:8080 (3124)
dic 04 16:29:21 server gunicorn[3124]: [2019-12-04 16:29:21 +0100] [3124] [INFO] Using worker: sync
dic 04 16:29:21 server gunicorn[3124]: [2019-12-04 16:29:21 +0100] [3127] [INFO] Booting worker with pid: 3127
gerard@server:/srv/hello$ 
```

**TRUCO**: En este caso convendría utilizar la opción `--access-logfile` y
`--access-logformat` de **gunicorn**, para poder ver en el *log* las peticiones
realizadas a la aplicación.

[1]: {{< relref "/articles/2015/11/escribiendo-units-en-systemd.md" >}}
