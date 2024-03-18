---
title: "Breve introducción a los ficheros zipapp de python"
slug: "breve-introduccion-a-los-ficheros-zipapp-de-python"
date: "2024-03-18"
categories: ['Desarrollo']
tags: ['python', 'zipapp', 'pip', 'gunicorn']
---

Hace mucho tiempo que sé que puedo importar módulos y paquetes de **python** desde
un archivo `.zip`, pero desconocía que puedo "empaquetar" un *script* con todas las
dependencias que tiene y hacerlo autocontenido, ya sea ejecutable o no. Solo haría
falta un intérprete de **python** y su librería estándar para ejecutarlo.<!--more-->

Desde la versión 2.6, **python** puede interpretar un fichero `.zip`, ejecutando un
fichero `__main__.py` como su punto de entrada. En la versión 3.5, esta funcionalidad
se hizo oficial, aprovechando que un fichero `.zip` puede contener datos arbitrarios
para añadir el intérprete a usar, en caso de ser ejecutable.

Además de este fichero `__main__.py`, este fichero puede contener otros paquetes,
ajenos o propios, que serán importables por el intérprete que ejecute el fichero.
Esto lo convierte en un fichero tipo `.jar` de **java**, y nos permite crear un
fichero ejecutable, que solo necesitaría un intérprete de **python** adecuado.

**AVISO**: Las extensiones compiladas en fichero `.so` o binarios en el fichero
`.zip` no se pueden cargar, por limitaciones del sistema operativo. Es importante
que el código contenido pueda ejecutar sin ellos, o que el sistema operativo
disponga de ellos de forma externa.

## Empaquetando un script arbitrario

Supongamos que tenemos un *script* para obtener nuestra dirección IP pública, usando
la API que nos ofrece [ipify][1]. Para conseguir este fin, vamos a utilizar **urllib3**,
que no está en la librería estándar y nos obligará a incluirlo en nuestra **zipapp**:

```bash
gerard@leviathan:~/workspace$ cat ipify.py
import urllib3

def show_my_ip():
    resp = urllib3.request('GET', 'https://api.ipify.org?format=json')
    print(f'IP Address: {resp.json().get("ip")}')
gerard@leviathan:~/workspace$
```

Para gestionar las dependencias, voy a utilizar un fichero `requirements.txt` y voy
a instalarlas usando **pip**. De esta forma, ambos ficheros pueden ser versionados
en un repositorio de código fuente.

```bash
gerard@leviathan:~/workspace$ cat requirements.txt
urllib3==2.2.1
gerard@leviathan:~/workspace$
```

La idea es que vamos a preparar una carpeta base para el fichero **zipapp**, y vamos
a añadir nuestro código, todas las dependencias, y un fichero `__main__.py`. Empezamos
instalando las dependencias necesarias; acto seguido copiamos nuestro código, que se
limita al fichero `ipify.py`.

```bash
gerard@leviathan:~/workspace$ pip install -r requirements.txt -t dist
...
gerard@leviathan:~/workspace$
```

**NOTA**: Al instalar las dependencias, puede interesarnos añadir los *flags*
`--no-compile` (para evitar ficheros `.pyc`) y `--no-binary :all:` para obtener
paquetes sin extensiones compiladas (si el paquete lo admite). Esto reducirá el tamaño
final del empaquetado, aunque va a causar que el código se cargue un poco más lento.

```bash
gerard@leviathan:~/workspace$ cp ipify.py dist/
gerard@leviathan:~/workspace$
```

Solo nos faltaría un fichero `__main__.py`, que se va a limitar a importar la función
`show_my_ip()` y a ejecutarla. Tan común es este caso, que el proceso de empaquetado
nos ofrece la generación del `__main__.py` con este comportamiento; voy a utilizar
esta facilidad, en el momento del empaquetado. En este momento, tenemos este contenido
para empaquetar:

```bash
gerard@leviathan:~/workspace$ tree -L 1 dist/
dist/
├── urllib3
├── urllib3-2.2.1.dist-info
└── ipify.py

2 directories, 1 file
gerard@leviathan:~/workspace$
```

Para empaquetar nuestra **zipapp**, basta con invocar el módulo `zipapp`, con algunos
*flags* interesantes:

