---
title: "Un servidor de git local con gitolite"
slug: "un-servidor-de-git-local-con-gitolite"
date: 2017-06-26
categories: ['Sistemas']
tags: ['git', 'gitolite']
---

A todos nos encanta el sistema de control de versiones **git**. Tanto a nivel local como a nivel público en *GitHub* es una maravilla; lo que no me gusta tanto es el precio que suelen tener las soluciones privadas. Sin embargo, y con un poco de habilidad, podemos encontrar alternativas.<!--more-->

Existen varias alternativas tipo web, como por ejemplo [GitLab](https://github.com/gitlabhq/gitlabhq) (imagen para **docker** en [DockerHub](https://hub.docker.com/r/gitlab/gitlab-ce/)); sin embargo, como amante del terminal me decanto por [Gitolite](http://gitolite.com/gitolite/index.html).

Además de las virtudes propias de **git**, **gitolite** nos ofrece un sistema de control de permisos en los repositorios bajo su administración, usando un usuario remoto SSH único y diferenciando quien es el usuario mediante la clave SSH que use para establecer la conexión.

Otro punto interesante es que el servidor (usuarios, repositorios y permisos) se administra mediante **git**, existiendo el usuario *admin* con permisos sobre el repositorio *gitolite-admin*. Este tiene la responsabilidad de clonar el repositorio, añadir los cambios y empujarlos con un *git push*.

## Montando el servidor

Como viene siendo tradición, vamos a aislar nuestro servicio de **gitolite** en un contenedor **docker**. Para ello vamos a utilizar una base de *Alpine Linux* que nos va a dar un conjunto de paquetes bastante actualizados, a un tamaño bastante pequeño.

Vamos a crear una imagen y le vamos a poner un *tag* para diferenciarla del resto, por ejemplo, *gitolite*. Aquí os paso el contexto para su construcción:

```bash
gerard@aldebaran:~/docker/gitolite$ cat Dockerfile 
FROM alpine:3.5
RUN apk add --no-cache openssh gitolite && \
    passwd -u git
COPY start.sh /
CMD ["/start.sh"]
gerard@aldebaran:~/docker/gitolite$ cat start.sh 
#!/bin/sh

ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key -N ''

echo "$SSH_PUBKEY" > /tmp/admin.pub
su git -c "gitolite setup -pk /tmp/admin.pub"
rm /tmp/admin.pub

exec /usr/sbin/sshd -D -e
gerard@aldebaran:~/docker/gitolite$ 
```

El *script* de inicialización *start.sh* va a iniciar el demonio de SSH, no sin antes generar las claves de *host* nuevas e inicializar **gitolite**. Un pequeño detalle interesante es que **gitolite** exige una clave pública SSH para que el usuario *admin* pueda modificar el repositorio de administración; por comodidad la vamos a pasar mediante la variable de entorno *SSH_PUBKEY*.

La forma más fácil de levantar el servidor es con **docker compose**, y aunque este varia según vuestros gustos personales, yo he usado algo así:

```bash
gerard@aldebaran:~/docker/gitolite$ cat docker-compose.yml 
version: '3'
services:
  gitolite:
    image: gitolite
    container_name: gitolite
    hostname: gitolite
    environment:
      SSH_PUBKEY: "ssh-rsa ..."
    ports:
      - "22:22"
gerard@aldebaran:~/docker/gitolite$ 
```

**TRUCO**: Para evitar indicar el usuario, la dirección IP y la clave SSH a usar, podemos definir algunos *hosts* en el fichero *~/.ssh/config*, que también nos va a ser útil en el momento de las operaciones **git** remotas, que no aceptan parámetros.

```bash
gerard@aldebaran:~$ cat .ssh/config 
...
Host gitolite-admin
	Hostname 127.0.0.1
	User git
	IdentityFile ~/docker/gitolite/keys/admin

Host gitolite-gerard
	Hostname 127.0.0.1
	User git
	IdentityFile ~/docker/gitolite/keys/gerard
gerard@aldebaran:~$ 
```

## Administrando gitolite

Como ya se ha indicado, el usuario *admin* debe clonar el repositorio *gitolite-admin* para editar los cambios. En principio es el único usuario y tiene permisos sobre el repositorio mencionado. Podemos ver sus permisos intentando entrar al servidor por SSH (recordad que lo he mapeado al puerto 22 de mi máquina).

```bash
gerard@aldebaran:~/docker/gitolite/workspace$ ssh -i ../keys/admin git@localhost
Warning: Permanently added 'localhost' (RSA) to the list of known hosts.
PTY allocation request failed on channel 0
hello admin, this is git@gitolite running gitolite3 v3.4.0-4380-g8bd1571 on git 2.11.2

 R W	gitolite-admin
 R W	testing
Connection to localhost closed.
gerard@aldebaran:~/docker/gitolite/workspace$ 
```

Alternativamente podemos usar el *host* declarado en la configuración SSH cliente (el truco está más arriba):

```bash
gerard@aldebaran:~/docker/gitolite/workspace$ ssh gitolite-admin
Warning: Permanently added '127.0.0.1' (RSA) to the list of known hosts.
PTY allocation request failed on channel 0
hello admin, this is git@gitolite running gitolite3 v3.4.0-4380-g8bd1571 on git 2.11.2

 R W	gitolite-admin
 R W	testing
Connection to 127.0.0.1 closed.
gerard@aldebaran:~/docker/gitolite/workspace$ 
```

La sesión se cierra, ya que la función de este SSH es solamente hacer las operaciones remotas de *clone*, *pull* y *push*. Cualquier otro usuario va a fallar si intenta entrar al servidor de la misma forma, ya que no hay nadie más autorizado.

Para realizar modificaciones tenemos que clonar el repositorio de administración:

```bash
gerard@aldebaran:~/docker/gitolite/workspace$ git clone gitolite-admin:gitolite-admin.git
Cloning into 'gitolite-admin'...
Warning: Permanently added '127.0.0.1' (RSA) to the list of known hosts.
remote: Counting objects: 6, done.
remote: Compressing objects: 100% (4/4), done.
remote: Total 6 (delta 0), reused 0 (delta 0)
Receiving objects: 100% (6/6), done.
Checking connectivity... done.
gerard@aldebaran:~/docker/gitolite/workspace$ 
```

Esto nos da el repositorio de administración, que de por sí, es bastante intuitivo.

```bash
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ tree
.
├── conf
│   └── gitolite.conf
└── keydir
    └── admin.pub

2 directories, 2 files
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ 
```

La carpeta *keydir* es donde hay que poner las claves de los usuarios SSH para que puedan entrar en la máquina. Es importante poner el formato `<usuario>.pub` donde `usuario` es el usuario tal como lo conoce **gitolite** y como hay que indicar en los permisos; da igual como se llama la clave privada en la máquina del usuario (por ejemplo, *id_rsa*).

El fichero *conf/gitolite.conf* tiene la especificación de los repositorios y los permisos que tienen los usuarios sobre ellos.

### Añadiendo usuarios

Para añadir o retirar usuarios, basta con añadir o quitar su clave de la carpeta *keydir* en nuestro repositorio local, para posteriormente hacer el correspondiente *push*. Por ejemplo, añado la clave para mi usuario:

```bash
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ tree
.
├── conf
│   └── gitolite.conf
└── keydir
    ├── admin.pub
    └── gerard.pub

2 directories, 3 files
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ git add keydir/gerard.pub 
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ git commit -m "Add user gerard"
...
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ 
```

Podemos ver que ahora puedo usar el usuario *gerard* para hacer SSH, pero que los repositorios a los que tiene acceso no son los mismos; de hecho, viene uno llamado *testing* por defecto. Recordad que **gitolite** decide el usuario en función de la clave SSH usada, y esta la he puesto en la configuración SSH cliente en *~/.ssh/config*

```bash
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ ssh gitolite-admin
Warning: Permanently added '127.0.0.1' (RSA) to the list of known hosts.
PTY allocation request failed on channel 0
hello admin, this is git@gitolite running gitolite3 v3.4.0-4380-g8bd1571 on git 2.11.2

 R W	gitolite-admin
 R W	testing
Connection to 127.0.0.1 closed.
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ ssh gitolite-gerard
Warning: Permanently added '127.0.0.1' (RSA) to the list of known hosts.
PTY allocation request failed on channel 0
hello gerard, this is git@gitolite running gitolite3 v3.4.0-4380-g8bd1571 on git 2.11.2

 R W	testing
Connection to 127.0.0.1 closed.
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ 
```

El punto interesante de todo esto es que todos los usuarios utilizan un *shell* restringido, pero este acepta un parámetro, que es el usuario. Este parámetro es forzado por SSH cuando alguna de las líneas del fichero *authorized_keys* da positivo.

```bash
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ docker exec gitolite cat /var/lib/git/.ssh/authorized_keys
# gitolite start
command="/usr/lib/gitolite/gitolite-shell admin",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa ...  
command="/usr/lib/gitolite/gitolite-shell gerard",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa ...  
# gitolite end
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ 
```

### Administrando repositorios y permisos

El fichero clave para esto es *conf/gitolite.conf*. Si vemos lo que tiene, comprenderemos inmediatamente lo que hay que hacer.

```bash
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ cat conf/gitolite.conf 
repo gitolite-admin
    RW+     =   admin

repo testing
    RW+     =   @all
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ 
```

Se trata de repositorios (o grupos) con una lista tabulada de permisos y usuarios o grupos a los que afectan. Más información en [la documentación](https://gitolite.com/gitolite/basic-admin.html). El grupo *all* es especial y viene predefinido.

Vamos a poner algunos repositorios, grupos y permisos:

```bash
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ cat conf/gitolite.conf 
@devs = dev1 dev2 dev3
@ops = ops1
@staff = @devs @ops

@blog =  blog-public blog-admin
@shop = shop-public shop-admin shop-api

repo gitolite-admin
    RW+ = admin

repo @blog
    RW+ = gerard
    RW = @devs
    R = @ops

repo @shop
    RW+ = @staff
    R = gerard
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ git add conf/gitolite.conf 
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ git commit -m "Added some projects and permissions"
[master f8fe801] Added some projects and permissions
 1 file changed, 16 insertions(+), 3 deletions(-)
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ git push
...  
Warning: Permanently added '127.0.0.1' (RSA) to the list of known hosts.
Counting objects: 4, done.
Delta compression using up to 4 threads.
Compressing objects: 100% (3/3), done.
Writing objects: 100% (4/4), 474 bytes | 0 bytes/s, done.
Total 4 (delta 0), reused 0 (delta 0)
remote: Initialized empty Git repository in /var/lib/git/repositories/blog-admin.git/
remote: Initialized empty Git repository in /var/lib/git/repositories/blog-public.git/
remote: Initialized empty Git repository in /var/lib/git/repositories/shop-admin.git/
remote: Initialized empty Git repository in /var/lib/git/repositories/shop-api.git/
remote: Initialized empty Git repository in /var/lib/git/repositories/shop-public.git/
To gitolite-admin:gitolite-admin.git
   5114865..f8fe801  master -> master
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ 
```

Y solo nos queda ver los permisos que tenemos ahora con los diferentes usuarios:

```bash
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ ssh gitolite-admin
Warning: Permanently added '127.0.0.1' (RSA) to the list of known hosts.
PTY allocation request failed on channel 0
hello admin, this is git@gitolite running gitolite3 v3.4.0-4380-g8bd1571 on git 2.11.2

 R W	gitolite-admin
Connection to 127.0.0.1 closed.
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ ssh gitolite-gerard
Warning: Permanently added '127.0.0.1' (RSA) to the list of known hosts.
PTY allocation request failed on channel 0
hello gerard, this is git@gitolite running gitolite3 v3.4.0-4380-g8bd1571 on git 2.11.2

 R W	blog-admin
 R W	blog-public
 R  	shop-admin
 R  	shop-api
 R  	shop-public
Connection to 127.0.0.1 closed.
gerard@aldebaran:~/docker/gitolite/workspace/gitolite-admin$ 
```

El repositorio *testing* no aparece en la configuración, pero sus datos siguen en el servidor. En caso de querer eliminarlo definitivamente, necesitamos eliminar su carpeta entrando en el servidor.
