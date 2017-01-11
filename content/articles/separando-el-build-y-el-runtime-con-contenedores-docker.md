Title: Separando el build y el runtime con contenedores Docker
Slug: separando-el-build-y-el-runtime-con-contenedores-docker
Date: 2016-10-10 08:00
Category: Operaciones
Tags: docker, python, build, runtime, release



Cuando montamos un contenedor **Docker** para servir una aplicación cualquiera, solemos poner un montón de dependencias necesarias solamente para compilar el paquete o para empaquetar sus librerías. Esto supone un gasto innecesario en espacio y en tiempo de ejecución; usando contenedores desechables podemos agilizar este proceso de forma altamente considerable.

Para ello vamos a partir de una aplicación simplista hecha con **python** que podemos encontrar en <https://github.com/Sirtea/autobuilder>. La idea es que vamos a preparar las dependencias en un contenedor, para luego sacar lo justo y necesario para poner en un contenedor que disponga solamente de lo justo para el *runtime*.

Para simplificar mas todavía, vamos a separar el código base del contenedor, de forma que este pueda ir cambiando modificando solamente un parámetro dado. Vamos a delegar la descarga y compilación del código base a un *script*, que no cambie y que permita trabajar con las diferentes versiones de nuestra aplicación.

Para que todo esto funcione, necesitamos seguir una cantidad mínima de reglas, que van a poderse cumplir independientemente del proyecto o del *framework* usado.

* En la base del repositorio hay un *requirements.txt* que nos va a indicar las librerías necesarias.
* La aplicación quedará alojada en una carpeta *app*, el módulo con la aplicación se va a llamar *app* (módulo o *package*) y el *callable* también se va a llamar *app*.
* El *virtualenv* se va aconstruir en */app/env*, para su uso futuro, en tiempo de *runtime*.

Vamos a empezar construyendo una carpeta contenedora de las dos imágenes que vamos a usar, separadas a su vez por otro nivel de carpetas.

```bash
gerard@sirius:~/docker/autobuilder$ tree
.
├── builder
│   ├── build.sh
│   └── Dockerfile
└── runner
    ├── app.ini
    └── Dockerfile

2 directories, 4 files
gerard@sirius:~/docker/autobuilder$ 
```

## La imagen de build

