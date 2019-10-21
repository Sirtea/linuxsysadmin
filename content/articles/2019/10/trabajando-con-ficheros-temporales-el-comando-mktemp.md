---
title: "Trabajando con ficheros temporales: el comando mktemp"
slug: "trabajando-con-ficheros-temporales-el-comando-mktemp"
date: "2019-10-21"
categories: ['Operaciones']
tags: ['fichero', 'temporal', 'script', 'bash']
---

En uno de los sitios en los que estuve trabajando, tenía un compañero un poco desordenado.
Cada vez que hacía un *script* que necesitaba guardar la salida en un fichero temporal,
reutilizaba los nombres o los acumulaba infinitamente en una carpeta temporal, cuyo nombre
dependía de la inspiración del momento.<!--more-->

Ambos comportamientos suponen un problema a la larga:

* El llenado de espacio o de inodos puede causar problemas en un sistema *linux*
    * Son servidores, así que es improbable que se reinicien y se libere la carpeta `/tmp`
    * Tener varias carpetas de ficheros temporales nos garantiza el caos absoluto y perder nuestros datos
* El reusado de nombres de ficheros es todavía más peligroso
    * Podemos sobreescribir algo importante de una ejecución anterior
    * Si hay dos ejecuciones paralelas de *scripts* que trabajen con ese fichero, los resultados serán impredecibles

Así pues, cuando yo trabajo con ficheros temporales, siempre utilizo el comando `mktemp`,
que nos crea un fichero vacío (garantizando que no existiera) y nos devuelve el *path*
completo al mismo; sin embargo **no lo elimina**, siendo este nuestro trabajo.

Para ello, hay dos técnicas utilizadas habitualmente por los que escribimos *scripts*:

* Lo creamos y lo eliminamos sin cerrarlo, con lo que no se eliminará efectivamente hasta que lo cerremos
* Podemos registrar un evento tipo *trap* para que al salir de nuestro *script* lo haga el propio *shell*

La que me gusta más es la segunda; es más limpia y no hay que ir con cuidado de no cerrar
el fichero antes de tiempo. Además, si el *script* falla, los *traps* se ejecutan igualmente.

## Un ejemplo práctico

Supongamos que tenemos un proceso de importación de datos de un sistema externo. Este
sistema nos proporciona unos datos en bruto que hay que procesar, cambiar de formato y,
posiblemente, insertar en una base de datos local.

Para obtener los datos es muy fácil hacerlo en **bash**, o tal vez alguien externo escribió el
*script* y no nos apetece reescribirlo; sin embargo, el procesado de datos lo vamos a hacer
en **python** porque nos ofrece muchas más facilidades para el proceso e inserción de los datos.

Así pues, tenemos un sistema de 3 *scripts*:

* Uno escrito en **bash** que obtiene los datos y los escribe en la salida estándar
* Uno en **python** que los procesa, los modifica y los guarda en la base de datos
* El *script* principal, también en **bash**, que llama a los otros dos

Para la salida del primer *script*, necesitamos recoger la salida en un fichero, para poder
pasárselo al segundo *script*; vamos a utilizar un fichero temporal para esto. El responsable
de crear y borrar los ficheros temporales va a ser el *script* principal, dejando que los
otros dos *scripts* simplemente los usen.

```bash
gerard@sirius:~/scripts$ cat ingesta_datos_externos.sh 
#!/bin/bash

TEMPFILE=$(mktemp)
echo "'${TEMPFILE}' creado"
trap 'rm -v ${TEMPFILE}' EXIT

./consultar_sistema_externo.sh > ${TEMPFILE}
./procesar_datos.py ${TEMPFILE}
gerard@sirius:~/scripts$ 
```

Estos dos *scripts* invocados harán lo que deban: el primero escribirá los datos en
la salida estándar, y el segundo los leerá para hacer lo que necesitemos; para limitar
el alcance del artículo, vamos ha hacer que no hagan nada.

```bash
gerard@sirius:~/scripts$ cat consultar_sistema_externo.sh 
#!/bin/bash
gerard@sirius:~/scripts$ 
```

```bash
gerard@sirius:~/scripts$ cat procesar_datos.py 
#!/usr/bin/env python3
gerard@sirius:~/scripts$ 
```

Nos quedamos con las tres ideas claves del artículo:

* Creamos un fichero temporal con `mktemp`, recogiendo su *path* en una variable
* Registramos un *trap* que elimine el fichero cuando el *script* principal acabe
* Trabajamos alegremente con nuestro fichero temporal, sin importar su nombre o su localización

Si necesitamos más control sobre la posición o el nombre del fichero temporal, podemos
poner algunos parámetros en la invocación de `mktemp`, aunque esto lo tendréis que
estudiar por vosotros mismos; la información está fácilmente a la vista:

```bash
gerard@sirius:~/scripts$ mktemp --help
Modo de empleo: mktemp [OPCIÓN]... [PLANTILLA]
Crea un fichero o un directorio temporal, de forma segura, y muestra su nombre.
TEMPLATE debe contener al menos 3 'X's consecutivas en la última componente.
Si no se especifica PLANTILLA, utiliza tmp.XXXXXXXXXX e implica --tmpdir.
los ficheros se crean con permisos u+rw, los directories con u+rwx,
menos las restricciones de umask.

  -d, --directory     crea un directorio, no un fichero
  -u, --dry-run       no crea nada, simplemente muestra un nombre (inseguro)
  -q, --quiet         elimina los mensajes sobre fallos de creación de
                        ficheros/directorios
      --suffix=SUF    añade SUF a PLANTILLA; SUF no debe contener la barra.
                        Esta opción va implícita si TEMPLATE no termina en X
  -p DIR --tmpdir[=DIR]  interpreta PLANTILLA relativa a DIR; si no se especifica
                     DIR, utiliza $TMPDIR si existe, o si no /tmp.
                     Con esta opción, PLANTILLA no debe ser un nombre absoluto;
                     al contrario que con -t, PLANTILLA puede contener barras,
                     pero mktemp solamente crea la última componente
  -t               interpreta PLANTILLA como una sola componente de nombre de
                     fichero relativa a un directorio: $TMPDIR, si existe;
                     o si no el directorio especificado con -p; o si no /tmp
                     (obsoleto)
      --help     muestra esta ayuda y finaliza
      --version  informa de la versión y finaliza

ayuda en línea sobre GNU coreutils: <http://www.gnu.org/software/coreutils/>
Informe de errores de traducción en mktemp a <http://translationproject.org/team/es.html>
Full documentation at: <http://www.gnu.org/software/coreutils/mktemp>
or available locally via: info '(coreutils) mktemp invocation'
gerard@sirius:~/scripts$ 
```

Y con esto evitamos seguir acumulando ficheros innecesarios, que solo molestan.

**Feliz *scripting*!**
