---
title: "Instalación de Debian desde debootstrap con debootstick"
slug: "instalacion-de-debian-desde-debootstrap-con-debootstick"
date: "2020-01-13"
categories: ['Sistemas']
tags: ['debian', 'debootstrap', 'debootstick', 'pendrive']
---

En mi cruzada por reducir la instalación de una distribución **Debian** y
conseguir hacerla repetible sigo buscando las herramientas adecuadas para
conseguirlo. Hoy le toca a una herramienta que encontré casi por casualidad
ejecutando un `apt search` rutinario que no dio el resultado esperado, pero
me dio a conocer **debootstick**.
<!--more-->

Se trata de un comando que permite empaquetar una carpeta tipo **debootstrap**
en un fichero de disco *raw* con todo lo necesario para arrancar el sistema
operativo; incluso es posible crear el sistema a partir de un contenedor **docker**.

A diferencia de [otros][1] [intentos][2] de este blog, que se basan en la creación
de *livecd* de manera manual y con el sistema de ficheros comprimidos, esta
herramienta intenta hacer una distribución sin comprimir y con capacidad para
actualizarse a futuro, como si de una instalación normal se tratara; solo que
su objetivo no es acabar en un CD, sino en un disco o un *pendrive*.

## Lo más básico

Lo primero que vamos a necesitar es el paquete **debootstick** y un entorno
tipo **chroot**. Como no tengo este entorno disponible, voy a instalar también
la herramienta **debootstrap**, que asegura que el resultado sea compatible
con **debootstick**.

```bash
gerard@builder:~$ sudo apt install debootstrap debootstick
...
gerard@builder:~$ 
```

Si leemos [la documentación][3], veremos que crear nuestra imagen no es nada
complicado; basta con tener un entorno **debootstrap** y ejecutar **debootstick**:

```bash
> sudo debootstrap buster rootfs
> sudo debootstick rootfs disk.img
```

Esto es suficiente para obtener un disco *raw* en el fichero `disk.img`, que
tiene capacidad para arrancar nuestras máquinas, aunque su uso depende de cada
tecnología de virtualización:

* **Máquina física** &rarr; Hay que copiar byte a byte la imagen a nuestro dispositivo.
* **KVM** y **QEMU** &rarr; Estos servicios trabajan directamente con discos *raw*.
* **VirtualBox** &rarr; Podemos escribir un disco virtual nuevo, o convertir el disco a VDI.

Aquí hay añadir algunas advertencias:

* Si creamos el entorno **debootstrap** con el *flag* `--variant=minbase`, no lleva servicio de red y se quedará sin configurar.
* El entorno **debootstrap** no incluye ningún usuario usable, y **root** viene bloqueado de serie.
* El entorno **debootstrap** no define un *hostname* para la máquina nueva, así que **debootstick** copia el del sistema creador.

**TRUCO**: Podemos modificar la jaula *chroot* manualmente o confiar en los
parámetros `--config-hostname` y `--config-root-password*` del comando **debootstick**.

## Una instalación un poco más útil

Veamos como quedaría una instalación algo más completa, pero relativamente simple:

Para ello necesitamos un servidor estándar con SSH y un usuario de trabajo, porque
la configuración estándar de SSH prohibe el uso directo del usuario **root**.
Como vamos a dejar el usuario **root** bloqueado, vamos a darle al usuario permisos
para hacer **sudo** libremente.

```bash
gerard@builder:~$ sudo debootstrap --include=openssh-server,sudo,dbus buster rootfs
...
I: Base system installed successfully.
gerard@builder:~$ 
```

**TRUCO**: Otro tema interesante es que un **debootstrap** no lleva el servicio **dbus**,
y eso causa una serie de *warnings* algo molestos, que podemos evitar con dicho paquete.

Por defecto, el usuario **root** viene bloqueado y el servicio SSH evita que pudiera
entrar si no lo estuviera. Podemos desbloquear el usuario **root** y permitirle hacer
SSH, o podemos utilizar un usuario auxiliar con permisos de **sudo**, que es lo que
voy a hacer, al estilo de **Ubuntu**; solo es necesario que pertenezca al grupo **sudo**.

```bash
gerard@builder:~$ sudo chroot rootfs useradd -G sudo -m -s /bin/bash gerard
gerard@builder:~$ sudo chroot rootfs passwd gerard
New password: 
Retype new password: 
passwd: password updated successfully
gerard@builder:~$ 
```

En este punto, la configuración de red brilla por su ausencia, y sin ella, no vamos a
poder entrar por SSH a nuestro nuevo servidor. Igual tenemos un monitor para hacer la
configuración localmente, pero lo más cómodo es poner ahora una configuración básica.

```bash
gerard@builder:~$ cat rootfs/etc/network/interfaces
auto lo
iface lo inet loopback

allow-hotplug enp0s3
iface enp0s3 inet dhcp
gerard@builder:~$ 
```

**TRUCO**: El nombre de las interfaces de red depende de cada *hardware*. Voy a
utilizar los que tendrá cuando ejecute en una máquina **VirtualBox**, que además,
coincide con las de la máquina en la que estoy construyendo la imagen.

Solo nos queda empaquetar el disco *raw*. Le daré un nombre porque el de la máquina
de construcción no me gusta (podría haber creado un fichero `rootfs/etc/hostname`
de forma manual, pero así es más cómodo).

```bash
gerard@builder:~$ sudo debootstick --config-hostname debian rootfs debian.img
...
I: debian.img ready (size: 692M). 
gerard@builder:~$ 
```

**TRUCO**: No es necesario limpiar la *cache* o las listas de APT; esto lo hace **debootstick**.

## Uso de nuestra nueva imagen

En este momento tenemos un fichero `debian.img` que podemos guardar con llave e ir
copiando según nos convenga. Su tamaño es el mínimo necesario, unos 692mb en mi caso.

### Uso virtualizado

Este empaquetado intentará redimensionar el disco para ocupar todo el espacio
disponible tras el primer arranque. Podemos incrementar el tamaño del "disco" con el
comando `truncate`, o modificar el tamaño del disco en el servicio de virtualización.

```bash
gerard@desktop:~/workspace$ truncate -s 2G debian.img
gerard@desktop:~/workspace$ 
```

En el caso de usar **VirtualBox**, como este no trabaja con discos *raw*, necesitamos
hacer una conversión de formato, con el comando `VBoxManage`:

```bash
gerard@desktop:~/workspace$ VBoxManage convertfromraw debian.img debian.vdi
Converting from raw image file="debian.img" to file="debian.vdi"...
Creating dynamic image with size 2147483648 bytes (2048MB)...
gerard@desktop:~/workspace$ 
```

Y ya podríamos añadirlo a una máquina virtual.

### Uso físico

Si pretendemos utilizar un disco físico, sea un disco duro o un *pendrive*,
solo necesitamos hacer una copia byte a byte, con el comando `dd`:

```bash
> sudo dd if=disk.img of=/dev/sdb
```

**WARNING**: La operación es destructiva con el disco `/dev/sdb`. Aseguráos
de que es el disco correcto o podéis tener pérdidas de datos importantes.

Solo faltaría arrancar desde este disco, y normalmente esto se hace desde la BIOS,
o directamente cambiando el disco de máquina. Esto queda como deberes para el lector.

[1]: {{< relref "/articles/2015/12/creacion-de-un-livecd-con-debian.md" >}}
[2]: {{< relref "/articles/2019/04/ensamblando-un-livecd-con-debian-y-xorriso.md" >}}
[3]: https://github.com/drakkar-lig/debootstick
