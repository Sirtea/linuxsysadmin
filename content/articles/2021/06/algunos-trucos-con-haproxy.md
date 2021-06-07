---
title: "Algunos trucos con Haproxy"
slug: "algunos-trucos-con-haproxy"
date: "2021-06-04"
categories: ['Sistemas']
tags: ['haproxy', 'configuración', 'systemd', 'https', 'sni', 'certificado']
---

Hace tiempo que no usaba **haproxy**. Puede ser porque he priorizado otras
soluciones, sean otros servicios como **nginx** o, simplemente la plataforma
ya me ofrecía soluciones incorporadas o empresariales. Pero la verdad es que
**haproxy** funciona, y es una solución a la que vuelvo de forma recurrente.<!--more-->

Y es que cada vez que configuro este servicio descubro algún truco nuevo que
puedo aplicar a mis sistemas. Este artículo pretende exponer algunos de estos
trucos.

Para ello, partimos de un sistema **Debian 10**, aunque podría haber sido
cualquier otro sistema operativo que use **systemd**, ya que uno de los trucos
depende de él. Si la máquina no tiene haproxy instalado, es momento de hacerlo.

```bash
gerard@loadbalancer:~$ sudo apt install haproxy
...
gerard@loadbalancer:~$
```

## Configuración separada en snippets

Uno de los inconvenientes de **haproxy** es que la configuración viene en
un fichero de configuración único. Esto no es un problema para configuraciones
simples con un número reducido de *frontends* y *backends*, pero no es cómodo
en configuraciones de muchos dominios.

Vamos a utilizar la propiedad `ExecStartPre` de **systemd** para juntar los
*snippets* en un fichero de configuración utilizable, antes de levantar el
servicio. Para ello vamos a crear una carpeta para los propios *snippets*
de la configuración:

```bash
gerard@loadbalancer:/etc/haproxy$ pwd
/etc/haproxy
gerard@loadbalancer:/etc/haproxy$ ls
errors  haproxy.cfg
gerard@loadbalancer:/etc/haproxy$ sudo mkdir conf.d
gerard@loadbalancer:/etc/haproxy$
```

Vamos a juntar esta configuración con el comando `cat`, que nos garantiza
el orden alfabético de los ficheros en su concatenación. En principio, el
orden no es muy importante si declaramos uno o más bloques principales en
un solo fichero; sin embargo voy a preceder cada fichero con un número para
ordenar un poco los bloques (primero la sección global, luego los *stats*,
los *frontends* y finalmente los *backends*).

La configuración básica ya incluye las secciones *global* y *defaults*.
Para no perderlas, vamos a mover este fichero para ser un *snippet* más:

```bash
gerard@loadbalancer:/etc/haproxy$ sudo mv haproxy.cfg conf.d/00-global.cfg
gerard@loadbalancer:/etc/haproxy$
```

Digamos que ponemos los siguientes ficheros extra: `01-stats.cfg`,
`02-frontend.cfg`, `03-backend_web.cfg`, `03-backend_api.cfg`:

```bash
gerard@loadbalancer:/etc/haproxy$ tree -I errors
.
└── conf.d
    ├── 00-global.cfg
    ├── 01-stats.cfg
    ├── 02-frontend.cfg
    ├── 03-backend_api.cfg
    └── 03-backend_web.cfg

1 directory, 5 files
gerard@loadbalancer:/etc/haproxy$
```

**NOTA**: Vemos que no existe el fichero `haproxy.cfg`. Este se va a crear
*a posteriori*, antes de levantar el servicio, y se irá modificando en cada
ejecución de `systemctl start haproxy` (o restart).

Ahora toca la parte de **systemd**; para ello queremos añadir una directiva
`ExecStartPre` adicional que junte los ficheros. Para ello vamos a crear
un *override* de **systemd**, que no es demasiado complejo:

```bash
gerard@loadbalancer:~$ sudo systemctl edit haproxy
gerard@loadbalancer:~$
```

El comando anterior ha creado un fichero nuevo, en el que hemos puesto el
siguiente contenido:

```bash
gerard@loadbalancer:~$ cat /etc/systemd/system/haproxy.service.d/override.conf
[Service]
ExecStartPre=bash -c "cat /etc/haproxy/conf.d/*.cfg > /etc/haproxy/haproxy.cfg"
gerard@loadbalancer:~$
```

**TRUCO**: Concatenamos los ficheros `*.cfg` para poder desactivarlos si
fuera necesario; solo habría que cambiarles la extensión o añadirles un sufijo.

Hacemos el `systemctl daemon-reload` para que lea la nueva configuración
de nuestra *unit*, y volvemos a levantar el servicio:

```bash
gerard@loadbalancer:~$ sudo systemctl daemon-reload
gerard@loadbalancer:~$
```

