---
title: "Ejecutando cron en un contenedor Docker"
slug: "ejecutando-cron-en-un-contenedor-docker"
date: "2020-01-21"
categories: ['Sistemas']
tags: ['docker', 'cron']
---

A veces nos conviene ejecutar tareas de forma periodica en nuestro servidor,
y para ello disponemos de **cron** y de **anacron**. Sin embargo, en un entorno
clusterizado de **Docker** no es fácil decidir en qué máquina lo ponemos o
simplemente necesitamos que pueda acceder a alguna red *overlay*.
<!--more-->

En estos casos es necesario que el servicio **cron** ejecute en un contenedor
dentro de nuestra infraestructura **Docker** y para ello se necesitan algunas
modificaciones en el servicio, ya que la forma en la que está hecho **cron**
no permite el uso correcto en un contenedor de forma correcta.

* La salida de nuestros comandos no se ve en un `docker logs`
* Las variables de entorno no aparecen en los *jobs* de nuestro **cron**

Afortunadamente, ambas tienen solución, pero hay que entender qué es lo que
pasa, y porqué **cron** y **Docker** no colaboran todo lo bien que se desearía.

## Estado inicial

Creamos una imagen de **docker** con el único entendido que debe ejecutar
**cron** en *foreground* (para que el contenedor no acabe inmediatamente), y
le suministramos el fichero `crontab` con un comando cualquiera.

```bash
gerard@atlantis:~/dockercron$ cat Dockerfile 
FROM debian:buster-slim
RUN apt update && apt install -y --no-install-recommends cron && rm -rf /var/lib/apt/lists/*
CMD ["/usr/sbin/cron", "-f"]
COPY job.sh /
COPY crontab /etc/
gerard@atlantis:~/dockercron$ 
```

```bash
gerard@atlantis:~/dockercron$ cat crontab 
* * * * * root /job.sh
gerard@atlantis:~/dockercron$ 
```

```bash
gerard@atlantis:~/dockercron$ cat job.sh 
#!/bin/bash

echo "Hello ${NAME}"!
echo "." >> /tmp/job.log
gerard@atlantis:~/dockercron$ chmod 755 job.sh 
gerard@atlantis:~/dockercron$ 
```

Solo nos queda construir la imagen, de la manera habitual:

```bash
gerard@atlantis:~/dockercron$ docker build -t dockercron .
...
gerard@atlantis:~/dockercron$ 
```

Y ejecutamos nuestro contenedor:

```bash
gerard@atlantis:~/dockercron$ docker run --rm -e NAME=gerard --name myjob dockercron
...
```

Se supone que esto ejecuta cada minuto, pero no vemos salida estándar. Podemos
comprobar que se está ejecutando nuestro *script* si miramos el número de líneas
del fichero de *log*, que con el tiempo debería incrementar:

```bash
gerard@atlantis:~$ docker exec myjob wc -l /tmp/job.log
1 /tmp/job.log
gerard@atlantis:~$ docker exec myjob wc -l /tmp/job.log
2 /tmp/job.log
gerard@atlantis:~$ 
```

## Recogiendo la salida de nuestros *jobs*

**IMPORTANTE**: La salida que vemos en `docker logs` y en el `docker run`,
**es la salida del proceso con PID 1**, y no veremos ninguna otra salida.

En este caso, **cron** ejecuta como proceso con PID 1, y cada vez que ejecuta
un *job* crea un subproceso (digamos que tiene PID 2). Este ejecuta nuestro
comando (digamos PID 3). La salida estándar del proceso con PID 3 se corresponde
con la del proceso con PID 2, y es por esto que podemos recogerla en el *crontab*.

Esta salida podemos escribirla en `/dev/null` o en un fichero, según nuestras
necesidades, pero **jamás llegará a la salida del PID 1**. Eso es algo que
tenemos que hacer nosotros explícitamente.

Para ello necesitamos saber algunas cosas referentes a los *file descriptors*:

* Los *file descriptors* de un proceso con PID 123 estan en `/proc/123/fd/`
    * El *file descriptor* 0 es la entrada estándar
    * El *file descriptor* 1 es la salida estándar
    * El *file descriptor* 2 es la salida de error
