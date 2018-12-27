Title: Un repositorio de Debian con reprepro
Slug: un-repositorio-de-debian-con-reprepro
Date: 2016-01-11 08:00
Category: Sistemas
Tags: linux, debian, repositorio, reprepro, nginx, gpg, apt



Una de las grandes facilidades que nos ofrece una distribución de Linux es su sistema de gestor de paquetes. Los paquetes oficiales nos simplifican la instalación y mantenimiento de paquetes; sin embargo, podemos sacar provecho del sistema de paquetes para uso personal, para automatizar instalaciones y actualizaciones que queramos hacer.

En este artículo vamos a crear un repositorio en el que podemos poner paquetes, sean sacados del repositorio oficial (para hacer de caché), o sean paquetes creados por nosotros con aplicativos propios o empaquetados a partir de paquetes no libres.

Para hacerlo, necesitamos una máquina en donde pondremos el repositorio, y a efectos de demostración, una máquina en donde instalaremos paquetes de dicho repositorio. En este caso, usaremos como *LXC* tecnología para crear las máquina virtuales.

```bash
root@lxc:~# lxc-ls -f
NAME        STATE    IPV4      IPV6  AUTOSTART  
----------------------------------------------
client      RUNNING  10.0.0.3  -     YES        
repository  RUNNING  10.0.0.2  -     YES        
root@lxc:~# 
```

## Montando el repositorio

Un repositorio *Debian* no es mas que un servidor web sirviendo una estructura de ficheros con una forma concreta, que vamos a crear con **reprepro** y vamos a servir con **nginx**. Así pues, los instalamos.

```bash
root@repository:~# apt-get install reprepro nginx-light
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias       
Leyendo la información de estado... Hecho
...
Se instalarán los siguientes paquetes NUEVOS:
  ca-certificates gnupg-agent gnupg2 libarchive13 libassuan0 libcurl3-gnutls libffi6 libgmp10 libgnutls-deb0-28 libgpgme11 libhogweed2 libidn11 libksba8 libldap-2.4-2
  liblzo2-2 libnettle4 libp11-kit0 libpth20 librtmp1 libsasl2-2 libsasl2-modules libsasl2-modules-db libssh2-1 libtasn1-6 libxml2 nginx-common nginx-light openssl
  pinentry-curses reprepro sgml-base xml-core
0 actualizados, 32 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 7.645 kB de archivos.
Se utilizarán 21,2 MB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
root@repository:~# 
```

Un repositorio necesita una clave **gpg** para firmar los paquetes que sirve; aunque de eso se encarga **reprepro**, tenemos que generarla:

```bash
root@repository:~# gpg --gen-key
gpg (GnuPG) 1.4.18; Copyright (C) 2014 Free Software Foundation, Inc.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
...
gpg: /root/.gnupg/trustdb.gpg: se ha creado base de datos de confianza
gpg: clave C1B88DF7 marcada como de confianza absoluta
claves pública y secreta creadas y firmadas.
...
root@repository:~# 
```

Ahora podemos ver que las claves se han creado y podemos anotar su identificador para continuar con el procedimiento.

```bash
root@repository:~# gpg --list-keys
/root/.gnupg/pubring.gpg
------------------------
pub   2048R/C1B88DF7 2016-01-07
uid                  Gerard Monells <gerard.monells@gmail.com>
sub   2048R/5C5B84E3 2016-01-07

root@repository:~# 
```

Vamos a crear el repositorio en */opt/repo/*, con una carpeta *public* que es lo que vamos a servir con **nginx**.

```bash
root@repository:~# mkdir -p /opt/repo/{conf,public}
root@repository:~# 
```

Por comodidad, vamos a trabajar en la carpeta base del repositorio.

```bash
root@repository:~# cd /opt/repo
root@repository:/opt/repo# 
```

Un repositorio hecho con **reprepro** se declara mediante un fichero de configuración, que vamos a crear en la carpeta *conf*, declarando el nombre del repositorio, las arquitecturas y la clave con la que se firman los paquetes.

```bash
root@repository:/opt/repo# cat conf/distributions 
Codename: linuxsysadmin
Components: main
Architectures: i386
SignWith: C1B88DF7
root@repository:/opt/repo# 
```

Vamos a poner la parte pública de nuestra clave **gpg** en la raíz del servidor web, para que los clientes puedan agregarla a su almacén de claves, para usar sin problemas los paquetes de nuestro repositorio.

```bash
root@repository:/opt/repo# gpg -a --export C1B88DF7 > /opt/repo/public/key.gpg
root@repository:/opt/repo# 
```

Ahora vamos a poner una configuración a **nginx** que nos permita servir la carpeta pública en el puerto web.

```bash
root@repository:/opt/repo# cat /etc/nginx/sites-enabled/repository
server {
	server_name localhost;
	root /opt/repo/public;
	autoindex on;
}
root@repository:/opt/repo# 
```

Recargamos o reiniciamos el servicio **nginx** para que la configuración surta efecto:

```bash
root@repository:/opt/repo# service nginx restart
root@repository:/opt/repo# 
```

## Añadiendo paquetes al repositorio

Añadir un paquete a nuestro repositorio es tan fácil como invocar el comando *reprepro*, con la opción *includedeb* del paquete, en alguna carpeta de nuestra máquina. El resto son opciones que indican donde están las carpetas del repositorio.

**WARNING**: Si se pone un paquete empaquetado por nosotros, es importante que su fichero *control* incluya las directivas *Section* y *Priority*, normalmente solo recomendadas, pero necesarias para **reprepro**.

Por ejemplo, podemos usar el paquete de un [artículo anterior]({filename}/articles/empaquetando-ficheros-punto-deb.md).

```bash
root@repository:/opt/repo# reprepro --distdir ./public/dists --outdir ./public includedeb linuxsysadmin /root/welcome_1.0-1_all.deb 
Exporting indices...
root@repository:/opt/repo# 
```

**WARNING**: Puede que el comando falle si no se ha montado el sistema de ficheros */dev/pts*, especialmente en un entorno tipo **chroot**.

