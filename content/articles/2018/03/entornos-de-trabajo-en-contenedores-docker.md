---
title: "Entornos de trabajo en contenedores Docker"
slug: "entornos-de-trabajo-en-contenedores-docker"
date: 2018-03-05
categories: ['Miscelánea']
tags: ['docker', 'herramientas', 'workspace']
---

Cuando usamos herramientas concretas para todos los miembros de un mismo equipo, suele ser problemático instalarlo en sus equipos. Por la ausencia de instalación y su gran reproducibilidad, es cada vez más frecuente distribuir esas herramientas en una imagen de **Docker**, aunque esto no garantiza estar libres de otros problemas.<!--more-->

El tema más problemático suele ser la diferencia entre el usuario del equipo y el del contenedor **Docker**; un fichero guardado con el usuario *john* en el contenedor pasaria a pertenecer, por ejemplo, al usuario *james* en el *host*.

Esto se debe a que el usuario se guarda en el disco como su identificador numérico, que luego se interpreta de acuerdo al fichero */etc/passwd* del sistema operativo que lo lea. Afortunadamente, este es un problema menor que puede ser solventado con un poco de habilidad.

## Un ejemplo práctico: un contenedor para usar Python

Hay pocos motivos para no instalar **python** directamente en el sistema *host*; para su fácil distribución, para utilizar diferentes versiones o simplemente para disponer de ellas en un servidor donde no podríamos instalarlo normalmente por seguridad. Sin embargo es un ejemplo con alto valor didáctico.

Empezaremos con una imagen que solo contenga los binarios que usamos habitualmente; vamos a montar la carpeta de trabajo desde el *host* de **docker**. Los binarios que suelo utilizar son los siguientes:

* python
* virtualenv
* pep8

Así pues, nos limitaremos a utilizar un *Dockerfile* básico con estas tres herramientas, y la distribución que más nos guste:

```bash
gerard@atlantis:~/projects/pyenv$ cat Dockerfile
FROM alpine:3.6
RUN apk add --no-cache py-virtualenv py-pep8
gerard@atlantis:~/projects/pyenv$
```

**NOTA**: No se indica **python** ya que es una dependencia de los otros paquetes.

### El problema

Vamos a trabajar un poco con las nuevas herramientas, aunque solo sea para crear un proyecto vacío:

```bash
gerard@atlantis:~/projects/pyenv$ docker run -ti --rm --volume /home/gerard/projects/pyenv/workspace:/workspace pyenv
/ # adduser -u 1200 gerard
Changing password for gerard
New password:
Bad password: similar to username
Retype password:
passwd: password for gerard changed by root
/ # cd workspace/
/workspace # echo '' > app.py
/workspace # su - gerard
4bf4f4abe9e2:~$ cd /workspace/
4bf4f4abe9e2:/workspace$ virtualenv env
Traceback (most recent call last):
  File "/usr/bin/virtualenv", line 11, in <module>
    load_entry_point('virtualenv==15.1.0', 'console_scripts', 'virtualenv')()
  File "/usr/lib/python2.7/site-packages/virtualenv.py", line 713, in main
    symlink=options.symlink)
  File "/usr/lib/python2.7/site-packages/virtualenv.py", line 925, in create_environment
    site_packages=site_packages, clear=clear, symlink=symlink))
  File "/usr/lib/python2.7/site-packages/virtualenv.py", line 1110, in install_python
    mkdir(lib_dir)
  File "/usr/lib/python2.7/site-packages/virtualenv.py", line 323, in mkdir
    os.makedirs(path)
  File "/usr/lib/python2.7/os.py", line 150, in makedirs
    makedirs(head, mode)
  File "/usr/lib/python2.7/os.py", line 150, in makedirs
    makedirs(head, mode)
  File "/usr/lib/python2.7/os.py", line 157, in makedirs
    mkdir(name, mode)
OSError: [Errno 13] Permission denied: '/workspace/env'
4bf4f4abe9e2:/workspace$ exit
/workspace # exit
gerard@atlantis:~/projects/pyenv$ tree -ug
.
├── [gerard   gerard  ]  workspace
│   └── [root     root    ]  app.py
└── [gerard   gerard  ]  Dockerfile

1 directory, 2 files
gerard@atlantis:~/projects/pyenv$
```

