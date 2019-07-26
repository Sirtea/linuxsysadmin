---
title: "Empaquetando ficheros .deb"
slug: "empaquetando-ficheros-punto-deb"
date: 2015-12-28
categories: ['Operaciones']
tags: ['linux', 'debian', 'ubuntu', 'paquete', 'deb']
---

Una de las grandes ventajas de *linux* es su sistema de paquetes. Con ellos es posible instalar de forma fácil un paquete de forma fácil y confiable. Hoy vamos a hacer un paquete *.deb* como ejemplo que instale un *script* cualquiera en la carpeta */usr/bin/* para su uso cotidiano.<!--more-->

Por limpieza, vamos a crear una carpeta temporal para hacer el empaquetado, desde donde vamos a ejecutar todo el resto del procedimiento.

```bash
root@packager:~# mkdir workspace
root@packager:~# cd workspace/
root@packager:~/workspace# 
```

## Preparación de la estructura del paquete

Vamos a poner el *script* que queramos empaquetar, respetando al estructura que tendrá una vez se instale el paquete. También le damos los permisos que va a tener una vez instalado.

```bash
root@packager:~/workspace# mkdir -p usr/bin
root@packager:~/workspace# cat usr/bin/welcome
#!/bin/bash

echo 'Hello world!'
root@packager:~/workspace# chmod 755 usr/bin/welcome
root@packager:~/workspace# 
```

## Empaquetado de la carpeta de trabajo

Antes de empaquetar de acuerdo a las políticas de los paquetes *.deb*, sea en *Debian* o en *Ubuntu*, se requiere de una carpeta **DEBIAN** con un fichero **control**, que va a contener los metadatos del paquete.

Para este fichero nos podemos guiar por la [documentación oficial](https://www.debian.org/doc/debian-policy/ch-controlfields.html). Como vamos a hacer un paquete mínimo, vamos a poner solamente los campos obligatorios y uno de los opcionales, que indicarán las necesidades de nuestro script:

* **Obligatorios**:
    * Package
    * Version
    * Architecture
    * Maintainer
    * Description
* **Opcionales**:
    * Depends

Para que el *script* pueda funcionar, hay que localizar todo aquello que pueda necesitar, y añadirlo al paquete o declarar los paquetes de los que dependa, para que se puedan instalar automáticamente si no estuvieran en el sistema destino.

Concretamente, este *script* necesita dos comandos para funcionar: **bash** y **echo**. Vamos a localizarlos a ver de que paquete provienen. La idea es que nuestro paquete va a necesitar todos los paquetes que contengan los comandos necesarios, sin necesidad de incorporarlos.

```bash
root@packager:~/workspace# which bash
/bin/bash
root@packager:~/workspace# dpkg -S /bin/bash
bash: /bin/bash
root@packager:~/workspace# which echo
/bin/echo
root@packager:~/workspace# dpkg -S /bin/echo 
coreutils: /bin/echo
root@packager:~/workspace# 
```

De ahí deducimos que necesitamos los paquetes **bash** y **coreutils**, que aunque suelen venir de serie, vale la pena declararlos por si no fuera el caso. Esto es lo que va en el campo **Depends**.

Reuniendo estos datos, podemos crear el fichero **control**, por ejemplo, como este:

```bash
root@packager:~/workspace# mkdir -p DEBIAN
root@packager:~/workspace# cat DEBIAN/control 
Package: welcome
Version: 1.0-1
Architecture: all
Maintainer: Linux Sysadmin
Description: A fancy shell script
 To demonstrate how to package a .deb file
Depends: bash, coreutils
root@packager:~/workspace# 
```

Adicionalmente, la carpeta **DEBIAN** puede contener otros *scripts*, como por ejemplo, **preinst**, **postinst**, **prerm** y **postrm**, que podrían, por ejemplo, crear los usuarios necesarios.

Como último paso, vamos a invocar el comando **dpkg-deb** para empaquetar la carpeta de trabajo.

```bash
root@packager:~/workspace# cd ..
root@packager:~# dpkg-deb --build workspace/ welcome_1.0-1_all.deb
dpkg-deb: construyendo el paquete `welcome' en `welcome_1.0-1_all.deb'.
root@packager:~# 
```

## Comprobación de que el paquete funciona

Vamos a comprobar que el paquete no está instalado, por ejemplo buscando el *script* que hemos empaquetado:

```bash
root@packager:~# which welcome
root@packager:~# welcome 
bash: /usr/bin/welcome: No existe el fichero o el directorio
root@packager:~# 
```
Efectivamente, no lo está; ahora se trata de invocar **dpkg** para instalar nuestro paquete.

```bash
root@packager:~# dpkg -i welcome_1.0-1_all.deb 
Seleccionando el paquete welcome previamente no seleccionado.
(Leyendo la base de datos ... 9984 ficheros o directorios instalados actualmente.)
Preparando para desempaquetar welcome_1.0-1_all.deb ...
Desempaquetando welcome (1.0-1) ...
Configurando welcome (1.0-1) ...
root@packager:~# 
```

Y finalmente, verificamos que tenemos nuestro *script* en */usr/bin/* como esperábamos:

```bash
root@packager:~# which welcome
/usr/bin/welcome
root@packager:~# welcome
Hello world!
root@packager:~# 
```

Y con esto tenemos nuestro paquete que podemos poner a buen recaudo.
