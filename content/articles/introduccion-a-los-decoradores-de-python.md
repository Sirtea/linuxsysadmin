Title: Introducción a los decoradores de python
Slug: introduccion-a-los-decoradores-de-python
Date: 2017-09-04 10:00
Category: Desarrollo
Tags: python, decorador



Mucha gente no sabe de lo que hablamos cuando nos referimos a *decoradores* en contexto de programación *python*. No es un concepto demasiado complejo, pero nos puede servir para simplificar bastante nuestro código. Sin embargo, hay que admitir que es un concepto difícil si intentamos estudiarlo sin ninguna ayuda externa.

Los decoradores no son otra cosa que **azúcar sintáctico**. En realidad solo son funciones que aceptan una función origen por parámetro. Cuando llamemos a la función origen, en realidad estaremos llamando a la funcíon que devolvió la función decorador.

Esto nos da varias posibilidades, como por ejemplo hacer cosas antes y después de declarar una función, o la posibilidad de suplantarla por completo, en vistas a añadir cosas a cada llamada, o a condicionar su ejecución. A continuación veremos algunos ejemplos:

## El decorador simple

Vemos un primer *script* hecho en *python*:

```python
#!/usr/bin/env python

def simple_decorator(func):
    print 'Decorating', func
    return func

@simple_decorator
def myfunc():
    print 'Hello world!'

myfunc()
myfunc()
```

La línea que empieza con `@` está **decorando** la función a la que precede. En este caso, `simple_decorator` es un decorador; esto es una función que acepta una función a la que decora.

El script mencionado arriba es exactamente el mismo que el siguiente, en donde la aplicación del decorador es explícita.

```python
#!/usr/bin/env python

def simple_decorator(func):
    print 'Decorating', func
    return func

def myfunc():
    print 'Hello world!'
myfunc = simple_decorator(myfunc)

myfunc()
myfunc()
```

Ejecutamos el *script* y vemos como se comporta:

```bash
gerard@atlantis:~/projects/decorators$ ./simple.py
Decorating <function myfunc at 0x7f3433328668>
Hello world!
Hello world!
gerard@atlantis:~/projects/decorators$
```

La función se decora una sola vez, en tiempo de declaración; ejecutar varias veces la función no hace repetir el código de la función decoradora. De la misma forma, una llamada a `myfunc()` ejecuta la misma función, porque es la función que devolvió el decorador.

## Decoradores parametrizados

El ejemplo anterior era solo un ejemplo. En el mundo real nos puede interesar tener un decorador que sea parametrizable, cambiando sus parámetros para adaptarse a las necesidades.

```python
#!/usr/bin/env python

def register_route(url):
    def wrapper(func):
        print 'Registering function', func, 'to', url
        return func
    return wrapper

@register_route('/')
def home_page():
    return 'home page'
# same as: home_page = register_route('/')(home_page)

@register_route('/admin')
def admin_panel():
    return 'admin panel'
# same as: admin_panel = register_route('/admin')(admin_panel)

print admin_panel()
print home_page()
print home_page()
```

Vemos que las funciones están decoradas por la misma función, pero esta viene parametrizada. No os dejéis engañar; la expresión entera es un decorador, haciendo que `register_route('/')` devuelva la función con la que vamos a decorar la función final.

El decorador en sí mismo es `wrapper`, pero en este caso tenemos la ventaja de que el decorador tiene visibilidad a las variables y parámetros de `register_route`, que tiene la obligación de devolver el decorador, que como ya sabemos es una función que acepta a otra por parámetro.

```bash
gerard@atlantis:~/projects/decorators$ ./parametrized.py
Registering function <function home_page at 0x7f2c07d79758> to /
Registering function <function admin_panel at 0x7f2c07d797d0> to /admin
admin panel
home page
home page
gerard@atlantis:~/projects/decorators$
```

Es interesante recalcar que las decoraciones se hacen en tiempo de declaración de la función, y luego podemos observar las llamadas que hacemos a las mismas. Otra observación es que el código del decorador ve, no solamente la función decorada `func`, sino también los parámetros de la funcion `register_route`.

Esta construcción es típica de algunos *frameworks* que usan esta misma forma para crear la tabla de rutas. El reactor del mismo *framework* va a ir llamando estas funciones según las peticiones lleguen. como ejemplo, podemos observar el caso del *framework* **bottle**:

```python
from bottle import Bottle

app = Bottle()

@app.get('/')
def index():
    return 'Hello world'
```

## Reemplazando la función decorada

Hacer cosas en tiempo de declaración de una función puede ayudarnos en muchas ocasiones, pero la verdadera potencia de los decoradores viene cuando podemos interceptar cada llamada a una función, sea para enriquecerla, o para reemplazarla total o parcialmente. Veamos un ejemplo de cada:

### Enriqueciendo una función

Este es un caso claro de *man-in-the-middle*. Queremos ejecutar una función que acabe llamando a la original, pero que haga algo más. En este ejemplo, queremos cronometrar nuestras funciones. Para ello hacemos el siguiente *script*:

```python
#!/usr/bin/env python

import time

def measure_time(func):
    def wrapper(*args, **kwargs):
        ini = time.time()
        func(*args, **kwargs)
        end = time.time()
        print 'Execution time:', end - ini, 'seconds'
    return wrapper

@measure_time
def myfunc():
    print 'Start'
    time.sleep(3)
    print 'End'

myfunc()
myfunc()
```

Con el decorador `measure_time`, conseguimos que `myfunc()` quede reemplazada por la función `wrapper()`, que va a guardar el valor inicial del cronómetro, va a llamar a nuestra función original, y finalmente va a escribir en pantalla la diferencia en el cronómetro.

