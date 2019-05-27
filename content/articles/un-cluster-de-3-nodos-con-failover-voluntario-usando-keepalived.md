Title: Un clúster de 3 nodos con failover voluntario usando Keepalived
Slug: un-cluster-de-3-nodos-con-failover-voluntario-usando-keepalived
Date: 2019-05-27 10:00
Category: Sistemas
Tags: cluster, keepalived



Trabajando con **Docker Swarm** me doy cuenta de que hay muchos servicios tipo "ventanilla única" que suelo poner en los mismos *managers*. El asunto es que un despliegue con **Docker Swarm** funciona mejor con un número impar de *managers*, siendo 3 o 5 lo recomendable para un entorno de producción.

Además, me he dado cuenta de que el orquestador es capaz de manejar el funcionamiento del servicio mejor que el resto de herramientas; lo que no se lleva tan bien es el cambio de IP compartida en caso de un reinicio voluntario y controlado del servidor.

Esto me llevó a pensar en un método para indicar a **keepalived** que un nodo no era un buen candidato para mantener la IP flotante, cosa que solo pude conseguir jugando con las prioridades. Lo malo es que en el peor caso, nuestro nodo puede no librarse de dicha IP, aunque nos ayuda en la mayoría de casos.

El truco es simple: se trata de declarar un *check* que aporte mucha prioridad habitualmente, pero que se permita fallar ante una acción concreta del operador, como por ejemplo, **la presencia de un fichero concreto** (que es la aproximación que voy a usar). Así el resto de servidores se vuelven mejores candidatos para obtener la dirección IP flotante y se la llevarían.

## Entorno

Tenemos 3 servidores, todos ellos con **Debian Stretch** y 256mb de memoria; para el ejemplo basta, pero habrá que darles más si el servidor va a servir para algo en el futuro. Solo tienen un servidor de SSH instalado.

* **Server01** &rarr; IP 10.10.0.3
* **Server02** &rarr; IP 10.10.0.4
* **Server03** &rarr; IP 10.10.0.5

La idea es que la dirección IP compartida es la 10.10.0.2, que es la que se administrará **keepalived**. Instalamos **keepalived** en todos los servidores:

```bash
gerard@server01:~$ sudo apt install keepalived
...
gerard@server01:~$ 
```

```bash
gerard@server02:~$ sudo apt install keepalived
...
gerard@server02:~$ 
```

```bash
gerard@server03:~$ sudo apt install keepalived
...
gerard@server03:~$ 
```

## Implementación

Para que un fichero pueda ser la diferencia entre tener la IP compartida o no, necesitamos un *check*, que reduzca la prioridad por debajo del resto de servidores en caso de tener dicho fichero presente.

Le vamos a dar a cada servidor 100 puntos como "premio" por no tener el fichero, más de 1 a 3 puntos por servidor que nos van a servir para desempatar entre ellos y asegurar el servidor que recoge el testigo.

De esta forma, las configuraciones nos quedarían de esta forma:

```bash
gerard@server01:~$ cat /etc/keepalived/keepalived.conf 
vrrp_script chk_releasevip {
    script "/usr/bin/test ! -e /tmp/releasevip"
    interval 5
    weight 100
}

vrrp_instance VI_1 {
    interface enp0s3
    priority 3
    virtual_router_id 51
    virtual_ipaddress {
        10.10.0.2
    }
    track_script {
        chk_releasevip
    }
}
gerard@server01:~$ 
```

```bash
gerard@server02:~$ cat /etc/keepalived/keepalived.conf 
vrrp_script chk_releasevip {
    script "/usr/bin/test ! -e /tmp/releasevip"
    interval 5
    weight 100
}

vrrp_instance VI_1 {
    interface enp0s3
    priority 2
    virtual_router_id 51
    virtual_ipaddress {
        10.10.0.2
    }
    track_script {
        chk_releasevip
    }
}
gerard@server02:~$ 
```

```bash
gerard@server03:~$ cat /etc/keepalived/keepalived.conf
vrrp_script chk_releasevip {
    script "/usr/bin/test ! -e /tmp/releasevip"
    interval 5
    weight 100
}

vrrp_instance VI_1 {
    interface enp0s3
    priority 1
    virtual_router_id 51
    virtual_ipaddress {
        10.10.0.2
    }
    track_script {
        chk_releasevip
    }
}
gerard@server03:~$ 
```

