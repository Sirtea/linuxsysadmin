---
title: "Una vision general de OverlayFS"
slug: "una-vision-general-de-overlayfs"
date: "2021-06-10"
categories: ['Sistemas']
tags: ['debian', 'debootstrap', 'jaula', 'overlayfs', 'squashfs']
---

Ya vimos en otro artículo sobre los sistemas de ficheros tipo *stacked*,
como por ejemplo [AUFS][1]. Estos nos pueden ser útiles en multitud de
ocasiones, y en particular **OverlayFS**, que ya viene en el *kernel* de
muchos de los **Linux** habituales y sirve como la base sobre la que se
construye **Docker**.<!--more-->

La idea es muy simple: tenemos un sistema de ficheros, al que vamos a
llamar *merged* que es el resultado de juntar 2 o más capas de entre las
siguientes:

* Una *upperdir* opcional, que es de lectura y escritura
* Una *lowerdir* (si hay *upperdir*, sino se necesitan dos) o más, que son de solo lectura

La idea es que la carpeta *merged* va contener todos los ficheros y
carpetas de todas las otras capas, usando la de más arriba en caso de
duda. Las escrituras siempre van a la *upperdir*, que sirve como capa
de cambios respecto a las otras *lowerdir*, evitando así modificarlas.

**NOTA**: En caso de tener una capa *upperdir* también es necesario
tener una carpeta *workdir* para uso interno del sistema operativo,
sobre la que no tenemos control, pero que debe estar en el mismo sistema
de ficheros que la *upperdir*.

Por ejemplo podríamos montar una *merged* de 3 formas:

* `mount -t overlay overlay -o lowerdir=lower1:lower2 merged`  
  Mezcla de dos *lowerdir* sin *upperdir*, que nos deja un *merged*
  de solo lectura, al no tener **upperdir**.
* `mount -t overlay overlay -o lowerdir=lower1,upperdir=upper,workdir=work merged`  
  Sistema tradicional de capa base y capa de cambios, que guarda los
  cambios hechos en *merged* en la carpeta *upperdir*.
* `mount -t overlay overlay -o lowerdir=lower1:lower2,upperdir=upper,workdir=work merged`  
  Juntando ambos conceptos, podemos hacer una capa de cambios, juntando
  dos capas de solo lectura. Esto nos permite "trocear" la base, sobre
  la que añadimos una capa de cambios.

**TRUCO**: En todo caso, veremos todos los ficheros y carpetas presentes
en todas las capas, con el entendido que se van a guardar los cambios
en *upperdir*, y que en caso de lectura, primero veremos el fichero
de *upperdir* y en caso de no estar, veríamos los *lowerdir* en el
orden especificado (en el tercer ejemplo, el orden sería `upper/`,
`lower1/` y finalmente `lower2/` ).

## Una pequeña demostración

Supongamos que tenemos dos capas de solo lectura, que son `lower1/`
y `lower2/`. Queremos ver la mezcla de ambas carpetas en una sola,
y queremos poder modificarlas sin que eso repercuta en las capas
de solo lectura. Esto nos obliga a poner un *upperdir* y un *workdir*.

```bash
gerard@debian:~/projects/overlay$ tree
.
├── lower1
│   ├── a
│   └── b
├── lower2
│   ├── a
│   └── c
├── merged
├── upper
└── work

5 directories, 4 files
gerard@debian:~/projects/overlay$
```

Para la demostración nos limitaremos a poner como contenido de los
ficheros una la capa de la que proceden, y así podremos salir de dudas.

```bash
gerard@debian:~/projects/overlay$ grep . lower*/*
lower1/a:lower1
lower1/b:lower1
lower2/a:lower2
lower2/c:lower2
gerard@debian:~/projects/overlay$
```

Montamos el sistema de ficheros *overlayfs* con el comando arriba mencionado:

```bash
gerard@debian:~/projects/overlay$ sudo mount -t overlay overlay -o lowerdir=lower1:lower2,upperdir=upper,workdir=work merged
gerard@debian:~/projects/overlay$
```

Podemos comprobar que la carpeta `merged/` contiene los ficheros de los dos
*lowerdir* y que el contenido es el esperado. Cabe indicar que, en el caso
del fichero `a`, veremos primero el de `lower1/` por ser el primer *lowerdir*
de la lista y no haber un *upperdir* más prioritario.

