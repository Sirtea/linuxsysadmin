---
title: "Algunos trucos varios para bash y systemd"
slug: "algunos-trucos-varios-para-bash-y-systemd"
date: "2022-04-29"
categories: ["Operaciones"]
tags: ["bash", "systemd"]
---

A veces descubrimos algunos trucos que no merecen un artículo en sí mismos. Para
estos casos, una opción es dejarlos olvidados en algún apartado remoto de la memoria;
como no queremos tener que recordar, me voy a limitar a dejarlos por aquí como ideas
para cuando se puedan utilizar.<!--more-->

## Usando cadenas aleatorias

Algunas veces nos puede interesar disponer de cierta aleatoriedad en nuestros *scripts*.
Si estos se hacen utilizando **bash**, disponemos de la función `$RANDOM` que devuelve
un número de 0 a 32767, sacado de la fuente de entropía de nuestro sistema (por ejemplo,
de `/dev/random` o `/dev/urandom`).

```bash
gerard@debian:~$ echo $RANDOM
26639
gerard@debian:~$
```

Si queremos un valor algo más acotado, podemos utilizar aritmética básica. Por ejemplo,
para tener un resultado de una tirada de dado, podemos hacer:

```bash
gerard@debian:~$ echo $((1 + $RANDOM % 6))
4
gerard@debian:~$
```

Si por contra necesitamos un resultado un poco más elaborado, ya necesitaríamos utilizar
**python** o **perl**. Una notable excepción son los valores que el mismo *kernel* de
Linux ya nos ofrecen de serie, por ejemplo, un UUID:

```bash
gerard@debian:~$ cat /proc/sys/kernel/random/uuid
970b8777-6768-4d53-8252-8f264a3950ec
gerard@debian:~$ cat /proc/sys/kernel/random/uuid
5093ca94-5d26-4e12-99eb-03ae4b22fc93
gerard@debian:~$ cat /proc/sys/kernel/random/uuid
6cfa28af-0f48-4572-ad7b-9afa77b41b3f
gerard@debian:~$
```

## Generando marcas temporales

Estoy harto de utilizar *scripts* de *backups* de forma automatizada; algunos de ellos
se lanzan desde procesos tipo **cron**. Para su fácil organización, la mayoría suelen
llevar algún tipo de marca temporal que indican el momento en el que se hizo ese *backup*.

En el caso concreto de **bash**, podemos invocar el comando `date`, que dispone de todo
tipo de formatos de salida, e incluso nos ofrece la posibilidad de operar en UTC
(*flag* `-u`) o en hora local.

Algunos formatos útiles pasan por:

* `%Y`, `%m`, `%d` &rarr; Año (4 dígitos), mes y día (2 dígitos)
* `%F` &rarr; Fecha en formato ISO, equivale a `%Y-%m-%d`
* `%H`, `%M`, `%S` &rarr; Hora, minuto y segundo (2 dígitos)
* `%T` &rarr; Tiempo en formato ISO, equivale a `%H:%M:%S`
* `%s` &rarr; *UNIX timestamp* (segundos transcurridos desde el tiempo "0" de UNIX, que es 1970-01-01 00:00:00 UTC)
* `%N` &rarr; Nanosegundos de la hora actual; se puede intercalar un dígito para limitar el número de decimales (por ejemplo, `%3N` serían 3 dígitos, equivalente a milisegundos).

Así pues, mis *backups* suelen tener fecha y hora sin caracteres irrelevantes:

```bash
gerard@debian:~$ touch backup_$(date "+%Y%m%d_%H%M%S").tar.gz
gerard@debian:~$ ls -1 backup_*
backup_20220429_004536.tar.gz
gerard@debian:~$
```

Si necesito valores numéricos diferentes entre dos ejecuciones muy seguidas, añado los
nanosegundos o una porción de los mismos (décimas, microsegundos, milisegundos...):

```bash
gerard@debian:~$ date -u +%s.%3N
1651186083.154
gerard@debian:~$
```

## Limpiando los logs de systemd

Cuando **systemd** ejecuta un binario o un *script*, muchas veces este último no recoge
su salida estándar o la de error; esto va a parar a un "*logger* de oficio" que es el
**systemd journal**. Esto nos permite consultarlos con el comando `journalctl -u <servicio>`.

El problema de esta aproximación es que los *logs* se acumulan en ficheros en
`/var/log/journal/`, que no podemos ver con un usuario normal y que se suelen acumular
sin control por parte de herramientas externas como **logrotate**.

Si fuera necesario hacer algún tipo de eliminación de estos *logs*, también se nos ofrece
una forma fácil de hacerlo; basta con invocar `journalctl` con algunos *flags* relacionados:

* `--rotate` &rarr; Causa que el fichero activo de *log* se archive, lo que lo hace susceptible de ser afectado por el resto de *flags*.
* `--vacuum-size` &rarr; Limpia ficheros inactivos suficientes para limitar el espacio, aunque no va a borrar el fichero activo.
* `--vacuum-time` &rarr; Limpia todas las entradas de los ficheros inactivos para intentar mantener el tiempo indicado.
* `--vacuum-files` &rarr; Limpia ficheros inactivos para intentar mantener el número indicado.

**AVISO**: Si se indican a "0" no se hace nada; se considera que esto equivale a deshabilitar el *flag*.

**TRUCO**: Se pueden combinar estos *flags* para conseguir un efecto más restrictivo.

Por ejemplo, para mantener 7 días de *logs*, utilizaría:

```bash
gerard@debian:~$ sudo journalctl --vacuum-time=7d
Vacuuming done, freed 0B of archived journals from /run/log/journal.
Vacuuming done, freed 0B of archived journals from /var/log/journal/aa7ee5a5eb1442d98c8013df2c83d857.
Vacuuming done, freed 0B of archived journals from /var/log/journal.
gerard@debian:~$
```

Si quisiera mantener los *logs* en un tamaño estable, trabajaría con el tamaño:

```bash
gerard@debian:~$ sudo journalctl --vacuum-size=100M
Vacuuming done, freed 0B of archived journals from /var/log/journal/aa7ee5a5eb1442d98c8013df2c83d857.
Vacuuming done, freed 0B of archived journals from /run/log/journal.
Vacuuming done, freed 0B of archived journals from /var/log/journal.
gerard@debian:~$
```

Finalmente, para hacer una limpieza total, mantendría un solo fichero (el activo), no sin antes vaciarlo con un rotado...

```bash
gerard@debian:~$ sudo journalctl --rotate --vacuum-files=1
Deleted archived journal /var/log/journal/aa7ee5a5eb1442d98c8013df2c83d857/system@02c71151a6f749389e6d3ceb1a3c57c4-0000000000005c65-0005dc5bf6c5d381.journal (8.0M).
Deleted archived journal /var/log/journal/aa7ee5a5eb1442d98c8013df2c83d857/user-1000@61d7facc2a7c4cf3870e43c452e62b7a-0000000000005c66-0005dc5bf6ea60fa.journal (8.0M).
Vacuuming done, freed 16.0M of archived journals from /var/log/journal/aa7ee5a5eb1442d98c8013df2c83d857.
Vacuuming done, freed 0B of archived journals from /var/log/journal.
Vacuuming done, freed 0B of archived journals from /run/log/journal.
gerard@debian:~$
```
