---
title: "Poniendo un Docker Registry en el Swarm"
slug: "poniendo-un-docker-registry-en-el-swarm"
date: "2021-02-25"
categories: ['Sistemas']
tags: ['docker', 'swarm', 'registro']
---

Muchas veces nos encontramos que es más fácil y barato contratar un servicio de registro
**Docker** en el *cloud*. Así nos olvidamos del *hosting*, certificados SSL, *backups*
y demás tareas de administración. Otras veces preferimos recortar en costes y hacer un
registro local en nuestra propia infraestructura, como ya hicimos [aquí][1] y [aquí][2].<!--more-->

Esta última opción nos plantea algunas opciones:

* Usar HTTPS, con certificados válidos.
  * Hay que pagar el certificado, o usar y configurar algo como [Let’s Encrypt][3].
  * Hay que estar pendiente de la renovación e instalación de los certificados.
* Usar HTTPS, con certificados autofirmados.
  * Hay que [añadir el certificado][4] en todos los nodos del **Swarm**.
  * Alternativamente podemos modificar los [insecure registries][4].
* Usar HTTP plano.
  * Hay que configurar sí o sí los [insecure registries][4].

Aunque si nos fijamos, la configuración por defecto de **Docker** ya nos dan parte del trabajo hecho...

```bash
gerard@atlantis:~$ docker info
...
 Insecure Registries:
  127.0.0.0/8
...
gerard@atlantis:~$ 
```

Eso significa que cualquier registro local, con IP 127.x.x.x va a ser de confianza
para **docker**; va hacer las peticiones por HTTPS (confiando en el certificado) y si
no se trata de HTTPS, las hará por HTTP. Eso vale para registros locales, escuchando
en *localhost*, que viene a ser algo así como "la máquina en la que estamos".

En un entorno de **swarm** no nos sirve demasiado, porque cada nodo consultaría su
registro local. Eso supone un reto adicional, o eso creía hasta que me acordé de
este pequeño trozo de [la documentación][5] (aunque el texto describe un ejemplo
usando el puerto 8080):

> When you access port 8080 on **any node**, Docker routes your request to an active container.

Es decir, que si publicamos nuestro registro en el puerto 5000, todos los nodos van a
poder acceder al registro en el puerto 5000 de cualquier nodo, incluso **de sí mismo**.

Como confiamos en las direcciones locales, podemos usar certificados autofirmados o
incluso HTTP plano; solo debemos tener la precaución de utilizar la dirección local
al utilizar el registro (por ejemplo, 127.0.0.1). Usar HTTP o HTTPS, autenticación o
no, es una decisión que tendremos que tomar de acuerdo a la facilidad de acceso a
nuestro entorno por terceros usuarios (de nuestra empresa o de fuera).

## El entorno

Para no complicar el artículo utilizamos un **swarm** pequeño, a modo de ejemplo.
Partimos de un **docker swarm** simple, de dos nodos; puesto que este es un ejemplo
rápido y no productivo, de momento nos vale.

```bash
gerard@server01:~$ docker node ls
ID                            HOSTNAME   STATUS    AVAILABILITY   MANAGER STATUS   ENGINE VERSION
swyr79nl5vbe70o0bigx4s054 *   server01   Ready     Active         Leader           20.10.3
siaz5eahkoznldau8208k87op     server02   Ready     Active                          20.10.3
gerard@server01:~$ 
```

## Desplegando el registro

Supongamos que tenemos un entorno **swarm** totalmente cerrado, en el que solo tienen
acceso los administradores más confiables de nuestro equipo. Por ello decidimos que
no necesitamos HTTP ni autenticación, lo que hace más breve y conciso el artículo.

El *stack* no guarda ninguna complicación; solo hay que tener en cuenta que hay
que publicar el puerto y que, como usamos volúmenes locales, el contenedor se debe
desplegar siempre en el mismo nodo.

```bash
gerard@server01:~/stacks/tools$ cat stack.yml 
version: '3'
services:
  registry:
    image: registry:2.7
    volumes:
      - registry_data:/var/lib/registry
    ports:
      - "5000:5000"
    deploy:
      placement:
        constraints:
          - "node.hostname==server02"
volumes:
  registry_data:
gerard@server01:~/stacks/tools$ 
```

Vamos a desplegar nuestro servicio de registro con el típico *script* de *deploy*:

```bash
gerard@server01:~/stacks/tools$ cat deploy.sh 
#!/bin/bash

docker stack deploy -c stack.yml tools
gerard@server01:~/stacks/tools$ 
```

```bash
gerard@server01:~/stacks/tools$ ./deploy.sh 
Creating network tools_default
Creating service tools_registry
gerard@server01:~/stacks/tools$ 
```

Ahora esperamos a que levante el servicio de registro...

```bash
gerard@server01:~/stacks/tools$ docker stack ps tools
ID             NAME               IMAGE          NODE       DESIRED STATE   CURRENT STATE            ERROR     PORTS
oh7abrq1f1xa   tools_registry.1   registry:2.7   server02   Running         Running 11 seconds ago             
gerard@server01:~/stacks/tools$ 
```

Y verificamos que ambos nodos (**server01** y **server02**) acceden al registro en
su dirección local, aunque de momento el registro está vacío y no alberga ninguna imagen:

```bash
gerard@server01:~$ curl http://127.0.0.1:5000/v2/_catalog
{"repositories":[]}
gerard@server01:~$ 
```

```bash
gerard@server02:~$ curl http://127.0.0.1:5000/v2/_catalog
{"repositories":[]}
gerard@server02:~$ 
```

## Subiendo una imagen al registro

