---
title: "Prototipos de proyectos de forma fácil"
slug: "prototipos-de-proyectos-de-forma-facil"
date: "2021-05-28"
categories: ['Miscelánea']
tags: ['prototipo', 'python', 'cookiecutter', 'copier']
---

Cada vez nos encontramos con el mismo problema; empezamos un nuevo proyecto
y tenemos que crear toda la estructura del proyecto partiendo de cero, de un
ejemplo, o haciendo copy-paste de otro anterior. Esto implica cambiar algunos
nombres de ficheros y carpetas, o contenido de ciertos ficheros; es toda una
invitación al desastre.<!--more-->

Hoy vamos a ver como podemos hacer estas plantillas usando dos alternativas
escritas en **python**: *cookiecutter* y *copier*. Si no las tenemos, podemos
instalárnoslas, por ejemplo, en un *virtualenv*.

```bash
gerard@arcadia:~/projects/bootstrap$ python3 -m venv env
gerard@arcadia:~/projects/bootstrap$
```

```bash
gerard@arcadia:~/projects/bootstrap$ . env/bin/activate
(env) gerard@arcadia:~/projects/bootstrap$
```

```bash
(env) gerard@arcadia:~/projects/bootstrap$ pip install cookiecutter copier
...
(env) gerard@arcadia:~/projects/bootstrap$
```

```bash
(env) gerard@arcadia:~/projects/bootstrap$ pip freeze | egrep "cookiecutter|copier"
cookiecutter==1.7.3
copier==5.1.0
(env) gerard@arcadia:~/projects/bootstrap$
```

## Exponemos el ejemplo

A partir de ahora vamos a trabajar con un ejemplo bastante simple, pero con
alto valor didáctico: vamos a empezar con un proyecto básico escrito usando
[el *framework* falcon][1].

```bash
(env) gerard@arcadia:~/projects/bootstrap$ tree ejemplo/
ejemplo/
├── myapi
│   └── __init__.py
├── requirements.txt
└── server.sh

1 directory, 3 files
(env) gerard@arcadia:~/projects/bootstrap$
```

Incluyo el contenido de todos los ficheros por tener el ejemplo completo,
aunque no es muy relevante, cubre todas las necesidades de un prototipo
más grande, aunque no más complejo.

```bash
(env) gerard@arcadia:~/projects/bootstrap$ cat ejemplo/myapi/__init__.py
import falcon

class HelloResource:
    def on_get(self, req, resp, name):
        resp.media = {'hello': name}

app = falcon.App()
app.add_route('/hello/{name}', HelloResource())
(env) gerard@arcadia:~/projects/bootstrap$
```

```bash
(env) gerard@arcadia:~/projects/bootstrap$ cat ejemplo/requirements.txt
gunicorn
falcon
(env) gerard@arcadia:~/projects/bootstrap$
```

```bash
(env) gerard@arcadia:~/projects/bootstrap$ cat ejemplo/server.sh
#!/bin/bash

export PYTHONDONTWRITEBYTECODE=" "

gunicorn --reload --bind 127.0.0.1:8080 myapi:app
(env) gerard@arcadia:~/projects/bootstrap$
```

La parte más importante a tener en cuenta es que hay cosas que van a cambiar
entre diferentes instancias de esta plantilla; para este ejemplo tan simple,
vamos a renombrar la carpeta a un nombre más descriptivo (es un *package* de
**python**), y el *script* de servidor va a necesitar reflejar eso mismo en
la aplicación que levanta.

## Aproximación con cookiecutter

Una plantilla de **cookiecutter** no es más que una carpeta contenedora, que
incluye los metadatos necesarios y una carpeta con un nombre variable, que es
lo que se crea cuando la instanciamos.

Es obligado que esta primera carpeta tenga un nombre variable, y para eso tiene
que llamarse algo como `{{cookiecutter.variable}}`. Esto es lo mismo que debemos
poner en los ficheros cada vez que queramos reemplazar algún contenido concreto.

Digamos que lo parametrizamos y lo dejamos así:

```bash
(env) gerard@arcadia:~/projects/bootstrap$ tree falcon_api.cookiecutter/
falcon_api.cookiecutter/
├── {{cookiecutter.folder_name}}
│   ├── {{cookiecutter.package_name}}
│   │   └── __init__.py
│   ├── requirements.txt
│   └── server.sh
└── cookiecutter.json

2 directories, 4 files
(env) gerard@arcadia:~/projects/bootstrap$
```

Las carpetas tienen nombre variable; el `folder_name` sería la carpeta
contenedora del proyecto final y el `package_name` sería el nombre del
paquete **python**, que referenciamos en el fichero `server.sh` en el
comando de ejecución:

```bash
(env) gerard@arcadia:~/projects/bootstrap$ cat falcon_api.cookiecutter/\{\{cookiecutter.folder_name\}\}/server.sh
#!/bin/bash

export PYTHONDONTWRITEBYTECODE=" "

gunicorn --reload --bind 127.0.0.1:8080 {{cookiecutter.package_name}}:app
(env) gerard@arcadia:~/projects/bootstrap$
```

**NOTA**: El resto de ficheros no ha cambiado desde el ejemplo inicial.

