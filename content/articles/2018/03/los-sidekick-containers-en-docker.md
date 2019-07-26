---
title: "Los sidekick containers en Docker"
slug: "los-sidekick-containers-en-docker"
date: 2018-03-19
categories: ['Sistemas']
tags: ['docker', 'sidekick']
---

Algunas veces nos hemos encontrado que necesitamos ejecutar dos procesos o más para un servicio, aunque uno de ellos es el servicio principal y el otro se limita a ayudar al otro de alguna manera. Mejor que ponerlos en el mismo contenedor, podemos limitarnos a usar el patrón *sidekick containers*.<!--more-->

En vez de utilizar un gestor de procesos para levantar ambas funciones, lo que añade complejidad a la imagen global, podemos utilizar dos contenedores que se comuniquen mediante volúmenes.

En estos casos, debemos ver ambos contenedores como un *pack* indivisible, que deben ser desplegados en el mismo servidor, y se escalan a la vez. Para asegurar ese despliegue condicionado, cada orquestador tiene su método, como por ejemplo, los **pods** de **kubernetes**.

Llamaremos al contenedor inicial como *principal* y el resto, de apoyo, son los *sidekick* containers. Las funciones de estos últimos son muy variopintas; por nombrar algunas, podemos decir:

* Envío de logs a un servidor centralizado
* Hacer backups de la base de datos del contenedor principal
* Actualizar contenido para otro servicio de forma automática

Con un poco de imaginación se os ocurrirán muchas más.

## Un ejemplo: un servidor web con contenido en git

Tenemos un servidor web que sirve un contenido concreto. Tal como escalamos, necesitamos más copias del mismo y hay que sincronizarlo. Podríamos poner el contenido en la imagen, pero al cambiar este, habría que hacer un redespliegue masivo

Entonces podemos utilizar el patrón *sidekick* containers para hacer lo siguiente:

1. Un contenedor principal con el servidor web que elijamos, sirviendo desde un volumen.
2. Un contenedor *sidekick* que exporta el volumen del contenedor principal y lo va actualizando.

De esta forma, no importa cuantas replicas tengamos de este par, ni tampoco si cambia el contenido de la fuente; cada *sidekick* se dedicará mantener actualizado el contenido de su contenedor principal, por supesto sin intervención manual.

Hay muchas formas de sincronizar el contenido desde una fuente, pero por decisión de diseño, vamos a suponer que tenemos la fuente en un repositori **git**, que gestiona las copias incrementales y nos aligera la transferencia.

### El servidor web

Se trata de un servidor web normal y corriente, sirviendo un *document root* cualquiera. Para agilizar, voy a utilizar una imagen prefabricada de **nginx**, con una configuración para servir */srv/www/*.

```bash
gerard@atlantis:~/projects/sidekick$ cat web/Dockerfile
FROM sirrtea/nginx:alpine
COPY web.conf /etc/nginx/conf.d/
gerard@atlantis:~/projects/sidekick$ cat web/web.conf
server {
    server_name _;
    listen 80;
    root /srv/www;
    index index.html;
}
gerard@atlantis:~/projects/sidekick$
```

Vamos a construir la imagen con los comandos habituales, y le vamos a poner el *tag* **web**, para usar en el resto del artículo.

### El clonador de git

Básicamente se trata de un contenedor que ejecute periodicamente un `git pull`, o un `git clone` si la carpeta estaba vacía. Para poder reutilizar la imagen, voy a parametrizar el repositorio a usar, la carpeta en donde clonarlo y el tiempo de espera entre actualizaciones.

```bash
gerard@atlantis:~/projects/sidekick$ cat updater/Dockerfile
FROM alpine:3.7
RUN apk add --no-cache git
COPY run.sh /
CMD ["/run.sh"]
gerard@atlantis:~/projects/sidekick$ cat updater/run.sh
#!/bin/sh

cd ${DESTINATION}
while true; do
    if [ -e .git ]; then
        git pull
    else
        git clone ${REPOSITORY} .
    fi
    sleep ${DELAY}
done
gerard@atlantis:~/projects/sidekick$
```

Construiremos la imagen como siempre y vamos a ponerle el *tag* **updater**, para referencia del resto del artículo.

### Juntando los contenedores

La idea es que el contenedor tipo **web** sirva la carpeta */srv/www/*, que es un volumen. El contenedor tipo **updater** va a exportar el volumen, y va a actualizar la carpeta del mismo, para que las peticiones al contenedor **web** se encuentren con el contenido actalizado periodicamente.

Vamos a utilizar **docker-compose** para agilizar el levantamiento de ambos contenedores:

```bash
gerard@atlantis:~/projects/sidekick$ cat docker-compose.yml
version: '2'
services:
  web:
    image: web
    volumes:
      - /srv/www
    ports:
      - "8080:80"
  web_sidekick:
    image: updater
    environment:
      DESTINATION: /srv/www
      REPOSITORY: https://github.com/Sirtea/sidekick-example.git
      DELAY: 60
    volumes_from:
      - web
gerard@atlantis:~/projects/sidekick$
```

En este caso configuramos el contenedor **web_sidekick** para clonar el repositorio `sidekick-example.git`, en la carpeta `/srv/www` y actualizarlo cada minuto.

El truco reside en los volúmenes:

* **web** sirve la carpeta `/srv/www`, que es un volumen
* **web_sidekick** hace dos cosas:
	* Exporta los volúmenes de **web**, de forma que la carpeta `/srv/www` es la misma que sirve **web**
	* Actualiza el contenido de la carpeta `/srv/www` con lo que tengamos en el repositorio de **git**

Y de esta forma, el contenedor **web** sirve un contenido que va a ir cambiando tal como el desarrollador haga los correspondientes *commits* en el repositorio.

## Escalando el servicio

Si queremos poner más servidores web, la ecuación es simple: un contenedor *sidekick* por cada contenedor principal.

* Cada servidor web tiene un volumen
* Hace falta un contenedor *sidekick* para actualizar un volumen

Eso convierte el contenedor principal y el contenedor *sidekick* en un par indivisible, que actuan juntos en una relacion de simbiosis. En caso de que lo hagamos mal y no haya contenedor *sidekick* para algún contenedor web, su contenido no se actualizaría y obtendríamos un error 404 en las páginas de ese servidor.