```bash
gerard@loadbalancer:~$ sudo systemctl restart haproxy
Job for haproxy.service failed because the control process exited with error code.
See "systemctl status haproxy.service" and "journalctl -xe" for details.
gerard@loadbalancer:~$
```

Ha fallado, y eso es porque ya había un comando ejecutándose **antes** del
nuestro: una verificación de la configuración que falla por estar la
configuración ausente (o si tuviera errores previos).

```bash
gerard@loadbalancer:~$ systemctl status haproxy
● haproxy.service - HAProxy Load Balancer
   Loaded: loaded (/lib/systemd/system/haproxy.service; enabled; vendor preset: enabled)
  Drop-In: /etc/systemd/system/haproxy.service.d
           └─override.conf
   Active: failed (Result: exit-code) since Thu 2021-06-03 03:34:53 CEST; 1min 43s ago
     Docs: man:haproxy(1)
           file:/usr/share/doc/haproxy/configuration.txt.gz
  Process: 987 ExecStartPre=/usr/sbin/haproxy -f $CONFIG -c -q $EXTRAOPTS (code=exited, status=1/FAILURE)
gerard@loadbalancer:~$
```

```bash
gerard@loadbalancer:~$ systemctl show haproxy | grep ^ExecStartPre
ExecStartPre={ path=/usr/sbin/haproxy ; argv[]=/usr/sbin/haproxy -f $CONFIG -c -q $EXTRAOPTS ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }
ExecStartPre={ path=/usr/bin/bash ; argv[]=/usr/bin/bash -c cat /etc/haproxy/conf.d/*.cfg > /etc/haproxy/haproxy.cfg ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }
gerard@loadbalancer:~$
```

No nos queda otra que eliminar las opciones existentes (con un `ExecStartPre`
vacío), y añadir la nuestra, seguida de la que ya había, que sacamos de su
*unit* original:

```bash
gerard@loadbalancer:~$ cat /lib/systemd/system/haproxy.service | grep ^ExecStartPre
ExecStartPre=/usr/sbin/haproxy -f $CONFIG -c -q $EXTRAOPTS
gerard@loadbalancer:~$
```

```bash
gerard@loadbalancer:~$ sudo systemctl edit haproxy
gerard@loadbalancer:~$ cat /etc/systemd/system/haproxy.service.d/override.conf
[Service]
ExecStartPre=
ExecStartPre=bash -c "cat /etc/haproxy/conf.d/*.cfg > /etc/haproxy/haproxy.cfg"
ExecStartPre=/usr/sbin/haproxy -f $CONFIG -c -q $EXTRAOPTS
gerard@loadbalancer:~$
```

Y ahora no deberíamos tener más problemas:

```bash
gerard@loadbalancer:~$ sudo systemctl daemon-reload
gerard@loadbalancer:~$
```

```bash
gerard@loadbalancer:~$ systemctl show haproxy | grep ^ExecStartPre
ExecStartPre={ path=/usr/bin/bash ; argv[]=/usr/bin/bash -c cat /etc/haproxy/conf.d/*.cfg > /etc/haproxy/haproxy.cfg ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }
ExecStartPre={ path=/usr/sbin/haproxy ; argv[]=/usr/sbin/haproxy -f $CONFIG -c -q $EXTRAOPTS ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }
gerard@loadbalancer:~$
```

```bash
gerard@loadbalancer:~$ sudo systemctl restart haproxy
gerard@loadbalancer:~$
```

**NOTA**: Podemos observar como ha aparecido o se ha modificado el fichero `haproxy.cfg`.

```bash
gerard@loadbalancer:~$ ls /etc/haproxy/
conf.d  errors  haproxy.cfg
gerard@loadbalancer:~$
```

## Haciendo uso de SNI de la forma fácil

Cuando hemos tenido que poner varios dominios SSL en una misma IP, se hace
necesario [utilizar SNI][1]. Basta con indicar los certificados uno por uno
en la directiva `bind ssl`.

Cuando repites algo tan mecánico, es posible cometer errores de sintaxis
(por ejemplo, olvidarse del `crt` o escribir mal la ruta al certificado);
en caso de tener muchos dominios, la lista se hace inmanejable por su longitud.
Por ejemplo:

```bash
gerard@loadbalancer:/etc/haproxy/certs$ sudo openssl req -x509 -nodes -newkey rsa:4096 -keyout web.local.pem -out web.local.pem -days 365 -subj "/CN=web.local"
...
gerard@loadbalancer:/etc/haproxy/certs$
```

```bash
gerard@loadbalancer:/etc/haproxy/certs$ sudo openssl req -x509 -nodes -newkey rsa:4096 -keyout api.local.pem -out api.local.pem -days 365 -subj "/CN=api.local"
...
gerard@loadbalancer:/etc/haproxy/certs$
```

