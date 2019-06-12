Title: LVM: logical volume manager
Slug: lvm-logical-volume-manager
Date: 2016-01-18 09:00
Category: Operaciones
Tags: linux, lvm, logical volume manager



Cuando eres un usuario medio no te complicas; particionas tu disco, a menudo usando un sistema de particionado guiado e instalas tu sistema operativo favorito. El problema es cuando las particiones se te quedan cortas. Para estos casos, se inventó una tecnología llamada *logical volume manager*, usando sus siglas: **LVM**.

LVM es una implementación de un administrador de volúmenes lógicos para el kernel Linux. Se escribió originalmente en 1998 por Heinz Mauelshagen, que se basó en el administrador de volúmenes de Veritas usado en sistemas HP-UX.

Lo que hay que saber es que las "particiones" son ahora *logical volumes*, que son particiones de un *volume group*. A su vez, este *volume group* es una agrupación de discos físicos, *physical volume* en el argot de **LVM**.

La ventaja de **LVM** es que podemos redimensionar nuestros *logical volumes* (siempre que el sistema de ficheros lo permita) y que podemos añadir y quitar *physical volumes* a nuestros *volume groups*, a efectos de incrementar su espacio disponible.

Usos frecuentes para **LVM**:

* Dimensionado de discos en caliente
* Creación de particiones de espacio limitado
* Capacidad para crear *snapshots point-in-time*

## Un ejemplo

Partimos de una máquina virtual con cualquier distribución *Linux*, por ejemplo *Debian*, que dispone de 2 discos adicionales dedicados para **LVM**. Con uno bastaría, pero ya pongo los dos para tenerlo hecho cuando el tutorial avance.

```bash
root@server:~# fdisk -l /dev/sdb

Disco /dev/sdb: 8 GiB, 8589934592 bytes, 16777216 sectores
Unidades: sectores de 1 * 512 = 512 bytes
Tamaño de sector (lógico/físico): 512 bytes / 512 bytes
Tamaño de E/S (mínimo/óptimo): 512 bytes / 512 bytes
root@server:~# fdisk -l /dev/sdc

Disco /dev/sdc: 4 GiB, 4294967296 bytes, 8388608 sectores
Unidades: sectores de 1 * 512 = 512 bytes
Tamaño de sector (lógico/físico): 512 bytes / 512 bytes
Tamaño de E/S (mínimo/óptimo): 512 bytes / 512 bytes
root@server:~# 
```

Los discos que forman un *volume group* no necesitan tener el mismo tamaño; así que con uno de 8 GB y otro de 4 GB tendremos bastante.

Nos aseguramos que tenemos el paquete **lvm2** instalado, y si no lo estuviera, lo instalamos.

```bash
root@server:~# apt-get install lvm2
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias       
Leyendo la información de estado... Hecho
...
Se instalarán los siguientes paquetes NUEVOS:
  dmeventd libdevmapper-event1.02.1 liblvm2cmd2.02 libreadline5 lvm2
0 actualizados, 5 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 1.530 kB de archivos.
Se utilizarán 3.898 kB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
root@server:~# 
```

Vamos a crear un *volume group* con 1 solo disco. Así que primero vamos a preparar */dev/sdb* como *physical volume*.

```bash
root@server:~# pvcreate /dev/sdb 
  Physical volume "/dev/sdb" successfully created
root@server:~# 
```

Y ahora creamos un *volume group* a partir del nuevo *physical volume*

```bash
root@server:~# vgcreate vg1 /dev/sdb 
  /proc/devices: No entry for device-mapper found
  Volume group "vg1" successfully created
root@server:~# 
```

Vemos que tenemos un *volume group* llamado **vg1** y que dispone de 8 GB, todos ellos libres.

```bash
root@server:~# vgs
  VG   #PV #LV #SN Attr   VSize VFree
  vg1    1   0   0 wz--n- 8,00g 8,00g
root@server:~# 
```

Nos gustaría que nuestros usuarios tuvieran una partición dedicada, así quedarán limitados en el espacio que pueden usar, sin molestar el resto del sistema operativo. En el argot de **LVM** se trata de un *logical volume*. Lo creamos, por ejemplo de 5 GB:

```bash
root@server:~# lvcreate vg1 -L 5G -n users
  Logical volume "users" created
root@server:~# 
```

Miramos la salida de los comandos **lvs**, **vgs** y **pvs**: sin sorpresas. Tenemos un *logical volume* de 5 GB, al *volume group* le quedan 3 GB igual que al *physical volume* subyacente.

```bash
root@server:~# lvs
  LV    VG   Attr       LSize Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  users vg1  -wi-a----- 5,00g                                                    
root@server:~# vgs
  VG   #PV #LV #SN Attr   VSize VFree
  vg1    1   1   0 wz--n- 8,00g 3,00g
root@server:~# pvs
  PV         VG   Fmt  Attr PSize PFree
  /dev/sdb   vg1  lvm2 a--  8,00g 3,00g
root@server:~# 
```

