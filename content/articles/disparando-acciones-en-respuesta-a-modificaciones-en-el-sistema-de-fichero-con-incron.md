Title: Disparando acciones en respuesta a modificaciones en el sistema de fichero con incron
Slug: disparando-acciones-en-respuesta-a-modificaciones-en-el-sistema-de-fichero-con-incron
Date: 2016-10-03 08:00
Category: Sistemas
Tags: 



El otro día recibí una petición diferente en mi trabajo. Se necesitaba monitorizar una carpeta, de forma que cuando alguien dejara ficheros, se lanzara una tarea para procesarlos. Tras buscar un poco por internet, topé con una herramienta tipo *cron*, que ejecutaba comandos ante eventos en el sistema de ficheros.

Como me pareció interesante, me puse a investigar como funcionaba y, aunque no sirvió para cubrir nuestras necesidades, decidí apuntarla por sus usos potenciales en el futuro.

Como no podía ser de otra forma, vamos a empezar instalando el paquete que lo contiene:

```bash
root@65b056d5d699:~# apt-get install -y incron
Reading package lists... Done
Building dependency tree       
Reading state information... Done
The following NEW packages will be installed:
  incron
0 upgraded, 1 newly installed, 0 to remove and 0 not upgraded.
Need to get 68.8 kB of archives.
After this operation, 321 kB of additional disk space will be used.
...  
Processing triggers for systemd (215-17+deb8u4) ...
root@65b056d5d699:~# 
```

Normalmente, los servicios se levantan solos en **Debian**, pero como estamos trabajando con un contenedor **docker** mediante **SSH**, vamos a tener que hacerlo manualmente.

```bash
root@65b056d5d699:~# service incron start
[ ok ] Starting File system events scheduler: incron.
root@65b056d5d699:~# 
```

Esta herramienta se puede configurar de forma similar al **cron**; tenemos la opción de poner ficheros de configuración en */etc/incron.d/* o podemos usar comandos de **incron** por usuario, mediante el comando *incron*, con los flags correspondientes.

* **incron -l** &rarr; lista la tabla de incron del usuario actual
* **incron -e** &rarr; edita la tabla de incron del usuario actual
* **incron -r** &rarr; elimina la tabla de incron del usuario actual

Para usar **incron** a nivel de usuario, este debe aparecer en */etc/incron.allow*.

## Un caso práctico

Supongamos que tenemos un servidor web **nginx**.

```bash
root@65b056d5d699:/etc/nginx/sites-enabled# netstat -lntp
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      249/nginx       
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      1/sshd          
tcp6       0      0 :::22                   :::*                    LISTEN      1/sshd          
root@65b056d5d699:/etc/nginx/sites-enabled# 
```

