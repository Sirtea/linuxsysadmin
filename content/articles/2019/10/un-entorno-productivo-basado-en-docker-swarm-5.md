---
title: "Un entorno productivo basado en Docker Swarm (V)"
slug: "un-entorno-productivo-basado-en-docker-swarm-5"
date: "2019-10-14"
categories: ['Sistemas']
tags: ['linux', 'entorno', 'docker', 'swarm', 'deployment', 'python', 'falcon', 'httpie']
series: "Un entorno productivo basado en Docker Swarm"
---

En los anteriores artículos de la serie vimos como montar un entorno entero basado
en **docker swarm**; añadimos un par de servicios de infraestructura básica, como
son el balanceador y un *cluster* de bases de datos. Eran pasos que se hacen una
sola vez y raramente se modifican. Ahora toca provisionar aplicaciones, en un proceso
que vamos a repetir frecuentemente.<!--more-->

Y es que ha llegado el momento de la verdad: nuestros desarrolladores han completado
una *release*, y nos toca ponerla en funcionamiento. Para el caso, vamos a suponer
que se trata de una API de gatitos, que nos permite (en su primera versión) proveer
las operaciones más básicas de alta, baja, modificación y consulta.

**NOTA**: La aplicación usada [es esta][1], que está hecha con **python** y
**falcon**; con ella ilustro los ejemplos, aunque podéis escribir la vuestra propia
en el lenguaje que más os apetezca.

Normalmente tendríamos un *toolkit* para descargar el código de algún repositorio,
compilar lo que tocara, crear la imagen de **docker** y publicar en algún registro;
para no complicar el asunto en exceso, voy a hacer estos pasos manualmente.

## Etapa de *build*

El *tarball* con el código, o el clon del repositorio no nos sirven demasiado;
queremos imagenes **docker** en un registro para que el *cluster* pueda hacer los
respectivos `docker pull`. Así pues tenemos que hacer un `docker build` y el
correspondiente `docker push`.

No tenemos un registro privado, pero es fácil de hacer, tanto su [uso simple][2],
como un uso profesional [con autenticación y SSL][3]. Por simplicidad, voy a
utilizar [Docker Hub][4], aunque será solo de forma temporal; luego eliminaré la imagen.

Empezamos con el *build*:

```bash
gerard@builder:~/kittenapi$ docker build -t sirrtea/kittenapi .
...
Successfully built 008e3cc7144a
Successfully tagged sirrtea/kittenapi:latest
gerard@builder:~/kittenapi$ 
```

Asumiendo que ya hemos creado el repositorio en **Docker Hub**, solo necesitamos
hacer un *push*, para que la imagen esté disponible en un registro accesible
por todas la partes que lo puedan necesitar.

```bash
gerard@builder:~/kittenapi$ docker login
Login with your Docker ID to push and pull images from Docker Hub. If you don't have a Docker ID, head over to https://hub.docker.com to create one.
Username: sirrtea
Password: 
...
Login Succeeded
gerard@builder:~/kittenapi$ 
```

```bash
gerard@builder:~/kittenapi$ docker push sirrtea/kittenapi
The push refers to repository [docker.io/sirrtea/kittenapi]
...
latest: digest: sha256:4116e4398a0e2852b0dd2dad0b6d080af9711f107400eaefaf644edeb5f0bf7a size: 1365
gerard@builder:~/kittenapi$ 
```

## Un usuario para el acceso a la base de datos

Nuestra nueva aplicación necesita una nueva base de datos **mongodb**. Ya creamos
el *cluster* en un artículo anterior, pero es necesario crearle el usuario porque
activamos la autenticación y, sin autenticarse, no va a poder hacer nada.

Para ello necesitamos buscar el nodo primario del *cluster*, ya que la creación
de un usuario es una escritura, que solo se acepta en un primario. Nos conectamos
a un nodo cualquiera, nos autenticamos como *admin* y sacamos un `rs.status()`;
con la salida es trivial saber cuál es el primario, al que nos vamos a conectar.

