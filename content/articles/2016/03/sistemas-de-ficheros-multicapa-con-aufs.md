---
title: "Sistemas de ficheros multicapa con aufs"
slug: "sistemas-de-ficheros-multicapa-con-aufs"
date: 2016-03-28
categories: ['Operaciones']
tags: ['linux', 'debian', 'jessie', 'mount', 'aufs', 'squashfs', 'debootstrap']
---

Trabajando con contenedores tenemos una parte que se repite: el sistema de ficheros base, que copiamos siempre. Otras veces nos puede interesar hacer un sistema capaz de descartar los cambios desde un punto inicial. Podemos crear una capa base de solo lectura y añadir otra capa de cambios con **aufs**.<!--more-->

La idea es crear un sistema de ficheros que sea el resultado de mezclar otros dos: una capa de solo lectura y una capa de cambios, que podría ser de lectura y escritura. Esta nueva capa puede, a su vez, servir de base para otro sistema de ficheros.

De hecho, esta técnica de "apilado" se utiliza en la distribución de pendrive llamada [Slax](http://www.slax.org/). Mediante el apilado de módulos, mas una capa final de cambios, consiguen crear un sistema de ficheros linux entero, con una capa de cambios que se puede descartar en cualquier momento.

Empezaremos con un sistema de ficheros simulado en una carpeta, que llamaremos *base*. También pondremos una carpeta *unified* que va a ser el sistema de ficheros resultante, y una carpeta *changes* que va a alojar los cambios del sistema de ficheros respecto al sistema *base*.

```bash
root@server:~# tree
.
├── base
│   ├── bin
│   │   └── hello.sh
│   └── conf
│       └── hello.conf
├── changes
└── unified

5 directories, 2 files
root@server:~#
```

Para esta demostración nos vale poca cosa, por ejemplo un binario y su configuración. En casos algo mas complejos podría tratarse de una jaula entera de sistema operativo.

La "aplicación" y su configuración son simples, se muestran como guía, para ver como lo evolucionamos.

```bash
root@server:~# cat base/bin/hello.sh
#!/bin/bash

source conf/hello.conf

echo "Hello ${NAME}!"
root@server:~# cat base/conf/hello.conf
NAME="Gerard"
root@server:~#
```

Ahora vamos a crear el sistema combinado en la carpeta *unified*, usando la *base* como capa de solo lectura, y la carpeta *changes* como la capa de lectura escritura.

```bash
root@server:~# mount -t aufs -o br:changes=rw:base=ro none unified
root@server:~#
```

Podemos ver que la carpeta *unified* es una unión de la capa base con la de cambios. Puesto que no hay cambios, por ahora las carpetas coinciden en contenido.

```bash
root@server:~# tree
.
├── base
│   ├── bin
│   │   └── hello.sh
│   └── conf
│       └── hello.conf
├── changes
└── unified
    ├── bin
    │   └── hello.sh
    └── conf
        └── hello.conf

7 directories, 4 files
root@server:~#
```

De ahora en adelante, solo queda trabajar con el sistema de ficheros *unified*, así que vamos a trabajar en esa carpeta.

```bash
root@server:~# cd unified/
root@server:~/unified#
```

Si ejecutamos el binario, vemos que reacciona como se supone que debe hacerlo.

```bash
root@server:~/unified# ./bin/hello.sh
Hello Gerard!
root@server:~/unified#
```

En un momento dado, vemos que queremos modificar un fichero, por ejemplo, el de configuración, cambiando el parámetro **NAME**.


```bash
root@server:~/unified# cat conf/hello.conf
NAME="Gerard Monells"
root@server:~/unified#
```

Efectivamente, el resultado es el esperado.

```bash
root@server:~/unified# ./bin/hello.sh
Hello Gerard Monells!
root@server:~/unified#
```

Ahora vamos a crear nuevas carpetas y nuevos ficheros, por ejemplo, una carpeta *data* con un fichero *greetings*.

```bash
root@server:~/unified# mkdir data
root@server:~/unified# ./bin/hello.sh > data/greetings
root@server:~/unified#
```

Volvemos al nivel de carpetas anteriores, para investigar lo que está pasando.

```bash
root@server:~/unified# cd ..
root@server:~#
```

Podemos ver que el sistema *base* ha quedado intacto. De la misma forma, todas las modificaciones respecto a la base se han almacenado en la carpeta *changes*. En conjunto, nos queda la carpeta *unified* con la suma de ambos.

```bash
root@server:~# tree
.
├── base
│   ├── bin
│   │   └── hello.sh
│   └── conf
│       └── hello.conf
├── changes
│   ├── conf
│   │   └── hello.conf
│   └── data
│       └── greetings
└── unified
    ├── bin
    │   └── hello.sh
    ├── conf
    │   └── hello.conf
    └── data
        └── greetings

10 directories, 7 files
root@server:~#
```

Es fácil intuir que el fichero *greetings* es el de la capa de cambios, ya que no hay otro. En el caso del fichero *hello.conf* modificado, se ha modificado el de la capa de cambios, y es el que vemos en el punto de montaje *unified*, aunque hayan dos.

```bash
root@server:~# cat base/conf/hello.conf
NAME="Gerard"
root@server:~# cat unified/conf/hello.conf
NAME="Gerard Monells"
root@server:~# cat changes/conf/hello.conf
NAME="Gerard Monells"
root@server:~#
```

**TRUCO**: el sistema de ficheros de solo lectura *base* no tiene porque estar en una carpeta; podría tratarse se un sistema de fichero simulado montado en un fichero, montado mediante un **mount -o loop**; por ejemplo, un sistema de ficheros **squashfs**.

De hecho, como la capa *base* no se modifica, nada nos impide crear otro sistema de ficheros, a base de sumar esta misma *base* con otra capa de cambios.

```bash
root@server:~# mkdir changes2 unified2
root@server:~# mount -t aufs -o br:changes2=rw:base=ro none unified2
root@server:~#
```

Y con esto tenemos dos sistemas de ficheros, *unified* y *unified2*, que comparten una capa *base* común.

```bash
root@server:~# tree
.
├── base
│   ├── bin
│   │   └── hello.sh
│   └── conf
│       └── hello.conf
├── changes
│   ├── conf
│   │   └── hello.conf
│   └── data
│       └── greetings
├── changes2
├── unified
│   ├── bin
│   │   └── hello.sh
│   ├── conf
│   │   └── hello.conf
│   └── data
│       └── greetings
└── unified2
    ├── bin
    │   └── hello.sh
    └── conf
        └── hello.conf

14 directories, 9 files
root@server:~#
```

En este caso no supone mucho ahorro, ya que la capa base es pequeña, pero... ¿os imagináis que la capa base es una jaula entera resultado de un **debootstrap**?

De hecho, esta capa *base* compartida no hay que copiarla, con lo que ganamos tiempo al crear una jaula grande, y además, si lo juntamos con **squashfs** podemos ahorrar bastante espacio.
