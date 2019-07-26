---
title: "Problemas de escritura con openshift"
slug: "problemas-de-escritura-con-openshift"
date: 2017-08-21
categories: ['Sistemas']
tags: ['docker', 'openshift', 'permisos']
---

En mi trabajo se ha decidido por el uso de virtualización por contenedores usando **Openshift**. No es nada demasiado nuevo, puesto que ya usábamos **Docker** de manera habitual, pero ha habido alguna *feature* que nos ha hecho plantearnos el modo en el que hacemos las cosas, especialmente para las escrituras.<!--more-->

Todo viene por una directiva de seguridad que prohibe estrictamente ejecutar un contenedor como *root*, y de la misma manera, ejecuta el contenedor con un usuario aleatorio para incrementar la seguridad general.

El problema viene para el pobre hombre que se dedica a generar imágenes, ya que la falta de determinismo, te asegura casi al 100% que no vas a poder escribir en las carpetas del contenedor, a menos que sepas lo que estás haciendo.

Sin embargo, saber lo que hace **Openshift** no es tarea complicada:

* Se te asegura que nunca vas a usar el *uid* 0, sino uno aleatorio
* El grupo del usuario de ejecución se mantiene siempre como *root*

Un problema derivado de esto es que no podemos ejecutar nada que requiera *root*, como por ejemplo SSH (que no podríamos exponer en **Openshift** de todas formas). Otro problema es que no tendremos permisos para crear carpetas en *runtime* o incluso para cambiar el usuario de ejecución.

## Simulando el comportamiento de Openshift

Vamos a poner un ejemplo tipo para entender lo que pasa:

```bash
gerard@atlantis:~/projects/openshift_simulator$ cat Dockerfile
FROM python:2-slim
COPY server.py /
CMD ["/server.py"]
gerard@atlantis:~/projects/openshift_simulator$ cat server.py
#!/usr/bin/env python

from wsgiref.simple_server import make_server, demo_app

server = make_server('0.0.0.0', 8080, demo_app)
server.serve_forever()
gerard@atlantis:~/projects/openshift_simulator$

Y lo construimos:

```bash
gerard@atlantis:~/projects/openshift_simulator$ docker build -t openshift_simulator .
Sending build context to Docker daemon  3.072kB
...
Successfully tagged openshift_simulator:latest
gerard@atlantis:~/projects/openshift_simulator$
```

Normalmente lo ejecutaríamos de la siguiente manera:

```
gerard@atlantis:~/projects/openshift_simulator$ docker run -ti --rm -p 8888:8080 --name test1 openshift_simulator
...
```

Podemos comprobar que los procesos, tanto nuevos como antiguos, corren con el usuario *root*.

```bash
gerard@atlantis:~$ docker exec test1 id
uid=0(root) gid=0(root) groups=0(root)
gerard@atlantis:~$ docker exec test1 ps -efa
UID        PID  PPID  C STIME TTY          TIME CMD
root         1     0  0 14:18 pts/0    00:00:00 python /server.py
root        17     0  0 14:20 ?        00:00:00 ps -efa
gerard@atlantis:~$
```

Sin embargo, en **openshift** el usuario se elige de forma aleatoria, y se impone con el *flag* de usuario *-u*, como sigue:

```bash
gerard@atlantis:~/projects/openshift_simulator$ docker run -ti --rm -p 8888:8080 --name test2 -u 123456 openshift_simulator
...
```

Y podemos ver que los procesos amparados por este contenedor se ejecutarían con el *uid* especificado.

```bash
gerard@atlantis:~$ docker exec test2 id
uid=123456 gid=0(root) groups=0(root)
gerard@atlantis:~$ docker exec test2 ps -efa
UID        PID  PPID  C STIME TTY          TIME CMD
123456       1     0  0 14:22 pts/0    00:00:00 python /server.py
123456       9     0  0 14:22 ?        00:00:00 ps -efa
gerard@atlantis:~$
```

## Implicaciones en escritura

Como no sabemos el usuario con el que vamos a ejecutar, es especialmente interesante saber donde vamos a escribir, ya que los permisos de lectura suelen ser suficientes para todo el mundo. Sin embargo, las carpetas de escritura suelen estar más restringidas.

En este caso, estas carpetas tienen dos posibles salidas:

* Les damos barra libre con permisos 777, que no van a gustar a ningún miembro del equipo de seguridad
* Afinamos los permisos aprovechándonos de que nunca vamos a ser *root*, pero vamos a ejecutar con su grupo

De esta forma, podemos ver la propiedad y los permisos de forma individual:

* **Usuario**: con pertenencia a *root* nos aseguramos de que los permisos no aplican nunca, con lo que podemos ponerlos como queramos.
* **Grupo**: Esta es la mejor forma de asegurar que la carpeta nos pertenece. Aquí si que tenemos que dar permisos de escritura.
* **Otros**: Nunca hay que dar permisos de escritura a este grupo; ningún auditor de seguridad lo va a permitir.

De esta forma, la pertenencia habuitual para carpetas de lectura y escritura que suelo poner es `root:root`, y los permisos acostumbran a ser 575, aunque no me libro de explicaciones cuando pido las excepciones de seguridad pertinentes.
