Title: Verificando la salud de nuestros contenedores en Docker
Slug: verificando-la-salud-de-nuestros-contenedores-en-docker
Date: 2019-06-03 14:00
Category: Operaciones
Tags: docker, healthcheck, swarm



Como bien sabemos los que trabajamos con **Docker**, el servidor es bastante malo comprobando si un contenedor está funcionando o no. El *check* que hace **Docker** solo se molesta en ver si el proceso invocado está ejecutando o no, aunque no esté respondiendo. Esto ha cambiado recientemente con los *healthchecks*

Y es que a partir de Docker 1.12, existe un nuevo concepto en **Docker** que nos permite indicar **como se comprueba la salud de un contenedor**. Para hacerlo, solo necesitamos declarar **como se verifica si el contenedor está saludable o no**, y es tan simple como un comando, que puede devolver:

* 0 &rarr; Significa que el contenedor funcionaría bien y el servicio está correcto.
* 1 &rarr; Este código de retorno significaría que el contenedor no está dando el servicio esperado.

La naturaleza de este comando es variada: puede tratarse de un comando estándar del contenedor, un *script* propio o lo que nos apetezca; el único punto a tener en cuenta es que se ejecuta **dentro del contenedor**, y por lo tanto, va a necesitar tener las herramientas necesarias para ejecutarlo.

Este *healthcheck* puede especificarse en el `Dockerfile` y en el `docker run` o `docker-compose.yml`. En caso de tener varios en el `Dockerfile`, solo queda activo el último declarado. Si se especifica uno en *runtime*, este tiene preferencia sobre el que declare la imagen; esto puede servir para sobreescribirlo o deshabilitarlo.

## Un ejemplo

Supongamos que queremos utilizar en contenedor `sirrtea/mongo:alpine` y queremos definir la salud del mismo con un *healthcheck* que asegure que el puerto 27017 está abierto.

Esto se haría comprobando esta condición con cualquier herramienta que viniera con la imagen, o podemos poner un *script* o binario propio. Hay que asegurarse que el *healthcheck* devuelve 0 o 1, así que si no devuelve 0, vamos a forzar el 1 con un "OR" de **bash**.

```bash
gerard@atlantis:~/workspace/mongo_healthcheck$ cat Dockerfile 
FROM sirrtea/mongo:alpine
HEALTHCHECK --interval=5s --timeout=3s --start-period=30s --retries=2 CMD nc -nz localhost 27017 || exit 1
gerard@atlantis:~/workspace/mongo_healthcheck$ 
```

El comando no necesita grandes explicaciones, excepto por los parámetros:

* `--interval` &rarr; El intervalo con el que se ejecutan los *checks* (por defecto 30s).
* `--timeout` &rarr; El tiempo desde que se lanza un *check* hasta que se considera un fallo (por defecto 30s).
* `--start-period` &rarr; Todo *check* que falle en este primer intervalo no se contabiliza  (por defecto 0s).
* `--retries` &rarr; El número de *checks* consecutivos que deben fallar para dar la salud del contenedor por mala  (por defecto 3).

Aplicado a nuestro caso, lo que pasaría es lo siguiente:

* El contenedor empieza en el estado `health: starting`.
* Se hace un *check* cada 5 segundos, dándolo por malo a los 3 segundos si no hay respuesta.
    * Si el *check* falló en los 30 primeros segundos, no cuenta y seguimos en `health: starting`.
    * Si el *check* es correcto, el estado pasa a `healthy` (aunque sea dentro de los 30 primeros segundos).
    * Si el *check* falla pasados los 30 primeros segundos o tras un `healthy`, y lo hace tres veces seguidas (un fallo y dos reintentos), el estado se vuelve `unhealthy`.

En nuestro caso, si hacemos un `docker ps` veremos que pasamos de `health: starting` a `healthy`, en menos de 30 segundos:

```bash
gerard@atlantis:~/workspace/mongo_healthcheck$ docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS                            PORTS               NAMES
8d1ee9518d0b        healthymongo        "/usr/bin/mongod --c…"   5 seconds ago       Up 3 seconds (health: starting)                       hungry_blackwell
gerard@atlantis:~/workspace/mongo_healthcheck$ 
```

