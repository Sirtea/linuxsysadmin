---
title: "Los beneficios de los healthchecks en Docker"
slug: "los-beneficios-de-los-healthchecks-en-docker"
date: "2021-03-04"
categories: ['Operaciones']
tags: ['docker', 'healthcheck', 'swarm']
---

Ya hemos hablado de los *healthchecks* de **Docker** en [otras ocasiones][1]. Sin
embargo, aprecio en muchos de los servicios que administro que brillan por su ausencia;
es algo que no puedo entender, por la multitud de beneficios que nos aporta desde un
punto de vista de operaciones en los despliegues.<!--more-->

Y es que no me canso de predicar sus virtudes, ya que nos permite saber:

* Que el puerto de escucha está abierto.
* Que el servidor de aplicaciones está levantado.
* Que la aplicación está inicializada, y su estado
  * La aplicación responde bien
  * La aplicación responde mal
  * La aplicación no responde

Es especialmente útil en el caso de un *cluster* de **Docker Swarm**, que nos permite
hacer una actualización del servicio sin cortes, evitando ocasiones en las que se levanta
un contenedor y se da por bueno antes de que realmente esté funcionando adecuadamente;
esto es especialmente cierto para algunos servidores de aplicaciones que levantan rápido,
pero luego tardan bastante en tener la aplicación inicializada.

Con un poco de lógica adicional, podemos tener un *healthcheck* más complejo que nos
indique si el servidor se ha quedado sin responder, si falta alguna configuración para
el correcto funcionamiento de nuestra aplicación, o si algún elemento necesario no
estuviera disponible (base de datos, API de terceros, ...).

Otro punto conflictivo es la forma de consultar esos *healthchecks*; hacerlo mirando a un
*endpoint* concreto nos indica que la aplicación está respondiendo, pero se requiere un
cliente HTTP para hacer la consulta correspondiente (y eso no siempre está en la imagen).

Muchos autores en la red abogan por prescindir de herramientas externas (tipo `wget` o `curl`)
porque no siempre están disponibles y reducen la portabilidad de la imagen a otras imágenes base.
Por ejemplo, en `python:3-alpine` disponemos de `wget` (de **Alpine Linux**), mientras que
en `python:3-slim` (es una **Debian** con **Python**) no disponemos de ella y habría que añadirla.

**TRUCO**: Es mucho más fácil añadir un cliente HTTP escrito en el mismo intérprete que
nuestra aplicación. Se suele necesitar algún fichero adicional, pero obtenemos exactamente lo
que necesitamos, con el mismo *runtime* que el resto del código.

## Una aplicación con healthcheck

Supongamos que tenemos una API escrita en **Python**, utilizando el *framework* **Falcon**.
También hemos tomado la decisión que el *healthcheck* va a devolver un estado HTTP 200 en el
caso que todo vaya bien, y en el caso de que vaya mal, cualquier otro estado (por ejemplo un 503).

Simplemente se trata de un nuevo *endpoint* que responderá en `/status` y se limitará a
realizar algunos *checks* para decidir si el servicio funciona o no. El *healthcheck* deberá
ser interpretado como correcto si este *endpoint* devuelve un estado 200, y como falso (tanto
si responde con un estado 503 como si no responde en absoluto).

**NOTA**: La aplicación no hace nada más por ahora; no es relevante y solo añade complejidad
innecesaria al artículo.

```bash
gerard@atlantis:~/projects/healthcheck_python_demo$ cat app.py 
import falcon
import time


class StatusResource():
    def arbitrary_check(self):
        return int(time.time()) % 10 != 0

    def on_get(self, req, resp):
        if req.remote_addr != '127.0.0.1':
            raise falcon.HTTPNotFound()
        if not self.arbitrary_check():
            resp.body = 'FAIL - Arbitrary check failed'
            resp.status = falcon.HTTP_SERVICE_UNAVAILABLE
        else:
            resp.body = 'OK - Everything is OK'


api = falcon.API()
api.add_route('/status', StatusResource())
gerard@atlantis:~/projects/healthcheck_python_demo$ 
```

```bash
gerard@atlantis:~/projects/healthcheck_python_demo$ cat requirements.txt 
falcon==2.0.0
gunicorn==20.0.4
gerard@atlantis:~/projects/healthcheck_python_demo$ 
```

Este ejemplo ejecuta un *check* que falla 1 segundo de cada 10, para comprobar
que el *healthcheck* realmente falla cuando debe fallar. Además, hemos puesto
algo de código para limitar el acceso al *endpoint* solamente desde dentro del
contenedor (los *healthchecks* se ejecutan **dentro del contenedor**).

