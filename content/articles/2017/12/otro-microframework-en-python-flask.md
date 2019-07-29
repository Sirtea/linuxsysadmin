---
title: "Otro microframework en python: Flask"
slug: "otro-microframework-en-python-flask"
date: 2017-12-04
categories: ['Desarrollo']
tags: ['python', 'framework', 'microframework', 'flask']
series: "Flask framework"
---

Cuando queremos hacer una nueva aplicación web podemos usar un *framework* completo como **django** o uno minimalista como **bottle**. Entre ambos existe una amplia variedad de *frameworks* que nos pueden aportar variedad y algunas de las funcionalidades más demandadas. En esta categoria podemos encontrar un *microframework* muy interesante llamado **Flask**.<!--more-->

De hecho, este *framework* es enormemente similar a [otro que ya vimos]({{< relref "/articles/2017/05/desarrollando-aplicaciones-web-con-python-y-bottle.md" >}}). Lo único que impide que ambos *frameworks* se fusionen es un choque ideológico entre ambos autores, y su forma de afrontar la distribución del código fuente; mientras que el autor de **bottle** mantiene la idea del fichero único, el de **flask** cree firmemente en la necesidad de separar las capas dependiendo de su función.

De esta forma, **flask** es solo la unión de 3 grandes librerías del mismo autor:

* **flask**: una librería que funciona como pegamento entre todas las demás
* **werkzeug**: posiblemente la mejor librería para tratar con el protocolo **WSGI**
* **jinja2**: el mejor motor de plantillas existente para **python**, muy parecido al de **django**

Este *framework* no trabaja con ninguna capa de datos, dándonos la libertad para elegir la que más nos guste, y dándonos libertad para usar cualquier servicio de datos, sea SQL, NoSQL, u otros, incluso ninguno.