```bash
gerard@debian:~/projects/overlay$ tree merged/
merged/
├── a
├── b
└── c

0 directories, 3 files
gerard@debian:~/projects/overlay$
```

```bash
gerard@debian:~/projects/overlay$ grep . merged/*
merged/a:lower1
merged/b:lower1
merged/c:lower2
gerard@debian:~/projects/overlay$
```

Vamos a crear un nuevo fichero y vamos a reescribir otro, trabajando en la
vista, que es `merged/` y es nuestra carpeta de trabajo:

```bash
gerard@debian:~/projects/overlay$ echo merged > merged/a
gerard@debian:~/projects/overlay$ echo merged > merged/d
gerard@debian:~/projects/overlay$
```

Podemos observar que el contenido de la vista `merged/` es el esperado,
acumulando los cambios en `upper/` (que es la capa de cambios). Los
ficheros de `lower1/` y de `lower2` no han sufrido cambio alguno, y
vemos que leer el fichero `a` nos muestra el contenido del *upperdir*,
que tiene preferencia respecto a los *lowerdir*.

```bash
gerard@debian:~/projects/overlay$ tree
.
├── lower1
│   ├── a
│   └── b
├── lower2
│   ├── a
│   └── c
├── merged
│   ├── a
│   ├── b
│   ├── c
│   └── d
├── upper
│   ├── a
│   └── d
└── work
    └── work [error opening dir]

6 directories, 10 files
gerard@debian:~/projects/overlay$
```

```bash
gerard@debian:~/projects/overlay$ grep . merged/*
merged/a:merged
merged/b:lower1
merged/c:lower2
merged/d:merged
gerard@debian:~/projects/overlay$
```

```bash
gerard@debian:~/projects/overlay$ grep . lower*/* upper/*
lower1/a:lower1
lower1/b:lower1
lower2/a:lower2
lower2/c:lower2
upper/a:merged
upper/d:merged
gerard@debian:~/projects/overlay$
```

Esto hace los backups más simples, nos permite ahorrar espacio en disco
(reutilizando las capas base) y, en caso de intrusión, sabemos que solo
nos han podido cambiar el *upperdir*; reconstruir la jaula es tan simple
como vaciar la capa de cambios en `upper/` y remontar el `merged/`...

**TRUCO**: En caso de querer montar el sistema de ficheros *merged* en
tiempo de *boot*, basta con utilizar el fichero `/etc/fstab`, con una
línea así:

```bash
overlay /merged overlay noauto,x-systemd.automount,lowerdir=/lower1:/lower2,upperdir=/upper,workdir=/work 0 0
```

**TRUCO**: Las carpetas *lowerdir* son de solo lectura; nada nos impide
utilizar carpetas montadas como solo lectura, por ejemplo que sean
el montaje de un fichero **SquashFS**.

## Un caso real con varias jaulas

Tengo un amigo que está paranoico con la seguridad; no hay aplicación
que no quiera ver enjaulada, y no le gusta nada **Docker**. Esto le
obliga a utilizar **chroot** y **debootstrap** para todo, pero eso tiene
un coste en espacio de disco utilizado.

Veamos como podemos hacer un sistema con 3 jaulas **chroot** con base
**Debian**, dos de ellas ejecutando **nginx** y la otra si nada especial.
Empezaremos instalando la herramienta que vamos a usar:

```bash
gerard@alcatraz:~$ sudo apt install debootstrap
...
gerard@alcatraz:~$
```

Por ser ordenados, vamos a colocar todas las carpetas en `/srv/overlay/`,
con una carpeta `lowerdirs/` para contener los *lowerdirs*, una carpeta
`workdirs/` para contener los *workdirs*, una carpeta `upperdirs/` para
contener los *upperdirs* y una carpeta `/srv/jails/` para los *merged*
(así será transparente para los usuarios).

```bash
gerard@alcatraz:/srv$ tree
.
├── jails
└── overlay
    ├── lowerdirs
    ├── upperdirs
    └── workdirs

5 directories, 0 files
gerard@alcatraz:/srv$
```

### La capa base Debian

Se trata de un sistema de fichero **Debian** estándar que vamos a crear
con **debootstrap**, y que vamos a reutilizar para todo el resto. Le
vamos a borrar algunos ficheros innecesarios para ahorrar espacio, pero
esto es opcional.

