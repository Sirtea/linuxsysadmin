---
title: "Una imagen de Docker para hacer backups de MongoDB"
slug: "una-imagen-de-docker-para-hacer-backups-de-mongodb"
date: "2020-01-28"
categories: ['Operaciones']
tags: ['docker', 'swarm', 'mongodb', 'backup']
---

Uno de los aspectos que voy dejando de lado en mis artículos es el tema de los
*backups*; suele bastar con ejecutar algún comando o *script* en una tarea tipo
**cron**. Si el servicio **mongodb** se encuentra en **docker**, a veces queda
inaccesible fuera de **docker** y hay que *dockerizar* el *backup*.
<!--more-->

De esta forma, el contenedor que ejecuta los *backups* tiene acceso a las redes
definidas dentro del propio **docker** y puede acceder cómodamente por nombre
de servicio. Ya de paso, este contenedor de *backup* queda declarado en nuestros
*stacks* y no corremos el riesgo de perder las tareas **cron** si se nos cae el
servidor o lo cambiamos en un futuro.

Para hacer un contenedor de *backups*, solo necesitamos 2 cosas:

* Las herramientas para hacer el *backup*
* Una forma de lanzar tareas cada cierto tiempo

Ya vimos en otros artículos el [uso de **cron** en un contenedor][1] u otro caso
de [uso de un **cron** alternativo][2], pero seamos sinceros: en el mundo de
**docker** la simplicidad cuenta, y un *script* puede ser una prueba de concepto
fácil, de esas que suelen quedarse de forma permanente.

**NOTA**: Si se quiere reemplazar el contenedor en el futuro por uno con un
**cron** decente, es posible; pero queda como tarea para el lector.

## Decisiones de diseño

Para hacer una imagen parametrizable, vamos a tomar algunas decisiones de diseño:

* Vamos a configurar el *scheduler* con variables de entorno
  * `DELAY` indica el tiempo de espera hasta la primera ejecución (opcional)
  * `INTERVAL` indica el intervalo entre ejecuciones
* Vamos a configurar el comando de *backup* con otras variables de entorno
  * `MONGODB_URI` es la cadena de conexión a nuestro objetivo (el segmento de base de datos se puede omitir, para hacerlas todas)
  * `FILENAME` es la plantilla del nombre de fichero que se va a generar, con el *path* completo a guardar

## Una posible implementación

**NOTA**: Voy a poner los tiempos al comando `sleep` y el FILENAME al comando
`date`; más información sobre su formato en la documentación de cada uno.

Con estas especificaciones de configuración, el *scheduler* es un ejercicio
de *scripting* simple. Solamente voy a acabar el comando `mongodump` con un `&`
para que el tiempo de ejecución del *backup* no retrase la espera del
siguiente intervalo.

```bash
gerard@atlantis:~/Escritorio/mongobackup$ cat build/scheduler.sh 
#!/bin/bash

test -n "${MONGODB_URI}" || { echo "MONGODB_URI not defined" >&2; exit 1; }
test -n "${FILENAME}" || { echo "FILENAME not defined" >&2; exit 1; }
test -n "${INTERVAL}" || { echo "INTERVAL not defined" >&2; exit 1; }

sleep ${DELAY:-0}
while true; do
	mongodump --uri=${MONGODB_URI} --archive=$(date +${FILENAME}) --gzip &
	sleep ${INTERVAL}
done
gerard@atlantis:~/Escritorio/mongobackup$ 
```

**TRUCO**: Podemos mover el comando `mongodump` a un *script* propio, que puede
hacer más comandos con el fichero resultado, como por ejemplo, subirlo o un (S)FTP
o a un *storage* en la nube. Sed creativos en este punto.

La construcción de la imagen tampoco entraña ninguna complejidad; basta con
seguir el [procedimiento de instalación][3] para la imagen base elegida, o
utilizar [una imagen que ya lo contenga][4], añadir el *scheduler* y ejecutarlo
como proceso del contenedor.

```bash
gerard@atlantis:~/Escritorio/mongobackup$ cat build/Dockerfile 
FROM debian:buster-slim
RUN apt update && \
    apt install -y wget gnupg && \
    wget -qO- https://www.mongodb.org/static/pgp/server-4.2.asc | apt-key add - && \
    echo "deb http://repo.mongodb.org/apt/debian buster/mongodb-org/4.2 main" > /etc/apt/sources.list.d/mongodb-org-4.2.list && \
    apt update && \
    apt install -y mongodb-org-tools && \
    rm -rf /var/lib/apt/lists/*
COPY scheduler.sh /
CMD ["/scheduler.sh"]
gerard@atlantis:~/Escritorio/mongobackup$ 
```

