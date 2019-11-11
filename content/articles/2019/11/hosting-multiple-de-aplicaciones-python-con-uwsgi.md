---
title: "Hosting múltiple de aplicaciones Python con UWSGI"
slug: "hosting-multiple-de-aplicaciones-python-con-uwsgi"
date: "2019-11-11"
categories: ['Sistemas']
tags: ['python', 'uWSGI', 'nginx']
---

Desde que adopté **docker** no he vuelto a utilizar servidores de aplicaciones para
mis aplicaciones **python**. Sin embargo, en mi trabajo hay mucha gente que no confía
en **docker** y que prefieren utilizar servidores como llevan haciéndolo toda su vida
laboral, aunque se ha visto forzados a cambiar el lenguaje de programación usado.<!--more-->

El choque cultural cuando se encuentran delante de una aplicación **python** es el
descubrimiento de que se suele servir una aplicación concreta en un puerto diferente
del resto. Por supuesto, ellos están acostumbrados a *subpaths* y a *virtualhosts*.

En casos como estos, en donde pretenden poner varias aplicaciones en un solo servidor,
la elección más conservadora es utilizar **uwsgi**, que les permite trabajar con
versiones de **python** distintas y con conjuntos de librerías contenidas en sus
propios *virtualhosts*, evitando mezclar las librerías.

**NOTA**: La posibilidad de [escribir servicios y plantillas de systemd][1] para
levantar varias veces un servidor **gunicorn** les suele parecer magia negra, y lo
fácil para ellos es utilizar **uwsgi** en modo emperador.

Por todo ello, vamos a montar un servidor destinado a alojar varias aplicaciones
**python**, utilizando *unix sockets* para ocultar el tema de los puertos, y creando
la ilusión de una fachada única mediante *virtualhosts* de un **nginx**.

## Paquetes necesarios

Para que el montaje funcione, necesitamos un **nginx** y un **uwsgi** (en modo) emperador.
Como estamos hablando de servir aplicaciones en **python**, vamos a poner el *plugin*
adecuado para esta carga de trabajo; como tenemos unos compañeros habituados a tocar
*virtualenvs*, vamos a instalar también esta herramienta para disponer de ella.

```bash
gerard@debian:~$ sudo apt install nginx-light uwsgi-emperor uwsgi-plugin-python3 python3-venv
...
gerard@debian:~$ 
```

## Preparando la primera aplicación

Supongamos ahora que queremos desplegar una aplicación que nos viene hecha. Vamos
a destinar una carpeta para contener nuestro código y librerías, por ejemplo,
`/srv/demo/`, en donde estará nuestra aplicación de demostración.

Creamos la carpeta con los permisos que más nos convengan, entendiendo que **uwsgi**
solo necesita permisos de lectura. Por comodidad, me voy a poner de propietario
para no tener que utilizar **sudo** todo el rato:

```bash
gerard@debian:~$ sudo install -d -o gerard -g gerard /srv/demo
gerard@debian:~$ cd /srv/demo/
gerard@debian:/srv/demo$ 
```

Esperamos separar código de librerías, y por ello voy a crear una carpeta `app`
y un *virtualenv* `env`; dejaré el fichero `requirements.txt` fuera de ambas.

```bash
gerard@debian:/srv/demo$ mkdir app
gerard@debian:/srv/demo$ python3 -m venv env
gerard@debian:/srv/demo$ touch requirements.txt
gerard@debian:/srv/demo$ 
```

Es momento de desplegar la aplicación en la carpeta `app` y modificar el fichero
`requirements.txt` de acorde a nuestra aplicación. Por poner un ejemplo rápido,
pondré un ejemplo sencillo:

```bash
gerard@debian:/srv/demo$ cat app/app.py 
import bottle

app = bottle.Bottle()

@app.get('/')
def index():
    return 'Hello world\n'
gerard@debian:/srv/demo$ cat requirements.txt 
bottle==0.12.17
gerard@debian:/srv/demo$ 
```

