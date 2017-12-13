Title: Usando extensiones en Flask
Slug: usando-extensiones-en-flask
Date: 2017-12-18 10:00
Category: Desarrollo
Tags: python, framework, microframework, flask, extensiones
Series: Flask framework



Muchos de los *microframeworks* que existen en **python** no ofrecen ninguna ayuda con las tareas más simples que toda aplicación acaba implementando; eso nos hace decantarnos casi siempre por una opción más pesada de *framework*, como por ejemplo, **Django**. Sin embargo, gracias a los **blueprints** de **Flask**, esto es innecesario.

Ya vimos en [otro artículo]({filename}/articles/creciendo-con-flask-los-blueprints.md) que este *framework* tiene una funcionalidad llamada **blueprints**, que nos permiten encapsular un subconjunto de rutas, vistas y contenido estático para mantenibilidad y para su uso en otros proyectos.

Este mismo modelo de desarrollo ha permitido que muchas personas desarrollen sus **blueprints** reusables y, en alguno de los casos, ofrecerlos a cualquiera que los pueda necesitar. Son especialmente interesantes las extensiones oficiales que se ofrecen con **Flask**, que podemos encontrar en [la página de extensiones](http://flask.pocoo.org/extensions/).

Hay una lista interesante de extensiones, tanto en la página oficial, como por otros lugares de internet; cualquiera puede ofrecer extensiones. A pesar de ello, hay extensiones de plena confianza que van a servir de base para casi cualquier proyecto que deseemos empezar.

En mi caso, mis favoritas son **flask-mongoengine** y **flask-admin** y suelen ser motivo suficiente para empezar cada nuevo proyecto en **Flask**. Vamos a intentar introducir el uso de extensiones con estos dos ejemplos.

## Un proyecto vacío

Todas las modificaciones que se van a ir haciendo, se basan en una aplicación básica vacía. Siguiendo nuestra metodología, vamos a utilizar *virtualenv*, vamos recoger las dependencias en un fichero *requirements.txt* y vamos a disponer de un servidor de desarrollo.

```bash
(.venv) gerard@atlantis:~/projects/flask-extensions$ cat requirements.txt
Flask==0.12.2
Flask-Admin==1.5.0
flask-mongoengine==0.9.3
(.venv) gerard@atlantis:~/projects/flask-extensions$
```

```bash
(.venv) gerard@atlantis:~/projects/flask-extensions$ cat server.sh
#!/bin/bash

PYTHONDONTWRITEBYTECODE=" " \
FLASK_DEBUG=1 \
FLASK_APP=app.py \
MONGODB_URL='mongodb://localhost:27017/test' \
SECRET_KEY='1234567890' \
flask run --host 0.0.0.0 --port 8080
(.venv) gerard@atlantis:~/projects/flask-extensions$
```

```bash
(.venv) gerard@atlantis:~/projects/flask-extensions$ cat app.py
from flask import Flask

app = Flask(__name__)
(.venv) gerard@atlantis:~/projects/flask-extensions$
```

Sobra decir que tenemos un servidor de **mongodb** en alguna parte, dispuesto a ser utilizado por nuestra capa de datos. En este caso concreto, el servidor corre en local.

## Definiendo el modelo con flask-mongoengine

Esta extensión no añade demasiado valor en sí misma, pero se integra magníficamente con **Flask**. En esencia se trata de un **blueprint** que utiliza la misma configuración que nuestra aplicación y se conecta al servidor de acuerdo a esta configuración.

Vamos a definir nuestros modelos como lo haríamos en **mongoengine**, salvo que los tipos declarados en **mongoengine** también lo están dentro del **blueprint** que hemos creado. Con un modelo pequeño de demostración nos vale:

```bash
(.venv) gerard@atlantis:~/projects/flask-extensions$ cat models.py
from flask_mongoengine import MongoEngine

db = MongoEngine()


class User(db.Document):
    username = db.StringField()
    password = db.StringField()
    fullname = db.StringField()
    meta = {'collection': 'users'}


class Product(db.Document):
    sku = db.StringField()
    title = db.StringField()
    description = db.StringField()
    meta = {'collection': 'products'}
(.venv) gerard@atlantis:~/projects/flask-extensions$
```

Vamos a recurrir a la clase principal (que es la que declara el objeto *app*) y vamos a importar el **blueprint**, para registrarlo posteriormente. Como añadido, vamos a sacar la URL de **mongodb** de una variable de entorno, porque la idea es usar esta aplicación en un contenedor en el futuro; de momento, esta variable queda declarada en el fichero *server.sh*.

```bash
(.venv) gerard@atlantis:~/projects/flask-extensions$ cat app.py
from flask import Flask
from models import db
import os

MONGODB_URL = os.environ.get('MONGODB_URL')

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {'host': MONGODB_URL}
db.init_app(app)
(.venv) gerard@atlantis:~/projects/flask-extensions$
```

Los modelos definidos con **flask-mongoengine** disponen de un *QuerySet* modificado, que nos permitirá hacer paginación o lanzar automáticamente un error 404 si no se encuentra un elemento, pero eso ya queda como deberes para el lector.

## Una interfaz de administración gratuita con flask-admin

Esta extensión trabaja más que la anterior, pero en cierta manera, depende de ella. Se trata de un **blueprint** que crea un interfaz de administración en base a los modelos y de unas clases *ModelView* que son capaces de analizar los mismos y crear automáticamente las listas y formularios necesarios.

La idea es la misma: creamos el **blueprint** y registramos el objeto *ModelView* para cada objeto que deseemos en el panel de administración. El objeto básico *ModelView* suele ser suficiente para la mayoría de casos, pero en otros vamos a querer personalizar lo que se ve, lo que se puede hacer, y los filtros disponibles.

Esto lo dejamos para el lector, y nos vamos a centrar en como se haría. Para ello, imaginemos que queremos ocultar el campo *password* en la gestión de usuarios:

```bash
(.venv) gerard@atlantis:~/projects/flask-extensions$ cat models.py
from flask_mongoengine import MongoEngine

db = MongoEngine()


class User(db.Document):
    username = db.StringField()
    password = db.StringField()
    fullname = db.StringField()
    meta = {'collection': 'users'}


class Product(db.Document):
    sku = db.StringField()
    title = db.StringField()
    description = db.StringField()
    meta = {'collection': 'products'}
(.venv) gerard@atlantis:~/projects/flask-extensions$ cat admin.py
from flask_admin import Admin
from flask_admin.contrib.mongoengine import ModelView
from models import User, Product


class HidePasswordModelView(ModelView):
    column_exclude_list = ('password',)

admin = Admin()
admin.add_view(HidePasswordModelView(User))
admin.add_view(ModelView(Product))
(.venv) gerard@atlantis:~/projects/flask-extensions$
```

Solo queda importar el **blueprint** y registrarlo en nuestra aplicación; esto se consigue en el fichero *app.py*. Cabe decir que esta extensión requiere de una configuración `SECRET_KEY` para encriptar las *cookies* de **Flask**.

```bash
(.venv) gerard@atlantis:~/projects/flask-extensions$ cat app.py
from flask import Flask
from models import db
from admin import admin
import os

SECRET_KEY = os.environ.get('SECRET_KEY')
MONGODB_URL = os.environ.get('MONGODB_URL')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['MONGODB_SETTINGS'] = {'host': MONGODB_URL}
db.init_app(app)
admin.init_app(app)
(.venv) gerard@atlantis:~/projects/flask-extensions$
```

Y sin especificar ningún parámetro extra, nuestro panel de administración se va a encontrar por defecto en <http://localhost:8080/admin/>. Esto se puede modificar al registrar el **blueprint**.

**WARNING**: El panel de administración solo sirve para administrar. No tiene autenticación integrada y queda como responsabilidad del usuario decidir que hacer. Se puede desactivar antes de ir a producción, se puede limitar el acceso mediante autenticación básica o certificados, e incluso se puede poner una extensión de autenticación como **flask-login** o **flask-auth**.

## En resumen

Con esto tenemos un interesante esqueleto sobre el que crear en un tiempo mínimo cualquier aplicación que nos propongamos. Para acelerar la inicialización de un nuevo proyecto, he creado esta base como un repositorio de **GitHub**, que podéis clonar en <https://github.com/Sirtea/flask-skel>.
