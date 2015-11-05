Title: Restart automático de servicios con systemd
Slug: restart-automatico-de-servicios-con-systemd
Date: 2015-11-05 22:30
Category: Sistemas
Tags: linux, debian, jessie, systemd, nginx



Cuando estamos gestionando un servidor, es posible que se caiga alguno
de sus servicios. Esto es especialmente molesto cuando nos interesa tener
un *uptime* elevado. Para conseguirlo, se han utilizado diferentes maneras,
desde poner personas a monitorizar en modo 24x7 hasta herramientas auxiliares
como gestores tipo *runit*, *supervisor* o *monit*.

Con la entrada en escena de *systemd* en la mayoría de distribuciones grandes
de *linux* este problema se ha acabado; el mismo proceso que hace de **init**
puede encargarse de mantener los procesos levantados, y reiniciarlos en caso
de caída.

En este tutorial pretendo hacer que un servicio estándar se vea beneficiado de
un **override**, que permita el inicio automático de un servicio cuando se cae,
sin tener que reescribir la **unit** que se encarga del servicio o proceso.

Partimos de un servidor básico *Linux* con *systemd*. En este caso vamos a
utilizar la última versión estable de *Debian*, a la que le vamos a instalar
un servicio estándar como *nginx* que nos va a servir como conejillo de indias.

```bash
root@server:~# apt-get install nginx-light
root@server:~# 
```

## Procedimiento

Como comprobación previa, observemos como este **restart** automático no
funciona; tenemos el servicio en ejecución, lo matamos y observamos que no
se levanta de nuevo, por mucho que esperemos.

```bash
root@server:~# ps faux | grep nginx
root       685  0.0  0.8   4556  2240 pts/0    S+   11:41   0:00          \_ grep nginx
root       662  0.0  0.7   6356  1856 ?        Ss   11:41   0:00 nginx: master process /usr/sbin/nginx -g daemon on; master_process on;
www-data   663  0.1  0.9   6504  2456 ?        S    11:41   0:00  \_ nginx: worker process                           
www-data   664  0.0  0.9   6504  2456 ?        S    11:41   0:00  \_ nginx: worker process                           
www-data   665  0.0  0.9   6504  2456 ?        S    11:41   0:00  \_ nginx: worker process                           
www-data   666  0.1  0.9   6504  2456 ?        S    11:41   0:00  \_ nginx: worker process                           
root@server:~# kill 662
root@server:~# ps faux | grep nginx
root       691  0.0  0.8   4556  2220 pts/0    S+   11:41   0:00          \_ grep nginx
root@server:~# 
```

Ahora necesitamos localizar el nombre de la **unit** que se encarga de ese
servicio, puesto que la carpeta de **overrides** debe llamarse igual.

```bash
root@server:~# systemctl list-units -a | grep nginx
  nginx.service    loaded    inactive dead    A high performance web server and a reverse proxy server
root@server:~# 
```

Como curiosidad, este fichero se encuentra en */lib/systemd/system/*,
siguiendo las convenciones del empaquetado de *Debian*. Alternativamente,
podemos localizar los ficheros instalados por un paquete con el
comando *dpkg -L nginx-light*.

```bash
root@server:~# ls -lh /lib/systemd/system/nginx.service 
-rw-r--r-- 1 root root 986 dic  1  2014 /lib/systemd/system/nginx.service
root@server:~# 
```

En caso de ser una **unit** escrita por nosotros, se encontraría en
*/etc/systemd/system/*. Esta es la convención:

* */lib/systemd/system/* &rarr; **units** de sistema, puestas por los paquetes instalados
* */lib/systemd/system/* &rarr; **units** o **overrides** puestos por el usuario (nosotros)

Para añadir nuevas directivas (**overrides**) a una **unit** sin reescribirla
entera, basta con crear una carpeta con su mismo nombre, concatenando **.d**.
Dentro podemos poner tantos ficheros *.conf* como creamos necesarios, añadiendo
las directivas que queramos añadir o modificar.

```bash
root@server:~# mkdir /etc/systemd/system/nginx.service.d
root@server:~# cat /etc/systemd/system/nginx.service.d/autorestart.conf
[Service]
Restart=always
RestartSec=1
root@server:~# 
```

En este caso, se ha indicado que queremos un **restart** siempre, sean cuales
sean las circunstancias en las que se cayó el proceso, y que espere 1 segundo
antes de intentarlo. Por como está hecho *systemd*, **no** va a levantar un
servicio que hemos parado invocando el comando *systemctl*.

Para que los cambios en el fichero de configuración se apliquen es necesario
recargar las configuraciones, indicando a *systemd* que tienen que recargarlas.

```bash
root@server:~# systemctl daemon-reload
root@server:~# 
```

## Comprobación

Básicamente vamos a repetir el paso de la comprobación; se localiza el
proceso **master** y se finaliza (por ejemplo, con un **SIGTERM** normal).

```bash
root@server:~# ps faux | grep nginx
root       782  0.0  0.8   4556  2252 pts/0    S+   11:56   0:00          \_ grep nginx
root       776  0.0  0.7   6356  1936 ?        Ss   11:56   0:00 nginx: master process /usr/sbin/nginx -g daemon on; master_process on;
www-data   777  0.0  1.0   6504  2536 ?        S    11:56   0:00  \_ nginx: worker process                           
www-data   778  0.0  1.0   6504  2536 ?        S    11:56   0:00  \_ nginx: worker process                           
www-data   779  0.0  1.0   6504  2536 ?        S    11:56   0:00  \_ nginx: worker process                           
www-data   780  0.0  1.0   6504  2536 ?        S    11:56   0:00  \_ nginx: worker process                           
root@server:~# kill 776
root@server:~# ps faux | grep nginx
root       787  0.0  0.9   4556  2280 pts/0    S+   11:56   0:00          \_ grep nginx
root@server:~# 
```

Ahora solo hay que esperar el paso de los segundos configurados, y volver a
ver si el servicio está corriendo; aunque en este esperé algo menos de lo
configurado; la paciencia no es una de mis virtudes...

```bash
root@server:~# ps faux | grep nginx
root       789  0.0  0.8   4556  2192 pts/0    S+   11:56   0:00          \_ grep nginx
root@server:~# ps faux | grep nginx
root       791  0.0  0.9   4556  2280 pts/0    S+   11:56   0:00          \_ grep nginx
root@server:~# ps faux | grep nginx
root       802  0.0  0.8   4556  2236 pts/0    S+   11:56   0:00          \_ grep nginx
root       796  0.0  0.7   6356  1932 ?        Ss   11:56   0:00 nginx: master process /usr/sbin/nginx -g daemon on; master_process on;
www-data   797  0.0  1.0   6504  2592 ?        S    11:56   0:00  \_ nginx: worker process                           
www-data   798  0.0  1.0   6504  2592 ?        S    11:56   0:00  \_ nginx: worker process                           
www-data   799  0.0  1.0   6504  2592 ?        S    11:56   0:00  \_ nginx: worker process                           
www-data   800  0.0  1.0   6504  2532 ?        S    11:56   0:00  \_ nginx: worker process                           
root@server:~# 
```

Y con esto tenemos nuestro **autorestart** para este servicio.
