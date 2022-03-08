---
title: "Haciendo backups con BorgBackup"
slug: "haciendo-backups-con-borgbackup"
date: 2019-05-20
categories: ['Operaciones']
tags: ['backup', 'borgbackup', 'ssh']
---

Es un hecho inmutable que los desastres con nuestros datos ocurren; da igual lo cuidadosos que seamos, o si el servicio se autoreplica. En algún momento puede perderse información por un fallo imprevisto, o puede que sea necesario restablecer un punto conocido, para buscar errores o para cumplir imperativos legales.<!--more-->

De hecho, hacer un *backup* o una copia de respaldo es uno de los primeros requisitos cuando se trata de poner algo en producción, y fruto de esta necesidad han nacido muchas iniciativas que tratan de cubrirlas. Una de estas soluciones es **BorgBackup**, y sus funcionalidades atrajeron mi atención desde el principio. Más información en [su página web](https://borgbackup.readthedocs.io/en/stable/).

## Un caso de ejemplo

Supongamos que tenemos un máquina de la que necesitamos copias de seguridad, a la que llamaremos **client**, y un servidor de *backup* llamado **bakserver**. Cada uno de estos servidores tiene lo siguiente:

* **bakserver** &rarr; **borgbackup** y SSH servidor
* **client** &rarr; **borgbackup** y SSH cliente

**TRUCO**: El paquete **borgbackup** está disponible en los repositorios de las distribuciones principales, a veces como **borgbackup** y otras como **borg**.

Puesto que **borgbackup** funciona usando el protocolo SSH, hemos habilitado en acceso sin claves por comodidad y con vistas a una futura automatización.

En el servidor **client** tenemos una serie de carpetas que queremos guardar; concretamente, la carpeta `bin/`, `tools/` y `wallpapers/`, por poner un ejemplo.

```bash
client:~$ ls
bin         tools       wallpapers
client:~$ 
```

Para ello, vamos a utilizar **borgbackup** desde la máquina cliente **client**, que envía su respaldo al servidor central **bakserver**, usando el usuario *borg* que previamente hemos utilizado.

**AVISO**: Todos los comandos se ejecutan en la máquina cliente, siendo el servidor un simple proveedor de disco a través de SSH. Esto evita poner servicios adicionales en cada máquina.

### Creando y borrando backups

Vamos a empezar creando el espacio de *backups* en la máquina remota, que utilizando jerga de **borgbackup**, se llama **repositorio**. Para no complicar innecesariamente el artículo, no voy a utilizar encriptación ninguna.

```bash
client:~$ borg init --encryption=none borg@bakserver:clientrepo
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
client:~$ 
```

En este **repositorio** se crean **archivos**, que no son otra cosa que los diferentes *backups* que vamos haciendo. Hacer un *backup* es bastante simple, con la única complicación de saber la URL destino; la documentación ayuda en este punto.

```bash
client:~$ borg create --stats borg@bakserver:clientrepo::initial bin/ tools/ wallpapers/
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
------------------------------------------------------------------------------
Archive name: initial
Archive fingerprint: 8c7050a1639a8c9e40403b0791879027c16c75d5deabe93bc2af006036a4505c
Time (start): Mon, 2019-05-06 10:21:29
Time (end):   Mon, 2019-05-06 10:21:29
Duration: 0.89 seconds
Number of files: 6
Utilization of max. archive size: 0%
------------------------------------------------------------------------------
                       Original size      Compressed size    Deduplicated size
This archive:               34.57 MB             34.71 MB             34.71 MB
All archives:               34.57 MB             34.71 MB             34.71 MB

                       Unique chunks         Total chunks
Chunk index:                      21                   21
------------------------------------------------------------------------------
client:~$ 
```

Y con esto tenemos nuestro backup completo, cosa que podemos verificar listando los **archivos** en nuestro **repositorio**:

```bash
client:~$ borg list borg@bakserver:clientrepo
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
initial                              Mon, 2019-05-06 10:23:11 [de00f6579345eccae5163d7ba5705a93790cbb0a6e451c7114462572e99fcc1b]
client:~$ 
```

Una de las funcionalidades más útiles de **borgbackup** es que hace *backups* incrementales de forma muy eficiente, evitando duplicar ficheros que no cambien. Esto es lo que podemos ver si repetimos el mismo *backup*.

```bash
client:~$ borg create --stats borg@bakserver:clientrepo::initial_v2 bin/ tools/ wallpapers/
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
------------------------------------------------------------------------------
Archive name: initial_v2
Archive fingerprint: 6b8b1b34e434ab45aa038e81ad7dc9cabe7da2554c9fd5ce659b1a8351c93166
Time (start): Mon, 2019-05-06 10:23:50
Time (end):   Mon, 2019-05-06 10:23:50
Duration: 0.47 seconds
Number of files: 6
Utilization of max. archive size: 0%
------------------------------------------------------------------------------
                       Original size      Compressed size    Deduplicated size
This archive:               34.57 MB             34.71 MB                450 B
All archives:               69.14 MB             69.41 MB             34.71 MB

                       Unique chunks         Total chunks
Chunk index:                      22                   42
------------------------------------------------------------------------------
client:~$ 
```

El *backup* que acabamos de hacer tiene un tamaño de 35mb, pero solo ocupa 450 bytes en el repositorio. Esto es así porque los ficheros identicos se referencian, en vez de duplicarse.

```bash
client:~$ borg list borg@bakserver:clientrepo
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
initial                              Mon, 2019-05-06 10:23:11 [de00f6579345eccae5163d7ba5705a93790cbb0a6e451c7114462572e99fcc1b]
initial_v2                           Mon, 2019-05-06 10:23:50 [6b8b1b34e434ab45aa038e81ad7dc9cabe7da2554c9fd5ce659b1a8351c93166]
client:~$ 
```

De la misma forma que creamos *backups*, podemos eliminarlos. Esta es una opción no habitual, ya que **borgbackup** ofrece la función de retención de *backups* antiguos, con el comando `borg prune`. Borrar un **archivo** es tan simple como indicar el **archivo** a borrar:

```bash
client:~$ borg delete borg@bakserver:clientrepo::initial_v2
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
client:~$ 
```

Y por supuesto, solo nos quedaría el *backup* inicial, tras el borrado del segundo *backup*.

```bash
client:~$ borg list borg@bakserver:clientrepo
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
initial                              Mon, 2019-05-06 10:23:11 [de00f6579345eccae5163d7ba5705a93790cbb0a6e451c7114462572e99fcc1b]
client:~$ 
```

Si necesitamos una fichero comprimido de un **archivo** concreto, podemos hacer un `borg export-tar`, que intentará darnos el fichero con un formato adecuado al nombre del fichero de salida indicado.

```bash
client:~$ borg export-tar borg@bakserver:clientrepo::initial initial.tar.gz
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
client:~$ 
```

```bash
client:~$ ls
bin             initial.tar.gz  tools           wallpapers
client:~$ 
```

En este caso, el fichero `initial.tar.gz` estará comprimido con **gzip**, cosa que **borgbackup** ha deducido de la extensión `.tar.gz`.

### Un escenario de recuperación

Vamos a cometer un error a propósito, no muy diferente del que podría hacer un usuario descuidado; borraremos todo lo que hay en nuestra carpeta personal.

```bash
client:~$ rm * -R
client:~$ 
```

Entonces recibiremos la visita del susodicho usuario con sus quejas habituales e indicando que "no ha hecho nada". Nada que hacer, excepto de tirar de *backup*. Le ofrecemos al usuario el listado de *backups* de los que disponemos, rezando para que alguno le valga.

```bash
client:~$ borg list borg@bakserver:clientrepo
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
initial                              Mon, 2019-05-06 10:23:11 [de00f6579345eccae5163d7ba5705a93790cbb0a6e451c7114462572e99fcc1b]
client:~$ 
```

Le convencemos de restablecer el *backup* `initial`, ya que no tenemos otro, y efectuamos la restauración con `borg extract`. Así de fácil:

```bash
client:~$ borg extract borg@bakserver:clientrepo::initial
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
client:~$ 
```

```bash
client:~$ ls
bin         tools       wallpapers
client:~$ 
```

Otra opción es que se necesite restaurar el *backup* en otra carpeta o en otra máquina. También es posible.

```bash
client:~$ mkdir justtoinspect
client:~$ cd justtoinspect/
client:~/justtoinspect$ borg extract borg@bakserver:clientrepo::initial
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
client:~/justtoinspect$ ls
bin         tools       wallpapers
client:~/justtoinspect$ 
```

### Otras consideraciones

Si necesitamos hacer un poco de limpieza eliminando el **repositorio**, es posible:

```bash
client:~$ borg delete borg@bakserver:clientrepo
Using a pure-python msgpack! This will result in lower performance.
Remote: Using a pure-python msgpack! This will result in lower performance.
You requested to completely DELETE the repository *including* all archives it contains:
initial                              Mon, 2019-05-06 10:23:11 [de00f6579345eccae5163d7ba5705a93790cbb0a6e451c7114462572e99fcc1b]
Type 'YES' if you understand this and want to continue: YES
client:~$ 
```

El punto flaco de esta solución es que se ejecuta a petición. Para hacer estos *backups* de forma automatizada necesitaremos poner algo de lógica de nuestra parte:

* Poner un *script* en una tarea **cron**
* Lanzar el *backup*, ya sea manualmente o usando algo como **ansible**

**TRUCO**: En todos los casos podemos poner una capa extra para simplificar el proceso, como por ejemplo [borgmatic](https://torsion.org/borgmatic/), que se encarga de simplificar nuestras líneas de comandos (*backup* y *prune*) utilizando un fichero de configuración simple.
