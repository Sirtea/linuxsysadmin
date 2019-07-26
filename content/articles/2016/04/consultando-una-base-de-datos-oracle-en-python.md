---
title: "Consultando una base de datos Oracle en python"
slug: "consultando-una-base-de-datos-oracle-en-python"
date: 2016-04-18
categories: ['Desarrollo']
tags: ['linux', 'debian', 'jessie', 'python', 'oracle', 'script', 'virtualenv', 'wheel']
---

El otro día estuve optimizando unos *scripts* hechos en *bash* que había hecho otro. Como resultado del lenguaje usado era un caos de comandos, muchos de ellos para limpiar la salida y darle la forma adecuada. Los reescribí en *python* usando la librería **cx_Oracle**, que compilé en un fichero *wheel*.<!--more-->

El mayor problema al que te enfrentas si intentas instalar una librería *python* que no está en la librería estándar, es que debes usar el gestor de paquetes, previo uso del usuario **root**. Y eso no siempre es posible.

Así que para hacer una instalación en mi carpeta personal, me decanté por crear un **virtualenv** en donde se iba a instalar una *wheel* precompilada en una máquina similar. Lo documento para tenerlo a mano.

Voy a explicar dos procedimientos: el primero es como instalar el *package* en una máquina que tenga herramientas de compilación y como empaquetarlo en un fichero *wheel*; el segundo consiste en instalar la *wheel* localmente en la máquina que la va a usar, a modo de *runtime*.

Para seguir esta guía, necesitamos una máquina con **Linux** cualquiera, que en mi caso ha sido una **Debian Jessie**. Estos son los paquetes necesarios como requisitos:

* unzip
* python
* libaio1

En la máquina en donde se vaya a crear la *wheel*, también serán necesarios los siguientes:

* python-dev
* gcc

