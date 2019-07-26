---
title: "Compartiendo carpetas con NFS"
slug: "compartiendo-carpetas-con-nfs"
date: 2017-02-06
categories: ['Sistemas']
tags: ['linux', 'debian', 'jessie', 'NFS']
---

Son muchas las veces que queremos tener una carpeta disponible en todas las máquinas que usamos habitualmente, sea una unidad de *backup*, o sea una carpeta de intercambio de fotos. Disponemos de servidores tipo FTP, pero es mas cómodo tener una unidad remota como una carpeta mas de nuestra máquina.<!--more-->

Para esta guía, vamos a utilizar dos máquinas *Debian Jessie*, actuando como el servidor (el que tiene las carpetas compartidas) y como el cliente (el ordenador de un usuario concreto).

Un *setup* mas realista sería poner el servidor en un servidor casero (tipo *Raspberry Pi*), mientras que los ordenadores cliente serían los de los diferentes usuarios de casa.

**CUIDADO**: El servidor NFS de *linux* va por *kernel*, así que nos os va a funcionar desde un contenedor, por ejemplo *LXC* o *Docker*. En este caso, las máquinas disponen de *kernel* completo, porque se han utilizado *VirtualBox*.

Así pues, disponemos de 2 máquinas:

* **server** &rarr; 10.0.0.2
* **client** &rarr; 10.0.0.3

## Preparando el servidor

Para preparar el servidor, necesitamos instalar el paquete que provee el servidor de **NFS**, que en este caso es **nfs-kernel-server**.

```bash
root@server:~# apt-get install -y nfs-kernel-server
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes extras:
  file libevent-2.0-5 libldap-2.4-2 libmagic1 libnfsidmap2 libpython-stdlib libpython2.7-minimal libpython2.7-stdlib libsasl2-2
  libsasl2-modules libsasl2-modules-db libsqlite3-0 libtirpc1 mime-support nfs-common python python-minimal python2.7
  python2.7-minimal rpcbind
Paquetes sugeridos:
  libsasl2-modules-otp libsasl2-modules-ldap libsasl2-modules-sql libsasl2-modules-gssapi-mit libsasl2-modules-gssapi-heimdal
  open-iscsi watchdog python-doc python-tk python2.7-doc binutils binfmt-support
Se instalarán los siguientes paquetes NUEVOS:
  file libevent-2.0-5 libldap-2.4-2 libmagic1 libnfsidmap2 libpython-stdlib libpython2.7-minimal libpython2.7-stdlib libsasl2-2
  libsasl2-modules libsasl2-modules-db libsqlite3-0 libtirpc1 mime-support nfs-common nfs-kernel-server python python-minimal
  python2.7 python2.7-minimal rpcbind
0 actualizados, 21 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 6.072 kB de archivos.
Se utilizarán 23,7 MB de espacio de disco adicional después de esta operación.
...
root@server:~#
```

Supongamos que queremos compartir la carpeta */shared/*, lo que significa que tenemos que crearla si no existiera, y hay que darle los permisos adecuados al uso que se le vaya a dar. A modo de ejemplo, vamos a dar todos los permisos posibles a todo el mundo.

```bash
root@server:~# mkdir /shared
root@server:~# chmod 777 /shared/
root@server:~#
```

Vamos a declarar este punto *exportable*, con permisos de escritura para las máquinas que lo necesiten.

```bash
root@server:~# cat /etc/exports
/shared 10.0.0.3(rw,sync)
root@server:~#
```

Finalmente hacemos un *restart* o un *reload* del servicio de **NFS** para que recargue la configuración.

**AVISO**: Este servicio no arranca en contenedores.

```bash
root@server:~# systemctl restart nfs-kernel-server
root@server:~#
```

Y con esto ya tenemos nuestra carpeta *exportable* disponible para los clientes definidos en */etc/exports*.

## Preparando una de las máquinas cliente

El primer paso consiste en instalar el paquete **nfs-common**, que nos va a proveer de las utilidades necesarias para montar el sistema de ficheros remoto.

```bash
root@client:~# apt-get install -y nfs-common
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes extras:
  file libevent-2.0-5 libldap-2.4-2 libmagic1 libnfsidmap2 libpython-stdlib libpython2.7-minimal libpython2.7-stdlib libsasl2-2
  libsasl2-modules libsasl2-modules-db libsqlite3-0 libtirpc1 mime-support python python-minimal python2.7 python2.7-minimal
  rpcbind
Paquetes sugeridos:
  libsasl2-modules-otp libsasl2-modules-ldap libsasl2-modules-sql libsasl2-modules-gssapi-mit libsasl2-modules-gssapi-heimdal
  open-iscsi watchdog python-doc python-tk python2.7-doc binutils binfmt-support
Se instalarán los siguientes paquetes NUEVOS:
  file libevent-2.0-5 libldap-2.4-2 libmagic1 libnfsidmap2 libpython-stdlib libpython2.7-minimal libpython2.7-stdlib libsasl2-2
  libsasl2-modules libsasl2-modules-db libsqlite3-0 libtirpc1 mime-support nfs-common python python-minimal python2.7
  python2.7-minimal rpcbind
0 actualizados, 20 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 5.954 kB de archivos.
Se utilizarán 23,3 MB de espacio de disco adicional después de esta operación.
...
root@client:~#
```

Creamos un punto de montaje para la carpeta remota, en caso de necesitarla.

```bash
root@client:~# mkdir /compartida
root@client:~#
```

Y montamos la carpeta remota, usando las herramientas estándar.

```bash
root@client:~# mount -t nfs 10.0.0.2:/shared /compartida
root@client:~#
```

Si nos gustara el resultado, podemos hacer el montaje automático añadiendo una línea en */etc/fstab*, que podéis copiar tal cual de */etc/mtab* cuando la carpeta remota esté montada.

## Algunas pruebas de funcionamiento

Partimos de una carpeta compartida vacía, y vemos que también está vacía en el cliente.

```bash
root@server:~# ls /shared/
root@server:~#

root@client:~# ls /compartida/
root@client:~#
```

Ahora podemos crear un fichero cualquiera en la máquina cliente.

```bash
root@client:~# touch /compartida/client_data
root@client:~#
```

Podemos ver que no hay ningún problema por trabajar en la carpeta desde otra máquina, por ejemplo, creando un fichero en la máquina servidor.

```bash
root@server:~# touch /shared/server_data
root@server:~#
```

Finalmente vemos que la carpeta, sea la carpeta local del servidor o la carpeta montada remotamente del cliente, reflejan ambos cambios aplicados anteriormente.

```bash
root@server:~# ls /shared/
client_data  server_data
root@server:~#

root@client:~# ls /compartida/
client_data  server_data
root@client:~#
```

Y con esto vemos que funciona como debe.