**NOTA**: Si partimos de la imagen oficial de **mongodb**, sería tan fácil
como copiar el *script* y declarar el `CMD` (esto no lo he probado).

## Probando la solución

Para ver que la solución funciona, solo necesitamos un servicio **mongodb**
ejecutando en un entorno **docker**. Podemos hacer un único servicio de *backup*
para todo el servicio de datos, pero soy de la opinión que esto es innecesario;
hay bases de datos que no necesitan *backup* y cada aplicación es reponsable
de los datos que quiera guardar. Voy a hacer un servicio por base de datos.

Para simplificar, voy a tener una única base de datos y un servicio de *backup*
para la misma, en un entorno *docker swarm* de un solo nodo. Si este *cluster*
creciera o se modificara, sería el encargado de recolocar los servicios de datos
y de *backup* necesarios, sin tener que modificar la URI de **mongo** o las
tareas **cron** de los servidores.

Esta podría ser una declaración posible de los servicios:

```bash
gerard@atlantis:~/Escritorio/mongobackup$ cat stack.yml 
version: '3'
services:
  mongo:
    image: sirrtea/mongo:debian
  backup:
    image: mongobackup
    volumes:
      - backups:/backup
    environment:
      DELAY: 10s
      INTERVAL: 1m
      MONGODB_URI: mongodb://mongo/shop
      FILENAME: /backup/shop_%Y%m%d_%H%M%S.archive.gz
volumes:
  backups:
gerard@atlantis:~/Escritorio/mongobackup$ 
```

Desplegamos el *stack* como solemos hacerlo:

```bash
gerard@atlantis:~/Escritorio/mongobackup$ docker stack deploy -c stack.yml database
Creating network database_default
Creating service database_mongo
Creating service database_backup
gerard@atlantis:~/Escritorio/mongobackup$ 
```

**WARNING**: En este punto, nos damos cuenta de que los *backups* se guardan
en un volumen; no es lo ideal y habría que moverlos fuera de la infraestructura
habitual a un servicio de acumulación de datos de forma segura y redundada.

Podemos ver que funciona mirando los *logs* del servicio o buscando el nodo
del *swarm* en el que se ejecuta, en donde habrá un volumen local (por definición
del *stack*). Como solo tenemos un nodo, este paso es trivial.

```bash
gerard@atlantis:~/Escritorio/mongobackup$ docker service logs database_backup
database_backup.1.mea109mwyoo2@atlantis    | 2020-01-10T11:43:43.449+0000	writing shop.fruits to archive '/backup/shop_20200110_114343.archive.gz'
database_backup.1.mea109mwyoo2@atlantis    | 2020-01-10T11:43:43.452+0000	done dumping shop.fruits (3 documents)
gerard@atlantis:~/Escritorio/mongobackup$ 
```

```bash
gerard@atlantis:~$ sudo tree -h /var/lib/docker/volumes/database_backups
/var/lib/docker/volumes/database_backups
└── [4.0K]  _data
    ├── [ 110]  shop_20200110_114143.archive.gz
    ├── [ 110]  shop_20200110_114243.archive.gz
    └── [ 371]  shop_20200110_114343.archive.gz

1 directory, 3 files
gerard@atlantis:~$ 
```

Podemos comprobar que han pasado tres intervalos de tiempo (definidos como 1 minuto),
y que el tercero ha incorporado algunos documentos (que he añadido a mano). Como
curiosidad, el comando `mongodump` no tiene salida en las dos primeras ejecuciones
(que es cuando la base de datos no existía todavía).

**WARNING**: Hacer un *backup* cada minuto puede matar el rendimiento de vuestro servidor;
como prueba de concepto nos sirve, pero **no hagáis esto** en un entorno real.

## Conclusión

A partir de aquí, ya tenemos *backups*; cambiar el *script* de *backup* o el mecanismo
de tareas recurrentes es una mejora que podemos hacer en un futuro. Lo importante
es que se ejecute el comando `mongodump` y que el resultado esté a buen recaudo.

[1]: {{< relref "/articles/2020/01/ejecutando-cron-en-un-contenedor-docker.md" >}}
[2]: {{< relref "/articles/2018/05/un-cron-alternativo-con-go-go-cron.md" >}}
[3]: https://docs.mongodb.com/manual/administration/install-on-linux/
[4]: https://hub.docker.com/_/mongo
