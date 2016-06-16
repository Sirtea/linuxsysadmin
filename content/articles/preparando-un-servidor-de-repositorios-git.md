Title: Preparando un servidor de repositorios GIT
Slug: preparando-un-servidor-de-repositorios-git
Date: 2016-06-20 08:30
Category: Sistemas
Tags: linux, git, ssh, docker



Algunas veces tenemos necesidad de crear un proyecto con un equipo pequeño y necesitamos versionarlo en un sitio accesible para todos los participantes involucrados. El precio de soluciones en la nube suele ser prohibitivo, y montar una solución gráfica puede ser demasiado. Lo podemos hacer simplemente usando **git** y **ssh**.

La idea es muy simple; solo se necesita un servidor de **ssh**, que es la forma de transportar los datos, y los binarios de **git** para que los organice a placer. También vamos a necesitar un usuario **git**, que es el que vamos a usar para entrar, ya sea para crear y borrar repositorios, como para las operaciones remotas recibidas por el repositorio.

**TRUCO**: Podemos eliminar la petición de *password* para todos los accesos que se hagan por **SSH**, sean para entrar en las máquinas por **SSH** mediante cualquier *shell* de este artículo, o como resultado de una operación remota de **git**. Esto se puede hacer usando autenticación **SSH** por claves, como se explica en un [artículo anterior]({filename}/articles/autenticacion-ssh-por-claves.md).

## Montando el servidor

Para crear la máquina base, vamos a utilizar **Docker** por comodidad. Aprovechando esta tecnología, podemos crear el contenedor partiendo de una imagen creada con un *Dockerfile*.

```bash
gerard@sirius:~/build$ cat Dockerfile
FROM debian:jessie
RUN apt-get update && \
    apt-get install -y git openssh-server && \
    mkdir /var/run/sshd
RUN useradd git -G sudo -s /bin/bash -m && \
    echo "git:git" | chpasswd
CMD ["/usr/sbin/sshd", "-D"]
gerard@sirius:~/build$ 
```

Construimos la imagen, basándonos en el anterior *Dockerfile*, y le añadimos el *tag* "gitserver".

```bash
gerard@sirius:~/build$ docker build -t gitserver .
Sending build context to Docker daemon 5.632 kB
Step 1 : FROM debian:jessie
 ---> bb5d89f9b6cb
Step 2 : RUN apt-get update &&     apt-get install -y git openssh-server &&     mkdir /var/run/sshd
 ---> Running in 6b612781b788
...
 ---> e88e644b0a53
Removing intermediate container 6b612781b788
Step 3 : RUN useradd git -G sudo -s /bin/bash -m &&     echo "git:git" | chpasswd
 ---> Running in 0e865bda447e
 ---> 81d111c19c71
Removing intermediate container 0e865bda447e
Step 4 : CMD /usr/sbin/sshd -D
 ---> Running in 67bbebe61c74
 ---> 81c2dd7b156a
Removing intermediate container 67bbebe61c74
Successfully built 81c2dd7b156a
gerard@sirius:~/build$ 
```

Lanzamos una instancia del contenedor para que podamos utilizarla. La parte importante es el *flag* **-d** para ejecutar el contenedor en *background*, y el *flag* **-p** que nos permite publicar el puerto 22 del contenedor en el puerto 22222 de la máquina *host*.

```bash
gerard@sirius:~/build$ docker run -d --name gitserver1 -h gitserver1 -p 22222:22 gitserver
c26f30a94bb75b35c6d6cfe6a6bc5b1ef6929aafe1b5636acd207e019743540b
gerard@sirius:~/build$ 
```

Vamos a entrar en el servidor **SSH** para crear el repositorio *myrepo.git* que nos va a servir de ejemplo.

```bash
gerard@sirius:~/build$ ssh git@localhost -p 22222
git@localhost's password: 

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
git@gitserver1:~$ git init --bare myrepo.git
Initialized empty Git repository in /home/git/myrepo.git/
git@gitserver1:~$ exit
logout
Connection to localhost closed.
gerard@sirius:~/build$ 
```

Desde la máquina *host* (o desde cualquier otra), podemos clonar el repositorio. Como tenemos el puerto del contenedor publicado en el puerto 22222 de la máquina *host* (la de trabajo, en este caso), la usamos tal cual para clonar.

