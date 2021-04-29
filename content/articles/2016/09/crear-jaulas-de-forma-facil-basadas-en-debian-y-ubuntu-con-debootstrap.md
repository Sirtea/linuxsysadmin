---
title: "Crear jaulas de forma fácil basadas en Debian y Ubuntu con debootstrap"
slug: "crear-jaulas-de-forma-facil-basadas-en-debian-y-ubuntu-con-debootstrap"
date: 2016-09-19
categories: ['Seguridad']
tags: ['linux', 'debian', 'ubuntu', 'debootstrap', 'jaula']
---

Cuando creamos jaulas nos enfrentamos siempre al mismo dilema: usar una imagen de dudoso origen o perder nuestro tiempo investigando y buscando librerías que falten. Sin embargo, hay una forma mejor, que es descargar un sistema básico con herramientas oficiales que nos van a dar hasta un gestor de paquetes.<!--more-->

Hay algunas distribuciones que nos ofrecen herramientas para descargar un sistema base a partir de sus repositorios, y que a menudo son la base de sus propias instalaciones. En el caso de las distribuciones **Debian** y derivadas (**Ubuntu**, **Knoppix**, ...) esta herramienta se llama **debootstrap** y de uso bastante sencillo.

De hecho, otras herramientas parten de estas herramientas para usar como base para las suyas. Un ejemplo serían las imágenes de **docker**, que no son mas que el resultado de la ejecución de **debootstrap**.

Este tutorial se ha ejecutado en un contenedor **docker** de usar y tirar, para no polucionar mi máquina con herramientas innecesarias. También se asume que se dispone de la herramienta instalada que, por si no la tuvierais, se instala así:

```bash
root@8e7b4f301aa0:~# apt-get install debootstrap
Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following extra packages will be installed:
  ca-certificates libffi6 libgmp10 libgnutls-deb0-28 libhogweed2 libicu52 libidn11 libnettle4 libp11-kit0 libpsl0 libssl1.0.0 libtasn1-6 openssl wget
Suggested packages:
  gnutls-bin
The following NEW packages will be installed:
  ca-certificates debootstrap libffi6 libgmp10 libgnutls-deb0-28 libhogweed2 libicu52 libidn11 libnettle4 libp11-kit0 libpsl0 libssl1.0.0 libtasn1-6 openssl wget
0 upgraded, 15 newly installed, 0 to remove and 0 not upgraded.
Need to get 10.8 MB of archives.
After this operation, 39.1 MB of additional disk space will be used.
Do you want to continue? [Y/n] y
...
root@8e7b4f301aa0:~# 
```

Esta herramienta viene acompañada de los diferentes *scripts* que conocen la forma de llegar al resultado deseado. Cabe remarcar que cuando mas reciente es la versión, mas *scripts* lleva incorporados. En mi caso, usé **Debian Jessie**, que como podéis ver, sabe construir **Ubuntu 9.10 (Karmic Koala)**, pero no **Ubuntu 16.04 (Xenial Xerus)**.

```bash
root@8e7b4f301aa0:~# dpkg -L debootstrap | grep scripts
/usr/share/debootstrap/scripts
/usr/share/debootstrap/scripts/hoary
/usr/share/debootstrap/scripts/woody.buildd
/usr/share/debootstrap/scripts/feisty
/usr/share/debootstrap/scripts/warty.buildd
/usr/share/debootstrap/scripts/potato
/usr/share/debootstrap/scripts/sarge.fakechroot
/usr/share/debootstrap/scripts/hoary.buildd
/usr/share/debootstrap/scripts/gutsy
/usr/share/debootstrap/scripts/warty
/usr/share/debootstrap/scripts/sarge
/usr/share/debootstrap/scripts/sid
/usr/share/debootstrap/scripts/sarge.buildd
/usr/share/debootstrap/scripts/edgy
/usr/share/debootstrap/scripts/dapper
/usr/share/debootstrap/scripts/breezy
/usr/share/debootstrap/scripts/woody
/usr/share/debootstrap/scripts/saucy
/usr/share/debootstrap/scripts/testing
/usr/share/debootstrap/scripts/unstable
/usr/share/debootstrap/scripts/oneiric
/usr/share/debootstrap/scripts/stretch
/usr/share/debootstrap/scripts/stable
/usr/share/debootstrap/scripts/etch-m68k
/usr/share/debootstrap/scripts/maverick
/usr/share/debootstrap/scripts/raring
/usr/share/debootstrap/scripts/lenny
/usr/share/debootstrap/scripts/hardy
/usr/share/debootstrap/scripts/wheezy
/usr/share/debootstrap/scripts/squeeze
/usr/share/debootstrap/scripts/etch
/usr/share/debootstrap/scripts/oldstable
/usr/share/debootstrap/scripts/precise
/usr/share/debootstrap/scripts/trusty
/usr/share/debootstrap/scripts/utopic
/usr/share/debootstrap/scripts/natty
/usr/share/debootstrap/scripts/jaunty
/usr/share/debootstrap/scripts/jessie
/usr/share/debootstrap/scripts/lucid
/usr/share/debootstrap/scripts/intrepid
/usr/share/debootstrap/scripts/quantal
/usr/share/debootstrap/scripts/karmic
/usr/share/debootstrap/scripts/vivid
root@8e7b4f301aa0:~# 
```