```bash
gerard@alcatraz:/srv/overlay/lowerdirs$ sudo debootstrap --variant=minbase buster debian
...
gerard@alcatraz:/srv/overlay/lowerdirs$ sudo chroot debian/ apt clean
gerard@alcatraz:/srv/overlay/lowerdirs$ sudo chroot debian/ rm -rf /var/lib/apt/lists/*
gerard@alcatraz:/srv/overlay/lowerdirs$
```

Y ya tenemos nuestro primer *lowerdir* base en `/srv/overlay/lowerdirs/debian/`.

```bash
gerard@alcatraz:/srv/overlay$ tree -L 2
.
├── lowerdirs
│   └── debian
├── upperdirs
└── workdirs

4 directories, 0 files
gerard@alcatraz:/srv/overlay$
```

### La capa de añadido con Nginx

Vamos a crear una jaula con **OverlayFS** y vamos a instalar **nginx**.
Esto hará que los añadidos acaben en el *upperdir* de la nueva jaula, que
vamos a convertir en una nueva capa *lowerdir* para otras jaulas.

Nos aseguramos que tenemos el *upperdir* necesario, junto con el *workdir*
y la carpeta contenedora de nuestra nueva jaula temporal:

```bash
gerard@alcatraz:/srv/overlay$ sudo mkdir upperdirs/temporal
gerard@alcatraz:/srv/overlay$ sudo mkdir workdirs/temporal
gerard@alcatraz:/srv/overlay$ tree -L 2
.
├── lowerdirs
│   └── debian
├── upperdirs
│   └── temporal
└── workdirs
    └── temporal

6 directories, 0 files
gerard@alcatraz:/srv/overlay$
```

Ya podemos crear la jaula como la vista de la capa **Debian** base y
la carpeta *upperdir* nueva como capa de cambio, en donde vamos a
recoger el añadido de **nginx**.

```bash
gerard@alcatraz:/srv/jails$ sudo mkdir temporal
gerard@alcatraz:/srv/jails$ sudo mount -t overlay overlay -o lowerdir=/srv/overlay/lowerdirs/debian,upperdir=/srv/overlay/upperdirs/temporal,workdir=/srv/overlay/workdirs/temporal temporal/
gerard@alcatraz:/srv/jails$
```

```bash
gerard@alcatraz:/srv/jails$ sudo chroot temporal/ apt update
...
gerard@alcatraz:/srv/jails$ sudo chroot temporal/ apt install nginx-light
...
gerard@alcatraz:/srv/jails$ sudo chroot temporal/ apt clean
gerard@alcatraz:/srv/jails$ sudo chroot temporal/ rm -rf /var/lib/apt/lists/*
gerard@alcatraz:/srv/jails$
```

En este punto, ya no nos interesa la jaula temporal y solo nos interesa
el añadido, que está en el *upperdir*. Vamos a rescatar el *upperdir*
como un nuevo *lowerdir* para su uso futuro, y vamos a limpiar todo el
resto, que ya no nos sirve.

```bash
gerard@alcatraz:/srv/overlay$ sudo umount /srv/jails/temporal/
gerard@alcatraz:/srv/overlay$ sudo mv upperdirs/temporal/ lowerdirs/nginx
gerard@alcatraz:/srv/overlay$ sudo rm -Rf workdirs/temporal/ /srv/jails/temporal/
gerard@alcatraz:/srv/overlay$
```

En este punto ya tenemos nuestra capa como un *lowerdir* más, listo
para su uso futuro. En caso de más añadidos, podemos repetir este
paso tanto como sea necesario.

```bash
gerard@alcatraz:/srv/overlay$ tree -L 2
.
├── lowerdirs
│   ├── debian
│   └── nginx
├── upperdirs
└── workdirs

5 directories, 0 files
gerard@alcatraz:/srv/overlay$
```

### Las jaulas individuales

Ya queremos entregar las 3 jaulas al usuario, para que las pueda modificar a
placer. Como esperamos que las modifique, las 3 jaulas van a necesitar su
propio *upperdir* y, por lo tanto, un *workdir*.

