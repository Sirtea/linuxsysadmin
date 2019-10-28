---
title: "Algunos trucos con el cliente SSH y su configuración"
slug: "algunos-trucos-con-el-cliente-ssh-y-su-configuracion"
date: "2019-10-28"
categories: ['Operaciones']
tags: ['linux', 'ssh', 'configuración']
---

Nunca dejo de maravillarme de la cantidad de *keywords* y parámetros que nos ofrece
SSH. Sin embargo, tanta funcionalidad tiene un precio, que es la dificultad de
descubrirlos todos y, a la larga, nos quedamos con solo unos pocos. Otro problema
es la creciente longitud de nuestras líneas de comandos.<!--more-->

Por suerte, disponemos de dos herramientas muy útiles que nos permiten ir descubriendo
y utilizando este servicio tan imprescindible como omnipresente:

* Una magnífica documentación, sea el **man**, el *flag* `--help` o páginas de internet.
* Una configuración cliente, tanto a nivel de sistema como a nivel de usuario.

En este artículo pretendo dejar constancia de algunas configuraciones interesantes
que suelo utilizar en mi día a día, utilizando la configuración cliente en `~/.ssh/config`
para limitar bastante la longitud de mis líneas de comandos.

## Las *host keys* y los cierres de sesión

No hay nada más molesto que regenerar un servidor y tener a SSH quejándose porque
han canviado las *host keys*, lo que interpreta como una suplantación de identidad
del servidor "conocido", aunque es exactamente lo que queríamos...

**TRUCO**: Utilizamos la directiva `StrictHostKeyChecking no` para que no lo verifique.
Adicionalmente, podemos hacer que no se guarde la relación entre la IP del servidor y su
*host key*, indicando que lo "guarde" en `/dev/null` utilizando la directiva `UserKnownHostsFile`

Otro problema que se me presenta a menudo es el de sesiones SSH que se han cerrado de forma
automática tras un periodo de inactividad, tal como un descanso o una reunión. En estos casos,
podemos hacer que el mismo SSH cliente mande *keepalives* para mantener la sesión abierta.
Basta indicarle los segundos entre *keepalive* con la directiva `ServerAliveInterval`.

Aplicando estas directivas en todas las conexiones por defecto, se consigue poniendo una
configuración como la siguiente en nuestra configuración cliente:

```bash
gerard@debian:~$ cat .ssh/config
...
Host *
	StrictHostKeyChecking no
	UserKnownHostsFile /dev/null
	ServerAliveInterval 60
...
gerard@debian:~$ 
```

## Parámetros de conexión por servidor

Otro de los problemas habituales trabajando con SSH son las líneas de comandos infinitamente
largas por necesitar una cantidad considerable de parámetros. Por poner un ejemplo:

```bash
gerard@debian:~$ ssh -i .ssh/id_ec2  -p 2222 ec2-user@ec2-xxx-xxx-xxx-xxx.compute-x.amazonaws.com
...
gerard@debian:~$ 
```

Esto no es fácil de recordar ni agradable de escribir. Por suerte, SSH nos permite
declarar un nombre arbitrario con la directiva `Host` y aplicar otras directivas
que aplican para esa conexión:

* `Hostname` &rarr; Para indicar el nombre real o la dirección del servidor.
* `Port` &rarr; Para indicar el puerto que debe usar SSH para hacer la conexión.
* `User` &rarr; Para indicar el usuario con el que queremos entrar en el servidor.
* `IdentityFile` &rarr; Ruta de la clave SSH cliente que hay que utilizar para la conexión.

Con estas opciones podemos declarar la conexión anterior en `~/.ssh/config` de la siguiente forma:

```bash
gerard@debian:~$ cat .ssh/config
...
Host webserver
	Hostname ec2-xxx-xxx-xxx-xxx.compute-x.amazonaws.com
	Port 2222
	User ec2-user
	IdentityFile ~/.ssh/id_ec2
...
gerard@debian:~$ 
```

El resultado es la capacidad de usar el nombre `webserver` para aglutinar las opciones;
en caso de tener instalado el paquete **bash-completion** dispondremos de la función de
autocompletar con la tecla TAB...

```bash
gerard@debian:~$ ssh webserver
...
gerard@debian:~$ 
```

## Aplicar opciones comunes a varios servidores

Muchas veces trabajamos con varios servidores que comparten nombre de usuario, puertos
u otros parámetros SSH. En estos casos, podemos declarar la lista de servidores en la
directiva `Host`, separados por espacios. Es posible también especificar patrones con
los carácteres `*` (0 o más carácteres), `?` (exactamente un carácter) o `!` (negación).

Para complementar esta declaración global, es posible que un *host* esté referenciado
en varios bloques tipo `Host`, aplicando en caso de duda el bloque más específico.

```bash
gerard@debian:~$ cat .ssh/config
...
Host appserver* database
	User gerard
	IdentityFile ~/.ssh/id_jump
	Port 2222

Host appserver01
	Hostname 10.0.0.3

Host appserver02
	Hostname appserver02.local
	Port 2223

Host database
	Hostname mongodb.local
	User mongo
...
gerard@debian:~$ 
```

En este caso haríamos SSH utilizando los nombres **appserver01**, **appserver02** y
**database**. El puerto por defecto sería el 2222 y el usuario sería `gerard`, aunque
en el caso de **appserver02** cambiamos el puerto por el 2223 y en el caso de **database**
cambiamos el usuario por `mongo`.

## Usando máquinas de salto intermedias

Un patrón muy usado es el de entrar en un sistema a través de un solo *host* altamente
auditado, a través del que obtenemos visibilidad del resto de servidores. Como ejecutar
dos veces el comando `ssh` no era cómodo, se inventó una forma de suprimir ese salto
utilizando la directiva `ProxyCommand` como escribí en [un artículo anterior][1].

Tan frecuente era esta forma de trabajar que el cliente OpenSSH acabó haciéndolo oficial
a través de la directiva `ProxyJump` (o el parámetro `-J` de `ssh`). Eso simplifica la
línea de comandos hasta el punto de indicar el salto en el propio comando:

```bash
gerard@debian:~$ ssh -J gateway hiddenserver
...
gerard@debian:~$ 
```

Podemos hacerlo más simple todavía escondiendo ese parámetro en la configuración SSH
cliente, para dejar el comando en un solo `ssh hiddenserver`:

```bash
gerard@debian:~$ cat .ssh/config
...
Host hiddenserver
	ProxyJump gateway
...
gerard@debian:~$ 
```

**TRUCO**: Podemos indicar un *host* `gateway` para esconder sus parámetros de conexión.
Si optamos por usar claves SSH, van individualmente para `gateway` y para `hiddenserver`,
pero en ambos casos se utilizan las claves privadas locales y no hay que poner nada en `gateway`.

[1]: {{< relref "/articles/2018/01/usando-un-bastion-ssh.md" >}}
