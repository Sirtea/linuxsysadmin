---
title: "Reduciendo el tamaño de nuestros binarios con musl libc"
slug: "reduciendo-el-tamano-de-nuestros-binarios-con-musl-libc"
date: 2016-05-16
categories: ['Seguridad']
tags: ['linux', 'musl', 'libc', 'chroot', 'jaula']
---

Cuando construimos jaulas, por el motivo que sea, vemos que no quedan pequeñas. El problema es el conjunto de librerías que hay que poner en el caso de los binarios *dinámicos*, o el exceso de tamaño en el caso de los *estáticos*. Cambiando la librería base, podemos reducir su tamaño.<!--more-->

La mayoría de los binarios de un sistema *linux* necesitan una librería llamada *libc*. La que suelen poner en todas las distribuciones es la **GNU libc**, que es compatible con todos los proyectos de software libre y no suele dar problemas.

Sin embargo, no es la única; si tenemos un binario que se puede compilar con estas otras librerías, la reducción de tamaño suele ser importante. Esto no nos preocupa en un sistema "normal" porque el disco es barato, pero es frustrante cuando tenemos que cargar cientos de megas para poner solamente un par de servicios en una jaula.

Así que vamos a crear una jaula usando **musl libc** como demostración, para ver como se reducen la cantidad de librerías y el tamaño de la jaula.

## El compilador que enlaza con musl libc

La librería de **musl libc** puede usarse de dos formas: construir una *toolchain* dedicada o usar un *wrapper* de la que tengamos en el sistema. Como la primera merecería un artículo por sí misma, usaremos la segunda. Es digno de mención indicar que existen *toolchains* prefabricadas.

El procedimiento para instalar el *wrapper* de **musl libc** es relativamente simple; se trata del típico procedimiento *configure && make && make install*. Para ello vamos a necesitar algunas herramientas:

```bash
root@musl:~# apt-get install wget gcc make
...
root@musl:~#
```

Nos descargamos la versión de **musl libc** que queramos utilizar usando el comando *wget*.

```bash
root@musl:~# wget https://www.musl-libc.org/releases/musl-1.1.14.tar.gz
...
root@musl:~#
```

Descomprimimos el *tarball* descargado y nos ponemos en la carpeta creada.

```bash
root@musl:~# tar xzf musl-1.1.14.tar.gz
root@musl:~# cd musl-1.1.14
root@musl:~/musl-1.1.14#
```

Vamos a configurar el paquete, con lo que se va a generar un *Makefile* compatible con nuestro sistema. Es un buen momento para indicar la carpeta que va a contener el "compilador".

```bash
root@musl:~/musl-1.1.14# ./configure --prefix=/opt/musl/
...
root@musl:~/musl-1.1.14#
```

Una vez obtenido el *Makefile*, podemos construir el "compilador" con la orden *make*. Si tenéis la suerte de contar con mas de un procesador, podéis acelerar este paso con el *flag* **-j2**, por ejemplo (serían dos threads); lo ideal poner el número de núcleos disponibles.

```bash
root@musl:~/musl-1.1.14# make
...
root@musl:~/musl-1.1.14#
```

Y con los binarios construidos, los ponemos en su sitio con *make install*. Puesto que indicamos un *prefix* en el *configure*, va a crear esa carpeta, creando en ella las carpetas necesarias (por ejemplo, *bin* y *lib*).

```bash
root@musl:~/musl-1.1.14# make install
...
root@musl:~/musl-1.1.14#
```

