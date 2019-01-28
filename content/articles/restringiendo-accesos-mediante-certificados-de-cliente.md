Title: Restringiendo accesos mediante certificados de cliente
Slug: restringiendo-accesos-mediante-certificados-de-cliente
Date: 2016-02-22 08:00
Category: Sistemas
Tags: linux, debian, jessie, nginx, 2 way ssl, ssl, https, certificado



De vez en cuando, tenemos algún contenido web o una API que necesita un control de acceso superior. El método mas eficaz del que disponemos hoy en día es la autenticación con certificados SSL cliente, en donde es el cliente el que debe ofrecer un certificado que el servidor validará.

Como se trata de proteger contenido web, vamos a necesitar un servidor web, por ejemplo, **nginx**. De paso, vamos a instalar el paquete **openssl**, que nos permitirá generar los certificados usados.

```bash
root@server:~# apt-get install nginx-light openssl
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes extras:
  nginx-common
Paquetes sugeridos:
  fcgiwrap nginx-doc ssl-cert ca-certificates
Se instalarán los siguientes paquetes NUEVOS:
  nginx-common nginx-light openssl
0 actualizados, 3 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 1.126 kB de archivos.
Se utilizarán 2.148 kB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
root@server:~#
```

## Generar el certificado y la clave de la CA

Empezaremos por generar la clave de la CA, que va a servir para firmar el certificado que pondremos en el servidor.

```bash
root@server:~# openssl genrsa -des3 -out ca.key 4096
Generating RSA private key, 4096 bit long modulus
...................................................................++
.++
e is 65537 (0x10001)
Enter pass phrase for ca.key:
Verifying - Enter pass phrase for ca.key:
root@server:~#
```

Ahora generamos el certificado de la CA. Lo generamos directamente firmado en un solo paso.

```bash
root@server:~# openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/C=ES/ST=Spain/L=Barcelona/O=LinuxSysadmin"
Enter pass phrase for ca.key:
root@server:~#
```

## Generar el certificado para el servidor web

Generamos la clave para el certificado del servidor web.

```bash
root@server:~# openssl genrsa -des3 -out server.key 4096
Generating RSA private key, 4096 bit long modulus
.............................................++
.....................................++
e is 65537 (0x10001)
Enter pass phrase for server.key:
Verifying - Enter pass phrase for server.key:
root@server:~#
```

Ahora creamos un certificado para el servidor web. Es importante que el campo **CN** sea el mismo que el nombre del *virtualhost*.

```bash
root@server:~# openssl req -new -key server.key -out server.csr -subj "/C=ES/ST=Spain/L=Barcelona/O=LinuxSysadmin/CN=private.linuxsysadmin.tk"
Enter pass phrase for server.key:
root@server:~#
```

Y lo firmamos con la clave y el certificado de la CA.

```bash
root@server:~# openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out server.crt
Signature ok
subject=/C=ES/ST=Spain/L=Barcelona/O=LinuxSysadmin/CN=private.linuxsysadmin.tk
Getting CA Private Key
Enter pass phrase for ca.key:
root@server:~#
```

**TRUCO**: Si la clave está protegida por una passphrase, se va a necesitar introducirla cada vez que se quiera levantar el servidor web. Nos lo podemos ahorrar con unos simples comandos, que dejará la clave como insegura.

```bash
root@server:~# mv server.key server.key.secure
root@server:~# openssl rsa -in server.key.secure -out server.key
Enter pass phrase for server.key.secure:
writing RSA key
root@server:~#
```

## Generar el certificado cliente

Generamos la clave para el certificado del cliente.

```bash
root@server:~# openssl genrsa -des3 -out client.key 1024
Generating RSA private key, 1024 bit long modulus
...............................++++++
.....................++++++
e is 65537 (0x10001)
Enter pass phrase for client.key:
Verifying - Enter pass phrase for client.key:
root@server:~#
```

El siguiente paso consiste en generar una petición de certificado, que posteriormente haremos firmar. El campo **CN** puede ser recogido por el servidor web y trasladado mediante cabeceras a un hipotético *backend*, en caso de hacer un *proxy_pass*.

