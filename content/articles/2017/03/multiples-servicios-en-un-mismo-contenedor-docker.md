---
title: "Múltiples servicios en un mismo contenedor Docker"
slug: "multiples-servicios-en-un-mismo-contenedor-docker"
date: 2017-03-06
categories: ['Sistemas']
tags: ['docker', 'runit', 'LAMP', 'apache', 'mysql', 'php']
---

Como ya sabemos, un contenedor **docker** solo puede ejecutar un proceso, y su finalización implica la parada del contenedor. Sin embargo, a veces nos puede interesar cargar los contenedores con algún servicio más, para hacerlos autosuficientes. Para ello, nos podemos ayudar de un *gestor de procesos*, como por ejemplo, **runit**.<!--more-->

Antes de nada, [una referencia en contra](https://blog.docker.com/2014/06/why-you-dont-need-to-run-sshd-in-docker/); esto complica nuestro contenedor de una forma no recomendad por el propia autor de **docker**.

> If you need multiple processes, you need to add one at the top-level to take care of the others. In other words, you’re turning a lean and simple container into something much more complicated.

Avisados quedáis; a partir de aquí, vamos a ver como hacerlo con un ejemplo bastante extendido: un servidor [LAMP](https://es.wikipedia.org/wiki/LAMP). La idea es que usaremos un *gestor de procesos* llamado **runit** (aunque hay otros candidatos), que me gusta por su simplicidad.

## Ejemplo: El contenedor LAMP

Nuestro contenedor va a ser un servidor muy clásico, con un **apache**, un **mysql**, **php5** y los paquetes que esta configuración requiera, como por ejemplo, el driver de la base de datos **php5-mysql**.

**AVISO**: No voy a añadir las instrucciones de *docker build* ni de *docker run* porque no aportan nada nuevo. Mejor centrémonos en las partes importantes.

Vamos a utilizar la siguiente topología en la carpeta del *Dockerfile*. La idea es que vamos a alojar el código **php** en la carpeta *www*, las configuraciones del **apache** en la carpeta *apache2* y las configuraciones de **runit** en *services*. No hay configuración específica para el **mysql**.

```bash
gerard@antares:~/docker/lamp$ tree
.
├── apache2
│   ├── custom.conf
│   └── site.conf
├── services
│   ├── apache2
│   │   └── run
│   └── mysql
│       └── run
├── www
│   └── adminer.php
└── Dockerfile

5 directories, 6 files
gerard@antares:~/docker/lamp$ 
```

Y como no, el *Dockerfile* usado:

```bash
gerard@antares:~/docker/lamp$ cat Dockerfile 
FROM debian:jessie
ENV DEBIAN_FRONTEND noninteractive

# Paquetes necesarios
RUN apt-get update && \
    apt-get install -y runit php5 php5-mysql mysql-server && \
    rm -rf /var/lib/apt/lists/*

# Configuracion de runit
COPY services /etc/service

# Configuracion de apache
RUN unlink /etc/apache2/sites-enabled/000-default.conf
COPY apache2/custom.conf /etc/apache2/conf-enabled

# Configuracion y contenido del sitio
COPY apache2/site.conf /etc/apache2/sites-enabled
COPY www /srv/www

CMD ["/usr/bin/runsvdir", "/etc/service"]
gerard@antares:~/docker/lamp$ 
```

### Runit

El proceso principal, que se va a dedicar a controlar los otros procesos es **runit**, concretamente mediante el binario *runsvdir*. De acuerdo a nuestro *Dockerfile*, va a gestionar un proceso por carpeta en */etc/service*. Dentro de esta carpeta va a tener información de ejecución e información de estado.

Es importante poner un *script* llamado *run* con permisos de ejecución, que es el *script* que **runit** va a ejecutar y monitorizar, reiniciándolo en caso de caerse. No hay sorpresas en estos *scripts*.

```bash
gerard@antares:~/docker/lamp$ cat services/apache2/run 
#!/bin/sh

exec /usr/sbin/apache2ctl -D FOREGROUND
gerard@antares:~/docker/lamp$ cat services/mysql/run 
#!/bin/sh

exec /usr/bin/mysqld_safe
gerard@antares:~/docker/lamp$ 
```

### Apache

El **apache** necesita la configuración del *virtualhost* que le indica lo que debe servir, y donde está; esto debe ir en */etc/apache2/sites-enabled*, de acuerdo con el *layout* de directorios que utiliza la distribución usada (**Debian** en este caso). Hemos eliminado el *virtualhost* que viene por defecto.

```bash
gerard@antares:~/docker/lamp$ cat apache2/site.conf 
<VirtualHost *:80>
	DocumentRoot /srv/www
	LogLevel info
	ErrorLog ${APACHE_LOG_DIR}/error.log
	CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
gerard@antares:~/docker/lamp$ 
```

El otro punto conflictivo es que el fichero de configuración base no lleva permisos para servir nada en */srv/www*, sino en */var/www*. Personalmente creo que el contenido debería estar en */srv/www*, así que tengo que añadir estos permisos, que se puede hacer cómodamente con un fichero adicional en la carpeta */etc/apache2/conf-enabled*, que se incluye desde el fichero */etc/apache2/apache2.conf*.

```bash
gerard@antares:~/docker/lamp$ cat apache2/custom.conf 
<Directory /srv/>
	Options Indexes FollowSymLinks
	AllowOverride None
	Require all granted
</Directory>
gerard@antares:~/docker/lamp$ 
```

### MySQL

No hay nada especial para **mysql**. Simplemente dejamos que la variable de entorno *DEBIAN_FRONTEND* indique a **apt-get** que no pregunte una contraseña para el usuario *root*, quedando este usuario sin contraseña. Esto debe ser revisado con esmero.

### Contenido web

Para mantener limpia la carpeta de *build*, he decidido poner el contenido web en una carpeta *www* aparte. Simplemente se trata del *document root* de nuestro *virtualhost*.

En este caso se ha usado [Adminer](https://www.adminer.org/) que es una aplicación prefabricada de un solo fichero para administrar nuestra base de datos. La parte interesante es que se trata de algo hecho en **php** que se conecta a nuestro **mysql**, y nos demuestra que todo funciona. Reemplazad el contenido de esta carpeta por vuestro código final.

### Más servicios

Se necesita subir código mediante un servidor **FTP** o **SFTP**, algún **cron job**, **logrotate** o lo que sea? Pues usad la misma filosofía: instalad, configurad e instruid a **runit** para que levante el proceso. Sin límites.

**RESULTADO**: Tras construir la imagen y ejecutarla, ya tenemos nuestro servidor funcionando en un solo contenedor.
