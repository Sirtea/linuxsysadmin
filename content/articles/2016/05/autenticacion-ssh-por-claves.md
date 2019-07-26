---
title: "Autenticación SSH por claves"
slug: "autenticacion-ssh-por-claves"
date: 2016-05-30
categories: ['Operaciones']
tags: ['linux', 'ssh', 'autenticación', 'password', 'passphrase', 'rsa']
---

A pesar de que el protocolo **SSH** es lo que mas seguridad ofrece hoy en día, un servidor rápido puede probar gran cantidad de contraseñas generadas mediante un generador por fuerza bruta. Para añadir mas seguridad podemos autenticar mediante claves en vez de usar contraseña, opcionalmente protegidos con una *passphrase*.<!--more-->

La idea es que un cliente del servidor **SSH** se autentique reemplazando la contraseña habitual por una clave, previamente generada y con su parte pública compartida con anterioridad.

## Disposición inicial

Para la demostración tenemos dos servidores, con los roles claramente especificados en el nombre:

```bash
root@lxc:~# lxc-ls -f
NAME       STATE    IPV4      IPV6  AUTOSTART
---------------------------------------------
client     RUNNING  10.0.0.3  -     NO
sshserver  RUNNING  10.0.0.2  -     NO
root@lxc:~#
```

En el caso del servidor, necesitamos un servidor **SSH** levantado y listo para recibir nuevas sesiones.

```bash
root@sshserver:~# netstat -lntp
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      76/sshd
tcp6       0      0 :::22                   :::*                    LISTEN      76/sshd
root@sshserver:~#
```

Vamos a crear un usuario con el que podamos entrar en el servidor.

```bash
root@sshserver:~# grep gerard /etc/passwd
gerard:x:1000:1000:,,,:/home/gerard:/bin/bash
root@sshserver:~#
```

Si intentamos entrar en el servidor desde la máquina cliente, vemos que se nos pide la contraseña, tras lo cual iniciamos la sesión.

```bash
root@client:~# ssh gerard@10.0.0.2
gerard@10.0.0.2's password:

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
gerard@sshserver:~$
```

De hecho, si lo volvemos a intentar, se nos pedirá la *password* una y otra vez.

## Montando el par de claves

Desde la máquina cliente, generamos el par de claves mediante el comando **ssh-keygen**. Sin parámetros va a generar un clave tipo **RSA**, que ya nos vale.

Es importante indicar que la *passphrase* es más segura que la *password*, y que la necesidad de la clave convierte el combo en lo mas seguro de lo que disponemos. Vamos a dejarla en blanco para asegurar la autenticación con claves sin *passphrase*, por comodidad nuestra.

```bash
root@client:~# ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (/root/.ssh/id_rsa):
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /root/.ssh/id_rsa.
Your public key has been saved in /root/.ssh/id_rsa.pub.
The key fingerprint is:
58:6b:38:71:82:a4:b2:97:4d:cc:6d:cd:43:6d:26:00 root@client
The key's randomart image is:
+---[RSA 2048]----+
|    E.....       |
|   = o +. +      |
|. . = = *+       |
| o + . B o       |
|. o . + S        |
| .     o         |
|                 |
|                 |
|                 |
+-----------------+
root@client:~#
```

Esto nos ha generado el par de claves en la carpeta que nos preguntó el comando de generación. En este caso dejamos los valores por defecto.

```bash
root@client:~# ls -1 .ssh/
id_rsa
id_rsa.pub
known_hosts
root@client:~#
```

Vemos que tenemos dos ficheros nuevos. El fichero *id_rsa* es la clave privada, y es una parte que nunca debe compartirse. El fichero *id_rsa.pub* es la parte pública de la clave y es la que debemos repartir a los servidores a los que pretendamos tener acceso con la clave.

```bash
root@client:~# cat .ssh/id_rsa.pub
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDHR7HSGhP8afT1pz/no+qVT1uKsEhh4CZXIbDebibbKiyPYVaKl/FLovYnCwk0IWXAsiJB1eXkQhX0he0gSK66UIZFnKVr8+G1J1kg9zuqxFTxpJTrM2WbdTZ+nk3bNgKTFKiQNsZ/IMvb/vjgU365LNtDclnajto0scgSCZQBvDfxrNVH8NIyv4IBTKheD6oSNgQsmzpvbWRyKBZf3dRRdVH00tsIC20fdAONtNfcWNToakRMX0/svW7RxUDlJEU/icsm3lf6xRf927CdB0ziu90i9mpzCxTMP3xbsrOJ0/mtdqROjql+OHNvxJa8FOtvX/ZdkNRAPOvuo4AieLZp root@client
root@client:~#
```

Para garantizar el acceso a nuestro servidor, debemos poner una nueva línea en el fichero *authorized_keys* del usuario remoto, que es la parte pública de la clave. Es especialmente importante que la carpeta *.ssh* exista y no tenga permisos para nada ni nadie aparte del usuario propietario.

```bash
gerard@sshserver:~$ mkdir .ssh
gerard@sshserver:~$ chmod 700 .ssh/
gerard@sshserver:~$ cat .ssh/authorized_keys
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDHR7HSGhP8afT1pz/no+qVT1uKsEhh4CZXIbDebibbKiyPYVaKl/FLovYnCwk0IWXAsiJB1eXkQhX0he0gSK66UIZFnKVr8+G1J1kg9zuqxFTxpJTrM2WbdTZ+nk3bNgKTFKiQNsZ/IMvb/vjgU365LNtDclnajto0scgSCZQBvDfxrNVH8NIyv4IBTKheD6oSNgQsmzpvbWRyKBZf3dRRdVH00tsIC20fdAONtNfcWNToakRMX0/svW7RxUDlJEU/icsm3lf6xRf927CdB0ziu90i9mpzCxTMP3xbsrOJ0/mtdqROjql+OHNvxJa8FOtvX/ZdkNRAPOvuo4AieLZp root@client
gerard@sshserver:~$
```

Pueden haber varias claves públicas en el fichero *authorized_keys*, para garantizar la autenticación desde diferentes lugares sin compartir las claves entre los servidores de  origen.

## Comprobando su funcionamiento

Para ver que todo funciona, basta con intentar entrar en la sesión; si todo va bien, no nos va a pedir *password* sino *passphrase*, suponiendo que no la dejáramos en blanco.

```bash
root@client:~# ssh gerard@10.0.0.2

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Thu May 19 10:11:51 2016 from 10.0.0.3
gerard@sshserver:~$
```

De hecho, si ponemos el *flag* de *verbose*, vemos que el servidor origen **ofrece** automáticamente la clave generada. Si la clave no estuviera en los sitios normales, habría que indicarlo en el comando **ssh**.

```bash
root@client:~# ssh -v gerard@10.0.0.2
...
debug1: Connecting to 10.0.0.2 [10.0.0.2] port 22.
debug1: Connection established.
...
debug1: Authentications that can continue: publickey,password
debug1: Next authentication method: publickey
debug1: Offering RSA public key: /root/.ssh/id_rsa
...
debug1: Authentication succeeded (publickey).
...
gerard@sshserver:~$
```

Es importante recalcar que la parte privada que se ofrece es la que hay en la carpeta del usuario del servidor origen, pero la validación se hace con el fichero *authorized_keys* del usuario en el servidor remoto.
