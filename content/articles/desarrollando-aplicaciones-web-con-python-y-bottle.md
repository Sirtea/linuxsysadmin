Title: Desarrollando aplicaciones web con python y bottle
Slug: desarrollando-aplicaciones-web-con-python-y-bottle
Date: 2017-05-15 10:00
Category: Desarrollo
Tags: python, microframework, framework, bottle



Ya sabéis que me gusta mucho el lenguaje **python**. Muchos de mis ejemplos y algunas aplicaciones simples no merecen el uso de un *framework* tan grande como pueda ser **django**. Para estos casos me encantan los *microframeworks*, y aunque hay varias alternativas disponibles, me gusta especialmente un *microframework* llamado **bottle**.

Una de las mejores características de este *framework* es que no es complejo. Ponerse a hacer algo cuesta un tiempo de aprendizaje tendiendo a cero, y [la documentación](https://bottlepy.org/docs/dev/) es excelente. Solamente nos oculta la complejidad del protocolo **WSGI**.

Otro punto a favor es la sencillez y simplicidad. No tiene dependencias con ninguna base de datos, motor de plantillas (aunque lleva un motor de plantillas mínimo) o *middleware* externo. No añade nada que no tenga una especificación formal, y evita protocolos propios (por ejemplo, sesiones), en favor de especificaciones aceptadas (por ejemplo, *cookies*).

## Objetos y métodos básicos

* **Bottle**: Objeto principal del *framework*, es una forma de aglutinar el *callable wsgi* con un conjunto de rutas. Nuestra aplicación va a ser una instancia de este objeto.
* **request**: Objeto nos permite acceder a los datos referentes a la petición que nos han hecho. Incluye los parámetros GET, las *cookies* y cabeceras, entre otras cosas.
* **response**: Objeto que nos permite modificar nuestras repuestas, añadiendo cabeceras, códigos de estado, *cookies* y otros conceptos.
* **template**: Método que inyecta nuestro contexto a una plantilla y nos devuelve la respuesta ya formada, lista para devolverla.
* **view**: Lo mismo que el método **template**, pero en versión decorador.
* **redirect**: *Helper* que nos permite devolver una redirección a otra URL en nuestro código.
* **abort**: *Helper* que nos permite devolver estado de error desde nuestro controlador.

## Una aplicación vacía

Vamos a crear una carpeta para contener nuestro proyecto:

```bash
gerard@aldebaran:~/projects$ mkdir myapp
gerard@aldebaran:~/projects$ cd myapp/
gerard@aldebaran:~/projects/myapp$ 
```

Siguiendo las buenas prácticas, vamos a trabajar con **virtualenv**, que nos servirá para poner nuestras librerías, que de momento se limitan al *framework*. En adelante, es posible poner librerías para acceder a una base de datos, nuevos motores de plantillas y librerías más específicas.

```bash
gerard@aldebaran:~/projects/myapp$ virtualenv .venv
New python executable in /home/gerard/projects/myapp/.venv/bin/python
Installing setuptools, pip, wheel...done.
gerard@aldebaran:~/projects/myapp$ . .venv/bin/activate
(.venv) gerard@aldebaran:~/projects/myapp$ pip install bottle
Collecting bottle
Installing collected packages: bottle
Successfully installed bottle-0.12.13
(.venv) gerard@aldebaran:~/projects/myapp$ 
```

Como queremos poder reproducir nuestro entorno usaremos *pip freeze* para guardar las dependencias, en vista a poderlas instalar en un futuro entorno real.

```bash
(.venv) gerard@aldebaran:~/projects/myapp$ pip freeze > requirements.txt
(.venv) gerard@aldebaran:~/projects/myapp$ 
```

Lo mínimo para ejecutar una aplicación *WSGI compilant* es un servidor *WSGI* y la aplicación misma. Una aplicación construida con **bottle** es básicamente una instancia del objeto *Bottle*, a la que iremos registrando rutas. De momento la dejamos vacía, lo que nos va a responder siempre un error 404.

```bash
(.venv) gerard@aldebaran:~/projects/myapp$ cat app.py 
from bottle import Bottle

app = Bottle()
(.venv) gerard@aldebaran:~/projects/myapp$ 
```

En un entorno real, el servidor a usar sería otro, por ejemplo **apache**, **uwsgi** o **gunicorn**, pero para desarrollar, podemos aprovecharnos del servidor integrado.

```bash
(.venv) gerard@aldebaran:~/projects/myapp$ python -m bottle --debug --reload app:app
Bottle v0.12.13 server starting up (using WSGIRefServer())...
Listening on http://localhost:8080/
Hit Ctrl-C to quit.
```

Para nuestra comodidad futura, vamos a poner el comando en un *script*, en el que podemos definir nuestras propias variables de entorno o aquellas que queramos aplicar estando en nuestro entorno de desarrollo.

```bash
(.venv) gerard@aldebaran:~/projects/myapp$ cat server.sh 
#!/bin/bash

PYTHONDONTWRITEBYTECODE=" " \
python -m bottle --debug --reload app:app
(.venv) gerard@aldebaran:~/projects/myapp$ chmod a+x server.sh 
(.venv) gerard@aldebaran:~/projects/myapp$ ./server.sh 
Bottle v0.12.13 server starting up (using WSGIRefServer())...
Listening on http://localhost:8080/
Hit Ctrl-C to quit.
```

Y ya podemos dirigirnos a <http://localhost:8080/> para comprobar un bonito error 404.

## Registrando rutas a controladores

La idea es muy simple: se registran rutas a funciones que devuelven la respuesta resultado. Hay varias formas de añadir rutas a nuestra aplicación, pero la que más me gusta es el decorador.

```bash
(.venv) gerard@aldebaran:~/projects/myapp$ cat app.py 
from bottle import Bottle

app = Bottle()

@app.get('/')
def home():
    return '<h1>Home page</h1>'
(.venv) gerard@aldebaran:~/projects/myapp$ 
```

De esta forma, todas las peticiones GET a / van a devolver una página HTML con el contenido retornado. El código de retorno es un 200 y el *content-type* es *text/html* por defecto, aunque se puede cambiar con el objeto *response*.

## Usando plantillas y segmentos de URL

No es una buena práctica poner en el controlador la respuesta HTML. Para eso, **bottle** nos ofrece un motor de plantillas propio, y la facilidad de trabajar con otros. También nos permite capturar parte de la URL como parámetros; veamos un ejemplo:

```bash
(.venv) gerard@aldebaran:~/projects/myapp$ cat app.py 
from bottle import Bottle, view

app = Bottle()

@app.get('/')
def home():
    return '<h1>Home page</h1>'

@app.get('/hello/<name>')
@view('hello')
def hello(name):
    return {
        'nombre': name,
    }
(.venv) gerard@aldebaran:~/projects/myapp$ cat views/hello.tpl 
<p>Hola {{ nombre }}</p>
(.venv) gerard@aldebaran:~/projects/myapp$ 
```

En este caso, todo lo que siga a */hello/* en la URL se pasará a la función controlador, como una variable local *name*. Nuestra función devuelve un contexto, para que el decorador *view* pueda pintar la plantilla *hello*, que se encuentra en *views/hello.tpl*. Las variables disponibles para la plantilla son las claves del diccionario, que van a valer lo que pongamos como valores en el mismo diccionario.

En el caso de hacer una petición a */hello/gerard*, la variable local *name* va a valer "gerard" y la plantilla va a disponer de una variable *nombre* que vale también "gerard".

Algunas aplicaciones no necesitan plantillas HTML. Por ejemplo una API solo necesitaría convertir una expresión *python* en su equivalente JSON, mediante una función adecuada, que podemos ver como un motor de plantillas.

## Modelos y respuestas distintas

No hay ninguna capa de acceso a datos en **bottle**. Si se necesita acceder a datos, se debe usar alguna librería auxiliar; personalmente me encanta [mongoengine](http://mongoengine.org/) y [peewee](http://docs.peewee-orm.com/en/latest/). Otra opción es implementar un patrón [Data Access Object](https://es.wikipedia.org/wiki/Data_Access_Object).

Aún así, las buenas prácticas incitan a separar el modelo de los controladores, y eso lo podéis hacer fácilmente relegando las funciones u objetos de datos en un módulo aparte.

Vamos a hacer una ruta para devolver objetos en forma de API con JSON (REST, por supuesto). Así también podemos ver como indicar un *content-type* distinto.

```bash
(.venv) gerard@aldebaran:~/projects/myapp$ cat app.py 
from bottle import Bottle, view, abort, response
from json import dumps
from models import get_product

app = Bottle()

@app.get('/')
def home():
    return '<h1>Home page</h1>'

@app.get('/hello/<name>')
@view('hello')
def hello(name):
    return {
        'nombre': name,
    }

@app.get('/products/<id>')
def api_get_product(id):
    product = get_product(id)
    response.content_type = 'application/json'
    if product is not None:
        return dumps(product)
    response.status = 404
(.venv) gerard@aldebaran:~/projects/myapp$ cat models.py 
products = {
	'1': {
		'name': 'Apple',
		'price': 1.0,
	},
	'2': {
		'name': 'Orange',
		'price': 0.8,
	},
	'3': {
		'name': 'Pear',
		'price': 1.2,
	},
}

def get_product(id):
	product = products.get(id)
	if product is not None:
		return product.copy()
	return None
(.venv) gerard@aldebaran:~/projects/myapp$ 
```

Y con esto solo nos queda probar las respuestas:

```bash
gerard@aldebaran:~$ curl -i http://localhost:8080/products/1
HTTP/1.0 200 OK
...  
Content-Type: application/json

{"price": 1.0, "name": "Apple"}
gerard@aldebaran:~$ curl -i http://localhost:8080/products/2
HTTP/1.0 200 OK
...  
Content-Type: application/json

{"price": 0.8, "name": "Orange"}
gerard@aldebaran:~$ curl -i http://localhost:8080/products/22
HTTP/1.0 404 Not Found
...  
Content-Type: application/json

gerard@aldebaran:~$ 
```

## Conclusión

Siguiendo la documentación y usando librerías varias, se puede tener algo simple en muy poco tiempo. Dada la naturaleza del desarrollo web, los controladores se pueden ir añadiendo a medida que se necesiten. Eso nos da tiempo a descubrir las infinitas posibilidades de este *microframework*.

Algunas de las operaciones habituales (sesiones, capa de acceso a datos, autenticaciones varias, conectores a terceros, ...) no vienen. Aquellos con más vista de futuro probablemente vais a hacer código para evitar estos pequeños inconvenientes, pero si no lo queréis, *python* os ofrece muchas más soluciones para vuestro uso y disfrute. Los que disfrutáis con la belleza de lo simple, sed bienvenidos.
