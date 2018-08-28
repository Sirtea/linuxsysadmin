Title: Ajustando bloques de disco reservado con tune2fs
Slug: ajustando-bloques-de-disco-reservado-con-tune2fs
Date: 2018-09-03 10:00
Category: Operaciones
Tags: bloques reservados, tune2fs



Llega el momento que tantas veces hemos repetido: montamos un servidor para una función concreta, y le asignamos un disco o partición a la carpeta que va a alojar la cantidad creciente de datos necesarios. De repente nos fijamos en que la capacidad del disco se ha perdido tras formatear.

No, no es una broma; solo tenemos que ver un ejemplo. Supongamos que asignamos un disco de 1 terabyte (no son difíciles ni caros de comprar hoy en día) a una máquina que lo va a necesitar para alojar todo lo referente a un entorno con **docker**.

```bash
gerard@docker:~$ df -h
S.ficheros     Tamaño Usados  Disp Uso% Montado en
...
/dev/sda1        7,9G   1,3G  6,2G  17% /
/dev/sdb1       1007G    77M  956G   1% /var/lib/docker
gerard@docker:~$
```

**¿Véis en `/dev/sdb1` que el tamaño usado y el disponible no coinciden con el tamaño del disco? Hay 50 gigabytes desaparecidos!**

Este es un fenómeno que se da al formatear un disco con formato ext2, ext3 o ext4. Esto es así porque, muchas veces, este tipo de particiones sirven para alojar ficheros de sistema. Cuando estas particiones se llenan, el sistema deja de funcionar como es debido.

La solución que los desarrolladores de los sistemas de ficheros extX encontraron fue la de reservar un bloque del disco (un 5% por defecto) al que solo puede acceder **root** o algún servicio que ejecute como **root**. Esto es fácil de comprobar:

```bash
gerard@docker:~$ sudo tune2fs -l /dev/sdb1 | egrep -i "block (count|size)"
Block count:              268435200
Reserved block count:     13421760
Block size:               4096
gerard@docker:~$
```

Vemos que se han reservado 13421760 bloques de 4096 bytes (un 5% de todos los bloques). Usando la calculadora, nos salen 51,2 gigabytes, que es la cantidad en la que difiere el comando `df`.

Como esta partición no necesita un trato especial si se llena, podemos reducir el porcentaje de bloques reservados, exactamente a 0:

```bash
gerard@docker:~$ sudo tune2fs -m 0 /dev/sdb1
tune2fs 1.43.4 (31-Jan-2017)
Se pone el porcentaje de bloques reservados a 0% (0 bloques)
gerard@docker:~$
```

Si volvemos a mirar con `tune2fs` los bloques reservados, veremos que ya no se reserva ninguno, que es el 0% solicitado.

```bash
gerard@docker:~$ sudo tune2fs -l /dev/sdb1 | egrep -i "block (count|size)"
Block count:              268435200
Reserved block count:     0
Block size:               4096
gerard@docker:~$
```

Un nuevo vistazo con el comando `df` nos mostrará que ya no hay 50gb desaparecidos:

```bash
gerard@docker:~$ df -h
S.ficheros     Tamaño Usados  Disp Uso% Montado en
...
/dev/sda1        7,9G   1,3G  6,2G  17% /
/dev/sdb1       1007G    77M 1007G   1% /var/lib/docker
gerard@docker:~$
```

Puestos a revisar el tamaño de la reserva, podemos mirar la partición `/dev/sda1`. En esta partición reside el sistema operativo, y necesita algunos bloques reservados, por si acaso. Sin embargo, el tamaño de los discos crece y el tamaño reservado de forma porcentual, también; no es lo mismo reservar el 5% de 4gb que de 400gb...

Personalmente creo que hay que dejar algún bloque reservado, pero con una partición de 8gb, el 5% son 400mb. Esto me parece una barbaridad, y creo que sobra espacio de emergencia. Si bajamos ese porcentaje al 1%, estaríamos hablando de 80mb de reserva, que son más que suficientes para acceder a liberar espacio si se llenara.

```bash
gerard@docker:~$ sudo tune2fs -m 1 /dev/sda1
tune2fs 1.43.4 (31-Jan-2017)
Se pone el porcentaje de bloques reservados a 1% (20966 bloques)
gerard@docker:~$
```

Ahora podemos verificar que los bloques reservados bajan al 1%, lo que nos deja con 20966 bloques de 4096 bytes (unos 82mb).

```bash
gerard@docker:~$ sudo tune2fs -l /dev/sda1 | egrep -i "block (count|size)"
Block count:              2096640
Reserved block count:     20966
Block size:               4096
gerard@docker:~$
```

Así pues, liberamos unos 320mb, lo que nos deja algo más de espacio para lo que podamos necesitar.

```bash
gerard@docker:~$ df -h
S.ficheros     Tamaño Usados  Disp Uso% Montado en
...
/dev/sda1        7,9G   1,3G  6,5G  17% /
/dev/sdb1       1007G    77M 1007G   1% /var/lib/docker
gerard@docker:~$
```
