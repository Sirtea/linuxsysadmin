Title: Evolucionando los contenedores: Docker
Slug: evolucionando-los-contenedores-docker
Date: 2016-05-23 08:00
Category: Virtualización
Tags: linux, docker, contenedor, dockerfile, jaula



Los contenedores tienen su caso de uso y son muy útiles. Sin embargo, ir copiando la imagen es una pérdida de tiempo. Aunque podemos solventar el problema con un sistema de ficheros *copy-on-write* o un sistema de ficheros tipo *union*, **Docker** ya nos lo ofrece todo preparado para su uso.

**Docker** trabaja con imágenes, que no son otra cosa que jaulas en donde tienen todo lo que necesitan para ejecutar su contenido. Estas imágenes se forman a partir de capas que se muestran como una sola mediante **aufs**. Esto nos permite construir jaulas a partir de otras, ahorrando duplicidad de ficheros en disco y aligerando sus instancias.

Nuestro contenedor no es otra cosa que una capa de cambios (inicialmente vacía) montada encima de la imagen mediante **aufs**. Esta capa se elimina cuando el contenedor se destruye. El coste de crear el contenedor es prácticamente nulo, y no se modifica nunca la imagen base.

La gran diferencia con otras tecnologías, por ejemplo **LXC**, es su filosofía: un contenedor **Docker** ejecuta un solo comando, acabando la ejecución cuando este acaba.

## Instalación y verificación

