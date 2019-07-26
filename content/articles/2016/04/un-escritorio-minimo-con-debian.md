---
title: "Un escritorio mínimo con Debian"
slug: "un-escritorio-minimo-con-debian"
date: 2016-04-25
categories: ['Miscelánea']
tags: ['linux', 'debian', 'jessie', 'escritorio', 'xfce']
---

Harto de distribuciones para escritorio cargados con aplicaciones que no se usan, decidí que esta vez iba a instalar un escritorio de trabajo partiendo de una *Debian netinstall*. El resto va a ser instalar las aplicaciones justas y necesarias para nuestro trabajo diario. En este artículo describo como lo hice.<!--more-->

Este tutorial se asume que ya tenemos la distribución instalada de una forma mínima, sin nada que sea innecesario. Vamos a instalar los paquetes que se necesiten para nuestro escritorio.

Para practicar la instalación y probar variaciones, es recomendable hacerlo en una máquina virtual, por ejemplo, usando **VirtualBox**.

En cuanto a los requisitos, vamos a partir de una distribución *Debian Jessie* normal, con una cantidad de memoria tirando a poca, y con un disco también bastante escaso. El resultado es bastante ligero.

```bash
root@kobayashi-maru:~# cat /etc/debian_version
8.4
root@kobayashi-maru:~# free -m
             total       used       free     shared    buffers     cached
Mem:           500         65        435          4          6         34
-/+ buffers/cache:         23        476
Swap:            0          0          0
root@kobayashi-maru:~# df -h
S.ficheros     Tamaño Usados  Disp Uso% Montado en
/dev/sda1        4,0G   600M  3,2G  16% /
udev              10M      0   10M   0% /dev
tmpfs            101M   4,4M   96M   5% /run
tmpfs            251M      0  251M   0% /dev/shm
tmpfs            5,0M      0  5,0M   0% /run/lock
tmpfs            251M      0  251M   0% /sys/fs/cgroup
root@kobayashi-maru:~#
```

