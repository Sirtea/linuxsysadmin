Title: Creación de un livecd con Debian
Slug: creacion-de-un-livecd-con-debian
Date: 2015-12-02 12:30
Category: Operaciones
Tags: linux, debian, jessie, zerofree, debootstrap, squashfs, genisoimage, isolinux, iso, livecd



Tras ver como las actualizaciones de mis máquinas virtuales *VirtualBox* expandían mis discos *.vdi* sin control, quise pasar la herramienta *zerofree* y un compactado con la herramienta oficial *VBoxManage*. No quería instalar *zerofree* de forma permanente y no pude encontrar un *livecd* que lo tuviera, así que decidí crear uno.

Para conseguirlo, se va a usar un sistema de ficheros creado con *debootstrap* y compactado mediante *SquashFS*; este sistema de ficheros se va a empaquetar en un *.iso* junto con un *kernel*, un *initrd* y el bootloader *isolinux*. La herramienta que hace eso es *genisoimage*.

Este tutorial se ejecutó en una distribución *Debian*, pero no hay ningún problema en hacerlo en una *Ubuntu* u otra distribución, siempre que sepamos como crear la imagen base para empaquetar.

## Preparación del entorno

Todo el proceso va a ser ejecutado con el usuario *root* por comodidad.

Empezaremos por instalar todas las tecnologías que hemos mencionado:

```bash
root@desktop:~# apt-get install debootstrap isolinux squashfs-tools genisoimage
...
root@desktop:~# 
```

Creamos una carpeta de trabajo para contener todos los ficheros temporales y el producto final, por limpieza:

```bash
root@desktop:~# mkdir live_boot
root@desktop:~# cd live_boot
root@desktop:~/live_boot# 
```

Todos los comandos que se detallan a continuación se hacen desde dentro de esta carpeta.

## Preparación del sistema de ficheros, el kernel y el initrd

El sistema de ficheros se hace a partir de una jaula estándar de una distribución normal. En este paso, las distribuciones que usan *debootstrap* nos facilitan mucho las cosas (aunque esta es la operación mas larga de este tutorial):

```bash
root@desktop:~/live_boot# debootstrap --variant=minbase jessie chroot
I: Retrieving Release 
I: Retrieving Release.gpg 
I: Checking Release signature
I: Valid Release signature (key id 75DDC3C4A499F1A18CB5F3C8CBF8D6FD518E17E1)
I: Retrieving Packages 
I: Validating Packages 
I: Resolving dependencies of required packages...
I: Resolving dependencies of base packages...
...
I: Base system installed successfully.
root@desktop:~/live_boot# 
```

Ahora se trata de preparar esta jaula con los paquetes que necesitemos y las configuraciones adecuadas. Vamos a montar los pseudo sistemas de ficheros */proc*, */sys*, */dev* y */dev/pts*, que posiblemente nos van a hacer falta cuando estemos dentro de la jaula.

```bash
root@desktop:~/live_boot# mount -o bind /proc/ chroot/proc/
root@desktop:~/live_boot# mount -o bind /sys/ chroot/sys/
root@desktop:~/live_boot# mount -o bind /dev/ chroot/dev/
root@desktop:~/live_boot# mount -o bind /dev/pts/ chroot/dev/pts/
root@desktop:~/live_boot# 
```

Entramos en la jaula:

```bash
root@desktop:~/live_boot# chroot chroot
root@desktop:/# 
```

**CUIDADO**: A partir de ahora, y hasta nuevo aviso, todos los comandos se hacen **dentro** de la jaula.

Antes de nada, vamos a asignar una password al usuario *root*, porque sino, no vamos a poder entrar en el *livecd*.

```bash
root@desktop:/# passwd    
Enter new UNIX password: 
Retype new UNIX password: 
passwd: password updated successfully
root@desktop:/# 
```

Asignamos el nombre de máquina que mostrará el *livecd* una vez haya hecho el *boot*:

```bash
root@desktop:/# echo "zerofree" > /etc/hostname
root@desktop:/# 
```