```bash
gerard@loadbalancer:/etc/haproxy$ tree certs/
certs/
├── api.local.pem
└── web.local.pem

0 directories, 2 files
gerard@loadbalancer:/etc/haproxy$
```

```bash
gerard@loadbalancer:/etc/haproxy$ cat haproxy.cfg
...
frontend www
    bind *:80
    bind *:443 ssl crt /etc/haproxy/certs/web.local.pem crt /etc/haproxy/certs/api.local.pem
    http-request redirect scheme https unless { ssl_fc }
    use_backend web if { hdr(host) -i web.local }
    use_backend api if { hdr(host) -i api.local }
...
gerard@loadbalancer:/etc/haproxy$
```

Lo que no se conoce demasiado, es que se puede indicar solamente la carpeta
de los certificados y **haproxy** leerá todos sus ficheros en tiempo de
*start*, para luego servirlos basándose en su campo `CN`. El nombre del
fichero **no importa**, pero hay que hacer un restart para que los vuelva a
leer desde el disco.

```bash
gerard@loadbalancer:/etc/haproxy$ cat haproxy.cfg
...
frontend www
    bind *:80
    bind *:443 ssl crt /etc/haproxy/certs/
    http-request redirect scheme https unless { ssl_fc }
    use_backend web if { hdr(host) -i web.local }
    use_backend api if { hdr(host) -i api.local }
...
gerard@loadbalancer:/etc/haproxy$
```

Esto resume los cambios solamente a renovar los certificados y a añadir
los nuevos *backends* una sola vez...

```bash
gerard@loadbalancer:/etc/haproxy$ sudo systemctl restart haproxy
gerard@loadbalancer:/etc/haproxy$
```

```bash
gerard@loadbalancer:/etc/haproxy$ curl -svk --resolve web.local:443:127.0.0.1 https://web.local/ 2>&1 | egrep "CN|Host:"
*  subject: CN=web.local
*  issuer: CN=web.local
> Host: web.local
gerard@loadbalancer:/etc/haproxy$
```

```bash
gerard@loadbalancer:/etc/haproxy$ curl -svk --resolve api.local:443:127.0.0.1 https://api.local/ 2>&1 | egrep "CN|Host:"
*  subject: CN=api.local
*  issuer: CN=api.local
> Host: api.local
gerard@loadbalancer:/etc/haproxy$
```

## Sirviendo una fichero estático

Llega el momento de pasar a producción y aparecen algunos detalles con los
que no contábamos. Puede ser el código de verificación de **Google**, un
fichero de **Let’s Encrypt** o una página de mantenimiento.

No queremos modificar nuestro *backend* para servir estos ficheros, y no
nos parece bonito montar un servidor web para ello. Podemos jugar con los
*frontends* de **hapropxy** para separar la petición de este fichero concreto.

Sabemos que el *backend* va a dar un error 503 si no hay *backends*
disponibles, y podemos cambiar el fichero de error en caso de un error,
así que solo tenemos que forzar que no hayan *backends* y listo. Una
solución muy ingeniosa!

```bash
gerard@loadbalancer:/etc/haproxy$ cat /etc/haproxy/haproxy.cfg
...
frontend www
    bind *:80
    bind *:443 ssl crt /etc/haproxy/certs/
    http-request redirect scheme https unless { ssl_fc }
    acl is_google path /google85de17e42482bf61.html
    use_backend google if is_google
    use_backend web if { hdr(host) -i web.local }
    use_backend api if { hdr(host) -i api.local }
...
backend google
    errorfile 503 /etc/haproxy/errors/google.http
...
gerard@loadbalancer:/etc/haproxy$
```

Vemos que el primer paso es identificar las peticiones a este fichero
concreto, que hacemos en el *frontend* con su respectiva ACLs.
Mandamos la petición a un *backend* propio, diferente de nuestros
preciados *backends*.

La segunda parte es declarar el *backend* propio **sin servidores**.
Esto va a causar un error 503. Solo tenemos que indicar el fichero
para este error concreto:

```bash
gerard@loadbalancer:/etc/haproxy/errors$ cat google.http ; echo ''
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 53

google-site-verification: google85de17e42482bf61.html
gerard@loadbalancer:/etc/haproxy/errors$
```

Y tras recargar el servicio **haproxy**, ya lo tendríamos:

```bash
google-site-verification: google85de17e42482bf61.htmlgerard@loadbalancer:/etc/haproxy/errors$ curl -ski https://localhost/google85de17e42482bf61.html; echo ''
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Length: 53

google-site-verification: google85de17e42482bf61.html
gerard@loadbalancer:/etc/haproxy/errors$
```

[1]: {{< relref "/articles/2019/11/sirviendo-diferentes-certificados-por-virtualhost-mediante-sni.md" >}}