Cuando el *make install* haya funcionado, podemos salir de la carpeta de fuentes y eliminarla. En este caso, lo importante ha quedado en */opt/musl/*.

```bash
root@musl:~/musl-1.1.14# cd ..
root@musl:~# rm -R musl-1.1.14*
root@musl:~#
```

## Construyendo una jaula de ejemplo

Supongamos que tenemos un código fuente de un ejecutable que queremos en la jaula. En este caso vamos a hacer un sencillo programa:

```bash
root@musl:~# cat hello.c
#include "stdio.h"
#include "stdlib.h"

int main() {
    printf("Hello world!\n");
    exit(0);
}
root@musl:~#
```

### Versión estática

Compilamos nuestro binario con el *flag* **-static**. Eso hace que el binario incluya lo que necesita de **musl libc**, con lo que no va a necesitar ninguna librería de sistema. Este binario debería funcionar en todas las máquinas con la misma arquitectura (en mi caso, x86). No os olvidéis del *strip*, que va a eliminar los símbolos de *debug* y reduce el tamaño del binario.

```
root@musl:~# /opt/musl/bin/musl-gcc -static -o hello hello.c
root@musl:~# strip hello
root@musl:~#
```

Creamos una carpeta para la jaula, en la que ponemos nuestro ejecutable, sin nada mas, porque no lo necesita.

```bash
root@musl:~# mkdir jail_static
root@musl:~# cp hello jail_static/
root@musl:~# tree jail_static/ -h
jail_static/
└── [4.9K]  hello

0 directories, 1 file
root@musl:~#
```

Lanzamos un *chroot* que va modificar la percepción de las carpetas; a todos los efectos, *jail_static/* va a ser */* mientras el comando lanzado no acabe. Esto implica que nuestro binario estaría en la raíz de la jaula.

```bash
root@musl:~# chroot jail_static/ /hello
Hello world!
root@musl:~#
```

Vemos que funciona y que solo hemos necesitado 5 kilobytes para nuestra jaula. Obviamente, vamos a necesitar algo mas para poner un servicio completo.

Hay que indicar que varios binarios posiblemente llevarían incrustados los mismos pedazos de **musl libc** duplicando código, y que para actualizar la librería habría que recompilarlos todos con la nueva versión.

### Versión dinámica

Que nuestro binario sea dinámico implica que no incluye ningún código de **musl libc**, así que la va a necesitar cerca para funcionar. La ventaja es los binarios son independientes de la librería usada, que podemos actualizar simplemente cambiándola por la nueva, sin recompilar los binarios.

Para compilar este caso no vamos a indicar ningún *flag* de compilación, ya que el formato dinámico es el habitual.

```bash
root@musl:~# /opt/musl/bin/musl-gcc -o hello hello.c
root@musl:~# strip hello
root@musl:~#
```

La parte mala es que este binario no funciona sin sus librerías, que podemos buscar con *ldd*:

```bash
root@musl:~# ldd hello
./hello: error while loading shared libraries: /usr/lib/i386-linux-gnu/libc.so: invalid ELF header
root@musl:~#
```

Desgraciadamente, el *ldd* del sistema funciona con la librería del sistema. La funcionalidad del *ldd* para **musl libc** la proporciona la misma librería, siempre que se llame *ldd*. Hacer un enlace nos basta.

```
root@musl:~# ln -s /opt/musl/lib/libc.so ldd
root@musl:~# ./ldd hello
        /lib/ld-musl-i386.so.1 (0xb7757000)
        libc.so => /lib/ld-musl-i386.so.1 (0xb7757000)
root@musl:~# ldd /lib/ld-musl-i386.so.1
        statically linked
root@musl:~#
```

Como vemos, nuestro binario necesita el fichero */lib/ld-musl-i386.so.1*, y este a ninguno mas. Con esta información podemos montar la jaula. Cabe decir que la librería puede reducirse con el comando *strip*.

```bash
root@musl:~# mkdir jail_dynamic
root@musl:~# mkdir jail_dynamic/lib
root@musl:~# cp hello jail_dynamic/
root@musl:~# cp /lib/ld-musl-i386.so.1 jail_dynamic/lib/
root@musl:~# strip jail_dynamic/lib/ld-musl-i386.so.1
root@musl:~# tree jail_dynamic/ -h
jail_dynamic/
├── [2.2K]  hello
└── [4.0K]  lib
    └── [531K]  ld-musl-i386.so.1

1 directory, 2 files
root@musl:~#
```

Y como es de esperar, la jaula funciona como se espera:

```bash
root@musl:~# chroot jail_dynamic/ /hello
Hello world!
root@musl:~#
```

En este caso, la jaula ocupa mas que la versión estática. En el caso de haber mas binarios, podría salirnos a cuenta; desde luego, en este caso no hay beneficio ninguno, y además tenemos una complejidad adicional. Valorad cada caso individualmente.
