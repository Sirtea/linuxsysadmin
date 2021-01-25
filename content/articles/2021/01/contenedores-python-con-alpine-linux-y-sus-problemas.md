---
title: "Contenedores Python con Alpine Linux y sus problemas"
slug: "contenedores-python-con-alpine-linux-y-sus-problemas"
date: "2021-01-25"
categories: ['Sistemas']
tags: ['docker', 'python', 'alpine', 'musl']
---

Los que leéis de vez en cuando este *blog* ya sabéis que tengo especial
predilección por **Python** y **Docker**,  con el que utilizo la versión
"alpine" de las imágenes siempre que puedo. Al menos eso es lo que pensaba
hasta hace poco tiempo, cuando la librería *musl libc* me dejó tirado.<!--more-->

Y es que algunas de las librerías de **Python** están escritas en lenguaje C;
eso significa que *se compilan* en tiempo de instalación. Esto es un problema
en un entorno mínimo, en donde no se tienen compiladores. Para echar más sal
a la herida, no suelen disponer de una versión *pure python* para estos casos.

## Una librería *pure python*

Por suerte son la gran mayoría de ellas. Están escritas en **Python** y
ejecutan como ficheros `.py`. Como no dependen de librerías del sistema, no
tienen problemas en ejecutar en un contenedor normal o *alpine*.

Veamos como ejemplo **gunicorn**:

```bash
gerard@atlantis:~$ docker run -ti --rm python:3.8-alpine sh
/ # pip install gunicorn
...
Successfully installed gunicorn-20.0.4
...
/ # find /usr/local/lib/python3.8/site-packages/gunicorn/ -type f -name "*.so"
/ # 
```

Podemos ver que no hay problemas instalando y que no genera librerías
compiladas (que generan un fichero `.so`). Eso significa que no necesitamos
nada más que el intérprete de **python** para ejecutar este programa.

## Una librería híbrida

Hay otras librerías que funcionan bien como *pure python*, pero aportan la
capacidad de *compilarse* para acelerar el tiempo de ejecución. Si encuentran
los compiladores necesarios, los utilizan; sino, utilizan una versión
*pure python* de la misma (que se presupone algo más lenta).

Como ejemplo podemos mencionar **pymongo**:

```bash
gerard@atlantis:~$ docker run -ti --rm python:3.8-alpine sh
/ # pip install pymongo
...
Successfully installed pymongo-3.11.2
...
/ # find /usr/local/lib/python3.8/site-packages/ -type f -name "*.so"
/ # 
```

Estamos ante el mismo caso que antes; no se compila y funciona sin extensiones
compiladas. Veamos ahora lo que pasa si se encuentra con un compilador y las
cabeceras adecuadas:

```bash
gerard@atlantis:~$ docker run -ti --rm python:3.8-alpine sh
/ # apk add gcc musl-dev
...
/ # pip install pymongo
Collecting pymongo
  Downloading pymongo-3.11.2.tar.gz (770 kB)
     |████████████████████████████████| 770 kB 2.9 MB/s 
Building wheels for collected packages: pymongo
  Building wheel for pymongo (setup.py) ... done
  Created wheel for pymongo: filename=pymongo-3.11.2-cp38-cp38-linux_x86_64.whl size=383630 sha256=d292dac8e08458d340ee262831da57e188021ff875a9c8e024aa9512572fc9a7
  Stored in directory: /root/.cache/pip/wheels/67/fc/93/cf33d1a4fc544841766e79597b093ddb4da4e6563b037cc5ab
Successfully built pymongo
Installing collected packages: pymongo
Successfully installed pymongo-3.11.2
...
/ # find /usr/local/lib/python3.8/site-packages/ -type f -name "*.so"
/usr/local/lib/python3.8/site-packages/pymongo/_cmessage.cpython-38-x86_64-linux-gnu.so
/usr/local/lib/python3.8/site-packages/bson/_cbson.cpython-38-x86_64-linux-gnu.so
/ # 
```

Ahora encontramos dos módulos (*cmessage* y *cbson*) que no se interpretan y
ejecutan código directamente utilizando la librería C del sistema. Se supone que
esto se traduce en una mejora de los tiempos de ejecución del módulo, pero tenemos
el coste extra en tiempo de construcción del contenedor y en eliminar el
compilador del contenedor resultante.

## Una librería problemática

A veces nos encontramos una librería de **python** que no funciona si no tiene
una versión compilada; esto es un problema porque la compilación depende de
los compiladores locales y de la librería de C del sistema presente. Hay que
compilar de cero **sí o sí**.

Como apasionado de los *tokens* **JWT**, suelo utilizar las librerías **pyjwt**
o **python-jose**. Las dos confían en segundas librerías para hacer los cálculos
criptográficos necesarios para sus firmas.

En el caso de **pyjwt**, esta segunda librería es **cryptography**; **python-jose**
puede utilizar otras segundas librerías, incluso de la librería estándar de
**python**. Lo que sí que es cierto es que si utiliza **cryptography**, el tiempo
de firma y verificación se reduce drásticamente.

Vamos pues a utilizar la librería **cryptography**:

```bash
/ # pip install cryptography
Collecting cryptography
  Downloading cryptography-3.3.1.tar.gz (539 kB)
     |████████████████████████████████| 539 kB 3.7 MB/s 
  Installing build dependencies ... error
  ERROR: Command errored out with exit status 1:
   command: /usr/local/bin/python /usr/local/lib/python3.8/site-packages/pip install --ignore-installed --no-user --prefix /tmp/pip-build-env-gni7fvxi/overlay --no-warn-script-location --no-binary :none: --only-binary :none: -i https://pypi.org/simple -- 'setuptools>=40.6.0' wheel 'cffi>=1.12; platform_python_implementation != '"'"'PyPy'"'"''
       cwd: None
...
/ # 
```

