Title: Exponiendo puertos TCP a través de un firewall con ngrok
Slug: exponiendo-puertos-tcp-a-traves-de-un-firewall-con-ngrok
Date: 2017-06-12 10:00
Category: Operaciones
Tags: ngrok, túnel, ssh



A veces tenemos la necesidad de exponer en internet algún puerto TCP de forma temporal, para hacer *testing* o alguna *demo*. Ya vimos como podemos hacer esto mediante [túneles SSH reversos]({filename}/articles/creando-tuneles-con-ssh.md), aunque no siempre disponemos de un dominio público. En estos casos podemos usar un sistema de túneles llamado **ngrok**.

El concepto es muy simple, tal como nos indican en su [página web](https://ngrok.com/):

> **Secure tunnels to localhost**  
> I want to expose a local server behind a NAT or firewall to the internet.

Se trata de un binario que abre un túnel reverso SSH contra una de sus servidores, exponiendo dicho puerto mediante un dominio de la forma `<dominio.ngrok.io>`. Algunas de las funcionalidades requieren una versión de pago, pero la versión gratuita nos puede sacar de algún apuro.

## El escenario de partida

Vamos a suponer que estamos desarrollando una página web y nos interesa que un cliente nos valide que es lo que quiere, o puede ser que pidamos opiniones de terceros.

Vamos a suponer que es una página HTML simple, aunque podría ser un puerto levantado por nuestro *framework* favorito. Para servirlo vamos a utilizar un servidor web simple, por ejemplo, el *SimpleHTTPServer* de **python**.

No vamos a desarrollar una página muy completa, solo lo justo para que se vea el ejemplo. Este es nuestro código HTML:

```bash
gerard@sodium:~/web$ cat index.html 
<!doctype html>

<html lang="es">

<head>
  <meta charset="utf-8">
  <title>Lorem ipsum</title>
  <link rel="stylesheet" href="style.css">
</head>

<body>
  <h1>Lorem ipsum</h1>
  <p>Lorem ipsum dolor sit amet</p>
  <p>Lorem ipsum dolor sit amet</p>
  <p>Lorem ipsum dolor sit amet</p>
</body>

</html>
gerard@sodium:~/web$ 
```

Por poner algo con un poco de color, utilizaremos una hoja de estilo CSS:

```bash
gerard@sodium:~/web$ cat style.css 
body {
  width: 800px;
  margin: auto;
  background-color: cyan;
}

h1 { text-align: center; }
p { text-align: justify; }
gerard@sodium:~/web$ 
```

Y como necesitamos servirla, ponemos un servidor cualquiera para servirlo, por ejemplo, el de **python**.

```bash
gerard@sodium:~/web$ python -m SimpleHTTPServer
Serving HTTP on 0.0.0.0 port 8000 ...
```

En este punto podemos ver la página web localmente en <http://localhost:8000/>, aunque por estar detrás de un *firewall*, nadie más allá del *firewall* puede verlo.

## Instalando ngrok

En este caso, el título no es muy acertado, ya que **no se instala**. Se trata de un solo binario compilado estáticamente, que solo tiene que ser descargado y descomprimido.

Siguiendo la página de descarga, he elegido el binario que funciona para mi sistema operativo y arquitectura, que para variar es un sistema *Linux* de 64 bits. Podemos descargar el enlace directamente en el navegador o con una comando adecuado.

```bash
gerard@sodium:~$ wget https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
converted 'https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip' (ANSI_X3.4-1968) -> 'https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip' (UTF-8)
--2016-12-27 17:18:09--  https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
Resolving bin.equinox.io (bin.equinox.io)... 107.20.195.3, 23.21.165.77, 107.20.164.208
Connecting to bin.equinox.io (bin.equinox.io)|107.20.195.3|:443... connected.
HTTP request sent, awaiting response... 200 OK
Length: 5142256 (4.9M) [application/octet-stream]
Saving to: 'ngrok-stable-linux-amd64.zip'

ngrok-stable-linux-amd64 100%[====================================>]   4.90M  2.39MB/s   in 2.0s   

2016-12-27 17:18:12 (2.39 MB/s) - 'ngrok-stable-linux-amd64.zip' saved [5142256/5142256]

gerard@sodium:~$ 
```

Se trata de un fichero *.zip* que tenemos que descomprimir para obtener el binario.

```bash
gerard@sodium:~$ unzip ngrok-stable-linux-amd64.zip 
Archive:  ngrok-stable-linux-amd64.zip
  inflating: ngrok                   
gerard@sodium:~$ 
```

En este punto podemos dejar el nuevo binario en alguna carpeta que esté en el *PATH* del sistema, aunque no es necesario. En este caso no voy a hacerlo por brevedad.

## Levantando el túnel

El binario tiene muchas opciones, algunas funcionan en la versión gratuita, pero otras no. Podemos ver lo que tenemos disponible invocando el binario sin más parámetros.

```bash
gerard@sodium:~$ ./ngrok 
NAME:
   ngrok - tunnel local ports to public URLs and inspect traffic

DESCRIPTION:
    ngrok exposes local networked services behinds NATs and firewalls to the
    public internet over a secure tunnel. Share local websites, build/test
    webhook consumers and self-host personal services.
    Detailed help for each command is available with 'ngrok help <command>'.
    Open http://localhost:4040 for ngrok's web interface to inspect traffic.

EXAMPLES:
    ngrok http 80                    # secure public URL for port 80 web server
    ngrok http -subdomain=baz 8080   # port 8080 available at baz.ngrok.io
    ngrok http foo.dev:80            # tunnel to host:port instead of localhost
    ngrok tcp 22                     # tunnel arbitrary TCP traffic to port 22
    ngrok tls -hostname=foo.com 443  # TLS traffic for foo.com to port 443
    ngrok start foo bar baz          # start tunnels from the configuration file

VERSION:
   2.1.18

AUTHOR:
  inconshreveable - <alan@ngrok.com>

COMMANDS:
   authtoken	save authtoken to configuration file
   credits	prints author and licensing information
   http		start an HTTP tunnel
   start	start tunnels by name from the configuration file
   tcp		start a TCP tunnel
   tls		start a TLS tunnel
   update	update ngrok to the latest version
   version	print the version string
   help		Shows a list of commands or help for one command
gerard@sodium:~$ 
```

Es muy interesante la opción del puerto TCP, pero esta es de pago. Sin embargo, la opción de un túnel HTTP es gratuita. Es la que vamos a usar.

```bash
gerard@sodium:~$ ./ngrok http 8000
```

El comando nos va a pintar una página de estado, con alguna información útil para saber a donde tenemos que apuntar el navegador remoto.

```bash
ngrok by @inconshreveable                                                           (Ctrl+C to quit)
                                                                                                    
Session Status                online                                                                
Version                       2.1.18                                                                
Region                        United States (us)                                                    
Web Interface                 http://127.0.0.1:4040                                                 
Forwarding                    http://54b3ca80.ngrok.io -> localhost:8000                            
Forwarding                    https://54b3ca80.ngrok.io -> localhost:8000                           
                                                                                                    
Connections                   ttl     opn     rt1     rt5     p50     p90                           
                              0       0       0.00    0.00    0.00    0.00                          
```

De esta salida podemos sacar dos datos importantes:

* La página pública referente a nuestro túnel, <http://54b3ca80.ngrok.io/>
* Una página local de estadísticas local en <http://localhost:4040/>

La página de estado es una gran utilidad; es en donde podemos ver información de estado y un análisis exhaustivo de las peticiones recibidas. Vale la pena darle un vistazo.