Para que el *livecd* pueda hacer *boot*, vamos a necesitar el paquete **live-boot** y un *kernel* adecuado a la máquina que va a usar el *livecd*. El paquete del *kernel* ya nos va a dotar de un *initrd* que también vamos a necesitar para el *livecd*. Este paso también tarda un poco.

```bash
root@desktop:/# apt-get install linux-image-486 live-boot
Reading package lists... Done
Building dependency tree... Done
...
Setting up linux-image-3.16.0-4-586 (3.16.7-ckt11-1+deb8u3) ...
...  
/etc/kernel/postinst.d/initramfs-tools:
update-initramfs: Generating /boot/initrd.img-3.16.0-4-586
...
root@desktop:/# 
```

Ahora vamos a instalar los paquetes que queramos en el *livecd*; yo voy a poner *zerofree* que es la herramienta que motivó este *livecd*.

```bash
root@desktop:/# apt-get install zerofree
...
Unpacking zerofree (1.0.3-1) ...
Setting up zerofree (1.0.3-1) ...
root@desktop:/# 
```

**OPCIONAL**: Para reducir el tamaño final, voy a limpiar todos los archivos temporales que usa *apt*, tanto los archivos *.deb* en */var/cache/apt*, como las listas de paquetes disponibles en */var/lib/apt*.

```bash
root@desktop:/# cat /dev/null > /etc/apt/sources.list
root@desktop:/# apt-get update
Reading package lists... Done
root@desktop:/# apt-get clean 
root@desktop:/# 
```

Y finalmente salimos de la jaula:

```bash
root@desktop:/# exit
exit
root@desktop:~/live_boot# 
```

**CUIDADO**: A partir de ahora, todos los comandos se hacen **fuera** de la jaula.

Vamos a desmontar los pseudo sistemas de ficheros que ya no son necesarios, y que van a molestar cuando compactemos la jaula. Como apunte, la jaula había levantado un proceso */usr/sbin/uuidd* que evitaba desmontar *chroot/dev*, por lo que tuve que finalizar el proceso con un *kill*.

```bash
root@desktop:~/live_boot# umount chroot/dev/pts/
root@desktop:~/live_boot# umount chroot/dev/
root@desktop:~/live_boot# umount chroot/sys/
root@desktop:~/live_boot# umount chroot/proc/
root@desktop:~/live_boot# 
```

**OPCIONAL**: Sabiendo que mis máquinas virtuales son clones y el comando que va a correr siempre el comando *zerofree* contra el disco */dev/sda1*, se puede poner los comandos en el *.bash_history* de *root* para poderlos recuperar mediante el uso de flechas.

```bash
root@desktop:~/live_boot# cat chroot/root/.bash_history 
zerofree /dev/sda1
poweroff
root@desktop:~/live_boot# 
```

## Empaquetando la imagen

Vamos a crear una carpeta contenedora, que va a servir como raíz del *livecd*. Dentro le vamos a poner una carpeta *live* (para el sistema de ficheros, el *kernel* y el *initrd*) y una carpeta *isolinux* (para todo lo referente al *bootloader*).

```bash
root@desktop:~/live_boot# mkdir -p image/{live,isolinux}
root@desktop:~/live_boot# 
```

Vamos a poner el sistema de ficheros en formato *SquashFS*. Como apunte, el *kernel* y el *initrd* (ambos en la carpeta */boot*) se excluyen porque el *bootloader* es incapaz de leerlos de allí; así que los copiamos a la misma carpeta.

```bash
root@desktop:~/live_boot# mksquashfs chroot image/live/filesystem.squashfs -e boot
Parallel mksquashfs: Using 1 processor
Creating 4.0 filesystem on image/live/filesystem.squashfs, block size 131072.
...  
root@desktop:~/live_boot# cp chroot/boot/vmlinuz-3.16.0-4-586 image/live/vmlinuz
root@desktop:~/live_boot# cp chroot/boot/initrd.img-3.16.0-4-586 image/live/initrd
root@desktop:~/live_boot# 
```

Ahora vamos con el *bootloader*. Lo primero es poner una configuración para saber qué menú nos va a mostrar:

