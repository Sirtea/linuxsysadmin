---
title: "Utilizando apt-cacher-ng para agilizar la instalación de paquetes"
slug: "utilizando-apt-cacher-ng-para-agilizar-la-instalacion-de-paquetes"
date: 2015-12-21
categories: ['Sistemas']
tags: ['linux', 'debian', 'jessie', 'apt-cacher-ng', 'cache']
---

Hace tiempo veo que tras usar muchas maquinas virtuales *Debian* para el uso diario y para las demostraciones de este blog, el ancho de banda usado para bajar los paquetes se dispara. La mayoría de veces se trata de los mismos paquetes, para instalar las mismas aplicaciones, servicios o actualizaciones.<!--more-->

En el artículo de hoy, voy a enseñar como usar un *proxy* con una *caché* para *apt-get*, llamado **apt-cacher-ng**, de forma que los paquetes son descargados por la primera máquina que los pida, guardados en un servidor local y aprovechados por el resto de máquinas.

## Preparación de las máquinas

Partimos de la máquina habitual, llamada **aptcacher**, siendo esta un contenedor LXC con una *Debian Jessie* básica, aunque esto se podría haber puesto en una *Ubuntu* o cualquier otra distribución que funcione con paquetes *.deb*.

Otras máquinas que vamos a usar son unas máquinas cliente en donde vamos a instalar paquetes cualesquiera para demostrar el funcionamiento, llamadas **client1** y **client2**; estos clientes están en la misma red que la máquina **aptcacher** y tienen conectividad con ella por el puerto *TCP* 3142.

```bash
root@lxc:~# lxc-ls -f
NAME       STATE    IPV4      IPV6  AUTOSTART  
---------------------------------------------
aptcacher  RUNNING  10.0.0.2  -     YES        
client1    RUNNING  10.0.0.3  -     YES        
client2    RUNNING  10.0.0.4  -     YES        
root@lxc:~# 
```

Empezamos instalando el servicio **apt-cacher-ng** en la máquina servidor **aptcacher**:

```bash
root@aptcacher:~# apt-get install apt-cacher-ng
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias... Hecho
...  
Se instalarán los siguientes paquetes NUEVOS:
  apt-cacher-ng ed
0 actualizados, 2 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 500 kB de archivos.
Se utilizarán 1.168 kB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
root@aptcacher:~# 
```

Las configuraciones que vienen por defecto son bastante adecuadas y no tuve que efectuar ningún cambio.

Por otra parte, hay que configurar las máquinas que se quieran beneficiar de este servidor, añadiendo una línea de configuración en su **apt-get**, por ejemplo, poniendo un fichero adicional en */etc/apt/apt.conf.d/*

```bash
root@aptcacher:~# cat /etc/apt/apt.conf.d/02proxy 
Acquire::http { Proxy "http://10.0.0.2:3142"; };
root@aptcacher:~# 

root@client1:~# cat /etc/apt/apt.conf.d/02proxy 
Acquire::http { Proxy "http://10.0.0.2:3142"; };
root@client1:~# 

root@client2:~# cat /etc/apt/apt.conf.d/02proxy 
Acquire::http { Proxy "http://10.0.0.2:3142"; };
root@client2:~# 
```

Y con esto queda montado todo el sistema.

## Funcionamiento de la caché

El funcionamiento es muy simple: basta con instalar en un cliente un paquete, por ejemplo, *python*.

```bash
root@client1:~# apt-get install python
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias... Hecho
...  
Se instalarán los siguientes paquetes NUEVOS:
  file libexpat1 libffi6 libmagic1 libpython-stdlib libpython2.7-minimal
  libpython2.7-stdlib libsqlite3-0 mime-support python python-minimal
  python2.7 python2.7-minimal
0 actualizados, 13 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 5.010 kB de archivos.
Se utilizarán 21,3 MB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
Descargados 5.010 kB en 15s (327 kB/s)                                        
...
root@client1:~# 
```

Como estos paquetes no están en la *caché* del servidor, se han descargado de internet en 15 segundos, de acuerdo a la velocidad de mi conexión de internet y de la velocidad de respuesta de los repositorios elegidos.

Si revisamos la página de estadísticas de **apt-cacher-ng**, disponible en `http://aptcacher:3142/acng-report.html` podemos ver que se han descargado 4,78mb en 13 paquetes; todos son **miss** de la cache, es decir, se han ido a buscar al repositorio oficial.

![Estadísticas web de apt-cacher](/images/apt-cacher-ng-1.jpg)

Ahora vamos a instalar *python* en otro de los clientes:

```bash
root@client2:~# apt-get install python
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias... Hecho
...
Se instalarán los siguientes paquetes NUEVOS:
  file libexpat1 libffi6 libmagic1 libpython-stdlib libpython2.7-minimal
  libpython2.7-stdlib libsqlite3-0 mime-support python python-minimal
  python2.7 python2.7-minimal
0 actualizados, 13 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 5.010 kB de archivos.
Se utilizarán 21,3 MB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
Descargados 5.010 kB en 1s (3.902 kB/s)
root@client2:~# 
```

Hemos elegido el paquete *python* para asegurar que ambas máquinas instalan lo mismo; como se puede ver, se ha descargado la misma cantidad de datos, pero en vez de los 15 segundos anteriores, ahora se ha tardado 1 segundo. Eso es porque los paquetes solicitados estaban en el *proxy*, es decir, en el servidor **aptcacher**.

Podemos ver en la misma página de administración el resultado: ahora hay 13 **hits** adicionales, ya que los paquetes solicitados estaban en local.

![Estadísticas web de apt-cacher](/images/apt-cacher-ng-2.jpg)

De esta forma, si tenemos un elevado número de máquinas del mismo tipo, solo consumiremos el ancho de banda necesario para traerlos de internet **una sola vez**.
