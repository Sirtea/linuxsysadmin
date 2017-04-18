Title: Administrando Docker vía web: Portainer
Slug: administrando-docker-via-web-portainer
Date: 2017-04-24 10:00
Category: Operaciones
Tags: docker, portainer



El otro día me topé con un desarrollador que quiere desplegar sus contenedores **Docker** en el servidor de integración, pero no conoce la sintaxis del comando *docker* y prefiere una interfaz gráfica. Eso me llevó a investigar, buscando una opción bonita, funcional y ligera; al final, me topé con **Portainer**.

Podemos encontrar la imagen en **DockerHub** en [este link](https://hub.docker.com/r/portainer/portainer/), así como una ligera descripción.

> Portainer is a lightweight management UI which allows you to easily manage your Docker host or Swarm cluster.
> Portainer is meant to be as simple to deploy as it is to use. It consists of a single container that can run on any Docker engine (Docker for Linux and Docker for Windows are supported).
> Portainer allows you to manage your Docker containers, images, volumes, networks and more ! It is compatible with the standalone Docker engine and with Docker Swarm.

## Instalación de portainer

Levantar el contenedor no tiene ningún misterio; basta con seguir las instrucciones de **DockerHub** y las que nos pueda ofrecer la aplicación. Empezaremos haciendo un `docker pull portainer/portainer`, para tener la imagen en local y maravillarnos de su ligereza: se trata solo de 10mb.

```bash
gerard@aldebaran:~/docker$ docker images
REPOSITORY            TAG                 IMAGE ID            CREATED             SIZE
portainer/portainer   latest              1ad990af4145        5 hours ago         9.96 MB
gerard@aldebaran:~/docker$ 
```

Mirando [la página web](http://portainer.io/install.html), vemos que levantar el contenedor no tiene ninguna dificultad; se trata de ejecutar la imagen tal cual, exponiendo el puerto 9000 a nuestra máquina *host* de **docker**, para su fácil acceso vía web. También le voy a dar un nombre de contenedor para su fácil administración.

```bash
gerard@aldebaran:~/docker$ docker run -d -p 9000:9000 --name portainer portainer/portainer
afcc57cfb1d0002d7e43cbdd5e6fcd0c6ada594eeac62132722e25cbb4569270
gerard@aldebaran:~/docker$ 
```

Apuntando el navegador a la dirección IP del *host*, con HTTP en el puerto 9000, vemos que ha levantado. La primera vez nos va a pedir una contraseña para el usuario *admin*, así que la rellenamos. Lo siguiente es declarar el **Docker Engine** o el **Docker Swarm** que queramos controlar. Como yo quiero controlar mi **Docker Engine** local, lo indico; y me salta una advertencia de que necesita el *unix socket* de **docker** mapeado en el contenedor.

> On Linux and when using Docker for Mac or Docker for Windows or Docker Toolbox, ensure that you have started Portainer container with the following Docker flag -v "/var/run/docker.sock:/var/run/docker.sock"

Esto significa parar el contenedor y levantarlo de nuevo con el nuevo volumen. También significa que vamos a tener que introducir la contraseña para el usuario *admin*. Mirando [la documentación](https://portainer.readthedocs.io/en/stable/deployment.html#persist-portainer-data), vemos que nos basta con poner la carpeta */data/* en un volumen del *host* para persistir las configuraciones.

Esto nos alarga la línea de comandos a ejecutar y empieza a ser tedioso de poner. Como siempre, **docker-compose** al poder.

```bash
gerard@aldebaran:~/docker/portainer$ cat docker-compose.yml
version: '2'
services:
  portainer:
    image: portainer/portainer
    container_name: portainer
    hostname: portainer
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./volumes/data:/data
    ports:
      - "9000:9000"
gerard@aldebaran:~/docker/portainer$ docker-compose up -d
Creating network "portainer_default" with the default driver
Creating portainer
gerard@aldebaran:~/docker/portainer$ 
```

Tras poner por última vez la contraseña del usuario *admin* e indicar que queremos controlar la instancia local, ya tenemos la interfaz ejecutando.

![Portainer dashboard]({filename}/images/portainer-dashboard.jpg)

En esta interfaz podremos lanzar todas las operaciones habituales cómodamente desde la web. Con ella podemos administrar las imágenes, los contenedores, las redes y los volúmenes.

**AVISO**: **Portainer** no tiene ningún sistema de persistencia y los comandos son enviados desde el formulario directamente al demonio de **Docker**; no se puede editar un contenedor creado, solo se puede recrearlo, de cero. Si os equivocáis, por ejemplo en una variable de entorno, no os queda más opción que recrear el contenedor entero.

## Plantillas

Las plantillas son formas bonitas de levantar imágenes. Nos permiten elegir las plantillas con botones y luego nos dan un formulario prefabricado para rellenar variables de entorno. Nada más.

Si usamos variables de entorno para configurar nuestros contenedores, son de gran ayuda. El conjunto básico de plantillas es muy limitado, pero se puede ampliar; nuevamente la respuesta está en [la documentación](https://portainer.readthedocs.io/en/stable/templates.html).

Muy a *grosso* modo, las plantillas disponibles se declaran en un fichero *templates.json*, que se descarga remotamente y se indica su localización con el *docker command* `--templates http://portainer-templates/templates.json`.

Este fichero se puede servir con cualquier servidor web del que dispongamos, o si no tenemos uno, podemos construir una imagen con **nginx**, por ejemplo. La documentación da detalles de como hacerlo.

Yo mismo he creado mi propio contenedor **nginx** para servir mi fichero de plantillas, con **Alpine Linux**. No voy a poner como porque no es el *scope* de este artículo, pero si voy a actualizar el fichero *docker-compose.yml* para ver el resultado final.

```bash
gerard@aldebaran:~/docker/portainer$ cat docker-compose.yml 
version: '2'
services:
  portainer:
    image: portainer/portainer
    container_name: portainer
    hostname: portainer
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./volumes/data:/data
    ports:
      - "9000:9000"
    command: --templates http://portainer-templates/templates.json
  portainer-templates:
    image: portainer-templates
    container_name: portainer-templates
    hostname: portainer-templates
    volumes:
      - ./volumes/templates/templates.json:/srv/www/templates.json:ro
gerard@aldebaran:~/docker/portainer$ docker-compose up -d
Creating portainer-templates
Creating portainer
gerard@aldebaran:~/docker/portainer$ 
```

Ahora solo queda crear un fichero con contenido adecuado de acuerdo a la documentación, que iremos actualizando a lo largo de la vida de nuestro proyecto. Solo voy a poner un *snippet* del fichero para que os hagáis una idea de como es:

```bash
gerard@aldebaran:~/docker/portainer$ cat volumes/templates/templates.json 
[
    {
        "title": "Kittens",
        "description": "A beautiful kitten listing",
        "logo": "https://s-media-cache-ak0.pinimg.com/736x/5d/bb/17/5dbb17d702b29b11f46d7a9c7ea53891.jpg",
        "image": "acme/kittens",
        "env": [
            {
                "name": "ENTORNO",
                "label": "ENTORNO"
            },
            {
                "name": "MONGO_URL",
                "label": "MONGO_URL"
            }
        ]
    },
    {
        "title": "MongoDB",
        "description": "MongoDB is a free and open-source cross-platform document-oriented database",
        "logo": "https://media.glassdoor.com/sqll/433703/mongodb-squarelogo-1407269491216.png",
        "image": "acme/mongo"
    }
]
gerard@aldebaran:~/docker/portainer$ 
```

En este caso dispondríamos de dos plantillas. La primera utiliza la imagen *acme/kittens* y necesita dos variables de entorno. La segunda utiliza la imagen *acme/mongo* y no necesita variables de entorno.
