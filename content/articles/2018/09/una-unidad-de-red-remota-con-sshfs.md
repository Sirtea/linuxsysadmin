---
title: "Una unidad de red remota con SSHFS"
slug: "una-unidad-de-red-remota-con-sshfs"
date: 2018-09-10
categories: ['Sistemas']
tags: ['unidad', 'remota', 'ssh', 'sshfs']
---

Es muy cómodo dejar un fichero en una carpeta local y saber que ese fichero está a salvo, en la nube; seguramente los que utilizáis un servicio de sincronización en la nube váis a estar de acuerdo. La empresas no suelen permitirlo, pero podéis utilizar un servicio local por **SSH**.<!--more-->

El ingenio se llama **SSHFS** y lanza las operaciones de lectura y escritura contra una máquina remota que solamente debe ofrecer **SSH**, de forma que para nosotros parece que se trate de un sistema de ficheros local.

## El servidor

Para utilizar **SSHFS** solo necesitamos un servidor que ofrezca **SSH**, aunque también funciona por **SFTP**. Como comodidad adicional, vamos a utilizar [autenticacíon por claves]({{< relref "/articles/2016/05/autenticacion-ssh-por-claves.md" >}}). Como conisderación de seguridad, vamos a enjaular al usuario que guarde los datos y lo vamos a lmitar a **SFTP**.

**NOTA**: Se asume que el servidor ya tiene el servidor **SSH** instalado; de no ser así, basta con hacer un `sudo apt install openssh-server`.

Lo primero es crear un usuario para que **SSHFS** pueda entrar al servidor por **SSH**/**SFTP**:

```bash
gerard@server:~$ sudo adduser nas
...
gerard@server:~$
```

Le asignamos la parte pública de la clave **SSH** en el fichero `~/.ssh/authorized_keys` para evitar que tengamos que introducir la contraseña cada vez que montemos la carpeta remota en el cliente, y para evitar ataques de fuerza bruta.

```bash
nas@server:~$ cat .ssh/authorized_keys
ssh-rsa ...
nas@server:~$
```

En este punto, ya podríamos entrar, pero como hemos decidido enjaular, tenemos que ajustar algunos permisos:

* La carpeta en donde lo enjaulemos (su *home*) debe pertenecer a **root**
* Esto nos obliga a tener una carpeta de trabajo en donde nuestro usuario pueda escribir
* Vamos a cambiar el propietario de la carpeta `.ssh` para evitar que este usuario [la pueda eliminar]({{< relref "/articles/2018/08/cambiando-la-posicion-del-fichero-authorized-keys.md" >}})

Con todo esto, la carpeta nos va a quedar así:

```bash
nas@server:/home$ tree -I gerard -augp
.
└── [drwxr-xr-x root     root    ]  nas
    ├── [drwxr-xr-x nas      nas     ]  archives
    └── [drwxr-xr-x root     root    ]  .ssh
        └── [-rw-r--r-- root     root    ]  authorized_keys

3 directories, 1 file
nas@server:/home$
```

Estamos listos para enjaular; modificamos el fichero `/etc/ssh/sshd_config` para enjaular a este usuario:

```bash
gerard@server:~$ cat /etc/ssh/sshd_config
...
Match User nas
        ChrootDirectory /home/%u
        ForceCommand internal-sftp
gerard@server:~$
```

Solo nos queda recargar el servicio **SSH** para que lea la nueva configuración.

```bash
gerard@server:~$ sudo service ssh restart
gerard@server:~$
```

## El cliente

Para poder montar el sistema de ficheros remoto, se necesita el paquete **sshfs**, así que lo instalamos.

```bash
gerard@client:~$ sudo apt-get install sshfs
...
gerard@client:~$
```

Necesitamos una carpeta en donde montar el sistema de ficheros remoto, que llamaremos `NAS`; como no la tengo, la creo:

```bash
gerard@client:~$ mkdir NAS
gerard@client:~$
```

Para montar la carpeta remota solo necesitamos un comando; asumimos que la parte privada de la clave **SSH** está en `.ssh/id_rsa`.

```bash
gerard@client:~$ sshfs nas@server:/archives NAS -o idmap=user
gerard@client:~$
```

A partir de ahora podemos trabajar en la carpeta como si de una carpeta local se tratara, por ejemplo:

```bash
gerard@client:~$ cd NAS/
gerard@client:~/NAS$ echo 123 > file
gerard@client:~/NAS$ touch emptyfile
gerard@client:~/NAS$ ls -lh
total 4,0K
-rw-r--r-- 1 nas nas 0 ago  8 12:25 emptyfile
-rw-r--r-- 1 nas nas 4 ago  8 12:25 file
gerard@client:~/NAS$
```

Y como es de esperar, estos ficheros han acabado en el servidor:

```bash
gerard@server:~$ tree -augp /home/nas/
/home/nas/
├── [drwxr-xr-x nas      nas     ]  archives
│   ├── [-rw-r--r-- nas      nas     ]  emptyfile
│   └── [-rw-r--r-- nas      nas     ]  file
└── [drwxr-xr-x root     root    ]  .ssh
    └── [-rw-r--r-- root     root    ]  authorized_keys

2 directories, 3 files
gerard@server:~$
```

En el momento que nos cansemos de utilizar la unidad de red, solo tenemos que desmontarla, y la seguiremos viendo con lo que tenía antes del montaje.

```bash
gerard@client:~$ fusermount -u NAS
gerard@client:~$ ls -lh NAS/
total 0
gerard@client:~$
```
