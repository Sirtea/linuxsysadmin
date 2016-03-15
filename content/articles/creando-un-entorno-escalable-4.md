Title: Creando un entorno escalable (IV)
Slug: creando-un-entorno-escalable-4
Date: 2016-03-21 08:00
Category: Sistemas
Tags: linux, debian, jessie, proxy http, balanceador, ssl, nginx, virtual hosts, port forwarding
Series: Creando un entorno escalable



Acabamos el artículo anterior de esta serie con las aplicaciones corriendo en sus respectivas máquinas. En este artículo vamos a poner una fachada a todo el sistema, mediante un *proxy HTTP* que haga las funciones de terminación *SSL* y de *balanceador*, exponiendo todo el sistema en una sola dirección IP.

Como *proxy HTTP* tenemos varias opciones; solo se necesita un servidor web que soporte *virtual hosts*, protocolo HTTP sobre SSL, capacidad de hacer de *proxy* y capacidad para balancear las peticiones entre varias opciones.

Si analizamos estos requisitos, podemos comprobar que las opciones son muchas; desde el todopoderoso **apache** al **nginx**, pasando por soluciones de balanceador puro como **haproxy**, u opciones mas esotéricas como **squid**. En este caso, se utiliza **nginx** por su facilidad de uso y su bajo consumo de recursos. Cumple con el subconjunto básico de funcionalidades necesario, pero no dispone de tantos algoritmos de balanceo como otras opciones.

## Instalación de paquetes

Empezamos instalando los requisitos para nuestra fachada; en principio solo se necesitaría el servidor web **nginx** (en la versión mínima) y **openssl** para generar los certificados. Adicionalmente instalaremos **curl** para comprobar que el resultado es correcto.

```bash
root@frontend:~# apt-get install nginx-light curl
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes extras:
  ca-certificates libcurl3 libffi6 libgmp10 libgnutls-deb0-28 libhogweed2 libidn11 libldap-2.4-2 libnettle4 libp11-kit0 librtmp1
  libsasl2-2 libsasl2-modules libsasl2-modules-db libssh2-1 libtasn1-6 nginx-common openssl
Paquetes sugeridos:
  gnutls-bin libsasl2-modules-otp libsasl2-modules-ldap libsasl2-modules-sql libsasl2-modules-gssapi-mit
  libsasl2-modules-gssapi-heimdal fcgiwrap nginx-doc ssl-cert
Se instalarán los siguientes paquetes NUEVOS:
  ca-certificates curl libcurl3 libffi6 libgmp10 libgnutls-deb0-28 libhogweed2 libidn11 libldap-2.4-2 libnettle4 libp11-kit0
  librtmp1 libsasl2-2 libsasl2-modules libsasl2-modules-db libssh2-1 libtasn1-6 nginx-common nginx-light openssl
0 actualizados, 20 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 4.077 kB de archivos.
Se utilizarán 8.832 kB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
root@frontend:~#
```

