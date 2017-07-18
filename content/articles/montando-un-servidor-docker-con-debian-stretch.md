Title: Montando un servidor docker con Debian Stretch
Slug: montando-un-servidor-docker-con-debian-stretch
Date: 2017-07-24 10:00
Category: Sistemas
Tags: linux, debian, stretch, docker, docker-compose



Finalmente ha sucedido: ha llegado el esperado lanzamiento de **Debian Stretch**. Como buen linuxero no me he podido resistir a hacer alguna instalación para probar, aunque solo sea como una máquina virtual. Su función, determinada por mi actual flujo de trabajo, va a ser como servidor de **docker** con **docker-compose**.

En este caso, lo necesito para mi uso personal, pero en el ámbito de mi trabajo. Una de las particularidades a las que me enfrento es un *proxy* **squid** no transparente, así que también voy a ponerlo como anotaciones en el artículo.

## El servidor base

Se trata de instalar un sistema operativo básico con SSH, partiendo de la imagen *netinst*, que considero suficiente para un servidor estándar, y me evita descargar una *iso* más grande.

No voy a explicar como se instala; simplemente he respondido las preguntas de la instalación tal como me las hacía. Solo hace falta tener en cuenta que se eligió el servidor **SSH** durante la instalación (concretamente en el *tasksel*) y que se indicó el *proxy* cuando se me preguntó.

Para evitar que la operación **apt-get update** tarde más tiempo de lo debido, vamos a limpiar el fichero */etc/apt/sources.list*, eliminando las entradas que no nos interesen.

Y ya para acabar, vamos a crear una carpeta *bin* para nuestro usuario de trabajo, lo que hace especialmente fácil poner *scripts* locales para el mismo usuario.

```bash
gerard@atlantis:~$ mkdir bin
gerard@atlantis:~$
```

## Instalar docker engine y docker-compose

### Docker engine

Para instalar **docker engine** vamos a seguir [la documentación](https://docs.docker.com/engine/installation/linux/docker-ce/debian/). El primer paso es descargarse la clave oficial GPG de **docker**, para que **apt** confíe en la fuente de *software*.

**NOTA**: es probable que el comando **wget** falle si estamos detrás de un *proxy*; basta con exportar la variable de entorno **https_proxy**.

```bash
root@atlantis:~# apt-get install apt-transport-https
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
...
root@atlantis:~# wget -qO- https://download.docker.com/linux/debian/gpg | apt-key add -
OK
root@atlantis:~#
```

Añadimos la línea adecuada para usar el repositorio oficial de **docker** y, tras hacer el correspondiente *update*, instalamos el paquete **docker-ce**.

```bash
root@atlantis:~# echo "deb https://download.docker.com/linux/debian stretch stable" > /etc/apt/sources.list.d/docker.list
root@atlantis:~# apt-get update
Obj:1 http://security.debian.org/debian-security stretch/updates InRelease
Des:2 https://download.docker.com/linux/debian stretch InRelease [20,2 kB]
Des:3 https://download.docker.com/linux/debian stretch/stable amd64 Packages [1.934 B]
Ign:4 http://ftp.fr.debian.org/debian stretch InRelease
Des:5 http://ftp.fr.debian.org/debian stretch-updates InRelease [88,5 kB]
Obj:6 http://ftp.fr.debian.org/debian stretch Release
Descargados 111 kB en 5s (19,5 kB/s)
Leyendo lista de paquetes... Hecho
root@atlantis:~# apt-get install docker-ce
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
...
root@atlantis:~#
```

Para hacer mas fácil el acceso a **docker** para el usuario de trabajo, vamos a añadirlo al mismo grupo.

```bash
root@atlantis:~# usermod -a -G docker gerard
root@atlantis:~#
```

### Docker compose

Para instalar esta utilidad, vamos a seguir [su documentación](https://docs.docker.com/compose/install/). En esencia se limita a descargar el binario en algún lugar del *path* y a darle permisos de ejecución.

```bash
root@atlantis:~# wget -qO /usr/local/bin/docker-compose https://github.com/docker/compose/releases/download/1.14.0/docker-compose-`uname -s`-`uname -m`
root@atlantis:~# chmod 755 /usr/local/bin/docker-compose
root@atlantis:~#
```

## Sobre los servidores proxy

Trabajar detrás de un servidor *proxy* es un problema cuando trabajamos con **docker**, ya que el *proxy* debe configurarse a nivel de servicio, luego debe especificarse en cada *docker build* y finalmente en cada *docker run*.

La primera configuración *proxy* necesaria es la de **apt**. Por suerte para nosotros, cuando instalamos el sistema operativo y lo indicamos ya nos guardó ese parámetro en */etc/apt/apt.conf*.

```bash
gerard@atlantis:~$ cat /etc/apt/apt.conf
Acquire::http::Proxy "http://192.168.0.2:3128";
gerard@atlantis:~$
```

A veces, algunos comandos como el **wget** necesitan definir el *proxy* como una variable de sistema; por ejemplo, para poner la variable **https_proxy** para esta sesión de terminal, podemos hacer algo como:

```bash
root@atlantis:~# export https_proxy=http://192.168.0.2:3128
root@atlantis:~#
```

El demonio de **docker** utiliza el *proxy* definido en las variables de sistema. En el caso de *systemd* podemos añadir estas variables de forma fácil añadiendo una configuración *overlay*. Esto hace necesario recargar las configuraciones para el demonio de **systemd** y luego el mismo demonio de **docker** para que utilice las nuevas variables.

```bash
root@atlantis:~# mkdir /etc/systemd/system/docker.service.d
root@atlantis:~# cat /etc/systemd/system/docker.service.d/proxy.conf
[Service]
Environment="HTTP_PROXY=http://192.168.0.2:3128"
Environment="HTTPS_PROXY=http://192.168.0.2:3128"
root@atlantis:~# systemctl daemon-reload
root@atlantis:~# systemctl restart docker
root@atlantis:~#
```

Finalmente, y por comodidad podemos añadir estas variables de entorno de forma permanente para el usuario de trabajo en el fichero *~/.bashrc*, de forma que en cada nueva sesión de SSH no tengamos que redefinirlas. Aprovechamos también para añadir algunos *alias* útiles para reducir los comandos de construcción de imágenes y ejecución de contenedores, escondiendo las variables del *proxy*.

```bash
gerard@atlantis:~$ cat .bashrc
...
alias drun='docker run -e "http_proxy=http://192.168.0.2:3128" -e "https_proxy=http://192.168.0.2:3128"'
alias dbuild='docker build --build-arg="http_proxy=http://192.168.0.2:3128" --build-arg="https_proxy=http://192.168.0.2:3128"'
export HTTP_PROXY=http://192.168.0.2:3128
export HTTPS_PROXY=${HTTP_PROXY}
export http_proxy=${HTTP_PROXY}
export https_proxy=${HTTP_PROXY}
export NO_PROXY="127.0.0.1,localhost"
export no_proxy=${NO_PROXY}
gerard@atlantis:~$
```

## Siguientes pasos

Es probable que este servidor necesite algunas utilidades que no hayan venido con los paquetes base. Nada nos impide ponerlos nosotros a mano, con los correspondientes *apt-get install*. A partir de aquí, solo nos queda disfrutar de nuestro nuevo servidor **docker** mínimo.
