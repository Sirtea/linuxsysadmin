---
title: "Haciendo snapshots con LVM"
slug: "haciendo-snapshots-con-lvm"
date: 2016-02-15
categories: ['Operaciones']
tags: ['linux', 'lvm', 'logical volume manager', 'snapshot', 'point-in-time', 'backup']
---

Una de las funcionalidades mas implementadas en los sistemas de ficheros de nueva generación es la capacidad de hacer *snapshots point-in-time*. Sin embargo, no tenemos que renunciar a la estabilidad de los sistemas de ficheros tradicionales como **ext4**; otras veces no es posible por requisitos del servicio que debe usarlo.<!--more-->

En este tutorial vamos a demostrar lo fácil que es hacer este tipo de *snapshots*, usando como tecnología subyacente el **logical volume manager**, de ahora en adelante, **LVM**.

Los únicos requisitos para seguir esta guía son el paquete **lvm** y un disco físico sobre el que vamos a construir el *volume group* que va a alojar los *logical volumes*; al menos van a ser la partición original y algo de espacio para servir como volumen para el *snapshot*.

## Preparación

Empezamos instalando los requisitos software:

```bash
root@server:~# apt-get install lvm2
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes extras:
  dmeventd libdevmapper-event1.02.1 liblvm2cmd2.02 libreadline5
Paquetes sugeridos:
  thin-provisioning-tools
Se instalarán los siguientes paquetes NUEVOS:
  dmeventd libdevmapper-event1.02.1 liblvm2cmd2.02 libreadline5 lvm2
0 actualizados, 5 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 1.530 kB de archivos.
Se utilizarán 3.898 kB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
root@server:~#
```

Suponiendo que el disco que vamos a usar es */dev/sdb*, vamos a acondicionarlo para que pueda actuar como *physical volume*.

```bash
root@server:~# pvcreate /dev/sdb
  Physical volume "/dev/sdb" successfully created
root@server:~#
```

Ahora vamos a usar este *physical volume* para crear el *volume group*.

```bash
root@server:~# vgcreate lvm /dev/sdb
  /proc/devices: No entry for device-mapper found
  Volume group "lvm" successfully created
root@server:~#
```

Vamos a sacar un *logical volume* para crear el sistema de ficheros que va a ser el objeto del *snapshot*. El tamaño del volumen puede ser el que nos convenga, e incluso crecer según sea necesario. De momento, nos basta con 1 GB.

```bash
root@server:~# lvcreate lvm -L 1G -n datos
  Logical volume "datos" created
root@server:~#
```

Lo formateamos como si de un disco mas se tratara.

```bash
root@server:~# mkfs.ext4 /dev/lvm/datos
mke2fs 1.42.12 (29-Aug-2014)
Se está creando El sistema de ficheros con 262144 4k bloques y 65536 nodos-i

UUID del sistema de ficheros: 1ad4e531-82de-4797-9968-28cb33b3badd
Respaldo del superbloque guardado en los bloques:
        32768, 98304, 163840, 229376

Reservando las tablas de grupo: hecho
Escribiendo las tablas de nodos-i: hecho
Creando el fichero de transacciones (8192 bloques): hecho
Escribiendo superbloques y la información contable del sistema de ficheros: hecho

root@server:~#
```

Vamos a asumir que nuestro servicio necesita dejar sus datos en */data*; como no existe, vamos a crearlo.

```bash
root@server:~# mkdir /data
root@server:~#
```

El siguiente paso es montar ese volumen en su sitio, en este caso, en */data*. Se deja como ejercicio personal ponerlo en el */etc/fstab*.

```bash
root@server:~# mount /dev/lvm/datos /data/
root@server:~#
```

Vamos a crear algo de contenido en la carpeta para simular los datos que dejaría el servicio que supuestamente usaría esta carpeta.

```bash
root@server:~# echo 1 > /data/a
root@server:~# echo 1 > /data/b
root@server:~#
```

## Creación del snapshot

Hacer un *snapshot* es tan fácil como invocar el binario **lvcreate** con el parámetro *-s*, especificando el tamaño, el nombre y el volumen objetivo.

```bash
root@server:~# lvcreate -L 100M -n datos-snap -s /dev/lvm/datos
  Logical volume "datos-snap" created
root@server:~#
```

El volumen *datos-snap* solo contiene las diferencias con el volumen original, así que no necesita tener el mismo tamaño que el original. Sin embargo, si hubiera mas de 100 MB de cambios, este *snapshot* quedaría inválido.

De momento, creo que con 100 MB va a ser suficiente, ya que solo pretendo sacar un fichero comprimido de ese *snapshot*, eliminándolo después. Un tamaño seguro habría sido el mismo que el volumen original. Sin embargo, como se trata de otro volumen **LVM**, podremos extenderla a posteriori con *lvextend*.

Vamos a analizar el contenido; lo montamos en una carpeta cualquiera para ver su contenido.

```bash
root@server:~# mount /dev/lvm/datos-snap /mnt/
root@server:~#
```

Es fácil de verificar que tienen el mismo contenido.

```bash
root@server:~# grep . /data/* /mnt/*
/data/a:1
/data/b:1
/mnt/a:1
/mnt/b:1
root@server:~#
```

Vamos a continuar simulando que el servicio escribe en el volumen original, por ejemplo, modificando uno de los ficheros.

```bash
root@server:~# echo 2 > /data/a
root@server:~#
```

Y verificamos que el *snapshot point-in-time* se quedó en el momento temporal en el que lo hicimos, quedando como estaba entonces:

```bash
root@server:~# grep . /data/* /mnt/*
/data/a:2
/data/b:1
/mnt/a:1
/mnt/b:1
root@server:~#
```

Verificando los *logical volume* con el comando *lvs*, vemos que es un volumen de 100 MB, con una ocupación baja, del 0,08%. El *snapshot* quedaría inservible si llegara a superar el 100%.

```bash
root@server:~# lvs
  LV         VG   Attr       LSize   Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  datos      lvm  owi-aos---   1,00g
  datos-snap lvm  swi-aos--- 100,00m      datos  0,08
root@server:~#
```

## Sacando el backup

El objetivo inicial era sacar una copia de los datos, congelados en un momento concreto. Tenemos ese momento en el volumen *datos-snap*.

Empezaremos montándolo en alguna carpeta cualquiera, si no lo teníamos ya (lo hemos montado en el punto anterior).

```bash
root@server:~# mount /dev/lvm/datos-snap /mnt/
root@server:~#
```

Con el volumen montado, el resto es procedimiento estándar. En este caso, vamos a sacar un fichero *.tar.gz* con el contenido de la carpeta:

```bash
root@server:~# cd /mnt/
root@server:/mnt# tar cvzf /root/backup.tar.gz *
a
b
root@server:/mnt#
```

Y finalmente vamos a limpiar el *snapshot*, empezando por desmontar el volumen. Como estamos dentro de la carpeta no vamos a poder desmontar el volumen, así que salimos.

```bash
root@server:/mnt# cd
root@server:~# umount /mnt/
root@server:~#
```

Y ahora que no lo tenemos montado, lo eliminamos sin problemas con las herramientas propias de **LVM**.

```bash
root@server:~# lvremove /dev/lvm/datos-snap
Do you really want to remove active logical volume datos-snap? [y/n]: y
  Logical volume "datos-snap" successfully removed
root@server:~#
```

Y solo quedará poner el fichero *backup.tar.gz* a buen recaudo.
