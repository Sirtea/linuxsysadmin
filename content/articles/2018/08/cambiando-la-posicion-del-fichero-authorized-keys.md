---
title: "Cambiando la posición del fichero authorized_keys"
slug: "cambiando-la-posicion-del-fichero-authorized-keys"
date: 2018-08-13
categories: ['Sistemas']
tags: ['ssh', 'sftp', 'authorized_keys', 'jaula']
---

Un requerimiento de seguridad estándar en mi trabajo, es que los servidores SFTP no permitan la autenticación con *passwords* normales, y estamos obligados a usar autenticación por claves. El otro día tuvimos una queja de un usuario que no podía entrar porque había eliminado su carpeta `.ssh` de forma consciente.<!--more-->

En casos como este no nos queda más remedio que reirnos un rato y restablecer su fichero `authorized_keys` desde un *backup*. Sin embargo, hay varias preguntas que se nos deberían plantear en estos casos:

* ¿Por qué este usuario tenía permisos para escribir la carpeta `.ssh`?
* ¿Por qué estaba su fichero `authorized_keys` en su *home*?

Siempre debes pensar que un usuario puede meter la pata, y como son muchos, siempre tenemos muchos manazas con problemas similares. No hay nada que se pueda hacer en este sentido, pero debemos plantearnos si podemos evitar que el problema ocurrido se pueda repetir.

En este caso concreto, no tardamos mucho en evitar que se repitiera, ya que disponiamos de dos métodos sencillos para evitarlo:

1. Quitarle los permisos de escritura en la carpeta `.ssh`.
2. Quitar la carpeta `.ssh` de su línea de tiro, concretamente, fuera de su jaula.

Cabe decir que nos decantamos por la 2, y aquí explico como se hace.

## Mover el fichero authorized_keys de sitio

Empezamos con un *setup* estándar en donde **bob** puede entrar usando su clave ssh:

```bash
gerard@sirius:~$ sftp -i id_bob bob@sftpserver
Connected to sftpserver.
sftp> ls -la
drwxr-xr-x    4 0        0            4096 Jul 18 15:42 .
drwxr-xr-x    4 0        0            4096 Jul 18 15:42 ..
drwxr-xr-x    2 1001     1001         4096 Jul 18 15:42 .ssh
drwxr-xr-x    2 1001     1001         4096 Jul 18 15:38 archives
sftp>
```

Con los permisos mostrados, no le sería difícil eliminar su clave, que es la única manera permitida de entrar en su cuenta; así pues, vamos a mover la posición de dicho fichero para que no lo vea el usuario en su *home*.

El truco consiste en modificar la directiva `AuthorizedKeysFile` en el fichero `/etc/ssh/sshd_config`. Mas información en [las páginas *man*](https://linux.die.net/man/5/sshd_config). Especificamente nos interesa el *token* `%u`, que es el nombre del usuario que intenta logarse, en este caso, **bob**.

Como decisión de diseño, vamos a poner las claves en `/srv/sshkeys/<usuario>`, aunque esto es arbitrario y susceptible a cambio.

```bash
gerard@sftpserver:~$ cat /etc/ssh/sshd_config
...
AuthorizedKeysFile /srv/sshkeys/%u
...
Match Group sftponly
  ChrootDirectory %h
  ForceCommand internal-sftp
  PasswordAuthentication no
gerard@sftpserver:~$ sudo service ssh restart
gerard@sftpserver:~$
```

Nos cargamos la carpeta `.ssh` del usuario **bob** y la ponemos en `/srv/sshkeys/bob`:

```bash
gerard@sftpserver:~$ ls -la /home/bob/
total 12
drwxr-xr-x 3 root root 4096 jul 19 08:46 .
drwxr-xr-x 4 root root 4096 jul 18 17:35 ..
drwxr-xr-x 2 bob  bob  4096 jul 18 17:38 archives
gerard@sftpserver:~$ cat /srv/sshkeys/bob
ssh-rsa ...
gerard@sftpserver:~$
```

Y sin sorpresas, la mecánica no cambia nada, solo que en este caso, el usuario no tiene el fichero `authorized_keys` a tiro, y por lo tanto, no puede liarla.

```bash
gerard@sirius:~$ sftp -i id_bob bob@sftpserver
Connected to sftpserver.
sftp> ls -la
drwxr-xr-x    3 0        0            4096 Jul 19 06:46 .
drwxr-xr-x    3 0        0            4096 Jul 19 06:46 ..
drwxr-xr-x    2 1001     1001         4096 Jul 18 15:38 archives
sftp>
```

Y con esto nos ahorramos problemas futuros del tipo "he borrado la carpeta `.ssh`".