El paquete **nginx** de la distribución *Debian* viene con una configuración por defecto en */etc/nginx/sites-enabled/*, que vamos a eliminar para evitar que se pise con nuestras configuraciones.

```bash
root@frontend:~# ls -lh /etc/nginx/sites-enabled/
total 0
lrwxrwxrwx 1 root root 34 feb 26 11:28 default -> /etc/nginx/sites-available/default
root@frontend:~# unlink /etc/nginx/sites-enabled/default
root@frontend:~#
```


## Consideraciones de seguridad

Cuando nuestro servidor web recibe una petición, va a iniciar una nueva conexión contra el servidor de *backend* que toque o el de *backoffice*. Para habilitar esto, se necesitan nuevas reglas en el *firewall*, que en este caso es **firehol**, instalado en la máquina anfitriona.

```bash
root@lxc:~# cat /etc/firehol/firehol.conf
...  
app_servers="10.0.0.3 10.0.0.4 10.0.0.5"
frontend_server="10.0.0.2"
...
router internal inface lxc0 outface lxc0
...  
    route webcache accept src "$frontend_server" dst "$app_servers"
root@lxc:~#
```

No os olvidéis de reiniciar **firehol**, para que se apliquen las nuevas reglas.

```bash
root@lxc:~# service firehol restart
...  
root@lxc:~#
```

## Montando los virtualhosts de ambas aplicaciones

La parte privada va a estar escondida tras una terminación **HTTPS**. Esa aplicación se podría esconder tras una [autenticación de certificados cliente]({filename}/articles/restringiendo-accesos-mediante-certificados-de-cliente.md) o mediante [autenticación básica]({filename}/articles/restringiendo-accesos-web-mediante-autenticacion-basica.md). Por simplicidad vamos a usar esta última.

Empezamos generando un certificado autofirmado para el servidor web, directamente firmado, y su clave. Fijaos que no generamos ningún certificado de CA, ya que no tenemos ninguna intención de generar autenticación cliente en el futuro.

```bash
root@frontend:~# openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout server.key -out server.crt -subj "/C=ES/ST=Spain/L=Barcelona/O=LinuxSysadmin/CN=shop.linuxsysadmin.tk"
Generating a 2048 bit RSA private key
.......................................+++
.................................................................................................................................................................+++
writing new private key to 'server.key'
-----
root@frontend:~#
```
Ponemos la clave y el certificado generado en sus respectivas localizaciones, de acuerdo a los estándares.

```bash
root@frontend:~# cp server.key /etc/ssl/private/
root@frontend:~# cp server.crt /etc/ssl/certs/
root@frontend:~#
```

Como verificación, así quedaría la carpeta */etc/ssl/*:

```bash
root@frontend:~# tree /etc/ssl/
/etc/ssl/
├── certs
│   └── server.crt
├── openssl.cnf
└── private
    └── server.key

2 directories, 3 files
root@frontend:~#
```

Para poder autenticar mediante autenticación básica, generamos un usuario en un fichero tipo **htpasswd**.

```bash
root@frontend:~# echo "admin:$(openssl passwd -crypt s3cr3t)" > /etc/nginx/shop.basic_auth
root@frontend:~# cat /etc/nginx/shop.basic_auth
admin:rOU9H0ABEB2H6
root@frontend:~#
```

Y con todas las piezas listas, montamos los virtualhosts, en un fichero de configuración o en varios, según nos apetezca.

```bash
root@frontend:~# cat /etc/nginx/sites-enabled/shop
upstream backends {
        server backend1:8080;
        server backend2:8080;
}

server {
        listen 80 default_server;
        server_name _;

        location / {
                proxy_pass http://backends;
        }
}

server {
        listen 443 ssl;
        server_name _;

        ssl_certificate /etc/ssl/certs/server.crt;
        ssl_certificate_key /etc/ssl/private/server.key;

        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/shop.basic_auth;

        location / {
                proxy_pass http://backoffice:8080;
        }
}
root@frontend:~#
```

La configuración es bastante estándar; se trata de un *server* (equivalente en **nginx** a un *virtualhost* de **apache**) para cada protocolo. La parte de administración es solamente la mediación **SSL** y un *proxy_pass* hacia el *backoffice*. La parte de la API pública también se limita a hacer un *proxy_pass*, solo que se hace contra *backends* que es un objeto **upstream**, que es el que define el balanceador.

Ahora solo queda reiniciar el servidor web para aplicar los cambios. De acuerdo a la documentación, habría bastado un *reload*.

```bash
root@frontend:~# service nginx restart
root@frontend:~#
```

## Comprobando que las aplicaciones funcionan

Para comprobar que la parte de la API funciona y balancea adecuadamente, basta con hacer peticiones. Podemos comprobar el *backend* que la ha servido porque la aplicación pone una cabecera que especifica el nombre del *host* que la resolvió. Con dos peticiones veremos que va alternativamente a cada *backend*.

```bash
root@frontend:~# curl -i http://localhost/products/
HTTP/1.1 200 OK
Server: nginx/1.6.2
Date: Fri, 26 Feb 2016 11:04:38 GMT
Content-Type: application/json
Content-Length: 3
Connection: keep-alive
Backend: backend1

[]
root@frontend:~# curl -i http://localhost/products/
HTTP/1.1 200 OK
Server: nginx/1.6.2
Date: Fri, 26 Feb 2016 11:04:40 GMT
Content-Type: application/json
Content-Length: 3
Connection: keep-alive
Backend: backend2

[]
root@frontend:~#
```

Para la parte privada, haremos la petición, de la misma manera; vamos a añadir el flag *-k* para sobrepasar el certificado autofirmado. Como no hemos indicado el usuario y la contraseña, nos devuelve un error 401, que indica que no estamos autorizados a pasar mas allá.

```bash
root@frontend:~# curl -i -k https://localhost/products
HTTP/1.1 401 Unauthorized
Server: nginx/1.6.2
Date: Fri, 26 Feb 2016 11:05:35 GMT
Content-Type: text/html
Content-Length: 194
Connection: keep-alive
WWW-Authenticate: Basic realm="Admin Area"

<html>
<head><title>401 Authorization Required</title></head>
<body bgcolor="white">
<center><h1>401 Authorization Required</h1></center>
<hr><center>nginx/1.6.2</center>
</body>
</html>
root@frontend:~#
```

Y con esto parece que funciona, a falta de probar con un navegador adecuado.

## Un pequeño detalle: abrimos los puertos

Puesto que este entorno está montado sobre virtualización **LXC**, necesitamos que la dirección IP de la maquina anfitriona exponga los puertos de la máquina *frontend*. Para ello hay que habilitar un mecanismo que se llama *port forwarding*, coloquialmente conocido como "abrir el puerto".

Mediante una directiva de **firehol** indicamos que pasaremos todas las peticiones recibidas a los puertos 80 y 443 directamente a la máquina de *frontend*. Hay que habilitar ese tráfico de **FORWARD**, mediante otras reglas.

```bash
root@lxc:~# cat /etc/firehol/firehol.conf
...
frontend_server="10.0.0.2"
...
dnat to "$frontend_server" proto tcp dport 80
dnat to "$frontend_server" proto tcp dport 443
...
router world2lan inface eth0 outface lxc0
    route http accept dst "$frontend_server"
    route https accept dst "$frontend_server"
...
root@lxc:~#
```

Y nuevamente reiniciamos el servicio para aplicar las nuevas reglas.

```bash
root@lxc:~# service firehol restart
...
root@lxc:~#
```

## Accediendo a las aplicaciones en la IP pública

Vamos a acceder con un navegador a la parte de administración, para ver que funciona y para rellenar algunos datos, para que se vea una respuesta de la API con fundamento.

El primer paso consiste en abrir el navegador con la URL adecuada, y nos tropezamos con la autenticación.

![Auth basic]({filename}/images/entorno-escalable-auth-basic.jpg)

Tras pasar la autenticación podemos acceder a los formularios para añadir productos.

![Admin form]({filename}/images/entorno-escalable-admin-form.jpg)

Tras añadir tres productos, vemos que ya se genera la lista, en formato web.

![Admin list]({filename}/images/entorno-escalable-admin-list.jpg)

Con los datos introducidos podemos consumir la API, para comprobar que los datos que hemos introducido en la base de datos (mediante la aplicación de administración) están disponibles.

```bash
gerard@desktop:~$ wget -qO- http://192.168.1.232/products/
[
    {
        "price": 1.5, 
        "_id": "123", 
        "description": "Apples"
    }, 
    {
        "price": 1.0, 
        "_id": "456", 
        "description": "Oranges"
    }, 
    {
        "price": 2.0, 
        "_id": "789", 
        "description": "Pears"
    }
]
gerard@desktop:~$ 
```

Y consultando un producto concreto, también funciona como debe.

```bash
gerard@desktop:~$ wget -qO- http://192.168.1.232/products/456
{
    "price": 1.0, 
    "_id": "456", 
    "description": "Oranges"
}
gerard@desktop:~$ 
```

Y con esto comprobamos que todo queda en su sitio. Solo hará falta limpiar cualquier desecho que hayamos dejado en */root/*.

***Y con este artículo cerramos la serie.***
