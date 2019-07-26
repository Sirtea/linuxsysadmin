---
title: "Un sistema de ficheros comprimido y de solo lectura: squashfs"
slug: "un-sistema-de-ficheros-comprimido-y-de-solo-lectura-squashfs"
date: 2018-02-19
categories: ['Operaciones']
tags: ['squashfs', 'mount', 'filesystem']
---

Cuando trabajamos con tamaños de disco muy limitados, como por ejemplo en dispositivos *embedded* o *pendrives*, nos vemos obligados a reducir nuestros sistemas de ficheros. Algunos de estos sistemas de ficheros son de solo lectura, y vienen comprimidos, lo que nos permite ahorrar en espacio de disco, no en funcionalidades.<!--more-->

En este campo aparece el nombre de *squashfs*, que es básicamente un sistema de ficheros *ext2* comprimido. La única diferencia entre *ext2*, *ext3* y *ext4* es el *journal*, que es el registro encargado de que no se pierdan las escrituras hechas en el disco en caso de fallo antes de *flushear* lo *bufferes*, así que la version *ext2* no es ni un atraso ni un impedimento.

## Creación del sistema de ficheros

Para crear un sistema de ficheros nos hacen falta las herramientas **mksquashfs** y posiblemente el decompresor **unsquashfs**. En *Debian* se pueden obtener instalando el paquete **squashfs-tools**.

```bash
gerard@atlantis:~$ sudo apt-get install squashfs-tools
[sudo] password for gerard:
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes adicionales:
  liblzo2-2
Se instalarán los siguientes paquetes NUEVOS:
  liblzo2-2 squashfs-tools
0 actualizados, 2 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 179 kB de archivos.
Se utilizarán 488 kB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
gerard@atlantis:~$
```

Vamos a crear un sistema de ficheros normal en un carpeta, que luego vamos a comprimir. Hoy, y a modo de ejemplo, vamos a crearlos con ficheros de contenido aleatorio; normalmente suelo poner jaulas o partes del sistema operativo.

```bash
gerard@atlantis:~/squashtest$ mkdir rootfs
gerard@atlantis:~/squashtest$ dd if=/dev/urandom of=/dev/stdout bs=1K count=10 | base64 > rootfs/file1
10+0 registros leídos
10+0 registros escritos
10240 bytes (10 kB, 10 KiB) copied, 0,000641935 s, 16,0 MB/s
gerard@atlantis:~/squashtest$ dd if=/dev/urandom of=/dev/stdout bs=1K count=10 | base64 > rootfs/file2
10+0 registros leídos
10+0 registros escritos
10240 bytes (10 kB, 10 KiB) copied, 0,000119261 s, 85,9 MB/s
gerard@atlantis:~/squashtest$
```

Si miramos lo que nos ha quedado, vemos que el resultado es el correcto. Tened en cuenta que la carpeta contenedora *rootfs* se considerará la raíz del sistema de ficheros.

```bash
gerard@atlantis:~/squashtest$ tree -h
.
└── [4.0K]  rootfs
    ├── [ 14K]  file1
    └── [ 14K]  file2

1 directory, 2 files
gerard@atlantis:~/squashtest$
```

Solo nos queda lanzar el comando **mksquashfs** que se encargará de comprimir el conjunto de carpetas que indiquemos y creará el fichero que declaremos en el último parámetro.

```bash
gerard@atlantis:~/squashtest$ mksquashfs rootfs/ rootfs.sqsh
Parallel mksquashfs: Using 1 processor
Creating 4.0 filesystem on rootfs.sqsh, block size 131072.
[==================================================================================================================================================================================================|] 2/2 100%

Exportable Squashfs 4.0 filesystem, gzip compressed, data block size 131072
        compressed data, compressed metadata, compressed fragments, compressed xattrs
        duplicates are removed
Filesystem size 20.80 Kbytes (0.02 Mbytes)
        76.13% of uncompressed filesystem size (27.32 Kbytes)
Inode table size 53 bytes (0.05 Kbytes)
        54.08% of uncompressed inode table size (98 bytes)
Directory table size 30 bytes (0.03 Kbytes)
        75.00% of uncompressed directory table size (40 bytes)
Number of duplicate files found 0
Number of inodes 3
Number of files 2
Number of fragments 1
Number of symbolic links  0
Number of device nodes 0
Number of fifo nodes 0
Number of socket nodes 0
Number of directories 1
Number of ids (unique uids + gids) 1
Number of uids 1
        gerard (1000)
Number of gids 1
        gerard (1000)
gerard@atlantis:~/squashtest$
```

Podemos ver en este caso que el tamaño del sistema de ficheros final es solamente el 76.13% de lo que era antes de comprimir. No es mucho, pero con ficheros más realistas suele comprimir más, pero de momento nos vale. Veamos el tamaño final del sistema de ficheros, que se queda en 24kb:

```bash
gerard@atlantis:~/squashtest$ ls -lh
total 28K
drwxr-xr-x 2 gerard gerard 4,0K sep 20 10:43 rootfs
-rw-r--r-- 1 gerard gerard  24K sep 20 10:44 rootfs.sqsh
gerard@atlantis:~/squashtest$
```

## Uso del sistema de ficheros

Para montar el sistema de ficheros no nos hace falta nada especial, ni ninguna de las **squashfs-tools**, al menos en *Debian*, que ya incluye el módulo de *squashfs* en el *kernel*.

 El fichero *rootfs.sqsh* no sirve por si solo; hay que montarlo. Supongamos que queremos montar nuestro nuevo sistema de ficheros en la carpeta *mount/*, que al no existir, crearemos.
 
```bash
gerard@atlantis:~/squashtest$ mkdir mount
gerard@atlantis:~/squashtest$
```

El comando de montaje no es diferente de cualquier otro, y lo podríamos poner en el */etc/fstab* para que se monte solo en cada reinicio. De momento os paso el comando de *mount* básico, que demuestra lo fácil que es de hacer:

```bash
gerard@atlantis:~/squashtest$ sudo mount rootfs.sqsh mount/
[sudo] password for gerard:
gerard@atlantis:~/squashtest$ tree mount/
mount/
├── file1
└── file2

0 directories, 2 files
gerard@atlantis:~/squashtest$
```

Como todo sistema de ficheros montado en *linux*, queda accesible en la carpeta de montaje. Para acceder a los ficheros solo necesitamos hacerlo de la forma habitual, aunque por tratarse de un sistema de ficheros de solo lectura, solo podemos leerlo, pero no escribirlo.

```bash
gerard@atlantis:~/squashtest$ touch mount/hello
touch: no se puede efectuar `touch' sobre 'mount/hello': Sistema de ficheros de sólo lectura
gerard@atlantis:~/squashtest$
```

## Añadiendo una capa de lectura y escritura

Un sistema de ficheros de lectura solo no tiene mucha utilidad en sí misma; aunque es verdad que podemos poner la jaula como solo lectura y montar una carpeta de trabajo solamente. Sin embargo hay otro método ámpliamente utilizado para hacer que parezca de lectura y escritura.

Se trata del método que utiliza la distribución [Slax](https://www.slax.org/es/). La idea es que el sistema de ficheros "final" es una carpeta en la que se montan varias capas de sistema de ficheros. Esto se consigue con sistemas de ficheros tipo *UnionFS*, *AUFS* o *overlayfs*.

De esta forma podemos tener la imagen base, posiblemente compartida por varios montajes distintos, y luego disponer de varias capas de diferencias respecto al original. Estas capas de diferencias suelen ser más pequeñas que la imagen base y se pueden descartar para volver a la versíon original de lo que teníamos en la carpeta.
