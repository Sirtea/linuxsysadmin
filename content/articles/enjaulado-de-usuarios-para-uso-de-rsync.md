Title: Enjaulado de usuarios para uso de rsync
Slug: enjaulado-de-usuarios-para-uso-de-rsync
Date: 2016-01-04 10:00
Category: Seguridad
Tags: linux, rsync, rssh, ssh, ldd, jaula



Todos nos hemos encontrado alguna vez con una web, sea en *HTML* o en *PHP*, que se compone de centenares o miles de ficheros, y que hay que ir actualizando cada vez que cambian unos pocos ficheros. En estos casos la capacidad incremental de la herramienta **rsync** puede ayudarnos mucho.

Sin embargo, la herramienta **rsync** funciona por el puerto de *SSH*, y dar acceso al mismo es un problema desde el punto de vista de la seguridad del sistema. Vamos a crear una jaula para los usuarios que lo necesiten, y vamos a limitar los comandos que puede utilizar, de forma que solo pueda hacer **rsync**.

Para poder continuar, necesitamos las 2 herramientas que se van a usar: **rsync** y **rssh**.

```bash
root@webserver:~# apt-get install rssh rsync
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias       
Leyendo la información de estado... Hecho
...
Se instalarán los siguientes paquetes NUEVOS:
  libpopt0 rssh rsync
0 actualizados, 3 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 505 kB de archivos.
Se utilizarán 962 kB de espacio de disco adicional después de esta operación.
...
root@webserver:~# 
```

## Preparación del sistema de enjaulado

Como decisión de diseño, he decidido que voy a enjaular todos los usuarios que pertenezcan a un grupo, al que llamaremos *restricted*.

```bash
root@webserver:~# groupadd restricted
root@webserver:~# 
```

Ahora vamos a configurar el demonio **SSH** para que todos los usuarios del grupo *restricted* queden enjaulados en */srv/jails/*, en una carpeta por usuario. La directiva *X11Forwarding* y *AllowTcpForwarding* son restricciones adicionales y no son necesarias.

```bash
root@webserver:~# cat /etc/ssh/sshd_config 
...
Match group restricted
	ChrootDirectory /srv/jails/%u
	X11Forwarding no
	AllowTcpForwarding no
root@webserver:~# 
```

Y reiniciamos el demonio para que se apliquen las modificaciones en la configuración.

```bash
root@webserver:~# service ssh restart
root@webserver:~# 
```

## Creando una jaula para el primer usuario

Para tener un usuario enjaulado, necesitamos un usuario, en este caso, el usuario *web*. Le vamos a poner *rssh* como shell, su carpeta personal como */* y le asignamos el grupo *restricted* para que quede enjaulado.

```bash
root@webserver:~# useradd -d / -s /usr/bin/rssh -G restricted web
root@webserver:~# 
```

Para que el usuario *web* pueda entrar en esta máquina, necesita una contraseña. Alternativamente, podríamos haber montado una autenticación por claves *SSH*.

```bash
root@webserver:~# passwd web
Introduzca la nueva contraseña de UNIX: 
Vuelva a escribir la nueva contraseña de UNIX: 
passwd: contraseña actualizada correctamente
root@webserver:~# 
```

