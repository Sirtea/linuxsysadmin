---
title: "Tipos de volúmenes en Docker"
slug: "tipos-de-volumenes-en-docker"
date: 2016-07-18
categories: ['Operaciones']
tags: ['docker', 'volumenes']
---

Una de las mas importantes funcionalidades de **Docker** son los volúmenes. Estos no son mas que carpetas en nuestro sistema de ficheros y son capaces de sobrevivir al ciclo de vida normal del contenedor. Eso nos permite, entre otras cosas, compartir varios ficheros con otros contenedores o con el *host*.<!--more-->

Los volúmenes son bastante útiles porque permiten compartirse entre contenedores, o el propio *host*. Eso nos permite consultar todos los *logs* cómodamente desde un contenedor dedicado, hacer *backups* de un contenedor desde otro dedicado, o recuperar esos mismo *backups* hacia nuestro *host*.

De hecho, he visto contenedores con la única función de producir ficheros (*.tar.gz*, *.deb*, ...) en volúmenes que luego son consumidos por servicios de *runtime*, por ejemplo un servidor web, un repositorio o simplemente un NFS.

Los volúmenes pueden ser de 3 tipos distintos, y se categorizan según esta lista:

* Data volumes
    * Anonymous data volumes
    * Named data volumes
* Mounted volumes

## Data volumes

Se trata de carpetas que se crean en */var/lib/docker/* y que pueden compartirse entre diferentes contenedores.

### Anonymous data volumes

Se crean cuando se levanta un contenedor, mediante el comando *docker run*, por ejemplo:

```bash
gerard@sirius:~$ docker run -ti --rm -v /data alpine:3.4 sh
/ # 
```

Esto nos crea un volumen asociado al contenedor creado.

```bash
root@sirius:~# docker volume ls
DRIVER              VOLUME NAME
local               1b39e6601cd3711c27f3a1a4eb50d82e182151fd14b82048f47b0d50ad22b97a
root@sirius:~# tree /var/lib/docker/volumes/
/var/lib/docker/volumes/
├── 1b39e6601cd3711c27f3a1a4eb50d82e182151fd14b82048f47b0d50ad22b97a
│   └── _data
└── metadata.db

2 directories, 1 file
root@sirius:~# 
```

A su vez, otro contenedor puede montar los volúmenes de otro contenedor, ya sea porque los creó o porque los ha montado de un tercero.

```bash
root@sirius:~# docker run -ti --rm --volumes-from adoring_lovelace alpine:3.4 sh
/ # 
```

Ahora mismo, la carpeta */data/* pertenece al primer contendor, pero es la misma para ambos contenedores.

**Docker** mantiene una cuenta de los contenedores que están usando un volumen, y estos solo se eliminan cuando el último contenedor que lo usa sale con el parámetro *--rm* o si se hace un *docker rm -v*. En cualquier otro caso, el volumen se queda parasitando, hasta que lo eliminamos manualmente usado *docker volume rm*.

### Named data volumes

Estos volúmenes no dependen de ningún contenedor concreto, y se pueden montar en cualquier contenedor. Se crean específicamente usando el comando *docker volume create*, o al ejecutar un contenedor si le damos un nombre en la línea de comandos.

```bash
gerard@sirius:~$ docker volume create --name vol1
vol1
gerard@sirius:~$ docker run -ti --rm -v vol2:/data alpine:3.4 true
gerard@sirius:~$ docker volume ls
DRIVER              VOLUME NAME
local               vol1
local               vol2
gerard@sirius:~$ 
```

Estos volúmenes no se eliminan por si solos nunca y persisten cuando su contenedor desaparece. Para eliminarlos se necesita una intervención manual mediante el comando *docker volume rm*.

```bash
gerard@sirius:~$ docker volume ls
DRIVER              VOLUME NAME
local               vol1
local               vol2
gerard@sirius:~$ docker volume rm vol1 vol2
vol1
vol2
gerard@sirius:~$ docker volume ls
DRIVER              VOLUME NAME
gerard@sirius:~$ 
```

## Mounted volumes

Otras veces nos interesa montar ficheros o carpetas desde la máquina *host*. En este caso, podemos montar la carpeta o el fichero especificando la ruta completa desde la máquina *host*, y la ruta completa en el contenedor. Es posible también especificar si el volumen es de lectura y escritura (por defecto) o de solo lectura.

```bash
gerard@sirius:~/docker$ docker run -ti --rm -v /etc/hostname:/root/parent_name:ro -v /opt/:/data alpine:3.4 sh
/ # cat /root/parent_name 
sirius
/ # ls /data/
/ # 
```

Este último caso es ideal para recuperar *backups* o ficheros generados en un contenedor, en vistas a su utilización futura por parte de otros contenedores o del mismo *host*.