## Usando el repositorio

Cambiamos de máquina; ahora vamos a la máquina que vaya a usar el repositorio y vamos a configurar el repositorio nuevo.

Lo primero es declarar la **source** de nuestro repositorio, declarando la dirección web del repositorio, el nombre del repositorio y el componente.

```bash
root@client:~# cat /etc/apt/sources.list.d/linuxsysadmin.list 
deb http://10.0.0.2/ linuxsysadmin main
root@client:~# 
```

Ahora nos descargamos la clave pública del repositorio y la añadimos al almacén de claves de **apt**.

```bash
root@client:~# wget -qO- http://10.0.0.2/key.gpg | apt-key add -
OK
root@client:~# 
```

Y con esto ya tenemos el repositorio habilitado. A partir de aquí su uso es el mismo que el de cualquier otro repositorio. Hacemos un *apt-get update* para descargar la lista de paquetes del repositorio.

```bash
root@client:~# apt-get update
Des:1 http://10.0.0.2 linuxsysadmin InRelease [1.340 B]
...
Des:2 http://10.0.0.2 linuxsysadmin/main i386 Packages [333 B]
...
Descargados 2.040 B en 6s (330 B/s)                                                                                                                                    
Leyendo lista de paquetes... Hecho
root@client:~# 
```

A partir de aquí, y sabiendo nuestro sistema los paquetes de los que dispone el nuevo repositorio, podemos buscar los paquetes que hay en él.

```bash
root@client:~# apt-cache search welcome | grep ^welcome
welcome2l - Linux ANSI boot logo
welcome - A fancy shell script
root@client:~# apt-cache show welcome
Package: welcome
Version: 1.0-1
Architecture: all
Maintainer: Linux Sysadmin
Priority: optional
Section: main
Filename: pool/main/w/welcome/welcome_1.0-1_all.deb
Size: 786
SHA256: 2e701f7fbc090230fb7abc06597fbe5b4e9e70dcc553e749e69793a745b032f2
SHA1: 41351d1d2135bcee09e1fa3bade984ece9f23caf
MD5sum: 574fab58b3c871184047c40d0e732b35
Description: A fancy shell script
 To demonstrate how to package a .deb file
Description-md5: ed73975a1e7c5f0422fef1f624586821
Depends: bash, coreutils

root@client:~# 
```

Visto que el paquete está disponible, podemos instalarlo, usando *apt-get* o cualquier otro frontal, gráfico o no.

```bash
root@client:~# apt-get install welcome
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias       
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes NUEVOS:
  welcome
0 actualizados, 1 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 786 B de archivos.
Se utilizarán 0 B de espacio de disco adicional después de esta operación.
Des:1 http://10.0.0.2/ linuxsysadmin/main welcome all 1.0-1 [786 B]
Descargados 786 B en 0s (37,4 kB/s)
debconf: se retrasa la configuración de los paquetes, ya que «apt-utils» no está instalado
Seleccionando el paquete welcome previamente no seleccionado.
(Leyendo la base de datos ... 10434 ficheros o directorios instalados actualmente.)
Preparando para desempaquetar .../archives/welcome_1.0-1_all.deb ...
Desempaquetando welcome (1.0-1) ...
Configurando welcome (1.0-1) ...
root@client:~# 
```

Tal como lo esperábamos, el comando *welcome* está instalado y funciona como esperábamos:

```bash
root@client:~# which welcome
/usr/bin/welcome
root@client:~# welcome
Hello world!
root@client:~# 
```

Y con esto tenemos nuestro repositorio funcional.