Y ahora vamos a crearle una estructura de carpetas muy básica en donde deberá estar su jaula. Puesto que se trata del usuario *web*, la carpeta de la jaula (la que el usuario verá como */*) va a ser */srv/jails/web/*.

**IMPORTANTE**: Esta carpeta y todas las de la ruta deben perteneces al usuario *root* y tener permisos de escritura solo por el *owner*; de otra manera, el *SSH* falla al enjaular.

```bash
root@webserver:~# mkdir -p /srv/jails/web/{usr/bin,etc,lib}
root@webserver:~# 
```

Para limitar que el usuario solo pueda hacer *rsync* vamos a necesitar la ayuda de *rssh*; así pues, vamos a poner ambos binarios en la jaula.

```bash
root@webserver:~# cp /usr/bin/rssh /srv/jails/web/usr/bin/
root@webserver:~# cp /usr/bin/rsync /srv/jails/web/usr/bin/
root@webserver:~# 
```

Estos dos comandos son binarios *linkados* dinámicamente que necesitan librerías. Vamos a buscarlos con el comando **ldd**.

```bash
root@webserver:~# ldd /usr/bin/rssh 
	linux-gate.so.1 (0xb7789000)
	libc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xb760a000)
	/lib/ld-linux.so.2 (0xb778c000)
root@webserver:~# ldd /usr/bin/rsync 
	linux-gate.so.1 (0xb7741000)
	libattr.so.1 => /lib/i386-linux-gnu/libattr.so.1 (0xb76a3000)
	libacl.so.1 => /lib/i386-linux-gnu/libacl.so.1 (0xb7699000)
	libpopt.so.0 => /lib/i386-linux-gnu/libpopt.so.0 (0xb768a000)
	libc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xb7519000)
	/lib/ld-linux.so.2 (0xb7744000)
root@webserver:~# 
```

Y las copiamos en la carpeta *lib* de la jaula.

```bash
root@webserver:~# cp /lib/ld-linux.so.2 /srv/jails/web/lib/
root@webserver:~# cp /lib/i386-linux-gnu/libc.so.6 /srv/jails/web/lib/
root@webserver:~# cp /lib/i386-linux-gnu/libattr.so.1 /srv/jails/web/lib/
root@webserver:~# cp /lib/i386-linux-gnu/libacl.so.1 /srv/jails/web/lib/
root@webserver:~# cp /lib/i386-linux-gnu/libpopt.so.0 /srv/jails/web/lib/
root@webserver:~# 
```

Voy a quitar los permisos de ejecución de la librería *libc* porque no lo necesita.

```bash
root@webserver:~# chmod 644 /srv/jails/web/lib/libc.so.6 
root@webserver:~# 
```

Ahora que tenemos las librerías en la jaula, volvemos a mirar que otras librerías puedan necesitar con **ldd**, para evitar dejarnos ninguna.

```bash
root@webserver:~# ldd /srv/jails/web/lib/*
/srv/jails/web/lib/ld-linux.so.2:
	statically linked
/srv/jails/web/lib/libacl.so.1:
	linux-gate.so.1 (0xb77b3000)
	libattr.so.1 => /lib/i386-linux-gnu/libattr.so.1 (0xb779e000)
	libc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xb762d000)
	/lib/ld-linux.so.2 (0xb77b6000)
/srv/jails/web/lib/libattr.so.1:
	linux-gate.so.1 (0xb7756000)
	libc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xb75da000)
	/lib/ld-linux.so.2 (0xb7759000)
/srv/jails/web/lib/libc.so.6:
	/lib/ld-linux.so.2 (0xb779f000)
	linux-gate.so.1 (0xb779c000)
/srv/jails/web/lib/libpopt.so.0:
	linux-gate.so.1 (0xb7782000)
	libc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xb75fe000)
	/lib/ld-linux.so.2 (0xb7785000)
root@webserver:~# 
```

Y como no han entrado de nuevas, hemos acabado con esto. Ahora vamos a copiar la configuración de **rssh**.

```bash
root@webserver:~# cp /etc/rssh.conf /srv/jails/web/etc/
root@webserver:~# 
```

Vamos a añadir la directiva *allowrsync* ya que, por defecto, no se permite nada:

**ANTES**:

```bash
root@webserver:~# grep allowrsync /srv/jails/web/etc/rssh.conf 
#allowrsync
root@webserver:~# 
```

**DESPUES**:

```bash
root@webserver:~# grep allowrsync /srv/jails/web/etc/rssh.conf 
allowrsync
root@webserver:~# 
```

Como estamos esperando que el usuario *web* deje sus cosas en una carpeta *www*, vamos a crearla, ya que va a ser la única en la que pueda copiar sus cosas.

```bash
root@webserver:~# mkdir /srv/jails/web/www
root@webserver:~# 
```

Y le damos permisos necesarios para que escriba en ella; por ejemplo, le damos la propiedad de la carpeta.

```bash
root@webserver:~# chown web:web /srv/jails/web/www/
root@webserver:~# 
```

Y con esto queda completa la jaula. Como demostración, muestro la salida del comando **tree**:

```bash
root@webserver:~# tree /srv/jails/web/
/srv/jails/web/
├── etc
│   └── rssh.conf
├── lib
│   ├── ld-linux.so.2
│   ├── libacl.so.1
│   ├── libattr.so.1
│   ├── libc.so.6
│   └── libpopt.so.0
├── usr
│   └── bin
│       ├── rssh
│       └── rsync
└── www

5 directories, 8 files
root@webserver:~# 
```

## Uso de la jaula

Supongamos que tenemos un proyecto web en una máquina *developer*, por ejemplo:

```bash
gerard@developer:~$ tree web/
web/
└── index.html

0 directories, 1 file
gerard@developer:~$ 
```

Intentamos entrar por *SSH* y vemos que falla:

```bash
gerard@developer:~$ ssh web@10.0.0.2
web@10.0.0.2's password: 

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Wed Dec 30 21:12:44 2015 from 10.0.0.3

This account is restricted by rssh.
Allowed commands: rsync 

If you believe this is in error, please contact your system administrator.

Connection to 10.0.0.2 closed.
gerard@developer:~$ 
```

Vamos a usar *rsync* para sincronizar este proyecto con el servidor que acabamos de montar. Para eso, la máquina cliente necesita tener instalado el paquete **rsync**.

```bash
gerard@developer:~$ rsync -rvzc --delete web/ web@10.0.0.2:/www
web@10.0.0.2's password: 
sending incremental file list
index.html

sent 139 bytes  received 35 bytes  49.71 bytes/sec
total size is 12  speedup is 0.07
gerard@developer:~$ 
```

Si repetimos el comando, vemos que la lista de ficheros no incluye el *index.html*, porque no ha cambiado respecto a lo que tenemos en el servidor, así que no lo manda.

```bash
gerard@developer:~$ rsync -rvzc --delete web/ web@10.0.0.2:/www
web@10.0.0.2's password: 
sending incremental file list

sent 83 bytes  received 12 bytes  7.60 bytes/sec
total size is 12  speedup is 0.13
gerard@developer:~$ 
```

los *flags* elegidos son **-r** (recursivo), **-v** (verbose), **-z** (comprimido), **-c** (diferenciar por *checksum*) y **--delete** (para borrar fichero que estén en el servidor y no deban).

**IMPORTANTE**: la carpeta origen acaba con */*. Esa es la diferencia entre copiar el contenido de la carpeta y copiar la carpeta misma.

Analizamos el resultado y vemos que lo hemos copiado en */www/*, siempre desde el punto de vista de la jaula.

```bash
root@webserver:~# ls /www
ls: no se puede acceder a /www: No existe el fichero o el directorio
root@webserver:~# tree /srv/jails/web/
/srv/jails/web/
├── etc
│   └── rssh.conf
├── lib
│   ├── ld-linux.so.2
│   ├── libacl.so.1
│   ├── libattr.so.1
│   ├── libc.so.6
│   └── libpopt.so.0
├── usr
│   └── bin
│       ├── rssh
│       └── rsync
└── www
    └── index.html

5 directories, 9 files
root@webserver:~# 
```

Y con esto está todo hecho. Solo falta instalar el servidor web, pero eso lo dejo pendiente.