```bash
gerard@alcatraz:/srv/overlay$ sudo mkdir {upperdirs,workdirs}/{nginx1,nginx2,debian1}
gerard@alcatraz:/srv/overlay$ tree -L 2
.
├── lowerdirs
│   ├── debian
│   └── nginx
├── upperdirs
│   ├── debian1
│   ├── nginx1
│   └── nginx2
└── workdirs
    ├── debian1
    ├── nginx1
    └── nginx2

11 directories, 0 files
gerard@alcatraz:/srv/overlay$
```

Les creamos la carpeta contenedora de la jaula, y les montamos la jaula
juntando los *lowerdirs* necesarios, con los *upperdirs* y los *workdirs*.
Hay que prestar atención a los *lowerdirs* montados: `debian` para todos,
pero solo el añadido `nginx` al que lo necesite.

```bash
gerard@alcatraz:/srv/jails$ sudo mkdir nginx1 nginx2 debian1
gerard@alcatraz:/srv/jails$ sudo mount -t overlay overlay -o lowerdir=/srv/overlay/lowerdirs/debian:/srv/overlay/lowerdirs/nginx,upperdir=/srv/overlay/upperdirs/nginx1,workdir=/srv/overlay/workdirs/nginx1 /srv/jails/nginx1/
gerard@alcatraz:/srv/jails$ sudo mount -t overlay overlay -o lowerdir=/srv/overlay/lowerdirs/debian:/srv/overlay/lowerdirs/nginx,upperdir=/srv/overlay/upperdirs/nginx2,workdir=/srv/overlay/workdirs/nginx2 /srv/jails/nginx2/
gerard@alcatraz:/srv/jails$ sudo mount -t overlay overlay -o lowerdir=/srv/overlay/lowerdirs/debian,upperdir=/srv/overlay/upperdirs/debian1,workdir=/srv/overlay/workdirs/debian1 /srv/jails/debian1/
gerard@alcatraz:/srv/jails$
```

Y ya tenemos las jaulas listas para trabajar; es interesante ver que las
jaulas de **nginx** utilizan ambas capas, pero que la jaula **debian**
parte solamente de la primera (y por lo tanto, no tiene **nginx**).

```bash
gerard@alcatraz:/srv/jails$ sudo chroot nginx1/ which nginx
/usr/sbin/nginx
gerard@alcatraz:/srv/jails$ sudo chroot nginx2/ which nginx
/usr/sbin/nginx
gerard@alcatraz:/srv/jails$ sudo chroot debian1/ which nginx
gerard@alcatraz:/srv/jails$
```

Tras la modificación de la jaula `nginx1`, vemos que se comporta según
lo esperado, sin modificar la jaula `nginx2`:

```bash
gerard@alcatraz:/srv/jails$ sudo chroot nginx1/ ls /var/www/html/
index.html
gerard@alcatraz:/srv/jails$ sudo chroot nginx2/ ls /var/www/html/
index.nginx-debian.html
gerard@alcatraz:/srv/jails$
```

Estas modificaciones se guardan en el *upperdir* de `nginx1`, que es el
punto en el que deberíamos hacer copias de seguridad o investigar cambios
sospechosos del sistema de ficheros.

```bash
gerard@alcatraz:/srv/overlay$ tree upperdirs/
upperdirs/
├── debian1
├── nginx1
│   ├── etc
│   │   └── nginx
│   │       └── sites-enabled
│   │           ├── default
│   │           └── web
│   └── var
│       └── www
│           └── html
│               ├── index.html
│               └── index.nginx-debian.html
└── nginx2

9 directories, 4 files
gerard@alcatraz:/srv/overlay$
```

**NOTA**: En este caso se borraron los ficheros originales `default` y
`index.nginx-debian.html`; esto queda marcado como un cambio, creando
un [dispositivo especial][2] con *major* y *minor* a cero, reservado
por el *kernel* de **Linux**.

```bash
gerard@alcatraz:/srv/overlay$ tree upperdirs/nginx1/ -p
upperdirs/nginx1/
├── [drwxr-xr-x]  etc
│   └── [drwxr-xr-x]  nginx
│       └── [drwxr-xr-x]  sites-enabled
│           ├── [c---------]  default
│           └── [-rw-r--r--]  web
└── [drwxr-xr-x]  var
    └── [drwxr-xr-x]  www
        └── [drwxr-xr-x]  html
            ├── [-rw-r--r--]  index.html
            └── [c---------]  index.nginx-debian.html

6 directories, 4 files
gerard@alcatraz:/srv/overlay$
```