```bash
gerard@docker05:~$ docker ps
CONTAINER ID        IMAGE                  COMMAND                  CREATED              STATUS              PORTS               NAMES
077a6f40b30e        sirrtea/mongo:debian   "/usr/bin/mongod --c…"   About a minute ago   Up About a minute                       mongo_mongo02.1.ralisf5jh5etw5yc0fx3q95wi
gerard@docker05:~$ docker exec -ti 077a6f40b30e mongo
MongoDB shell version v4.0.11
...
rs:SECONDARY> use admin
switched to db admin
rs:SECONDARY> db.auth("admin", "s3cr3t")
1
rs:SECONDARY> rs.status()
...
	"members" : [
		{
...
			"name" : "mongo01:27017",
...
			"stateStr" : "PRIMARY",
...
rs:SECONDARY> 
```

Nos conectamos al primario, nos autenticamos y creamos un usuario para nuestra nueva
aplicación, con el nombre de la base de datos, el usuario y la *password* que veamos
conveniente. En mi caso, el nombre de la base de datos y el usuario coinciden;
la contraseña ha sido autogenerada.

```bash
gerard@docker04:~$ docker ps
CONTAINER ID        IMAGE                  COMMAND                  CREATED             STATUS              PORTS               NAMES
092ce50d0bf6        sirrtea/mongo:debian   "/usr/bin/mongod --c…"   5 minutes ago       Up 5 minutes                            mongo_mongo01.1.uy2lcliipqo7glhp5y5miymq8
gerard@docker04:~$ docker exec -ti 092ce50d0bf6 mongo admin
...
rs:PRIMARY> db.auth("admin", "s3cr3t")
1
rs:PRIMARY> db.createUser({user: "kittenapi", pwd: "LCg1SMxoWDg7gkuQ", roles: [{role: "readWrite", db: "kittenapi"}]})
Successfully added user: {
	"user" : "kittenapi",
	"roles" : [
		{
			"role" : "readWrite",
			"db" : "kittenapi"
		}
	]
}
rs:PRIMARY> 
```

Y con esto ya tenemos un usuario para trabajar con la base de datos de la aplicación.

## Desplegando el servicio en el *swarm*

Para mantener una estructura similar al resto de artículos, vamos a suponer que tenemos
un clon del repositorio de ficheros de *stack*, con una carpeta para la base de datos,
una carpeta para los balanceadores, y una carpeta para cada aplicación, como sigue:

```bash
gerard@docker01:~$ mkdir kittenapi
gerard@docker01:~$ cd kittenapi/
gerard@docker01:~/kittenapi$ 
```

La aplicación en sí misma no es muy compleja; no necesita secretos, ni configuraciones;
solamente tenemos que aplicar las variables de entorno para configurar la aplicación,
y las *labels* necesarias para que **traefik** lo reconozca. Haciendo memoria, este
contenedor necesita estar conectada a las 2 redes creadas:

* A la red *frontend*, para que **traefik** le pueda pasar peticiones.
* A la red *backend*, que le garantiza acceso a la base de datos.

**TRUCO**: Se recomienda que no se ejecuten aplicaciones en los *managers* y que
se utilicen solo para gestionar el *cluster*; en mi caso también deben alojar los
contenedores de **traefik**. La forma para limitar el deploy es usando *labels*.

```bash
gerard@docker01:~/kittenapi$ docker node update --label-add usage=apps docker04
docker04
gerard@docker01:~/kittenapi$ docker node update --label-add usage=apps docker05
docker05
gerard@docker01:~/kittenapi$ docker node update --label-add usage=apps docker06
docker06
gerard@docker01:~/kittenapi$ 
```

De esta forma podemos escribir un fichero tipo *compose* de este estilo:

