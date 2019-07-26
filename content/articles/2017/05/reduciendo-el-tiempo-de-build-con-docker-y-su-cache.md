---
title: "Reduciendo el tiempo de build con Docker y su caché"
slug: "reduciendo-el-tiempo-de-build-con-docker-y-su-cache"
date: 2017-05-08
categories: ['Operaciones']
tags: ['docker', 'dockerfile', 'cache']
---

Cuando construimos imágenes **docker**, muchas veces no somos conscientes del poder de la caché integrada. Si reordenamos algunas instrucciones y aplicamos algún truco, podemos evitarnos el hecho de reconstruir muchas de esas capas, llegando a reducir el tiempo de *rebuild* a prácticamente cero, siempre y cuando no hayan grandes cambios.<!--more-->

Esa es una reflexión que me hice el otro día. Es verdad que con la caché integrada me ahorro de descargar la imagen base y de instalar algunas dependencias habituales, pero usando la cabeza descubrí que puedo conseguir mucho más.

Es muy habitual que tenga que construir proyectos que usen **python**, pero me molesta un poco tener que perder el tiempo en el comando **pip** instalando dependencias; hay que tener en cuenta que casi nunca cambian entre diferentes versiones y es un tiempo que no sería necesario.

Así que hice el ejercicio de reordenar las instrucciones en mi *Dockerfile*, moviendo al principio aquellas instrucciones que raramente provocarán cambios, y dejando al final aquellas que es más frecuente que cambien, y por lo tanto, que necesiten ser reconstruidas.

## Un ejemplo práctico

Para empezar, vamos a usar un aplicación simple, concretamente un *hello world* estándar con un *microframework* llamado **bottle**.

```bash
gerard@aldebaran:~/docker/myapp$ tree
.
├── app
│   ├── app.py
│   └── requirements.txt
└── Dockerfile

1 directory, 3 files
gerard@aldebaran:~/docker/myapp$ 
```

Realmente la aplicación es lo de menos, siendo este ejemplo extrapolable a cada *framework* o librería que se necesite; se incluyen por tener el ejemplo completo.

```bash
gerard@aldebaran:~/docker/myapp$ cat app/app.py 
from bottle import Bottle

app = Bottle()

@app.get('/')
def hello():
    return 'Hello world!'
gerard@aldebaran:~/docker/myapp$ cat app/requirements.txt 
bottle==0.12.13
gerard@aldebaran:~/docker/myapp$ cat app/app.py 
from bottle import Bottle

app = Bottle()

@app.get('/')
def hello():
    return 'Hello world!'
gerard@aldebaran:~/docker/myapp$ 
```

Para construir la imagen, usamos un *Dockerfile* muy estándar y nada complejo:

```bash
gerard@aldebaran:~/docker/myapp$ cat Dockerfile
FROM alpine:3.5
RUN apk add --no-cache py-gunicorn py2-pip
COPY app/ /srv/app/
RUN pip install -r /srv/app/requirements.txt
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--user=nobody", "--group=nobody", "--workers=2", "--chdir=/srv/app", "app:app"]
gerard@aldebaran:~/docker/myapp$ 
```

Así que construimos nuestra imagen, con el comando habitual:

```bash
gerard@aldebaran:~/docker/myapp$ docker build -t myapp:1.0 .
Sending build context to Docker daemon  5.632kB
...  
Successfully built 46611b6a730f
gerard@aldebaran:~/docker/myapp$ 
```

No es difícil comprobar lo que pasa cuando modificamos un poco nuestra aplicación, que en este caso se localiza entera en *app.py*: se reconstruyen todos los pasos a partir del tercero (el COPY).