Solo nos quedaría reiniciar el demonio de **keepalived** para que apliquen los cambios.

```bash
gerard@server01:~$ sudo systemctl restart keepalived
gerard@server01:~$ 
```

```bash
gerard@server02:~$ sudo systemctl restart keepalived
gerard@server02:~$ 
```

```bash
gerard@server03:~$ sudo systemctl restart keepalived
gerard@server03:~$ 
```

## Pruebas

En estado habitual, con todos los servidores levantados y sin el fichero de control, la IP flotante debería estar en **server01**, ya que tiene prioridad 103 (3+100) contra las prioridades 102 y 101 de sus vecinos (**server02** y **server03** respectivamente).

```bash
gerard@server01:~$ ip a | grep 10.10
    inet 10.10.0.3/24 brd 10.10.0.255 scope global enp0s3
    inet 10.10.0.2/32 scope global enp0s3
gerard@server01:~$ 
```

```bash
gerard@server02:~$ ip a | grep 10.10
    inet 10.10.0.4/24 brd 10.10.0.255 scope global enp0s3
gerard@server02:~$ 
```

```bash
gerard@server03:~$ ip a | grep 10.10
    inet 10.10.0.5/24 brd 10.10.0.255 scope global enp0s3
gerard@server03:~$ 
```

Supongamos que queremos liberar la IP flotante de **server01**; esto se hace haciendo fallar el *check*, que mira que no exista el fichero `/tmp/releasevip`. Esto lo podemos hacer creando el fichero.

```bash
gerard@server01:~$ touch /tmp/releasevip
gerard@server01:~$ 
```

Solo hay que esperar un máximo de 5 segundos a que se ejecute el *check*, que es lo que declaramos en el *interval* del mismo. Sin sorpresas, **server01** pierde la IP compartida y **server02** la asume (prioridad 3 contra 102 y 101).

```bash
gerard@server01:~$ ip a | grep 10.10
    inet 10.10.0.3/24 brd 10.10.0.255 scope global enp0s3
gerard@server01:~$ 
```

```bash
gerard@server02:~$ ip a | grep 10.10
    inet 10.10.0.4/24 brd 10.10.0.255 scope global enp0s3
    inet 10.10.0.2/32 scope global enp0s3
gerard@server02:~$ 
```

Ahora vamos a quitar la IP de **server02** también, de la misma manera:

```bash
gerard@server02:~$ touch /tmp/releasevip
gerard@server02:~$ 
```

La IP compartida cae en **server03**, ya que tiene prioridad 101 contra las prioridades 3 y 2 del resto de servidores.

```bash
gerard@server01:~$ ip a | grep 10.10
    inet 10.10.0.3/24 brd 10.10.0.255 scope global enp0s3
gerard@server01:~$ 
```

```bash
gerard@server02:~$ ip a | grep 10.10
    inet 10.10.0.4/24 brd 10.10.0.255 scope global enp0s3
gerard@server02:~$ 
```

```bash
gerard@server03:~$ ip a | grep 10.10
    inet 10.10.0.5/24 brd 10.10.0.255 scope global enp0s3
    inet 10.10.0.2/32 scope global enp0s3
gerard@server03:~$ 
```

**AVISO**: Si el servidor **server03** fallara o le pusiéramos el fichero de control, **server01** asumiría la IP flotante **a pesar de tener el fichero de control** (prioridad 3 contra 2 y 1).

Si quitamos el fichero de control del servidor **server02**, este pasaría a tener prioridad (102 contra 3 y 101) y robaría la IP flotante:

```bash
gerard@server02:~$ rm /tmp/releasevip 
gerard@server02:~$ 
```

```bash
gerard@server02:~$ ip a | grep 10.10
    inet 10.10.0.4/24 brd 10.10.0.255 scope global enp0s3
    inet 10.10.0.2/32 scope global enp0s3
gerard@server02:~$ 
```

En el caso de quitar el fichero de **server01**, este pasaría a tener más prioridad, y por lo tanto se asigna la IP compartida.

```bash
gerard@server01:~$ rm /tmp/releasevip 
gerard@server01:~$ 
```

```bash
gerard@server01:~$ ip a | grep 10.10
    inet 10.10.0.3/24 brd 10.10.0.255 scope global enp0s3
    inet 10.10.0.2/32 scope global enp0s3
gerard@server01:~$ 
```

Y con esto hemos conseguido nuestro objetivo.