Si trabajamos como *root*, el fichero del *host* queda con el propietario incorrecto, y si usamos un usuario con el mismo nombre, no tenemos garantias de que casen, siendo el caso peor el de no poder escribir en el entorno de trabajo.

En mi caso, el usuario *gerard* en el *host* tiene identificador 1000, y he creado el usuario *gerard* del contenedor con identificador 1200 adrede para que se evidencie el problema.

### La solución

**Docker** nos ofrece una solución muy interesante: podemos ejecutar un contenedor especificando el usuario, sea en modo texto o en modo numérico. Como en mi caso el usuario *gerard* tiene identificador 1000 y el grupo *gerard* también, basta con indicar el *flag* `-u 1000:1000`.

```bash
gerard@atlantis:~/projects/pyenv/workspace$ docker run -ti --rm --volume /home/gerard/projects/pyenv/workspace:/workspace -u 1000:1000 pyenv
/ $ cd workspace/
/workspace $ echo aaa > run.py
/workspace $ virtualenv env
New python executable in /workspace/env/bin/python2
Also creating executable in /workspace/env/bin/python
Installing setuptools, pip, wheel...done.
/workspace $ ls -lh
total 8
drwxr-xr-x    5 1000     1000        4.0K Nov 14 16:23 env
-rw-r--r--    1 1000     1000           4 Nov 14 16:23 run.py
/workspace $ exit
gerard@atlantis:~/projects/pyenv/workspace$ ls -lh
total 8,0K
drwxr-xr-x 5 gerard gerard 4,0K nov 14 17:23 env
-rw-r--r-- 1 gerard gerard    4 nov 14 17:23 run.py
gerard@atlantis:~/projects/pyenv/workspace$
```

**TRUCO**: Podemos usar el comando **id** para sacar ambos valores numéricos de forma automatizable.

```bash
gerard@atlantis:~/projects/pyenv/workspace$ docker run -ti --rm --volume /home/gerard/projects/pyenv/workspace:/workspace -u $(id -u):$(id -g) pyenv
/ $ id
uid=1000 gid=1000
/ $
```

Y con esto los identificadores cuadran y no tenemos más problemas, aunque el identificador 1000 no se asocia con ningún usuario del contendor y se lista en modo numerico. La relación entre el valor numérico y nombre del usuario está en el fichero */etc/passwd* y el del grupo en */etc/group*; podemos simplemente mapear esos ficheros del *host*.

```bash
gerard@atlantis:~/projects/pyenv/workspace$ docker run -ti --rm -v /home/gerard/projects/pyenv/workspace:/workspace -u $(id -u):$(id -g) -v /etc/passwd:/etc/passwd -v /etc/group:/etc/group pyenv
/ $ ls workspace/ -lh
total 8
drwxr-xr-x    5 gerard   gerard      4.0K Nov 14 16:23 env
-rw-r--r--    1 gerard   gerard         4 Nov 14 16:23 run.py
/ $
```

Solo nos quedaría encapsular esa línea de comandos en un script para su fácil invocación, por ejemplo mapeando la carpeta actual al *workspace* del contenedor, de la siguiente forma:

```bash
gerard@atlantis:~/projects/newproject$ cat /home/gerard/bin/pyenv
#!/bin/bash

docker run -ti --rm \
  --user $(id -u):$(id -g) \
  --volume /etc/passwd:/etc/passwd:ro \
  --volume /etc/group:/etc/group:ro \
  --read-only \
  --volume $(pwd):/workspace \
  --workdir /workspace \
  pyenv
gerard@atlantis:~/projects/newproject$
```
