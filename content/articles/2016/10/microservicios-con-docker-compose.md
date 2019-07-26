---
title: "Microservicios con docker-compose"
slug: "microservicios-con-docker-compose"
date: 2016-10-24
categories: ['Operaciones']
tags: ['docker', 'docker-compose', 'microservicios']
---

**Docker** es una gran herramienta para levantar contenedores aislados, pero en el mundo real nos encontramos con despliegues mas complejos, que requieren varias imágenes trabajando en conjunto. En este caso, levantar los contenedores puede ser una auténtica pesadilla. Para automatizar estos casos podemos utilizar un *orquestador*, como por ejemplo, **docker-compose**.<!--more-->

Para entender como funciona nos vamos a servir de un microservicio básico, que consiste en un *balanceador* público y varios *frontends*, que en este caso van a ser mínimos para no complicar innecesariamente este artículo.

Estos *frontends* van a responder a las peticiones con su *hostname*, solo para ver que el balanceador hace lo que debe. En un caso mas cercano a la realidad, las aplicaciones harían algo mas útil, posiblemente utilizando una base de datos.

## El balanceador

Esta imagen se declara con un *Dockerfile* y sus ficheros auxiliares. Aunque en este caso se ha copiado un [artículo anterior]({{< relref "/articles/2016/09/imagenes-docker-reusables-mediante-configuraciones-dinamicas.md" >}}), se vuelven a exponer los ficheros por comodidad.

```bash
gerard@sirius:~/docker/composetest$ cat balancer/Dockerfile 
FROM alpine:3.4
RUN apk add --no-cache nginx && \
    ln -s /dev/stdout /var/log/nginx/access.log && \
    ln -s /dev/stderr /var/log/nginx/error.log && \
    mkdir /run/nginx
COPY nginx.conf /etc/nginx/
COPY config.sh entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]
gerard@sirius:~/docker/composetest$ cat balancer/nginx.conf 
worker_processes  1;
events {
	worker_connections  1024;
}
http {
	include mime.types;
	default_type application/octet-stream;
	sendfile on;
	keepalive_timeout 65;
	include conf.d/*;
}
gerard@sirius:~/docker/composetest$ cat balancer/config.sh 
#!/bin/sh

echo "upstream backend {"
for BACKEND in $(echo ${BACKENDS} | sed 's/,/ /g'); do
echo "	server $BACKEND;"
done
echo """\
}

server {
	listen 80;
	server_name _;

	location / {
		proxy_pass http://backend;
	}
}
"""
gerard@sirius:~/docker/composetest$ cat balancer/entrypoint.sh 
#!/bin/sh

./config.sh > /etc/nginx/conf.d/balancer
exec /usr/sbin/nginx -g "daemon off;"
gerard@sirius:~/docker/composetest$ 
```

## El frontend

Vamos a poner una aplicación básica en **python**, que se va a servir con el servidor de aplicaciones **uWSGI** y solo va a informar de su *hostname*. Ahí pego su *Dockerfile* y los otros ficheros auxiliares.

```bash
gerard@sirius:~/docker/composetest$ cat frontend/Dockerfile 
FROM alpine:3.4
RUN apk add --no-cache uwsgi-python
COPY app.py app.ini /opt/app/
ENTRYPOINT ["uwsgi", "--plugin=python", "/opt/app/app.ini"]
gerard@sirius:~/docker/composetest$ cat frontend/app.py 
import os

def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    yield os.uname()[1] + '\n'
gerard@sirius:~/docker/composetest$ cat frontend/app.ini 
[uwsgi]
http-socket = :8080
chdir = /opt/app/
module = app:app
gerard@sirius:~/docker/composetest$ 
```

## Declarando y levantando el servicio con docker-compose

