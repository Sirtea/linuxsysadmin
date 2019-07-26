---
title: "Problemas de log con docker y python"
slug: "problemas-de-log-con-docker-y-python"
date: 2017-05-01
categories: ['Operaciones']
tags: ['python', 'docker', 'buffering', 'logs', 'salida estándar']
---

El otro día estaba haciendo un *script* de **python** que debía ejecutarse en un contenedor **docker**. A pesar de la cantidad de *verbose* que le puse, no era capaz de ver ningún texto cuando miraba los *logs*. Tras mucha búsqueda, finalmente encontré el culpable en la variable de entorno **PYTHONUNBUFFERED**.<!--more-->

El *script* en sí mismo solo pretendía comprobar si habían eventos en una cola, para su posterior proceso. La sorpresa es que no podía ver nada cuando ejecutaba **docker** en modo *detached* o en **docker-compose**.

## El problema

Para reducir mucho el problema, se plantea un *script* llamado *poll.sh* que emita un mensaje en la salida estándar cada segundo, como sigue:

```python
#!/usr/bin/env python

from datetime import datetime
import time

while True:
    print datetime.utcnow().strftime('%H:%M:%S')
    time.sleep(1)
```

Podemos comprobar que hace lo que se le supone. Sin embargo, el problema aparece al crear una imagen para su ejecución con **docker**. Vamos a usar una imagen base de *DockerHub* para mantener la dimensión del problema bajo control.

```bash
gerard@aldebaran:~/docker/poller$ cat Dockerfile 
FROM python:2-slim
COPY poll.py /
CMD ["python", "poll.py"]
gerard@aldebaran:~/docker/poller$ 
```

Tras construir la imagen, vemos que no hay salida durante su ejecución:

```bash
gerard@aldebaran:~/docker/poller$ docker run --name poller -d poller
314d32b425d1d222527678fc15c73147162d62195c56422fc90729e9b4f6594b
gerard@aldebaran:~/docker/poller$ sleep 10
gerard@aldebaran:~/docker/poller$ docker logs poller
gerard@aldebaran:~/docker/poller$ 
```

Tras 10 segundos de espera, el *script* debería haber escrito unas 10 veces en la salida, y sin embargo no muestra nada.

## La causa

Tras mucho esperar, me di cuenta de un factor interesante: tras varios minutos, se añadían muchas líneas en la salida, con sus *timestamps* diferenciados entre sí por un segundo, más o menos.

el primer pensamiento que viene en mi cabeza ante este comportamiento, es *buffering*; no se trata de que la salida no sale, sino que sale en paquetes grandes, que se han ido acumulando en un *buffer* para optimizar las escrituras a los dispositivos permanentes.

Como esto no es aceptable para mi aplicación, intenté buscar en **python** una respuesta satisfactoria, encontrándola en [la documentación](https://docs.python.org/2/using/cmdline.html#cmdoption-u).

Parece ser que **python** acepta una opción *-u* en la línea de comandos, o una variable de entorno **PYTHONUNBUFFERED** que elimina el comportamiento *buffereado* de la salida estándar.

## La solución

Sabiendo la causa del problema, la solución es todavía más simple: solo se trata de desactivar este comportamiento.

Esto se consigue con alguna de las dos opciones siguientes:

* Podemos invocar el intérprete con el *flag -u*
* Podemos hacer que el intérprete se ejecute en un entorno que defina la variable **PYTHONUNBUFFERED**

Así pues, y tras modificar un poco nuestro *Dockerfile*, el problema deja de existir.

```bash
gerard@aldebaran:~/docker/poller$ cat Dockerfile 
FROM python:2-slim
COPY poll.py /
CMD ["python", "-u", "poll.py"]
gerard@aldebaran:~/docker/poller$ 
```

Y de esta forma podemos repetir el *test* inicial, para demostrar que ya no nos ocurre de nuevo.

```bash
gerard@aldebaran:~/docker/poller$ docker run --name poller -d poller
bb3bdaaf5ef92e2f38a70b30163abd335920aa940eb1327716eac3fa656ad651
gerard@aldebaran:~/docker/poller$ sleep 10
gerard@aldebaran:~/docker/poller$ docker logs poller
13:24:08
13:24:09
13:24:10
13:24:11
13:24:12
13:24:13
13:24:14
13:24:15
13:24:16
13:24:17
13:24:18
13:24:19
13:24:20
13:24:21
13:24:22
gerard@aldebaran:~/docker/poller$ 
```

De hecho, el comportamiento es más evidente si vemos los *logs* en modo *follow*, o lo que es lo mismo, usando el *flag -f*. Con él podemos ver como salta una traza cada segundo, de forma puntual y sin retardos.
