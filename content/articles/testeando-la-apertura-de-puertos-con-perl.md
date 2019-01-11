Title: Testeando la apertura de puertos con Perl
Slug: testeando-la-apertura-de-puertos-con-perl
Date: 2019-01-14 10:00
Category: Operaciones
Tags: perl, script, tcp



Muchas veces me toca solicitar la apertura de puertos en un *firewall* que no administro. Muchas veces estos administradores se olvidan de ejecutar pasos que resultan en una ausencia total de conectividad, lo que me obliga a revisar su trabajo antes de poner alguna aplicación dando servicio en ese puerto.

La política de muchas redes es que el *firewall* responda un *connection refused* cuando bloquea las peticiones internas, con lo que no se puede ver si es que no hay aplicación, o es que el *firewall* la ha bloqueado. Normalmente levantaría un servicio de "usar y tirar" para comprobar que se llega a ese puerto y que se obtiene una respuesta adecuada:

```bash
gerard@shangrila:~/workspace$ python3 -m http.server 8080
Serving HTTP on 0.0.0.0 port 8080 ...
10.0.2.2 - - [09/Jan/2019 12:33:26] "GET / HTTP/1.1" 200 -
10.0.2.2 - - [09/Jan/2019 12:33:26] code 404, message File not found
10.0.2.2 - - [09/Jan/2019 12:33:26] "GET /favicon.ico HTTP/1.1" 404 -
^C
Keyboard interrupt received, exiting.
gerard@shangrila:~/workspace$
```

Sin embargo esta vez había algo diferente; se trataba de una máquina **AIX** sin **python** y gestionada por terceros, que no me iban a instalar **python**, y mucho menos para esa tontería... 

Así que fuí mirando las herramientas de las que disponía: no había **netstat**, ningún compilador de **C**, nada de nada... excepto **perl**. No soy nada fan de **perl**, pero fue mi salvación. Por supuesto, no conozco casi nada el lenguaje, así que tuve que tirar de internet. Tras simplificar ejemplos de cientos de líneas llegué a un servidor mínimo capaz de aceptar peticiones TCP y loguear la IP origen, como concepto de que se llega. Me limito a dejarlo por aquí, para futuras referencias:

```perl
#!/usr/bin/perl

use IO::Socket;

$port = $ARGV[0];
$socket = new IO::Socket::INET (
    LocalHost => '0.0.0.0',
    LocalPort => $port,
    Proto => 'tcp',
    Listen => 5,
    Reuse => 1
);
die "Coudn't open socket" unless $socket;
print "TCP Server listening on port $port\n";

while(1) {
        $client_socket = $socket->accept();
        $peer_address = $client_socket->peerhost();
        print "I got a connection from $peer_address\n";
}
```

En cuanto a la ejecución, nada del otro mundo: basta con invocar el *script* con el puerto a abrir por parámetro. El ejemplo asume que el *script* tiene permisos de ejecución; sino, os va tocar poner el intérprete delante.

```bash
gerard@shangrila:~/workspace$ ./tcpserver.pl 8080
TCP Server listening on port 8080
```


Si llega alguna petición al "servidor" que tenemos montado, veremos que queda registrada su IP origen:

```bash
gerard@shangrila:~/workspace$ ./tcpserver.pl 8080
TCP Server listening on port 8080
I got a connection from 10.0.2.2
```

Y con esto podemos asegurar que nos llegan los paquetes de red. En este caso concreto, las peticiones se han hecho con un navegador normal, y como no devolvemos respuesta, nos da un mensaje del tipo `ERR_EMPTY_RESPONSE`; esto es completamente normal.