```bash
gerard@docker01:~/kittenapi$ cat kittenapi.yml 
version: '3'
services:
  kittenapi:
    image: sirrtea/kittenapi
    environment:
      MONGODB_URI: mongodb://kittenapi:LCg1SMxoWDg7gkuQ@mongo01:27017,mongo02:27017,mongo03:27017/kittenapi?replicaSet=rs&authSource=admin
    networks:
      - frontend
      - backend
    deploy:
      replicas: 2
      labels:
        traefik.http.routers.kittenapi.rule: Host(`kittenapi.example.com`)
        traefik.http.services.kittenapi.loadbalancer.server.port: 8080
        traefik.enable: "true"
      placement:
        constraints:
        - node.labels.usage == apps
networks:
  frontend:
    external: true
  backend:
    external: true
gerard@docker01:~/kittenapi$ 
```

**NOTA**: Las *labels* sirven para la versión 2.0 de **traefik**, que es la usada en el entorno.

Y con esto ya podemos desplegar:

```bash
gerard@docker01:~/kittenapi$ docker stack deploy -c kittenapi.yml kittenapi
Creating service kittenapi_kittenapi
gerard@docker01:~/kittenapi$ 
```

Comprobamos que todo ha levantado como debe:

```bash
gerard@docker01:~/kittenapi$ docker stack ps kittenapi
ID                  NAME                    IMAGE                      NODE                DESIRED STATE       CURRENT STATE           ERROR               PORTS
tng8x8ly8ufq        kittenapi_kittenapi.1   sirrtea/kittenapi:latest   docker05            Running             Running 8 seconds ago                       
owjvcv7dillq        kittenapi_kittenapi.2   sirrtea/kittenapi:latest   docker06            Running             Running 8 seconds ago                       
gerard@docker01:~/kittenapi$ 
```

## Comprobando el servicio

La comprobación es simple y se puede hacer de dos maneras:

* Mirar el *dashboard* de **traefik**, expuesto en el puerto 8080 del *gateway*
* Interactuar con la API y ver que todo responde desde una máquina cualquiera

**NOTA**: La máquina **desktop** accede al puerto 80 del *gateway* mediante un
*port forwarding* en el puerto 8000 (es el *host* de **VirtualBox**). Esto es
arbitrario y va a depender de vuestro *setup* de red.

**TRUCO**: Como no he puesto los registros DNS, vamos a probarlo con la cabecera HTTP
`Host`. También nos vamos a ayudar de una herramienta magnífica llamada [HTTPie][5],
que nos simplifica el uso de la API y nos formatea la salida.

Partimos de una base de datos vacía, así que la API no nos devuelve ningún recurso
para la colección `kittens` (estamos probando el método GET); sin sorpresas:

```bash
gerard@desktop:~$ http get :8000/kittens Host:kittenapi.example.com
HTTP/1.1 200 OK
...

[]

gerard@desktop:~$ 
```

Probamos ahora el método POST, creando algunos gatitos para la colección:

```bash
gerard@desktop:~$ http post :8000/kittens Host:kittenapi.example.com name=Ginger
HTTP/1.1 201 Created
...
gerard@desktop:~$ http post :8000/kittens Host:kittenapi.example.com name=Snowball
HTTP/1.1 201 Created
...
gerard@desktop:~$ http post :8000/kittens Host:kittenapi.example.com name=Molly
HTTP/1.1 201 Created
...
gerard@desktop:~$ http get :8000/kittens Host:kittenapi.example.com
HTTP/1.1 200 OK
...

[
    {
        "id": 1,
        "name": "Ginger"
    },
    {
        "id": 2,
        "name": "Snowball"
    },
    {
        "id": 3,
        "name": "Molly"
    }
]

gerard@desktop:~$ 
```

Para probar los métodos más inusuales (PUT y DELETE), hacemos las peticiones
de modificación y borrado, cambiando el nombre de un gatito y eliminando otro:

