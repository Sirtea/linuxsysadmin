---
title: "Un registro local de Docker"
slug: "un-registro-local-de-docker"
date: 2017-01-09
categories: ['Sistemas']
tags: ['registro', 'docker']
---

He llegado a ese momento en el que el número de imágenes **docker** que he construido se me ha ido de las manos. Ya no pueden seguir ocupando espacio en mi local, así que me he decidido a montar mi propio registro de imágenes, para mi uso y disfrute privado.<!--more-->

Si miramos en [DockerHub](https://hub.docker.com/_/registry/) no nos va a costar demasiado encontrar una imagen que nos proporciones este servicio. Ejecutar esta imagen para uso local no tiene ninguna complicación, y basta con seguir las instrucciones. La cosa se complica si queremos sacarlo de nuestra infraestructura, pero no va a ser el caso de hoy.

## Levantando un registro local

Siguiendo las instrucciones, lanzamos el comando indicado en la documentación:

```bash
gerard@aldebaran:~/docker/registry$ docker run -d -p 5000:5000 registry
735016f722f25c0d8a8f09c1e2b856011d46fa4efd3a4d6c7846405140443128
gerard@aldebaran:~/docker/registry$ 
```

Solo necesitamos exponer el puerto 5000 que, por comodidad, va a usar el mismo puerto en mi máquina local. La única parte con estado de la imagen es */var/lib/registry*, y puede resultar interesante saberlo para hacer copias de seguridad; no voy a hacerlo porque la imagen ya lleva por defecto un *container volume* declarado.

```bash
gerard@aldebaran:~/docker/registry$ docker history registry
IMAGE               CREATED             CREATED BY                                      SIZE                COMMENT
c9bd19d022f6        7 weeks ago         /bin/sh -c #(nop)  CMD ["/etc/docker/registry   0 B                 
<missing>           7 weeks ago         /bin/sh -c #(nop)  ENTRYPOINT ["/entrypoint.s   0 B                 
<missing>           7 weeks ago         /bin/sh -c #(nop) COPY file:7b57f7ab1a8cf85c0   155 B               
<missing>           7 weeks ago         /bin/sh -c #(nop)  EXPOSE 5000/tcp              0 B                 
<missing>           7 weeks ago         /bin/sh -c #(nop)  VOLUME [/var/lib/registry]   0 B                 
<missing>           7 weeks ago         /bin/sh -c #(nop) COPY file:6c4758d509045dc45   295 B               
<missing>           7 weeks ago         /bin/sh -c #(nop) COPY file:3f73dd916d906a0db   27.21 MB            
<missing>           7 weeks ago         /bin/sh -c set -ex     && apk add --no-cache    1.287 MB            
<missing>           7 weeks ago         /bin/sh -c #(nop) ADD file:7afbc23fda8b0b3872   4.803 MB            
gerard@aldebaran:~/docker/registry$ docker inspect 735016f722f2
[
    {
...  
        "Mounts": [
            {
                "Name": "875b58044b85426eb82b5ea74f51f22865994d1bb84d26317c91abaaf1d5f83c",
                "Source": "/var/lib/docker/volumes/875b58044b85426eb82b5ea74f51f22865994d1bb84d26317c91abaaf1d5f83c/_data",
                "Destination": "/var/lib/registry",
                "Driver": "local",
                "Mode": "",
                "RW": true,
                "Propagation": ""
            }
        ],
...  
    }
]
gerard@aldebaran:~/docker/registry$ 
```

Si preferís la versión usando **docker-compose**, no difiere demasiado:

```bash
gerard@aldebaran:~/docker/registry$ cat docker-compose.yml 
version: '2'
services:
  registry:
    image: registry
    hostname: registry
    container_name: registry
    volumes:
      - ./data:/var/lib/registry
    ports:
      - "5000:5000"
gerard@aldebaran:~/docker/registry$ docker-compose up -d
Creating network "registry_default" with the default driver
Creating registry
gerard@aldebaran:~/docker/registry$ 
```

En este caso, se ha optado por mapear el volumen */var/lib/registry* en una carpeta local, para poder inspeccionarlo fácilmente y para sacar *backups* con mas facilidad todavía.

## Uso de nuestro registro local

Se puede trabajar con nuestro registro de la misma forma con la que lo haríamos con *DockerHub*, a base de usar el comando *docker push* y *docker pull*. Solo hay que mencionar que el registro destino viene especificado en el nombre de la imagen, en el formato `<host>:<port>/<imagen>:<tag>`. Por ejemplo, vamos a subir una imagen *alpine:3.4*, aunque podría ser una imagen nuestra.

```bash
gerard@aldebaran:~/docker/registry$ docker tag alpine:3.4 localhost:5000/alpine:3.4
gerard@aldebaran:~/docker/registry$ docker images
REPOSITORY                                                                                      TAG                 IMAGE ID            CREATED             SIZE
alpine                                                                                          3.4                 baa5d63471ea        7 weeks ago         4.803 MB
localhost:5000/alpine                                                                           3.4                 baa5d63471ea        7 weeks ago         4.803 MB
gerard@aldebaran:~/docker/registry$ docker push localhost:5000/alpine:3.4
The push refers to a repository [localhost:5000/alpine]
011b303988d2: Pushed 
3.4: digest: sha256:1354db23ff5478120c980eca1611a51c9f2b88b61f24283ee8200bf9a54f2e5c size: 528
gerard@aldebaran:~/docker/registry$ 
```

Y las capas que conforman nuestra imagen, quedan guardadas en nuestro registro local, como podemos ver:

```bash
gerard@aldebaran:~/docker/registry$ tree data/
data/
└── docker
    └── registry
        └── v2
            ├── blobs
            │   └── sha256
            │       ├── 13
            │       │   └── 1354db23ff5478120c980eca1611a51c9f2b88b61f24283ee8200bf9a54f2e5c
            │       │       └── data
            │       ├── 36
            │       │   └── 3690ec4760f95690944da86dc4496148a63d85c9e3100669a318110092f6862f
            │       │       └── data
            │       └── ba
            │           └── baa5d63471ead618ff91ddfacf1e2c81bf0612bfeb1daf00eb0843a41fbfade3
            │               └── data
            └── repositories
                └── alpine
                    ├── _layers
                    │   └── sha256
                    │       ├── 3690ec4760f95690944da86dc4496148a63d85c9e3100669a318110092f6862f
                    │       │   └── link
                    │       └── baa5d63471ead618ff91ddfacf1e2c81bf0612bfeb1daf00eb0843a41fbfade3
                    │           └── link
                    ├── _manifests
                    │   ├── revisions
                    │   │   └── sha256
                    │   │       └── 1354db23ff5478120c980eca1611a51c9f2b88b61f24283ee8200bf9a54f2e5c
                    │   │           └── link
                    │   └── tags
                    │       └── 3.4
                    │           ├── current
                    │           │   └── link
                    │           └── index
                    │               └── sha256
                    │                   └── 1354db23ff5478120c980eca1611a51c9f2b88b61f24283ee8200bf9a54f2e5c
                    │                       └── link
                    └── _uploads

28 directories, 8 files
gerard@aldebaran:~/docker/registry$ 
```

Nada nos impediría hacer un `docker pull localhost:5000/alpine:3.4` en el futuro.

**TRUCO**: En caso de querer hacer un *push* de un tag *default* de la imagen `tools/tsung`, bastaría con que usar `localhost:5000/tools/tsung`; el nombre de la imagen puede contener el separador `/` y el *tag* es opcional, usando el *tag* por defecto *default*, justo como pasa con *DockerHub*.

## Consultando el contenido de nuestro registro

Ahora mismo nuestro registro solo tiene guardado un *alpine:3.4*. Para poder ver una salida mas interesante de la API del registro, subo una *alpine:edge* y una *debian:jessie*. Así podemos apreciar dos imágenes, y una de ellas, con dos *tags*.

Empezamos dando un nombre que contenga *localhost:5000* como ya hemos visto más arriba:

```bash
gerard@aldebaran:~/docker/registry$ docker tag {,localhost:5000/}alpine:edge
gerard@aldebaran:~/docker/registry$ docker tag {,localhost:5000/}debian:jessie
gerard@aldebaran:~/docker/registry$ docker images | grep localhost
localhost:5000/debian                                                                           jessie              73e72bf822ca        4 weeks ago         123 MB
localhost:5000/alpine                                                                           edge                a1a3cae7a75e        7 weeks ago         3.979 MB
localhost:5000/alpine                                                                           3.4                 baa5d63471ea        7 weeks ago         4.803 MB
gerard@aldebaran:~/docker/registry$ 
```

Y los empujamos al registro:

```bash
gerard@aldebaran:~/docker/registry$ docker push localhost:5000/alpine:edge
The push refers to a repository [localhost:5000/alpine]
6f4ada5745cd: Pushed 
edge: digest: sha256:cd9c03c2d382fcf00c31dc1635445163ec185dfffb51242d9e097892b3b0d5b4 size: 528
gerard@aldebaran:~/docker/registry$ docker push localhost:5000/debian:jessie
The push refers to a repository [localhost:5000/debian]
fe4c16cbf7a4: Pushed 
jessie: digest: sha256:c1ce85a0f7126a3b5cbf7c57676b01b37c755b9ff9e2f39ca88181c02b985724 size: 529
gerard@aldebaran:~/docker/registry$ 
```

Disponemos de una API con -al menos- dos métodos que nos sirven para ver lo que hay en el registro:

* Listar las imágenes de nuestro repositorio -> `GET /v2/_catalog`
* Listar los *tags* de una imagen concreta -> `GET /v2/<imagen>/tags/list`

Así, podemos ver lo que hay con las siguientes invocaciones:

```bash
gerard@aldebaran:~/docker/registry$ curl http://localhost:5000/v2/_catalog
{"repositories":["alpine","debian"]}
gerard@aldebaran:~/docker/registry$ curl http://localhost:5000/v2/alpine/tags/list
{"name":"alpine","tags":["edge","3.4"]}
gerard@aldebaran:~/docker/registry$ curl http://localhost:5000/v2/debian/tags/list
{"name":"debian","tags":["jessie"]}
gerard@aldebaran:~/docker/registry$ 
```

Se puede automatizar esta salida con un simple *script*, que he escrito en **python**:

```bash
gerard@aldebaran:~/docker/registry$ cat list_registry.py 
#!/usr/bin/env python

import httplib
import json

def get_json_response(host, port, uri):
    c = httplib.HTTPConnection(host, port)
    c.request('GET', uri)
    r = c.getresponse()
    return json.load(r)

catalog = get_json_response('localhost', 5000, '/v2/_catalog')
for image in catalog['repositories']:
    print '* %s' % image
    taginfo = get_json_response('localhost', 5000, '/v2/%s/tags/list' % image)
    for tag in taginfo['tags']:
        print '    * %s:%s' % (taginfo['name'], tag)
gerard@aldebaran:~/docker/registry$ 
```

Y con esto vemos una salida bastante legible.

```bash
gerard@aldebaran:~/docker/registry$ ./list_registry.py 
* alpine
    * alpine:edge
    * alpine:3.4
* debian
    * debian:jessie
gerard@aldebaran:~/docker/registry$ 
```