Sin embargo, lo que realmente hace grande a este *framework* son los **blueprints**, que lo hacen extensible hasta límites insospechados, pero eso lo vermos más adelante. No nos olvidemos de mencionar la [magnífica documentación](http://flask.pocoo.org/docs/) y estaremos trasteando con el *framework* en menos de 2 horas.

Y si he conseguido picar tu curiosidad, te recomiendo encarecidamente leerte el libre *online* [Explore Flask](https://exploreflask.com/en/latest/) que es muy interesante y algo más completo que este artículo.

## Objetos y métodos básicos

* **Flask**: Objeto principal del *framework*, es una forma de aglutinar el *callable wsgi* con un conjunto de rutas. Nuestra aplicación va a ser una instancia de este objeto.
* **request**: Objeto que nos permite acceder a los datos referentes a la petición que nos han hecho. Incluye los parámetros GET, las cookies y cabeceras, entre otras cosas.
* **response**: Objeto que nos permite modificar nuestras respuestas, añadiendo cabeceras, códigos de estado, cookies y otros conceptos.
* **render_template**: Método que inyecta nuestro contexto a una plantilla y nos devuelve la respuesta ya formada, lista para devolverla.
* **redirect**: Helper que nos permite devolver una redirección a otra URL en nuestro código.
* **abort**: Helper que nos permite devolver estado de error desde nuestro controlador.

## Una aplicación vacía

Vamos a crear una carpeta para contener nuestro proyecto:

```bash
gerard@atlantis:~/projects$ mkdir myapp
gerard@atlantis:~/projects$ cd myapp/
gerard@atlantis:~/projects/myapp$
```

Siguiendo las buenas prácticas, vamos a trabajar con virtualenv, que nos servirá para poner nuestras librerías, que de momento se limitan al *framework*. En adelante, es posible poner librerías para acceder a una base de datos, nuevos motores de plantillas y librerías más específicas.

```bash
gerard@atlantis:~/projects/myapp$ virtualenv .venv
New python executable in /home/gerard/projects/myapp/.venv/bin/python
Installing setuptools, pip, wheel...done.
gerard@atlantis:~/projects/myapp$ . .venv/bin/activate
(.venv) gerard@atlantis:~/projects/myapp$ pip install flask
...
Installing collected packages: itsdangerous, click, Werkzeug, MarkupSafe, Jinja2, flask
Successfully installed Jinja2-2.9.6 MarkupSafe-1.0 Werkzeug-0.12.2 click-6.7 flask-0.12.2 itsdangerous-0.24
(.venv) gerard@atlantis:~/projects/myapp$
```

Como queremos poder reproducir nuestro entorno usaremos pip freeze para guardar las dependencias, en vista a poderlas instalar en un futuro entorno real.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ pip freeze > requirements.txt
(.venv) gerard@atlantis:~/projects/myapp$
```

Lo mínimo para ejecutar una aplicación *WSGI compilant* es un servidor WSGI y la aplicación misma. Una aplicación construida con **flask** es básicamente una instancia del objeto *Flask*, a la que iremos registrando rutas. De momento la dejamos vacía, lo que nos va a responder siempre un error 404.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ cat app.py
from flask import Flask

app = Flask(__name__)
(.venv) gerard@atlantis:~/projects/myapp$
```

En un entorno real, el servidor a usar sería otro, por ejemplo **apache**, **uwsgi** o **gunicorn**, pero para desarrollar, podemos aprovecharnos del servidor integrado.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ FLASK_DEBUG=1 FLASK_APP=app.py flask run
 * Serving Flask app "app"
 * Forcing debug mode on
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 579-205-006
```

Para nuestra comodidad futura, vamos a poner el comando en un script, en el que podemos definir nuestras propias variables de entorno o aquellas que queramos aplicar estando en nuestro entorno de desarrollo.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ cat server.sh
#!/bin/bash

PYTHONDONTWRITEBYTECODE=" " \
FLASK_DEBUG=1 \
FLASK_APP=app.py \
flask run --host 0.0.0.0 --port 8080
(.venv) gerard@atlantis:~/projects/myapp$ chmod 755 server.sh
(.venv) gerard@atlantis:~/projects/myapp$ ./server.sh
 * Serving Flask app "app"
 * Forcing debug mode on
 * Running on http://0.0.0.0:8080/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 579-205-006
```

Y ya podemos dirigirnos a http://localhost:8080/ para comprobar un bonito error 404.

## Registrando rutas a controladores

La idea es muy simple: se registran rutas a funciones que devuelven la respuesta resultado. Hay varias formas de añadir rutas a nuestra aplicación, pero la que más me gusta es el decorador.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ cat app.py
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Home page</h1>'
(.venv) gerard@atlantis:~/projects/myapp$
```

De esta forma, todas las peticiones GET a / van a devolver una página HTML con el contenido retornado. El código de retorno es un 200 y el *content-type* es *text/html* por defecto, aunque se puede cambiar con el objeto *response*.

## Usando plantillas y segmentos de URL

No es una buena práctica poner en el controlador la respuesta HTML. Para eso, **flask** nos ofrece el motor de plantillas **jinja2**. También nos permite capturar parte de la URL como parámetros; veamos un ejemplo:

```bash
(.venv) gerard@atlantis:~/projects/myapp$ cat app.py
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1>Home page</h1>'

@app.route('/hello/<name>')
def hello(name):
    data = {
        'nombre': name,
    }
    return render_template('hello.html', **data)
(.venv) gerard@atlantis:~/projects/myapp$ cat templates/hello.html
<p>Hola {{ nombre }}</p>
(.venv) gerard@atlantis:~/projects/myapp$
```

Y de esta forma, todas las URLs de la forma */hello/nombre* capturará el segmento como *name* y lo va a pasar a la funcion *render_template* que hará lo que tenga que hacer con ella, que en este caso es pintarla.

Algunas aplicaciones no necesitan plantillas HTML. Por ejemplo una API solo necesitaría convertir una expresión python en su equivalente JSON, mediante una función adecuada, que podemos ver como un motor de plantillas.

## Blueprints

Las aplicaciones web tienden a crecer mucho, especialmente si planificamos funcionalidades de acuerdo a algún método ágil. En estos casos podemos contar con los **blueprints**.

Básicamente, un **blueprint** es una manera de organizar tu aplicación en trozos, más pequeños y reusables. Como toda otra aplicación **Flask**, es una colección de vistas, plantillas y otros elementos estáticos. A pesar de esto, un **blueprint** no es una aplicación en sí misma, y debe ser registrado en una aplicación de verdad antes de que se pueda usar.

La razón principal por la que deberíamos utilizar **blueprints** es la de desacoplar nuestra aplicación en componentes más pequeños y reusables, encargándose cada uno de uno solo de los aspectos de la aplicación. Esto los hace mantenibles y más fáciles de *debuguear*.

En la práctica, los **blueprints** han derivado en *extensiones* genéricas que nos permiten trabajar con módulos preparados para sacarnos el trabajo duro de encima. Mis favoritos son **Flask-Admin** y **Flask-Mongoengine**, pero eso queda para otro artículo.