### Sobre el espacio en disco

El espacio en disco ocupado parece que es 4 veces el de la jaula; esto es
porque el comando `du` cuenta también los sistemas de ficheros montados
dentro del que pidamos:

```bash
gerard@alcatraz:/srv$ sudo du -sh * | sort -h
129M    overlay
373M    jails
gerard@alcatraz:/srv$
```

Podemos utilizar `df` o poner el *flag* `-x` para que se quede en nuestro
dispositivo físico:

```bash
gerard@alcatraz:/srv$ sudo du -shx * | sort -h
4,0K    jails
129M    overlay
gerard@alcatraz:/srv$
```

También podemos ver qué tamaño consume cada capa mirando simplemente
sus partes individuales:

```bash
gerard@alcatraz:/srv$ sudo du -sh overlay/{upper,lower}dirs/* | sort -h
4,0K    overlay/upperdirs/debian1
4,0K    overlay/upperdirs/nginx2
52K     overlay/upperdirs/nginx1
7,9M    overlay/lowerdirs/nginx
121M    overlay/lowerdirs/debian
gerard@alcatraz:/srv$
```

Así pues, las jaulas individuales ocuparían 120-130mb cada una, pero con
**overlayfs** se quedan ocupando solamente unos 130mb entre todas, ya que
comparten todas las capas intermedias, de solo lectura; solo hay que añadir
las capas de cambios *upperdir*, en las que no esperamos muchas cambios.

Como punto extra, y si el espacio es un problema, podemos comprimir los
*lowerdir* con **squashfs** y montarlos desde el fichero comprimido, lo
que reduciría el espacio usado a unos impresionantes 47mb.

```bash
gerard@alcatraz:/srv$ sudo du -shx *
4,0K    jails
47M     overlay
gerard@alcatraz:/srv$
```

```bash
gerard@alcatraz:~$ df -h | grep overlay
/dev/loop0       2,9M   2,9M     0 100% /srv/overlay/lowerdirs/nginx
/dev/loop1        44M    44M     0 100% /srv/overlay/lowerdirs/debian
overlay          7,9G   950M  6,9G  12% /srv/jails/debian1
overlay          7,9G   950M  6,9G  12% /srv/jails/nginx1
overlay          7,9G   950M  6,9G  12% /srv/jails/nginx2
gerard@alcatraz:~$
```

Nada mal, considerando que las jaulas ocupaban 373mb, con **overlayfs**
pasamos a ocupar 129mb, y con **squashfs** caemos a 47mb. Esto es un
13% del tamaño real...

El *backup* consiste en guardar los *lowerdir* una sola vez (son de solo
lectura), en formato **squashfs** o comprimidos; los *upperdirs* necesitan
copias de seguridad periódicas, pero espero que no cambien demasiado.

**NOTA**: Dejo el fichero `/etc/fstab` para futuras referencias:

```bash
gerard@alcatraz:~$ cat /etc/fstab
...
/srv/overlay/lowerdirs/debian.sqsh /srv/overlay/lowerdirs/debian squashfs loop 0 0
/srv/overlay/lowerdirs/nginx.sqsh /srv/overlay/lowerdirs/nginx squashfs loop 0 0
overlay /srv/jails/nginx1 overlay noauto,x-systemd.automount,lowerdir=/srv/overlay/lowerdirs/debian:/srv/overlay/lowerdirs/nginx,upperdir=/srv/overlay/upperdirs/nginx1,workdir=/srv/overlay/workdirs/nginx1 0 0
overlay /srv/jails/nginx2 overlay noauto,x-systemd.automount,lowerdir=/srv/overlay/lowerdirs/debian:/srv/overlay/lowerdirs/nginx,upperdir=/srv/overlay/upperdirs/nginx2,workdir=/srv/overlay/workdirs/nginx2 0 0
overlay /srv/jails/debian1 overlay noauto,x-systemd.automount,lowerdir=/srv/overlay/lowerdirs/debian,upperdir=/srv/overlay/upperdirs/debian1,workdir=/srv/overlay/workdirs/debian1 0 0
gerard@alcatraz:~$
```

[1]: {{< relref "/articles/2016/03/sistemas-de-ficheros-multicapa-con-aufs.md" >}}
[2]: https://www.kernel.org/doc/Documentation/admin-guide/devices.txt
