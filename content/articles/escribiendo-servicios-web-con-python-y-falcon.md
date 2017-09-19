Title: Escribiendo servicios web con python y falcon
Slug: escribiendo-servicios-web-con-python-y-falcon
Date: 2017-09-19 17:00
Category: Desarrollo
Tags: falcon, REST, microframework, framework, python



El otro día me vi leyendo artículos sobre arquitecturas basadas en servicios web, especialmente centrados en patrones REST y codificados en JSON. No es la primera vez que hago algo con *frameworks* no específicos, pero tras buscar un poco por internet, descubrí un *framework* específico para servicios REST llamado **falcon**.

Se trata de u *microframework* de diseño simplista, ligero, rápido y sin ninguna magia. Eso nos lleva al punto que me enamoró: no toma ninguna decisión y no obliga a usar ninguna capa de persistencia ni ningún motor de plantillas o serializado.

Desde el punto de vista de rendimiento, está pensado para volar; no incluye nada que no sea específico de servicios web y sabe sacar provecho del *hardware* moderno, permitiendo miles de peticiones por segundo en un *hardware* modesto.

## Una aplicación básica

De forma similar a otros *frameworks* **python**, nuestra API es una instancia de un objeto que se dedica a despachar rutas a controladores (aunque aquí los llaman *resources*).

A diferencia de otros *frameworks*, sin embargo, el registro de *resources* a rutas es explícita, invocando el método `add_route` en el objeto API, que es la aplicación que debemos servir.

Los *resources* registrados en las rutas son simplemente objetos que definen los métodos `on_get`, `on_post` y hermanos, que se van a invocar dependiendo de verbo HTTP que nos sea solicitado, con un objeto tipo *request* y uno tipo *response*.

Veamos un ejemplo:

```bash
(.venv) gerard@sirius:~/projects/webservice$ cat requirements.txt 
falcon==1.2.0
(.venv) gerard@sirius:~/projects/webservice$ cat app.py 
import falcon
import json


class HelloResource(object):
    def on_get(self, req, res):
        res.body = json.dumps(
            {
                'message': 'Hello world',
            }
        )

api = falcon.API()
api.add_route('/', HelloResource())
(.venv) gerard@sirius:~/projects/webservice$ cat server.py 
#!/usr/bin/env python

from wsgiref.simple_server import make_server
from app import api

host = '127.0.0.1'
port = 8000
server = make_server(host, port, api)
try:
    print 'Serving on %s:%s...' % (host, port)
    server.serve_forever()
except KeyboardInterrupt:
    print '\nBye!'
(.venv) gerard@sirius:~/projects/webservice$ 
```

Ejecutamos el servidor de pruebas arriba expuesto para que sirva nuestra API simple:

```bash
(.venv) gerard@sirius:~/projects/webservice$ ./server.py 
Serving on 127.0.0.1:8000...
```

Y solo nos falta hacer alguna petición para ver como funciona:

```bash
gerard@sirius:~$ curl -i http://localhost:8000/
HTTP/1.0 200 OK
...  
content-type: application/json; charset=UTF-8

{"message": "Hello world"}
gerard@sirius:~$ curl -siX POST http://localhost:8000/ | head -1
HTTP/1.0 405 Method Not Allowed
gerard@sirius:~$ 
```

Y con esto tenemos una API simple. Lo normal es que los datos salgan de algún tipo de base de datos, pero **falcon** no ofrece soporte para ninguna, con lo que deberíamos usar lo que más nos convenga, por ejemplo **mongodb** con **mongoengine**.

En caso de querer extraer parámetros de la url, podemos registrar la ruta con una URL de la forma `/hello/{name}`. De esta forma, nuestra función recibiría un parámetro `name` con el contenido de ese segmento de URL, además de los objetos *request* y *response*. Un  ejemplo a continuación:

```bash
(.venv) gerard@sirius:~/projects/webservice$ cat app.py 
import falcon
import json


class HelloResource(object):
    def on_get(self, req, res, name):
        res.body = json.dumps(
            {
                'message': 'Hello %s' % name,
            }
        )

api = falcon.API()
api.add_route('/hello/{name}', HelloResource())
(.venv) gerard@sirius:~/projects/webservice$ 
```

## Hooks

Otra funcionalidad muy interesante son los *hooks*, que son métodos con la forma `func(req, resp, resource, params)` que se llaman antes o después de atender la función del *resource* y nos permiten hacer varias cosas; desde añadir código hasta condicionar un método concreto.

**AVISO**: Los *hooks* registrados con `falcon.after` no disponen del parámetro `params`.

Veamos un ejemplo, para evitar el código de serialización en cada método:

```bash
(.venv) gerard@sirius:~/projects/webservice$ cat app.py 
import falcon
import json


def serialize(req, res, resource):
    if req.client_accepts_json:
        res.body = json.dumps(res.body)


class HelloResource(object):
    @falcon.after(serialize)
    def on_get(self, req, res, name):
        res.body = {
            'message': 'Hello %s' % name,
        }

api = falcon.API()
api.add_route('/hello/{name}', HelloResource())
(.venv) gerard@sirius:~/projects/webservice$ 
```

Solo nos queda decir que estos *hooks* se pueden registrar a nivel de método o de *resource* (aplicaría a todos los métodos del *resource*). En caso de querer que aplique a toda la aplicación habría que escribir un *middleware* apropiado.
