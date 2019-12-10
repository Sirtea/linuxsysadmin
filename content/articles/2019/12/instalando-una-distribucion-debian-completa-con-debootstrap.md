---
title: "Instalando una distribución Debian completa con debootstrap"
slug: "instalando-una-distribucion-debian-completa-con-debootstrap"
date: "2019-12-10"
categories: ['Sistemas']
tags: ['linux', 'debian', 'buster', 'debootstrap', 'instalación']
---

Todos sabemos que podemos construir jaulas enteras de **Debian** con una
herramienta propia llamada **debootstrap**, pero pocos saben que es la misma
con la que se instala la distribución si usamos el instalador oficial que viene
en los CDs descargables. sin embargo la configuración posterior no es trivial.
<!--more-->

Empujado por la curiosidad, y tras haber hecho *live CDs* con antelación intenté
hacer una instalación simple si utilizar el instalador, y valiéndome de las
herramientas que tenía a mano. El resultado es una distribución mínima y plenamente
funcional (a falta de instalar los servicios que necesitemos); aquí expongo
el resultado para futuras referencias.

**NOTA**: Todo el proceso se creó utilizando **VirtualBox**; eso me dio una gran
libertad para "poner", "quitar" y clonar los discos. Esa parte la tendréis que
adaptar a vuestro sistema de virtualización o *cloud* habitual.

## Las herramientas

Partiremos de una distribución estándar de **Debian** sin pretensiones (yo parto
de una instalación *netinstall*, con SSH y nada más); el único requisito es
disponer del paquete **debootstrap**, que seguramente tendremos que instalar,
puesto que no suele estar por defecto.

```bash
gerard@builder:~$ sudo apt install debootstrap
...
gerard@builder:~$ 
```

## Preparar el disco destino

La idea inicial es la de crear un sistema de ficheros raíz en un disco secundario;
este es el que luego servirá como disco primario para la máquina final. Por ello
vamos a crear un disco nuevo y lo vamos a asignar a la máquina de construcción;
no es necesaria mucha capacidad y dependerá de su función. He asignado uno de 4gb,
pero en una de las pruebas puse uno de 1gb y me sobró espacio.

Necesitamos localizar el dispositivo del nuevo disco y hay varias maneras de hacerlo:

* Hacer acto de fe y creernos que el segundo disco es `/dev/sdb`
* Localizar el disco que está sin particionar
* Verificar la capacidad para asegurar que es el nuevo

Lanzamos el comando `lsblk`, que nos permite comprobar los dos últimos métodos:

```bash
gerard@builder:~$ lsblk
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
sda      8:0    0    2G  0 disk 
└─sda1   8:1    0    2G  0 part /
sdb      8:16   0    4G  0 disk 
sr0     11:0    1 1024M  0 rom  
gerard@builder:~$ 
```

**WARNING**: En este caso, el disco es `/dev/sdb`, pero revisad esto 2 veces:
lanzar los siguientes comandos sobre el disco equivocado va a destruir todos
sus datos. Si utilizáis virtualización o *cloud*, es un buen momento para
hacer un *snapshot*.

Absolutamente todos los comandos que siguen se hacen con el usuario **root** y,
aunque va contra todas las buenas prácticas, me ahorro el comando `sudo` manteniendo
abierta una sesión de **root**.

```bash
gerard@builder:~$ sudo su -
root@builder:~# 
```

Voy a utilizar una única partición para todo el sistema y, por lo tanto, voy a
ocupar con ella todo el disco; cambiad esto a vuestro gusto. Vamos a crear la
partición con la herramienta que más os guste o que tengáis a mano:

```bash
root@builder:~# echo -e 'n\np\n1\n\n\nw' | fdisk /dev/sdb
...
root@builder:~# 
```

**TRUCO**: Si optáis por el modo interactivo sería la secuencia "n p 1 &lt;vacío&gt; &lt;vacío&gt; w".

El siguiente paso sería formatear la partición:

```bash
root@builder:~# mkfs.ext4 /dev/sdb1
...
root@builder:~# 
```