```bash
gerard@leviathan:~/workspace$ python3 -m zipapp dist/ -o show_my_ip.pyz -m ipify:show_my_ip -p "/usr/bin/env python3" -c
gerard@leviathan:~/workspace$
```

Los *flags* y argumentos utilizados son:

* `dist/` &rarr; es la carpeta que será la base del fichero `.zip` (nuestra **zipapp**)
* `-o`/`--output` &rarr; sirve para indicar el fichero de salida; en caso de no indicarse, utilizaría el mismo nombre de la carpeta base, con extensión `.pyz` (`dist.pyz` en nuestro caso)
* `-m`/`--main` &rarr; indica que hay que crear un fichero `__main__.py` que importará y ejecutará nuestra función (en nuestro caso, usaríamos la función `show_my_ip()` del módulo `ipify`)
* `-p`/`--python` &rarr; indica que el fichero resultante será ejecutable, y que se interpreta con el *shebang* indicado (`/usr/bin/env python3` en nuestro caso)
* `-c`/`--compress` &rarr; indica que nuestra **zipapp** será un fichero comprimido (añadiendo tiempo de carga a cambio de tamaño en disco)

Y con esto tenemos un fichero **zipapp** que funcionaría de forma similar a un *script*,
siendo interpretado con el *shebang* indicado. El nombre del mismo no es importante, y
lo podemos poner en una carpeta en nuestro **path** para su fácil acceso.

```bash
gerard@leviathan:~/workspace$ ./show_my_ip.pyz
IP Address: 213.94.42.212
gerard@leviathan:~/workspace$
```

```bash
gerard@leviathan:~/workspace$ show_my_ip
IP Address: 213.94.42.212
gerard@leviathan:~/workspace$
```

Es interesante ver que nuestra **zipapp** tiene lo mismo que la carpeta `dist/`,
con el añadido del fichero `__main__.py`, cuyo contenido es bastante simple.

```bash
gerard@leviathan:~/workspace$ unzip -l show_my_ip.pyz | awk '{print $4}'
...
__main__.py
ipify.py
urllib3-2.2.1.dist-info/
urllib3/
...
gerard@leviathan:~/workspace$
```

```bash
gerard@leviathan:~/workspace$ unzip show_my_ip.pyz __main__.py
Archive:  show_my_ip.pyz
  inflating: __main__.py
gerard@leviathan:~/workspace$
```

```bash
gerard@leviathan:~/workspace$ cat __main__.py
# -*- coding: utf-8 -*-
import ipify
ipify.show_my_ip()
gerard@leviathan:~/workspace$
```

## Empaquetando una aplicación WSGI

Crear un **zipapp** de una aplicación WSGI no es muy diferente; el único concepto
diferente es que no ejecutamos la aplicación, sino un servidor de aplicaciones
que va a importar nuestra aplicación.

Para empezar el empaquetado, podemos utilizar cualquier aplicación WSGI; desde la
aplicación `wsgiref.simple_server:demo_app` hasta una aplicación escrita sin ningún
*framework*, pasando por todas las opciones de *framework* imaginables. En este
momento es irrelevante como esté construida la aplicación así que usamos un ejemplo
mínimo, contenido en su propio *package* y sacado de [la wikipedia][2]:

```bash
gerard@builder:~/webapp$ cat webapp/__init__.py
def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    yield b'Hello, World!\n'

app = application
gerard@builder:~/webapp$
```

Es importante recordar que no podemos ejecutar binarios dentro del fichero `.zip`,
ni importar librerías de sistema, así que vamos a optar por un servidor de aplicaciones
*pure python*, como podría ser **gunicorn**, que vamos a poner también en nuestra
**zipapp**. Nuestra aplicación no necesita más requisitos, así que nos quedaría
muy simple (de momento, no he puesto ni la versión de **gunicorn**):

```bash
gerard@builder:~/webapp$ cat requirements.txt
gunicorn
gerard@builder:~/webapp$
```

De forma análoga al caso anterior, nos limitamos a instalar las dependencias en una
carpeta temporal, en donde también copiaremos nuestra aplicación:

```bash
gerard@builder:~/webapp$ pip install -r requirements.txt -t dist
gerard@builder:~/webapp$
```

```bash
gerard@builder:~/webapp$ cp -R webapp/ dist/
gerard@builder:~/webapp$
```

