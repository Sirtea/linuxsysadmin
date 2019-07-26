---
title: "Usar un sistema de ficheros de lectura y escritura en un fichero .tar.gz"
slug: "usar-un-sistema-de-ficheros-de-lectura-y-escritura-en-un-fichero-targz.md"
date: 2017-10-23
categories: ['Operaciones']
tags: ['linux', 'archivemount', 'mount', 'tar', 'gz', 'targz']
---

¿Alguna vez habéis querido mirar en fichero *.tar.gz*, pero sin tener que descomprimirlo? Tal vez te gustaría extraer solo unos pocos ficheros; puede que lo que te interese es trabajar con una carpeta a la que le modificamos los archivos, sin tener que archivar esta carpeta cada cierto tiempo.<!--more-->

En este caso, tenemos un sistema de ficheros bastante interesante que se llama **archivemount**, y que nos permite ver un fichero *.tar.gz* como si de una carpeta local más se tratara. Al desmontar este sistema de fichero, se crea el mismo fichero de nuevo, de forma automática, y con previa copia del anterior.

Según la [wikipedia](https://en.wikipedia.org/wiki/Archivemount):

> archivemount is a FUSE-based file system for Unix variants, including Linux. Its purpose is to mount archives (i.e. tar, tar.gz, etc.) to a mount point where it can be read from or written to as with any other file system. This makes accessing the contents of the archive, which may be compressed, transparent to other programs, without decompressing them.

Para demostrar como funciona, necesitaremos una máquina normal. Como pienso desecharla tal como haya escrito estas palabras, voy a usar un contenedor **docker** con una **Debian Jessie**; la distribución no debería ser importante.

**TRUCO**: No se puede usar el comando **archivemount** en un contenedor **docker**, a menos que se levante con la opción *--privileged*, que es lo que yo he usado.

Vamos a empezar instalando el paquete **archivemount**, que nos va a dar las herramientas para montar nuestros ficheros comprimidos. Cada distribución lo hace a su manera; revisa la documentación de la tuya.

```bash
root@cfed45d103a2:~# apt-get install archivemount
Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following extra packages will be installed:
  fuse libalgorithm-c3-perl libarchive-extract-perl libarchive13 libcgi-fast-perl libcgi-pm-perl libclass-c3-perl libclass-c3-xs-perl libcpan-meta-perl libdata-optlist-perl
  libdata-section-perl libfcgi-perl libfuse2 libgdbm3 liblog-message-perl liblog-message-simple-perl liblzo2-2 libmodule-build-perl libmodule-pluggable-perl libmodule-signature-perl
  libmro-compat-perl libnettle4 libpackage-constants-perl libparams-util-perl libpod-latex-perl libpod-readme-perl libregexp-common-perl libsoftware-license-perl libsub-exporter-perl
  libsub-install-perl libterm-ui-perl libtext-soundex-perl libtext-template-perl libxml2 perl perl-modules rename sgml-base xml-core
Suggested packages:
  lrzip perl-doc libterm-readline-gnu-perl libterm-readline-perl-perl make libb-lint-perl libcpanplus-dist-build-perl libcpanplus-perl libfile-checktree-perl libobject-accessor-perl
  sgml-base-doc debhelper
Recommended packages:
  libarchive-tar-perl
The following NEW packages will be installed:
  archivemount fuse libalgorithm-c3-perl libarchive-extract-perl libarchive13 libcgi-fast-perl libcgi-pm-perl libclass-c3-perl libclass-c3-xs-perl libcpan-meta-perl libdata-optlist-perl
  libdata-section-perl libfcgi-perl libfuse2 libgdbm3 liblog-message-perl liblog-message-simple-perl liblzo2-2 libmodule-build-perl libmodule-pluggable-perl libmodule-signature-perl
  libmro-compat-perl libnettle4 libpackage-constants-perl libparams-util-perl libpod-latex-perl libpod-readme-perl libregexp-common-perl libsoftware-license-perl libsub-exporter-perl
  libsub-install-perl libterm-ui-perl libtext-soundex-perl libtext-template-perl libxml2 perl perl-modules rename sgml-base xml-core
0 upgraded, 40 newly installed, 0 to remove and 0 not upgraded.
Need to get 8172 kB of archives.
After this operation, 41.7 MB of additional disk space will be used.
Do you want to continue? [Y/n] y
...
root@cfed45d103a2:~# 
```

Para montar un fichero comprimido en una carpeta, necesitamos ambos, así que los creamos. El fichero comprimido va a ser un fichero *.tar.gz* vacío.

```bash
root@cfed45d103a2:~# mkdir data
root@cfed45d103a2:~# tar czvf data.tar.gz --files-from /dev/null
root@cfed45d103a2:~# 
```

Vemos como nos queda la carpeta local, con ambas cosas:

```bash
root@cfed45d103a2:~# tree
.
|-- data
`-- data.tar.gz

1 directory, 1 file
root@cfed45d103a2:~# 
```

Solo queda montar el sistema de ficheros para empezar a utilizarlo. Aunque se podría delegar el montaje del sistema de ficheros al sistema escribiendo en */etc/fstab*, vamos a hacerlo manualmente en este ejemplo.

```bash
root@cfed45d103a2:~# archivemount data.tar.gz data/
root@cfed45d103a2:~# 
```

Vamos a crear algunos ficheros en la carpeta. Es especialmente interesante fijarnos en que trabajamos con una carpeta normal, como lo haríamos habitualmente. De esta forma, hasta un *software* existente podría modificar este sistema de ficheros.

```bash
root@cfed45d103a2:~# echo "no content" > data/README
root@cfed45d103a2:~# echo "1.0" > data/VERSION
root@cfed45d103a2:~# 
```

Comprobamos lo que tenemos, solo para asegurar el éxito:

```bash
root@cfed45d103a2:~# tree
.
|-- data
|   |-- README
|   `-- VERSION
`-- data.tar.gz

1 directory, 3 files
root@cfed45d103a2:~# 
```

Cuando acabemos de trabajar con el sistema de ficheros y se desmonte, pasará la magia; se va a comprimir el sistema de ficheros en el fichero *.tar.gz* con el nombre inicial, previa copia del antiguo.

```bash
root@cfed45d103a2:~# umount data
root@cfed45d103a2:~# 
```

Podemos ver que el sistema de ficheros ya no está disponible, como esperaríamos de un *umount*; el fichero que montamos en su momento ha quedado como *data.tar.gz.orig*, y el fichero *data.tar.gz* tiene el contenido actualizado de nuestra sesión de trabajo.

```bash
root@cfed45d103a2:~# tree
.
|-- data
|-- data.tar.gz
`-- data.tar.gz.orig

1 directory, 2 files
root@cfed45d103a2:~# 
```

Podemos comprobar el contenido simplemente verificando lo que hay en los ficheros:

```bash
root@cfed45d103a2:~# tar tzf data.tar.gz
tar: Removing leading `/' from member names
/README
/VERSION
root@cfed45d103a2:~# tar tzf data.tar.gz.orig 
root@cfed45d103a2:~# 
```

Y como podíamos esperar, el fichero *data.gz.orig* está vacío y el fichero *data.tar.gz* contiene los nuevos ficheros. Es importante recalcar que si se volviera a montar y desmontar el sistema de ficheros -y hubieran cambios en el mismo-, se volvería a crear el fichero *data.tar.gz*, y el *data.tar.gz.orig* quedaría sobrescrito de nuevo.
