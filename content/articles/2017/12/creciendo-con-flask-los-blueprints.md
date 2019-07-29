---
title: "Creciendo con Flask: los blueprints"
slug: "creciendo-con-flask-los-blueprints"
date: 2017-12-11
categories: ['Desarrollo']
tags: ['python', 'framework', 'microframework', 'flask', 'blueprints']
---

Ya estuvimos hablando del *microframework* **Flask**, pero no profundizamos en su funcionalidad más avanzada: los **blueprints**, que son una agrupación de vistas, plantillas y contenido estático similar a las aplicaciones de **django**. Solamente por esta funcionalidad queda justificado el uso de este *framework* para proyectos de tamaños medio o grande.<!--more-->

Lo primero que tenemos que ver es la necesidad de utilizar **blueprints**. A medida que nuestra aplicación crece, el código lo hace también. Esto suele hacer código fuente grande e inmantenible. Invariablemente, veremos que nuestra aplicación es una amalgama de partes.

En este momento, nos va a interesar trocear en partes aquel fichero con todas nuestras vistas. Y la herramienta para hacer esto son los **blueprints**, ya sea para partir la aplicación *a posteriori* o queremos empezar haciéndolo bien desde el principio.

## Divide y vencerás

Os pongo un pequeño ejemplo, con este programa de gestión de hoteles:

![Programa modular](/images/programa_modular.gif)

¿Verdad que parece grande y descorazonador? **¡Divide y vencerás!**

Si lo troceamos adecuadamente, tenemos varios problemas menores, e incluso podemos poner a trabajar en ellos a un equipo grande, por separado. Incluso podemos añadir más módulos en un futuro; quien sabe, incluso podemos hacerlo genérico suficiente para que los hoteles activen solamente las partes que más falta les hagan.

Ese es el modelo de negocio de SAP...

## Un caso de uso de ejemplo

Supongamos que una empresa nos paga para hacer una web corporativa, con, de momento, las siguientes opciones:

* Una página principal para actuar como su *landing page*
* Algunas páginas menores, como por ejemplo el apartado legal o la presentación de la empresa, con contenido fijo
* Un boletín informativo con sus últimas noticias, a modo de rueda de prensa y con una maquetación diferente

Y cual es nuestra estratégia? **¡Divide y vencerás!**

Hagamos nuestra aplicación, a base de estas mismas 3 partes:

* Una vista normal para la *landing page*
* Un **blueprint** para las páginas menores
* Un **blueprint** para las noticias

## Implementación

Vamos a empezar con una aplicación vacía, solo con la página principal. A partir de ahí vamos a registrar las páginas menores y, finalmente, el módulo de notícias.

Para simplificar, no vamos a gestionar la capa de persistencia ni un panel de administración; esto queda como ejercicio al lector. Si os interesa mucho, y como veremos en un artículo posterior, podemos utilizar un **blueprint** prefabricado para ello.

### La página principal

Vamos a evitar el uso de **blueprints**, solo para demostrar que es posible mezclar vistas normales con **blueprints**. No hay ningún misterio en esto: una vista, una plantilla y un estilo.

Así quedaría nuestro proyecto con el primero de los puntos solucionados:

```bash
(.venv) gerard@atlantis:~/projects/myapp$ tree
.
├── static
│   └── style.css
├── templates
│   ├── layout.html
│   └── main.html
├── app.py
├── requirements.txt
└── server.sh

2 directories, 6 files
(.venv) gerard@atlantis:~/projects/myapp$
```

La vista solo renderiza la plantilla que nos interesa, aunque hay la complejidad añadida de que utiliza herencia.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ cat app.py
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def main_page():
    return render_template('main.html')
(.venv) gerard@atlantis:~/projects/myapp$
```

Finalmente tenemos las plantillas y algún *asset* estático.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ cat templates/layout.html
<!DOCTYPE html>
<html lang="es">
<head>
    <link rel="stylesheet" href="/static/style.css" />
</head>
<body>
{% block content %}{% endblock %}
</body>
</html>
(.venv) gerard@atlantis:~/projects/myapp$ cat templates/main.html
{% extends "layout.html" %}

{% block content %}
    <h1>Main page</h1>
{% endblock %}
(.venv) gerard@atlantis:~/projects/myapp$ cat static/style.css
html { background-color: cyan }
(.venv) gerard@atlantis:~/projects/myapp$
```

### Las páginas secundarias

Vamos a crear una carpeta para contener los recursos del **blueprint**. Como el **blueprint** debe ser importado y registrado por la aplicación, vamos a convertirlo en un módulo de **python** añadiendo un fichero *\_\_init\_\_.py*, que de paso servirá para contener el código del **blueprint**.

