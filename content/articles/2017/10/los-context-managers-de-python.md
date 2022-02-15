---
title: "Los context managers de python"
slug: "los-context-managers-de-python"
date: 2017-10-16
categories: ['Desarrollo']
tags: ['python', 'context manager']
---

Muchas veces nos pasa que necesitamos un objeto de esos que luego necesitan algún tipo de limpieza cuando ya no se necesitan. Cualquier programador avanzado os puede contar lo fácil que es olvidarse de la destrucción del mismo, y de las veces que lo ha hecho, él u otras personas.<!--more-->

Por suerte, **python** nos ofrece una forma de crear objetos con el *keyword with*, que nos asegura que el mismo lenguaje de programación llamará a los métodos de creación y destrucción del objeto. Este mecanismo se llama *context manager*.

Veamos un ejemplo simple de un *context manager* muy común y disponible en la biblioteca estándar de **python**:

```bash
gerard@sirius:~/contextmanagers$ cat example.py 
#!/usr/bin/env python

with open('greeting.txt') as f:
    print f.read()
gerard@sirius:~/contextmanagers$ cat greeting.txt 
Hello world
gerard@sirius:~/contextmanagers$ ./example.py 
Hello world

gerard@sirius:~/contextmanagers$ 
```

La idea es que la función `open()` va a inicializar y devolver un *file descriptor* que vamos a recoger como `f` gracias al *keyword* `as`. Cuando salgamos del bloque `with`, se va a llamar a una función que se va a encargar de cerrar el fichero a nivel de sistema operativo.

## Creando un context manager

Un *context manager* no es otra cosa que un objeto que tiene dos métodos: `__enter__()` y `__exit__()`. El método `__enter__()` es el que inicializa el objeto a devolver (el que recogemos con el *keyword* `as`) y lo devuelve, aunque es opcional devolver algo. El método `__exit__()` es el que se llama automáticamente cuando acaba el bloque `with`, y se encargaría de destruir el objeto devuelto.

Veamos un ejemplo para generar el marcado HTML de una forma programática:

```bash
gerard@sirius:~/contextmanagers$ cat html_v1.py 
#!/usr/bin/env python

class Tag(object):

    def __init__(self, tag):
        self.tag = tag

    def __enter__(self):
        print '<%s>' % self.tag

    def __exit__(self, *args):
        print '</%s>' % self.tag

with Tag('div'):
    with Tag('p'):
        print 'Lorem ipsum'
    with Tag('p'):
        print 'et dolor sit amet'
gerard@sirius:~/contextmanagers$ ./html_v1.py 
<div>
<p>
Lorem ipsum
</p>
<p>
et dolor sit amet
</p>
</div>
gerard@sirius:~/contextmanagers$ 
```

Este ejemplo no es muy útil, pero queda claro como y cuando se llaman los creadores y destructores. Es interesante que no devolvemos ninguna variable en el método `__enter__()`, y que por lo tanto, la cláusula `with` no recoge nada con un `as`.

## Una versión todavía más simple

Crear el objeto que va a actuar como *context manager* es interesante, pero también un montón de líneas en nuestro código. Si queremos simplificar nuestro *context manager*, podemos encontrar la solución en la biblioteca estándar de **python**, en el módulo *contextlib*.

De esta forma, el ejemplo anterior queda reducido a uno similar, que es el que sigue:

```bash
gerard@sirius:~/contextmanagers$ cat html_v2.py 
#!/usr/bin/env python

from contextlib import contextmanager

@contextmanager
def tag(tag):
    print '<%s>' % tag
    yield
    print '</%s>' % tag

with tag('div'):
    with tag('p'):
        print 'Lorem ipsum'
    with tag('p'):
        print 'et dolor sit amet'
gerard@sirius:~/contextmanagers$ ./html_v2.py 
<div>
<p>
Lorem ipsum
</p>
<p>
et dolor sit amet
</p>
</div>
gerard@sirius:~/contextmanagers$ 
```

En este caso es todavía más simple de entender: tenemos la inicialización, devolvemos la variable o nada con el *keyword* `yield` y finalmente tenemos el código de finalización.