```bash
gerard@aldebaran:~/docker/myapp$ docker build -t myapp:1.1 .
Sending build context to Docker daemon  5.632kB
Step 1/5 : FROM alpine:3.5
 ---> 4a415e366388
Step 2/5 : RUN apk add --no-cache py-gunicorn py2-pip
 ---> Using cache
 ---> fa57ea0220f9
Step 3/5 : COPY app/ /srv/app/
 ---> dcaa218d663e
Removing intermediate container 800e88f3a533
Step 4/5 : RUN pip install -r /srv/app/requirements.txt
 ---> Running in 29914cddfb3d
Collecting bottle==0.12.13 (from -r /srv/app/requirements.txt (line 1))
  Downloading bottle-0.12.13.tar.gz (70kB)
Installing collected packages: bottle
  Running setup.py install for bottle: started
    Running setup.py install for bottle: finished with status 'done'
Successfully installed bottle-0.12.13
You are using pip version 9.0.0, however version 9.0.1 is available.
You should consider upgrading via the 'pip install --upgrade pip' command.
 ---> 4e294d8038a8
Removing intermediate container 29914cddfb3d
Step 5/5 : CMD gunicorn --bind=0.0.0.0:8080 --user=nobody --group=nobody --workers=2 --chdir=/srv/app app:app
 ---> Running in 6021cfceff96
 ---> b781e46aec9c
Removing intermediate container 6021cfceff96
Successfully built b781e46aec9c
gerard@aldebaran:~/docker/myapp$ 
```

A partir de aquí, vamos a intentar mejorar eso.

### Reordenamos las capas: las menos probables de cambio, antes

En este ejemplo, no hay mucho que cambiar; solo hay una instrucción que es siempre la misma (el CMD), pero que se reconstruye porque las anteriores también lo hacen. En este caso, solo le indica el comando de *runtime*, y para esto no se depende ni del COPY, ni del *pip install*, así que puede ir antes de ambas.

```bash
gerard@aldebaran:~/docker/myapp$ cat Dockerfile
FROM alpine:3.5
RUN apk add --no-cache py-gunicorn py2-pip
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--user=nobody", "--group=nobody", "--workers=2", "--chdir=/srv/app", "app:app"]
COPY app/ /srv/app/
RUN pip install -r /srv/app/requirements.txt
gerard@aldebaran:~/docker/myapp$ 
```

En este punto no nos queda más remedio que reconstruir las 3 capas de nuevo, pero vemos que los *builds* sucesivos (con la aplicación modificada) no van a provocar cambio en esa capa.

```bash
gerard@aldebaran:~/docker/myapp$ docker build -t myapp:1.2 .
Sending build context to Docker daemon  5.632kB
...  
Successfully built b9ca6021019e
gerard@aldebaran:~/docker/myapp$ 
```
Cambiamos nuestra aplicación, y vemos que el paso CMD no se reconstruye:

```bash
gerard@aldebaran:~/docker/myapp$ docker build -t myapp:1.3 .
Sending build context to Docker daemon  5.632kB
...  
Step 3/5 : CMD gunicorn --bind=0.0.0.0:8080 --user=nobody --group=nobody --workers=2 --chdir=/srv/app app:app
 ---> Using cache
 ---> 0e99aa9dd9cf
...  
Successfully built b4289c56e7cb
gerard@aldebaran:~/docker/myapp$ 
```

Y con esto nos ahorramos reconstruir capas que realmente no cambian, pero ven forzada su reconstrucción porque las capas anteriores sí lo hacen. En un caso más complejo, el beneficio se notaría más que en este pequeño ejemplo.

### Copias parciales para ahorrarnos capas

El ejemplo anterior ha supuesto una mejora, pero vemos un hecho curioso: el *pip install* es el paso más lento en una reconstrucción y no sería necesario en caso de no cambiar las dependencias de nuestra aplicación, que es la mayoría de veces. Entonces, ¿Porqué se tiene que rehacer cada vez, para obtener exactamente el mismo resultado?

Simplemente se hace porque al copiar la carpeta, **docker** detecta un cambio *en alguno* de los ficheros, y por diseño, invalida la capa equivalente. Esto causa una invalidación de caché en cascada y obliga a las siguientes instrucciones a rehacerse.

El truco consiste en copiar solamente el fichero de requisitos, con la esperanza de que no haya cambiado, lo que nos ahorraría el *pip install*, ya que no invalidaría las capas de caché. El resto de la aplicación se puede copiar después.

```bash
gerard@aldebaran:~/docker/myapp$ cat Dockerfile
FROM alpine:3.5
RUN apk add --no-cache py-gunicorn py2-pip
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--user=nobody", "--group=nobody", "--workers=2", "--chdir=/srv/app", "app:app"]
COPY app/requirements.txt /srv/app/
RUN pip install -r /srv/app/requirements.txt
COPY app/ /srv/app/
gerard@aldebaran:~/docker/myapp$ 
```