```bash
gerard@sirius:~/build$ git clone ssh://git@localhost:22222/home/git/myrepo.git
Cloning into 'myrepo'...
git@localhost's password: 
warning: You appear to have cloned an empty repository.
Checking connectivity... done.
gerard@sirius:~/build$ 
```

Hacemos un poco de trabajo local, con sus respectivos *commits*. Finalmente podemos hacer un *push* a nuestro repositorio remoto, siguiendo el *workflow* de trabajo que queramos seguir.

```bash
gerard@sirius:~/build$ cd myrepo/
gerard@sirius:~/build/myrepo$ echo 0.0.1 > VERSION
gerard@sirius:~/build/myrepo$ git add VERSION 
gerard@sirius:~/build/myrepo$ git commit -m "Initial commit"
[master (root-commit) f30b82a] Initial commit
 1 file changed, 1 insertion(+)
 create mode 100644 VERSION
gerard@sirius:~/build/myrepo$ git push -u origin master
git@localhost's password: 
Counting objects: 3, done.
Writing objects: 100% (3/3), 222 bytes | 0 bytes/s, done.
Total 3 (delta 0), reused 0 (delta 0)
To ssh://git@localhost:22222/home/git/myrepo.git
 * [new branch]      master -> master
Branch master set up to track remote branch master from origin.
gerard@sirius:~/build/myrepo$ cd ..
gerard@sirius:~/build$ 
```

## Añadiendo restricciones a la sesión SSH

Es un poco peligroso permitir que el usuario *git* entre mediante una sesión **SSH** para hacer lo que le parezca.

Los mismos binarios de **git** incluyen **git-shell**, que es un *shell* que limita lo que puede hacer el usuario, aunque solo permitiría hacer las operaciones *push* y *pull* propias del trabajo remoto con **git**.

