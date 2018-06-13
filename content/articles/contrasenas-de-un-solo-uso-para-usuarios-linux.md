Title: Contraseñas de un solo uso para usuarios linux
Slug: contrasenas-de-un-solo-uso-para-usuarios-linux
Date: 2018-06-18 10:00
Category: Operaciones
Tags: password, temporal, caducar



No dejan de sorprenderme los administradores de sistemas que crean usuarios a petición, pero les asignan *passwords* supuestamente de un solo uso pidiéndoles que la cambien en el primer uso. La experiencia me dice que esa *password* solo se cambia si es estrictamente necesario. Esta petición la puedes forzar fácilmente.

## Un ejemplo

Vamos a simular una de estas peticiones, de un usuario *bob* que quiere acceder a un servidor llamado *server*. Un administrador tradicional va a ejecutar un comando estándar para crear el usuario, y le va a asignar una contraseña, posiblemente de diccionario.

### El problema

El servidor en cuestión es un servidor simulado, montado con **Alpine Linux**, y esto es lo que se ejecutaría en él:

```bash
/ # adduser -D bob
/ # echo "bob:temporal" | chpasswd 
chpasswd: password for 'bob' changed
/ # 
```

Le mandamos el par de usuario y contraseña al usuario, muchas veces usando un canal relativamente inseguro, como el correo electrónico o mediante un *post-it*. Le pedimos al usuario que la cambie, pero no podemos obligarle. Simplemente quiere entrar al servidor.

```bash
gerard@sirius:~/workspace/server$ ssh bob@server
bob@localhost's password: 
Welcome to Alpine!

The Alpine Wiki contains a large amount of how-to guides and general
information about administrating Alpine systems.
See <http://wiki.alpinelinux.org>.

You can setup the system with the command: setup-alpine

You may change this message by editing /etc/motd.

server:~$ 
```

Y tras ver que le funciona aparta la tarea y jamás se acuerda de cambiar su contraseña; otros directamente pasan de hacerlo, o se creen que su *post-it* es ley; lo pegan en su monitor y la seguridad de la cuenta queda altamente comprometida.

### La solución

La mejor forma que tenemos de forzar el cambio de la contraseña, sin tener demasiado trabajo, es delegarlo al sistema operativo. Las contraseñas en *linux* pueden configurarse para **caducar**. De hecho, directamente la podemos marcar como caducada, lo que va a forzar su cambio en el primer *login*.

Esto se hace mediante el comando `chage`, que nos permite el *flag* `-d`, que es el que indica la fecha del último cambio de contraseña. Este *flag* acepta el valor especial `0` que obliga a que el usuario cambie su contraseña tras el primer *login*. Esto se puede hacer en cualquier momento, pero es interesante hacerlo antes de mandarle la contraseña, cuando su usuario ya exista.

```bash
/ # chage -d 0 bob
/ # 
```

**NOTA**: El comando `chage` se encuentra en el paquete **shadow** en **Alpine Linux**; otras distribuciones lo tienen en el paquete **passwd**. Si no disponéis del comando, instalad el paquete adecuado.

El resultado es que el usuario va a poder entrar, pero no va a poder hacer nada hasta que haga un cambio de contraseña de forma exitosa. Por supuesto, esto invalida la contraseña temporal que le hayamos podido dar, y hace de nuestro servidor un lugar un poco más seguro.

```bash
gerard@sirius:~/workspace/server$ ssh bob@server
bob@localhost's password: 
Welcome to Alpine!

The Alpine Wiki contains a large amount of how-to guides and general
information about administrating Alpine systems.
See <http://wiki.alpinelinux.org>.

You can setup the system with the command: setup-alpine

You may change this message by editing /etc/motd.

WARNING: Your password has expired.
You must change your password now and login again!
Changing password for bob.
Current password: 
```

A partir de aquí, depende del usuario saber donde apunta la contraseña y con quien la comparte.