Adicionalmente, se necesita descargar el [Oracle instant client](https://www.oracle.com/downloads/index.html), concretamente el **basic** y, en caso de la construcción de la *wheel*, también el **sdk**.

```bash
root@oracle:~# ls -1
instantclient-basic-linux-12.1.0.2.0.zip
instantclient-sdk-linux-12.1.0.2.0.zip
root@oracle:~#
```

## Construyendo el fichero wheel

El primer paso consiste en descomprimir el *instant client* de Oracle, necesario para cualquier programa que intente conectarse a sus bases de datos.

```bash
root@oracle:~# unzip instantclient-basic-linux-12.1.0.2.0.zip
Archive:  instantclient-basic-linux-12.1.0.2.0.zip
  inflating: instantclient_12_1/adrci
  inflating: instantclient_12_1/BASIC_README
  inflating: instantclient_12_1/genezi
  inflating: instantclient_12_1/libclntshcore.so.12.1
  inflating: instantclient_12_1/libclntsh.so.12.1
  inflating: instantclient_12_1/libnnz12.so
  inflating: instantclient_12_1/libocci.so.12.1
  inflating: instantclient_12_1/libociei.so
  inflating: instantclient_12_1/libocijdbc12.so
  inflating: instantclient_12_1/libons.so
  inflating: instantclient_12_1/liboramysql12.so
  inflating: instantclient_12_1/ojdbc6.jar
  inflating: instantclient_12_1/ojdbc7.jar
  inflating: instantclient_12_1/uidrvci
  inflating: instantclient_12_1/xstreams.jar
root@oracle:~# unzip instantclient-sdk-linux-12.1.0.2.0.zip
Archive:  instantclient-sdk-linux-12.1.0.2.0.zip
   creating: instantclient_12_1/sdk/
   creating: instantclient_12_1/sdk/include/
  inflating: instantclient_12_1/sdk/include/oratypes.h
  inflating: instantclient_12_1/sdk/include/occi.h
  inflating: instantclient_12_1/sdk/include/ocikpr.h
  inflating: instantclient_12_1/sdk/include/odci.h
  inflating: instantclient_12_1/sdk/include/xa.h
  inflating: instantclient_12_1/sdk/include/ldap.h
  inflating: instantclient_12_1/sdk/include/oci.h
  inflating: instantclient_12_1/sdk/include/ocidfn.h
  inflating: instantclient_12_1/sdk/include/oci1.h
  inflating: instantclient_12_1/sdk/include/ort.h
  inflating: instantclient_12_1/sdk/include/ociextp.h
  inflating: instantclient_12_1/sdk/include/occiAQ.h
  inflating: instantclient_12_1/sdk/include/ori.h
  inflating: instantclient_12_1/sdk/include/nzerror.h
  inflating: instantclient_12_1/sdk/include/ocixmldb.h
  inflating: instantclient_12_1/sdk/include/ocidef.h
  inflating: instantclient_12_1/sdk/include/occiControl.h
  inflating: instantclient_12_1/sdk/include/ocidem.h
  inflating: instantclient_12_1/sdk/include/nzt.h
  inflating: instantclient_12_1/sdk/include/orid.h
  inflating: instantclient_12_1/sdk/include/ociap.h
  inflating: instantclient_12_1/sdk/include/orl.h
  inflating: instantclient_12_1/sdk/include/ocixstream.h
  inflating: instantclient_12_1/sdk/include/occiObjects.h
  inflating: instantclient_12_1/sdk/include/oci8dp.h
  inflating: instantclient_12_1/sdk/include/oro.h
  inflating: instantclient_12_1/sdk/include/occiCommon.h
  inflating: instantclient_12_1/sdk/include/ociapr.h
  inflating: instantclient_12_1/sdk/include/occiData.h
   creating: instantclient_12_1/sdk/admin/
  inflating: instantclient_12_1/sdk/admin/oraaccess.xsd
 extracting: instantclient_12_1/sdk/ottclasses.zip
   creating: instantclient_12_1/sdk/demo/
  inflating: instantclient_12_1/sdk/demo/occidemo.sql
  inflating: instantclient_12_1/sdk/demo/oraaccess.xml
  inflating: instantclient_12_1/sdk/demo/occiobj.cpp
  inflating: instantclient_12_1/sdk/demo/occidemod.sql
  inflating: instantclient_12_1/sdk/demo/occidml.cpp
  inflating: instantclient_12_1/sdk/demo/occiobj.typ
  inflating: instantclient_12_1/sdk/demo/setuporamysql.sh
  inflating: instantclient_12_1/sdk/demo/cdemo81.c
  inflating: instantclient_12_1/sdk/demo/demo.mk
  inflating: instantclient_12_1/sdk/ott
  inflating: instantclient_12_1/sdk/SDK_README
root@oracle:~#
```

Para que el sistema sepa donde lo hemos descomprimido, hay que definir la variable de entorno **ORACLE_HOME**.

```bash
root@oracle:~# export ORACLE_HOME=/root/instantclient_12_1/
root@oracle:~#
```

La compilación de las librerías contenidas en el *package* **cx_Oracle** tiene un error y busca una librería llamada *libclntsh.so*, que no se llama así en el *runtime*. Se puede evitar el problema copiando la librería con el nuevo nombre, o mediante un enlace simbólico.

```bash
root@oracle:~# cd instantclient_12_1/
root@oracle:~/instantclient_12_1# ln -s libclntsh.so.12.1 libclntsh.so
root@oracle:~/instantclient_12_1# cd ..
root@oracle:~#
```

Y con esto ya podemos empezar. Creamos un **virtualenv** que nos va a servir como plataforma de construcción del fichero *wheel*.

```bash
root@oracle:~# virtualenv env
New python executable in /root/env/bin/python
Installing setuptools, pip, wheel...done.
root@oracle:~#
```

Se activa el entorno virtual y se instala la librería mediante **pip**.

```bash
root@oracle:~# . env/bin/activate
(env) root@oracle:~# pip install cx_Oracle
Collecting cx-Oracle
  Using cached cx_Oracle-5.2.1.tar.gz
Building wheels for collected packages: cx-Oracle
  Running setup.py bdist_wheel for cx-Oracle ... done
  Stored in directory: /root/.cache/pip/wheels/1f/38/66/b37c50906777b231a241ee02134f0ae018615519af43566269
Successfully built cx-Oracle
Installing collected packages: cx-Oracle
Successfully installed cx-Oracle-5.2.1
(env) root@oracle:~#
```

Podemos verificar si funciona cargando el módulo, y por ejemplo, preguntando la versión del mismo.

```bash
(env) root@oracle:~# python -c "import cx_Oracle; print cx_Oracle.version"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ImportError: libclntsh.so.12.1: cannot open shared object file: No such file or directory
(env) root@oracle:~#
```

Este es un mal resultado; nos indica que no se encuentra un fichero *.so*. Este fichero está en **ORACLE_HOME**, pero el sistema intenta buscar en **LD_LIBRARY_PATH**. Con modificar esta variable de entorno funciona.

```bash
(env) root@oracle:~# export LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH
(env) root@oracle:~#
```

Otro error es que se queje de que no encuentra *libaio.so*. Esto indica que os habéis saltado los requisitos y necesitáis instalarlos.

```bash
(env) root@oracle:~# python -c "import cx_Oracle; print cx_Oracle.version"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ImportError: libaio.so.1: cannot open shared object file: No such file or directory
(env) root@oracle:~# apt-get install libaio1
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes NUEVOS:
  libaio1
0 actualizados, 1 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 9.634 B de archivos.
Se utilizarán 13,3 kB de espacio de disco adicional después de esta operación.
...
(env) root@oracle:~#
```

Finalmente obtenemos un resultado correcto, que nos indica que tenemos instalada la librería en nuestro entorno virtual.

```bash
(env) root@oracle:~# python -c "import cx_Oracle; print cx_Oracle.version"
5.2.1
(env) root@oracle:~#
```

Podemos aprovechar esta compilación para máquinas con el mismo tipo de procesador y con la misma versión de **python**, creando un fichero *wheel* con la librería ya compilada.

```bash
(env) root@oracle:~# pip wheel cx_Oracle
Collecting cx-Oracle
  Saved ./cx_Oracle-5.2.1-cp27-cp27mu-linux_i686.whl
Skipping cx-Oracle, due to already being wheel.
(env) root@oracle:~#
```

Y ese es el fichero que vamos a distribuir a los entornos de producción donde necesitemos crear *scripts* en **python** que se conecten a Oracle.

## Instalando en otras máquinas

Vamos a suponer que nos interesa poner el *runtime* de Oracle y la carpeta con nuestros *scripts* en */opt/*. De hecho, nada impide que se haga en una carpeta personal, en la que tengamos privilegios completos.

También vamos a necesitar un *instant client* para poder funcionar, aunque esta vez no se necesitan enlaces simbólicos ni declarar la variable de entorno **ORACLE_HOME**. Lo descargamos en su localización deseada.

```bash
root@oracle2:/opt# unzip /root/instantclient-basic-linux-12.1.0.2.0.zip
Archive:  /root/instantclient-basic-linux-12.1.0.2.0.zip
  inflating: instantclient_12_1/adrci
  inflating: instantclient_12_1/BASIC_README
  inflating: instantclient_12_1/genezi
  inflating: instantclient_12_1/libclntshcore.so.12.1
  inflating: instantclient_12_1/libclntsh.so.12.1
  inflating: instantclient_12_1/libnnz12.so
  inflating: instantclient_12_1/libocci.so.12.1
  inflating: instantclient_12_1/libociei.so
  inflating: instantclient_12_1/libocijdbc12.so
  inflating: instantclient_12_1/libons.so
  inflating: instantclient_12_1/liboramysql12.so
  inflating: instantclient_12_1/ojdbc6.jar
  inflating: instantclient_12_1/ojdbc7.jar
  inflating: instantclient_12_1/uidrvci
  inflating: instantclient_12_1/xstreams.jar
root@oracle2:/opt#
```

Las dependencias deberían estar ya instaladas, pero en mi caso no lo estaban. Las instalamos.

```bash
root@oracle2:/opt# apt-get install python libaio1
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes extras:
  file libexpat1 libffi6 libmagic1 libpython-stdlib libpython2.7-minimal libpython2.7-stdlib libsqlite3-0 mime-support
  python-minimal python2.7 python2.7-minimal
Paquetes sugeridos:
  python-doc python-tk python2.7-doc binutils binfmt-support
Se instalarán los siguientes paquetes NUEVOS:
  file libaio1 libexpat1 libffi6 libmagic1 libpython-stdlib libpython2.7-minimal libpython2.7-stdlib libsqlite3-0 mime-support
  python python-minimal python2.7 python2.7-minimal
0 actualizados, 14 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 5.020 kB de archivos.
Se utilizarán 21,3 MB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...  
root@oracle2:/opt#
```

Creamos la carpeta que va a contener el entorno virtual y los *scripts*, y creamos en ella el entorno virtual.

```bash
root@oracle2:/opt# mkdir scripts
root@oracle2:/opt# cd scripts/
root@oracle2:/opt/scripts# virtualenv env
New python executable in /opt/scripts/env/bin/python
Installing setuptools, pip, wheel...done.
root@oracle2:/opt/scripts#
```

Activamos el entorno virtual y le instalamos el fichero *wheel*, que habremos copiado en algún sitio. Este fichero es local a la máquina, y no se consulta el repositorio de **python** remoto para nada. De hecho, un *wheel* es un fichero *.zip* normal, que se descomprime en la carpeta adecuada del **virtualenv**.

```bash
root@oracle2:/opt/scripts# . env/bin/activate
(env) root@oracle2:/opt/scripts# pip install /root/cx_Oracle-5.2.1-cp27-cp27mu-linux_i686.whl
Processing /root/cx_Oracle-5.2.1-cp27-cp27mu-linux_i686.whl
Installing collected packages: cx-Oracle
Successfully installed cx-Oracle-5.2.1
(env) root@oracle2:/opt/scripts#
```

Probamos que funcione; es importante definir la variable de entorno **LD_LIBRARY_PATH** para que encuentre el *runtime* de Oracle. Es muy útil ponerlo en el fichero *~/.bashrc* para que se cargue solo al abrir el *shell*.

```bash
(env) root@oracle2:/opt/scripts# export LD_LIBRARY_PATH=/opt/instantclient_12_1/
(env) root@oracle2:/opt/scripts# python -c "import cx_Oracle; print cx_Oracle.version"
5.2.1
(env) root@oracle2:/opt/scripts#
```

Opcionalmente, podemos reducir la cantidad de librerías que conforman el *instant client*, ya que solo se necesitan 4, y reduce su tamaño de forma dramática.

```bash
(env) root@oracle2:/opt/scripts# du -sh /opt/instantclient_12_1/
169M    /opt/instantclient_12_1/
(env) root@oracle2:/opt/scripts#
```

Podemos ver que el *package* **cx_Oracle** es un fichero *.so* y que este requiere de los otros 4 en el *runtime*.

```
(env) root@oracle2:/opt/scripts# find env/ -name "*.so"
env/lib/python2.7/site-packages/cx_Oracle.so
(env) root@oracle2:/opt/scripts# ldd env/lib/python2.7/site-packages/cx_Oracle.so | grep instant
        libclntsh.so.12.1 => /opt/instantclient_12_1/libclntsh.so.12.1 (0xb5387000)
        libnnz12.so => /opt/instantclient_12_1/libnnz12.so (0xb4d9d000)
        libons.so => /opt/instantclient_12_1/libons.so (0xb4d69000)
        libclntshcore.so.12.1 => /opt/instantclient_12_1/libclntshcore.so.12.1 (0xb4a90000)
(env) root@oracle2:/opt/scripts# ldd /opt/instantclient_12_1/lib{clntsh,nnz,ons}* | grep instant
/opt/instantclient_12_1/libclntshcore.so.12.1:
/opt/instantclient_12_1/libclntsh.so.12.1:
        libnnz12.so => /opt/instantclient_12_1/libnnz12.so (0xb4f8c000)
        libons.so => /opt/instantclient_12_1/libons.so (0xb4f58000)
        libclntshcore.so.12.1 => /opt/instantclient_12_1/libclntshcore.so.12.1 (0xb4aec000)
/opt/instantclient_12_1/libnnz12.so:
        libclntshcore.so.12.1 => /opt/instantclient_12_1/libclntshcore.so.12.1 (0xb7115000)
/opt/instantclient_12_1/libons.so:
(env) root@oracle2:/opt/scripts#
```

Lo que significa que debería ser seguro eliminar el resto. Así que lo hacemos. Guardad una copia de seguridad antes de eliminar nada.

Tras eliminar lo que no nos sirve, la carpeta queda así:

```bash
(env) root@oracle2:/opt/scripts# tree /opt/instantclient_12_1/
/opt/instantclient_12_1/
├── libclntshcore.so.12.1
├── libclntsh.so.12.1
├── libnnz12.so
└── libons.so

0 directories, 4 files
(env) root@oracle2:/opt/scripts# du -sh /opt/instantclient_12_1/
55M     /opt/instantclient_12_1/
(env) root@oracle2:/opt/scripts#
```

No está nada mal; hemos pasado de 169mb a 55mb. Comprobamos que sigue funcionando:

```bash
(env) root@oracle2:/opt/scripts# python -c "import cx_Oracle; print cx_Oracle.version"
5.2.1
(env) root@oracle2:/opt/scripts#
```

Y parece correcto.

## Uso del package cx_Oracle

En este punto hay que seguir la documentación del módulo, que no es muy diferente de otras bases de datos; **cx_Oracle** sigue la misma especificación para todos los módulos de bases de datos.

La idea es que se crea un objeto **conexión**, del que se saca un **cursor** para cada consulta que queramos ejecutar, y que se itera para obtener las **filas**. Pongamos un ejemplo simple:

```bash
(env) root@oracle2:/opt/scripts# cat list_fruits.py
#!/usr/bin/env python

import cx_Oracle

HOST='my_host'
PORT='my_port'
SID='my_sid'
SERVICE='my_service_name'
USER='nobody'
PASSWORD='secret'

dsn = cx_Oracle.makedsn(HOST, PORT, SID, SERVICE)
connection = cx_Oracle.connect(user=USER, password=PASSWORD, dsn=dsn)

query = "select name, price from fruits"
cursor = connection.cursor()
cursor.execute(query)
for row in cursor:
    print ';'.join(row)
cursor.close()

connection.close()
(env) root@oracle2:/opt/scripts#
```

Ejecutamos como cualquier otro *script*:

```bash
(env) root@oracle2:/opt/scripts# ./list_fruits.py
Apple;0.99
Orange;0.89
Pear;1.19
(env) root@oracle2:/opt/scripts#
```

Y obtenemos los datos deseados, con la facilidad que nos aporta **python** para dar formato fácil a la salida de nuestros *scripts*.