```bash
gerard@desktop:~$ http put :8000/kittens/2 Host:kittenapi.example.com name=Snowball2
HTTP/1.1 200 OK
...
gerard@desktop:~$ http delete :8000/kittens/1 Host:kittenapi.example.com
HTTP/1.1 200 OK
...
gerard@desktop:~$ http get :8000/kittens Host:kittenapi.example.com
HTTP/1.1 200 OK
...

[
    {
        "id": 2,
        "name": "Snowball2"
    },
    {
        "id": 3,
        "name": "Molly"
    }
]

gerard@desktop:~$ 
```

Y con esto nos damos por satisfechos.

## Siguientes pasos

### Más servicios

Para añadir más servicios a nuestro *cluster*, es tan simple como repetir todo el
artículo, a excepción de las *labels*, que ya estarían presentes. Estos servicios
puede estar en la misma *stack*, o estar repartidos en varias *stacks*, de acuerdo
con la organización lógica que queráis imponer en vuestro *workflow*.

### Crear entradas DNS adecuadas

Probar con la cabecera `Host` es útil, pero no es cómodo. Para llegar a esta API,
se necesita un registro DNS en condiciones, para que todos los usuarios de la API
puedan llegar cómodamente por nombre y les resuelva a una dirección IP a la que
puedan acceder (posiblemente pública).

Un cambio de nombre de dominio no solo depende de la entrada DNS; si lo cambiáis,
recordad que **traefik** hace *virtualhosts*, tal como se define el las *labels*
del servicio. No os olvidéis de cambiarlas.

### Usar SSL para encriptar las conexiones

Ninguna API debería servirse por HTTP plano. De hecho, ninguna web debería.
**Traefik** soporta SSL a través de **LetsEncrypt** de forma nativa; si esto no
es posible, delegad la capa SSL al balanceador o *proxy* externo.

### Más servidores

Si nos quedamos cortos de recursos, el *cluster* es ampliable; solo necesitamos
clonar de nuevo la máquina **docker** base, configurar el *gateway* para que le
asigne una dirección IP fija y ejecutar el *join token* del *swarm*.

Recordad que *swarm* no va a recolocar ningún servicio que no sea estrictamente
necesario; podemos escalar los servicios para forzar nuevas instancias, que irían
a parar a los nodos más desocupados, escalando nuevamente a la baja para eliminar
contenedores de donde sobren.

Hay que tener presente que todos los servicios tienen restricciones de *placement*;
para que el nuevo servidor sea candidato para **traefik** deberá ser un *manager*
(acordáos de **keepalived**), para mover algún nodo de la base de datos hará falta
otra *label* (los datos no se moverán, así que confiad en la replicación del
*replica set*), y para alojar aplicaciones hace falta la *label* `usage=apps`.

### Backups

No se están haciendo backups de ninguna parte del sistema. Hay que identificar
las partes *stateful* de cada servicio para saber que es lo que hay que tener
respaldado, a saber:

* Las configuraciones de la infraestructura (especialmente la configuración del *gateway*)
* Las recetas de despliegue de servicios, con sus ficheros de configuración
* Los datos que nuestras aplicaciones necesiten
    * **Traefik** no tiene un estado que guardar
    * Las aplicaciones no deberían generar datos en su contenedor
    * La base de datos **es crítica**; pensad en su *backup* con urgencia

Por suerte, los servicios de *backup* pueden ser contenedores que ejecutan *scripts*
y sacan el resultado a un servicio externo; esto hace que todo quede en el *swarm* y
no necesitemos modificar nuestros servidores. Esto hace el entorno 100% reconstruíble.

[1]: /downloads/kittenapi.tar.gz
[2]: {{< relref "/articles/2017/01/un-registro-local-de-docker.md" >}}
[3]: {{< relref "/articles/2018/11/un-registro-docker-privado-por-https-con-autenticacion-basica.md" >}}
[4]: https://hub.docker.com/
[5]: https://httpie.org/
