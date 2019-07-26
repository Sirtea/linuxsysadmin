---
title: "Explorando bash: la variable de entorno PROMPT_COMMAND"
slug: "explorando-bash-la-variable-de-entorno-prompt-command"
date: 2017-06-19
categories: ['Operaciones']
tags: ['bash', 'variable', 'PROMPT_COMMAND']
---

Los *gurús* del terminal ya conocemos muchas de las virtudes de **bash**. Sin embargo, es una utilidad muy grande y no es raro que cada vez que busquemos encontremos cosas nuevas. Esta vez, y casi por curiosidad, encontré una variable llamada **PROMPT_COMMAND**, que aunque no es conocida, es muy útil.<!--more-->

El cometido de esta variable de entorno es el de ejecutar un comando de **bash** antes de pintar el símbolo de sistema, según [la documentación](http://www.tldp.org/HOWTO/Bash-Prompt-HOWTO/x264.html).

> Bash provides an environment variable called PROMPT_COMMAND. The contents of this variable are executed as a regular Bash command just before Bash displays a prompt.

No parece muy impresionante a simple vista, pero con algunas ideas adecuadas nos puede quitar mucho trabajo, automatizando aquellas tareas que hacemos cuando entramos en la carpeta, con vistas a trabajar en ella.

**NOTA**: En todos los ejemplos vamos a definir la variable **PROMPT_COMMAND** en el fichero *.bashrc*, para que se haga automáticamente. Para que se active, hace falta hacer un *source* del fichero o abrir de nuevo el terminal; no siempre se menciona en los ejemplos.

## Un comando informativo e incondicional

¿Que hay mas útil que saber la hora del día sin tener que salir del terminal? Podemos poner una función que nos informe de la hora cada vez que pintemos el símbolo del sistema. Luego enchufamos esta función en la variable de entorno, y cada vez que lo pinte, tenemos un bonito reloj.

```bash
gerard@aldebaran:~$ cat .bashrc 
...
prompt_command() {
	echo -n "Current time: "
	date "+%Y-%m-%d %H:%M:%S"
}
export PROMPT_COMMAND=prompt_command
gerard@aldebaran:~$ 
```

Solo hace falta abrir de nuevo el terminal, o hacer un *source* del fichero *.bashrc*. La siguiente vez que pinte un *prompt*, ejecutará antes nuestra función; de hecho lo va a ejecutar tan pronto como acabe el comando *source*.

```bash
gerard@aldebaran:~$ source .bashrc
Current time: 2017-01-13 10:27:11
gerard@aldebaran:~$ 
```

## Un conjunto de instrucciones por carpeta

Supongamos que cada vez que entremos en una carpeta queremos ejecutar un conjunto distinto de comandos. Solo necesitamos que cada carpeta defina su propio *script* para ejecutar. Nuestra función va a darse cuenta de que ese *script* existe, y lo va a ejecutar automáticamente en caso afirmativo.

```bash
gerard@aldebaran:~$ cat .bashrc 
...
prompt_command() {
	if test -x .prompt_command.sh; then ./.prompt_command.sh; fi
}
export PROMPT_COMMAND=prompt_command
gerard@aldebaran:~$ 
```

Des esta forma, cada carpeta que tenga un *script* llamado *.prompt_command.sh* conseguirá que sea ejecutado cada vez que se dibuje el *prompt*. Lo que haga el *script* ya es un tema de preferencia personal.

```bash
gerard@aldebaran:~$ cd projects/
gerard@aldebaran:~$ cat sandbox/.prompt_command.sh
#!/bin/bash

echo "Hello world"
gerard@aldebaran:~/projects$ cd sandbox/
Hello world
gerard@aldebaran:~/projects/sandbox$ 
```

Es importante ver que solo ha saltado el mensaje informativo en la carpeta *sandbox*. De hecho, cada comando que ejecutemos en ella va a disparar el comando. Añadid lógica extra para evitar ejecuciones inútiles.

## Creación y activado automático de *virtualenvs* de python

Este es el *script* que más trabajo me ahorra. Cuando trabajo con **python** suelo hacerlo siempre con *virtualenv*, y con la variable **PYTHONDONTWRITEBYTECODE**, para ahorrarme los molestos ficheros *.pyc*.

La idea es que activar y desactivar el *virtualenv* es tedioso, y me gustaría que se activara automáticamente si la carpeta lo tiene, para desactivarlo al salir de la carpeta, aunque sin desactivarlo en las carpetas subordinadas. Como plus, cuando se active el *virtualenv*, también puedo hacer que se defina la variable de entorno y que se creen los *virtualenvs* de forma automática si no estuvieran creados.

Para ello, me basta con una convención simple:

* Una carpeta con un fichero *requirements.txt* debería tener un *virtualenv* llamado *.venv* en la misma carpeta, con las dependencias instaladas.
* Una carpeta que tenga una carpeta llamada *.venv* asume que es un *virtualenv* y lo activa, si no estuviera ya activado.
* En caso de no haber una carpeta *.venv* pero hubiera un *virtualenv* activo, solo se desactivaría si la nueva carpeta no está dentro de la que contenga el *virtualenv* activado.

**TRUCO**: Un *virtualenv* define una variable de entorno **VIRTUAL_ENV** con el *path* que lo contiene. El resto es una simple comparación de *substrings*.

```bash
gerard@aldebaran:~$ cat .bashrc 
...
prompt_command() {
	if test -e requirements.txt -a ! -e .venv; then
		virtualenv .venv
		./.venv/bin/pip install -r requirements.txt
	fi
	if test -d .venv; then
		if test -z "${VIRTUAL_ENV}"; then
			source .venv/bin/activate
			export PYTHONDONTWRITEBYTECODE=" "
		fi
	else
		if test -n "${VIRTUAL_ENV}"; then
			if [ ${PWD:0:${#VIRTUAL_ENV}-5} != ${VIRTUAL_ENV:0:${#VIRTUAL_ENV}-5} ]; then
				unset PYTHONDONTWRITEBYTECODE
				deactivate
			fi
		fi
	fi
}
export PROMPT_COMMAND=prompt_command
gerard@aldebaran:~$ 
```

Y con esto ya nos funciona el montaje. Asumamos que tenemos un fichero *requirements.txt* en la carpeta *sandbox*.

```bash
gerard@aldebaran:~$ cd projects/
gerard@aldebaran:~/projects$ cat sandbox/requirements.txt 
Django==1.10.5
gerard@aldebaran:~/projects$ 
```

Solo necesitamos entrar en ella para que se ejecute nuestra función; como hay un *requirements.txt* y no hay un *.venv*, lo crea, instalando en él las dependencias contenidas en el fichero *requirements.txt*.

```bash
gerard@aldebaran:~/projects$ cd sandbox/
New python executable in /home/gerard/projects/sandbox/.venv/bin/python
Installing setuptools, pip, wheel...done.
Collecting Django==1.10.5 (from -r requirements.txt (line 1))
  Using cached Django-1.10.5-py2.py3-none-any.whl
Installing collected packages: Django
Successfully installed Django-1.10.5
(.venv) gerard@aldebaran:~/projects/sandbox$ 
```

Ahora ya tenemos en *virtualenv* activado, hasta salir de la carpeta. Si volvemos a entrar, solo lo acitva, sin reinstalarlo. Al entrar en una subcarpeta, no lo desactiva.

```bash
(.venv) gerard@aldebaran:~/projects/sandbox$ cd ..
gerard@aldebaran:~/projects$ cd sandbox/
(.venv) gerard@aldebaran:~/projects/sandbox$ cd folder/
(.venv) gerard@aldebaran:~/projects/sandbox/folder$ 
```

Y con esto me evito tener que ir preocupándome de los *virtualenvs* y de los fichero *.pyc*. Muy útil y muy productivo.
