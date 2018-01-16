Title: Evitando usar virtualenv mediante el uso de PYTHONPATH
Slug: evitando-usar-virtualenv-mediante-el-uso-de-pythonpath
Date: 2018-01-22 10:00
Category: Operaciones
Tags: python, virtualenv, pip



Soy un gran fan de **python** y siempre ando trasteando con alguna librería nueva, en vistas a un *script* para simplificar mi trabajo, o simplemente como un *wekeend project*. Me es infinitamente útil usar **virtualenv**, pero genera una carpeta que ocupa demasiado y contiene algo más que solamente las librerías.

De hecho, solo tenemos que comprobar lo que ocupa un *virtualenv* vacío:

```bash
gerard@aldebaran:~/test$ virtualenv env
New python executable in /home/gerard/test/env/bin/python
Installing setuptools, pip, wheel...done.
gerard@aldebaran:~/test$ du -sh env/
16M	env/
gerard@aldebaran:~/test$ 
```

Por el propio funcionamiento de **python**, las carpetas de librerías son relativas al binario del mismo lenguaje, así que no es de extrañar que *virtualenv* ponga un binario en cada entorno; activar este entorno se limita a poner la carpeta *bin/* del *virtualenv* en el *PATH*. A esto le añadimos las herramientas *pip* y *easy_install*, y tenemos un montón de espacio desperdiciado.

```bash
gerard@aldebaran:~/test$ find env/ -type f | xargs ls -lrSh 2>/dev/null | tail
-rw-r--r-- 1 gerard gerard 114K mar 22 15:13 env/lib/python2.7/site-packages/pkg_resources/__init__.pyc
-rw-r--r-- 1 gerard gerard 114K mar 22 15:13 env/lib/python2.7/site-packages/pip/_vendor/pkg_resources/__init__.pyc
-rw-r--r-- 1 gerard gerard 115K mar 22 15:13 env/lib/python2.7/site-packages/pip/_vendor/html5lib/html5parser.py
-rw-r--r-- 1 gerard gerard 119K mar 22 15:13 env/lib/python2.7/site-packages/pip/_vendor/html5lib/html5parser.pyc
-rw-r--r-- 1 gerard gerard 219K mar 22 15:13 env/lib/python2.7/site-packages/pip/_vendor/pyparsing.py
-rw-r--r-- 1 gerard gerard 221K mar 22 15:13 env/lib/python2.7/site-packages/pyparsing.pyc
-rw-r--r-- 1 gerard gerard 222K mar 22 15:13 env/lib/python2.7/site-packages/pip/_vendor/pyparsing.pyc
-rw-r--r-- 1 gerard gerard 226K mar 22 15:13 env/lib/python2.7/site-packages/pyparsing.py
-rw-r--r-- 1 gerard gerard 337K mar 22 15:13 env/lib/python2.7/site-packages/pip/_vendor/requests/cacert.pem
-rwxr-xr-x 1 gerard gerard 3,7M mar 22 15:13 env/bin/python
gerard@aldebaran:~/test$ 
```

Las carpetas desde las que se cargan los módulos y librerías de **python** no son inmutables; se pueden añadir en *runtime* a la lista *sys.path* o se puede indicar en las variables de entorno del sistema, como podemos ver en [la documentación](https://docs.python.org/2/using/cmdline.html#envvar-PYTHONPATH). Solo necesitamos una manera de instalarlas en una carpeta propia, y esto es precisamente lo que nos permite el *flag --target* de *pip*.

```bash
gerard@aldebaran:~/test$ pip install -t libs mongoengine
Collecting mongoengine
Collecting six (from mongoengine)
  Using cached six-1.10.0-py2.py3-none-any.whl
Collecting pymongo>=2.7.1 (from mongoengine)
  Using cached pymongo-3.4.0-cp27-cp27mu-manylinux1_x86_64.whl
Installing collected packages: six, pymongo, mongoengine
Successfully installed mongoengine-0.11.0 pymongo-3.4.0 six-1.10.0
gerard@aldebaran:~/test$ 
```

Y eso nos instala las librerías con sus dependencias en la carpeta *libs/*, que va a crear si hace falta.

**NOTA**: Si el paquete instalaba binarios, no va a hacerlo, ya que no dispone de tal carpeta para dejarlo; este método no sería posible.

```bash
gerard@aldebaran:~/test$ tree -d libs/
libs/
├── bson
├── gridfs
├── mongoengine
│   ├── base
│   └── queryset
├── mongoengine-0.11.0.dist-info
├── pymongo
├── pymongo-3.4.0.dist-info
└── six-1.10.0.dist-info

9 directories
gerard@aldebaran:~/test$ du -sh libs/
3,2M	libs/
gerard@aldebaran:~/test$ 
```

A pesar de la reducción de tamaño en disco, esto por sí solo no nos sirve de nada; si no le indicamos donde tiene que buscar **mongoengine**, el intérprete va a fallar importándolo:

```bash
gerard@aldebaran:~/test$ python
Python 2.7.9 (default, Jun 29 2016, 13:08:31) 
[GCC 4.9.2] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import mongoengine
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ImportError: No module named mongoengine
>>> 
```

Para usar esa carpeta de librerías, solo necesitamos que el intérprete de **python** sepa donde están, sea por la variable de entorno o modificando la lista de carpetas *sys.path* en *runtime*.

Veamos ambos casos, empezando con la opción en *runtime*:

```bash
gerard@aldebaran:~/test$ python
Python 2.7.9 (default, Jun 29 2016, 13:08:31) 
[GCC 4.9.2] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import mongoengine
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ImportError: No module named mongoengine
>>> import sys
>>> sys.path.append('libs')
>>> import mongoengine
>>> 
```

Y solo queda hacerlo mediante el uso de la variable de entorno *PYTHONPATH*, sea exportándola para su uso futuro, o modificándola solo para el proceso acompañante:

```bash
gerard@aldebaran:~/test$ PYTHONPATH=libs python
Python 2.7.9 (default, Jun 29 2016, 13:08:31) 
[GCC 4.9.2] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import mongoengine
>>> 
>>> exit()
gerard@aldebaran:~/test$ export PYTHONPATH=libs
gerard@aldebaran:~/test$ python
Python 2.7.9 (default, Jun 29 2016, 13:08:31) 
[GCC 4.9.2] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import mongoengine
>>> 
```

Ahora toca elegir cual de las dos formas os gusta más. Yo suelo utilizar la variable de entorno cuando ejecuto un *script* de *bash*, sino lo hago mediante *python*.
