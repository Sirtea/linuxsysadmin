Title: Auditando las acciones de los usuarios de nuestro SFTP
Slug: auditando-las-acciones-de-los-usuarios-de-nuestro-sftp
Date: 2017-04-03 10:00
Category: Operaciones
Tags: sftp, ssh, auditoría



Algunas veces me he encontrado con usuarios de alguno de mis servidores SFTP que se quejan porque "les desaparecen archivos". Si estamos seguros que esas desapariciones no tienen nada que ver con nosotros, lo mas probable es que lo hayan hecho los mismos usuarios, sea manualmente o de forma automática.

En casos así, no podemos hacer nada para demostrar cuando y porqué ha pasado, pero podemos pillar al usuario *in fraganti* en casos posteriores. Para eso solo es necesario habilitar un nivel de trazas que nos permita capturar la actividad de un usuario.

El mismo servidor SFTP nos enviará esta actividad al *rsyslog* de forma automática si habilitamos el *loglevel* adecuado a nuestro comando SFTP. A partir de aquí se asume que el servicio *rsyslog* está instalado en nuestro sistema.

```bash
admin@sftpserver:~$ cat /etc/ssh/ssh_config 
...
ForceCommand internal-sftp -l VERBOSE
...
admin@sftpserver:~$ 
```

Esta directiva nos va a enviar las trazas al *rsyslog* escribiendo los mensajes en */dev/log*, **siempre desde el punto de vista de la sesión activa**. Eso significa que si hemos enjaulado a nuestros usuarios, la posición del dispositivo no será la de siempre; un usuario enjaulado en */srv/jails/guest/* debería tener el dispositivo en */srv/jails/guest/dev/log*.

La parte buena es que el mismo *rsyslog* se encarga de crear ese dispositivo para nosotros, con la configuración adecuada. Solo necesitamos crear la carpeta *dev/* en la jaula de nuestro usuario y añadir la directiva correcta.

```bash
admin@sftpserver:~$ mkdir /srv/jails/guest/dev
admin@sftpserver:~$ 
```

El otro punto espinoso es que la configuración del *rsyslog* no lleva ninguna regla por defecto para guardar esos *logs* en ningún fichero. Con añadir una nueva línea a la configuración de nuestro *rsyslog* será suficiente.

Podemos añadir ambas directivas mediante un fichero de configuración nuevo, utilizando la carpeta */etc/rsyslog.d/*, como sigue:

```bash
admin@sftpserver:~$ cat /etc/rsyslog.d/jails.conf 
$AddUnixListenSocket /srv/jails/guest/dev/log

:programname, isequal, "internal-sftp" -/var/log/sftp.log
admin@sftpserver:~$ 
```

Y tras recargar la configuración de los servicios SFTP y *rsyslog*, habremos acabado y podremos ver el resultado funcionando, asumiendo que haya entrado alguna sesión desde la recarga de los servicios.

```bash
admin@sftpserver:~$ cat /var/log/sftp.log
Nov 24 11:02:31 sftpserver internal-sftp[32]: session opened for local user guest from [172.17.0.1]
Nov 24 11:02:31 sftpserver internal-sftp[32]: received client version 3
Nov 24 11:02:31 sftpserver internal-sftp[32]: realpath "."
Nov 24 11:02:50 sftpserver internal-sftp[32]: opendir "/"
Nov 24 11:02:50 sftpserver internal-sftp[32]: closedir "/"
Nov 24 11:02:50 sftpserver internal-sftp[32]: lstat name "/archives"
Nov 24 11:02:52 sftpserver internal-sftp[32]: realpath "/archives/"
Nov 24 11:02:52 sftpserver internal-sftp[32]: stat name "/archives"
Nov 24 11:03:00 sftpserver internal-sftp[32]: open "/archives/testfile" flags WRITE,CREATE,TRUNCATE mode 0644
Nov 24 11:03:00 sftpserver internal-sftp[32]: close "/archives/testfile" bytes read 0 written 12
Nov 24 11:03:10 sftpserver internal-sftp[32]: opendir "/archives/"
Nov 24 11:03:10 sftpserver internal-sftp[32]: closedir "/archives/"
Nov 24 11:03:10 sftpserver internal-sftp[32]: lstat name "/archives/testfile"
Nov 24 11:03:12 sftpserver internal-sftp[32]: lstat name "/archives/testfile"
Nov 24 11:03:12 sftpserver internal-sftp[32]: remove name "/archives/testfile"
Nov 24 11:03:16 sftpserver internal-sftp[32]: session closed for local user guest from [172.17.0.1]
admin@sftpserver:~$ 
```

La lectura de estos *logs* es todo un arte; solo quiero recalcar que las sesiones se indican mediante el PID del *internal-sftp* y que las acciones son bastante descriptivas. En este caso solo hay una sesión que es la número 32.

Si intentamos entender lo que se ha hecho en esta sesión, vemos que las acciones mas importantes son el *open/close* de *testfile*, en modo de escritura y tras escribir 12 *bytes*. Poco después, en la misma sesión, se ha borrado el fichero. El resto de acciones se disparan cuando nos movemos por las carpetas.