**TRUCO**: Para ejecutar **debootstrap** en un contenedor **docker** (de usar y tirar, por ejemplo), hace falta correr el contenedor con un *flag* especial: *--privileged*. Esto es debido a que **debootstrap** intenta montar el sistema de ficheros */proc* y no dispone de permisos para hacerlo en circunstancias normales.

## Un ejemplo de uso básico

A priori, este comando solo necesita saber la distribución que queremos descargar y la carpeta donde lo queremos hacer.

```bash
root@8e7b4f301aa0:~# debootstrap jessie jail
...
root@8e7b4f301aa0:~# 
```

Podemos contar con varios *flags* que van a modificar ligeramente su comportamiento. A lo largo del tutorial vamos a utilizar el *flag --variant=minbase* que va a descargar menos paquetes todavía, acelerando su ejecución. Yo suelo usar siempre este *flag*, porque al instalar con *apt-get* otros paquetes, ya se incorporarían las dependencias.

```bash
root@8e7b4f301aa0:~# debootstrap --variant=minbase jessie jail 
I: Retrieving Release 
I: Retrieving Release.gpg 
I: Checking Release signature
I: Valid Release signature (key id 75DDC3C4A499F1A18CB5F3C8CBF8D6FD518E17E1)
I: Retrieving Packages 
I: Validating Packages 
I: Resolving dependencies of required packages...
I: Resolving dependencies of base packages...
I: Found additional required dependencies: acl adduser dmsetup insserv libaudit-common libaudit1 libbz2-1.0 libcap2 libcap2-bin libcryptsetup4 libdb5.3 libdebconfclient0 libdevmapper1.02.1 libgcrypt20 libgpg-error0 libkmod2 libncursesw5 libprocps3 libsemanage-common libsemanage1 libslang2 libsystemd0 libudev1 libustr-1.0-1 procps systemd systemd-sysv udev 
I: Found additional base dependencies: debian-archive-keyring gnupg gpgv libapt-pkg4.12 libreadline6 libstdc++6 libusb-0.1-4 readline-common 
I: Checking component main on http://ftp.us.debian.org/debian...
...
I: Base system installed successfully.
root@8e7b4f301aa0:~# 
```