* El proceso en ejecución (por ejemplo 123) se puede encontrar en `/proc/self` (es un *soft link* a `/proc/123`)
* Los dispositivos `/dev/std*` son *soft links* a `/proc/self/fd/`
    * `/dev/stdin` es un *soft link* a `/proc/self/fd/0`
    * `/dev/stdout` es un *soft link* a `/proc/self/fd/1`
    * `/dev/stderr` es un *soft link* a `/proc/self/fd/2`

Sabiendo esto, vemos que el *cron job* del ejemplo estaría escribiendo su salida
en `/dev/stdout`, que siguiendo la cadena de *links* sería `/proc/self/fd/1` que
finalmente sería `/proc/2/fd/1`. Si quisiéramos escribir en la salida del proceso
con PID 1, deberíamos escribir en `/proc/1/fd/1`.

En el único sitio que podemos hacer esto en el proceso con PID 2 (que es el que
puede escribir la salida y sabemos seguro que ejecuta como **root**; nuestro
*script* podría ejecutar con otro usuario). Llegados a este punto, solo tenemos
que modificar nuestro fichero `/etc/crontab`:

```bash
gerard@atlantis:~/dockercron$ cat crontab 
* * * * * root /job.sh >/proc/1/fd/1 2>/proc/1/fd/2
gerard@atlantis:~/dockercron$ 
```

Reconstruimos la imagen y ejecutamos de nuevo:

```bash
gerard@atlantis:~/dockercron$ docker run --rm -e NAME=gerard --name myjob dockercron
Hello !
Hello !
...
```

## Accediendo a las variables de entorno

La salida anterior nos muestra que la variable de entorno NAME no llega al *script*.
Esto es porque **cron** crea un entorno de ejecución vacío de dichas variables y
no traspasa las que pusimos en el contenedor.

Esto no tiene solución; la única opción que nos queda es la de hacer un `source`
de un fichero con las variables de entorno que nos convengan. Este fichero se puede
generar en un *script* inicial que acabe invocando a **cron**, pero por simplicidad
voy a ponerlo a mano, solamente para exponer la solución.

```bash
gerard@atlantis:~/dockercron$ cat envvars 
export NAME=gerard
gerard@atlantis:~/dockercron$ 
```

Por supuesto, hay que copiarlo en la imagen (o usar secretos y configuraciones),
y hay que indicar al *cron job* que se haga el `source` antes de lanzar nuestro
*script*, para que éste pueda encontrar las variables adecuadamente rellenadas.

```bash
gerard@atlantis:~/dockercron$ cat Dockerfile 
FROM debian:buster-slim
RUN apt update && apt install -y --no-install-recommends cron && rm -rf /var/lib/apt/lists/*
CMD ["/usr/sbin/cron", "-f"]
COPY job.sh /
COPY crontab /etc/
COPY envvars /
gerard@atlantis:~/dockercron$ 
```

```bash
gerard@atlantis:~/dockercron$ cat crontab 
* * * * * root . /envvars; /job.sh >/proc/1/fd/1 2>/proc/1/fd/2
gerard@atlantis:~/dockercron$ 
```

**TRUCO**: El comando `source` no parece funcionar en el *cron job*. Le he
reemplazado por el comando `.` que funciona y, que en teoría, hace lo mismo.

Y tras hacer el correspondiente *build*, todo debería funcionar según lo esperado:

```bash
gerard@atlantis:~/dockercron$ docker run --rm --name myjob dockercron
Hello gerard!
Hello gerard!
...
```

Para una versión automatizada podéis mirar en [GitHub][1] y su correspondiente
en [DockerHub][2], lo que nos simplificaría el caso anterior a lo siguiente:

```bash
gerard@atlantis:~/dockercron$ cat env.list 
CRON_INTERVAL=* * * * *
CRON_USER=root
CRON_COMMAND=echo Hello ${NAME}
CRONENV_NAME=gerard
gerard@atlantis:~/dockercron$ docker run --rm --env-file env.list sirrtea/cron:debian
Hello gerard
Hello gerard
...
```

Y gracias a estos trucos ya podemos crear contenedores para lanzar nuestras
tareas automatizadas y periodicas; por ejemplo podríamos utilizarlo para lanzar
un *backup* a un servidor o *cluster* de base de datos que solo fuera accesible
desde una red *overlay*, beneficiándonos del nombre del servicio DNS.

[1]: https://github.com/Sirtea/dockerfiles/tree/master/cron/debian
[2]: https://hub.docker.com/repository/docker/sirrtea/cron
