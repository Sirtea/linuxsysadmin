---
title: "Restringiendo los comandos ejecutables con SSH y un par de claves"
slug: "restringiendo-los-comandos-ejecutables-con-ssh-y-un-par-de-claves"
date: 2019-06-10
categories: ['Operaciones']
tags: ['linux', 'ssh', 'jaula', 'authorized_keys']
---

Una petición muy habitual que recibo es la de algún usuario que quiere ejecutar "algo" en un servidor. Como no puede ser de otra manera dadas las restricciones de seguridad de la compañía, solo le puedo dar acceso por SSH; pero poner una jaula para restringir sus acciones es tedioso.<!--more-->

Por suerte para nosotros, SSH incluye un mecanismo para que un usuario autorizado a entrar por un par de claves SSH solo pueda ejecutar un comando concreto, y es extremadamente fácil de conseguir...

## Situación inicial

Supongamos que el usuario *arthur* quiere entrar en el servidor *avalon* para ejecutar algún comando de sistema o *script* propio, que le devuelva la información que necesita. Para ello, le vamos a crear un usuario con acceso por par de claves SSH; esto no resulta nada complicado y [ya lo hemos hecho antes]({{< relref "/articles/2016/05/autenticacion-ssh-por-claves.md" >}}).

```bash
root@avalon:/home/arthur/.ssh# cat authorized_keys 
ssh-rsa AAA... arthur@camelot
root@avalon:/home/arthur/.ssh# 
```

El problema en este punto es que el usuario puede entrar por SSH y hacer lo que sea, dentro de sus permisos habituales. Incluso puede hacer uso de una sesión interactiva y chafardear el sistema a voluntad.

```bash
arthur@camelot:~$ ssh -i id_avalon arthur@avalon
Linux avalon 4.9.0-9-amd64 #1 SMP Debian 4.9.168-1+deb9u2 (2019-05-13) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Mon Jun  3 10:37:47 2019 from 10.0.2.2
arthur@avalon:~$ 
```

Lo que queremos es que solo pueda ejecutar un solo *script*, pero no queremos entrar en las complejidades de montar una jaula para ello.

## SSH al rescate

El protocolo SSH nos permite añadir un comando prefijado a la clave en el fichero `authorized_keys`. Esto provocará que toda sesión SSH, interactiva o no, ejecute este comando o *script*. De esta forma no vamos a dar control al usuario para moverse a sus anchas por el sistema.

```bash
root@avalon:/home/arthur/.ssh# cat authorized_keys 
command="~/.ssh/restrict.sh" ssh-rsa AAA... arthur@camelot
root@avalon:/home/arthur/.ssh# 
```

El comando especificado debe estar disponible en el sistema, y si se trata de un *script* este debe estar disponible para que el usuario pueda ejecutarlo. Por poner un ejemplo podemos poner un saludo.

```bash
root@avalon:/home/arthur/.ssh# cat restrict.sh 
#!/bin/bash

echo "Hello ${USER}"
root@avalon:/home/arthur/.ssh# 
```

Todas las sesiones de SSH del usuario van a ejecutar este *script*, que hará lo que nos parezca más adecuado en cada caso. Al acabar el *script*, la sesión SSH se cierra y nos quedamos sin fisgones dando vueltas por el sistema.

```bash
arthur@camelot:~$ ssh -i id_avalon arthur@avalon
Hello arthur
Connection to localhost closed.
arthur@camelot:~$ 
```

Si pasamos otro comando, es ignorado en favor del que hemos indicado:

```bash
arthur@camelot:~$ ssh -i id_avalon arthur@avalon ls
Hello arthur
arthur@camelot:~$ 
```

**PROBLEMA**: Esta aproximación nos deja ejecutar **un solo comando**.

## Permitiendo varios comandos para una sola clave

Como hemos indicado, solo se puede lanzar un comando o *script* por clave SSH. sin embargo hay varias formas de ejecutar más de uno:

