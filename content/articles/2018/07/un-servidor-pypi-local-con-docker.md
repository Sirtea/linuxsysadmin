---
title: "Un servidor pypi local con Docker"
slug: "un-servidor-pypi-local-con-docker"
date: 2018-07-09
categories: ['Sistemas']
tags: ['python', 'PyPI', 'wheel', 'docker']
---

Estaba yo el otro día investigando una nueva librería de **python**, pero necesitaba de otra librería que se compilaba. Harto de perder el tiempo compilando cada vez esta librería, recuperé un antiguo artículo que me permitía distribuir el archivo *wheel* ya compilado tantas veces yo quisiera; como no, usando **docker**.<!--more-->

El artículo anterior es [este]({{< relref "/articles/2016/09/un-servidor-pypi-local.md" >}}), y su único objetivo era montar un servidor de **pypi** local que nos permite alojar nuestros ficheros *wheel*, aunque funciona genial para evitar múltiples compilaciones y como *caché* de paquetes.

## El servidor pypi

Para facilitar el montaje y la distribución de este servidor, se ha decidido hacer una imagen de **docker** para encapsular lo necesario; de paso, el fichero *Dockerfile* es una magnífica receta para evitar un montón de pasos manuales que salían en el artículo citado.

El fichero *Dockerfile* no puede ser más explícito; puesto que necesitamos instalar **pypiserver** mediante **pip**, los instalamos. También se define el comando que va a levantar el servidor y se crea la carpeta en donde deben residir nuestros paquetes. No veo muy útil crear un *virtualenv*; un contenedor **docker** ya es un entorno aislado en sí mismo.

```bash
gerard@sirius:~/workspace/pypiserver$ cat Dockerfile 
FROM alpine:3.7
RUN apk add --no-cache py2-pip tini && \
    pip install pypiserver && \
    mkdir /srv/packages
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/bin/pypi-server", "/srv/packages"]
gerard@sirius:~/workspace/pypiserver$ 
```

**TRUCO**: El binario `pypi-server` no cumple como un *init* correcto, y el contenedor no acaba hasta que **docker** lo mata. Para evitar ese problema, vamos a utilizar **tini**, tal y como explicamos en [otro artículo]({{< relref "/articles/2017/09/un-proceso-inicial-para-docker-tini-y-dumb-init.md" >}}).

Construimos la imagen con los comandos habituales y le damos un *tag* para su fácil uso cuando lo queramos levantar.

```bash
gerard@sirius:~/workspace/pypiserver$ docker build -t pypiserver .
...
Successfully tagged pypiserver:latest
gerard@sirius:~/workspace/pypiserver$ 
```

Y solo queda revisar que la imagen existe y que su tamaño tiene sentido:

```bash
gerard@sirius:~/workspace/pypiserver$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
pypiserver          latest              ad483ac352d7        56 seconds ago      52.8MB
alpine              3.7                 3fd9065eaf02        5 months ago        4.15MB
gerard@sirius:~/workspace/pypiserver$ 
```

Para el *runtime*, vamos a utilizar *docker-compose* para reducir la longitud del comando de levantamiento, dejándolo todo explícitamente declarado en el fichero *docker-compose.yml*.

La otra decisión de diseño es servir los *wheels* desde una carpeta local, en donde podemos ponerlos y quitarlos con gran facilidad. Solo necesitamos declarar la carpeta para los paquetes, que voy a poner en la misma carpeta del *docker-compose.yml*:

```bash
gerard@sirius:~/workspace/pypiserver$ tree
.
├── packages
├── docker-compose.yml
└── Dockerfile

1 directory, 2 files
gerard@sirius:~/workspace/pypiserver$ 
```

En el *docker-compose.yml* nos limitamos a montar la carpeta local como volumen y publicar el puerto del contenedor en nuestro servidor; esto hará el contenedor transparente a los ojos del resto de servidores.

```bash
gerard@sirius:~/workspace/pypiserver$ cat docker-compose.yml 
version: '3'
services:
  pypiserver:
    image: pypiserver
    container_name: pypiserver
    hostname: pypiserver
    volumes:
      - ./packages:/srv/packages:ro
    ports:
      - "8080:8080"
    restart: always
gerard@sirius:~/workspace/pypiserver$ 
```

Ya no falta nada para levantarlo todo y lo hacemos sin más preámbulos.

```bash
gerard@sirius:~/workspace/pypiserver$ docker-compose up -d
Creating network "pypiserver_default" with the default driver
Creating pypiserver
gerard@sirius:~/workspace/pypiserver$ 
```

Y con esto tenemos el servidor funcional.

## Rellenando nuestro servidor de paquetes

El único requisito para poder servir paquetes es dejarlos en la carpeta que a ese fin hemos destinado. No es importante como llegan los paquetes ahí; podemos:

