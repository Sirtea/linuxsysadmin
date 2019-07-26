---
title: "Creando una jaula CentOS"
slug: "creando-una-jaula-centos"
date: 2016-01-25
categories: ['Seguridad']
tags: ['linux', 'centos', 'maipo', 'jaula']
---

Algunas veces nos puede interesar levantar procesos o demonios en entornos controlados, por ejemplo en una jaula, o para crear un contenedor. Otras veces, por comodidad o conocimiento, nos puede interesar cambiar la distribución, por ejemplo, servicios *CentOS* en un servidor *Ubuntu*. Hoy vamos a construir una jaula con *CentOS*.<!--more-->

Vamos a crear una jaula de *CentOS*, partiendo de una distribución basada en **yum**. En este caso, se trata de una distribución *RedHat*.

```bash
[root@mars ~]# cat /etc/redhat-release
Red Hat Enterprise Linux Server release 7.2 (Maipo)
[root@mars ~]#
```

## Creación de la jaula

Empezaremos declarando una variable para indicar donde vamos a crear la jaula.

```bash
[root@mars ~]# export JAIL=/root/jail
[root@mars ~]#
```

Vamos a crear la carpeta de la jaula y la estructura necesaria para albergar los datos del comando **rpm**.

```bash
[root@mars ~]# mkdir -p ${JAIL}/var/lib/rpm
[root@mars ~]#
```

Como la base de datos de **rpm** no existe, la vamos a recrear con el mismo comando:

```bash
[root@mars ~]# rpm --rebuilddb --root=${JAIL}
[root@mars ~]# 
```

Vemos ahora que tenemos una estructura de carpetas que empieza a parecerse a lo que debería.

```bash
[root@mars ~]# tree $JAIL
/root/jail
`-- var
    `-- lib
        `-- rpm
            `-- Packages

3 directories, 1 file
[root@mars ~]#
```

El siguiente paso consiste en localizar el fichero *.rpm* relativo a la *release* de *CentOS* que queramos en nuestra jaula. Apuntamos el navegador al servidor web con el repositorio base en [http://mirror.centos.org/centos/](http://mirror.centos.org/centos/) y buscamos el *link*.

Suponiendo que queramos un *CentOS* versión 7 y con una arquitectura *x64_64*, el *link* podría ser [http://mirror.centos.org/centos/7/os/x86_64/Packages/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm](http://mirror.centos.org/centos/7/os/x86_64/Packages/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm).

```bash
[root@mars ~]# rpm -i --root=${JAIL} --nodeps http://mirror.centos.org/centos/7/os/x86_64/Packages/centos-release-7-2.1511.el7.centos.2.10.x86_64.rpm
warning: Generating 12 missing index(es), please wait...
warning: /root/jail/var/tmp/rpm-tmp.Vy1z44: Header V3 RSA/SHA256 Signature, key ID f4a80eb5: NOKEY
[root@mars ~]#
```

El siguiente paso consiste en instalar **yum** en la jaula, que va a traer todas las dependencias necesarias para completar la jaula.

**WARNING**: El comando **yum** busca las llaves del repositorio en */etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7*, y no en la jaula. Esto se puede solventar con un *link* simbólico:

```bash
[root@mars ~]# ln -s ${JAIL}/etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7 /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
[root@mars ~]#
```

Y ya podemos instalar **yum** y sus dependencias:

```bash
[root@mars ~]# yum --installroot=${JAIL} install -y yum
...
Resolving Dependencies
...
Dependencies Resolved
...
Install  1 Package (+89 Dependent packages)

Total download size: 49 M
Installed size: 245 M
...
Complete!
[root@mars ~]#
```

Si queremos una jaula mas mínima todavía, en vez de *yum* podemos instalar los paquetes necesarios, dejando que las dependencias hagan el resto:

```bash
[root@mars ~]# yum --installroot=${JAIL} install bash httpd
```

Alternativamente, se puede construir una jaula completa instalando el grupo *core* en vez de *yum*:

```bash
[root@mars ~]# yum --installroot=${JAIL} groupinstall core
```

Ya tenemos la jaula; es un buen momento para sacar una copia  de la carpeta.

## Uso de la jaula

Esta copia es transferible a otras máquinas, aunque no sean derivadas de *RedHat*. En este caso, la jaula se puso a funcionar en una máquina con *Debian*.

Declaramos la carpeta donde tenemos la jaula, copiada o descomprimida.

```bash
[root@uranus ~]# export JAIL=/root/jail
[root@uranus ~]#
```

Opcionalmente, podemos copiar el esqueleto de configuración para el usuario **root**.

```bash
root@uranus:~# cp ${JAIL}/etc/skel/.* ${JAIL}/root
cp: se omite el directorio «/root/jail/etc/skel/.»
cp: se omite el directorio «/root/jail/etc/skel/..»
root@uranus:~# 
```

Es hora de entrar en la jaula para definir la contraseña de **root**, configuración de red  y otros detalles.

```bash
root@uranus:~# chroot ${JAIL} /bin/bash -l
[root@uranus /]# 
```

Verificamos que estamos dentro de la jaula, por ejemplo, mirando la versión y distribución instalada.

```bash
[root@uranus /]# cat /etc/redhat-release 
CentOS Linux release 7.2.1511 (Core) 
[root@uranus /]# exit
root@uranus:~# 
```

Podemos instalar cualquier paquete deseado en el interior de la jaula, sea mediante el comando **chroot** o el comando **systemd-nspawn**.

Finalmente, y suponiendo que hay **systemd** instalado en la máquina anfitriona, podemos ejecutar la jaula como un contenedor.

```bash
root@uranus:~# systemd-nspawn -b -D jail/
Spawning container jail on /root/jail.
...
Welcome to CentOS Linux 7 (Core)!
...
CentOS Linux 7 (Core)
Kernel 3.16.0-4-amd64 on an x86_64

jail login: 
```

Y con esto ya tenemos nuestra jaula.