Supongamos que tenemos nuestra aplicación, lista para crear la imagen y subirla.
La aplicación en sí misma es ahora irrelevante; cualquiera nos valdría. Para este
caso concreto hemos preparado un contexto para la [aplicación de ejemplo][6] escrita
con el *framework* **Flask**.

```bash
gerard@server01:~/build/helloworld$ cat app.py 
from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!\n'
gerard@server01:~/build/helloworld$ 
```

```bash
gerard@server01:~/build/helloworld$ cat requirements.txt 
gunicorn==20.0.4
Flask==1.1.2
gerard@server01:~/build/helloworld$ 
```

```bash
gerard@server01:~/build/helloworld$ cat Dockerfile 
FROM python:3.9-alpine
COPY app.py requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--chdir=/app", "app:app"]
gerard@server01:~/build/helloworld$ 
```

Construimos la imagen con los comandos habituales, dándole un nombre y un *tag*,
precedidos por la dirección de nuestro registro, para que un `docker push` sepa
en qué registro subirlo en un futuro cercano.

```bash
gerard@server01:~/build/helloworld$ docker build -t 127.0.0.1:5000/helloworld:v1 .
...
Successfully tagged 127.0.0.1:5000/helloworld:v1
gerard@server01:~/build/helloworld$ 
```

Podemos verificar que disponemos de nuestra imagen como imagen local:

```bash
gerard@server01:~/build/helloworld$ docker images
REPOSITORY                  TAG          IMAGE ID       CREATED              SIZE
127.0.0.1:5000/helloworld   v1           43988269a061   About a minute ago   55.3MB
python                      3.9-alpine   770dd9c7c0e8   3 days ago           44.7MB
gerard@server01:~/build/helloworld$ 
```

Y la subimos al registro con el típico `docker push`. En este caso no hay que
hacer *login* porque hemos decidido que no hace falta autenticación, al tratarse
de un entorno cerrado y aislado de curiosos.

```bash
gerard@server01:~/build/helloworld$ docker push 127.0.0.1:5000/helloworld:v1
The push refers to repository [127.0.0.1:5000/helloworld]
...
gerard@server01:~/build/helloworld$ 
```

Finalmente verificamos que ambos nodos ven la misma imagen en el registro, a pesar de
que la subida se hizo desde el primer nodo; se trata pues **del mismo registro**.

```bash
gerard@server01:~$ curl http://127.0.0.1:5000/v2/_catalog
{"repositories":["helloworld"]}
gerard@server01:~$ 
```

```bash
gerard@server02:~$ curl http://127.0.0.1:5000/v2/_catalog
{"repositories":["helloworld"]}
gerard@server02:~$ 
```

## Desplegando desde nuestro registro

En un futuro podemos querer desplegar un servicio basado en la imagen que hemos
creado en el paso anterior. Ello no entraña ninguna dificultad y basta con indicar
la procedencia de la imagen: `127.0.0.1:5000/helloworld:v1`. Cada nodo que lo
necesite descargará la imagen de la dirección local que, como ya hemos visto, se
trata del servicio de registro alojado en **server02**.

Podemos hacer algo como lo siguiente:

```bash
gerard@server01:~/stacks/apps$ cat stack.yml 
version: '3'
services:
  helloworld:
    image: 127.0.0.1:5000/helloworld:v1
    ports:
      - "8080:8080"
    deploy:
      replicas: 4
gerard@server01:~/stacks/apps$ 
```

```bash
gerard@server01:~/stacks/apps$ cat deploy.sh 
#!/bin/bash

docker stack deploy -c stack.yml apps
gerard@server01:~/stacks/apps$ 
```

```bash
gerard@server01:~/stacks/apps$ ./deploy.sh 
Creating network apps_default
Creating service apps_helloworld
gerard@server01:~/stacks/apps$ 
```

Si esperamos un poco veremos que el nodo *leader* (uno de los *managers*), va a
repartir a los diferentes nodos las tareas de desplegar los contenedores necesarios
según la especificación que le hemos indicado (son 4 en este ejemplo, 2 en cada nodo
por casualidad). Cada nodo que lo necesite se descargará la imagen para poder levantar
el contenedor; en este caso, **server02** la descargará, pero **server01** no lo hará,
puesto que ya la tenía tras hacer el *build*.

```bash
gerard@server01:~$ docker stack ps apps
ID             NAME                IMAGE                          NODE       DESIRED STATE   CURRENT STATE            ERROR     PORTS
i0fm4sm559o6   apps_helloworld.1   127.0.0.1:5000/helloworld:v1   server02   Running         Running 51 seconds ago             
ai68kl2xwxwg   apps_helloworld.2   127.0.0.1:5000/helloworld:v1   server01   Running         Running 59 seconds ago             
wx86w8bluhe5   apps_helloworld.3   127.0.0.1:5000/helloworld:v1   server02   Running         Running 51 seconds ago             
0huco1cl92t1   apps_helloworld.4   127.0.0.1:5000/helloworld:v1   server01   Running         Running 59 seconds ago             
gerard@server01:~$ 
```

Solo falta comprobar que el servicio funciona y nuestra aplicación se comporta como esperamos...

```bash
gerard@server01:~$ curl http://127.0.0.1:8080/
Hello, World!
gerard@server01:~$ 
```

[1]: {{< relref "/articles/2017/01/un-registro-local-de-docker.md" >}}
[2]: {{< relref "/articles/2018/11/un-registro-docker-privado-por-https-con-autenticacion-basica.md" >}}
[3]: https://letsencrypt.org/
[4]: https://docs.docker.com/registry/insecure/
[5]: https://docs.docker.com/engine/swarm/ingress/#publish-a-port-for-a-service
[6]: https://flask.palletsprojects.com/en/1.1.x/quickstart/#a-minimal-application