* Poner varias claves SSH por usuario, cada una con un comando permitido. Es un opción, aunque creo que la peor.
* Hacer que el *script* sea interactivo y se pueda elegir qué ejecutar.
* Permitir al *script* actuar según lo pida el usuario, de forma transparente y controlada.

### Un script interactivo

Nuestro *script* puede solicitar de forma interactiva lo que queramos ejecutar, simplemente aceptando entrada del usuario. luego podemos acabar el *script* (y por lo tanto, la sesión SSH) o podemos optar por iterar hasta que nos pidan acabar.

```bash
root@avalon:/home/arthur/.ssh# cat restrict.sh
#!/bin/bash

function menu() {
    echo "Hello ${USER}. Your choices are:
Your choices are:
1       See today's date
2       See who's logged in
q       Quit"
}

menu
echo -n "Your choice: "
read ans

while [ "$ans" != "q" ]
do
    case "$ans" in
        1) date ;;
        2) who ;;
        q)
            echo "Goodbye"
            exit 0
            ;;
        *) echo "Invalid choice '$ans': please try again"
    esac
    menu
    echo -n "Your choice: "
    read ans
done
root@avalon:/home/arthur/.ssh# 
```

Ahora el usuario dispone de un menú en el que puede elegir lo que quiere ejecutar, y por decisión de diseño, iremos repitiendo el menú de elección hasta la opción de salir:

```bash
arthur@camelot:~$ ssh -i id_avalon arthur@avalon
Hello arthur. Your choices are:
Your choices are:
1       See today's date
2       See who's logged in
q       Quit
Your choice: 1
lun jun  3 11:35:35 CEST 2019
Hello arthur. Your choices are:
Your choices are:
1       See today's date
2       See who's logged in
q       Quit
Your choice: 2
gerard   pts/0        2019-06-03 10:39 (10.0.2.2)
arthur   pts/1        2019-06-03 11:35 (10.0.2.2)
Hello arthur. Your choices are:
Your choices are:
1       See today's date
2       See who's logged in
q       Quit
Your choice: q
Connection to localhost closed.
arthur@camelot:~$ 
```

### Un script transparente

Cuando utilizamos esta técnica de limitación por comando, el comando original se pasa al *script* como la variable de entorno `SSH_ORIGINAL_COMMAND`. Podemos sacar provecho de esto y decidir lo que hacemos y lo que prohibimos mediante la inspección de lo que el usuario quería originalmente.

```bash
root@avalon:/home/arthur/.ssh# cat restrict.sh
#!/bin/bash

case "${SSH_ORIGINAL_COMMAND}" in
    pwd) pwd ;;
    whoami) whoami ;;
    *) echo "Can only execute 'pwd' and 'whoami', sorry"
esac
root@avalon:/home/arthur/.ssh# 
```

De esta manera, podemos evaluar el comando solicitado por el usuario y permitir ejecutarlo o denegarlo según nos parezca conveniente:

```bash
arthur@camelot:~$ ssh -i id_avalon arthur@avalon
Can only execute 'pwd' and 'whoami', sorry
Connection to localhost closed.
arthur@camelot:~$ ssh -i id_avalon arthur@avalon pwd
/home/arthur
arthur@camelot:~$ ssh -i id_avalon arthur@avalon whoami
arthur
arthur@camelot:~$ ssh -i id_avalon arthur@avalon ls
Can only execute 'pwd' and 'whoami', sorry
arthur@camelot:~$ 
```

## Conclusión

Estos ejemplos no son demasiado representativos del uso que le suelo dar en situaciones reales. Las peticiones suelen ser más complejas, sacando la información de una base de datos o del sistema operativo, cambiando su formato y usando otros lenguajes para conseguir lo que se necesita en cada momento.

Utilizando este método nos ahorramos las jaulas de forma fácil y sin renunciar a las facilidades que el sistema operativo original nos provee, como por ejemplo las librerías, intérpretes u otros binarios.
