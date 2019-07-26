---
title: "Semáforos en linux"
slug: "semaforos-en-linux"
date: 2016-11-28
categories: ['Operaciones']
tags: ['linux', 'semáforo', 'concurrencia']
---

Tras revisar un *bug* de cierto proceso en *background* de una aplicación en mi trabajo, vimos que saltaban dos ejecuciones simultáneas y los dos procesos interferían entre ellos. Implementar una exclusión mutua en el proceso era costoso, así que opté por hacerlo con un comando **linux**, que descubrí por internet.<!--more-->

La idea es que podemos asegurar que un comando o *script* pase por un semáforo tal como lo entienden en procesos concurrentes; se marca una zona de exclusión en donde solo un número determinado de procesos pueden estar a la vez. En el caso concreto de un solo proceso, se conoce como un *mutex*.

Así pues, si tenemos un disparador de eventos, como por ejemplo **incron**, podemos evitar una avalancha de procesos disparados en un plazo de tiempo minúsculo, limitando el *stress* causado a la carga del sistema, y evitando también, problemas derivados de que nuestro proceso no acepte concurrencia.

Como ya va siendo habitual, vamos a empezar instalando el paquete que ofrece la utilidad *sem*:

```bash
root@helium:~# apt-get install -y parallel
Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following extra packages will be installed:
  libalgorithm-c3-perl libarchive-extract-perl libcgi-fast-perl libcgi-pm-perl libclass-c3-perl libclass-c3-xs-perl libcpan-meta-perl libdata-optlist-perl libdata-section-perl libfcgi-perl
  libgdbm3 liblog-message-perl liblog-message-simple-perl libmodule-build-perl libmodule-pluggable-perl libmodule-signature-perl libmro-compat-perl libpackage-constants-perl
  libparams-util-perl libpod-latex-perl libpod-readme-perl libregexp-common-perl libsoftware-license-perl libsub-exporter-perl libsub-install-perl libterm-ui-perl libtext-soundex-perl
  libtext-template-perl perl perl-modules rename
Suggested packages:
  perl-doc libterm-readline-gnu-perl libterm-readline-perl-perl make libb-lint-perl libcpanplus-dist-build-perl libcpanplus-perl libfile-checktree-perl libobject-accessor-perl
Recommended packages:
  libarchive-tar-perl
The following NEW packages will be installed:
  libalgorithm-c3-perl libarchive-extract-perl libcgi-fast-perl libcgi-pm-perl libclass-c3-perl libclass-c3-xs-perl libcpan-meta-perl libdata-optlist-perl libdata-section-perl libfcgi-perl
  libgdbm3 liblog-message-perl liblog-message-simple-perl libmodule-build-perl libmodule-pluggable-perl libmodule-signature-perl libmro-compat-perl libpackage-constants-perl
  libparams-util-perl libpod-latex-perl libpod-readme-perl libregexp-common-perl libsoftware-license-perl libsub-exporter-perl libsub-install-perl libterm-ui-perl libtext-soundex-perl
  libtext-template-perl parallel perl perl-modules rename
0 upgraded, 32 newly installed, 0 to remove and 1 not upgraded.
Need to get 6794 kB of archives.
After this operation, 38.4 MB of additional disk space will be used.
...
root@helium:~# 
```

Vamos a partir también de un *script* que tarde un tiempo (para darnos tiempo a probar cosas concurrentemente). Este es el *script* que no debería tener dos ejecuciones concurrentes; recordamos que tiene permisos de ejecución.

```bash
root@helium:~# cat do_stuff.sh 
#!/bin/bash

echo "$(date +'%H:%M:%S') - Started process $1"
sleep 10
echo "$(date +'%H:%M:%S') - Ended process $1"
root@helium:~# 
```

Nada en especial; este *script* recibe un parámetro para identificar la ejecución que estamos mirando, y lo único que hace es perder el tiempo (usad la imaginación), previo registro de la hora de comienzo y de final. La ejecución no depara sorpresas.

```bash
root@helium:~# ./do_stuff.sh 1
14:22:31 - Started process 1
14:22:41 - Ended process 1
root@helium:~# 
```

## Esperando en el semáforo

Como ya hemos mencionado, no nos interesaba que no ejecutaran mas de una vez concurrentemente. Para ello, vamos a disponer de un semáforo que deje pasar un solo proceso.

```bash
root@helium:~# cat protected_do_stuff.sh 
#!/bin/bash

echo "$(date +'%H:%M:%S') - Semaphore for process $1"
sem --fg --id semaphore_do_stuff -j 1 /root/do_stuff.sh $1
root@helium:~# 
```

Esto indica que el comando *sem* se va a bloquear si ya hay otro proceso en marcha para el semáforo indicado con el *flag --id*. El parámetro *-j* indica el número de procesos que pueden pasar a la vez, que en este caso, es uno solo. Cuando no haya nada ejecutando en el semáforo, otro proceso podrá pasar a ejecutar un comando, que en este caso es el *script* anterior, con el mismo parámetro identificativo.

Vemos que si no hay competencia en el mismo semáforo, no nos ralentiza nada. De hecho, los semáforos con distinto identificador son independientes, y no interfieren entre ellos, aunque en este ejemplo solo usemos uno.

```bash
root@helium:~# ./protected_do_stuff.sh 1
14:30:50 - Semaphore for process 1
14:30:50 - Started process 1
14:31:00 - Ended process 1
root@helium:~# 
```

Supongamos ahora que se lanza dos veces el mismo *script*, con dos identificadores diferentes y con unos pocos segundos de diferencia. Los siguientes comandos se han lanzado desde dos sesiones de terminal distintas, ya que el proceso corre en primer plano.

```bash
root@helium:~# ./protected_do_stuff.sh 1
14:35:46 - Semaphore for process 1
14:35:47 - Started process 1
14:35:57 - Ended process 1
root@helium:~# 
```

Esperamos unos segundos y lanzamos el otro:

```bash
root@helium:~# ./protected_do_stuff.sh 2
14:35:50 - Semaphore for process 2
14:35:58 - Started process 2
14:36:08 - Ended process 2
root@helium:~# 
```

El primer proceso ha topado con el semáforo y ha empezado sin problemas en el mismo instante, aunque sin microsegundos no parece tan inmediato. Unos 4 segundos después se ha lanzado el otro comando, que ha tenido que esperar a que el primero acabara, antes de empezar. Esto se ve mejor si mezclamos las trazas de evento:

```
14:35:46 - Semaphore for process 1
14:35:47 - Started process 1
14:35:50 - Semaphore for process 2
14:35:57 - Ended process 1
14:35:58 - Started process 2
14:36:08 - Ended process 2
```

En este caso se ve claramente que el proceso 2 queda parado en el semáforo hasta que el proceso 1 acaba, momento en el que puede empezar. Estoy seguro que esto tendrá muchas aplicaciones futuras.
