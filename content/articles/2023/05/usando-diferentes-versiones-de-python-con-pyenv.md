---
title: "Usando diferentes versiones de Python con pyenv"
slug: "usando-diferentes-versiones-de-python-con-pyenv"
date: "2023-05-25"
categories: ['Sistemas']
tags: ['linux', 'debian', 'python', 'pyenv']
---

Tal como el mundo de las aplicaciones va adoptando arquitecturas orientadas a microservicios
nos encontramos con la necesidad de alojar más aplicaciones pequeñas, y normalmente con
requisitos distintos en cuanto al lenguaje de programación, su versión o sus librerías;
esto nos lleva a la adopción de contenedores, pero no siempre es posible.<!--more-->

Ya sea en una máquina de trabajo de un desarrollador o en un servidor que no disponga
de capacidad de despliegue de contenedores, no nos queda otra que hacer convivir el
conjunto de aplicaciones que estamos desarrollando o sirviendo.

**Python** tiene una forma muy interesante de gestionar los conflictos de librerías que
se llama **virtualenv**; sin embargo, las versiones de **Python** son otro tema. Como
alguien me dijo una vez, es una mala idea toquetear el **python** del sistema operativo;
es muy fácil romper las herramientas más básicas del mismo.

Así pues, la recomendación es separar las diferentes versiones de **python**, y eso solo
se puede hacer de unas pocas formas: o bien utilizamos jaulas (o contenedores), o bien
tenemos instalaciones independientes para poder usar. Es en esta última forma en la que
**pyenv** nos ayuda; se trata de manejar varias versiones de **python** de forma fácil,
e instalarlas o eliminarlas de forma (más o menos) fácil.

## Instalación de pyenv

La instalación de **pyenv** es muy simple; basta con utilizar un *script* alojado en
su web. Para ello vamos a necesitar **curl** o **wget**. El *script* en sí mismo está
escrito en **bash** y requiere de **git**. Empezaremos instalándolos todos:

```bash
gerard@asclepius:~$ sudo apt install curl git
...
gerard@asclepius:~$
```

La instalación a partir de aquí es ejecutar el *script* que [se nos indica][1]:

```bash
gerard@asclepius:~$ curl https://pyenv.run | bash
...
WARNING: seems you still have not added 'pyenv' to the load path.

# Load pyenv automatically by appending
# the following to
~/.bash_profile if it exists, otherwise ~/.profile (for login shells)
and ~/.bashrc (for interactive shells) :

export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Restart your shell for the changes to take effect.

# Load pyenv-virtualenv automatically by adding
# the following to ~/.bashrc:

eval "$(pyenv virtualenv-init -)"

gerard@asclepius:~$
```

Solo nos falta añadir al `.bash_profile` o al `.profile` lo que nos indica:

```bash
gerard@asclepius:~$ tail -3 .profile
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
gerard@asclepius:~$
```

Salimos de la sesión para que, al entrar, nos aplique el nuevo `.profile`.

## Instalando versiones nuevas de python

La instalación no puede ser más fácil: `pyenv install <version>`. Podemos elegir versión de
entre las disponibles, que veremos con el comando `pyenv install --list`.

Lo único que debe decirse es que **pyenv** instala la versión **compilándola** *in situ*.
Esto nos obliga a tener una serie de compiladores, herramientas y cabeceras de librerías.

La [documentación][2] indica los paquetes que tenemos que instalar, pero podemos prescindir
de algunos; en concreto me bastan con el compilador **gcc** y la herramienta **make**. Las
cabeceras de las librerías no son tan importantes y, si faltan, habrá módulos de la librería
estándar no disponibles. Como pretendo trabajar con aplicaciones "servidor", el módulo **tkinter**
que sirve para hacer aplicaciones de escritorio, no me sirve y quito `tk-dev`. El resto se
quedan, ya que no pesan mucho y pueden sernos útiles.

```bash
gerard@asclepius:~$ sudo apt install make gcc libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libncurses-dev libxml2-dev libffi-dev liblzma-dev uuid-dev
...
gerard@asclepius:~$
```

Ahora sí: vamos a "instalar" la versión 3.11 de **python**. Esto solo debería hacerse una
vez (me ha tardado unos 4 minutos en una máquina virtualizada con **VirtualBox**, con un
solo procesador y 512mb de memoria).

```bash
gerard@asclepius:~$ pyenv install 3.11
Downloading Python-3.11.3.tar.gz...
-> https://www.python.org/ftp/python/3.11.3/Python-3.11.3.tgz
Installing Python-3.11.3...
Installed Python-3.11.3 to /home/gerard/.pyenv/versions/3.11.3
gerard@asclepius:~$
```

Encontraremos nuestro nuevo **python** en `~/.pyenv/versions/`. Aunque no es muy relevante,
podemos sacar un *backup* para no tener que volver a compilarla, o copiarla para otra máquina.

