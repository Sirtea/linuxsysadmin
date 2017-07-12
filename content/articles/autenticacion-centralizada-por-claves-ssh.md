Title: Autenticación centralizada por claves SSH
Slug: autenticacion-centralizada-por-claves-ssh
Date: 2017-07-17 10:00
Category: Sistemas
Tags: ssh / autenticación / password / passphrase / centralizado



Ya vimos en [un artículo anterior]({filename}/articles/autenticacion-ssh-por-claves.md) como autenticar las sesiones **SSH** mediante claves locales en la máquina. Sin embargo, esto no es práctico cuando tenemos muchos servidores, y hay que replicar esas claves en todos ellos. Hoy vamos a ver como usar un *script* que pueda sacar las claves dinámicamente.

Empezamos teniendo un servidor con el servicio **SSH** levantado; vamos a crear un usuario *guest* en él para que pueda abrir una sesión en él.

## Estado inicial

```bash
root@sshserver:~# adduser guest
Adding user `guest' ...
Adding new group `guest' (1000) ...
Adding new user `guest' (1000) with group `guest' ...
Creating home directory `/home/guest' ...
Copying files from `/etc/skel' ...
Enter new UNIX password: 
Retype new UNIX password: 
passwd: password updated successfully
Changing the user information for guest
Enter the new value, or press ENTER for the default
	Full Name []: 
	Room Number []: 
	Work Phone []: 
	Home Phone []: 
	Other []: 
Is the information correct? [Y/n] y
root@sshserver:~# 
```

Por supuesto, este usuario pueden entrar con su contraseña sin problemas.

```
gerard@sirius:~/docker/ssh$ ssh guest@sshserver
guest@sshserver's password: 

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
guest@sshserver:~$ 
```

## El script

La idea es que necesitamos un *script* que reciba como primer parámetro el usuario del que queremos las claves, y este *script* nos va a dar una salida con el mismo formato que pondríamos en el *authorized_keys*. Eso significa que podemos devolver 0, 1 o mas líneas, con una clave pública por línea.

No es importante de donde saque este *script* la información; puede ser de un campo LDAP, de una base de datos, o de una llamada a un *webservice*. Para evitar complicaciones innecesarias, para este artículo y a modo de ejemplo, vamos a poner los valores en el mismo *script*. Echad un poco de imaginación si lo reproducís.

Supongamos que queremos entrar con el usuario *guest*, y disponemos en la máquina inicial la clave privada *id_rsa*, habiendo generado una clave pública correspondiente. Creamos un *script* que nos vuelque esta clave si el usuario solicitado es *guest*, siempre con permisos de ejecución.

```bash
root@sshserver:~# cat /usr/bin/authorized_keys_by_user.sh 
#!/bin/bash

if [ "$1" == "guest" ]; then
    echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC9heqwqgv+O9aekeCpETDR/6BdTQWDOrSlNN/tnZeZZa8/qjf0JEF4r8jSA/MquPQog1tpOXM0XUEY9YWNphARAmZ/gV1IiNJZmqQJSb2pk2/nQLq9nCqWoHBgKHKINUKfgmsiopGz9IjnZw5BBZKrloE9ZU0oApduxnVUTl/G71OWH/SdCbef08zvwVvLxv3zAWEKSnRvnSn5Q/FkRNb4Qe09po8ePgMqpZWKUvEpAntOvokI7uid300mmZjiUL8EMbJo4oJ3ONOnDbH8FNKEmGI4q2UK5HbDIUm8SJcmyJXvoo6xabApkc2AcM7X2tXRd8wiYS0p7YjLVMcIJ/NR gerard@sirius"
fi
root@sshserver:~# chmod 755 /usr/bin/authorized_keys_by_user.sh 
root@sshserver:~# 
```

Podemos comprobar que nos da la clave pública para el usuario *guest* y ninguna para otros usuarios.

```bash
root@sshserver:~# /usr/bin/authorized_keys_by_user.sh guest
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC9heqwqgv+O9aekeCpETDR/6BdTQWDOrSlNN/tnZeZZa8/qjf0JEF4r8jSA/MquPQog1tpOXM0XUEY9YWNphARAmZ/gV1IiNJZmqQJSb2pk2/nQLq9nCqWoHBgKHKINUKfgmsiopGz9IjnZw5BBZKrloE9ZU0oApduxnVUTl/G71OWH/SdCbef08zvwVvLxv3zAWEKSnRvnSn5Q/FkRNb4Qe09po8ePgMqpZWKUvEpAntOvokI7uid300mmZjiUL8EMbJo4oJ3ONOnDbH8FNKEmGI4q2UK5HbDIUm8SJcmyJXvoo6xabApkc2AcM7X2tXRd8wiYS0p7YjLVMcIJ/NR gerard@sirius
root@sshserver:~# /usr/bin/authorized_keys_by_user.sh other
root@sshserver:~# 
```

En este caso hemos puesto una sola clave, pero podrían haber sido varias, igual que cuando usamos el fichero *authorized_keys*.

## Configuración SSH

Por una limitación del servicio **SSH**, es necesario que tanto el *script* como todas las carpetas en el *path*, pertenezcan al usuario *root* y que solo este tenga permisos de escritura. Aunque nos saldría un mensaje de error en el *log* del **SSH**, cuesta poco de comprobarlo antes.

```bash
root@sshserver:~# for folder in / /usr /usr/bin /usr/bin/authorized_keys_by_user.sh; do stat --printf "%U:%G\t%A %n\n" $folder; done
root:root	drwxr-xr-x /
root:root	drwxr-xr-x /usr
root:root	drwxr-xr-x /usr/bin
root:root	-rwxr-xr-x /usr/bin/authorized_keys_by_user.sh
root@sshserver:~# 
```

El truco consiste en indicar dos directivas al demonio **SSH**, para que sepa que debe ejecutar este *script* para sacar el *authorized_keys* de cada usuario.

```
root@sshserver:~# tail -2 /etc/ssh/sshd_config 
AuthorizedKeysCommand /usr/bin/authorized_keys_by_user.sh
AuthorizedKeysCommandUser nobody
root@sshserver:~# 
```

Recargamos la configuración del demonio **SSH**, para que relea la configuración nueva que acabamos de poner.

```bash
root@sshserver:~# service ssh reload
Reloading OpenBSD Secure Shell server's configuration: sshd.
root@sshserver:~# 
```

Y solo nos queda comprobar que podemos entrar con el usuario *guest* usando la clave privada. En este ejemplo no se indica porque la clave *.ssh/id_rsa* es ofrecida por defecto, y es la parte privada de la clave que pusimos en el *script* remoto.

```bash
gerard@sirius:~/docker/ssh$ ssh guest@sshserver

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Thu Jul 21 08:39:21 2016 from 172.20.0.1
guest@sshserver:~$ 
```

A partir de aquí, podéis modificar el *script* remoto para que saque la información de las claves de algún sitio centralizado (LDAP, base de datos, *webservice*, ...).
