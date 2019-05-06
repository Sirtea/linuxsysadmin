Title: Descubriendo el funcionamiento de zookeeper
Slug: descubriendo-el-funcionamiento-de-zookeeper
Date: 2019-05-06 10:00
Category: Sistemas
Tags: zookeeper, cluster



Tras probar algunos servicios pensados para la nube o para contenedores, veo que algunos de ellos dependen de una pieza central llamada **zookeeper**. Como soy una persona curiosa, he decidido dedicar un artículo a entender como funciona este servicio, que se limita a guardar cosas de forma distribuida y redundante.

Se puede ver como un servicio en donde se guardan cadenas de *bytes* en nodos, que a su vez se organizan jerárquicamente como si de una estructura de ficheros *Unix* se tratara. De esta manera, podríamos tener en el *path* `/myservice/config` una cadena de carácteres, que podría ser la representación de dicha configuración, por ejemplo codificada en JSON.

La principal gracia de esta aproximación es la de tener una configuración centralizada para un conjunto de servicios que la recuperan de **zookeeper**. Otra de las ventajas de este servicio es que está pensado para funcionar de forma distribuida y altamente redundante, con lo que la alta disponibilidad está garantizada.

## Levantando una instancia de zookeeper

Levantar **zookeeper** es tan fácil como descargar la distribución, enchufar una configuración y ejecutar un *script*; más información para este método en [la documentación](https://zookeeper.apache.org/doc/r3.4.14/zookeeperStarted.html). Entre los requisitos se encuentra **java** pero no estaba dispuesto a ensuciar mi máquina con instalaciones de *software* que no voy a utilizar casi nunca.

Por ello, voy a echar mano de **docker**, que lo tiene todo listo en una imagen oficial y me permite levantar un entorno de "usar y tirar", que bien me vale para la demostración. La imagen la podéis encontrar en [DockerHub](https://hub.docker.com/_/zookeeper/). Para el caso de una instancia sola, no hay mucha complicación; he usado **docker-compose** por comodidad.

```bash
gerard@atlantis:~/workspace/zktest$ cat docker-compose.yml 
version: '3'
services:
  zookeeper:
    image: zookeeper
    container_name: zookeeper
    hostname: zookeeper
    ports:
      - "2181:2181"
gerard@atlantis:~/workspace/zktest$ 
```

Levantamos con el comando habitual y, como hemos publicado el puerto, ya podremos trabajar como si lo tuviéramos localmente.

```bash
gerard@atlantis:~/workspace/zktest$ docker-compose up -d
Creating network "zktest_default" with the default driver
Creating zookeeper ... done
gerard@atlantis:~/workspace/zktest$ 
```

## Trasteando con zookeeper

Como tantos otros *datastores*, **zookeeper** viene con un cliente de terminal, que nos permite probar, administrar y ver lo que va pasando en nuestros datos; solo hay que ejecutar `zkCli.sh`. Tened en cuenta este cliente está instalado dentro del contenedor.

```bash
gerard@atlantis:~/workspace/zktest$ docker exec -ti zookeeper zkCli.sh
Connecting to localhost:2181
...
[zk: localhost:2181(CONNECTED) 0] 
```

El sistema de *namespaces* de **zookeeper** funciona como un sistema de ficheros tipo *unix* o *linux*, con el carácter `/` para separar nodos (equivalente de ficheros y carpetas). Cada uno de estos nodos, tiene un contenido (puede que vacío) y una lista de hijos (posiblemente también vacía). En este aspecto se comporta más como una estructura arborescente.

```bash
[zk: localhost:2181(CONNECTED) 1] ls /
[zookeeper]
[zk: localhost:2181(CONNECTED) 2] ls /zookeeper
[quota]
[zk: localhost:2181(CONNECTED) 3] ls /zookeeper/quota
[]
[zk: localhost:2181(CONNECTED) 4] 
```

Los contenidos en **zookeeper** están pensados para ser leídos muchas veces, pero es algo más lento para escribir o modificar el contenido. Esto no nos evita que debamos crear antes algo de contenido.

```bash
[zk: localhost:2181(CONNECTED) 12] create /hello "world"
Created /hello
[zk: localhost:2181(CONNECTED) 13] 
```

Podemos ver el resultado listando los hijos del nodo raíz, y podemos consultar el contenido que acabámos de crear:

```bash
[zk: localhost:2181(CONNECTED) 13] ls /
[hello, zookeeper]
[zk: localhost:2181(CONNECTED) 14] get /hello
world
cZxid = 0x2
ctime = Wed Apr 10 11:05:17 GMT 2019
mZxid = 0x2
mtime = Wed Apr 10 11:05:17 GMT 2019
pZxid = 0x2
cversion = 0
dataVersion = 0
aclVersion = 0
ephemeralOwner = 0x0
dataLength = 5
numChildren = 0
[zk: localhost:2181(CONNECTED) 15] 
```

De la misma forma, podemos borrar el nodo de forma fácil:

```bash
[zk: localhost:2181(CONNECTED) 15] delete /hello
[zk: localhost:2181(CONNECTED) 16] ls /
[zookeeper]
[zk: localhost:2181(CONNECTED) 17] 
```

Nada nos impide crear nodos dentro de otros nodos, así que vamos a crear una configuración para un servicio hipotético. El valor de la configuración es solamente una cadena de texto, y podemos poner lo que queramos; tanto su modificación como su interpretación dependen de la aplicación que los use. Para hacer el ejemplo legible y pequeño, voy a poner un objeto JSON.

```bash
[zk: localhost:2181(CONNECTED) 20] create /myapp ""
Created /myapp
[zk: localhost:2181(CONNECTED) 21] ls /
[zookeeper, myapp]
[zk: localhost:2181(CONNECTED) 22] 
```

```bash
[zk: localhost:2181(CONNECTED) 23] create /myapp/config '{"DB_URL": "mongodb://mongoserver:27017/myapp"}'
Created /myapp/config
[zk: localhost:2181(CONNECTED) 24] 
```

Podemos verificar que dicha configuración se ha guardado:

```bash
[zk: localhost:2181(CONNECTED) 25] get /myapp/config
{"DB_URL": "mongodb://mongoserver:27017/myapp"}
...  
[zk: localhost:2181(CONNECTED) 26] 
```

De hecho, nada nos impide crear más nodos colgando de `/myapp`, demostrando así que esto es un árbol de datos.

```bash
[zk: localhost:2181(CONNECTED) 26] create /myapp/loglevel "WARN"
Created /myapp/loglevel
[zk: localhost:2181(CONNECTED) 27] get /myapp/loglevel
WARN
...  
[zk: localhost:2181(CONNECTED) 28] 
```

También podemos ver que el nodo `/myapp` tiene subnodos, pero estos ya no tienen nada más colgando, como evidencia la lista vacía de hijos:

```bash
[zk: localhost:2181(CONNECTED) 29] ls /myapp
[config, loglevel]
[zk: localhost:2181(CONNECTED) 30] ls /myapp/loglevel
[]
[zk: localhost:2181(CONNECTED) 31] 
```

# Utilizando zookeeper en nuestras aplicaciones

Hay conectores de **zookeeper** para una gran mayoría de lenguajes de programación, y todos ellos se basan en las mismas primitivas que hemos visto antes. Por ejemplo, en **python** podemos usar **kazoo**.

```bash
(env) gerard@atlantis:~/workspace/zktest$ cat requirements.txt 
kazoo==2.6.1
(env) gerard@atlantis:~/workspace/zktest$ 
```

En cuanto a las operaciones, son las mismas, y solo cambia la sintaxis para adaptarse al lenguaje usado. Adicionalmente, podemos conectar a un servicio remoto, que con el cliente terminal no vimos porque lo hace por defecto al servidor local.

```bash
(env) gerard@atlantis:~/workspace/zktest$ cat test.py 
from kazoo.client import KazooClient

# Conectamos
zk = KazooClient(hosts='127.0.0.1:2181')
zk.start()

# Zookeeper vacío
print(zk.get_children('/'))

# Creamos un path y llenamos de datos
zk.ensure_path('/myapi/database')
zk.create('/myapi/database/host', b'mongoserver')
zk.create('/myapi/database/port', b'27017')

# Listado de estructura
print(zk.get_children('/'))
print(zk.get_children('/myapi'))
print(zk.get_children('/myapi/database'))

# Consulta de contenidos
host = zk.get('/myapi/database/host')[0]
port = zk.get('/myapi/database/port')[0]
print(host, port)

# Limpiamos las claves de test
for path in ('/myapi/database/host', '/myapi/database/port', '/myapi/database', '/myapi'):
    zk.delete(path)

# Desconectamos
zk.stop()
(env) gerard@atlantis:~/workspace/zktest$ 
```

Estas operaciones han quedado englobadas en el objeto cliente, que se ha inicializado al principio del *script* y se ha cerrado antes de acabar. Podemos ver el resultado de la ejecución, aunque en este caso ha optado por trocear la configuración en más subnodos, para no tener que serializarla.

```bash
(env) gerard@atlantis:~/workspace/zktest$ python3 test.py 
['zookeeper']
['zookeeper', 'myapi']
['database']
['host', 'port']
b'mongoserver' b'27017'
(env) gerard@atlantis:~/workspace/zktest$ 
```

## Clusterización de zookeeper

Como se ha comentado al principio del artículo, una de las virtudes de este servicio es su redundancia, que nos ofrece una alta disponibilidad casi total. Para ello, **zookeeper** implementa un modelo de replicación distribuida de las operaciones, en donde la modificación real se autoriza mediante el *quorum* de **más de la mitad** de las instancias.

Si hacéis las cuentas, lo ideal es poner un número impar de instancias y a la vez, más de una para garantizar algún punto de fallo. Para no alargar el artículo innecesáriamente, voy a poner 3 instancias; nuevamente la imagen oficial nos ofrece una forma fácil de sobreescribir la configuración de cada intancia, usando variables de entorno.

```bash
gerard@atlantis:~/workspace/zktest$ cat docker-compose.cluster.yml 
version: '3'
services:
  zookeeper1:
    image: zookeeper
    container_name: zookeeper1
    hostname: zookeeper1
    environment:
      ZOO_MY_ID: 1
      ZOO_SERVERS: server.1=zookeeper1:2888:3888 server.2=zookeeper2:2888:3888 server.3=zookeeper3:2888:3888
  zookeeper2:
    image: zookeeper
    container_name: zookeeper2
    hostname: zookeeper2
    environment:
      ZOO_MY_ID: 2
      ZOO_SERVERS: server.1=zookeeper1:2888:3888 server.2=zookeeper2:2888:3888 server.3=zookeeper3:2888:3888
  zookeeper3:
    image: zookeeper
    container_name: zookeeper3
    hostname: zookeeper3
    environment:
      ZOO_MY_ID: 3
      ZOO_SERVERS: server.1=zookeeper1:2888:3888 server.2=zookeeper2:2888:3888 server.3=zookeeper3:2888:3888
gerard@atlantis:~/workspace/zktest$ 
```

Solo hay que levantar el *cluster* usando **docker-compose**, de acuerdo al procedimiento habitual:

```bash
gerard@atlantis:~/workspace/zktest$ docker-compose -f docker-compose.cluster.yml up -d
Creating network "zktest_default" with the default driver
Creating zookeeper2 ... done
Creating zookeeper3 ... done
Creating zookeeper1 ... done
gerard@atlantis:~/workspace/zktest$ 
```

En la parte de verificación del funcionamiento del *cluster* se nota algo más de dejadez por parte de los desarrolladores; la información ofrecida es mínima e insuficiente. En este caso nos conformaremos en saber que hay un *leader* y que los otros dos son *followers*.

```bash
gerard@atlantis:~/workspace/zktest$ docker exec -ti zookeeper1 zkServer.sh status
ZooKeeper JMX enabled by default
Using config: /conf/zoo.cfg
Mode: follower
gerard@atlantis:~/workspace/zktest$ docker exec -ti zookeeper2 zkServer.sh status
ZooKeeper JMX enabled by default
Using config: /conf/zoo.cfg
Mode: follower
gerard@atlantis:~/workspace/zktest$ docker exec -ti zookeeper3 zkServer.sh status
ZooKeeper JMX enabled by default
Using config: /conf/zoo.cfg
Mode: leader
gerard@atlantis:~/workspace/zktest$ 
```

Para los que necesitan una prueba más del funcionamiento del *cluster*, podemos mirar los logs, viendo lo que ha pasado con el proceso de elección de *leader*. Con **docker-compose**, esta operación es trivial:

```bash
gerard@atlantis:~/workspace/zktest$ docker-compose -f docker-compose.cluster.yml logs | grep ELECTION
zookeeper3    | 2019-04-10 12:05:20,713 [myid:3] - INFO  [QuorumPeer[myid=3]/0.0.0.0:2181:Leader@380] - LEADING - LEADER ELECTION TOOK - 255
zookeeper2    | 2019-04-10 12:05:20,709 [myid:2] - INFO  [QuorumPeer[myid=2]/0.0.0.0:2181:Follower@65] - FOLLOWING - LEADER ELECTION TOOK - 988
zookeeper1    | 2019-04-10 12:05:20,712 [myid:1] - INFO  [QuorumPeer[myid=1]/0.0.0.0:2181:Follower@65] - FOLLOWING - LEADER ELECTION TOOK - 310
gerard@atlantis:~/workspace/zktest$ 
```

Y con esto hemos montado nuestro *cluster*. Lo único que hay que tener en cuenta es la modificación de las cadenas de conexión al **zookeeper** para que conozca a todos los posibles *leaders*, tal como sea necesario volverlos a elegir. Esto solo debería pasar por caídas, paradas controladas o problemas *hardware* de los nodos del *cluster*.