Tras ejecutar el comando, podemos ver que tenemos una carpeta *jail/* en donde podemos encontrar un sistema **Linux** bastante estándar, que corresponde con la distribución **Debian Jessie** pedida.

```bash
root@8e7b4f301aa0:~# ls -1 jail/
bin
boot
dev
etc
home
lib
lib64
media
mnt
opt
proc
root
run
sbin
srv
sys
tmp
usr
var
root@8e7b4f301aa0:~# 
```

Vemos que la instalación es bastante básica y tiene un tamaño reducido, ya que solo lleva lo mas básico, sin *kernel* y sin *bootloader*. Por no llevar, no lleva ni **nano** ni **vi**, por ejemplo. Usad *apt-get* para instalar los paquetes que veáis necesarios, una vez dentro de la jaula.

```bash
root@8e7b4f301aa0:~# du -sh jail/
202M	jail/
root@8e7b4f301aa0:~# 
```

De hecho, mucho de lo que hay en la jaula son ficheros de *apt-get*, que sirven para acelerar la operación normal de estas herramientas, pero que resultan inútiles si queremos una imagen mínima. Son ficheros que vuelven a aparecer con el uso normal de *apt-get* y que van cambiando con el tiempo. Como se trata de la caché de paquetes descargados y de los índices de los repositorios, nos los cargamos.

```bash
root@8e7b4f301aa0:~# chroot jail/ apt-get clean
root@8e7b4f301aa0:~# rm -rf jail/var/lib/apt/lists/*
root@8e7b4f301aa0:~# 
```

Esto libera un 33% del espacio ocupado. Ahora sería un buen momento para sacar un fichero comprimido para guardar la imagen.

```bash
root@8e7b4f301aa0:~# du -sh jail/
136M	jail/
root@8e7b4f301aa0:~# 
```

**TRUCO**: Si la carpeta *jail/* estuviera mapeada a un dispositivo tendríamos un disco de sistema operativo casi completo. Bastaría con instalarle un *kernel* y un *bootloader* para tener un sistema operativo funcional.

## Haciendo un fichero comprimido de paquetes descargados

Si la idea de ir copiando la jaula anterior no nos convence, podemos tener los paquetes *.deb* descargados y comprimidos en un fichero *.tar.gz*, para no tener que descargar todos los paquetes cada vez. Basta con poner el *flag* `--make-tarball`. En este caso, la carpeta de descarga es una carpeta temporal, que va a ser eliminada al terminar.

```bash
root@8e7b4f301aa0:~# debootstrap --variant=minbase --make-tarball=debian-jessie.tgz jessie temporal
I: Retrieving Release 
I: Retrieving Release.gpg 
I: Checking Release signature
I: Valid Release signature (key id 75DDC3C4A499F1A18CB5F3C8CBF8D6FD518E17E1)
I: Retrieving Packages 
I: Validating Packages 
I: Resolving dependencies of required packages...
I: Resolving dependencies of base packages...
I: Found additional required dependencies: acl adduser dmsetup insserv libaudit-common libaudit1 libbz2-1.0 libcap2 libcap2-bin libcryptsetup4 libdb5.3 libdebconfclient0 libdevmapper1.02.1 libgcrypt20 libgpg-error0 libkmod2 libncursesw5 libprocps3 libsemanage-common libsemanage1 libslang2 libsystemd0 libudev1 libustr-1.0-1 procps systemd systemd-sysv udev 
I: Found additional base dependencies: debian-archive-keyring gnupg gpgv libapt-pkg4.12 libreadline6 libstdc++6 libusb-0.1-4 readline-common 
I: Checking component main on http://ftp.us.debian.org/debian...
...
I: Deleting target directory
root@8e7b4f301aa0:~# 
```

Finalmente obtenemos nuestro fichero comprimido, que es mas fácil de copiar a diferentes máquinas, por tamaño y por velocidad de transmisión.

```bash
root@8e7b4f301aa0:~# du -sh debian-jessie.tgz 
43M	debian-jessie.tgz
root@8e7b4f301aa0:~# 
```

Este fichero contiene solamente los ficheros que descartamos al final del proceso, que son los *.deb* ya instalados y los índices del repositorio.

```bash
root@8e7b4f301aa0:~# tar tf debian-jessie.tgz | grep \/$
var/lib/apt/
var/lib/apt/lists/
var/lib/apt/lists/partial/
var/cache/apt/
var/cache/apt/archives/
var/cache/apt/archives/partial/
root@8e7b4f301aa0:~# tar tf debian-jessie.tgz | head
var/lib/apt/
var/lib/apt/lists/
var/lib/apt/lists/debootstrap.invalid_dists_jessie_main_binary-amd64_Packages
var/lib/apt/lists/debootstrap.invalid_dists_jessie_Release.gpg
var/lib/apt/lists/partial/
var/lib/apt/lists/debootstrap.invalid_dists_jessie_Release
var/cache/apt/
var/cache/apt/archives/
var/cache/apt/archives/libbz2-1.0_1.0.6-7+b3_amd64.deb
var/cache/apt/archives/bash_4.3-11+b1_amd64.deb
root@8e7b4f301aa0:~# 
```

Cuando queramos utilizar este fichero comprimido para crear una jaula, basta con indicar que use los paquetes en el fichero, mediante el *flag* `--unpack-tarball`.

```bash
root@8e7b4f301aa0:~# debootstrap --variant=minbase --unpack-tarball=/root/debian-jessie.tgz jessie rootfs
I: Retrieving Release 
I: Retrieving Release.gpg 
I: Checking Release signature
I: Valid Release signature (key id 75DDC3C4A499F1A18CB5F3C8CBF8D6FD518E17E1)
I: Validating Packages 
I: Resolving dependencies of required packages...
I: Resolving dependencies of base packages...
I: Found additional required dependencies: acl adduser dmsetup insserv libaudit-common libaudit1 libbz2-1.0 libcap2 libcap2-bin libcryptsetup4 libdb5.3 libdebconfclient0 libdevmapper1.02.1 libgcrypt20 libgpg-error0 libkmod2 libncursesw5 libprocps3 libsemanage-common libsemanage1 libslang2 libsystemd0 libudev1 libustr-1.0-1 procps systemd systemd-sysv udev 
I: Found additional base dependencies: debian-archive-keyring gnupg gpgv libapt-pkg4.12 libreadline6 libstdc++6 libusb-0.1-4 readline-common 
I: Checking component main on http://ftp.us.debian.org/debian...
...
I: Base system installed successfully.
root@8e7b4f301aa0:~# 
```

Este proceso sigue necesitando de conexión a internet, porque consulta al índice del repositorio para saber que paquetes necesita. Sin embargo, estos paquetes ya los tenemos, con lo que es un proceso bastante mas rápido y menos estresante para nuestra red.

## Construyendo una jaula para otra máquina

Supongamos ahora que tenemos una máquina que es de otra arquitectura y le descargamos el sistema de ficheros en nuestro local. Normalmente no sería posible ya que podemos descargar los ficheros *.deb* de la otra arquitectura, pero no podemos configurar los paquetes porque para esto se necesita ejecutar binarios que, por supuesto, no funcionan en nuestro local.

El comando **debootstrap** también nos permite esto. La idea está en "dejar listo" una estructura, de forma que solo haga falta copiar en destino y configurar los paquetes. Esto es tan fácil como indicar el *flag* `--foreign`, y adicionalmente, indicar la arquitectura deseada con `--arch`.

```bash
root@8e7b4f301aa0:~# debootstrap --variant=minbase --arch=armhf --foreign jessie rootfs
I: Retrieving Release 
I: Retrieving Release.gpg 
I: Checking Release signature
I: Valid Release signature (key id 75DDC3C4A499F1A18CB5F3C8CBF8D6FD518E17E1)
I: Retrieving Packages 
I: Validating Packages 
I: Resolving dependencies of required packages...
I: Resolving dependencies of base packages...
I: Found additional required dependencies: acl adduser dmsetup insserv libaudit-common libaudit1 libbz2-1.0 libcap2 libcap2-bin libcryptsetup4 libdb5.3 libdebconfclient0 libdevmapper1.02.1 libgcrypt20 libgpg-error0 libkmod2 libncursesw5 libprocps3 libsemanage-common libsemanage1 libslang2 libsystemd0 libudev1 libustr-1.0-1 procps systemd systemd-sysv udev 
I: Found additional base dependencies: debian-archive-keyring gnupg gpgv libapt-pkg4.12 libreadline6 libstdc++6 libusb-0.1-4 readline-common 
I: Checking component main on http://ftp.us.debian.org/debian...
...
root@8e7b4f301aa0:~# 
```

Esto nos deja un sistema "a medias", con un *script* que nos permita continuar a partir de este punto, una vez hayamos copiado la estructura generada en destino.

Si miramos el sistema de ficheros, veremos que se trata de la jaula casi acabada, con una carpeta *debootstrap/* que contiene lo necesario para continuar, incluido el *script* llamado *debootstrap*.

```bash
root@8e7b4f301aa0:~# ls rootfs/debootstrap/
arch  base  debootstrap  debootstrap.log  debpaths  devices.tar.gz  functions  required  suite	suite-script  variant
root@8e7b4f301aa0:~# 
```

Para continuar el proceso en la nueva máquina, tenemos que copiar en ella toda la carpeta `rootfs/`. Solo nos quedará usar `chroot` para entrar en la jaula y ejecutar el *script* para configurar lo que falte y eliminar las herramientas intermedias. Este proceso no requiere conexión a internet.

```bash
root@odroid:~# chroot rootfs/
# /debootstrap/debootstrap --second-stage
I: Keyring file not available at /usr/share/keyrings/debian-archive-keyring.gpg; switching to https mirror https://mirrors.kernel.org/debian
I: Installing core packages...
I: Unpacking required packages...
...
I: Base system installed successfully.
# 
```

Y finalmente podemos disfrutar de nuestra jaula en la nueva máquina.

```bash
# ls
bin  boot  dev	etc  home  lib	lib64  media  mnt  opt	proc  root  run  sbin  srv  sys  tmp  usr  var
# 
```