Fijaos que el decorador `measure_time` no devuelve nunca la función original `func`; en cambio declara y devuelve otra que será la función suplantante. Nuevamente, esta función `wrapper` tiene visibilidad por los parámetros de decorador, concretamente de `func`, que nos interesa conocer porque es la función original a la que queremos llamar.

```bash
gerard@atlantis:~/projects/decorators$ ./count_time.py
Start
End
Execution time: 3.01089406013 seconds
Start
End
Execution time: 3.00343680382 seconds
gerard@atlantis:~/projects/decorators$
```

Haciendo dos llamadas podemos comprobar que la función `wrapper` es llamada cada vez que invocamos a `myfunc`.

### Reemplazando parcial o totalmente otra función

Hay situaciones en las que no interesa hacer el comportamiento habitual. Por ejemplo, podemos restringir ciertas funciones a usuarios validados en nuestra web, o limitarlos por cualquier otro criterio. Vamos a suponer que solo queremos que el usuario *root* pueda llegar a ejecutar una función:

```python
#!/usr/bin/env python

import os

def root_required(func):
    def wrapper(*args, **kwargs):
        if os.geteuid() != 0:
            print 'You need root access to do this'
        else:
            func(*args, **kwargs)
    return wrapper

@root_required
def myfunc():
    print 'Access granted'

myfunc()
```

Como en el caso anterior, la función original es reemplazada por `wrapper`; la diferencia es que en vez de enriquecerla, va a llamar a la función original solo si se cumple cierto criterio, que en este caso es ejecutar como *root*.

```bash
gerard@atlantis:~/projects/decorators$ ./no_access.py
You need root access to do this
gerard@atlantis:~/projects/decorators$ sudo ./no_access.py
Access granted
gerard@atlantis:~/projects/decorators$
```

Muchos *frameworks* web usan este truco para permitir ejecutar ciertas vistas a usuarios seleccionados.

## Parámetros y reemplazo de funciones a la vez

También es posible utilizar la técnica del reemplazo con un decorador parametrizado, aunque este caso se complica; solo hay que tener en cuenta que necesitamos 3 funciones:

* Una para los parámetros
* El decorador en sí mismo
* La funcion suplantante

Podemos hacer un decorador para cachear resultados varios segundos:

```python
#!/usr/bin/env python

import datetime
import time

def now():
    return datetime.datetime.now().strftime('%H:%M:%S')

cache_data = {}
def cache_result(seconds):
    def wrapper1(func):
        def wrapper2(n):
            aux = cache_data.get(n)
            if aux is not None and aux[0] + seconds >= time.time():
                return aux[1]
            else:
                result = func(n)
                cache_data[n] = (time.time(), result)
                return result
        return wrapper2
    return wrapper1

@cache_result(2)
def complex_math(n):
    time.sleep(3)
    return n + 1

for number in (3, 3, 5, 3):
    print now(), 'Started complex_math with n = %s' % number
    result = complex_math(number)
    print now(), 'Ended complex_math with n = %s with result = %s' % (number, result)
```

En este caso tenemos las 3 funciones citadas:

* La función parametrizada (`cache_result`)
* La función decoradora (`wrapper1`)
* La función suplantante (`wrapper2`)

Cada vez que llamemos a la función `complex_math`, en realidad vamos a estar llamando a la función `wrapper2`, que va a poder acceder a los parámetros de las otras 2, siendo `func` la función original decorada.

```bash
gerard@atlantis:~/projects/decorators$ ./big_math.py
13:32:45 Started complex_math with n = 3
13:32:48 Ended complex_math with n = 3 with result = 4
13:32:48 Started complex_math with n = 3
13:32:48 Ended complex_math with n = 3 with result = 4
13:32:48 Started complex_math with n = 5
13:32:51 Ended complex_math with n = 5 with result = 6
13:32:51 Started complex_math with n = 3
13:32:54 Ended complex_math with n = 3 with result = 4
gerard@atlantis:~/projects/decorators$
```

Solo queda verificar que el decorador hace realmente lo que deseábamos: *cachear* la primera llamada con `n = 3`, de forma que la segunda no tarda los 3 segundos de *delay*. La tercera con la misma entrada se recalcula porque el tiempo de *cache* se ha pasado mientras se hacía la llamanda con `n = 5`.

## Siendo correctos con la firma de la función

Cuando reemplazamos la función original por otra, no engañamos a nadie. Por ejemplo, en un caso simple como el siguiente:

```python
#!/usr/bin/env python

def decorator(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
    return wrapper

@decorator
def myfunc():
    pass

print myfunc.__name__
```

Toda ls información referente a la firma de la función sale de acuerdo a la nueva función.

```bash
gerard@atlantis:~/projects/decorators$ ./no_wrap.py
wrapper
gerard@atlantis:~/projects/decorators$
```

Este cambio de firma puede suponer un problema en algún momento futuro. Para eso, la librería estándar nos ofrece una forma de copiar la firma de la función a la función suplantante: un decorador llamado `wraps` en el paquete `functools`.

```python
#!/usr/bin/env python

import functools

def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
    return wrapper

@decorator
def myfunc():
    pass

print myfunc.__name__
```

Con este pequeño añadido nos evitamos el problema, ya que este se encarga de copiar el nombre de la función, los *docstrings*, la lista de argumentos y otras propiedades desde la función decorada a la función suplantante.

```bash
gerard@atlantis:~/projects/decorators$ ./wrap.py
myfunc
gerard@atlantis:~/projects/decorators$
```

Parece una tontería, pero puede evitarnos muchos problemas difíciles de diagnosticar en un futuro no muy lejano.
