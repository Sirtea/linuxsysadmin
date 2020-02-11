---
title: "Traspasando bases de datos entre servidores MongoDB"
slug: "traspasando-bases-de-datos-entre-servidores-mongodb"
date: "2020-02-11"
categories: ['Operaciones']
tags: ['mongodb', 'mongodump', 'mongorestore']
---

Cuando hacemos proyectos simples que requieren el uso de una base de datos **mongodb**
es habitual poner un servidor simple y poco potente para salir del paso. A veces,
estos proyectos empiezan a crecer en número y en importancia y necesitamos plantearnos
su traspaso a *hardware* más potente o a una topología tipo *cluster*.
<!--more-->

En estos casos nos encontramos con la necesidad de juntar bases de datos provenientes
de varios servidores menores, y no es una tarea simple; podemos utilizar las facilidades
de las *replica sets* para clonar un servidor en caliente, pero no de varios, ya que
la nueva sincronización desecharía las sincronizaciones anteriores.

Antes podíamos utilizar *helper* `copydb` adecuado para la ocasión, pero según la
documentación, esto va a dejar de ser una opción en un futuro próximo:

> Deprecated since version 4.0: MongoDB deprecates copydb and its helper db.copyDatabase().

La recomendación por parte de los creadores es utilizar el combo `mongodump` / `mongorestore`,
que se encadenarían utilizando *unix pipes* para no necesitar siquiera un fichero
intermedio. Ambos comandos funcionan con la salida y la entrada estándar, haciendo
este procedimiento fácil, y permitiendo incluso usar SSH como capa de transporte.

## Situación inicial

Tenemos dos proyectos: un *blog* y una tienda. Cada uno utiliza un servidor de **mongodb**
distinto, distribuido de esta forma:

* **server01** &rarr; Es donde guardamos la base de datos del *blog*
* **server02** &rarr; Alberga los datos de nuestra tienda virtual
* **server03** &rarr; Es el nuevo servidor, más potente, y debería agrupar ambas bases de datos

Por simplicidad, cada uno de estos servidores es una instancia solitaria de **mongodb**
que expone su puerto 27017 a otros servidores de la red interna (que es donde están
los servidores de aplicación).

## Procedimiento

Como sabemos, el comando `mongodump` y el comando `mongorestore` funcionan conectándose
a un servidor **mongodb**, ya sea en local o en remoto. A veces estos remotos no están
disponibles vía red por políticas de seguridad, o por formar parte de redes distintas.

Así que disponemos de varias opciones:

1. Sacar un `mongodump` en un fichero, moverlo de servidor y hacer el `mongorestore`
2. Levantar una VPN o un túnel SSH para que haya acceso directo al puerto origen y destino
3. Utilizar `mongodump` y `mongorestore` a través de SSH directamente

**TRUCO**: Los comandos `mongodump` y `mongorestore` funcionan con parámetros de red
individuales y con URIs con el *flag* `--uri`. Esto nos permite poner orígenes y destinos
más complejos, como por ejemplo *replica sets*, autenticación o *read preferences*.

**WARNING**: Para que los comandos `mongodump` y `mongorestore` trabajen con la salida
y la entrada estándar necesitan el *flag* `--archive`, sin especificar el destino; esto
hará que asuman la lectura y la escritura desde la consola.

### Si tenemos conectividad directa o indirecta

Supongamos que **server01** y **server03** están en la misma red y se pueden comunicar
por el puerto 27017 si restricciones. Este es el caso más simple. Basta con ejecutar
los dos comandos en una máquina cualquiera especificando correctamente los servidores
origen y destino (que por defecto serían *localhost*).

```bash
gerard@server01:~$ mongodump -d blog --archive --gzip | mongorestore -h server03 --archive --gzip --drop
...
gerard@server01:~$ 
```

Alternativamente podemos lanzar desde cualquier servidor que tenga las *tools* instaladas:

```bash
gerard@server03:~$ mongodump -h server01 -d blog --archive --gzip | mongorestore --archive --gzip --drop
...
gerard@server03:~$ 
```

```bash
gerard@adminserver:~$ mongodump -h server01 -d blog --archive --gzip | mongorestore -h server03 --archive --gzip --drop
...
gerard@adminserver:~$ 
```

### Si podemos llegar por SSH a alguno de los servidores

Supongamos que **server02** y **server03** no son accesibles por red. Sin embargo,
como *sysadmins* tenemos acceso a ambos desde una máquina administrativa. El truco
es simple: lanzamos el `mongodump` en la máquina origen por SSH y en la salida estándar;
luego utilizamos una *unix pipe* para insertar esa salida en la entrada de un
`mongorestore` lanzado por SSH contra el servidor destino.

```bash
gerard@sirius:~$ ssh server02 mongodump -d shop --archive --gzip | ssh server03 mongorestore --archive --gzip --drop
...
gerard@sirius:~$ 
```

**TRUCO**: La máquina **sirius** no dispone de `mongodump` ni `mongorestore` instalados;
se ejecutan dichos comandos en los servidores **server02** y **server03** respectivamente.

## Conclusión

Tras mover cada base de datos a **server03**, nuestras aplicaciones pueden cambiar
su fuente de datos fácilmente (suponiendo que ese parámetro sea configurable), y si
lo hemos hecho bien, ganaremos los beneficios por los que pusimos el nuevo servidor,
que puede ser por alguno de los siguientes motivos:

* Mejor *hardware* (más rápido, más memoria, más capacidad, ...)
* Un *cluster* con alta disponibilidad y/o con alto rendimiento
* Un solo punto grande que administrar, en contra de varios pequeños

**TRUCO**: Este traspaso de bases de datos puede ser gradual; podemos ir desmantelando
servidores y reconfigurando las aplicaciones a medida que podamos. No es necesario
mover todas las bases de datos de golpe.
