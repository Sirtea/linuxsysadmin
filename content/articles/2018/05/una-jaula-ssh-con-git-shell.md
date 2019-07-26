---
title: "Una jaula SSH con git-shell"
slug: "una-jaula-ssh-con-git-shell"
date: 2018-05-14
categories: ['Operaciones']
tags: ['git', 'git-shell', 'jaula', 'ssh']
---

El otro día recibí una petición en el trabajo por parte de un cliente: poder ejecutar algunas operaciones por SSH en nuestro servidor. Solo de pensar en montar una jaula SSH con los binarios y sus librerías ya se me hizo cuesta arriba, y por eso lo hice con **git-shell**.<!--more-->

No he encontrado por internet nadie que haya hecho algo similar, así que lo he puesto por escrito en este artículo. Se trata de utilizar el *shell* restringido **git-shell** para que el usuario solo pueda utilizar los *scripts* o binarios presentes en la carpeta `~/git-shell-commands/`.

Por defecto, **git-shell** solo acepta las operaciones necesarias para trabajar remotamente con repositorios *git*. Esto se puede leer en [la documentación](https://git-scm.com/docs/git-shell):

> Call the corresponding server-side command to support the client’s git push, git fetch, or git archive --remote request.

Sin embargo, ante la presencia de una carpeta `~/git-shell-commands/` también nos añade los *scripts* y binarios de la misma al conjunto de operaciones que podemos ejecutar.

> If a ~/git-shell-commands directory is present, git shell will also handle other, custom commands by running "git-shell-commands/<command> <arguments>" from the user’s home directory.

Esto está pensado para operaciones administrativas como crear, borrar y modificar los repositorios alojados. Sin embargo, podemos utilizarlo para limitar los comandos que un usuario puede ejecutar, sean o no de *git*.

Por supuesto, el soporte a operaciones remotas de *git* no nos molesta; al no haber repositorios, estas operaciones van a fallar de todas formas. Así pues, vamos a centrarnos en nuestras propias operaciones.

## Un ejemplo simple

Supongamos que tenemos un servidor con SSH, al que vamos a llamar *server*. Para la demostración, se va a tratar de un servidor **Alpine Linux**, aunque esto no es relevante.

**NOTA**: A menos que se diga lo contrario, todos los comandos se ejecutan con *root*, aunque podéis usar *sudo* con el mismo efecto.

**AVISO**: Las sesiones de SSH a *server* responden con el nombre *localhost*. Esto es debido a que el servidor es un contenedor **docker** con el puerto 22 mapeado al puerto 22 del servidor *sirius*; al ser un ejemplo, prefiero no virtualizar máquinas nuevas.

Para disponer del binario **git-shell**, necesitamos el paquete **git** instalado. Si no lo tenéis hecho, es el mejor momento para hacerlo.

```bash
server:~# apk add --no-cache git
fetch http://dl-cdn.alpinelinux.org/alpine/v3.7/main/x86_64/APKINDEX.tar.gz
fetch http://dl-cdn.alpinelinux.org/alpine/v3.7/community/x86_64/APKINDEX.tar.gz
(1/6) Installing ca-certificates (20171114-r0)
(2/6) Installing libssh2 (1.8.0-r2)
(3/6) Installing libcurl (7.59.0-r0)
(4/6) Installing expat (2.2.5-r0)
(5/6) Installing pcre2 (10.30-r0)
(6/6) Installing git (2.15.0-r1)
Executing busybox-1.27.2-r7.trigger
Executing ca-certificates-20171114-r0.trigger
OK: 20 MiB in 20 packages
server:~# 
```

Vamos a crear un usuario para que nuestro cliente pueda entrar por SSH; nada nuevo por el momento, con la excepción de que vamos a indicar como su *shell* el mismo **git-shell**.

```bash
server:~# adduser -D customer -s /usr/bin/git-shell
server:~# echo "customer:s3cr3t" | chpasswd
chpasswd: password for 'customer' changed
server:~# 
```

Si el usuario intenta entrar en este punto, solo podrá utilizar las operaciones *git* remotas, siendo imposible que lance una sesión interactiva, o comandos sueltos por SSH.

```bash
gerard@sirius:~$ ssh customer@server
Warning: Permanently added 'localhost' (ECDSA) to the list of known hosts.
customer@localhost's password: 
Welcome to Alpine!

The Alpine Wiki contains a large amount of how-to guides and general
information about administrating Alpine systems.
See <http://wiki.alpinelinux.org>.

You can setup the system with the command: setup-alpine

You may change this message by editing /etc/motd.

fatal: Interactive git shell is not enabled.
hint: ~/git-shell-commands should exist and have read and execute access.
Connection to localhost closed.
gerard@sirius:~$ 
```

```bash
gerard@sirius:~$ ssh customer@server hostname
Warning: Permanently added 'localhost' (ECDSA) to the list of known hosts.
customer@localhost's password: 
fatal: unrecognized command 'hostname'
gerard@sirius:~$ 
```

Para activar **git-shell**, hay que crear la carpeta indicada `~/git-shell-commands`; los comandos que se pueden ejecutar son los que van dentro de la misma.

```bash
server:~# cd /home/customer/
server:/home/customer# mkdir git-shell-commands
server:/home/customer# chown customer:customer git-shell-commands/
server:/home/customer# 
```

Con esto el usuario ya va a poder entrar en una sesión interactiva, aunque no dispone de comandos para ejecutar:

```bash
gerard@sirius:~$ ssh customer@server
Warning: Permanently added 'localhost' (ECDSA) to the list of known hosts.
customer@localhost's password: 
Welcome to Alpine!

The Alpine Wiki contains a large amount of how-to guides and general
information about administrating Alpine systems.
See <http://wiki.alpinelinux.org>.

You can setup the system with the command: setup-alpine

You may change this message by editing /etc/motd.

git> hostname
unrecognized command 'hostname'
git> 
```

Solo nos faltaría rellenar la carpeta con los binarios o *scripts* que este usuario pueda necesitar. Como punto interesante, si existe un `help`, este se va a ejecutar al entrar por SSH de forma automática, y nos puede servir para que el usuario sepa que hacer (o para que pida ayuda en el medio de una sesión).

El resto de comandos son libres y podéis hacer literalmente lo que queráis, con el entendido que estos *scripts* pueden invocar todos los comandos del sistema de forma normal, pero  el usuario solo va a poder ejecutar estos *scripts*. Veamos un ejemplo:

```bash
server:/home/customer# cd git-shell-commands/
server:/home/customer/git-shell-commands# cat help 
#!/bin/sh

echo "Permitted commands:"
echo "  help - shows this help message"
echo "  hostname - shows hostname of this server"
echo "  get_connected_users - shows user currently logged on"
server:/home/customer/git-shell-commands# cat hostname 
#!/bin/sh

hostname
server:/home/customer/git-shell-commands# cat get_connected_users 
#!/bin/sh

n=$RANDOM
let n%=10
echo "Users connected: $n"
server:/home/customer/git-shell-commands# chown customer:customer *
server:/home/customer/git-shell-commands# chmod 755 *
server:/home/customer/git-shell-commands# 
```

Ahora es el momento de que el usuario se conecte y vea el resultado:

```bash
gerard@sirius:~$ ssh customer@server
Warning: Permanently added 'localhost' (ECDSA) to the list of known hosts.
customer@localhost's password: 
Welcome to Alpine!

The Alpine Wiki contains a large amount of how-to guides and general
information about administrating Alpine systems.
See <http://wiki.alpinelinux.org>.

You can setup the system with the command: setup-alpine

You may change this message by editing /etc/motd.

Permitted commands:
  help - shows this help message
  hostname - shows hostname of this server
  get_connected_users - shows user currently logged on
git> hostname
server
git> help
Permitted commands:
  help - shows this help message
  hostname - shows hostname of this server
  get_connected_users - shows user currently logged on
git> get_connected_users
Users connected: 4
git> exit
Connection to localhost closed.
gerard@sirius:~$ 
```

Y de esta forma, el usuario queda limitado, pero con estos 3 comandos posibles.