```bash
root@desktop:~/live_boot# cat image/isolinux/isolinux.cfg 
UI menu.c32

prompt 0
menu title Debian Zerofree

timeout 50

label Debian Live 3.16.0-4-586
menu label ^Debian Live 3.16.0-4-586
menu default
kernel /live/vmlinuz
append initrd=/live/initrd boot=live
root@desktop:~/live_boot# 
```

Copiamos la imagen del *bootloader* **isolinux** y los módulos que se necesitan, tanto porque nuestra configuración los usa o porque se usan desde otros módulos.

```bash
root@desktop:~/live_boot# cp /usr/lib/ISOLINUX/isolinux.bin image/isolinux/
root@desktop:~/live_boot# cp /usr/lib/syslinux/modules/bios/ldlinux.c32 image/isolinux/
root@desktop:~/live_boot# cp /usr/lib/syslinux/modules/bios/menu.c32 image/isolinux/
root@desktop:~/live_boot# cp /usr/lib/syslinux/modules/bios/libutil.c32 image/isolinux/
root@desktop:~/live_boot# 
```

Finalmente empaquetamos la imagen *.iso*. Para ello usaremos la herramienta *genisoimage* en la carpeta raíz de lo que sería el *livecd*.

```bash
root@desktop:~/live_boot# cd image/
root@desktop:~/live_boot/image# genisoimage -rational-rock -volid "Debian Zerofree" -cache-inodes -joliet -full-iso9660-filenames -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -output ../debian-zerofree.iso .
I: -input-charset not specified, using utf-8 (detected in locale settings)
Size of boot image is 4 sectors -> No emulation
  9.24% done, estimate finish Wed Dec  2 12:06:43 2015
 18.48% done, estimate finish Wed Dec  2 12:06:38 2015
 27.69% done, estimate finish Wed Dec  2 12:06:36 2015
 36.94% done, estimate finish Wed Dec  2 12:06:38 2015
 46.15% done, estimate finish Wed Dec  2 12:06:37 2015
 55.40% done, estimate finish Wed Dec  2 12:06:36 2015
 64.61% done, estimate finish Wed Dec  2 12:06:37 2015
 73.85% done, estimate finish Wed Dec  2 12:06:37 2015
 83.07% done, estimate finish Wed Dec  2 12:06:37 2015
 92.30% done, estimate finish Wed Dec  2 12:06:38 2015
Total translation table size: 2048
Total rockridge attributes bytes: 1335
Total directory bytes: 4570
Path table size(bytes): 38
Max brk space used 1a000
54178 extents written (105 MB)
root@desktop:~/live_boot/image# cd ..
root@desktop:~/live_boot# 
```

Y nuestra imagen *.iso* queda en la carpeta de trabajo, junto a la jaula y a la estructura del *livecd*. Solo necesitamos la imagen *.iso*, pero podemos dejar los ficheros intermedios hasta que estemos satisfechos con la imagen; es mas fácil modificar la jaula, el empaquetado *filesystem.squashfs* y la imagen *.iso* que volver a hacer un *debootstrap* entero...

```bash
root@desktop:~/live_boot# ls -lh
total 106M
drwxr-xr-x 20 root root 4,0K dic  2 11:30 chroot
-rw-r--r--  1 root root 106M dic  2 12:06 debian-zerofree.iso
drwxr-xr-x  4 root root 4,0K dic  2 11:53 image
root@desktop:~/live_boot# 
```

## Conclusión

Copiando esta imagen *.iso* a mi máquina con *VirtualBox* y montándola antes de hacer el *boot* de cada máquina, puedo usar la herramienta *zerofree* libremente, sin instalarla en las máquinas virtuales. Tras ello, el compactado de los ficheros *.vdi* libera los megabytes a cientos.

```bash
gerard@virtualbox:~/VirtualBox VMs$ VBoxManage modifyvdi Debian/Debian.vdi --compact
...
gerard@virtualbox:~/VirtualBox VMs$ 
```

En este caso concreto, la máquina **Debian** (*netinstall*) volvió a ocupar 700 mb, que es mucho mas interesante teniendo en cuenta que es la imagen que suelo clonar para hacer otras máquinas virtuales.