Incluso con el compilador y las cabeceras de *musl* no llegamos a buen puerto...

```bash
gerard@atlantis:~$ docker run -ti --rm python:3.8-alpine sh
/ # apk add gcc musl-dev
...
/ # pip install cryptography
Collecting cryptography
  Downloading cryptography-3.3.1.tar.gz (539 kB)
     |████████████████████████████████| 539 kB 2.9 MB/s 
  Installing build dependencies ... error
  ERROR: Command errored out with exit status 1:
   command: /usr/local/bin/python /usr/local/lib/python3.8/site-packages/pip install --ignore-installed --no-user --prefix /tmp/pip-build-env-iynvp75u/overlay --no-warn-script-location --no-binary :none: --only-binary :none: -i https://pypi.org/simple -- 'setuptools>=40.6.0' wheel 'cffi>=1.12; platform_python_implementation != '"'"'PyPy'"'"''
       cwd: None
```

Y es que esta librería necesita una lista de otras cabeceras de otras librerías
del sistema; es factible encontrarlas todas, pero podemos pasar un mal rato
para conseguirlo.

```bash
gerard@atlantis:~$ docker run -ti --rm python:3.8-alpine sh
/ # apk add gcc musl-dev libffi-dev openssl-dev
...
/ # pip install cryptography
...
Building wheels for collected packages: cryptography
  Building wheel for cryptography (PEP 517) ... done
  Created wheel for cryptography: filename=cryptography-3.3.1-cp38-cp38-linux_x86_64.whl size=362591 sha256=b83b2e23707f244014d3dff88edecc42695d3977d0dced4f82768043448dad20
  Stored in directory: /root/.cache/pip/wheels/9b/bd/12/c040f2df6b28138b66b0361cd218180a278b95763fc2466951
Successfully built cryptography
Installing collected packages: pycparser, six, cffi, cryptography
Successfully installed cffi-1.14.4 cryptography-3.3.1 pycparser-2.20 six-1.15.0
...
/ # 
```

## Y que pasa con otras distribuciones?

Pues pasa exactamente lo mismo; la única diferencia es que todas (menos
**Alpine Linux**) utilizan la librería **glibc** (en vez de **musl**).

Hay que recordar que [PyPI][1] distribuye las librerías, tanto en formato fuente
(ficheros `.tar.gz` o similar) como en formato *wheel* (ficheros `.whl`). Este
segundo formato es un formato binario, que básicamente es un fichero tipo *zip*
con las librerías ya compiladas.

Como la mayoría de distribuciones utilizan **glibc**, se suelen encontrar en
[PyPI][1] los ficheros *wheel* correspondientes a esta librería, para su uso
fácil y rápido en la mayoría de distribuciones sin necesitar una etapa de compilación.

Veamos lo que pasa cuando utilizamos la imagen `python:3.8-slim` (basada en **Debian**):

```bash
gerard@atlantis:~$ docker run -ti --rm python:3.8-slim bash
root@85a9ba8d702b:/# pip wheel cryptography
Collecting cryptography
  Downloading cryptography-3.3.1-cp36-abi3-manylinux2010_x86_64.whl (2.6 MB)
     |████████████████████████████████| 2.6 MB 2.4 MB/s 
Collecting cffi>=1.12
  Downloading cffi-1.14.4-cp38-cp38-manylinux1_x86_64.whl (411 kB)
     |████████████████████████████████| 411 kB 13.9 MB/s 
Collecting six>=1.4.1
  Downloading six-1.15.0-py2.py3-none-any.whl (10 kB)
Collecting pycparser
  Downloading pycparser-2.20-py2.py3-none-any.whl (112 kB)
     |████████████████████████████████| 112 kB 8.6 MB/s 
Saved /cryptography-3.3.1-cp36-abi3-manylinux2010_x86_64.whl
Saved /cffi-1.14.4-cp38-cp38-manylinux1_x86_64.whl
Saved /six-1.15.0-py2.py3-none-any.whl
Saved /pycparser-2.20-py2.py3-none-any.whl
...
root@85a9ba8d702b:/# python -m zipfile -l cryptography-3.3.1-cp36-abi3-manylinux2010_x86_64.whl 
File Name                                             Modified             Size
...
cryptography/hazmat/bindings/_padding.abi3.so  2020-12-10 02:19:26        36240
cryptography/hazmat/bindings/_openssl.abi3.so  2020-12-10 02:19:26      7084392
...
root@85a9ba8d702b:/# 
```

Se descarga los ficheros *wheel* directamente compilados y listos para desempaquetar,
lo que reduce el tiempo de *build* del contenedor y la complejidad del mismo de
una forma notable.

## Conclusiones

Muchas veces nos obsesionamos con reducir el tamaño de nuestras imágenes
con imágenes base más pequeñas. Sin embargo, esto tiene un coste en el que
rara vez pensamos.

La reducción "grande" se consigue con otras buenas prácticas, y no con la
utilización de otras bases. Si miramos el tamaño de las imágenes base, en
el caso de **python**, es una diferencia de tan solo 50 o 60 megabytes.

¿Vale la pena sufrir tanto como para justificar esos 60mb? Si pretendemos
construir la imagen y guardarla en un registro, puede valernos; si estamos
recreando la imagen continuamente en la etapa de desarrollo, igual preferimos
la simplicidad y la velocidad, en detrimento del tamaño final de la imagen.

[1]: https://pypi.org/