Estamos cansados de recargar la configuración cada vez que modificamos alguno de los ficheros de configuración, así que vamos a delegar esta tarea a **incron**. Concretamente queremos que cada vez que se modifique el fichero */etc/nginx/nginx.conf* o algunos de los *virtualhosts* en */etc/nginx/sites-enabled/*, se haga un *reload* del servicio.

Miramos la tabla de eventos posibles a monitorizar y vemos que nos interesa el evento **IN_MODIFY**. Se pueden monitorizar varios eventos uniéndolos con un **OR** lógico, pero no se pueden poner mas de una línea por carpeta monitorizada.

* **IN_ACCESS** &rarr; Se ha accedido al fichero o directorio.
* **IN_ATTRIB** &rarr; Se han cambiado los *metadatos* (o los *timestamps*).
* **IN_CLOSE_WRITE** &rarr; Se ha cerrado un fichero abierto en modo distinto al de escritura.
* **IN_CLOSE_NOWRITE** &rarr; Se ha cerrado un fichero abierto en modo de escritura.
* **IN_CREATE** &rarr; Se ha creado un fichero en el directorio monitorizado.
* **IN_DELETE** &rarr; Se ha borrado un fichero en la carpeta.
* **IN_DELETE_SELF** &rarr; El fichero o directorio monitorizado ha sido borrado.
* **IN_MODIFY** &rarr; El fichero ha sido modificado.
* **IN_MOVE_SELF** &rarr; El fichero o carpeta monitorizado se ha movido.
* **IN_MOVED_FROM** &rarr; Un fichero se ha movido desde la carpeta monitorizada.
* **IN_MOVED_TO** &rarr; Un fichero se ha movido hacia la carpeta monitorizada.
* **IN_OPEN** &rarr; Se ha abierto un fichero en la carpeta monitorizada.
* **IN_MOVE** &rarr; Combinación de IN_MOVED_FROM y de IN_MOVED_TO.
* **IN_CLOSE** &rarr; Combinación de IN_CLOSE_WRITE y IN_CLOSE_NOWRITE.
* **IN_ALL_EVENTS** &rarr; Todos los eventos anteriores.

Así pues, ponemos la tripleta *carpeta, evento, acción*, ya sea con el comando *incron -e* o mediante un fichero en */etc/incron.d/*. Es importante indicar que la salida del comando no se puede recoger en este fichero; si es necesario, habría que llamar a un *script* que tuviera la redirección.

```bash
root@65b056d5d699:~# cat /etc/incron.d/nginx 
/etc/nginx/nginx.conf IN_MODIFY /usr/sbin/service nginx reload
/etc/nginx/sites-enabled/ IN_MODIFY /usr/sbin/service nginx reload
root@65b056d5d699:~# 
```

En este punto no hay que recargar nada; **incron** ha detectado el cambio y se ha recargado solo.

Vamos a cambiar, por ejemplo, el puerto en el que escucha nuestra web.

**ANTES:**

```bash
root@65b056d5d699:~# cat /etc/nginx/sites-enabled/mysite 
server {
	listen 80 default_server;
	root /var/www/html;
	server_name _;
}
```

**DESPUES:**

```bash
root@65b056d5d699:~# cat /etc/nginx/sites-enabled/mysite 
server {
	listen 8080 default_server;
	root /var/www/html;
	server_name _;
}
root@65b056d5d699:~# 
```

Y sin recargar la configuración de **nginx** -puesto que ya lo ha hecho **incron**-, vemos que se ha puesto a escuchar en el nuevo puerto.

```bash
root@65b056d5d699:~# netstat -lntp
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN      249/nginx       
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      1/sshd          
tcp6       0      0 :::22                   :::*                    LISTEN      1/sshd          
root@65b056d5d699:~# 
```

## Ejecución parametrizada de nuestras tareas

El proceso de **incron** nos ofrece unos parámetros para discernir cual de los eventos disparó el *trigger*:

* **$$** &rarr; Símbolo de dólar.
* **$@** &rarr; Ruta de la carpeta monitorizada.
* **$#** &rarr; Fichero modificado.
* **$%** &rarr; Evento que disparó la acción, en texto.
* **$&** &rarr; Evento que disparó la acción, en número.

Si quisiéramos procesar un fichero tal como nos lo dejen en una carpeta, podemos usar un *script* con parámetros que haga lo que deba con el mismo.

```bash
root@65b056d5d699:~# cat /etc/incron.d/batch_process 
/opt/batch_process/inbox/ IN_WRITE_CLOSE /opt/batch_process/process_file.py $@ $#
root@65b056d5d699:~# 
```

Este *script* recibe la ruta de la carpeta monitorizada y el fichero. Lo que hace el *script* se deja a la imaginación del lector. Como punto adicional, recalcar que se ha usado el evento **IN_WRITE_CLOSE** en vez de **IN_CREATE** porque este último salta inmediatamente, y podríamos encontrarnos con un fichero a medio subir, en caso de ser puesto por un protocolo remoto.

Estoy seguro que en un futuro no muy lejano, esta herramienta me va a ser de gran utilidad.
