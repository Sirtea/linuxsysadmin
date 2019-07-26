---
title: "Un contenedor multiservicio con docker y s6"
slug: "un-contenedor-multiservicio-con-docker-y-s6"
date: 2018-09-24
categories: ['Sistemas']
tags: ['docker', 's6', 'nginx', 'ssh']
---

Lo he vuelto a hacer: a pesar de que es una antipráctica de **docker**, me veo tentado a ejecutar varios servicios en mis contenedores. Solo lo hago cuando estos servicios tienen un objetivo común, como servir PHP (nginx/php-fpm); para ello necesitamos un gestor de procesos. Hoy hablaremos de **s6**.<!--more-->

Hasta ahora, el servicio que utilizaba era [runit]({{< relref "/articles/2017/03/multiples-servicios-en-un-mismo-contenedor-docker.md" >}}), pero existe un servicio similar llamado **s6** que además sirve como [*init* correcto]({{< relref "/articles/2017/09/un-proceso-inicial-para-docker-tini-y-dumb-init.md" >}}) para **docker**. Por supuesto, no he podido resistir la tentación de darle un intento, y el resultado me ha gustado.

## Funcionamiento de s6

Cuando ejecutamos **s6**, ejecutamos el binario `s6-svscan` que monitoriza una carpeta concreta. En esta carpeta tenemos una subcarpeta por servicio; cada subcarpeta es la definición de un servicio y `s6-svscan` va a lanzar sobre la misma el proceso `s6-supervise`, que se encarga de mantener ese proceso concreto.

Esta subcarpeta tiene 3 tipos de ficheros y carpetas:

* Obligatoriamente un binario, enlace o *script* llamado `run`, que es lo que se ejecutará para levantar el servicio
* Opcionalmente un binario, enlace o *script* llamado `finish`, que se llamará cuando el servicio acabe por cualquier motivo
* Carpetas `event` y `status` que son efímeras y las usa **s6** para mantener el estado del proceso

Adicionalmente, la carpeta de servicios tiene un "servicio" especial: `.s6-svscan` que dispone de dos binarios, enalces o *scripts*:

* `finish` &rarr; se va a ejecutar cuando `s6-svscan` acaba por la causa que sea (es opcional, pero salta un *warning* si no lo encuentra)
* `crash` &rarr; se ejecuta si el proceso `s6-svscan` acaba anormalmente, y es opcional

Por lo tanto, un *setup* típico incluye crear `.s6-svscan/finish` y varios `<servicio>/run`. Con esto es suficiente.

## Un ejemplo: contenedor con servidor web y SFTP

El primer paso es definir la carpeta de servicios, de donde va a leer `s6-svscan`. En este ejemplo vamos a utilizar `/etc/s6` y en ella vamos a definir:

* `nginx/run` &rarr; para mantener levantado un servidor web **nginx**
* `ssh/run` &rarr; para mantener el servidor SSH/SFTP levantado
* `.s6-svscan/finish` &rarr; no hace nada, pero es para suprimir el *warning* al acabar el contenedor

```bash
gerard@atlantis:~/workspace/miniserver$ tree -a
.
├── s6
│   ├── nginx
│   │   └── run
│   ├── .s6-svscan
│   │   └── finish
│   └── ssh
│       └── run
├── Dockerfile
└── nginx.conf

4 directories, 5 files
gerard@atlantis:~/workspace/miniserver$
```

**NOTA**: No ponemos *scripts* de `finish` en los servicios porque no queremos hacer nada cuando acaben, más allá de su reinicio por parte de **s6**.

**TRUCO**: Si la caída de un servicio es suficientemente grave como para querer parar el contenedor, podéis poner `s6-svscanctl -t /etc/s6` en el script `finish` de ese servicio para parar **s6**.

Lo importante de los *scripts* de `run` es que no acaben, lo que se interpreta como servicio acabado (y candidato a levantar de nuevo). Este paradigma no nos es nuevo en **docker**.

En cuanto a los *scripts* en sí mismos, no hacen nada especialmente complicado:

```bash
gerard@atlantis:~/workspace/miniserver$ cat s6/nginx/run
#!/bin/sh

exec /usr/sbin/nginx -g "daemon off;"
gerard@atlantis:~/workspace/miniserver$
```

```bash
gerard@atlantis:~/workspace/miniserver$ cat s6/ssh/run
#!/bin/sh

for key in rsa ecdsa ed25519; do
    test -e /etc/ssh/ssh_host_${key}_key || ssh-keygen -t ${key} -N "" -f /etc/ssh/ssh_host_${key}_key -q
done

exec /usr/sbin/sshd -D -e
gerard@atlantis:~/workspace/miniserver$
```

```bash
gerard@atlantis:~/workspace/miniserver$ cat s6/.s6-svscan/finish
#!/bin/sh
gerard@atlantis:~/workspace/miniserver$
```

El único *script* que hace algo un poco más complejo es el de SSH, que se encarga de crear las *host keys* si no hubiera ninguna, para que cada contenedor genere las suyas propias y no vengan en la imagen.

En cuanto a la imagen, se necesita que todos los comandos usados funcionen en el contenedor. Esto nos obliga a instalar los paquetes y configuraciones como es habitual. La parte propia de **s6** se limita a tres cosas:

* Instalar el paquete **s6**
* Crear su carpeta de servicios en `/etc/s6`, en este caso mediante copia de los scripts
* Indicar que el comando a ejectuar será `s6-svscan /etc/s6`

Así quedaría el `Dockerfile`:

```bash
gerard@atlantis:~/workspace/miniserver$ cat Dockerfile
FROM alpine:3.8

# ssh daemon
RUN apk add --no-cache openssh && \
    adduser -D gerard && \
    echo "gerard:s3cr3t" | chpasswd

# nginx server
RUN apk add --no-cache nginx && \
    ln -s /dev/stdout /var/log/nginx/access.log && \
    ln -s /dev/stderr /var/log/nginx/error.log && \
    mkdir /run/nginx && \
    rm /etc/nginx/conf.d/default.conf && \
    install -d -o gerard -g gerard -m 755 /srv/www
COPY nginx.conf /etc/nginx/

# s6 supervision tools
RUN apk add --no-cache s6
COPY s6 /etc/s6
CMD ["/bin/s6-svscan","/etc/s6"]
gerard@atlantis:~/workspace/miniserver$
```

Por tener el ejemplo completo, y aunque no tiene nada que ver con **s6**, incluyo también la configuración de **nginx**:

```bash
gerard@atlantis:~/workspace/miniserver$ cat nginx.conf
worker_processes 1;

events {
        worker_connections 1024;
}

http {
        include mime.types;
        default_type application/octet-stream;
        sendfile on;
        keepalive_timeout 65;

        server {
                listen 80;
                server_name _;
                root /srv/www;
                index index.html;
                error_page 404 /404.html;

                location /404.html {
                        internal;
                }
        }
}
gerard@atlantis:~/workspace/miniserver$
```

Solo nos quedaría publicar los puertos de una forma inteligente, subir contenido por SFTP o SCP en `/srv/www`, y observar el resultado en el navegador.
