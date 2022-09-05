---
title: "Limpieza automática de datos sin usar en Docker"
slug: "limpieza-automatica-de-datos-sin-usar-en-docker"
date: "2022-09-05"
categories: ['Operaciones']
tags: ['docker', 'swarm', 'limpieza']
---

Es muy frecuente practicar el despliegue continuo en mis *clústeres* de **Docker Swarm**. Sin
embargo, esta práctica viene acompañada de un molesto pequeño problema: se me acaba el espacio en
disco por acumulación de objetos de **docker** (imágenes, contenedores parados, volúmenes, etc.).<!--more-->

Aunque ya conocía el comando `docker system prune`, ejecutarlo alegremente me daba cierto pavor;
algunos de los objetos podían ser necesarios a muy corto plazo. Esto cambió cuando descubrí que
el comando aceptaba un *flag* `--filter` que me permitía seleccionar los objetos que hacía tiempo
que no se utilizaban.

Como no podía ser de otra forma, añadí este nuevo conocimiento en una herramienta en mis *swarms*,
como un servicio auxiliar del mismo, ejecutando en un contenedor.

## La imagen de limpieza

Se trata de un contenedor que va a ejecutar periódicamente un el comando `docker system prune`,
con lo que vamos a necesitar los binarios de **docker** y acceso al *unix socket* que le
permitirá pasarle el comando de limpieza.

Vamos a encapsular el comando en un *script*, que nos permitirá acceder a las variables de
entorno de forma fácil y nos permitirá generar unos *logs* de ejecución que nos permitan
ver lo que está pasando.

Como el *script* va a ser un *shell script* estándar, no necesitamos ninguna imagen demasiado
recargada; en efecto, nos basta con la [imagen oficial de docker][1], a la que añadiremos el
*script*. En el momento de escritura de este artículo, esto se traduce en la imagen `docker:20.10`.

En cuanto al *script*, no tiene mucho misterio; se trata de lanzar el `docker system prune` cada
cierto tiempo, con una posible espera inicial adecuada (y puede que aleatoria). Esto nos deja
un *script* de este estilo:

```bash
gerard@sandbox:~/wiper$ cat run.sh
#!/bin/sh

SLEEP_TIME=${SLEEP_TIME:-3600}
UNUSED_TIME=${UNUSED_TIME:-24h}

prune () {
    echo "$(date +%FT%T) - Executing system prune..."
    docker system prune --all --force --filter "until=${UNUSED_TIME}"
}

sleep $((RANDOM % SLEEP_TIME))
while true; do
    prune
    sleep ${SLEEP_TIME}
done
gerard@sandbox:~/wiper$
```

**NOTA**: Estoy en contra de añadir el *flag* `--volumes`, puesto que los volúmenes con
nombre los creamos con mucho cariño y suelen contener información delicada. Prefiero gestionar
yo mismo su ciclo de vida, de forma manual.

Solo nos falta empaquetar el *script* en una imagen, mediante el uso de un fichero `Dockerfile`:

```bash
gerard@sandbox:~/wiper$ cat Dockerfile
FROM docker:20.10
COPY run.sh /
CMD ["/run.sh"]
gerard@sandbox:~/wiper$
```

## Desplegando la imagen en nuestro swarm

Suponiendo que tenemos la imagen disponible para todos los nodos del *swarm* (por ejemplo en
**DockerHub** o en un registro privado), el despliegue no tiene ninguna complicación. Lo que
hay que tener en cuenta es que:

1. El comando `docker` funciona escribiendo en el *unix socket* de la máquina que ejecuta **docker**, en la ruta `/var/run/docker.sock`. Podemos acceder al *unix socket* del servidor anfitrión montándolo como un volumen local.
2. La idea es que se ejecute un limpiador en cada nodo del *swarm*, ya que cada contenedor accede al *unix socket* de su anfitrión; así que la directiva `deploy.mode: global` nos viene de perlas.
3. Hemos escrito un *script* que se configura con variables de entorno. Aunque hay unos valores por defecto de tiempo de espera (`SLEEP_TIME` = 3600 segundos = 1 hora) y de antigüedad de los objetos (`UNUSED_TIME` = 24 horas), es interesante definir los valores a unos más adecuados según las políticas de despliegue de la empresa.

Llegados a este punto, suponiendo que ejecutamos cada día y que eliminamos los objetos
que lleven una semana sin usarse, tendríamos un *stack* bastante simple:

```bash
gerard@sandbox:~/tools$ cat stack.yml
version: '3'
services:
  wiper:
    image: wiper
    environment:
        SLEEP_TIME: 86400
        UNUSED_TIME: 168h
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    deploy:
      mode: global
gerard@sandbox:~/tools$
```

Lo acompañamos con un *script* de despliegue estándar, y listo:

```bash
gerard@sandbox:~/tools$ cat deploy.sh
#!/bin/bash

docker stack deploy -c stack.yml tools
gerard@sandbox:~/tools$
```

**CONCLUSIÓN**: Nunca más tuvimos problemas de espacio por acumulación innecesaria de elementos **docker** sin usar.

[1]: https://hub.docker.com/_/docker