Las buenas prácticas requieren separar algunas de las carpetas en particiones distintas, de forma que el disco raíz no se llene por el uso diario de los usuarios. Especialmente se recomienda asignar una partición o disco para la carpeta */home/*.

## El sistema de ventanas

Como primer paso, necesitamos el servidor de ventanas, que se encarga de mediar entre los *drivers* y las aplicaciones. En la distribución utilizada, se utiliza **xorg** para esta función.

```bash
root@kobayashi-maru:~# apt-get install xorg
...
root@kobayashi-maru:~#
```

Esto nos va a instalar el servidor, y gracias al sistema de dependencias de *Debian*, todos los drivers de entrada y de vídeo; esto añade muchos paquetes que seguramente no usaremos jamás, que necesitan irse actualizando y ocupan espacio en disco. En caso de querer reducir la cantidad de drivers instalados, y sabiendo los que necesitamos, podemos instalar los necesarios solamente.

```bash
root@kobayashi-maru:~# apt-get install xserver-xorg xserver-xorg-input-kbd xserver-xorg-input-mouse xserver-xorg-video-vesa
...
root@kobayashi-maru:~#
```

En este caso, yo opté por este sistema, instalando el *driver* de vídeo *vesa*, que es el que funciona con **VirtualBox** (este *driver* funciona siempre). En el caso de mi ordenador, puse el *driver* de vídeo *intel* (que es la tarjeta gráfica que tengo) y añadí el *driver* de entrada *synaptics* (que gestiona el *touchpad*).

## El entorno de escritorio

En este apartado tenemos muchas posibilidades; el ecosistema de entornos de escritorio es grande, pudiendo elegir entre *GNOME*, *KDE*, *XFCE*, *LXDE* y otros tantos.

Un entorno de escritorio que me gusta por su simplicidad es *LXDE*, que se puede instalar con el paquete **lxde**.

```bash
root@kobayashi-maru:~# apt-get install lxde
...
root@kobayashi-maru:~#
```

En caso de no necesitar todos los paquetes, es posible instalar un conjunto menor de paquetes. Una selección bastante completa podría ser la siguiente:

```bash
root@kobayashi-maru:~# apt-get install lxde-core lxappearance lxterminal lxtask
...
root@kobayashi-maru:~#
```

Sin embargo, este entorno de escritorio está muy limitado en cuando a herramientas de configuración, y yo preferí instalar *XFCE*, que conseguí con los paquetes **xfce4** y **xfce4-goodies** (opcional; incluye algunos *plugins* y aplicaciones extras).

```bash
root@kobayashi-maru:~# apt-get install xfce4 xfce4-goodies
...
root@kobayashi-maru:~#
```

## Cargar el modo gráfico

El primer método consiste en trabajar en modo terminal, levantando manualmente el entorno gráfico invocando el comando **startx**, que se encuentra en el paquete **xinit**.

```bash
root@kobayashi-maru:~# apt-get install xinit
...
root@kobayashi-maru:~#
```

Esto no es cómodo para el usuario corriente; lo normal es tener una pantalla de *login* para entrar en la sesión de escritorio. Nuevamente hay muchas alternativas, pero en nuestro caso hemos optado por poner el paquete **lightdm**.

```bash
root@kobayashi-maru:~# apt-get install lightdm
...
root@kobayashi-maru:~#
```

## Otras utilidades

Dependiendo del uso que vayamos a hacer, es interesante que nuestro ordenador pueda reproducir sonidos y tenga un gestor de redes, tanto cableadas como *wifi*.

El primero consiste en usar *ALSA*, y detectar la configuración de nuestro sonido, guardando dicha configuración para futuros reinicios de la máquina.

```bash
root@kobayashi-maru:~# apt-get install alsa-utils
...
root@kobayashi-maru:~# alsactl init
Found hardware: "ICH" "SigmaTel STAC9700,83,84" "AC97a:83847600" "0x8086" "0x0000"
Hardware is initialized using a generic method
root@kobayashi-maru:~# alsactl store
root@kobayashi-maru:~#
```

Para la parte del gestor de redes, hay nuevamente debate. Uno que me gusta y que cumple bien con su función es **wicd**.

```bash
root@kobayashi-maru:~# apt-get install wicd
...
root@kobayashi-maru:~#
```

## Las aplicaciones

Las aplicaciones a instalar son un tema muy personal; cada usuario va a necesitar unos tipos de aplicaciones u otras. Incluso así, de las aplicaciones de un tipo dado, pueden haber diversas opciones.

Estas aplicaciones se pueden ir instalando a *posteriori*, tal como se vayan necesitando. Sin embargo, podemos poner aquellas que se van a usar seguro, como un navegador web, por ejemplo *Chromium*.

```bash
root@kobayashi-maru:~# apt-get install chromium
...
root@kobayashi-maru:~#
```

Y para los fans de *Firefox*, también hay su alternativa:

```
root@kobayashi-maru:~# apt-get install iceweasel
...
root@kobayashi-maru:~#
```

## Y finalmente, la magia

Podemos limpiar los paquetes descargados e instalados, mediante un *clean* simple de **apt-get**. Esto liberará algunos *megas*.

```
root@kobayashi-maru:~# apt-get clean
root@kobayashi-maru:~#
```

Rebotamos nuestro ordenador, y dejamos que lo instalado tome el control del *boot*.

```
root@kobayashi-maru:~# reboot
...
```

Iremos a parar a la pantalla de *login*, y con un usuario adecuado deberíamos ver nuestro escritorio, tal como se muestra.

![Escritorio XFCE](/images/escritorio-xfce.jpg)

Ahora es tarea del usuario tunear el escritorio a su gusto, con paneles, *plugins* y *wallpapers*.

## Un apunte sobre los recursos

Tras instalar todos los componentes, vemos que los recursos apenas han subido; lo que nos da una idea del tipo de *hardware* que podemos usar.

```bash
gerard@kobayashi-maru:~$ df -h
S.ficheros     Tamaño Usados  Disp Uso% Montado en
/dev/sda1        4,0G   1,4G  2,5G  36% /
udev              10M      0   10M   0% /dev
tmpfs            101M   4,4M   96M   5% /run
tmpfs            251M      0  251M   0% /dev/shm
tmpfs            5,0M   4,0K  5,0M   1% /run/lock
tmpfs            251M      0  251M   0% /sys/fs/cgroup
tmpfs             51M   4,0K   51M   1% /run/user/110
tmpfs             51M   4,0K   51M   1% /run/user/1000
gerard@kobayashi-maru:~$ free -m
             total       used       free     shared    buffers     cached
Mem:           500        238        262          5         15        125
-/+ buffers/cache:         96        404
Swap:            0          0          0
gerard@kobayashi-maru:~$
```

El disco ha aumentado en unos 900 mb y la memoria ha pasado de 23 a 96 mb, sin tener ninguna aplicación abierta.

**CUIDADO**: Algunas aplicaciones necesitan mucho disco y también memoria. Depende de lo que se ponga, podemos pasar de unos requerimientos *hardware* austeros, a una máquina que dejaría de juguete a un supercomputador...

Para el uso que doy de mi *netbook* (navegar, redacción de artículos, programación de *scripts* y alguna sesión de *SSH*), los 2gb de memoria me sobran; con 128 mb tendría suficiente.