Solo falta instalar las librerías especificadas en el fichero `requirements.txt`,
que se hace de forma trivial, sin ninguna necesidad de activar el *virtualenv*:

```bash
gerard@debian:/srv/demo$ ./env/bin/pip install -r requirements.txt 
Collecting bottle==0.12.17 (from -r requirements.txt (line 1))
...
Successfully installed bottle-0.12.17
gerard@debian:/srv/demo$ 
```

si lo hemos hecho bien, tenemos todo lo necesario para ejecutar nuestra aplicación:

```bash
gerard@debian:/srv/demo$ tree -L 2
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
gerard@debian:/srv/demo$ 
```

## Activando la aplicación

Como ya sabemos, cuando **uwsgi** actúa en modo emperador, basta con dejar un fichero
de configuración en la carpeta monitorizada para que levante una instancia que la gestione.

En el caso concreto de **Debian**, esta carpeta es `/etc/uwsgi-emperor/vassals` y el
fichero de configuración podría ser algo parecido a esto:

```bash
gerard@debian:/srv/demo$ cat /etc/uwsgi-emperor/vassals/demo.ini
[uwsgi]
plugins = python3
http-socket = /tmp/demo.sock
master = true
workers = 2
chdir = /srv/demo/app
virtualenv = /srv/demo/env
module = app:app
gerard@debian:/srv/demo$ 
```

Y con esto ya estamos; deberíamos tener un proceso *master* y dos *slaves* pendientes
de nuestra aplicación, y un *unix socket* escuchando en `/tmp/demo.sock`. Si la versión
de **curl** lo permite, podemos verificar que todo funciona en este punto:

```bash
gerard@debian:/srv/demo$ curl --unix-socket /tmp/demo.sock http://localhost/
Hello world
gerard@debian:/srv/demo$ 
```

**TRUCO**: Podemos simplificar la configuración utilizando *magic variables*, utilizando
el nombre del fichero de configuración como `%n`, lo que favorece el *copy-paste*.

```bash
gerard@debian:/srv/demo$ cat /etc/uwsgi-emperor/vassals/demo.ini
[uwsgi]
plugins = python3
http-socket = /tmp/%n.sock
master = true
workers = 2
chdir = /srv/%n/app
virtualenv = /srv/%n/env
module = app:app
gerard@debian:/srv/demo$ 
```

**WARNING**: No nos vale hacer un *soft link* a una plantilla, ya que un `touch` del mismo
provocaría el *reload* de todas las aplicaciones basadas en la plantilla; hacer un `touch -h`
tampoco ayuda, porque **uwsgi** seguiría monitorizando la plantilla y no el *soft link*.

## Escondiendo nuestra aplicación tras un proxy reverso nginx

Esta parte requiere un conocimiento de la configuración de **nginx**, tema en el que
no voy a entrar. Jugando con el `server_name`, los puertos y las `location` podemos simular
una estructura de *virtualhosts* y de *urls* a nuestro gusto.

La única parte importante es como pasar las peticiones a las aplicaciones **python**:
basta con hacer un `proxy_pass` al *unix socket*, y de acuerdo a la documentación, tendría
la forma tipo `<protocolo>://unix://<path-al-unix-socket>`.

Suponiendo que queramos pasar todas la peticiones de `demo.example.org` de forma
transparente a nuestra aplicación de demostración sin modificar la URL, bastaría una
configuración como la que sigue:

```bash
gerard@debian:/srv/demo$ cat /etc/nginx/sites-enabled/demo 
server {
	listen 8080;
	server_name demo.example.org;

	location / {
		include proxy_params;
		proxy_pass http://unix:///tmp/demo.sock;
	}
}
gerard@debian:/srv/demo$ 
```

**TRUCO**: Este **nginx** también es un buen candidato para hacer balanceo o terminación SSL.

A partir de aquí, poner y quitar aplicaciones es trivial.

[1]: {{< relref "/articles/2015/11/escribiendo-units-en-systemd.md" >}}
