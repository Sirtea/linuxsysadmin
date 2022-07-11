---
title: "Haciendo backups de repositorios GIT"
slug: "haciendo-backups-de-repositorios-git"
date: "2022-07-11"
categories: ['Sistemas']
tags: ['git', 'backup']
---

Lo más preciado de un desarrollo siempre es el código: Si se trata de código hecho por desarrolladores,
hay muchas horas invertidas; si se trata de configuraciones como código, supone la forma de reconstruir
un sistema desde un punto catastrófico. Por ello es necesario tenerlo a buen recaudo.<!--more-->

Pero no siempre es fácil hacer un *backup* de los repositorios, especialmente cuando se trata de
repositorios remotos en lugares "cloud" tipo **GitHub** o **Bitbucket**. Por suerte, **git** nos permite
*clonar* sus repositorios, aunque sean remotos y luego hacer un *push* a un nuevo repositorio limpio.

## Haciendo el backup de un remoto

El truco está en hacer un *clon*, pero en modo servidor; no nos interesa el *working directory*.
Para facilitar este clonado, basta con hacer un `git clone --bare <remote>` o un `git clone --mirror <remote>`;
la belleza de esta aproximación es doble:

* Obtenemos una copia local sin inconsistencias y que no va a ser modificada mientras hacemos su archivado.
* El remoto puede ser un repositorio que esté donde quiera; si podemos clonarlo, podemos copiarlo.

### Un ejemplo: clonando un repositorio de **GitHub**

Supongamos que queremos hacer un clon del repositorio del [framework Falcon][1]. Como no tenemos la
clave SSH del desarrollador, obtenemos su URL de clonado en HTTPS, y listo. Sin complicaciones:

```bash
gerard@citadel:~$ git clone --mirror https://github.com/falconry/falcon.git
Clonando en un repositorio vacío 'falcon.git'...
remote: Enumerating objects: 26021, done.
remote: Counting objects: 100% (3069/3069), done.
remote: Compressing objects: 100% (1105/1105), done.
remote: Total 26021 (delta 2111), reused 2786 (delta 1960), pack-reused 22952
Recibiendo objetos: 100% (26021/26021), 9.88 MiB | 10.29 MiB/s, listo.
Resolviendo deltas: 100% (18253/18253), listo.
gerard@citadel:~$
```

Este tiene una estructura muy característica, que ya podría servir como remoto en sí misma:

```bash
gerard@citadel:~$ tree -I "*sample"
.
└── falcon.git
    ├── branches
    ├── config
    ├── description
    ├── HEAD
    ├── hooks
    ├── info
    │   └── exclude
    ├── objects
    │   ├── info
    │   └── pack
    │       ├── pack-f7c5d76a563fb343f96c716c3131d79c24fd4149.idx
    │       └── pack-f7c5d76a563fb343f96c716c3131d79c24fd4149.pack
    ├── packed-refs
    └── refs
        ├── heads
        └── tags

10 directories, 7 files
gerard@citadel:~$
```

Otra opción es hacer un archivo comprimido y guardarlo a buen recaudo.

```bash
gerard@citadel:~$ tar czf falcon.git.tar.gz falcon.git/
gerard@citadel:~$ ls -lh
total 11M
drwxr-xr-x 7 gerard gerard 4,0K jul 11 20:23 falcon.git
-rw-r--r-- 1 gerard gerard  11M jul 11 20:26 falcon.git.tar.gz
gerard@citadel:~$
```

### Otros ejemplos: remotos locales y otros protocolos

Como se trata de remotos normales de **git**, nada nos impide clonar repositorios de nuestros servidores,
y podemos combinarlos con los protocolos que tengamos a mano (por ejemplo HTTP, SSH o ficheros locales).
Para verlo, vamos a clonar un repositorio remoto (por SSH) y uno que esté en el mismo servidor (ficheros locales):

