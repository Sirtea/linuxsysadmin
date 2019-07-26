---
title: "Compilando python desde cero"
slug: "compilando-python-desde-cero"
date: 2016-04-04
categories: ['Operaciones']
tags: ['linux', 'redhat', 'centos', 'python']
---

Siempre que estoy trabajando en un servidor CentOS o RedHat, veo que las versiones de *python* que usan son bastante viejas. De hecho, hay una gran mejora de *python* entre las versiones 2.4, 2.6 y 2.7; así que es frecuente compilar una versión superior para nuestro uso.<!--more-->

Para este tutorial he usado una máquina virtual con un sistema operativo *RedHat*. Realmente no necesita ninguna configuración *hardware* adicional. Lo único relevante es que estamos tratando con una versión de *RedHat* 6.

```bash
[gerard@foundry ~]$ cat /etc/redhat-release
Red Hat Enterprise Linux Server release 6.7 (Santiago)
[gerard@foundry ~]$
```

El otro requisito necesario es el fichero *tarball* con las fuentes de *python*. Esto lo podemos encontrar en [la página de *python*](https://www.python.org/). Al tiempo de escritura, la última *release* de la serie de *python* 2 era la 2.7.11.

```bash
[gerard@foundry ~]$ wget https://www.python.org/ftp/python/2.7.11/Python-2.7.11.tgz
--2016-03-29 16:27:54--  https://www.python.org/ftp/python/2.7.11/Python-2.7.11.tgz
Resolving www.python.org... 185.31.17.223
Connecting to www.python.org|185.31.17.223|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 16856409 (16M) [application/octet-stream]
Saving to: “Python-2.7.11.tgz”

100%[========================================================================================>] 16,856,409  17.3M/s   in 0.9s

2016-03-29 16:27:55 (17.3 MB/s) - “Python-2.7.11.tgz” saved [16856409/16856409]

[gerard@foundry ~]$
```

## Compilar las fuentes

Descomprimimos el *tarball* y nos situamos en la carpeta recién creada.

```bash
[gerard@foundry ~]$ tar xzf Python-2.7.11.tgz
[gerard@foundry ~]$ cd Python-2.7.11
[gerard@foundry Python-2.7.11]$
```

El procedimiento de compilación es el estándar: **configure**, **make** y **make install**. Empezamos por configurarlo. Solo voy a añadir una carpeta que no interfiera con el sistema operativo, por ejemplo, */opt/python27/*. Otro punto interesante es el modificador **--enable-shared**, para generar la librería *libpython2.7.so*, por si nos hiciera falta.

```bash
[gerard@foundry Python-2.7.11]$ ./configure --prefix=/opt/python27
checking build system type... x86_64-unknown-linux-gnu
checking host system type... x86_64-unknown-linux-gnu
...
configure: creating ./config.status
config.status: creating Makefile.pre
config.status: creating Modules/Setup.config
config.status: creating Misc/python.pc
config.status: creating Modules/ld_so_aix
config.status: creating pyconfig.h
config.status: pyconfig.h is unchanged
creating Modules/Setup
creating Modules/Setup.local
creating Makefile
[gerard@foundry Python-2.7.11]$
```

Compilamos usando **make** con el *Makefile* recién generado por el *script* **configure**.

```bash
[gerard@foundry Python-2.7.11]$ make
...
Python build finished, but the necessary bits to build these modules were not found:
_bsddb             _curses            _curses_panel
_sqlite3           _tkinter           bsddb185
bz2                dbm                dl
gdbm               imageop            readline
sunaudiodev
To find the necessary bits, look in setup.py in detect_modules() for the module's name.

running build_scripts
[gerard@foundry Python-2.7.11]$
```

Hay algunos módulos de la librería estándar que necesitan las versiones **-devel** de algunas librerías, aunque se pueden obviar y no se construyen.

Opcionalmente podemos instalar algunas de esas librerías, y tras volver a ejecutar **configure** y **make**, se construirían esos módulos.

```bash
[gerard@foundry Python-2.7.11]$ yum install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel
[gerard@foundry Python-2.7.11]$
```

Finalmente lo ponemos en su carpeta (*--prefix*) mediante **make install**. No tengo permiso de escritura en */opt/*, así que vamos a usar **sudo** para todos los comandos que impliquen la carpeta */opt/*.

```bash
[gerard@foundry Python-2.7.11]$ sudo make install
Creating directory /opt/python27/bin
Creating directory /opt/python27/lib
...
[gerard@foundry Python-2.7.11]$
```

## Comprobar que funciona

Vamos a ejecutar el binario **python** para verificar que funciona y que estamos mirando la versión que toca. Vamos a usar la ruta completa para referirnos al binario, aunque lo ideal sería que estuviera en el *PATH*.

```bash
[gerard@foundry ~]$ /opt/python27/bin/python -V
Python 2.7.11
[gerard@foundry ~]$
```

Para ver que la librería estándar funciona y es utilizable, basta con importar alguno de sus módulos e invocar alguna de sus funciones.

```bash
[gerard@foundry ~]$ /opt/python27/bin/python
Python 2.7.11 (default, Mar 29 2016, 16:42:10)
[GCC 4.4.7 20120313 (Red Hat 4.4.7-16)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import os
>>> os.uname()
('Linux', 'foundry', '3.10.0-327.10.1.el7.x86_64', '#1 SMP Sat Jan 23 04:54:55 EST 2016', 'x86_64')
>>> exit()
[gerard@foundry ~]$
```

Y con esto lo damos por bueno.

## Opcional: reduciendo el espacio ocupado en disco

Nos posicionamos en la carpeta para analizar lo que ocupa.

```bash
[gerard@foundry Python-2.7.11]$ cd /opt/python27/
[gerard@foundry python27]$
```

Miramos lo que ocupa cada carpeta dentro de la carpeta contendora.

```bash
[gerard@foundry python27]$ du -sh * | sort -h
16K     share
676K    include
6.1M    bin
94M     lib
[gerard@foundry python27]$
```

El paso mas obvio es lanzar el comando **strip**. Esto va a eliminar los símbolos de *debug* y va a reducir el tamaño de los binarios y las librerías *.so*. El resto va a ignorarse, previo mensaje de error, que vamos a ignorar.

```bash
[gerard@foundry python27]$ find -type f | sudo xargs strip 2>/dev/null
[gerard@foundry python27]$ du -sh * | sort -h
16K     share
676K    include
1.8M    bin
76M     lib
[gerard@foundry python27]$
```

Algo hemos ganado; se han liberado unos 24 mb. Como nos resulta insuficiente, inspeccionemos la carpeta mas grande, que es la carpeta *lib/*.

```bash
[gerard@foundry python27]$ du -sh lib/* | sort -h
4.0K    lib/pkgconfig
1.8M    lib/libpython2.7.a
74M     lib/python2.7
[gerard@foundry python27]$
```

La librería *libpython2.7.a* es necesaria para compilar estáticamente binarios que vayan a incorporar la librería de *python*. En este caso no la necesitamos y podemos liberar 1.8 mb adicionales.

```bash
[gerard@foundry python27]$ sudo rm lib/libpython2.7.a
[gerard@foundry python27]$ du -sh * | sort -h
16K     share
676K    include
1.8M    bin
73M     lib
[gerard@foundry python27]$
```

Continuamos mirando la carpeta mas grande, que es *lib/python2.7/*.

```bash
[gerard@foundry python27]$ du -sh lib/python2.7/* | sort -h | tail -5
2.9M    lib/python2.7/encodings
3.1M    lib/python2.7/idlelib
3.4M    lib/python2.7/distutils
3.5M    lib/python2.7/lib-dynload
29M     lib/python2.7/test
[gerard@foundry python27]$
```

Es bastante inútil que el *runtime* de *python* incluya los tests que usan los desarrolladores de *python*, y son 29 mb que podemos eliminar de forma segura.

```bash
[gerard@foundry python27]$ sudo rm -R lib/python2.7/test/
[gerard@foundry python27]$ du -sh * | sort -h
16K     share
676K    include
1.8M    bin
44M     lib
[gerard@foundry python27]$
```

Si miramos el contenido de la carpeta con detenimiento, podemos ver que cada módulo tiene 3 versiones: *.py*, *.pyc* y *.pyo*; se trata del módulo en versión código, compilado y optimizado, respectivamente.

```bash
[gerard@foundry python27]$ ls -lh lib/python2.7/os.*
-rw-r--r--. 1 root root 26K Mar 29 16:43 lib/python2.7/os.py
-rw-r--r--. 1 root root 26K Mar 29 16:43 lib/python2.7/os.pyc
-rw-r--r--. 1 root root 26K Mar 29 16:43 lib/python2.7/os.pyo
[gerard@foundry python27]$
```

Realmente solo se necesita la versión *.py*, siendo las otras para acelerar la carga del módulo. Los otros se crean al importar el módulo, y si es posible, se escriben de nuevo en la carpeta. Vamos a borrarlas.

```bash
[gerard@foundry python27]$ find -name "*.pyo" | sudo xargs rm
[gerard@foundry python27]$ find -name "*.pyc" | sudo xargs rm
[gerard@foundry python27]$ du -sh * | sort -h
16K     share
676K    include
1.8M    bin
21M     lib
[gerard@foundry python27]$
```

Mucho mejor, pero... ¿sigue funcionando **python**? Lo comprobamos como antes, y vemos que si. 

```bash
[gerard@foundry python27]$ ./bin/python -V
Python 2.7.11
[gerard@foundry python27]$ ./bin/python -c "import os; print os.uname()"
('Linux', 'foundry', '3.10.0-327.10.1.el7.x86_64', '#1 SMP Sat Jan 23 04:54:55 EST 2016', 'x86_64')
[gerard@foundry python27]$
```

## Empaquetado para usos futuros

Esta carpeta va a servir para todas las máquinas *CentOS* y *RedHat* versión 6, con la misma família de procesador (en este caso x86_64). Hacemos un fichero comprimido y lo ponemos a buen recaudo.

```bash
[gerard@foundry opt]$ tar czf ~/python27.tar.gz python27/
[gerard@foundry opt]$ ls -lh ~
total 7.2M
-rw-rw-r--. 1 gerard gerard 7.2M Mar 29 17:01 python27.tar.gz
[gerard@foundry opt]$
```

Poco mas de 7 mb... nada mal, ¿no?
