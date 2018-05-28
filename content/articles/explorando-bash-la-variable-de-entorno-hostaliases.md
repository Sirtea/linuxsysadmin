Title: Explorando bash: la variable de entorno HOSTALIASES
Slug: explorando-bash-la-variable-de-entorno-hostaliases
Date: 2018-06-04 10:00
Category: Operaciones
Tags: bash, variable, HOSTALIASES



Muchas veces me he encontrado haciendo *demos* con aplicaciones ejecutando en local o en un contenedor. Otras tantas el cliente ha hecho un montón de preguntas tontas referentes a porqué pone *localhost*. En algunos de estos sistemas no disponía de acceso *root* o *sudo* para cambiar el fichero `/etc/hosts`.

En estos casos, es especialmente interesante conocer la variable de **bash** llamada **HOSTALIASES**. Se trata de una variable de entorno que define un *path* a un fichero, que va a ser una lista de *hosts* y su *alias*, aunque no soporta direcciones IP.

## Un ejemplo simple: falseando un servidor, con un servicio local

Tanto si os pongo un ejemplo en este *blog*, como si se trata de una *demo* para un cliente, es muy habitual esconder el hecho de que no hay un servidor dedicado ni virtual mediante la exposición del puerto de un contenedor.

Supongamos que tenemos un servidor web o de aplicaciones, empaquetado en una imagen **docker**. Para la *demo* lo ponemos a correr como contenedor. Como bien sabéis, buscar la dirección del contenedor suele ser pesado, así que optamos por exponer su puerto en la máquina local:

```bash
gerard@sirius:~$ curl http://localhost:8080/
Hello world
gerard@sirius:~$ 
```

**NOTA**: En realidad, el puerto 8080 de *localhost* va a parar el puerto 8080 del contenedor, cuya función es irrelevante ahora mismo.

Entonces viene el cliente, y en vez de fijarse en la aplicación misma, se fija en *localhost*, y empieza con las preguntas tontas habituales:

> ¿Por qué pone ahí localhost? Yo lo quiero en mi servidor, con redundancia y blah, blah, blah

Y aquí es cuando se nos hinchan las narices y decidimos engañarlo, mediante una resolución DNS, aunque sea simulada; como no tenemos acceso a los archivos del sistema y no queremos tampoco dejar basura en ellos, tiramos de la variable de entorno **HOSTALIASES**.

```bash
gerard@sirius:~$ cat hosts 
tuserver localhost
gerard@sirius:~$ export HOSTALIASES=~/hosts
gerard@sirius:~$ 
```

Y a partir de aquí, nadie tiene que enterarse de la localización exacta de la demo:

```bash
gerard@sirius:~$ curl http://tuserver:8080/
Hello world
gerard@sirius:~$ 
``` 

Y se acabaron las preguntas tontas fuera de contexto.