Vamos a crear un fichero para gobernar las acciones de **docker-compose**, siguiendo la [documentación](https://docs.docker.com/compose/compose-file/). La filosofía es muy simple; vamos a declarar como se construyen las imágenes, los puertos que publican y exponen, las variables de entorno necesarias y las dependencias entre las imágenes.

Empezamos con la imagen que no tiene dependencias, que es el *frontend*. Simplemente indicamos la carpeta que contiene el *Dockerfile* (desde la carpeta actual, por ejemplo), y vamos a indicar el puerto que expone, tal como indica la configuración de **uWSGI**.

El balanceador es un poco mas complejo; hay que indicar que no se puede levantar hasta que lo hagan los *frontends*, porque sino, el **nginx** no puede resolver sus nombres y acabaría inmediatamente. Hay que indicar que necesita acceso a los *frontends* para comunicar con su puerto 8080, y que vamos a publicar el puerto 80 en el contenedor como el 8888 en nuestra máquina física. El último paso es declarar las variables de entorno que se van a pasar al contenedor cuando este se ejecute; en este caso declaramos los servidores contra los que hay que hacer balanceo.

**IMPORTANTE**: Cuando ejecutemos **docker-compose**, va a levantar una instancia de cada imagen, pudiendo escalar a *posteriori*. Como **nginx** no va  levantar si no conoce alguno de los *hostnames* contra los que balancea, vamos indicar solamente el primero.

```bash
gerard@sirius:~/docker/composetest$ cat docker-compose.yml 
version: '2'
services:
  frontend:
    build: frontend
    expose:
      - 8080
  balancer:
    build: balancer
    depends_on:
      - frontend
    links:
      - frontend
    ports:
      - "8888:80"
    environment:
      - BACKENDS=composetest_frontend_1:8080
gerard@sirius:~/docker/composetest$ 
```

Con todo delcarado, solo nos falta levantar el servicio. Esto va a reconstruir todas las imágenes que crea necesarias, ya levantar los contenedores que no lo estén.

```bash
gerard@sirius:~/docker/composetest$ docker-compose up -d
Creating network "composetest_default" with the default driver
Building frontend
Step 1 : FROM alpine:3.4
 ---> 4e38e38c8ce0
Step 2 : RUN apk add --no-cache uwsgi-python
 ---> Running in a57c36878d96
fetch http://dl-cdn.alpinelinux.org/alpine/v3.4/main/x86_64/APKINDEX.tar.gz
fetch http://dl-cdn.alpinelinux.org/alpine/v3.4/community/x86_64/APKINDEX.tar.gz
(1/14) Installing mailcap (2.1.44-r0)
(2/14) Installing pcre (8.38-r1)
(3/14) Installing uwsgi (2.0.13-r0)
(4/14) Installing libbz2 (1.0.6-r4)
(5/14) Installing expat (2.1.1-r1)
(6/14) Installing libffi (3.2.1-r2)
(7/14) Installing gdbm (1.11-r1)
(8/14) Installing ncurses-terminfo-base (6.0-r7)
(9/14) Installing ncurses-terminfo (6.0-r7)
(10/14) Installing ncurses-libs (6.0-r7)
(11/14) Installing readline (6.3.008-r4)
(12/14) Installing sqlite-libs (3.13.0-r0)
(13/14) Installing python (2.7.12-r0)
(14/14) Installing uwsgi-python (2.0.13-r0)
Executing busybox-1.24.2-r9.trigger
OK: 53 MiB in 25 packages
 ---> 9749e8e317a7
Removing intermediate container a57c36878d96
Step 3 : COPY app.py app.ini /opt/app/
 ---> 98c310db1c73
Removing intermediate container 141de70e5976
Step 4 : ENTRYPOINT uwsgi --plugin=python /opt/app/app.ini
 ---> Running in 7e5243bddee1
 ---> 27da8b15e8b4
Removing intermediate container 7e5243bddee1
Successfully built 27da8b15e8b4
Creating composetest_frontend_1
Building balancer
Step 1 : FROM alpine:3.4
 ---> 4e38e38c8ce0
Step 2 : RUN apk add --no-cache nginx &&     ln -s /dev/stdout /var/log/nginx/access.log &&     ln -s /dev/stderr /var/log/nginx/error.log &&     mkdir /run/nginx
 ---> Running in 5e7a6e24b1ea
fetch http://dl-cdn.alpinelinux.org/alpine/v3.4/main/x86_64/APKINDEX.tar.gz
fetch http://dl-cdn.alpinelinux.org/alpine/v3.4/community/x86_64/APKINDEX.tar.gz
(1/3) Installing nginx-common (1.10.1-r1)
Executing nginx-common-1.10.1-r1.pre-install
(2/3) Installing pcre (8.38-r1)
(3/3) Installing nginx (1.10.1-r1)
Executing busybox-1.24.2-r9.trigger
OK: 6 MiB in 14 packages
 ---> b413d5ba8f3b
Removing intermediate container 5e7a6e24b1ea
Step 3 : COPY nginx.conf /etc/nginx/
 ---> e7db8e5794db
Removing intermediate container e33eef86f883
Step 4 : COPY config.sh entrypoint.sh /
 ---> e6fda1c75d22
Removing intermediate container 6cd5103894a9
Step 5 : ENTRYPOINT /entrypoint.sh
 ---> Running in cd26bbeaa306
 ---> ff47baa82723
Removing intermediate container cd26bbeaa306
Successfully built ff47baa82723
Creating composetest_balancer_1
gerard@sirius:~/docker/composetest$ 
```

Podemos ver que ahora tenemos un solo contenedor por imagen declarada:

```bash
gerard@sirius:~/docker/composetest$ docker-compose ps
         Name                       Command               State          Ports         
--------------------------------------------------------------------------------------
composetest_balancer_1   /entrypoint.sh                   Up      0.0.0.0:8888->80/tcp 
composetest_frontend_1   uwsgi --plugin=python /opt ...   Up      8080/tcp             
gerard@sirius:~/docker/composetest$ 
```

Y si probamos nuestro servicio, vemos que funciona, aunque solo balancea contra un *frontend*, que es lo que indicamos.

```bash
gerard@sirius:~/docker/composetest$ curl http://localhost:8888/
9ae8f4367e2b
gerard@sirius:~/docker/composetest$ curl http://localhost:8888/
9ae8f4367e2b
gerard@sirius:~/docker/composetest$ curl http://localhost:8888/
9ae8f4367e2b
gerard@sirius:~/docker/composetest$ 
```

## Escalando nuestro servicio

Escalar no es fácil; **docker-compose** solo nos permite modificar el número de contenedores de cada tipo que están corriendo en un momento dado. Para que estos nuevos contenedores reciban peticiones, hay que modificar la configuración del balanceador.

Empezaremos levantando otras 3 instancias de nuestro *frontend*; indicando que queremos 4, **docker-compose** va a levantar las 3 que faltan.

```bash
gerard@sirius:~/docker/composetest$ docker-compose scale frontend=4
Creating and starting 2 ... done
Creating and starting 3 ... done
Creating and starting 4 ... done
gerard@sirius:~/docker/composetest$ 
```

Para la parte del balanceador, no nos queda mas remedio que reconstruirlo. Por suerte, nuestra imagen se configura con variables de entorno, de forma que **docker-compose** solo va a levantar un contenedor nuevo, sin el proceso de reconstruir la imagen, que es innecesario.

Vamos a modificar el *docker-compose.yml*, para cambiar la variable de entorno *BACKENDS*. Como ya tenemos 4 instancias funcionando, no hay problema por parte del **nginx**.

```bash
gerard@sirius:~/docker/composetest$ cat docker-compose.yml 
version: '2'
services:
  frontend:
    build: frontend
    expose:
      - 8080
  balancer:
    build: balancer
    depends_on:
      - frontend
    links:
      - frontend
    ports:
      - "8888:80"
    environment:
      - BACKENDS=composetest_frontend_1:8080,composetest_frontend_2:8080,composetest_frontend_3:8080,composetest_frontend_4:8080
gerard@sirius:~/docker/composetest$ 
```

Levantamos el servicio de nuevo, y dejamos que **docker-compose** aplique su buen criterio. Vemos que no va a hacer nada con los *frontends* porque no han cambiado, y va a recrear el balanceador, con un tiempo mínimo.

```bash
gerard@sirius:~/docker/composetest$ docker-compose up -d
composetest_frontend_4 is up-to-date
composetest_frontend_2 is up-to-date
composetest_frontend_3 is up-to-date
composetest_frontend_1 is up-to-date
Recreating composetest_balancer_1
gerard@sirius:~/docker/composetest$ 
```

Vemos que efectivamente hay nuestros 5 contenedores en marcha:

```bash
gerard@sirius:~/docker/composetest$ docker-compose ps
         Name                       Command               State          Ports         
--------------------------------------------------------------------------------------
composetest_balancer_1   /entrypoint.sh                   Up      0.0.0.0:8888->80/tcp 
composetest_frontend_1   uwsgi --plugin=python /opt ...   Up      8080/tcp             
composetest_frontend_2   uwsgi --plugin=python /opt ...   Up      8080/tcp             
composetest_frontend_3   uwsgi --plugin=python /opt ...   Up      8080/tcp             
composetest_frontend_4   uwsgi --plugin=python /opt ...   Up      8080/tcp             
gerard@sirius:~/docker/composetest$ 
```

Y solo nos queda admirar como funcionan las peticiones balanceadas, siguiendo el algoritmo *round robin*.

```bash
gerard@sirius:~/docker/composetest$ curl http://localhost:8888/
9ae8f4367e2b
gerard@sirius:~/docker/composetest$ curl http://localhost:8888/
7490edd50676
gerard@sirius:~/docker/composetest$ curl http://localhost:8888/
63e9d7476267
gerard@sirius:~/docker/composetest$ curl http://localhost:8888/
4b6b11513400
gerard@sirius:~/docker/composetest$ curl http://localhost:8888/
9ae8f4367e2b
gerard@sirius:~/docker/composetest$ curl http://localhost:8888/
7490edd50676
gerard@sirius:~/docker/composetest$ curl http://localhost:8888/
63e9d7476267
gerard@sirius:~/docker/composetest$ curl http://localhost:8888/
4b6b11513400
gerard@sirius:~/docker/composetest$ 
```