Montamos la partición en `/mnt` para poder escribir los cambios en nuestro
nuevo disco. Si tenéis varias particiones, respetad la jerarquía final, pero
con el añadido `/mnt`; así pues, si tenéis una partición para `/home`, deberíais
montarla en `/mnt/home`. Alternativamente podéis trocear en particiones después
de realizar la imagen de disco completa, de forma manual.

```bash
root@builder:~# mount /dev/sdb1 /mnt/
root@builder:~# 
```

## Crear el sistema de ficheros base

Esta es la gran función de **debootstrap**; basta con indicar la distribución que
queremos descargar y la carpeta destino en donde va a dejarlo todo. Adicionalmente,
el comando también admite una serie de paquetes extra que queramos añadir. En
nuestro caso, vamos a poner algunos más:

* **grub2** &rarr; Es el paquete del *bootloader*, es decir, el menú de selección de sistema operativo.
* **linux-image-amd64** &rarr; El *kernel* acorde con nuestra arquitectura. Normalmente no viene porque no es necesario en una jaula.
* **openssh-server** &rarr; El servidor SSH, que como estoy creando una imagen de servidor, es casi un requisito.
* **locales** &rarr; El paquete con las traducciones idiomáticas. Es opcional, pero me gusta tener una instalación en español...
* **console-setup** &rarr; Este paquete opcional permite personalizar la distribución del teclado y la codificación de la pantalla.

Sabiendo esto, lanzamos el comando:

```bash
root@builder:~# debootstrap --include=grub2,linux-image-amd64,openssh-server,locales,console-setup buster /mnt/
I: Target architecture can be executed
...
I: Base system installed successfully.
root@builder:~# 
```

**TRUCO**: Una vez instalado, el sistema no podía hacer `systemctl list-units`
porque se quejaba de no tener DBUS. Con instalar el paquete **dbus** fue suficiente.

## Configurar el sistema nuevo

Aunque **Debian** tiene una configuración por defecto excelente, siempre es
necesario hacer algunos cambios. Para ello vamos a ejecutar una serie de comandos
**dentro de la jaula**, durante todo este paso.

```bash
root@builder:~# mount -t proc /proc /mnt/proc/
root@builder:~# mount -t sysfs /sys /mnt/sys/
root@builder:~# mount -o bind /dev /mnt/dev/
root@builder:~# chroot /mnt /bin/bash
root@builder:/# 
```

### El disco inicial

Cuando el sistema operativo arranca, uno de los pasos es montar los discos.
Para ello, lee el fichero `/etc/fstab` y saca los puntos de montaje y las opciones.
Es crucial tener montado nuestro disco en la carpeta raíz, o no se podrá ejecutar
absolutamente nada, ni siquiera el proceso inicial.

Para ahorrarnos sorpresas, vamos a hacer el montaje en `/etc/fstab` usando el
identificador del disco, que podemos sacar con un simple `blkid`:

```bash
root@builder:/# blkid 
/dev/sda1: UUID="4833cc78-a8b2-4e82-8ce6-f73e5e54c165" TYPE="ext4" PARTUUID="59ebc34d-01"
/dev/sdb1: UUID="4b7bea93-6137-4640-997e-bd8af70629f3" TYPE="ext4" PARTUUID="1e3f0298-01"
root@builder:/# 
```

```bash
root@builder:/# cat /etc/fstab 
UUID=4b7bea93-6137-4640-997e-bd8af70629f3 / ext4 defaults 1 1
root@builder:/# 
```

**TRUCO**: Podemos liberar un poco de espacio en disco haciendo un `apt clean`.

### La configuración de red

Configuramos los ficheros `/etc/hostname` y `/etc/hosts` para darle a nuestro
nuevo sistema un nombre. Esto se puede cambiar en cualquier momento, pero lo
vamos haciendo para que sepa el *hostname* que le debe asignar a la máquina en
el primer *boot*.

```bash
root@builder:/# cat /etc/hostname 
debian
root@builder:/# 
```

```bash
root@builder:/# cat /etc/hosts
127.0.0.1	localhost
127.0.1.1	debian
root@builder:/# 
```

También necesitamos una configuración de red, que incluye las *interfaces* y los
servidores DNS por defecto. Esto se configura en los ficheros `/etc/network/interfaces`
y `/etc/resolv.conf`. Pongo una configuración básica y la cambiaré en un futuro.