Construimos la imagen dos veces, una para crear la nueva estructura de capas (el precio de la primera construcción), y la otra para ver el beneficio de la nueva aproximación.

```bash
gerard@aldebaran:~/docker/myapp$ docker build -t myapp:1.4 .
Sending build context to Docker daemon  5.632kB
...  
Successfully built c64016c758a4
gerard@aldebaran:~/docker/myapp$ 
```

Y a partir de ahora, cada cambio de código que no implique un cambio en el *requirements.txt*, solo implicará copiar ese código sobre la capa que ya contiene nuestras dependencias, ahorrándonos el *pip install*, y convirtiendo el proceso de *build* en algo casi instantáneo.

```bash
gerard@aldebaran:~/docker/myapp$ time docker build -t myapp:1.5 .
Sending build context to Docker daemon  5.632kB
Step 1/6 : FROM alpine:3.5
 ---> 4a415e366388
Step 2/6 : RUN apk add --no-cache py-gunicorn py2-pip
 ---> Using cache
 ---> fa57ea0220f9
Step 3/6 : CMD gunicorn --bind=0.0.0.0:8080 --user=nobody --group=nobody --workers=2 --chdir=/srv/app app:app
 ---> Using cache
 ---> 0e99aa9dd9cf
Step 4/6 : COPY app/requirements.txt /srv/app/
 ---> Using cache
 ---> 32595afecfc4
Step 5/6 : RUN pip install -r /srv/app/requirements.txt
 ---> Using cache
 ---> e37068fe5c99
Step 6/6 : COPY app/ /srv/app/
 ---> d31b7abdbfb2
Removing intermediate container 01e78f27475d
Successfully built d31b7abdbfb2

real	0m0.330s
user	0m0.004s
sys	0m0.004s
gerard@aldebaran:~/docker/myapp$ 
```

De hecho, podemos ver que las capas compartidas entre las versiones con este nuevo truco se comparten casi todas. Esto hace que las nuevas versiones apenas ocupen espacio en disco (117 bytes en el ejemplo), siendo una capa con solamente nuestro código.

```bash
gerard@aldebaran:~/docker/myapp$ docker history myapp:1.4
IMAGE               CREATED             CREATED BY                                      SIZE                COMMENT
c64016c758a4        7 minutes ago       /bin/sh -c #(nop) COPY dir:244f5d5a6f7ec84...   117B                
e37068fe5c99        7 minutes ago       /bin/sh -c pip install -r /srv/app/require...   573kB               
32595afecfc4        7 minutes ago       /bin/sh -c #(nop) COPY file:2f968d5854b929...   16B                 
0e99aa9dd9cf        21 minutes ago      /bin/sh -c #(nop)  CMD ["gunicorn" "--bind...   0B                  
fa57ea0220f9        31 minutes ago      /bin/sh -c apk add --no-cache py-gunicorn ...   48.4MB              
4a415e366388        6 weeks ago         /bin/sh -c #(nop) ADD file:730030a984f5f0c...   3.99MB              
gerard@aldebaran:~/docker/myapp$ docker history myapp:1.5
IMAGE               CREATED             CREATED BY                                      SIZE                COMMENT
d31b7abdbfb2        3 minutes ago       /bin/sh -c #(nop) COPY dir:36a1b0f6acdabc2...   117B                
e37068fe5c99        7 minutes ago       /bin/sh -c pip install -r /srv/app/require...   573kB               
32595afecfc4        7 minutes ago       /bin/sh -c #(nop) COPY file:2f968d5854b929...   16B                 
0e99aa9dd9cf        21 minutes ago      /bin/sh -c #(nop)  CMD ["gunicorn" "--bind...   0B                  
fa57ea0220f9        31 minutes ago      /bin/sh -c apk add --no-cache py-gunicorn ...   48.4MB              
4a415e366388        6 weeks ago         /bin/sh -c #(nop) ADD file:730030a984f5f0c...   3.99MB              
gerard@aldebaran:~/docker/myapp$ 
```

La parte mala, es que el fichero *requirements.txt* se copia dos veces en nuestra imagen, en ambos COPY. Con un poco de trabajo podría evitarse eso pero, puesto que ocupa relativamente poco, es un precio que estoy dispuesto a pagar para tener *builds* instantáneos.