```bash
gerard@citadel:~$ git clone --mirror git@gitserver:myrepo1.git
Clonando en un repositorio vacío 'myrepo1.git'...
Warning: Permanently added 'localhost' (ECDSA) to the list of known hosts.
remote: Enumerando objetos: 3, listo.
remote: Contando objetos: 100% (3/3), listo.
Recibiendo objetos: 100% (3/3), 216 bytes | 216.00 KiB/s, listo.
remote: Total 3 (delta 0), reusado 0 (delta 0), pack-reusado 0
gerard@citadel:~$
```

```bash
gerard@citadel:~$ git clone --mirror /home/git/myrepo2.git/
Clonando en un repositorio vacío 'myrepo2.git'...
hecho.
gerard@citadel:~$
```

Ahora solo quedaría guardar los repositorios, en un archivo comprimido o sin comprimir, a vuestro gusto personal.

```bash
gerard@citadel:~$ ls -1d *.git
falcon.git
myrepo1.git
myrepo2.git
gerard@citadel:~$
```

## Restableciendo un backup

Ahora sucede el desastre; perdemos nuestros repositorios y necesitamos tirar de *backups* para reconstruirlos.
Es fácil: creamos un repositorio nuevo y hacemos un `git push --mirror <remoto nuevo>`.

```bash
gerard@citadel:~/falcon.git$ git push --mirror git@gitserver:sacred.git
Warning: Permanently added 'localhost' (ECDSA) to the list of known hosts.
Enumerando objetos: 26021, listo.
Contando objetos: 100% (26021/26021), listo.
Comprimiendo objetos: 100% (7668/7668), listo.
Escribiendo objetos: 100% (26021/26021), 9.87 MiB | 13.15 MiB/s, listo.
Total 26021 (delta 18253), reusado 26021 (delta 18253), pack-reusado 0
remote: Resolviendo deltas: 100% (18253/18253), listo.
To gitserver:sacred.git
 * [new branch]        0.1.10 -> 0.1.10
 * [new branch]        0.1.9 -> 0.1.9
 * [new branch]        0.2 -> 0.2
...
 * [new tag]           3.1.0 -> 3.1.0
 * [new tag]           3.1.0rc1 -> 3.1.0rc1
 * [new tag]           3.1.0rc2 -> 3.1.0rc2
 * [new tag]           3.1.0rc3 -> 3.1.0rc3
gerard@citadel:~/falcon.git$
```

Y con esto tenemos un repositorio restablecido y listo para usarse. Es importante recalcar que en, este caso,
también lo hemos movido de **GitHub** a un servidor nuestro... Es una forma interesante de cambiarse de *hosting*.

## Un script de backup de ejemplo

Si queremos hacer estos *backups* de forma recurrente y de varios repositorios, puede ser interesante automatizarlo
mediante un *script*. Pongo uno como ejemplo, usando carpetas temporales para dejar el servidor de *backup* limpio:

```bash
gerard@citadel:~$ cat gitbackup.sh
#!/bin/bash

backup () {
    tmpdir=$(mktemp -d)
    cd ${tmpdir}
    git clone --mirror ${1}
    tar czf $2 .
    rm -rf ${tmpdir}
}

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

backup https://github.com/falconry/falcon.git /home/gerard/bak/falcon_${TIMESTAMP}.tar.gz
backup git@gitserver:myrepo1.git /home/gerard/bak/myrepo1_${TIMESTAMP}.tar.gz
backup /home/git/myrepo2.git/ /home/gerard/bak/myrepo2_${TIMESTAMP}.tar.gz
gerard@citadel:~$
```

Tras ejecutarlo, podemos ver como se nos acumulan los *backups* en la carpeta indicada:

```bash
gerard@citadel:~$ tree
.
├── bak
│   ├── falcon_20220711_210314.tar.gz
│   ├── myrepo1_20220711_210314.tar.gz
│   └── myrepo2_20220711_210314.tar.gz
└── gitbackup.sh

1 directory, 4 files
gerard@citadel:~$
```

Y con este *script* metido en una tarea **cron**, tendríamos los *backups* en nuestro servidor de
*backups*. Estaría bien que se copiaran en algún lugar seguro, posiblemente cifrándolos primero...
Pero eso queda como deberes para el lector.

[1]: https://github.com/falconry/falcon