## El cliente HTTP para consultar el healthcheck

Ya hemos dicho que no queremos trabajar con herramientas del sistema operativo;
esto nos ahorra el tener que instalar paquetes adicionales y nos evita problemas
derivados de distintas implementaciones de la herramienta o de las librerías
de las que estas dependen.

Así pues, creamos un *script* en el mismo lenguaje que utiliza la aplicación,
que en este caso es **Python** y ya nos ofrece lo que necesitamos para el mismo.

```bash
gerard@atlantis:~/projects/healthcheck_python_demo$ cat health.py 
#!/usr/bin/env python

import http.client
import sys

try:
    c = http.client.HTTPConnection('localhost', 8080, timeout=5)
    c.request('GET', '/status')
    r = c.getresponse()
    assert r.status == 200
except AssertionError as e:
    print(r.read().decode('utf-8'))
    sys.exit(1)
except Exception:
    print('FAIL - Connection error')
    sys.exit(1)

print(r.read().decode('utf-8'))
sys.exit(0)
gerard@atlantis:~/projects/healthcheck_python_demo$ 
```

Básicamente se trata de hacer una petición al *endpoint* `/status` y verificar que
devuelve un estado 200; este es el caso "bueno" y requiere que devolvamos un código
de retorno "0" en el *script*, para que **Docker** pueda interpretar el *check* como
correcto. Otras salidas esperadas son otro código de estado HTTP (la aplicación responde
pero algo no va bien) o un *timeout* (la aplicación o el servidor no están listos).

## Empaquetando la imagen para su uso en Docker

Para empaquetar la imagen para **Docker** escribimos un fichero *Dockerfile*. No es
complicado, pero hay que tener en cuenta dos cosas nuevas: copiar el *script* de
*healthcheck* y declarar el *healthcheck* (o ponerlo en el fichero tipo *compose*
más adelante). Optamos por la segunda.

```bash
gerard@atlantis:~/projects/healthcheck_python_demo$ cat Dockerfile 
FROM python:3.8-slim
COPY requirements.txt app.py health.py /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--chdir=/app", "app:api"]
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s CMD /app/health.py
gerard@atlantis:~/projects/healthcheck_python_demo$ 
```

Solo falta por construir la imagen con los comandos habituales:

```bash
gerard@atlantis:~/projects/healthcheck_python_demo$ docker build -t healthdemo .
...
Successfully tagged healthdemo:latest
gerard@atlantis:~/projects/healthcheck_python_demo$ 
```

## Verificando el funcionamiento

Para verificar que funciona, solo necesitamos ejecutar un contenedor basado en
la imagen recién creada; podemos encontrar la salida de los *healthchecks* si
inspeccionamos el contenedor *a posteriori*.

```bash
gerard@atlantis:~$ docker run --name healthdemo --rm healthdemo
...
```

```bash
gerard@atlantis:~$ docker inspect healthdemo
...
        "State": {
...
            "Health": {
                "Status": "healthy",
                "FailingStreak": 0,
                "Log": [
                    {
...
                        "ExitCode": 0,
                        "Output": "OK - Everything is OK\n"
                    },
                    {
...
                        "ExitCode": 1,
                        "Output": "FAIL - Arbitrary check failed\n"
                    },
...
gerard@atlantis:~$ 
```

De acuerdo con la especificación del *healthcheck* en el fichero `Dockerfile`, se dará
por malo un contenedor que falle el *healthcheck* 3 veces seguidas (valor por defecto),
ejecutándose cada 5 segundos, teniendo en cuenta que los fallos no cuentan durante los
10 primeros segundos.

En el caso de tratarse de un servicio dentro de un **Docker Swarm**, el *healthcheck*
cumple con dos grandes casos de uso:

1. Desplegar un contenedor en sustitución de una que empiece a fallar por algún motivo en concreto.
2. En caso de un *update*, no bastará con ejecutar el servidor de aplicaciones;
habrá que esperar a que la aplicación responda correctamente antes de actualizar
el siguiente contenedor del servicio, eliminando el *downtime* de la actualización.

Ahora ya no deberá preocuparnos que la aplicación tarde minutos en levantar; **Docker**
no seguirá parando contenedores hasta que se estabilice el que está actualizando, momento
en el que continuará con el *update* (parando y recreando otro contenedor).

[1]: {{< relref "/articles/2019/06/verificando-la-salud-de-nuestros-contenedores-en-docker.md" >}}