La instalación es tan simple como seguir [la documentación](https://docs.docker.com/linux/step_one/). Así lo instalé en mi *netbook*:

```bash
gerard@sirius:~$ curl -fsSL https://get.docker.com/ | sh
...
gerard@sirius:~$ 
```

Comprobamos su funcionamiento, por ejemplo, levantando una imagen cualquiera.

```bash
gerard@sirius:~$ docker run -ti --rm debian echo 'Hello world'
Unable to find image 'debian:latest' locally
latest: Pulling from library/debian
8b87079b7a06: Pull complete 
a3ed95caeb02: Pull complete 
Digest: sha256:c8bdce9b6166fcd287c1336f5cd6262971f7f0e98db07c93c23d540a7a19cd96
Status: Downloaded newer image for debian:latest
Hello world
gerard@sirius:~$ 
```

Podemos ver en la salida del comando que no teníamos una imagen local de la imagen *debian*, con lo que la ha descargado. Podemos ver que ya la tenemos en local, y que si volvemos a lanzar el comando, no se descarga de nuevo.

```bash
gerard@sirius:~$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
debian              latest              bb5d89f9b6cb        4 days ago          125.1 MB
gerard@sirius:~$ docker run -ti --rm debian echo 'Hello world'
Hello world
gerard@sirius:~$ 
```

## Mejorando las imágenes con capas

Las imágenes que podemos encontrar en [Docker Hub](https://hub.docker.com/) son básicas; por ejemplo vienen sin un servidor **ssh** y sin **python**.

```bash
gerard@sirius:~$ docker run -ti --rm debian python -V
docker: Error response from daemon: Container command 'python' not found or does not exist..
            gerard@sirius:~$ 
```

Normalmente nos va a interesar trabajar con imágenes que ya contengan algunas de nuestras utilidades habituales. Para ello podemos construir una imagen a partir de otra que ya tengamos.

Para ampliar una imagen modificando otra hay dos formas, que se explican a continuación. Para entender los ejemplos, vamos a suponer que ampliamos la imagen *debian* con el paquete *python*.

### Creando una imagen instalando manualmente las diferencias

Para hacer esta, se necesita levantar un contenedor que vamos a modificar. Luego localizamos el identificador del contenedor y le damos un *commit*.

Empezamos de la imagen base *debian*, a la que instalamos los paquetes necesarios. En este caso, vamos a poner *python*.

```bash
gerard@sirius:~$ docker run -ti --rm debian
root@23c4caa12410:/# apt-get update
...
root@23c4caa12410:/# apt-get install -y python
...
root@23c4caa12410:/# 
```

Ahora, y desde otro terminal, buscamos el identificador del contenedor.

```bash
gerard@sirius:~$ docker ps
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
23c4caa12410        debian              "/bin/bash"         4 minutes ago       Up 4 minutes                            backstabbing_poincare
gerard@sirius:~$ 
```

Teniendo el identificador del contenedor, podemos hacer un *commit* y podemos ponerle un *tag* para referencias futuras.

```bash
gerard@sirius:~$ docker commit 23c4caa12410
sha256:f73b2072ab7404b83749fd098411a1c6392631668363c46fc7203d1a0d39782f
gerard@sirius:~$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
<none>              <none>              f73b2072ab74        9 seconds ago       167.4 MB
debian              latest              bb5d89f9b6cb        4 days ago          125.1 MB
gerard@sirius:~$ docker tag f73b2072ab74 python-debian-manual
gerard@sirius:~$ docker images
REPOSITORY             TAG                 IMAGE ID            CREATED              SIZE
python-debian-manual   latest              f73b2072ab74        About a minute ago   167.4 MB
debian                 latest              bb5d89f9b6cb        4 days ago           125.1 MB
gerard@sirius:~$ 
```

Y comprobamos que funciona como debe:

```bash
gerard@sirius:~$ docker run -ti --rm python-debian-manual python -V
Python 2.7.9
gerard@sirius:~$ 
```

### Creando una imagen automáticamente mediante Dockerfiles

Para este método vamos a usar el comando **docker build** que construye una imagen a partir de un *Dockerfile*, que le sirve de receta, y construye imágenes a partir de otras.

Supongamos que tenemos el siguiente *Dockerfile*:

```bash
gerard@sirius:~/build$ cat Dockerfile 
FROM debian
RUN apt-get update && \
    apt-get install -y python
CMD ["/bin/bash"]
gerard@sirius:~/build$ 
```

Bastaría crear la imágen en la carpeta actual con el comando mencionado, especificando opcionalmente el *tag*:

```bash
gerard@sirius:~/build$ docker build -t python-debian-auto .
Sending build context to Docker daemon 2.048 kB
Step 1 : FROM debian
 ---> bb5d89f9b6cb
Step 2 : RUN apt-get update &&     apt-get install -y python
 ---> Running in 4e975dc297fc
...  
 ---> 39025d968357
Removing intermediate container 4e975dc297fc
Step 3 : CMD /bin/bash
 ---> Running in 7331c2d109db
 ---> e52f43de8b80
Removing intermediate container 7331c2d109db
Successfully built e52f43de8b80
gerard@sirius:~/build$ 
```

Comprobamos que tenemos una imagen nueva y que funciona.

```bash
gerard@sirius:~/build$ docker images
REPOSITORY             TAG                 IMAGE ID            CREATED             SIZE
python-debian-auto     latest              e52f43de8b80        6 minutes ago       176 MB
python-debian-manual   latest              f73b2072ab74        22 minutes ago      167.4 MB
debian                 latest              bb5d89f9b6cb        4 days ago          125.1 MB
gerard@sirius:~/build$ docker run -ti --rm python-debian-auto python -V
Python 2.7.9
gerard@sirius:~/build$ 
```

## Creando una imagen desde cero

Hay veces en las que no queremos usar imágenes de dudoso origen, y queremos hacer una nuestra. En estos casos solo hay que saber que una imagen no es otra cosa que una jaula normal. Podemos hacer esto partiendo de una imagen vacía, pensada para estos casos.

Como ejemplo, vamos a crear una jaula con lo necesario para correr un solo comando: el ejemplo que utilizamos en [otro artículo]({filename}/articles/reduciendo-el-tamano-de-nuestros-binarios-con-musl-libc.md).

Vamos a utilizar el método del *Dockerfile*, añadiendo el binario estático.

```bash
gerard@sirius:~/build$ cat Dockerfile 
FROM scratch
ADD hello /
CMD ["/hello"]
gerard@sirius:~/build$ 
```

Construimos la imagen y vemos que ocupa lo mismo que el binario que le hemos puesto.

```bash
gerard@sirius:~/build$ docker build -t saluda .
Sending build context to Docker daemon 20.34 MB
Step 1 : FROM scratch
 ---> 
Step 2 : ADD hello /
 ---> 83da41eee33c
Removing intermediate container 5ea901ba61be
Step 3 : CMD /hello
 ---> Running in 54d7512dd61a
 ---> bf6c560144dd
Removing intermediate container 54d7512dd61a
Successfully built bf6c560144dd
gerard@sirius:~/build$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
saluda              latest              bf6c560144dd        25 seconds ago      5.416 kB
debian              latest              47af6ca8a14a        3 weeks ago         125.1 MB
gerard@sirius:~/build$ 
```

Probamos que funciona, como ya viene siendo costumbre:

```bash
gerard@sirius:~/build$ docker run --rm -ti saluda
Hello world!
gerard@sirius:~/build$ 
```
