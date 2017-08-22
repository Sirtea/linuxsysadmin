Title: Creando imágenes con estilo: la instrucción ONBUILD
Slug: creando-imagenes-con-estilo-la-instruccion-onbuild
Date: 2017-08-28 10:00
Category: Sistemas
Tags: docker, dockerfile, onbuild



En el día a día de mi trabajo, me encuentro con un conjunto muy variado de ficheros *Dockerfile* que vienen a hacer lo mismo, pero de formas muy distintas. El fichero original se pasa de mano en mano, pervirtiéndose en cada paso y al final queda hecho un gran asco.

Para evitar la reinvención de la rueda me propuse crear una imagen base, para que los desarrolladores no tuvieran que crear una imagen, que muchas veces está mal por falta de conocimiento de *Linux*, y que reduzca al máximo su participación.

## Un caso simple

Imaginemos una aplicación hecha con *NodeJS*, que es el caso más frecuente en mi trabajo; nuestro flujo de trabajo exige el uso de *npm* y del correspondiente *package.json*. Una instalación básica es bastante simple: se trata de copiar la aplicación, ejecutar el `npm install` de rigor y declarar que se va a ejecutar con `npm start`.

Tomemos como ejemplo el básico de *express*:

```bash
gerard@aldebaran:~/docker/nodetest/v1$ cat app/app.js 
const express = require('express')
const app = express()

app.get('/', function (req, res) {
  res.send('Hello World!')
})

app.listen(3000, function () {
  console.log('Example app listening on port 3000!')
})
gerard@aldebaran:~/docker/nodetest/v1$ cat app/package.json 
{
  "name": "app",
  "version": "1.0.0",
  "description": "",
  "main": "app.js",
  "scripts": {
    "start": "node app.js",
    "test": "echo \"Error: no test specified\" && exit 1"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "dependencies": {
    "express": "4.15.3"
  }
}
gerard@aldebaran:~/docker/nodetest/v1$ 
```

Siguiendo las instrucciones descritas más arriba, el *Dockerfile* no guarda ninguna complicación:

```bash
gerard@aldebaran:~/docker/nodetest/v1$ cat Dockerfile 
FROM node:6-slim
COPY app/ /srv/app/
WORKDIR /srv/app
RUN npm install --production
USER node
CMD ["npm", "start"]
gerard@aldebaran:~/docker/nodetest/v1$ 
```

Este *Dockerfile* nos genera una imagen adecuada, pero este fichero peca del mismo error que el resto: va a mutar un poco por cada mano por la que pase. Sin embargo, no podemos hacer una imagen base porque necesitamos la aplicación en la primera instrucción tras el **FROM**.

## La imagen base onbuild

Si miramos [la documentación](https://docs.docker.com/engine/reference/builder/#onbuild), podemos ver que podemos declarar algunas operaciones para que se lancen automáticamente tras todo **FROM** que herede de nuestra imagen base. De esta forma, podemos declarar operaciones pendientes, al no disponer todavía de la aplicación final que va a tener que ejecutar nuestro contenedor.

Vamos a retrasar la ejecución de todas aquellas instrucciones que dependan de la aplicación, que por cierto no está en este contexto, al no existir todavía:

```bash
gerard@aldebaran:~/docker/nodetest/onbuild$ cat Dockerfile 
FROM node:6-slim
ONBUILD COPY app/ /srv/app/
ONBUILD WORKDIR /srv/app
ONBUILD RUN npm install --production
ONBUILD USER node
CMD ["npm", "start"]
gerard@aldebaran:~/docker/nodetest/onbuild$ 
```

Con este *Dockerfile* podemos generar una imagen base, que registre nuestras operaciones pendientes. Si construimos la imagen, veremos que no se ejecuta el `npm install`, ni las otras instrucciones precedidas por **ONBUILD**. Cualquier *Dockerfile* que extienda esta imagen base, conseguirá varias cosas:

* Va a disponer de todos los añadidos por instrucciones lanzadas sin el **ONBUILD**
* Inmediatamente tras el **FROM** se van a ejecutar las operaciones indicadas en el **ONBUILD** (el **COPY**, el **WORKDIR**, el **RUN** y el **USER**)
* El desarrollador no necesita declarar todas estas operaciones; solo va a necesitar aquellas que sean específicas de su proyecto.

Veamos el mismo ejemplo de antes; creamos un contexto con la misma aplicación y un *Dockerfile*, aunque este último queda bastante simplificado (suponiendo que la imagen base ha sido etiquetada como *gerard/node:onbuild*):

```bash
gerard@aldebaran:~/docker/nodetest/v2$ tree
.
├── app
│   ├── app.js
│   └── package.json
└── Dockerfile

1 directory, 3 files
gerard@aldebaran:~/docker/nodetest/v2$ cat Dockerfile 
FROM gerard/node:onbuild
gerard@aldebaran:~/docker/nodetest/v2$ 
```

Si la construimos, vemos que justo tras acabar el paso del **FROM**, van a saltar de forma automática los *triggers*  declarados por la instrucción **ONBUILD**.

```bash
gerard@aldebaran:~/docker/nodetest/v2$ docker build -t gerard/app:v2 .
Sending build context to Docker daemon  4.608kB
Step 1/1 : FROM gerard/node:onbuild
# Executing 4 build triggers...
Step 1/1 : COPY app/ /srv/app/
Step 1/1 : WORKDIR /srv/app
Step 1/1 : RUN npm install --production
 ---> Running in e3fe9e739e34
...  
Step 1/1 : USER node
 ---> Running in 3725eb574aff
 ---> d4661e9857e8
Removing intermediate container 7c9b3293ed2f
Removing intermediate container 7976c2b5aaaa
Removing intermediate container e3fe9e739e34
Removing intermediate container 3725eb574aff
Successfully built d4661e9857e8
Successfully tagged gerard/app:v2
gerard@aldebaran:~/docker/nodetest/v2$ 
```

Y con esto aseguramos que el desarrollador pasa por el aro, usando las instrucciones que realmente necesitamos para ejecutar la aplicación.