Llegados a este punto, tenemos el siguiente contenido en la carpeta temporal:

```bash
gerard@builder:~/webapp$ tree dist -L 1
dist
├── bin
├── gunicorn
├── gunicorn-21.2.0.dist-info
├── packaging
├── packaging-24.0.dist-info
└── webapp

6 directories, 0 files
gerard@builder:~/webapp$
```

**TRUCO**: Cuando **gunicorn** importa la aplicación lo hace desde varios *pythonpath*.
Si la aplicación no se puede cargar del fichero `.zip` (por ejemplo, porque no la
pusimos), puede cargar la misma de la carpeta de trabajo o de otras carpetas selectas.
Esto hace que podamos tener un **zipapp** sin aplicación, con las dependencias y el
servidor de aplicaciones, mientras modificamos la aplicación en la misma carpeta...

En este momento, solo nos falta saber la función que tenemos que ejecutar para levantar
el servidor **gunicorn**, que usaremos para autogenerar nuestro `__main__.py`. Solo hace
falta mirar el *script* instalador por **pip** para ver lo que ejecuta el binario `gunicorn`.

```bash
gerard@builder:~/webapp$ cat dist/bin/gunicorn
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import sys
from gunicorn.app.wsgiapp import run
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(run())
gerard@builder:~/webapp$
```

Vemos que se ejecuta una función `run()` importada del *package* `gunicorn.app.wsgiapp`.
Entonces, tendremos que empaquetar la aplicación indicando que la función es `gunicorn.app.wsgiapp:run`.

```bash
gerard@builder:~/webapp$ python3 -m zipapp dist/ -o webapp.pyz -m gunicorn.app.wsgiapp:run
gerard@builder:~/webapp$
```

**NOTA**: No se ha indicado el intérprete de **python**; eso obliga a que la invocación
se haga especificándolo, por ejemplo, `python3 webapp.pyz webapp:app`. Como esta
aplicación se va a desplegar en otra máquina, dejamos que el administrador indique el
*path* correcto en destino. Tampoco hemos aplicado el *flag* de compresión, por brevedad.

Podemos ver el fichero `__main__.py` generado descomprimiéndolo de nuestra **zipapp**:

```bash
gerard@builder:~/webapp$ unzip webapp.pyz __main__.py
Archive:  webapp.pyz
 extracting: __main__.py
gerard@builder:~/webapp$
```

```bash
gerard@builder:~/webapp$ cat __main__.py
# -*- coding: utf-8 -*-
import gunicorn.app.wsgiapp
gunicorn.app.wsgiapp.run()
gerard@builder:~/webapp$
```

Podemos versionar este `__main__.py` para modificarlo a nuestro antojo; dos modificaciones
útiles son el añadido del parámetro aplicación (así nuestro administrador no necesita poner,
ni siquiera conocerlo), y una verificación de la versión de **python** (para ahorrarnos
desagradables sorpresas si no se cumplen nuestras expectativas). Tras ambas modificaciones,
me quedo con esto:

```bash
gerard@builder:~/webapp$ cat __main__.py
import sys
import gunicorn.app.wsgiapp

if sys.version_info < (3, 8):
    raise Exception('Required python >= 3.8')

sys.argv.append('webapp:app')
gunicorn.app.wsgiapp.run()
gerard@builder:~/webapp$
```

**WARNING**: No os olvidéis de copiarlo en la carpeta `dist/`; a partir de ahora, el
comando de empaquetado no necesitará indicar el *flag* `-m`, puesto que el `__main__.py`
ya lo ponemos nosotros.

```bash
gerard@builder:~/webapp$ cp __main__.py dist/
gerard@builder:~/webapp$
```

```bash
gerard@builder:~/webapp$ python3 -m zipapp dist/ -o webapp.pyz
gerard@builder:~/webapp$
```

Ahora solo nos queda invocar nuestra aplicación con algo tipo `python3 webapp.pyz <otros flags>`.
Esto hace la distribución de nuestra aplicación más cómoda, en la forma de un solo fichero.
La configuración, sin embargo, deberemos indicarla de otra manera (por ejemplo, con variables
de entorno o ficheros de configuración en un *path* conocido fuera del **zipapp**).

[1]: https://www.ipify.org/
[2]: https://en.wikipedia.org/wiki/Web_Server_Gateway_Interface