**TRUCO**: Esta instalación ocupa 321mb de disco. Podemos reducir el tamaño eliminando la carpeta
`lib/python3.11/test/` (118mb menos), eliminando la librería estática (que no vamos a usar)
`lib/python3.11/config-3.11-x86_64-linux-gnu/libpython3.11.a` (55mb menos), haciendo un **strip**
masivo (35mb menos) y limpiando los ficheros `.pyc` o sus carpetas `__pycache__` contenedoras
(68mb menos, aunque estos se van a ir recreando según haga falta). Ahora ocupa 45mb de disco.

Si decidimos copiar la carpeta `~/.pyenv/versions/` a otro servidor con **pyenv** (y posiblemente
sin compiladores), bastará con asegurar que tenemos todas las librerías *runtime* necesarias
para que nos funcionen todos los módulos. Por ejemplo, el módulo **sqlite3**:

```bash
gerard@jormundgander:~$ python -c "import sqlite3"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/home/gerard/.pyenv/versions/3.11.3/lib/python3.11/sqlite3/__init__.py", line 57, in <module>
    from sqlite3.dbapi2 import *
  File "/home/gerard/.pyenv/versions/3.11.3/lib/python3.11/sqlite3/dbapi2.py", line 27, in <module>
    from _sqlite3 import *
ImportError: libsqlite3.so.0: cannot open shared object file: No such file or directory
gerard@jormundgander:~$
```

Esto pasa porque el módulo **sqlite3** es un fichero `.so`, que depende de otra librería, que
solamente tenemos que instalar de la forma habitual:

```bash
gerard@jormundgander:~$ find .pyenv/versions/ -type f | xargs ldd 2>/dev/null | grep "not found"
        libsqlite3.so.0 => not found
gerard@jormundgander:~$
```

```bash
gerard@jormundgander:~$ sudo apt install libsqlite3-0
...
gerard@jormundgander:~$
```

```bash
gerard@jormundgander:~$ python -c "import sqlite3"
gerard@jormundgander:~$
```

**WARNING**: Tras añadir o retirar ficheros binarios de forma manual en `~/.pyenv/versions/`,
conviene hacer un `pyenv rehash` (o el `pyenv init` implícito del fichero `.profile`, que
hace un *rehash*) para que los detecte el nuevo **pyenv**.

## Utilizando pyenv

Si vamos poniendo instalaciones de **python**, veremos que tenemos disponibles varias de ellas:

```bash
gerard@asclepius:~$ pyenv versions
  3.8.16
  3.9.16
  3.10.11
  3.11.3
gerard@asclepius:~$
```

Cada vez que invocamos el comando `python`, **pyenv** nos va a ejecutar de forma transparente
el **python** que corresponda al contexto en el que estamos. Este contexto puede ser **global**,
**local** o **shell**.

El contexto **shell** indica que el **python** indicado se aplica solamente a la sesión en
curso. Esto se consigue con la variable de entorno `PYENV_VERSION`, que **pyenv** cambiará
según convenga, y que podemos restaurar con `pyenv shell --unset` si es necesario. Se trata del
que tiene preferencia. Entonces, si yo quiero utilizar en un terminal **python 3.11**, haré:

```bash
gerard@asclepius:~$ pyenv shell 3.11
gerard@asclepius:~$
```

```bash
gerard@asclepius:~$ python -V
Python 3.11.3
gerard@asclepius:~$
```

El segundo contexto por prioridad de aplicación es el contexto **local**. El **python** que
así se define, lo hace para la carpeta actual y todas sus subcarpetas, haciendo muy fácil
cambiar de proyecto sin preocuparse por la versión de **python** del mismo.
Esto lo consigue **pyenv** creando en la carpeta indicada un fichero `.python-version`,
que indica la versión utilizada y es una bonita forma de indicar la versión de **python**
necesaria para ejecutar el proyecto, especialmente para guardarlo en un repositorio de código.

```bash
gerard@asclepius:~/project1$ pyenv local 3.8
gerard@asclepius:~/project1$
```

```bash
gerard@asclepius:~/project2$ pyenv local 3.10
gerard@asclepius:~/project2$
```

```bash
gerard@asclepius:~$ (cd project1 && python -V)
Python 3.8.16
gerard@asclepius:~$ (cd project2 && python -V)
Python 3.10.11
gerard@asclepius:~$
```

Finalmente, el contexto **global** indica el **python** por defecto para el usuario actual
del sistema operativo, que se va a utilizar si no hay otra opción más específica. En este caso,
esta versión se guarda en `~/.pyenv/version`.

```bash
gerard@asclepius:~$ pyenv global 3.11
gerard@asclepius:~$
```

En caso de no tener claro qué **python** aplica en un momento dado, podemos consultarlo;
ya de paso nos va a decir por qué toca esa versión concreta:

```bash
gerard@asclepius:~/project1$ pyenv version
3.8.16 (set by /home/gerard/project1/.python-version)
gerard@asclepius:~/project1$
```

Sabiendo qué versión está activa, nuestra mecánica de trabajo es la de siempre, utilizando
las herramientas habituales, como **python**, **pip** y los **virtualenvs**.

[1]: https://github.com/pyenv/pyenv#automatic-installer
[2]: https://github.com/pyenv/pyenv/wiki#suggested-build-environment