Nótese la aparición de la nueva carpeta *pages/*:

```bash
(.venv) gerard@atlantis:~/projects/myapp$ tree
.
├── pages
│   ├── templates
│   │   ├── about.html
│   │   └── legal.html
│   └── __init__.py
├── static
│   └── style.css
├── templates
│   ├── layout.html
│   └── main.html
├── app.py
├── requirements.txt
└── server.sh

4 directories, 9 files
(.venv) gerard@atlantis:~/projects/myapp$
```

El funcionamiento es el mismo: regitramos vistas que renderizan plantillas y poco más. La parte interesante es que estas vistas se encapsulan en un objeto *Blueprint* que luego será registrado en la aplicación base.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ cat pages/__init__.py
from flask import Blueprint, render_template

pages = Blueprint('pages', __name__, template_folder='templates')

@pages.route('/about')
def about_page():
    return render_template('about.html')

@pages.route('/legal')
def legal_page():
    return render_template('legal.html')
(.venv) gerard@atlantis:~/projects/myapp$ cat pages/templates/about.html
{% extends "layout.html" %}

{% block content %}
    <h1>About page</h1>
{% endblock %}
(.venv) gerard@atlantis:~/projects/myapp$ cat pages/templates/legal.html
{% extends "layout.html" %}

{% block content %}
    <h1>Legal page</h1>
{% endblock %}
(.venv) gerard@atlantis:~/projects/myapp$
```

Con esto tenemos el **blueprint**, que va a haber que registrar en nuestra aplicación para que esta añada sus rutas a una ruta base, que en este caso, no está declarada. Esto hará que se registren en */*.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ cat app.py
from flask import Flask, render_template
from pages import pages

app = Flask(__name__)

@app.route('/')
def main_page():
    return render_template('main.html')

app.register_blueprint(pages)
(.venv) gerard@atlantis:~/projects/myapp$
```

De esta forma tendremos dos nuevas URLs en la aplicación:

* `http://localhost:8080/about`
* `http://localhost:8080/legal`

Es interesante ver que hay dos nuevas plantillas en el **blueprint**, pero la plantilla base y la hoja de estilos siguen siendo las de la aplicación principal. Los ficheros del **blueprint** tienen preferencia sobre el resto, pero no los eclipsan; los anteriores quedan disponibles por si no se sobreescribieran.

### El módulo de notícias

Este módulo es prácticamente igual al anterior, con dos sutiles diferencias:

* Usaremos otra plantilla base y otra hoja de estilos
* Nuestras rutas van a ir prefijadas por */news/*

La primera parte es tan simple como poner los nuevos ficheros para que no utilice los originales como plan B. La segunda se consigue declarando las rutas sin el prefijo y montando el **blueprint** con un prefijo en la aplicación original. Esto nos da cierta capacidad de recolocar un conjunto de URLs.

De nuevo, hacemos aparecer una carpeta nueva. Como las dos carpetas *templates/* se "fusionan" a ojos del cargador, me he visto obligado a esconder el segundo *layout.html* en una carpeta, para evitar colisiones de nombres.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ tree
.
├── news
│   ├── static
│   │   └── style.css
│   ├── templates
│   │   └── news
│   │       ├── latest.html
│   │       └── layout.html
│   └── __init__.py
├── pages
│   ├── templates
│   │   ├── about.html
│   │   └── legal.html
│   └── __init__.py
├── static
│   └── style.css
├── templates
│   ├── layout.html
│   └── main.html
├── app.py
├── requirements.txt
└── server.sh

8 directories, 13 files
(.venv) gerard@atlantis:~/projects/myapp$
```

La aplicación ya es repetitiva; se pone solamente por tener el ejemplo completo. Es importante ver que se ha utilizado el *helper* **url_for** para no calcular el *path* del fichero de estilos. Pido perdón por la chapuza de no usar una base de datos, y poner las noticias en el código.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ cat news/__init__.py
from flask import Blueprint, render_template

news = Blueprint('news', __name__, template_folder='templates', static_folder='static')

@news.route('/latest')
def latest_news():
    data = {
        'news': ['lorem', 'ipsum'],
    }
    return render_template('news/latest.html', **data)
(.venv) gerard@atlantis:~/projects/myapp$ cat news/templates/news/layout.html
<!DOCTYPE html>
<html lang="es">
<head>
    <link rel="stylesheet" href="{{ url_for('.static', filename='style.css') }}" />
</head>
<body>
{% block content %}{% endblock %}
<p><small>News app</small></p>
</body>
</html>
(.venv) gerard@atlantis:~/projects/myapp$ cat news/templates/news/latest.html
{% extends "news/layout.html" %}

{% block content %}
    <h1>Latest news</h1>
    <ul>
{% for new in news %}
        <li>{{ new }}</li>
{% endfor %}
    </ul>
{% endblock %}
(.venv) gerard@atlantis:~/projects/myapp$ cat news/static/style.css
html { background-color: red }
(.venv) gerard@atlantis:~/projects/myapp$
```

El punto interesante es que quremos mapear el **blueprint**. Eso significa que la URL */latest* del **blueprint** tiene que utilizar un prefijo, para que lo veamos en */news/latest*. Es ahora, en el momento de registrar el **blueprint**, cuando podemos especificar que todas sus URLs cuelguen de un prefijo adicional.

```bash
(.venv) gerard@atlantis:~/projects/myapp$ cat app.py
from flask import Flask, render_template
from pages import pages
from news import news

app = Flask(__name__)

@app.route('/')
def main_page():
    return render_template('main.html')

app.register_blueprint(pages)
app.register_blueprint(news, url_prefix='/news')
(.venv) gerard@atlantis:~/projects/myapp$
```

## Reflexiones

¿Os habéis fijado lo fácil que seria adoptar el módulo de noticias para otra aplicación?

Solo necesitamos tener un repositorio de **blueprints** listo para ser usado en proyectos nuevos. Si se piensan bien nuestros **blueprints** serán **reusables**. Algunos de ellos incluso se podrían convertir en **extensiones**, pero eso es otra historia.