* Descargarlos de [https://pypi.org/](https://pypi.org/)
* Pescarlos de nuestra caché local en `~/.cache/pip/`
* Obtenerlos mediante `pip wheel`

En este caso vamos a utilizar el tercer método. Como no tengo **pip** instalado en mi servidor, y para demostrar que solo necesito los ficheros *wheel*, voy a utilizar el **pip** de un *virtualenv* temporal, que destruiré al acabar. Otra opción sería crear un contenedor que los dejara en esa carpeta, que también montaría como un volumen.

```bash
gerard@sirius:~/workspace/pypiserver$ virtualenv env
Running virtualenv with interpreter /usr/bin/python2
New python executable in env/bin/python2
Also creating executable in env/bin/python
Installing setuptools, pip...done.
gerard@sirius:~/workspace/pypiserver$ 
```

Ni siquiera hace falta activar el *virtualenv*. Lo único que hace el *script* de activación es poner la carpeta *bin/* en el *PATH*, pero para lanzar el comando una vez no lo necesito...

```bash
gerard@sirius:~/workspace/pypiserver$ ./env/bin/pip wheel -w packages/ falcon mongoengine
...
gerard@sirius:~/workspace/pypiserver$ 
```

El comando `pip wheel` solo descarga los paquetes y los convierte en *wheels*, y los deja en la carpeta indicada, que es desde donde los servimos. Como ya tenemos lo que queríamos (los *wheels*), podemos eliminar el *virtualenv*, que nos deja la carpeta limpia de cosas innecesarias.

```bash
gerard@sirius:~/workspace/pypiserver$ rm -R env/
gerard@sirius:~/workspace/pypiserver$ 
```

Podemos ver que solo hemos conservado los ficheros *wheel* solicitados y sus dependencias; no hay más que lo estrictamente necesario.

```bash
gerard@sirius:~/workspace/pypiserver$ tree
.
├── packages
│   ├── falcon-1.4.1-py2.py3-none-any.whl
│   ├── mongoengine-0.15.0-py2-none-any.whl
│   ├── pymongo-3.6.1-cp27-none-linux_x86_64.whl
│   ├── python_mimeparse-1.6.0-py2.py3-none-any.whl
│   └── six-1.11.0-py2.py3-none-any.whl
├── docker-compose.yml
└── Dockerfile

1 directory, 7 files
gerard@sirius:~/workspace/pypiserver$ 
```

## Usando nuestro servidor local

El comando **pip** nos ofrece dos formas de añadir nuestro servidor: como URL única o como URL añadida a la normal. Haced un `pip install --help` para más detalles. Yo me decanto por usar solamente mi servidor, que aparentemente, tiene todo lo que necesito.

Supongamos que necesito el paquete **falcon** en el servidor **snowy**; lo instalamos con nuestro servidor local (*flag* `-i`) y punto. Observad las URLs de las que se descarga el paquete:

```bash
root@snowy:~# pip install --trusted-host 172.17.0.1 -i http://172.17.0.1:8080/ falcon
Looking in indexes: http://172.17.0.1:8080/
Collecting falcon
  Downloading http://172.17.0.1:8080/packages/falcon-1.4.1-py2.py3-none-any.whl (159kB)
    100% |████████████████████████████████| 163kB 7.8MB/s 
Collecting six>=1.4.0 (from falcon)
  Downloading http://172.17.0.1:8080/packages/six-1.11.0-py2.py3-none-any.whl
Collecting python-mimeparse>=1.5.2 (from falcon)
  Downloading http://172.17.0.1:8080/packages/python_mimeparse-1.6.0-py2.py3-none-any.whl
Installing collected packages: six, python-mimeparse, falcon
Successfully installed falcon-1.4.1 python-mimeparse-1.6.0 six-1.11.0
root@snowy:~# 
```

**NOTA**: El servidor local es HTTP plano, lo que lo convierte en un servidor no confiable; eso nos obliga  a poner el *flag* `--trusted-host` para que **pip** lo quiera usar. Otra opción sería utilizar HTTPS, lo que implica poner un *proxy reverso* delante, por ejemplo con **nginx**.

Otro servidor podría querer descargar los mismos paquetes u otros sin que eso nos repercuta en problemas, tal y como esperamos:

```bash
root@stormy:~# pip install --trusted-host 172.17.0.1 -i http://172.17.0.1:8080/ mongoengine
Looking in indexes: http://172.17.0.1:8080/
Collecting mongoengine
  Downloading http://172.17.0.1:8080/packages/mongoengine-0.15.0-py2-none-any.whl (99kB)
    100% |████████████████████████████████| 102kB 6.6MB/s 
Collecting pymongo>=2.7.1 (from mongoengine)
  Downloading http://172.17.0.1:8080/packages/pymongo-3.6.1-cp27-none-linux_x86_64.whl (256kB)
    100% |████████████████████████████████| 266kB 9.0MB/s 
Collecting six (from mongoengine)
  Downloading http://172.17.0.1:8080/packages/six-1.11.0-py2.py3-none-any.whl
Installing collected packages: pymongo, six, mongoengine
Successfully installed mongoengine-0.15.0 pymongo-3.6.1 six-1.11.0
root@stormy:~# 
```

Siempre y cuando utilizen los mismos tipos de CPU y versiones de **python**, pueden utilizar los mismos *wheels*. Eso nos evita compilarlos y reduce notoriamente el tiempo de red invertido en descargarlos.
