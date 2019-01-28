Title: Restringiendo accesos web mediante autenticación básica
Slug: restringiendo-accesos-web-mediante-autenticacion-basica
Date: 2016-02-08 08:30
Category: Sistemas
Tags: linux, debian, jessie, nginx, autenticacion basica, htpasswd, ssl, https, certificado



Algunas veces nos encontramos con la necesidad de restringir el acceso a algunos recursos web. Normalmente se suele implementar algún sistema de *login*, *cookies* o *sesiones*; no obstante, esta opción no siempre nos es posible, y tenemos que proteger esos recursos usando los mecanismos que nos ofrezca el servidor web.

**ATENCIÓN**: Este método es bastante simple, y se puede descodificar lo que manda el cliente; por eso se recomienda encarecidamente usar **SSL**, mediante el uso de **HTTPS**.

Empezaremos instalando el servidor web y la herramienta de generación de certificados para usar con **SSL**.

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
..................................++
.....................................................................++
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
.....................................................................++
......................................................................................................................................................................++
e is 65537 (0x10001)
Enter pass phrase for server.key:
Verifying - Enter pass phrase for server.key:
root@server:~#
```

Ahora creamos un certificado para el servidor web.

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

**TRUCO**: Si la clave está protegida por una *passphrase*, se va a necesitar introducirla cada vez que se quiera levantar el servidor web. Nos lo podemos ahorrar con unos simples comandos, que dejará la clave como insegura.

```bash
root@server:~# mv server.key server.key.secure
root@server:~# openssl rsa -in server.key.secure -out server.key
Enter pass phrase for server.key.secure:
writing RSA key
root@server:~#
```

## Montando el dominio web

Para habilitar **SSL** en un dominio, necesitamos la clave y el certificado del servidor, así que vamos a ponerlos en una carpeta pensado para tal efecto.

```bash
root@server:~# cp server.key /etc/ssl/private/
root@server:~# cp server.crt /etc/ssl/certs/
root@server:~#
```

Así quedarían los certificados una vez en su sitio.

```bash
root@server:~# tree /etc/ssl/
/etc/ssl/
├── certs
│   └── server.crt
├── openssl.cnf
└── private
    └── server.key

2 directories, 3 files
root@server:~#
```

Vamos a poner un fichero de configuración en **nginx**, que va a escuchar por el puerto 443 y con **SSL** habilitado. Indicamos también donde están los ficheros que servirá el **nginx**, la localización de los certificados y activamos la autenticación básica.

```bash
root@server:~# cat /etc/nginx/sites-enabled/private.linuxsysadmin.tk
server {
        listen 443 ssl;
        server_name private.linuxsysadmin.tk;
        root /www;

        ssl_certificate /etc/ssl/certs/server.crt;
        ssl_certificate_key /etc/ssl/private/server.key;

        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/auth/private;
}
root@server:~#
```

Ahora tenemos que crear un fichero tipo *.htpasswd* como los de **apache**. Crearemos primero la carpeta en donde lo vamos a dejar.

```bash
root@server:~# mkdir /etc/nginx/auth
root@server:~#
```

En la carpeta creada pondremos un fichero llamado *private* con un formato idéntico a los *.htpasswd* de **apache**. Aquí podríamos usar las herramientas de **apache-utils**, pero de momento nos conformaremos con crearlo con **openssl**.

```bash
root@server:~# echo "admin:$(openssl passwd -crypt s3cr3t)" >> /etc/nginx/auth/private
root@server:~# cat /etc/nginx/auth/private
admin:y6xasR0LI8mbg
root@server:~#
```

Finalmente reiniciamos el servidor web para que aplique los cambios en la configuración.

```bash
root@server:~# service nginx restart
root@server:~#
```

## Comprobación de funcionamiento

Es importante que nos acordemos de crear nuestro *document root* con algún contenido.

```bash
root@server:~# mkdir /www
root@server:~# echo "Private area" > /www/index.html
root@server:~#
```

Si apuntamos un navegador al dominio configurado, y tras aceptar nuestro certificado autofirmado como excepción, deberíamos ver que se nos piden las credenciales en una ventana emergente.

![Autenticación básica: credenciales]({static}/images/autenticacion-basica-credenciales.png)

Y con eso tenemos nuestro contenido protegido de los curiosos.
