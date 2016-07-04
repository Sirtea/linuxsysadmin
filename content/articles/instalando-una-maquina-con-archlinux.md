Title: Instalando una máquina con Archlinux
Slug: instalando-una-maquina-con-archlinux
Date: 2016-07-04 20:00
Category: Sistemas
Tags: linux, archlinux, distribución



Hoy quiero presentar una distribución de *linux* que es una maravilla; es rápida, altamente actualizada, y lo último en innovación. Se trata de una distribución tipo *rolling*, con una filosofía de última tendencia que es especialmente útil en un entorno no tan crítico, como puede ser una máquina tipo escritorio.

La parte menos buena, a parte del hecho de que los paquetes cambian mucho y pueden entrar algunos con algún fallo menor, es que la instalación no cuenta con un *wizard*, aunque en el proceso podemos aprender como funciona fácilmente.

Vamos a seguir bastante el procedimiento oficial de instalación, que podemos encontrar [aquí](https://wiki.archlinux.org/index.php/installation_guide). Este procedimiento de instalación lo vamos a lanzar sobre una máquina virtual, con un disco de 4gb y 512mb de memoria, aunque sin entorno gráfico necesita muchos menos recursos.

El primer paso consiste en descargar una imagen de instalación que vamos a introducir (o montar, que es el equivalente en *VirtualBox*), previo encendido de la máquina.

Un detalle es que la imagen de instalación lleva instalado un servidor *SSH*, que nos viene muy bien para capturar la salida de los diferentes comandos. Solo hay que levantar el servicio y darle una contraseña al usuario **root**.

```bash
root@archiso ~ # passwd
Enter new UNIX password:
Retype new UNIX password:
passwd: password updated successfully
root@archiso ~ # systemctl start sshd
root@archiso ~ # 
```

A partir de aquí, sigo el procedimiento desde una sesión *SSH*.

## Preparaciones

Aunque esto no es necesario, es recomendable usar nuestro teclado favorito. No hay nada mas frustrante que darle a una tecla pensando en un carácter y que te salga otro. Así que vamos a cargar la distribución de teclado que nos parezca.

```bash
root@archiso ~ # loadkeys es
root@archiso ~ #
```

El siguiente paso consiste en configurar la red que se va a usar durante la instalación. Por defecto viene preparado para usar *DHCP*, que nos vale, así que la dejamos como está.

Uno de los pasos mas importantes de toda la instalación es el particionado. Hacerlo mal en este punto es un problema futuro, y de hecho, mucha gente utiliza tecnologías como *LVM* que les dan cierta flexibilidad para cambios futuros.

En nuestro caso concreto, se trata de una máquina virtual que no va a durar mucho, así que nos basta con hacerlo a un nivel aceptable. Como disponemos de un solo disco de 4gb, vamos a particionarlo en dos, uno para el disco local, y otro para la partición de *swap* (una pequeña, que no nos sobra el disco). Personalmente he usado **cfdisk**, que me parece mas intuitivo que el resto, dejando las particiones de esta manera:

```bash
root@archiso ~ # fdisk -l
Disk /dev/sda: 4 GiB, 4294967296 bytes, 8388608 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: gpt
Disk identifier: A45FE619-7FFC-4EA2-8253-628FD2138198

Device       Start     End Sectors  Size Type
/dev/sda1     2048 7317503 7315456  3.5G Linux filesystem
/dev/sda2  7317504 8388574 1071071  523M Linux swap


Disk /dev/loop0: 318.9 MiB, 334385152 bytes, 653096 sectors
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
root@archiso ~ #
```

Siguiendo el manual, necesitamos formatear las particiones según las funciones que van a desempeñar, montando los discos en */mnt/* y sus subcarpetas. Como no tenemos particiones para */home/*, */var/* y */tmp/*, con montar la primera nos basta.

```bash
root@archiso ~ # mkfs.ext4 /dev/sda1
mke2fs 1.42.13 (17-May-2015)
Creating filesystem with 914432 4k blocks and 228928 inodes
Filesystem UUID: 295665be-7b09-4cad-9689-7fed5471bf25
Superblock backups stored on blocks:
        32768, 98304, 163840, 229376, 294912, 819200, 884736

Allocating group tables: done
Writing inode tables: done
Creating journal (16384 blocks): done
Writing superblocks and filesystem accounting information: done

root@archiso ~ # mount /dev/sda1 /mnt
root@archiso ~ #
```

Preparamos la partición de *swap* y la dejamos activada. Eso nos permitirá utilizarla durante la instalación, y que esta la detecte automáticamente para crear el fichero */etc/fstab*.

```bash
root@archiso ~ # mkswap /dev/sda2
Setting up swapspace version 1, size = 523 MiB (548380672 bytes)
no label, UUID=85cf7f55-cd3c-4002-9729-2d89ebadf942
root@archiso ~ # swapon /dev/sda2
root@archiso ~ #
```
Podemos verificar que está activada con un comando **free**, por ejemplo.

```bash
root@archiso ~ # free -m
              total        used        free      shared  buff/cache   available
Mem:            498          20         252          44         224         413
Swap:           522           0         522
root@archiso ~ #
```

## Instalación y configuración

El primer paso es descargar todos los paquetes de internet, mediante el comando **pacstrap**. Para ello se recomienda editar el fichero */etc/pacman.d/mirrorlist* para utilizar los *mirrors* que nos convengan, y que serán también los que use el sistema instalado. Como se pueden cambiar a *posteriori* y los que hay me parecen bien, no vamos a cambiar nada.

Así pues, lanzamos el **pacstrap** tal como indica el manual de instalación.

```bash
root@archiso ~ # pacstrap /mnt base
==> Creating install root at /mnt
==> Installing packages to /mnt
:: Synchronizing package databases...
 core                                                 119.7 KiB   783K/s 00:00 [############################################] 100%
 extra                                               1755.7 KiB   810K/s 00:02 [############################################] 100%
 community                                              3.5 MiB   851K/s 00:04 [############################################] 100%
:: There are 50 members in group base:
:: Repository core
   1) bash  2) bzip2  3) coreutils  4) cryptsetup  5) device-mapper  6) dhcpcd  7) diffutils  8) e2fsprogs  9) file
   10) filesystem  11) findutils  12) gawk  13) gcc-libs  14) gettext  15) glibc  16) grep  17) gzip  18) inetutils  19) iproute2
   20) iputils  21) jfsutils  22) less  23) licenses  24) linux  25) logrotate  26) lvm2  27) man-db  28) man-pages  29) mdadm
   30) nano  31) netctl  32) pacman  33) pciutils  34) pcmciautils  35) perl  36) procps-ng  37) psmisc  38) reiserfsprogs
   39) s-nail  40) sed  41) shadow  42) sysfsutils  43) systemd-sysvcompat  44) tar  45) texinfo  46) usbutils  47) util-linux
   48) vi  49) which  50) xfsprogs

Enter a selection (default=all):
...  
Total Download Size:   185.14 MiB
Total Installed Size:  572.80 MiB

:: Proceed with installation? [Y/n]
...
pacstrap /mnt base  51.53s user 124.01s system 39% cpu 7:25.44 total
root@archiso ~ #
```

Y con todos los paquetes instalados, empezaremos a configurar el sistema. El primer candidato es generar el fichero */etc/fstab*. Existe un *script* llamado **genfstab** que va a generar un fichero *fstab* basado en lo que tenemos ahora mismo activado.

```bash
root@archiso ~ # genfstab -p /mnt >> /mnt/etc/fstab
root@archiso ~ #
```

El resto de configuración se hace en un entorno **chroot** sobre la carpeta instalada, que es donde tenemos montado el disco raíz. La imagen de instalación nos ofrece un *script* de **chroot** que ya se encarga de montar los sistemas de ficheros especiales como */proc/*, */dev/* o */sys/*.

```bash
root@archiso ~ # arch-chroot /mnt
sh-4.3#
```

Los siguientes pasos son burocráticos y los mismos que en otras distribuciones: poner un nombre a la máquina, configurar el huso horario, generar *locales* y configurar el teclado a nivel permanente.

```bash
sh-4.3# echo "archlinux" > /etc/hostname
sh-4.3# ln -s /usr/share/zoneinfo/Europe/Madrid /etc/localtime
sh-4.3# grep -v ^# /etc/locale.gen
es_ES.UTF-8 UTF-8
sh-4.3# locale-gen
Generating locales...
  es_ES.UTF-8... done
Generation complete.
sh-4.3# echo "LANG=es_ES.UTF-8" > /etc/locale.conf
sh-4.3# echo "KEYMAP=es" > /etc/vconsole.conf
sh-4.3#
```

El siguiente paso no es fácil, y aunque puede hacerse a *posteriori*, merece la pena prestar atención. Para la configuración de red, necesitamos activar el servicio *systemd-networkd*, que va a leer los ficheros de configuración en */etc/systemd/network/* para levantar las interfaces con los parámetros adecuados.

```bash
sh-4.3# systemctl enable systemd-networkd
Created symlink /etc/systemd/system/multi-user.target.wants/systemd-networkd.service → /usr/lib/systemd/system/systemd-networkd.service.
Created symlink /etc/systemd/system/sockets.target.wants/systemd-networkd.socket → /usr/lib/systemd/system/systemd-networkd.socket.
sh-4.3# cat /etc/systemd/network/wired.network
[Match]
Name=enp0s3

[Network]
DHCP=ipv4
sh-4.3#
```

En caso de querer obtener los *DNS* de forma automática necesitamos habilitar el servicio *systemd-resolved*, que nos va a dejar un *resolv.conf* en */run/systemd/resolve/*; con un simple enlace va a ser suficiente.


```bash
sh-4.3# systemctl enable systemd-resolved
Created symlink /etc/systemd/system/multi-user.target.wants/systemd-resolved.service → /usr/lib/systemd/system/systemd-resolved.service.
sh-4.3# rm /etc/resolv.conf
sh-4.3# ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf
sh-4.3#
```

Generamos un *initramfs* para que en el siguiente arranque podamos disfrutar de todo lo nuevo que hemos configurado.

```bash
sh-4.3# mkinitcpio -p linux
==> Building image from preset: /etc/mkinitcpio.d/linux.preset: 'default'
  -> -k /boot/vmlinuz-linux -c /etc/mkinitcpio.conf -g /boot/initramfs-linux.img
==> Starting build: 4.5.4-1-ARCH
  -> Running build hook: [base]
  -> Running build hook: [udev]
  -> Running build hook: [autodetect]
  -> Running build hook: [modconf]
  -> Running build hook: [block]
  -> Running build hook: [filesystems]
  -> Running build hook: [keyboard]
  -> Running build hook: [fsck]
==> Generating module dependencies
==> Creating gzip-compressed initcpio image: /boot/initramfs-linux.img
==> Image generation successful
==> Building image from preset: /etc/mkinitcpio.d/linux.preset: 'fallback'
  -> -k /boot/vmlinuz-linux -c /etc/mkinitcpio.conf -g /boot/initramfs-linux-fallback.img -S autodetect
==> Starting build: 4.5.4-1-ARCH
  -> Running build hook: [base]
  -> Running build hook: [udev]
  -> Running build hook: [modconf]
  -> Running build hook: [block]
==> WARNING: Possibly missing firmware for module: aic94xx
==> WARNING: Possibly missing firmware for module: wd719x
  -> Running build hook: [filesystems]
  -> Running build hook: [keyboard]
  -> Running build hook: [fsck]
==> Generating module dependencies
==> Creating gzip-compressed initcpio image: /boot/initramfs-linux-fallback.img
==> Image generation successful
sh-4.3#
```

Y finalmente nos podemos dedicar a administrar usuarios y sus contraseñas. Como esto también se puede hacer a *posteriori*, voy solo a desbloquear al usuario **root**, dándole una *password* adecuada.

```bash
sh-4.3# passwd
Enter new UNIX password:
Retype new UNIX password:
passwd: password updated successfully
sh-4.3#
```

Y con esto tenemos el disco raíz perfectamente preparado, y un *kernel* listo para el arranque.

## Instalando el bootloader

Para que el *kernel*, *initrd* y el disco puedan funcionar, es necesario que el disco tenga algún tipo de estructura que le indique como hacerlo. El nombre genérico para esta pieza de *software* es *bootloader*. De todos los que hay (que no son pocos), vamos a usar un viejo amigo: **GRUB**.

```bash
sh-4.3# pacman -S grub
resolving dependencies...
looking for conflicting packages...

Packages (1) grub-1:2.02.beta2-6

Total Download Size:    5.27 MiB
Total Installed Size:  25.27 MiB

:: Proceed with installation? [Y/n] y
...
sh-4.3#
```

Instalamos el código de *boot* en el *MBR* con la herramienta que **GRUB** nos ofrece, siguiendo el manual.

```bash
sh-4.3# grub-install --target=i386-pc /dev/sda
Installing for i386-pc platform.
grub-install: warning: this GPT partition label contains no BIOS Boot Partition; embedding won't be possible.
grub-install: warning: Embedding is not possible.  GRUB can only be installed in this setup by using blocklists.  However, blocklists are UNRELIABLE and their use is discouraged..
grub-install: error: will not proceed with blocklists.
sh-4.3#
```

En este caso ha fallado, pero siguiendo el manual de instalación, eso se corrige mediante el uso del *flag* **--force**.

```bash
sh-4.3# grub-install --target=i386-pc /dev/sda --force
Installing for i386-pc platform.
grub-install: warning: this GPT partition label contains no BIOS Boot Partition; embedding won't be possible.
grub-install: warning: Embedding is not possible.  GRUB can only be installed in this setup by using blocklists.  However, blocklists are UNRELIABLE and their use is discouraged..
Installation finished. No error reported.
sh-4.3#
```

Como ya hemos conseguido instalar **GRUB** de forma exitosa, nos queda generar un fichero de configuración del *bootloader*, tal como dice el manual de instalación.

```bash
sh-4.3# grub-mkconfig -o /boot/grub/grub.cfg
Generating grub configuration file ...
Found linux image: /boot/vmlinuz-linux
Found initrd image: /boot/initramfs-linux.img
Found fallback initramfs image: /boot/initramfs-linux-fallback.img
done
sh-4.3#
```

Y con esto queda una instalación básica. Solo nos queda salir del entorno enjaulado, apagar la máquina, quitar el disco de instalación y encender.

```bash
sh-4.3# exit
exit
arch-chroot /mnt  10.17s user 19.71s system 3% cpu 14:10.46 total
root has logged on pts/1 from 10.0.2.2.
root@archiso ~ # reboot
```

## Resultado final

Tras actualizar y limpiar caché de paquetes, vemos que tenemos una distribución minimalista con 743mb de disco ocupados y 10mb de memoria.

```bash
[root@archlinux ~]# df -h
S.ficheros     Tamaño Usados  Disp Uso% Montado en
dev              247M      0  247M   0% /dev
run              250M   292K  249M   1% /run
/dev/sda1        3,4G   743M  2,5G  23% /
tmpfs            250M      0  250M   0% /dev/shm
tmpfs            250M      0  250M   0% /sys/fs/cgroup
tmpfs            250M      0  250M   0% /tmp
tmpfs             50M      0   50M   0% /run/user/0
[root@archlinux ~]# free -m
              total        used        free      shared  buff/cache   available
Mem:            498          10         441           0          46         470
Swap:           522           0         522
[root@archlinux ~]#
```

A partir de aquí podemos construir a base de instalar aquellos paquetes que necesitemos (escritorio, servicios, ...); sin embargo, esto queda para futuros artículos.