¿Y como podemos crear y destruir repositorios? En principio, no se puede. Sin embargo, si creamos una carpeta */home/git/git-shell-commands/*, el usuario va a poder ejecutar los *scripts* que allí pongamos.

Siguiendo esta idea, vamos a mejorar el *Dockerfile* para asignar **git-shell** al usuario *git* y para ponerle un par de comandos.

Vamos a crear dos *scripts* que nos permitan crear y destruir repositorios, que son los siguientes:

```bash
gerard@sirius:~/build$ cat create 
#!/bin/bash

if [ ${#} -ne 1 ]; then
    echo "[ERROR] Syntax: create <repository>"
    exit -1
fi

if [ -e ${1}.git ]; then
    echo "[ERROR] Repository ${1} exists"
    exit -1
fi

git init --bare ${1}.git
echo "[OK] Repository ${1} created"
exit 0
gerard@sirius:~/build$ cat destroy 
#!/bin/bash

if [ ${#} -ne 1 ]; then
    echo "[ERROR] Syntax: destroy <repository>"
    exit -1
fi

if [ -e ${1}.git ]; then
    rm -Rf ${1}.git
    echo "[OK] Repository ${1} deleted"
    exit 0
fi

echo "[ERROR] Repository ${1} does not exist"
exit -1
gerard@sirius:~/build$ 
```

También vamos a reescribir el *Dockerfile* con las nuevas modificaciones.

```bash
gerard@sirius:~/build$ cat Dockerfile.shell 
FROM debian:jessie
RUN apt-get update && \
    apt-get install -y git openssh-server && \
    mkdir /var/run/sshd
RUN useradd git -G sudo -s /usr/bin/git-shell -m && \
    echo "git:git" | chpasswd && \
    mkdir /home/git/git-shell-commands
COPY create destroy /home/git/git-shell-commands/
RUN cp /usr/share/doc/git/contrib/git-shell-commands/help /home/git/git-shell-commands/ && \
    cp /usr/share/doc/git/contrib/git-shell-commands/list /home/git/git-shell-commands/ && \
    chmod 755 /home/git/git-shell-commands/*
CMD ["/usr/sbin/sshd", "-D"]
gerard@sirius:~/build$ 
```

Creamos la imagen usando el *Dockerfile* antes mencionado, siguiendo el mismo procedimiento de la versión básica. Le ponemos un *tag* distinto para tener ambas imágenes funcionales.

```bash
gerard@sirius:~/build$ docker build -f Dockerfile.shell -t gitserver:shell .
Sending build context to Docker daemon 53.25 kB
Step 1 : FROM debian:jessie
 ---> bb5d89f9b6cb
Step 2 : RUN apt-get update &&     apt-get install -y git openssh-server &&     mkdir /var/run/sshd
 ---> Using cache
 ---> e88e644b0a53
Step 3 : RUN useradd git -G sudo -s /usr/bin/git-shell -m &&     echo "git:git" | chpasswd &&     mkdir /home/git/git-shell-commands
 ---> Running in 387d2791d63f
 ---> 0ab419cdfc2d
Removing intermediate container 387d2791d63f
Step 4 : COPY create destroy /home/git/git-shell-commands/
 ---> e1aa5fa9cb44
Removing intermediate container 92fd282c6979
Step 5 : RUN cp /usr/share/doc/git/contrib/git-shell-commands/help /home/git/git-shell-commands/ &&     cp /usr/share/doc/git/contrib/git-shell-commands/list /home/git/git-shell-commands/ &&     chmod 755 /home/git/git-shell-commands/*
 ---> Running in 45ed8f24a547
 ---> 2237b87165bc
Removing intermediate container 45ed8f24a547
Step 6 : CMD /usr/sbin/sshd -D
 ---> Running in b94b8c1ddf8a
 ---> e484e1465480
Removing intermediate container b94b8c1ddf8a
Successfully built e484e1465480
gerard@sirius:~/build$ 
```

Lanzamos una instancia de la imagen creada. Es importante cambiar el puerto; puesto que el 22222 está ocupado por la instancia anterior, usaré el siguiente.

```bash
gerard@sirius:~/build$ docker run -d --name gitserver2 -h gitserver2 -p 22223:22 gitserver:shell
e732027d11b90657ff109a455f032327f0e24eebe54a7e121d86eff6eab1bc4b
gerard@sirius:~/build$ 
```

Entramos por **SSH**. Nos podemos dar cuenta de que el *prompt* ha cambiado; estamos en el **git-shell** y tenemos limitados los comandos a los que añadimos en el *Dockerfile*.

```bash
gerard@sirius:~/build$ ssh git@localhost -p 22223
git@localhost's password: 

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Run 'help' for help, or 'exit' to leave.  Available commands:
create
destroy
list
git> 
```

Usamos el comando *create* para crear el repositorio y verificamos que está usando el comando *list*. Tendríamos disponible el comando *destroy*, pero de momento no lo vamos a utilizar.

```bash
git> create myrepo2
Initialized empty Git repository in /home/git/myrepo2.git/
[OK] Repository myrepo2 created
git> list
myrepo2.git
git> exit
Connection to localhost closed.
gerard@sirius:~/build$ 
```

Verificamos que funciona, clonando el repositorio como hemos hecho antes.

```bash
gerard@sirius:~/build$ git clone ssh://git@localhost:22223/home/git/myrepo2.git
Cloning into 'myrepo2'...
git@localhost's password: 
warning: You appear to have cloned an empty repository.
Checking connectivity... done.
gerard@sirius:~/build$ 
```

Hacemos algunos *commits* locales y finalmente los pasamos al repositorio remoto mediante un *push*.

```bash
gerard@sirius:~/build$ cd myrepo2/
gerard@sirius:~/build/myrepo2$ echo 0.0.1 > VERSION
gerard@sirius:~/build/myrepo2$ git add VERSION
gerard@sirius:~/build/myrepo2$ git commit -m "Initial commit"
[master (root-commit) fd40f39] Initial commit
 1 file changed, 1 insertion(+)
 create mode 100644 VERSION
gerard@sirius:~/build/myrepo2$ git push -u origin master
git@localhost's password: 
Counting objects: 3, done.
Writing objects: 100% (3/3), 222 bytes | 0 bytes/s, done.
Total 3 (delta 0), reused 0 (delta 0)
To ssh://git@localhost:22223/home/git/myrepo2.git
 * [new branch]      master -> master
Branch master set up to track remote branch master from origin.
gerard@sirius:~/build/myrepo2$ cd ..
gerard@sirius:~/build$ 
```
