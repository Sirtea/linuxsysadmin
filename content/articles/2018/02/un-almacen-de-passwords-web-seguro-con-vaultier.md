---
title: "Un almacén de passwords web seguro con vaultier"
slug: "un-almacen-de-passwords-web-seguro-con-vaultier"
date: 2018-02-05
categories: ['Seguridad']
tags: ['vaultier', 'password']
---

Cada vez que trabajo en un cliente me pasa lo mismo; las claves de acceso y las contraseñas de las diferentes herramientas y de los diferentes servidores están guardadas de forma caótica e inaccesible. Puesto que trabajamos en un equipo distribuido, me gusta tener esto publicado en remoto pero seguro.<!--more-->

Como reto personal, me he propuesto dar a conocer una de esas herramientas, con la esperanza de que la acaben adoptando por su genialidad.

Los requisitos son bastante simples:

* Debe permitir un control de acceso granular a usuarios y a grupos
* Debe poder clasificar nuestros secretos por algún criterio (por ejemplo por proyecto)
* Debe asegurar la confidencialidad de los secretos guardados

Tras un poco de búsqueda por internet, acabé encontrando una muy interesante llamada [Vaultier](http://www.vaultier.org/). Como plus extra, se nos ofrece la aplicación como una imagen de **docker**, lo que me permite hacer una instalación de usar y tirar.

![Panel de Vaultier](/images/vaultier.jpg)

## Instalación

Podemos hacer un *pull* de la imagen directamente desde [DockerHub](https://hub.docker.com/r/rclick/vaultier/):
```bash
gerard@aldebaran:~/docker/vaultier$ docker pull rclick/vaultier
Using default tag: latest
latest: Pulling from rclick/vaultier
...
Digest: sha256:624a1191c55e149ef77aa567b739297df4843342ba267660e59cf1610b163202
Status: Downloaded newer image for rclick/vaultier:latest
gerard@aldebaran:~/docker/vaultier$ 
```

Y la levantamos con un simple *docker run*, con la precaución de exponer su puerto 80 para poder acceder cómodamente a la dirección IP de nuestra máquina servidora; se puede hacer en *background* con el *flag -d*, aunque de momento, así se queda.

```bash
gerard@aldebaran:~/docker/vaultier$ docker run -ti --rm -p 80:80 rclick/vaultier
/usr/lib/python2.7/dist-packages/supervisor/options.py:295: UserWarning: Supervisord is running as root and it is searching for its configuration file in default locations (including its current working directory); you probably want to specify a "-c" argument specifying an absolute path to a configuration file for improved security.
  'Supervisord is running as root and it is searching '
2017-06-15 10:58:30,155 CRIT Supervisor running as root (no user in config file)
2017-06-15 10:58:30,173 INFO RPC interface 'supervisor' initialized
2017-06-15 10:58:30,173 CRIT Server 'unix_http_server' running without any HTTP authentication checking
2017-06-15 10:58:30,173 INFO supervisord started with pid 1
2017-06-15 10:58:31,175 INFO spawned: 'vaultier-celerybeat' with pid 9
2017-06-15 10:58:31,176 INFO spawned: 'nginx' with pid 10
2017-06-15 10:58:31,177 INFO spawned: 'vaultier-worker' with pid 11
2017-06-15 10:58:31,179 INFO spawned: 'postgresql' with pid 12
2017-06-15 10:58:31,186 INFO spawned: 'uwsgi' with pid 13
2017-06-15 10:58:32,988 INFO success: vaultier-celerybeat entered RUNNING state, process has stayed up for > than 1 seconds (startsecs)
2017-06-15 10:58:32,988 INFO success: nginx entered RUNNING state, process has stayed up for > than 1 seconds (startsecs)
2017-06-15 10:58:32,988 INFO success: vaultier-worker entered RUNNING state, process has stayed up for > than 1 seconds (startsecs)
2017-06-15 10:58:32,989 INFO success: postgresql entered RUNNING state, process has stayed up for > than 1 seconds (startsecs)
2017-06-15 10:58:32,989 INFO success: uwsgi entered RUNNING state, process has stayed up for > than 1 seconds (startsecs)
```

Vemos que la imagen dispone de varios servicios, que se manejan con **supervisor**. Esto nos levanta la aplicación entera y la base de datos que necesita para funcionar.

Solo nos queda dirigirnos a <http://localhost/> y ver nuestro nuevo servidor de secretos en funcionamiento.

## Conceptos básicos

La mecánica básica es muy simple; basta con perder un poco de tiempo jugando con al interfaz. Hay que tener en cuenta lo siguiente:

* Existen usuarios autenticados con certificados
* Estos usuarios pueden pertenecer a grupos
* Los secretos pueden ser contraseñas, notas o ficheros
* Los secretos se agrupan en *cards*
* Los *cards* se agrupan en *vaults*
* Los *vaults* se agrupan en *workspaces*
* Un *workspace* es creado por un usuario que es su administrador
* Usuarios y grupos se pueden invitar para compartir acceso a *cards*, a *vaults* y a *workspaces*

A partir de aquí, solo es necesario poner un sistema de niveles inteligentes que nos permitan compartir lo que necesitemos con los diferentes grupos que necesitamos.