```bash
gerard@atlantis:~/workspace/mongo_healthcheck$ docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS                    PORTS               NAMES
8d1ee9518d0b        healthymongo        "/usr/bin/mongod --c…"   27 seconds ago      Up 25 seconds (healthy)                       hungry_blackwell
gerard@atlantis:~/workspace/mongo_healthcheck$ 
```

Vamos a suponer que el servicio se presta en el puerto 27018 (que no tenemos escuchando, con lo que fallaríamos), pero esta vez vamos a sobreescribir el *healthcheck* en el `docker run`.

```bash
gerard@atlantis:~/workspace/mongo_healthcheck$ docker run --rm -d \
>   --health-cmd='nc -nz localhost 27018 || exit 1' \
>   --health-interval=5s \
>   --health-timeout=3s \
>   --health-start-period=30s \
>   --health-retries=2 \
>   healthymongo
c99d20739079e7f36c517a643d8cf853aa1b9474713446632864eda6f7a61fec
gerard@atlantis:~/workspace/mongo_healthcheck$ 
```

Solo hay que ir mirando el `docker ps` para ver como deja pasar 30 segundos en `health: starting` a `unhealthy`:

```bash
gerard@atlantis:~/workspace/mongo_healthcheck$ docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS                            PORTS               NAMES
c99d20739079        healthymongo        "/usr/bin/mongod --c…"   6 seconds ago       Up 5 seconds (health: starting)                       nervous_feistel
gerard@atlantis:~/workspace/mongo_healthcheck$ docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS                             PORTS               NAMES
c99d20739079        healthymongo        "/usr/bin/mongod --c…"   35 seconds ago      Up 33 seconds (health: starting)                       nervous_feistel
gerard@atlantis:~/workspace/mongo_healthcheck$ docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS                      PORTS               NAMES
c99d20739079        healthymongo        "/usr/bin/mongod --c…"   39 seconds ago      Up 38 seconds (unhealthy)                       nervous_feistel
gerard@atlantis:~/workspace/mongo_healthcheck$ 
```

Y si queremos saber porqué no esta saludable, podemos inspeccionar el contenedor (aunque en mi caso el comando no da salida, y por lo tanto, no hay diagnóstico):

```bash
gerard@atlantis:~/workspace/mongo_healthcheck$ docker inspect c99d20739079
...
            "Health": {
                "Status": "unhealthy",
                "FailingStreak": 42,
                "Log": [
                    {
                        "Start": "2019-05-27T13:49:52.432389569+02:00",
                        "End": "2019-05-27T13:49:52.548464716+02:00",
                        "ExitCode": 1,
                        "Output": ""
                    },
                    {
                        "Start": "2019-05-27T13:49:57.618824851+02:00",
                        "End": "2019-05-27T13:49:57.765852351+02:00",
                        "ExitCode": 1,
                        "Output": ""
                    },
...
gerard@atlantis:~/workspace/mongo_healthcheck$ 
```

## Utilidad de los healthchecks

El estado de los contenedores es una información que **Docker** "conoce", pero no hace nada con ella. Esto cambia con los orquestadores, como por ejemplo **Docker Swarm**. Este último tiene esta salud en cuenta para dos cosas:

* Reiniciar (y posiblemente recolocar) los contenedores *unhealthy* para asegurar que se da servicio con el número de contenedores especificado.
* Para hacer *rolling updates*, esperando a que los contenedores estén saludables antes de quitar los anteriores, resultando en despliegues sin *downtime*.

Aparte de su uso en *cluster*, podemos utilizar esta propiedad para que contenedores dependientes no empiecen antes de tener sus requisitos listos, como por ejemplo, su base de datos. Algo así como el siguiente `docker-compose.yml`:

```bash
version: "3"
services:
  database:
...
  api:
    depends_on:
      database:
        condition: service_healthy
...
```

Aunque es una opción posible, opino que es más fácil que el servicio de API conecte a la base de datos en su primera petición...