Sabiendo que ahora tenemos un dispositivo nuevo de 5 GB en */dev/vg1-users*, lo formateamos y lo montamos como cualquier otra partición.

```bash
root@server:~# mkfs.ext4 /dev/mapper/vg1-users 
mke2fs 1.42.12 (29-Aug-2014)
Se está creando El sistema de ficheros con 1310720 4k bloques y 327680 nodos-i

UUID del sistema de ficheros: 44788452-bbb4-42e3-a5f3-4a1cfa50cabb
Respaldo del superbloque guardado en los bloques: 
	32768, 98304, 163840, 229376, 294912, 819200, 884736

Reservando las tablas de grupo: hecho                           
Escribiendo las tablas de nodos-i: hecho                           
Creando el fichero de transacciones (32768 bloques): hecho
Escribiendo superbloques y la información contable del sistema de ficheros: hecho

root@server:~# tune2fs -m0 /dev/mapper/vg1-users 
tune2fs 1.42.12 (29-Aug-2014)
Se pone el porcentaje de bloques reservados a 0% (0 bloques)
root@server:~# mount /dev/mapper/vg1-users /home/
root@server:~# df -h /home
S.ficheros            Tamaño Usados  Disp Uso% Montado en
/dev/mapper/vg1-users   4,8G    10M  4,8G   1% /home
root@server:~# 
```

Tal como pasa el tiempo, vemos que los 5 GB de los usuarios se nos quedan cortos y decidimos que necesitan 10 GB. Como el *volume group* no tiene 5 GB mas, hay que ampliarlo.

Así pues, ponemos otro disco en la máquina, lo preparamos como *physical volume* y lo asignamos al *volume group*.

```bash
root@server:~# pvcreate /dev/sdc
  Physical volume "/dev/sdc" successfully created
root@server:~# vgextend vg1 /dev/sdc
  Volume group "vg1" successfully extended
root@server:~# 
```

Así nos queda el *volume group*: tiene 12 GB y se compone de dos *physical volumes*, uno de 8 GB y el otro de 4 GB, aunque para nosotros, el *volume group* es una masa uniforme de información, sin importar en que disco cae.

```bash
root@server:~# vgs
  VG   #PV #LV #SN Attr   VSize  VFree
  vg1    2   1   0 wz--n- 11,99g 6,99g
root@server:~# pvs
  PV         VG   Fmt  Attr PSize PFree
  /dev/sdb   vg1  lvm2 a--  8,00g 3,00g
  /dev/sdc   vg1  lvm2 a--  4,00g 4,00g
root@server:~# 
```

Ya estamos en disposición de reclamar los 10 GB que necesitamos, así que **extendemos** el *logical volume*.

```bash
root@server:~# lvs
  LV    VG   Attr       LSize Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  users vg1  -wi-ao---- 5,00g                                                    
root@server:~# lvextend /dev/mapper/vg1-users -L 10G
  Size of logical volume vg1/users changed from 5,00 GiB (1280 extents) to 10,00 GiB (2560 extents).
  Logical volume users successfully resized
root@server:~# lvs
  LV    VG   Attr       LSize  Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  users vg1  -wi-ao---- 10,00g                                                    
root@server:~# 
```

Como curiosidad, se han absorbido 2 GB adicionales de cada *physical volume*.

```
root@server:~# pvs
  PV         VG   Fmt  Attr PSize PFree
  /dev/sdb   vg1  lvm2 a--  8,00g    0 
  /dev/sdc   vg1  lvm2 a--  4,00g 1,99g
root@server:~# 
```

Y un último detalle: a pesar de que la nueva "partición" dispone de 10 GB, el sistema de fichero subyacente no lo sabe, y solo tiene *inodos* para indexar 5 GB de datos.

```bash
root@server:~# df -h /home/
S.ficheros            Tamaño Usados  Disp Uso% Montado en
/dev/mapper/vg1-users   4,8G    10M  4,8G   1% /home
root@server:~# 
```

Por suerte para nosotros, el sistema de ficheros usado es *ext4*, que nos permite redimensionarlo.

```bash
root@server:~# resize2fs /dev/mapper/vg1-users 
resize2fs 1.42.12 (29-Aug-2014)
El sistema de ficheros de /dev/mapper/vg1-users está montado en /home; hace falta cambiar el tamaño en línea
old_desc_blocks = 1, new_desc_blocks = 1
The filesystem on /dev/mapper/vg1-users is now 2621440 (4k) blocks long.

root@server:~# 
```

Y con esto, el sistema de ficheros de */home* ya tiene el nuevo tamaño disponible y listo para usar:

```bash
root@server:~# df -h /home/
S.ficheros            Tamaño Usados  Disp Uso% Montado en
/dev/mapper/vg1-users   9,8G    12M  9,7G   1% /home
root@server:~# 
```

Y con esto queda listo. Para hacer el montaje permanente, basta con añadir la línea adecuada a */etc/fstab*.
