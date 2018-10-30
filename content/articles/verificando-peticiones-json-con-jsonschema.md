Title: Verificando peticiones JSON con jsonschema
Slug: verificando-peticiones-json-con-jsonschema
Date: 2018-11-05 10:00
Category: Desarrollo
Tags: JSON, python, jsonschema



A medida que las empresas confían más y más en las APIs REST, los datos que viajan en formato JSON ha incrementado notablemente. Con este incremento, los errores por mensajes mal formados también se ha incrementado; esto nos obliga a validar los mensajes, no solamente de sintaxis, sino de semántica.

Y es que no podemos permitirnos que nuestros procesos fallen porque alguien ha enviado un *payload* que no es JSON, pero tampoco podemos dejar de filtrar aquellos mensages que, aun siendo JSON válidos, no cumplen con las especificaciones necesarias para cumplir el contrato de nuestras APIs.

Investigando un poco, parece ser que ya hay una especificación formal para validar mensajes JSON de acuerdo a un *schema*; mas información [aquí](https://json-schema.org/). Como no podía ser menos, **python** incluye varias implementaciones de un validador; concretamente nos vamos a centrar en **jsonschema**.

## Exponiendo el problema

Supongamos que queremos consumir el mensaje de un *endpoint* de *login*, en donde esperamos un JSON tipo "object" con dos campos de texto, el "user" y el "password". Como ejemplo, me limitaré a sacarlos por pantalla:

```bash
gerard@atlantis:~/workspace$ cat run.py
#!/usr/bin/env python3

import sys
import json

payload = json.load(sys.stdin)
print(payload)

user = payload.get('user')
password = payload.get('password')
print('%s / %s' % (user, password))
gerard@atlantis:~/workspace$
```

Para probar este *script*, vamos a poner un conjunto de posibles entradas con variedad de posibles problemas:

```
gerard@atlantis:~/workspace$ cat inputs/no_json
hello world
gerard@atlantis:~/workspace$ cat inputs/string_json
"lorem ipsum"
gerard@atlantis:~/workspace$ cat inputs/bad_dict_json
{"user": true}
gerard@atlantis:~/workspace$ cat inputs/good_dict_json
{"user": "gerard", "password": "s3cr3t"}
gerard@atlantis:~/workspace$
```

El primer ejemplo es el más evidente; el mensaje no cumple con la sintaxis JSON, así que ni lo podeemos leer. De hecho, no necesitamos un *schema* para descartarlo.

```bash
gerard@atlantis:~/workspace$ ./run.py < inputs/no_json
Traceback (most recent call last):
  File "./run.py", line 6, in <module>
    payload = json.load(sys.stdin)
  File "/usr/lib/python3.5/json/__init__.py", line 268, in load
    parse_constant=parse_constant, object_pairs_hook=object_pairs_hook, **kw)
  File "/usr/lib/python3.5/json/__init__.py", line 319, in loads
    return _default_decoder.decode(s)
  File "/usr/lib/python3.5/json/decoder.py", line 339, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
  File "/usr/lib/python3.5/json/decoder.py", line 357, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
gerard@atlantis:~/workspace$
```

El segundo ejemplo es un JSON válido como tal, pero no cumple con nuestros requisitos de campos. Aunque podemos leerlo, no es un diccionario, y por lo tanto no podemos sacar los campos necesarios.

```bash
gerard@atlantis:~/workspace$ ./run.py < inputs/string_json
lorem ipsum
Traceback (most recent call last):
  File "./run.py", line 9, in <module>
    user = payload.get('user')
AttributeError: 'str' object has no attribute 'get'
gerard@atlantis:~/workspace$
```

El tercer caso es un JSON válido, un objeto, pero no incluye el campo "password", con lo que no nos vale. Además, el campo "user" no es una cadena de texto, y puede que eso sea un problema en el futuro. Hay que remarcar que no nos supone un problema en este momento, pero eventualmente lo será.

```bash
gerard@atlantis:~/workspace$ ./run.py < inputs/bad_dict_json
{'user': True}
True / None
gerard@atlantis:~/workspace$
```

Finalmente tenemos un ejemplo bueno, que funciona y que cumpliría con nuestras expectativas. Este es el único caso que deberíamos dar por bueno.

```bash
gerard@atlantis:~/workspace$ ./run.py < inputs/good_dict_json
{'password': 's3cr3t', 'user': 'gerard'}
gerard / s3cr3t
gerard@atlantis:~/workspace$
```

## Jsonschema al rescate

Una de las librerías que implementan la validación de un *schema* JSON es, como su nombre indica, **jsonschema**. No viene en la librería estándar, así que lo instalamos (cosa que he hecho en un *virtualenv*).

```bash
(env) gerard@atlantis:~/workspace$ pip install jsonschema
Collecting jsonschema
  Downloading https://files.pythonhosted.org/packages/77/de/47e35a97b2b05c2fadbec67d44cfcdcd09b8086951b331d82de90d2912da/jsonschema-2.6.0-py2.py3-none-any.whl
Installing collected packages: jsonschema
Successfully installed jsonschema-2.6.0
(env) gerard@atlantis:~/workspace$
```

La más importante de todas las funciones de **jsonschema** es `validate()` que es una función que recibe el mensaje y el *schema* y puede acabar en una excepción (si el mensaje no cumple con el *schema*) o normalmente (si el mensaje cumple con el *schema*). La documentación completa está [aquí](https://python-jsonschema.readthedocs.io/en/latest/).

Nuestro *script* solo necesita declarar el *schema* e invocar la función; con un simple bloque `try/except` sabremos si la sintaxis y la semántica del mensaje son válidas.

```bash
(env) gerard@atlantis:~/workspace$ cat run_schema.py
#!/usr/bin/env python3

import sys
import json
import jsonschema

login_schema = {
    'type': 'object',
    'required': ['username', 'password'],
    'properties': {
        'username': {'type': 'string'},
        'password': {'type': 'string'},
    },
    'additionalProperties': False,
}

def check_json_schema(input, schema):
    try:
        payload = json.loads(input)
        jsonschema.validate(payload, schema)
        return True
    except (json.decoder.JSONDecodeError, jsonschema.exceptions.ValidationError):
        return False

input = sys.stdin.read()
if check_json_schema(input, login_schema):
    user = payload.get('user')
    password = payload.get('password')
    print('%s / %s' % (user, password))
else:
    print('ERROR')
(env) gerard@atlantis:~/workspace$
```

Efectivamente, solo el caso bueno nos permitiría seguir, ya que los demás no tienen sentido para nuestro caso de uso. La excepción `ValidationError` incluye los detalles de lo que falló.

```bash
(env) gerard@atlantis:~/workspace$ ./run_schema.py < inputs/no_json
ERROR
(env) gerard@atlantis:~/workspace$ ./run_schema.py < inputs/string_json
ERROR
(env) gerard@atlantis:~/workspace$ ./run_schema.py < inputs/bad_dict_json
ERROR
(env) gerard@atlantis:~/workspace$ ./run.py < inputs/good_dict_json
{'user': 'gerard', 'password': 's3cr3t'}
gerard / s3cr3t
(env) gerard@atlantis:~/workspace$
```

## Uso en APIs

No es muy habitual procesar ficheros JSON en un *script*, pero si hacemos una API, podemos esperar entradas de todo tipo. El estándar REST nos invita a responder un "400 Bad Request" cuando la petición no es la que se espera, y vamos a abusar de ello.

```bash
(env) gerard@atlantis:~/workspace$ cat app.py
import falcon
import jsonschema

login_schema = {
    'type': 'object',
    'required': ['user', 'password'],
    'properties': {
        'user': {'type': 'string'},
        'password': {'type': 'string'},
    },
    'additionalProperties': False,
}

def check_json_schema(payload, schema):
    try:
        jsonschema.validate(payload, schema)
    except jsonschema.exceptions.ValidationError:
        raise falcon.HTTPBadRequest('Bad JSON schema')

class LoginResource:
    def on_post(self, req, resp):
        check_json_schema(req.media, login_schema)
        resp.media = {'status': 'logged'}

app = falcon.API()
app.add_route('/login', LoginResource())
(env) gerard@atlantis:~/workspace$
```

Servimos nuestra API de ejemplo y probamos algunas entradas, solo para verificar que todo funciona:

El primer ejemplo, es un objecto al que le faltan campos, así que lo rechazamos.

```bash
gerard@atlantis:~$ curl -i -H "Content-type: application/json" -X POST http://localhost:8000/login/ --data '{"user": "gerard"}'; echo ''
HTTP/1.1 400 Bad Request
...
{"title": "Bad JSON schema"}
gerard@atlantis:~$
```

El segundo ejemplo es un objecto con los campos correctos, pero uno de ellos es numérico, así que lo rechazamos.

```
gerard@atlantis:~$ curl -i -H "Content-type: application/json" -X POST http://localhost:8000/login/ --data '{"user": "gerard", "password": 123}'; echo ''
HTTP/1.1 400 Bad Request
...
{"title": "Bad JSON schema"}
gerard@atlantis:~$
```

El tercer ejemplo, aunque es correcto, incluye un campo de más. El validador lo rechaza en virtud de la propiedad `additionalProperties: false`. Esto es una preferencia personal y os la podéis saltar, ignorando los campos extras.

```bash
gerard@atlantis:~$ curl -i -H "Content-type: application/json" -X POST http://localhost:8000/login/ --data '{"user": "gerard", "password": "123", "other": "field"}'; echo ''
HTTP/1.1 400 Bad Request
...
{"title": "Bad JSON schema"}
gerard@atlantis:~$
```

Finalmente le ponemos un caso correcto, y vemos que funciona como es debido.

```bash
gerard@atlantis:~$ curl -i -H "Content-type: application/json" -X POST http://localhost:8000/login/ --data '{"user": "gerard", "password": "123"}'; echo ''
HTTP/1.1 200 OK
...
{"status": "logged"}
gerard@atlantis:~$
```

**NOTA**: El *framework* **falcon** ya dispone de un decorador `falcon.media.validators.jsonschema` que hace lo mismo. He optado por describir el caso general, por ser más útil en otras situaciones.
