Title: Aplicaciones gráficas en un contenedor
Slug: aplicaciones-graficas-en-un-contenedor
Date: 2018-01-08 10:00
Category: Miscelánea
Tags: docker, escritorio



A veces nos encontramos en un ordenador que no tenemos preparado para usar nuestras aplicaciones habituales, o simplemente no es el nuestro, o no queremos ensuciarlo para probar aplicaciones nuevas. Si disponemos de **docker**, es posible ejecutarlas compartiendo solamente el *unix socket* del servidor gráfico para verlas en nuestra pantalla.

El fichero *Dockerfile* no es distinto del que usaríamos para una aplicación sin entorno gráfico, bastando instalar el programa que queramos y confiando en que el sistema de dependencias del gestor de paquetes consiga lo que este necesite.

En este caso pongo un editor de lenguaje de marcado *markdown*, pero se podría poner un navegador, un juego o lo que queramos.

```bash
gerard@sirius:~/docker/retext$ cat Dockerfile 
FROM debian:jessie
RUN apt-get update && \
    apt-get install -y retext && \
    rm -rf /var/lib/apt/lists/*
RUN useradd gerard
USER gerard
CMD ["/usr/bin/retext"]
gerard@sirius:~/docker/retext$ 
```

Construimos la imagen de la misma forma en la que lo hacemos habitualmente, con el mismo comando *docker build* habitual:

```bash
gerard@sirius:~/docker/retext$ docker build -t retext .
Sending build context to Docker daemon 2.048 kB
Step 1 : FROM debian:jessie
 ---> 19134a8202e7
Step 2 : RUN apt-get update &&     apt-get install -y retext &&     rm -rf /var/lib/apt/lists/*
 ---> Running in bb0cdc51af3e
...
 ---> 1150d6a6a3e2
Removing intermediate container bb0cdc51af3e
Step 3 : RUN useradd gerard
 ---> Running in 97e1de7b50d3
 ---> 4d8f69d5f570
Removing intermediate container 97e1de7b50d3
Step 4 : USER gerard
 ---> Running in 29bb618fc788
 ---> 1a7388f29cda
Removing intermediate container 29bb618fc788
Step 5 : CMD /usr/bin/retext
 ---> Running in fefaa04ee25e
 ---> af856bcf0c49
Removing intermediate container fefaa04ee25e
Successfully built af856bcf0c49
gerard@sirius:~/docker/retext$ 
```

Si intentamos ejecutar esta imagen, veremos que falla; el contenedor no tiene acceso a los dispositivos, ni al *unix socket* en donde este se ejecuta. Tampoco tenemos definida la variable de sistema *DISPLAY*.

```bash
gerard@sirius:~/docker/retext$ docker run --rm retext
QXcbConnection: Could not connect to display 
gerard@sirius:~/docker/retext$ 
```

Por suerte podemos añadir ambos mediante *flags* durante la ejecución del contenedor. Vamos a añadir el *unix socket* del servidor gráfico mediante un volumen, y vamos a definir la variable *DISPLAY* en función de la que tengamos en la máquina anfitrión.

```bash
gerard@sirius:~/docker/retext$ docker run --rm -e "DISPLAY=$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix retext
...
```

Y ya podremos ver la aplicación corriendo como una ventana más en nuestra pantalla, sin problemas ni complicaciones.
