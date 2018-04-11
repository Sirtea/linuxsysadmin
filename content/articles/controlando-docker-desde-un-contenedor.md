Title: Controlando Docker desde un contenedor
Slug: controlando-docker-desde-un-contenedor
Date: 2018-04-16 10:00
Category: Operaciones
Tags: docker, cliente, contenedor



Curioso de ver como mucho contenedores eran capaces de ver el contenido **Docker** de mi servidor, he decidido aprender como se hace, por si me hiciera falta en un futuro. En este artículo intento explicar las lecciones aprendidas, de forma que sean una futura referencia en caso de ser necesario.

El primer paso para conseguir mi objetivo era tener el binario `docker` en un contenedor. Una opción es copiarlo de mi servidor, junto con todas las dependencias; una opción más cuerda es aprovecharme de los paquetes existentes para ello.

Así pues, vamos a partir de un *Alpine Linux*, que por su tamaño, su seguridad y su magnífico gestor de paquetes, se hace el candidato ideal:

```bash
gerard@atlantis:~/projects/docker-client$ cat Dockerfile
FROM alpine:3.7
RUN apk add --no-cache docker && \
    rm /usr/bin/docker-proxy && \
    rm /usr/bin/docker-containerd-shim && \
    rm /usr/bin/docker-runc && \
    rm /usr/bin/docker-containerd-ctr && \
    rm /usr/bin/docker-containerd && \
    rm /usr/bin/dockerd
gerard@atlantis:~/projects/docker-client$
```

**TRUCO**: El paquete *docker* en *Alpine Linux* ocupa mucho espacio. Esto es debido a que incluye todos los binarios necesarios para ejecutar también el servidor. Como no nos interesa el servidor en un contenedor, los he eliminado.

Lo construímos para llegar a una imagen adecuada, que vamos a etiquetar *docker-client*:

```bash
gerard@atlantis:~/projects/docker-client$ docker build -t docker-client .
Sending build context to Docker daemon  2.048kB
...
Successfully built 583d47952c7a
Successfully tagged docker-client:latest
gerard@atlantis:~/projects/docker-client$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
docker-client       latest              583d47952c7a        7 seconds ago       30.2MB
alpine              3.7                 3fd9065eaf02        4 weeks ago         4.15MB
gerard@atlantis:~/projects/docker-client$
```

La ejecución de un contenedor desde la nueva imagen nos permite usar el comando `docker`, aunque los resultados no son los esperados.

```bash
gerard@atlantis:~/projects/docker-client$ docker run -ti --rm docker-client
/ # docker images
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
/ #
```

Esto es debido a que el cliente de **Docker** se comunica con el servidor mediante un *unix socket* que, al no tener el servicio corriendo, no está creado.

Como sabemos, **absolutamente todo** en *Linux* es un fichero, y podemos montar ficheros desde el servidor como *host volumes*. Por ejemplo:

```bash
gerard@atlantis:~/projects/docker-client$ docker run -ti --rm -v /var/run/docker.sock:/var/run/docker.sock docker-client
/ # docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
docker-client       latest              583d47952c7a        5 minutes ago       30.2MB
alpine              3.7                 3fd9065eaf02        4 weeks ago         4.15MB
/ #
```

El resultado es que vemos el contenido del servidor **Docker** del *host*, justo como queríamos. Cabe decir que no solo podemos listar las imágenes del *host*, sino que podemos controlar el ciclo de vida de un contenedor (`docker run`, `docker start`, `docker restart`, `docker stop`) e incluso ejecutar en ellos cosas (`docker exec`).

Esto va a tener muchas aplicaciones prácticas en el futuro, seguro...