```bash
root@server:~# openssl req -new -key client.key -out client.csr -subj "/C=ES/ST=Spain/L=Barcelona/O=LinuxSysadmin/CN=Gerard Monells"
Enter pass phrase for client.key:
root@server:~#
```

Firmamos nuestra petición de certificado con la clave de la CA, obteniendo el certificado final.

```bash
root@server:~# openssl x509 -req -days 365 -in client.csr -CA ca.crt -CAkey ca.key -set_serial 91 -out client.crt
Signature ok
subject=/C=ES/ST=Spain/L=Barcelona/O=LinuxSysadmin/CN=Gerard Monells
Getting CA Private Key
Enter pass phrase for ca.key:
root@server:~#
```

Ahora queda empaquetar la clave y el certificado en un fichero *client.p12* que pueda ser importado en un navegador web.

```bash
root@server:~# openssl pkcs12 -export -in client.crt -inkey client.key -out client.p12 -name "LinuxSysadmin"
Enter pass phrase for client.key:
Enter Export Password:
Verifying - Enter Export Password:
root@server:~#
```

## Montando el dominio web

Además de necesitar el certificado y la clave servidor, es necesario que el servidor web conozca el certificado de la CA para que pueda verificar el servidor cliente que nos ofrezca el navegador.

```bash
root@server:~# cp server.key /etc/ssl/private/
root@server:~# cp server.crt /etc/ssl/certs/
root@server:~# cp ca.crt /etc/ssl/certs/
root@server:~#
```

Así quedarían los certificados una vez en su sitio.

```bash
root@server:~# tree /etc/ssl/
/etc/ssl/
├── certs
│   ├── ca.crt
│   └── server.crt
├── openssl.cnf
└── private
    └── server.key

2 directories, 4 files
root@server:~#
```

Vamos a poner un fichero de configuración en **nginx**, que va a escuchar por el puerto 443 y con **SSL** habilitado. Indicamos también donde están los ficheros que servirá el **nginx**, la localización de los certificados y la necesidad de verificar al cliente mediante certificado contra el certificado de la CA.

```bash
root@server:~# cat /etc/nginx/sites-enabled/private.linuxsysadmin.tk
server {
    listen                      443 ssl;
    server_name                 private.linuxsysadmin.tk;
    root                        /www;

    ssl_certificate             /etc/ssl/certs/server.crt;
    ssl_certificate_key         /etc/ssl/private/server.key;
    ssl_client_certificate      /etc/ssl/certs/ca.crt;
    ssl_verify_client           on;
}
root@server:~#
```

Podemos verificar que la sintaxis de la configuración es correcta usando el binario de **nginx** con el parámetro adecuado.

```bash
root@server:~# nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
root@server:~#
```

Y sabiendo que es correcto, reiniciamos el servidor web.

```bash
root@server:~# service nginx restart
root@server:~#
```

## Comprobación de funcionamiento

Como hemos indicado en la configuración en el *document root*, vamos a servir el contenido que se encuentra en */www*. Empezaremos poniendo algún contenido en él.

```bash
root@server:~# mkdir /www
root@server:~# echo "Private area" > /www/index.html
root@server:~#
```

Ahora apuntemos el navegador a la **URL** del servidor web. Debemos aceptar el certificado autofirmado, puesto que no viene firmado por ninguna autoridad certificadora conocida, por ejemplo, **VeriSign**.

Aún así, como no hemos presentado el certificado cliente, el servidor web nos impide el acceso, con una respuesta **HTTP 400**.

![2 way SSL access denied]({static}/images/2-way-ssl-access-denied.png)

Ahora debemos importar el certificado *client.p12* en el navegador web. En el caso concreto de **Google Chrome**, se hace desde el siguiente menú:

> Menu &rarr; Settings &rarr; Show advanced settings &rarr; HTTPS/SSL &rarr; Manage certificates &rarr; Your certificates &rarr; Import &rarr; client.p12

Y ya podemos acceder a nuestro contenido protegido, previa selección del certificado a usar.

![2 way SSL certificate]({static}/images/2-way-ssl-certificate.png)

Y con esto ya tenemos montada la autenticación cliente mediante certificados.
