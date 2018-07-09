Title: Explorando los tokens JWT
Slug: explorando-los-tokens-jwt
Date: 2018-07-16 09:00
Category: Desarrollo
Tags: JWT, token, api, REST, autenticación



Hace mucho tiempo que me fascinan las APIs REST; sin embargo siempre he pasado de sistemas de autenticación en mis proyectos personales. Cuando me puse en serio a investigar sobre este tema, descubrí la autenticación basada en *tokens*, y especialmente, los **JSON Web Tokens**, que es lo que explico hoy.

Cuando leemos las buenas prácticas de los servicios REST, una de las máximas es que **no hay estado**; eso significa que no hay peticiones a medias, ni sesiones ni nada: todo lo necesario para completar una llamada está en la misma petición.

Tradicionalmente, hemos pasado el usuario y la contraseña de algún modo en las cabeceras, evitando a terceros mediante el uso de HTTPS. Este método requiere la validación de las credenciales en cada petición, y supone un estrés innecesario a la base de datos.

Este panorama cambia cuando aparece una nueva filosofía: hacer *login* una vez y expedir un *token* con toda la información necesaria para futuras peticiones, probablemente con validez temporal.

Los [JSON Web Tokens](https://jwt.io/) funcionan de esta manera, aunque no intentan encriptar ningún dato; se limitan a la verificación de que la firma del mensaje es válida.

## Forma de un token JWT

Un *token* JWT tiene la forma `xxxxx.yyyyy.zzzzz`, con 3 partes separadas por puntos:

* Una cabecera, que es una especificación del tipo de *token* y un base64 del algoritmo de *hash* usado.
* Un payload, que es la información arbitraria que cargamos en el momento de crear el *token* y está en base64; algunos campos tienen significado especial.
* Una firma, que es un *hash* del mensaje con una clave del servidor, que sirve para que el servidor pueda verificarla como suya.

Veamos un ejemplo, con el siguiente token:

```bash
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZ2VyYXJkIiwiZXhwIjoiMTUyOTQwMzc5NSJ9.07VsjI6OFGjMwYTmzE9g8qoPpXJYAB5DuGiIROOY4HM
```

**NOTA**: La forma habitual de obtener este *token* es mediante una operación de *login*, y normalmente tiene una fecha de expiración, que en JWT es el campo `exp`, como un *unix timestamp*.


```bash
gerard@atlantis:~/workspace/jwttest$ echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" | base64 -d; echo ''
{"alg":"HS256","typ":"JWT"}
gerard@atlantis:~/workspace/jwttest$
```

```bash
gerard@atlantis:~/workspace/jwttest$ echo "eyJ1c2VyIjoiZ2VyYXJkIiwiZXhwIjoiMTUyOTQwMzc5NSJ9" | base64 -d; echo ''
{"user":"gerard","exp":"1529403795"}
gerard@atlantis:~/workspace/jwttest$
```

Cualquiera (salvo uso de HTTPS) puede ver la información contenida en el *token*. Sin embargo, para verificar la firma se necesita saber la clave con la que se cifró. De esta forma, un servidor puede expedir un *token* con información, pero gracias a la firma puede verificar que el *token* que le devuelven es el que expedió y no ha sido modificado por un tercero.

Como punto a favor, el estándar JWT permite firmar con una sola clave, o usando un par de claves RSA, la privada para cifrar y la pública para desencriptar. Esto hace que nuestros auditores de seguridad se queden tranquilos, aunque como veremos, solo tiene utilidad real en algunos casos.

## Creando un token con una clave simétrica

Este es el caso de uso más simple: un solo servicio genera y consume el *token*. En este tipo de casos nos importa poco que se encripte y se desencripte con la misma clave, así que vamos a lo simple.

![JWT de clave simétrica]({filename}/images/JWT_Symmetric_Key.png)

Como lo vamos a hacer en **python**, vamos a necesitar una librería que siga este estándar, por ejemplo, `PyJWT`:

```bash
(env) gerard@atlantis:~/workspace/jwttest$ pip freeze
...
PyJWT==1.6.4
(env) gerard@atlantis:~/workspace/jwttest$
```

Vamos a utilizar un *script* para generar el *token* y otro para validarlo, que son estos:

```bash
(env) gerard@atlantis:~/workspace/jwttest$ cat simple_encode.py
import jwt
import datetime
import sys

KEY = sys.argv[1]
USER = sys.argv[2]

payload = {
    'user': USER,
    'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=60),
}

print jwt.encode(payload, KEY, algorithm='HS256')
(env) gerard@atlantis:~/workspace/jwttest$
```

```bash
(env) gerard@atlantis:~/workspace/jwttest$ cat simple_decode.py
import jwt
import datetime
import sys

KEY = sys.argv[1]
TOKEN = sys.argv[2]

print jwt.decode(TOKEN, KEY, algorithm='HS256')
(env) gerard@atlantis:~/workspace/jwttest$
```

En algún punto, expedimos un *token* con un *secret* dado:

```bash
(env) gerard@atlantis:~/workspace/jwttest$ python simple_encode.py secret gerard
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZ2VyYXJkIiwiZXhwIjoxNTI5NDA1NTU0fQ.3KNRsiIEcOvxN5b8Tgv_5qd8_58nA91fCkPxmnNr9F0
(env) gerard@atlantis:~/workspace/jwttest$
```

Si lo intentamos verificar con el mismo *secret*, no hay problema:

```bash
(env) gerard@atlantis:~/workspace/jwttest$ python simple_decode.py secret eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZ2VyYXJkIiwiZXhwIjoxNTI5NDA1NTU0fQ.3KNRsiIEcOvxN5b8Tgv_5qd8_58nA91fCkPxmnNr9F0
{u'user': u'gerard', u'exp': 1529405554}
(env) gerard@atlantis:~/workspace/jwttest$
```

Un *secret* que no corresponde nos da un error, indicando que no es el *secret* con el que ciframos y desciframos, seguramente porque nos han dado el cambiazo, y por lo tanto, rechazamos el *token*:

```bash
(env) gerard@atlantis:~/workspace/jwttest$ python simple_decode.py badsecret eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZ2VyYXJkIiwiZXhwIjoxNTI5NDA1NTU0fQ.3KNRsiIEcOvxN5b8Tgv_5qd8_58nA91fCkPxmnNr9F0
Traceback (most recent call last):
...
jwt.exceptions.InvalidSignatureError: Signature verification failed
(env) gerard@atlantis:~/workspace/jwttest$
```

Si dejamos pasar el tiempo de expiración, el *token* también pasa a ser inválido:

```bash
(env) gerard@atlantis:~/workspace/jwttest$ python simple_decode.py secret eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZ2VyYXJkIiwiZXhwIjoxNTI5NDA1NTU0fQ.3KNRsiIEcOvxN5b8Tgv_5qd8_58nA91fCkPxmnNr9F0
Traceback (most recent call last):
...
jwt.exceptions.ExpiredSignatureError: Signature has expired
(env) gerard@atlantis:~/workspace/jwttest$
```

De esta forma podemos estar seguros que no se ha generado un *token* por un tercero, y que el que dimos no ha sido modificado.

## Creando un token con una clave asimétrica

Se trata de un caso un poco más complicado: un servicio genera el *token* y otros lo consumen. En estos casos conviene que solo uno pueda cifrar, y todos puedan verificarlo; de esta forma, una API comprometida no expone el algoritmo de encriptación y evitamos suplantaciones.

Este caso se utiliza en esquemas de *single sign on*, en donde un servicio de autenticación genera el *token*, indicando a qué aplicaciones tiene acceso un usuario. La responsabilidad de verificar el permiso recae en cada aplicación individual.

![JWT de clave asimétrica]({filename}/images/JWT_Single_Sign_On.png)

Vamos a asegurarnos que tenemos las librerías **python** necesarias:

```bash
(env) gerard@atlantis:~/workspace/jwttest$ pip freeze
...
PyJWT==1.6.4
cryptography==2.2.2
(env) gerard@atlantis:~/workspace/jwttest$
```

También vamos a necesitar el par de claves RSA:

```bash
(env) gerard@atlantis:~/workspace/jwttest$ openssl genrsa -out private.pem 1024
Generating RSA private key, 1024 bit long modulus
...........................++++++
...........................++++++
e is 65537 (0x010001)
(env) gerard@atlantis:~/workspace/jwttest$
```

```bash
(env) gerard@atlantis:~/workspace/jwttest$ openssl rsa -in private.pem -pubout -out public.pem
writing RSA key
(env) gerard@atlantis:~/workspace/jwttest$
```

La idea es que la clave privada se queda en el servidor de autenticación, de forma que **puede cifrar**. La parte publica es para todas las aplicaciones que necesiten **verificar** el *token*. De esta forma solo una puede expedir *tokens*, y por lo tanto, es el único punto de *hacking* del sistema distribuído.

En el servidor de autenticación haríamos algo así:

```python
def create_new_token(user, permissions):
    expire = datetime.timedelta(seconds=EXPIRE_SECONDS)
    payload = {
        'user': user,
        'permissions': permissions,
        'exp': datetime.datetime.utcnow() + expire,
    }
    return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm='RS256')
```

Mientras que si el usuario facilita un *token* a una aplicación, esta hará algo como:

```python
def extract_token(token):
    try:
        decoded = jwt.decode(token, JWT_PUBLIC_KEY, algorithms='RS256')
        return decoded
    except:
        raise
```

De esta forma se puede validar el *token*, que sea correcto, no se haya modificado, no esté expirado y con la seguridad que solo lo pudo generar el servidor de autenticación. No hace falta para nada ir a la base de datos, o pedir una verificación al creador del *token*. Lo único que no verifica este método es si el *payload* incluye permisos para  el uso del método de la API solicitado.
