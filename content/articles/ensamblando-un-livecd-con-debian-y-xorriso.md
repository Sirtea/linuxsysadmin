Title: Ensamblando un livecd con Debian y xorriso
Slug: ensamblando-un-livecd-con-debian-y-xorriso
Date: 2019-04-05 10:00
Category: Operaciones
Tags: linux, debian, stretch, zerofree, debootstrap, squashfs, xorriso, isolinux, iso, livecd



Últimamente me he visto obligado a virtualizar en una máquina distinta de la habitual por un problema técnico; esto no sería un problema de no ser porque la arquitectura es de 32 bits. Eso me deja sin ninguna distribución prefabricada con la herramienta `zerofree` y me obliga a hacer una.

Ya lo hice una vez, tal como muestro en [este otro artículo]({filename}/articles/creacion-de-un-livecd-con-debian.md), pero las herramientas han cambiado mucho y era necesario hacer un artículo nuevo actualizado. El cambio principal es la sustitución de `genisoimage` por `xorriso`; también actualizo la versión de **Debian** a **stretch**, aunque esto no cambia el proceso de creación del *livecd*.

## Preparación del entorno de trabajo

Empezamos instalando las herramientas necesarias:

```bash
gerard@builder:~$ sudo apt install debootstrap isolinux squashfs-tools xorriso
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias       
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes adicionales:
  libburn4 libisoburn1 libisofs6 libjte1 liblzo2-2 syslinux-common
Paquetes sugeridos:
  jigit cdck
Se instalarán los siguientes paquetes NUEVOS:
  debootstrap isolinux libburn4 libisoburn1 libisofs6 libjte1 liblzo2-2 squashfs-tools
  syslinux-common xorriso
0 actualizados, 10 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 2.715 kB de archivos.
Se utilizarán 7.072 kB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
gerard@builder:~$ 
```

Para tener el entorno estructurado, vamos a crear una carpeta contenedora y vamos a trabajar desde la misma.

```bash
gerard@builder:~$ mkdir live_boot
gerard@builder:~$ cd live_boot/
gerard@builder:~/live_boot$ 
```

En esta carpeta vamos a acumular otras subcarpetas:

* `image` &rarr; Esta carpeta es la que utiliza `xorriso` para montar la imagen iso, y tiene dos subcarpetas:
    * `image/isolinux` &rarr; Carpeta con la configuración del `bootloader` **isolinux** y los módulos que pueda necesitar
    * `image/live` &rarr; Carpeta que alberga el *kernel*, el *initrd* y el sistema de ficheros del sistema *live* en formato **squashfs**
* `chroot` &rarr; Carpeta en donde vamos a hacer el `debootstrap` del sistema de ficheros del sistema *live*, antes de comprimirlo con **squashfs**

Vamos a empezar por crear la estructura necesaria para la imagen. Sin embargo, no vamos a crear la carpeta `chroot`, ya que se va a crear con el mismo comando `debootstrap`.

```bash
gerard@builder:~/live_boot$ sudo mkdir -p image/{live,isolinux}
gerard@builder:~/live_boot$ 
```

## Preparación del bootloader

Esta es la parte más fácil y rápida del proceso; la hacemos cuanto antes y nos la quitamos de encima. Si en un futuro recreamos el sistema *live*, seguramente no vamos a tener que cambiar esto, e incluso nos puede servir para un sistema *live* completamente distinto.

La parte de los módulos no ocupa demasiado (no llega a 1 mb); personalmente prefiero copiarlos todos y que no falten.

```bash
gerard@builder:~/live_boot$ sudo cp /usr/lib/ISOLINUX/isolinux.bin image/isolinux/
gerard@builder:~/live_boot$ sudo cp /usr/lib/syslinux/modules/bios/* image/isolinux/
gerard@builder:~/live_boot$ 
```

El *bootloader* necesita un fichero de configuración para definir el menú de entrada, y **isolinux** no es la excepción. Pongo uno sencillo y bastante genérico:

```bash
gerard@builder:~/live_boot$ cat image/isolinux/isolinux.cfg 
UI menu.c32

prompt 0
menu title Debian Zerofree

timeout 30

label Debian Live
menu label ^Debian Live
menu default
kernel /live/vmlinuz
append initrd=/live/initrd boot=live
gerard@builder:~/live_boot$ 
```