```bash
root@builder:/# cat /etc/network/interfaces
auto lo
iface lo inet loopback

auto enp0s3
iface enp0s3 inet dhcp
root@builder:/# 
```

```bash
root@builder:/# cat /etc/resolv.conf 
nameserver 8.8.8.8
root@builder:/# 
```

**NOTA**: La configuración por DHCP va a sobreescribir el fichero `/etc/resolv.conf`
con los servidores DNS que indique la respuesta DHCP. Solo pongo uno por defecto
para el caso en el que ningún servidor DHCP responda.

### Contraseña del usuario root

Para poder entrar en el nuevo sistema, vamos a necesitar un usuario. Normalmente me
gusta la aproximación que usa **Ubuntu**, con un usuario de **root** bloqueado y un
segundo usuario con permisos de **sudo**. En este caso, para simplificar, simplemente
voy a desbloquear el usuario **root**, y eso se consigue asignándole una *password*.

```bash
root@builder:/# passwd
Nueva contraseña: 
Vuelva a escribir la nueva contraseña: 
passwd: contraseña actualizada correctamente
root@builder:/# 
```

### Zona horaria y locales (opcional)

Este paso es opcional. La zona horaria por defecto es UTC, y eso nos puede servir.
En caso de que queramos algo más personalizado, basta reconfigurar el paquete **tzdata**:

```bash
root@builder:/# dpkg-reconfigure tzdata
...
Current default time zone: 'Europe/Madrid'
Local time is now:      Fri Nov 15 14:57:56 CET 2019.
Universal Time is now:  Fri Nov 15 13:57:56 UTC 2019.

root@builder:/# 
```

Si queremos cambiar el idioma del sistema, basta con reconfigurar el paquete **locales**:

```bash
root@builder:/# dpkg-reconfigure locales
...
Generating locales (this might take a while)...
  es_ES.UTF-8... done
Generation complete.
root@builder:/# 
```

### Configuración de la consola (opcional)

Si vamos a entrar en el sistema solamente por SSH, este paso no hace falta; solamente
sirve para los casos en los que hacemos un *login* en la máquina de forma física. En estos
casos, tanto la codificación de caracteres de la pantalla física como la configuración
del teclado se vuelven importantes. Solo por si acaso, prefiero dejarlos configurados:

```bash
root@builder:/# dpkg-reconfigure console-setup
root@builder:/# 
```

```bash
root@builder:/# dpkg-reconfigure keyboard-configuration
root@builder:/# 
```

### Preparando el bootloader

Para poder inciar un sistema **Linux**, es necesaria una pieza llamada *bootloader*.
El que viene por defecto en **Debian** se llama **GRUB**, y es el que vamos a utilizar
en este caso. Solamente necesitamos generar una configuración básica e instalar el
primer sector en el disco de arranque.

```bash
root@builder:/# grub-mkconfig -o /boot/grub/grub.cfg
Generando un fichero de configuración de grub...
Encontrada imagen de linux: /boot/vmlinuz-4.19.0-5-amd64
Encontrada imagen de memoria inicial: /boot/initrd.img-4.19.0-5-amd64
hecho
root@builder:/# 
```

```bash
root@builder:/# grub-install /dev/sdb
Instalando para plataforma i386-pc.
Instalación terminada. No se notificó ningún error.
root@builder:/# 
```

### Y todo listo

Como ya no hay nada más que hacer, **podemos salir de la jaula _chroot_**. Desmontamos
los sistemas de ficheros "del sistema" y desmontamos el disco que pusimos en `/mnt`.

```bash
root@builder:/# exit
exit
root@builder:~# 
```

```bash
root@builder:~# umount /mnt/proc
root@builder:~# umount /mnt/sys
root@builder:~# umount /mnt/dev
root@builder:~# 
```

```bash
root@builder:~# umount /mnt/
root@builder:~# 
```

Este disco contiene ahora una instalación básica de **Debian** y puede arrancar cualquier
máquina en el que lo instalemos. Como yo utilizé **VirtualBox** solo necesito crear una
máquina nueva (sin disco) y añadirle un clon del disco recién instalado.