Las variables se declaran en el fichero `cookiecutter.json`, con sus
valores por defecto, que se nos van a preguntar interactivamente cuando
usemos la plantilla.

```bash
(env) gerard@arcadia:~/projects/bootstrap$ cat falcon_api.cookiecutter/cookiecutter.json
{
  "folder_name": "myfolder",
  "package_name": "myapi"
}
(env) gerard@arcadia:~/projects/bootstrap$
```

Solo necesitamos ejecutar el comando `cookiecutter <ruta a la plantilla>`
para crear una instancia en la carpeta actual:

```bash
(env) gerard@arcadia:~/projects/bootstrap$ cookiecutter falcon_api.cookiecutter/
folder_name [myfolder]: folder1
package_name [myapi]:
(env) gerard@arcadia:~/projects/bootstrap$
```

En este caso indicamos un `folder_name` nuevo, pero aceptamos el
`package_name` por defecto. Con estas variables, **cookiecutter**
genera todos los nombres de carpetas, ficheros y su contenido; por
supuesto con los valores reemplazados.

```bash
(env) gerard@arcadia:~/projects/bootstrap$ tree folder1/
folder1/
├── myapi
│   └── __init__.py
├── requirements.txt
└── server.sh

1 directory, 3 files
(env) gerard@arcadia:~/projects/bootstrap$
```

```bash
(env) gerard@arcadia:~/projects/bootstrap$ cat folder1/server.sh
#!/bin/bash

export PYTHONDONTWRITEBYTECODE=" "

gunicorn --reload --bind 127.0.0.1:8080 myapi:app
(env) gerard@arcadia:~/projects/bootstrap$
```

## Versión mejorada con copier

Las diferencias con el anterior son mínimas; la carpeta contenedora sigue
siendo necesaria, pero los ficheros de la plantilla conviven en ella,
mezclados con los metadatos de **copier**.

```bash
(env) gerard@arcadia:~/projects/bootstrap$ tree falcon_api.copier/
falcon_api.copier/
├── [[package_name]]
│   └── __init__.py
├── copier.yml
├── requirements.txt
└── server.sh.jinja

1 directory, 4 files
(env) gerard@arcadia:~/projects/bootstrap$
```

```bash
(env) gerard@arcadia:~/projects/bootstrap$ cat falcon_api.copier/server.sh.jinja
#!/bin/bash

export PYTHONDONTWRITEBYTECODE=" "

gunicorn --reload --bind 127.0.0.1:8080 [[package_name]]:app
(env) gerard@arcadia:~/projects/bootstrap$
```

A simple vista saltan dos cosas a la vista: el uso de `[[variable]]` en
vez de `{{variable}}` y la presencia de una extensión para "marcar" los
ficheros que son plantillas, para ahorrarnos procesado. Es interesante ver
que no cargamos con el prefijo `cookiecutter.<variable>` y simplificamos
nuestra plantilla.

**NOTA**: En versiones posteriores de **copier** es posible indicar un
sufijo vacío para que se procesen todas, en caso de que lo veáis interesante.

La variables se indican en el fichero `copier.yml`, que es más simple
por ser un fichero YAML, y permite poner valores que afectan al resultado
del comando. En este caso, vamos a indicar otro sufijo (que sería `.tmpl`
por defecto en la versión usada).

```bash
(env) gerard@arcadia:~/projects/bootstrap$ cat falcon_api.copier/copier.yml
_templates_suffix: .jinja
package_name: myapi
(env) gerard@arcadia:~/projects/bootstrap$
```

Solo nos faltaría invocar a **copier** para crear una instancia de nuestro
proyecto nuevo. En este caso, la carpeta destino no se indica como variable,
sino como argumento en la invocación:

```bash
(env) gerard@arcadia:~/projects/bootstrap$ copier falcon_api.copier/ folder2

package_name? Format: yaml
🎤 [myapi]:

    create  requirements.txt
    create  server.sh
    create  myapi/
    create  myapi/__init__.py


(env) gerard@arcadia:~/projects/bootstrap$
```

Y obtenemos exactamente el mismo resultado de antes, sin sorpresas:

```bash
(env) gerard@arcadia:~/projects/bootstrap$ tree folder2/
folder2/
├── myapi
│   └── __init__.py
├── requirements.txt
└── server.sh

1 directory, 3 files
(env) gerard@arcadia:~/projects/bootstrap$
```

```bash
(env) gerard@arcadia:~/projects/bootstrap$ cat folder2/server.sh
#!/bin/bash

export PYTHONDONTWRITEBYTECODE=" "

gunicorn --reload --bind 127.0.0.1:8080 myapi:app
(env) gerard@arcadia:~/projects/bootstrap$
```

**WARNING**: Debido a un *bug*, no se conservan los permisos de los ficheros
originales; en este caso, hemos perdido el *flag* de ejecución de `server.sh`.

Ahora bien, hay algo que tiene **copier** que promete mucho: es capaz de
actualizar un proyecto ya creado desde una plantilla (que posteriormente ha
evolucionado), siempre que ambos estén versionados con **git**. Esto es algo
que tengo que investigar en el futuro.

[1]: {{< relref "/articles/2017/09/escribiendo-servicios-web-con-python-y-falcon.md" >}}