Y eso es todo.


## El sistema de ficheros raíz

La forma oficial de crear un sistema raíz **Debian** es utilizar **debootstrap**. Para minimizar el tamaño del sistema de ficheros (y por lo tanto, del *livecd*), he optado por utilizar la variante *minbase* que limita los paquetes que entiende como "sistema base"; el resto tendrán que entrar como dependencias de lo que instalemos. Este comando va a crear el sistema base en la carpeta `chroot`, que ya indicábamos al principio del artículo.

```bash
gerard@builder:~/live_boot$ sudo debootstrap --variant=minbase stretch chroot
I: Retrieving InRelease 
I: Retrieving Release 
I: Retrieving Release.gpg 
I: Checking Release signature
I: Valid Release signature (key id 067E3C456BAE240ACEE88F6FEF0F382A1A7B6500)
I: Retrieving Packages 
I: Validating Packages 
...
I: Base system installed successfully.
gerard@builder:~/live_boot$ 
```

Para acabar de configurar el sistema base, vamos a entrar en la jaula creada y para ello necesitamos montar los sistemas de ficheros del sistema:

```bash
gerard@builder:~/live_boot$ sudo mount -o bind /proc/ chroot/proc/
gerard@builder:~/live_boot$ sudo mount -o bind /sys/ chroot/sys/
gerard@builder:~/live_boot$ sudo mount -o bind /dev/ chroot/dev/
gerard@builder:~/live_boot$ sudo mount -o bind /dev/pts/ chroot/dev/pts/
gerard@builder:~/live_boot$ 
```

Usamos el comando `chroot` para entrar en la jaula, que está en la carpeta del mismo nombre:

```bash
gerard@builder:~/live_boot$ sudo chroot chroot/
root@builder:/# 
```

**AVISO**: Hasta nuevo aviso, todos los comandos se ejecutan dentro de la jaula.

Vamos a habilitar al usuario `root` asignándole una contraseña. Esto nos permitirá acceder al sistema usando este usuario. Lo recomendable sería un usuario normal, tal vez con permisos de `sudo`; en este caso voy a saltarme esta práctica.

```bash
root@builder:/# passwd
Enter new UNIX password: 
Retype new UNIX password: 
passwd: password updated successfully
root@builder:/# 
```

Modificamos la configuración relativa al nombre del sistema *live* para que le quede un nombre apropiado.

```bash
root@builder:/# echo "zerofree" > /etc/hostname
root@builder:/# 
```

Para que el sistema *live* pueda arrancar, vamos a necesitar algunos paquetes más: un *kernel*, los *scripts* para hacer un *live boot* y el paquete `systemd-sysv` que nos va a proveer del binario necesario `/sbin/init`, que es el que se ejecuta al acabar de cargar el *kernel*.

```bash
root@builder:/# apt install linux-image-686 live-boot systemd-sysv
Reading package lists... Done
Building dependency tree... Done
...  
Do you want to continue? [Y/n] y
...
update-initramfs: Generating /boot/initrd.img-4.9.0-8-686
live-boot: core filesystems devices utils udev blockdev dns.
root@builder:/# 
```

También voy a instalar las herramientas que motivaron la creación del *livecd*, que en este caso es **zerofree**.

```bash
root@builder:/# apt install zerofree
...
root@builder:/# 
```

Para reducir aún más el tamaño del sistema de ficheros hacemos algunas limpiezas, como por ejemplo de listados de paquetes y paquetes descargados. Aquí se podría borrar mucho más, pero nuevamente voy a lo fácil y seguro.

```bash
root@builder:/# cat /dev/null > /etc/apt/sources.list
root@builder:/# apt update
Reading package lists... Done
Building dependency tree       
Reading state information... Done
All packages are up to date.
root@builder:/# 
```

```bash
root@builder:/# apt clean
root@builder:/# 
```

Como ya no tenemos nada más que hacer en la jaula, salimos de la misma:

```bash
root@builder:/# exit
exit
gerard@builder:~/live_boot$ 
```

**AVISO**: Todos los comandos que siguen se ejecutan fuera de la jaula.

