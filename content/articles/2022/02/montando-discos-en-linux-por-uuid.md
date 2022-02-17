---
title: "Montando discos en Linux por UUID"
slug: "montando-discos-en-linux-por-uuid"
date: "2022-02-17"
categories: ['Sistemas']
tags: ['linux', 'mount', 'filesystem', 'UUID']
---

Ha vuelto a pasar: tengo una máquina virtual con un disco secundario que se queda pequeño.
Añado otro disco, lo preparo, sincronizo los datos y configuro su montaje en el `/etc/fstab`,
usando su nombre de dispositivo. Eventualmente, reinicio el servidor, tras retirar el disco
antiguo y su nombre de dispositivo ha cambiado, causando que la máquina no arranque.<!--more-->

Harto de este tipo de situaciones, y visto que el nombre de dispositivo no es de fiar, ha
llegado la hora de buscar un método alternativo de especificar un disco. Y el más fiable
de todos es su identificador único de disco o partición (UUID). Este se asigna cada vez
que formateamos el disco o partición.

## El problema expuesto

Mi máquina virtual tiene 2 discos, uno en el puerto SATA 0, que es mi disco raíz, y otro
en el puerto SATA 1, digamos que dispone de 4GB y está montado en `/var/lib/docker`. En este
estado, Linux asigna el dispositivo `/dev/sda` al disco en el puerto SATA 0, y `/dev/sdb`
al disco del puerto SATA 1.

Eventualmente, me doy cuenta de que el disco de 4GB de `/var/lib/docker` se ha quedado corto.
Nada nuevo; simplemente añado un disco de 32GB en el puerto SATA 2, reinicio la máquina virtual,
y monto este `/dev/sdc` (o partición) temporalmente a otra carpeta para sincronizar los datos
y actualizo el `/etc/fstab` acorde a `/dev/sdc`. Apago la máquina, quito el disco en el puerto
SATA 1 y la vuelvo a levantar. **¡ERROR!**

A pesar de que el disco de 32GB está en el puerto SATA 2, Linux le asigna el siguiente `/dev/sdX`
libre, que a falta de un disco en el puerto SATA 1, es `/dev/sdb`: **el nombre del dispositivo
ha cambiado** y el fichero `/etc/fstab` tiene `/dev/sdc`, lo que causa que **la máquina virtual
no arranque**.

## Usando el UUID en vez del nombre del dispositivo

Como ya hemos explicado, el nombre del dispositivo puede cambiar por varios motivos, pero
cada disco o partición dispone de un identificador único que se crea en tiempo de formateo,
con herramientas tipo `mkswap` o `mkfs`.

### Localizar el UUID de mi disco o partición

Podemos localizar el UUID de nuestras particiones de varias maneras. Podemos usar los
comandos `blkid`, `lsblk` o `tune2fs`; alternativamente podemos sacar esa información listando
los ficheros de dispositivos en `/dev`. Sin ser una lista exhaustiva, pongo algunos ejemplos:

```bash
gerard@server:~$ lsblk -f
NAME   FSTYPE FSVER LABEL UUID                                 FSAVAIL FSUSE% MOUNTPOINT
sda
└─sda1 ext4   1.0         3723d7aa-ca4d-4959-ade2-80d7b2d0bb5e    1,1G    43% /
sdb
└─sdb1 ext4   1.0         9b85a769-bd34-47a2-b69d-3549aa76f930   31,3G     0% /var/lib/docker
sr0
gerard@server:~$
```

```bash
gerard@server:~$ sudo blkid
/dev/sda1: UUID="3723d7aa-ca4d-4959-ade2-80d7b2d0bb5e" BLOCK_SIZE="4096" TYPE="ext4" PARTUUID="db07bacb-01"
/dev/sdb1: UUID="9b85a769-bd34-47a2-b69d-3549aa76f930" BLOCK_SIZE="4096" TYPE="ext4" PARTUUID="0d8dbb9b-c731-7a43-8310-7e64d3eea84c"
gerard@server:~$
```

```bash
gerard@server:~$ ls -lh /dev/disk/by-uuid/
total 0
lrwxrwxrwx 1 root root 10 feb 17 14:22 3723d7aa-ca4d-4959-ade2-80d7b2d0bb5e -> ../../sda1
lrwxrwxrwx 1 root root 10 feb 17 14:22 9b85a769-bd34-47a2-b69d-3549aa76f930 -> ../../sdb1
gerard@server:~$
```

```bash
gerard@server:~$ sudo tune2fs -l /dev/sdb1 | grep UUID
Filesystem UUID:          9b85a769-bd34-47a2-b69d-3549aa76f930
gerard@server:~$
```

**RESULTADO**: Nos queda claro que el disco que es `/dev/sdb1` (por el momento) y que está
montado en `/var/lib/docker` tiene el UUID `9b85a769-bd34-47a2-b69d-3549aa76f930`.

## Configurando el fichero `/etc/fstab`

Normalmente, suelo montar la partición "a mano" y sacar la línea del fichero `/etc/fstab`
revisando `/etc/mtab` o `/proc/mounts` (son el mismo fichero); sacar esa línea del comando
`mount` requiere cambiar el formato final y por ello lo suelo descartar.

```bash
gerard@server:~$ mount | grep "/var/lib/docker"
/dev/sdb1 on /var/lib/docker type ext4 (rw,relatime)
gerard@server:~$
```

```bash
gerard@server:~$ grep "/var/lib/docker" /etc/mtab
/dev/sdb1 /var/lib/docker ext4 rw,relatime 0 0
gerard@server:~$
```

```bash
gerard@server:~$ grep "/var/lib/docker" /proc/mounts
/dev/sdb1 /var/lib/docker ext4 rw,relatime 0 0
gerard@server:~$
```

Luego pego esa última línea en el fichero `/etc/fstab`:

```bash
gerard@server:~$ grep "/var/lib/docker" /etc/fstab
/dev/sdb1 /var/lib/docker ext4 rw,relatime 0 0
gerard@server:~$
```

Sin embargo, sabiendo que el nombre del dispositivo cambia, pero el identificador no,
podemos modificar esa línea en el fichero `/etc/fstab`, cambiando el nombre del dispositivo
por `UUID="xxxx"`. En este caso quedaría así:

```bash
gerard@server:~$ grep "/var/lib/docker" /etc/fstab
#/dev/sdb1 /var/lib/docker ext4 rw,relatime 0 0
UUID="9b85a769-bd34-47a2-b69d-3549aa76f930" /var/lib/docker ext4 rw,relatime 0 0
gerard@server:~$
```

Y con esto ya podemos añadir y quitar discos en el servidor, sin miedo a que nos descoloque los puntos de montaje en el proceso.
