Title: Un ODM para mongodb en python: mongoengine
Slug: un-odm-para-mongodb-en-python-mongoengine
Date: 2017-11-27 10:00
Category: Desarrollo
Tags: python, mongodb, mongoengine, odm



Aquellos que hemos usado **mongodb** desde **python**, ya conocemos las virtudes de **pymongo**. Sin embargo, este lenguaje es orientado a objetos, y trabajar con ellos hace nuestro código más simple y más legible. **Mongoengine** es un ODM, una librería que se encarga de convertir objetos en documentos **mongodb** y viceversa.

ODM son las siglas para *object to document mapper*, y es el equivalente a un ORM (*object to relational mapper*). La diferencia entre ambos conceptos es que los datos van a parar a la base de datos como un documento en contraposición a una base de datos relacional.

El objetivo de la librería es convertir nuestros modelos en objetos de **python** de forma declarativa. Toda la magia del acceso a la base de datos se hace de forma automática.

Este ODM está realmente bien hecho; soporta tipos de campos, herencia de clases, referencias a otros documentos e incluso listas en sus campos. Todo ello creando los índices necesarios para los accesos habituales, y la posibilidad de declarar otros índices que creamos necesarios.

## Declaración de los modelos

Veamos un ejemplo, con un subconjunto de los datos de un *blog* estándar. Para ello, el primer paso es declarar nuestros modelos:

```bash
(.venv) gerard@sirius:~/projects/mongoengine$ cat models.py 
import mongoengine


def connect(url):
    mongoengine.connect(host=url)


class Author(mongoengine.Document):
    name = mongoengine.StringField()
    meta = {'collection': 'authors'}


class Page(mongoengine.Document):
    title = mongoengine.StringField()
    content = mongoengine.StringField()
    meta = {'collection': 'pages', 'allow_inheritance': True}


class Post(Page):
    author = mongoengine.ReferenceField(
        'Author',
        reverse_delete_rule=mongoengine.CASCADE
    )
    date = mongoengine.DateTimeField()
    tags = mongoengine.ListField(mongoengine.StringField())
(.venv) gerard@sirius:~/projects/mongoengine$ 
```

Habéis visto algunas de las funcionalidades más interesantes?

* Subclases mediante terminología **python** habitual.
* Varios tipos de datos para los campos.
* Referencias a otros objetos que se cargan de forma *lazy*, es decir, cuando se accede al campo se lanza una nueva consulta.
* Reglas de tratamiento automático de referencias para objetos eliminados.
* Campos tipo lista, con tipología de los elementos de la misma. En el ejemplo son campos tipo `StringField` pero podrían ser cualquiera, como por ejemplo `ReferenceField`.

## Uso de nuestros modelos

Para crear nuestros objetos, basta hacerlo como se haría en **python** normal. Solo hay que tener en cuenta que los cambios no acabarán en la base de datos hasta que invoquemos el método `save` del objeto tipo `Document`.

```bash
(.venv) gerard@sirius:~/projects/mongoengine$ cat carga.py 
#!/usr/bin/env python

from models import Author, Page, Post, connect
from datetime import datetime

connect('mongodb://localhost:27017/test')

Page(title='About', content='blah').save()
a = Author(name='Gerard').save()
Post(title='Hello world', content='lorem ipsum', author=a,
     date=datetime.utcnow(), tags=['hello', 'world']).save()
(.venv) gerard@sirius:~/projects/mongoengine$ ./carga.py 
(.venv) gerard@sirius:~/projects/mongoengine$ 
```

Y el resultado es un esquema de base de datos bastante limpio, y sin ningún tipo de *overhead*. Solo hay que cargar con un campo adicional para diferenciar el tipo de objeto en el caso de herencia.

```bash
> use test
switched to db test
> show collections
authors
pages
> db.authors.find().pretty()
{ "_id" : ObjectId("59b1a4bb093f961b0aa6ed00"), "name" : "Gerard" }
> db.pages.find().pretty()
{
	"_id" : ObjectId("59b1a4bb093f961b0aa6ecff"),
	"_cls" : "Page",
	"title" : "About",
	"content" : "blah"
}
{
	"_id" : ObjectId("59b1a4bc093f961b0aa6ed01"),
	"_cls" : "Page.Post",
	"title" : "Hello world",
	"content" : "lorem ipsum",
	"author" : ObjectId("59b1a4bb093f961b0aa6ed00"),
	"date" : ISODate("2017-09-07T19:57:47.993Z"),
	"tags" : [
		"hello",
		"world"
	]
}
> 
```

Consultar los objetos de la base de datos requiere encontrarlos primero, con el método `Document.objects`. Esto nos puede traer un cursor de objetos o podemos invocar el método `first` para traer uno solo.

```bash
(.venv) gerard@sirius:~/projects/mongoengine$ cat consulta.py 
#!/usr/bin/env python

from models import Author, Post, connect

connect('mongodb://localhost:27017/test')

a = Author.objects(name='Gerard').first()
print 'Author:', a.name
for post in Post.objects(author=a):
    print '* Post:', post.title
    print '  Tags:', ', '.join(post.tags)
(.venv) gerard@sirius:~/projects/mongoengine$ 
```

Podemos ver que buscamos un autor por su nombre, asumiendo que el primero nos vale. Una vez tenemos el autor podemos encontrar sus posts y escribir algunos datos en la salida estándar.

Ejecutamos y vemos que el resultado es el esperado:

```bash
(.venv) gerard@sirius:~/projects/mongoengine$ ./consulta.py 
Author: Gerard
* Post: Hello world
  Tags: hello, world
(.venv) gerard@sirius:~/projects/mongoengine$ 
```

Para modificar los objetos, tenemos que consultarlos, modificar el objeto e invocar de nuevo el método `save`. De la misma manera, para borrarlo necesitamos el objeto en **python** e invocar a continuación el método `delete`.

## Conclusión

Sin duda esta librería es una gran ayuda para hacer un gran desarrollo. Estoy seguro que va a servirme para mi siguiente proyecto personal.

Hay muchas más cosas que se pueden hacer con este ODM; simplemente tenemos que ahondar en [la documentación](http://docs.mongoengine.org/apireference.html).