Desmontamos los sistemas de ficheros del sistema, porque la jaula no los necesita y no queremos que queden ocupando espacio cuando comprimamos el sistema de ficheros.

```bash
gerard@builder:~/live_boot$ sudo umount chroot/dev/pts/
gerard@builder:~/live_boot$ sudo umount chroot/dev/
gerard@builder:~/live_boot$ sudo umount chroot/sys/
gerard@builder:~/live_boot$ sudo umount chroot/proc/
gerard@builder:~/live_boot$ 
```

Si se necesita modificar alguna configuración a *posteriori*, no siempre es necesario entrar de nuevo en la jaula; basta con modificar el fichero, relativo a la carpeta de la jaula. En mi caso, me olvidé de modificar el `.bash_history`, y poner una lista de comandos me permite recuperarlos con las flechas direccionales; esto es muy cómodo cuando vas a lanzar los mismos comandos una y otra vez.

```bash
gerard@builder:~/live_boot$ sudo cat chroot/root/.bash_history
zerofree /dev/sda1
poweroff
gerard@builder:~/live_boot$ 
```

Y con esto nos queda el sistema de ficheros. Es interesante guardar la carpeta `chroot` después de comprimir el sistema de ficheros (aunque no se use), ya que si algo no está a nuestro gusto podemos rectificarlo y comprimir de nuevo, reduciendo el tiempo considerablemente.

## Ensamblando la imagen .iso

Llegados a este punto, solo necesitamos rellenar la carpeta `image/live`, puesto que `image/isolinux` ya tiene lo que necesitamos. Esta carpeta solo necesita 3 ficheros:

* El *kernel*
* El *initrd*
* El sistema de ficheros comprimido

Los dos primeros están instalados en la jaula, porque pusimos la imagen de *kernel* que nos pareció adecuada; simplemente nos los copiamos.

```bash
gerard@builder:~/live_boot$ sudo cp chroot/boot/vmlinuz-4.9.0-8-686 image/live/vmlinuz
gerard@builder:~/live_boot$ sudo cp chroot/boot/initrd.img-4.9.0-8-686 image/live/initrd
gerard@builder:~/live_boot$ 
```

El sistema de ficheros comprimido tampoco tiene mucho más problema; solo hay que tener en cuenta que **isolinux** no puede leer el *kernel* del fichero comprimido. Esto nos obliga a poner el *kernel* fuera del sistema comprimido (esto es el paso anterior), y nos permite excluirlo del fichero comprimido.

```bash
gerard@builder:~/live_boot$ sudo mksquashfs chroot image/live/filesystem.squashfs -e boot
Parallel mksquashfs: Using 1 processor
Creating 4.0 filesystem on image/live/filesystem.squashfs, block size 131072.
...
gerard@builder:~/live_boot$ 
```

Si lo hemos hecho bien, nos va a quedar una estructura similar a esta (excluyo la carpeta `chroot` por legibilidad, ya que no se usa para nada de ahora en adelante):