La filosofía es muy simple: crearemos una imagen que tenga todas las dependencias necesarias para la construcción de la aplicación (en nuestro caso el *virtualenv*), y vamos a poner un *script* llamado *build.sh* que se va a encargar de clonar un repositorio en [GitHub](https://github.com/) y va a construir una refererencia tambien indicada mediante variables de entorno.

```bash
gerard@sirius:~/docker/autobuilder$ cat builder/Dockerfile 
FROM alpine:3.4
RUN apk add --no-cache py-virtualenv git gcc musl-dev python-dev
COPY build.sh /
ENTRYPOINT ["sh", "build.sh"]
gerard@sirius:~/docker/autobuilder$ 
```

El *script* de *build* va a depender bastante de como se prepara nuestra aplicación. En este caso va a clonar el repositorio en una carpeta */build*, y va a copiar la referencia solicitada en una carpeta */app*, que luego va a ser acompañada con un *virtualenv*. Puesto que el *virtualenv* es dependiente de la localización en el servidor, vamos a usar también */app* en la máquina de *runtime*. En este paso es cuando hace falta usar la convención del fichero *requirements.txt*.

```bash
gerard@sirius:~/docker/autobuilder$ cat builder/build.sh 
#!/bin/sh

mkdir /app
git clone ${REPO} /build
cd /build
git archive ${REF} | tar xf - -C /app
virtualenv /app/env
/app/env/bin/pip install -r /app/requirements.txt
tar czf /shared/app.tar.gz -C / app
gerard@sirius:~/docker/autobuilder$ 
```

La idea es que el producto acabado quede comprimido en la carpeta */shared*. Personalmente he utilizado un fichero *.tar.gz*, pero se podría haber utilizado ficheros *.deb*, *.rpm* o lo que hiciera falta.

Falta construir la imagen a partir de los ficheros dados:

```bash
gerard@sirius:~/docker/autobuilder/builder$ docker build -t builder .
Sending build context to Docker daemon 3.072 kB
Step 1 : FROM alpine:3.4
3.4: Pulling from library/alpine
Digest: sha256:3dcdb92d7432d56604d4545cbd324b14e647b313626d99b889d0626de158f73a
Status: Downloaded newer image for alpine:3.4
 ---> 4e38e38c8ce0
Step 2 : RUN apk add --no-cache py-virtualenv git gcc musl-dev python-dev
 ---> Running in 36ab40f2fbc6
fetch http://dl-cdn.alpinelinux.org/alpine/v3.4/main/x86_64/APKINDEX.tar.gz
fetch http://dl-cdn.alpinelinux.org/alpine/v3.4/community/x86_64/APKINDEX.tar.gz
(1/35) Upgrading musl (1.1.14-r10 -> 1.1.14-r11)
(2/35) Installing binutils-libs (2.26-r0)
(3/35) Installing binutils (2.26-r0)
(4/35) Installing gmp (6.1.0-r0)
(5/35) Installing isl (0.14.1-r0)
(6/35) Installing libgomp (5.3.0-r0)
(7/35) Installing libatomic (5.3.0-r0)
(8/35) Installing libgcc (5.3.0-r0)
(9/35) Installing pkgconf (0.9.12-r0)
(10/35) Installing pkgconfig (0.25-r1)
(11/35) Installing mpfr3 (3.1.2-r0)
(12/35) Installing mpc1 (1.0.3-r0)
(13/35) Installing libstdc++ (5.3.0-r0)
(14/35) Installing gcc (5.3.0-r0)
(15/35) Installing ca-certificates (20160104-r4)
(16/35) Installing libssh2 (1.7.0-r0)
(17/35) Installing libcurl (7.50.1-r0)
(18/35) Installing expat (2.1.1-r1)
(19/35) Installing pcre (8.38-r1)
(20/35) Installing git (2.8.3-r0)
(21/35) Upgrading musl-utils (1.1.14-r10 -> 1.1.14-r11)
(22/35) Installing musl-dev (1.1.14-r11)
(23/35) Installing libbz2 (1.0.6-r4)
(24/35) Installing libffi (3.2.1-r2)
(25/35) Installing gdbm (1.11-r1)
(26/35) Installing ncurses-terminfo-base (6.0-r7)
(27/35) Installing ncurses-terminfo (6.0-r7)
(28/35) Installing ncurses-libs (6.0-r7)
(29/35) Installing readline (6.3.008-r4)
(30/35) Installing sqlite-libs (3.13.0-r0)
(31/35) Installing python (2.7.12-r0)
(32/35) Installing py-setuptools (20.8.0-r0)
(33/35) Installing py-pip (8.1.2-r0)
(34/35) Installing py-virtualenv (15.0.1-r0)
(35/35) Installing python-dev (2.7.12-r0)
Executing busybox-1.24.2-r9.trigger
Executing ca-certificates-20160104-r4.trigger
OK: 169 MiB in 44 packages
 ---> 86bd30dae926
Removing intermediate container 36ab40f2fbc6
Step 3 : COPY build.sh /
 ---> bb87e7021b1f
Removing intermediate container d1c160839571
Step 4 : ENTRYPOINT sh build.sh
 ---> Running in ec43f4786949
 ---> 9887ce973fe2
Removing intermediate container ec43f4786949
Successfully built 9887ce973fe2
gerard@sirius:~/docker/autobuilder/builder$ 
```

Esta imagen no se va a reconstruir -en principio- nunca. Las diferentes ejecuciones van a producir diferentes productos.

## La imagen de runtime

Esta imagen es todavía mas fácil; se trata de un servidor de aplicaciones estándar que va a servir la aplicación siguiendo las reglas descritas mas arriba.

Vamos a asumir que tenemos el *bundle* construido y llamado *app.tar.gz*, así que solo faltaría descomprimirlo para que quede todo en */app*.

```bash
gerard@sirius:~/docker/autobuilder/runner$ cat Dockerfile 
FROM alpine:3.4
RUN apk add --no-cache uwsgi-python
ADD app.tar.gz /
COPY app.ini /app/
ENTRYPOINT ["uwsgi", "--ini", "/app/app.ini"]
gerard@sirius:~/docker/autobuilder/runner$ 
```

El fichero que va a servir la aplicación depende de cada servidor de aplicaciones, y de momento, nos vale un sencillo. En este punto se vuelve especialmente importante respetar las convenciones del *virtualenv* y de la localización de la aplicación.

```bash
gerard@sirius:~/docker/autobuilder/runner$ cat app.ini 
[uwsgi]
http-socket = :8080
plugin = python
chdir = /app/app/
virtualenv = /app/env/
module = app:app
gerard@sirius:~/docker/autobuilder/runner$ 
```

## La hora de la release

Ha llegado el momento de hacer una *release*; así que vamos a hacer el *bundle* y la imagen de servicio, para luego poder servirlo. Este paso se va a repetir muy a menudo, dependiendo de la política de *releases* de vuestra compañía. Para obtener el *bundle*, necesitamos compilar la referencia del repositorio.

```bash
gerard@sirius:~/docker/autobuilder/runner$ docker run -ti --rm -e "REPO=https://github.com/Sirtea/autobuilder.git" -e "REF=v1.0.0" -v /home/gerard/docker/autobuilder/runner/:/shared/ builder
Cloning into '/build'...
remote: Counting objects: 10, done.
remote: Compressing objects: 100% (9/9), done.
remote: Total 10 (delta 0), reused 10 (delta 0), pack-reused 0
Unpacking objects: 100% (10/10), done.
Checking connectivity... done.
New python executable in /app/env/bin/python
Installing setuptools, pip, wheel...done.
Collecting click==6.6 (from -r /app/requirements.txt (line 1))
  Downloading click-6.6.tar.gz (283kB)
    100% |████████████████████████████████| 286kB 536kB/s 
Collecting Flask==0.11.1 (from -r /app/requirements.txt (line 2))
  Downloading Flask-0.11.1-py2.py3-none-any.whl (80kB)
    100% |████████████████████████████████| 81kB 809kB/s 
Collecting itsdangerous==0.24 (from -r /app/requirements.txt (line 3))
  Downloading itsdangerous-0.24.tar.gz (46kB)
    100% |████████████████████████████████| 51kB 724kB/s 
Collecting Jinja2==2.8 (from -r /app/requirements.txt (line 4))
  Downloading Jinja2-2.8-py2.py3-none-any.whl (263kB)
    100% |████████████████████████████████| 266kB 861kB/s 
Collecting MarkupSafe==0.23 (from -r /app/requirements.txt (line 5))
  Downloading MarkupSafe-0.23.tar.gz
Collecting mongoengine==0.10.6 (from -r /app/requirements.txt (line 6))
  Downloading mongoengine-0.10.6.tar.gz (346kB)
    100% |████████████████████████████████| 348kB 803kB/s 
Collecting pymongo==3.3.0 (from -r /app/requirements.txt (line 7))
  Downloading pymongo-3.3.0.tar.gz (494kB)
    100% |████████████████████████████████| 501kB 753kB/s 
Collecting Werkzeug==0.11.10 (from -r /app/requirements.txt (line 8))
  Downloading Werkzeug-0.11.10-py2.py3-none-any.whl (306kB)
    100% |████████████████████████████████| 307kB 1.1MB/s 
Building wheels for collected packages: click, itsdangerous, MarkupSafe, mongoengine, pymongo
  Running setup.py bdist_wheel for click ... done
  Stored in directory: /root/.cache/pip/wheels/b0/6d/8c/cf5ca1146e48bc7914748bfb1dbf3a40a440b8b4f4f0d952dd
  Running setup.py bdist_wheel for itsdangerous ... done
  Stored in directory: /root/.cache/pip/wheels/fc/a8/66/24d655233c757e178d45dea2de22a04c6d92766abfb741129a
  Running setup.py bdist_wheel for MarkupSafe ... done
  Stored in directory: /root/.cache/pip/wheels/a3/fa/dc/0198eed9ad95489b8a4f45d14dd5d2aee3f8984e46862c5748
  Running setup.py bdist_wheel for mongoengine ... done
  Stored in directory: /root/.cache/pip/wheels/ae/6d/cb/4573bb9aceaed483557761df59571c6a3f108e87a80d2ba03a
  Running setup.py bdist_wheel for pymongo ... done
  Stored in directory: /root/.cache/pip/wheels/bf/f7/14/6ed22fbc276fc2d9fa7cdb2235dea8d5f154d711dfdf4bdebe
Successfully built click itsdangerous MarkupSafe mongoengine pymongo
Installing collected packages: click, MarkupSafe, Jinja2, Werkzeug, itsdangerous, Flask, pymongo, mongoengine
Successfully installed Flask-0.11.1 Jinja2-2.8 MarkupSafe-0.23 Werkzeug-0.11.10 click-6.6 itsdangerous-0.24 mongoengine-0.10.6 pymongo-3.3.0
gerard@sirius:~/docker/autobuilder/runner$ 
```

Puesto que el *script* llamado *build.sh* deja el fichero *.tar.gz* en */shared*, y este es un volumen montado en la carpeta actual, vemos que nos aparece nuestro producto compilado.

```bash
gerard@sirius:~/docker/autobuilder$ tree
.
├── builder
│   ├── build.sh
│   └── Dockerfile
└── runner
    ├── app.ini
    ├── app.tar.gz
    └── Dockerfile

2 directories, 5 files
gerard@sirius:~/docker/autobuilder$ 
```

Efectivamente, este *bundle* contiene la aplicación y el *virtualenv* en la forma requerida, así que el siguiente paso es construir la imagen de *runtime* con este *bundle* incorporado.

```bash
gerard@sirius:~/docker/autobuilder/runner$ docker build -t runner .
Sending build context to Docker daemon 5.027 MB
Step 1 : FROM alpine:3.4
 ---> 4e38e38c8ce0
Step 2 : RUN apk add --no-cache uwsgi-python
 ---> Running in 9233d11f6646
fetch http://dl-cdn.alpinelinux.org/alpine/v3.4/main/x86_64/APKINDEX.tar.gz
fetch http://dl-cdn.alpinelinux.org/alpine/v3.4/community/x86_64/APKINDEX.tar.gz
(1/14) Installing mailcap (2.1.44-r0)
(2/14) Installing pcre (8.38-r1)
(3/14) Installing uwsgi (2.0.13-r0)
(4/14) Installing libbz2 (1.0.6-r4)
(5/14) Installing expat (2.1.1-r1)
(6/14) Installing libffi (3.2.1-r2)
(7/14) Installing gdbm (1.11-r1)
(8/14) Installing ncurses-terminfo-base (6.0-r7)
(9/14) Installing ncurses-terminfo (6.0-r7)
(10/14) Installing ncurses-libs (6.0-r7)
(11/14) Installing readline (6.3.008-r4)
(12/14) Installing sqlite-libs (3.13.0-r0)
(13/14) Installing python (2.7.12-r0)
(14/14) Installing uwsgi-python (2.0.13-r0)
Executing busybox-1.24.2-r9.trigger
OK: 53 MiB in 25 packages
 ---> b7c2de7c84d1
Removing intermediate container 9233d11f6646
Step 3 : ADD app.tar.gz /
 ---> 9b8046268ece
Removing intermediate container 0a5f930580a2
Step 4 : COPY app.ini /app/
 ---> 345641630c11
Removing intermediate container 8b0fe594e89d
Step 5 : ENTRYPOINT uwsgi --ini /app/app.ini
 ---> Running in 586c9d5f49ae
 ---> a83cfc054bdc
Removing intermediate container 586c9d5f49ae
Successfully built a83cfc054bdc
gerard@sirius:~/docker/autobuilder/runner$ 
```

Y con esto tenemos nuestra imagen.

## Ejecutando la imagen

Esta parte no tiene mucho misterio; basta con ejecutar la imagen como lo haríamos normalmente. Esta aplicación en concreto lee las configuraciones desde las variables de entorno, así que se las ponemos. En este caso particular, tenemos la imagen de **Docker Hub** [mongo](https://hub.docker.com/_/mongo/) en la dirección *IP* indicada.

```bash
gerard@sirius:~/docker/autobuilder/runner$ docker run -ti --rm -p 8888:8080 -e "MONGODB_URI=mongodb://172.17.0.2:27017/shop" runner
...
```

Podemos comprobar que todo funciona lanzando una petición *HTTP* estándar:

```bash
gerard@sirius:~$ curl http://localhost:8888/
<h1>Fruits</h1>
<ul>
<li>Apple</li>
<li>Orange</li>
<li>Pear</li>
</ul>
gerard@sirius:~$ 
```

Y ahora podemos ver que la imagen de *runtime* queda mucho mas reducida, mas rápida de construir y sin tanto *bloat*. Supongo que podemos reducir mas lo que ocupa la imagen seleccionando versiones de **python** alternativas; el sistema operativo base son solo 4.8mb...

```bash
gerard@sirius:~/docker/autobuilder/runner$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
runner              latest              e190cce7685a        31 seconds ago      60.75 MB
builder             latest              edf62460d187        7 minutes ago       164 MB
gerard@sirius:~/docker/autobuilder/runner$ 
```

De hecho, la *cache* de **Docker** funciona a las mil maravillas en este caso; si hubiera que reconstruir la imagen de *runtime*, se ejecutarían solo los pasos 3, 4 y 5. Esto convierte el hecho de "hacer una *release*" en casi inmediato.