```bash
gerard@builder:~/live_boot$ tree -Ih chroot
.
└── [4.0K]  image
    ├── [4.0K]  isolinux
    │   ├── [1.6K]  cat.c32
    │   ├── [ 24K]  chain.c32
    │   ├── [1.2K]  cmd.c32
    │   ├── [3.6K]  cmenu.c32
    │   ├── [1.5K]  config.c32
    │   ├── [4.1K]  cptime.c32
    │   ├── [4.4K]  cpu.c32
    │   ├── [1.7K]  cpuid.c32
    │   ├── [2.7K]  cpuidtest.c32
    │   ├── [1.6K]  debug.c32
    │   ├── [4.0K]  dhcp.c32
    │   ├── [2.0K]  disk.c32
    │   ├── [8.4K]  dmi.c32
    │   ├── [ 12K]  dmitest.c32
    │   ├── [3.2K]  elf.c32
    │   ├── [2.7K]  ethersel.c32
    │   ├── [ 10K]  gfxboot.c32
    │   ├── [1.6K]  gpxecmd.c32
    │   ├── [161K]  hdt.c32
    │   ├── [3.6K]  hexdump.c32
    │   ├── [1.8K]  host.c32
    │   ├── [1.7K]  ifcpu64.c32
    │   ├── [4.0K]  ifcpu.c32
    │   ├── [4.2K]  ifmemdsk.c32
    │   ├── [1.9K]  ifplop.c32
    │   ├── [ 40K]  isolinux.bin
    │   ├── [ 175]  isolinux.cfg
    │   ├── [1.6K]  kbdmap.c32
    │   ├── [4.8K]  kontron_wdt.c32
    │   ├── [114K]  ldlinux.c32
    │   ├── [5.0K]  lfs.c32
    │   ├── [178K]  libcom32.c32
    │   ├── [ 65K]  libgpl.c32
    │   ├── [ 99K]  liblua.c32
    │   ├── [ 24K]  libmenu.c32
    │   ├── [ 23K]  libutil.c32
    │   ├── [4.6K]  linux.c32
    │   ├── [2.9K]  ls.c32
    │   ├── [6.7K]  lua.c32
    │   ├── [10.0K]  mboot.c32
    │   ├── [2.4K]  meminfo.c32
    │   ├── [ 26K]  menu.c32
    │   ├── [3.3K]  pci.c32
    │   ├── [3.4K]  pcitest.c32
    │   ├── [2.9K]  pmload.c32
    │   ├── [1.6K]  poweroff.c32
    │   ├── [3.1K]  prdhcp.c32
    │   ├── [1.5K]  pwd.c32
    │   ├── [ 12K]  pxechn.c32
    │   ├── [1.3K]  reboot.c32
    │   ├── [ 13K]  rosh.c32
    │   ├── [1.6K]  sanboot.c32
    │   ├── [3.1K]  sdi.c32
    │   ├── [ 15K]  sysdump.c32
    │   ├── [7.4K]  syslinux.c32
    │   ├── [3.0K]  vesa.c32
    │   ├── [2.1K]  vesainfo.c32
    │   ├── [ 26K]  vesamenu.c32
    │   ├── [1.8K]  vpdtest.c32
    │   ├── [2.4K]  whichsys.c32
    │   └── [3.5K]  zzjson.c32
    └── [4.0K]  live
        ├── [111M]  filesystem.squashfs
        ├── [ 18M]  initrd
        └── [3.4M]  vmlinuz

3 directories, 64 files
gerard@builder:~/live_boot$ 
```

Si es así, lo tenemos todo; solo hace falta lanzar **xorriso** para que nos lo empaquete todo en un fichero `.iso`:

```bash
gerard@builder:~/live_boot$ sudo xorriso -as mkisofs -r -J -joliet-long -l -cache-inodes -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin -partition_offset 16 -A "Debian Live" -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o debian-zerofree.iso image
xorriso 1.4.6 : RockRidge filesystem manipulator, libburnia project.

Drive current: -outdev 'stdio:debian-zerofree.iso'
Media current: stdio file, overwriteable
Media status : is blank
Media summary: 0 sessions, 0 data blocks, 0 data, 6676m free
xorriso : NOTE : -as mkisofs: Ignored option '-cache-inodes'
Added to ISO image: directory '/'='/home/gerard/live_boot/image'
xorriso : UPDATE : 66 files added in 1 seconds
xorriso : UPDATE : 66 files added in 1 seconds
xorriso : NOTE : Copying to System Area: 432 bytes from file '/usr/lib/ISOLINUX/isohdpfx.bin'
libisofs: NOTE : Aligned image size to cylinder size by 245 blocks
...  
ISO image produced: 69120 sectors
Written to medium : 69120 sectors at LBA 0
Writing to 'stdio:debian-zerofree.iso' completed successfully.

gerard@builder:~/live_boot$ 
```

Y con esto deberíamos tener el fichero generado en la misma carpeta.

```bash
gerard@builder:~/live_boot$ ls -lh *.iso
-rw-r--r-- 1 root root 135M mar 26 20:18 debian-zerofree.iso
gerard@builder:~/live_boot$ 
```

Si no nos convence el resultado, bastaría con modificar la jaula a nuestro gusto, reempaquetar el sistema de ficheros, copiar el *kernel* y el *initrd* si han cambiado, y relanzar **xorriso**.
