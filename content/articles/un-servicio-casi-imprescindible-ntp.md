Title: Un servicio casi imprescindible: NTP
Slug: un-servicio-casi-imprescindible-ntp
Date: 2017-10-02 10:00
Category: Sistemas
Tags: ntp, servidor, hora



Normalmente, me gustan los servidores con un número de servicios tirando a mezquino; menos servicios significan menos actualizaciones, menos superficie de ataque y menos recursos ocupados. Sin embargo, hay algunos que son imprescindibles, mientras que otros son altamente recomendables. Este es el caso del **NTP**, que mantiene la hora actualizada.

Esto es crucial para muchos servicios de *cluster*, que necesitan una sincronización temporal estricta. Otros usos son para aplicaciones y sus *logs*, en donde el momento exacto en el que pasan las cosas es crucial, y puede ser consultado en *logs* de varias máquinas, que idealmente deberían coincidir. Finalmente, el otro uso que considero indispensable es para aquellas máquinas que se dedican a virtualizar contenedores u otras máquinas virtuales, ya que pagando el precio del proceso una única vez, permite a sus descendientes (por ejemplo, contenedores **docker**) seguir actualizadas.

## Instalación de NTP

El servicio **NTP** se instala en un solo paquete, que tanto en la famíla *RedHat* con en la família *Debian*, se llama **ntp**. Usad las herramientas que tengáis a mano en vuestra distribución.

```bash
root@server:~# apt-get install ntp
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes adicionales:
  libopts25 libperl5.24 perl perl-modules-5.24 rename
Paquetes sugeridos:
  ntp-doc perl-doc libterm-readline-gnu-perl | libterm-readline-perl-perl make
Se instalarán los siguientes paquetes NUEVOS:
  libopts25 libperl5.24 ntp perl perl-modules-5.24 rename
0 actualizados, 6 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 7.103 kB de archivos.
Se utilizarán 42,1 MB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
root@server:~#
```

La configuración por defecto ya viene preconfigurada con algunos servidores base contra los que sincronizar. Podemos ver que estamos sincronizando y contra qué, con el comando **ntpq**:

```bash
root@server:~# ntpq -p
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
 0.debian.pool.n .POOL.          16 p    -   64    0    0.000    0.000   0.000
 1.debian.pool.n .POOL.          16 p    -   64    0    0.000    0.000   0.000
 2.debian.pool.n .POOL.          16 p    -   64    0    0.000    0.000   0.000
 3.debian.pool.n .POOL.          16 p    -   64    0    0.000    0.000   0.000
root@server:~#
```

En este caso, podemos ver que, debido a la configuración de red, no llegamos a los servidores:

* El tiempo desde la última sincronización no existe (*when* vacío)
* El *stratum* de los servidores es infinito, con lo que son inaccesibles (*st* vale 16 para marcar esta inaccesibilidad)

Así pues, vamos a cambiar la configuración del **NTP** para acceder a un servidor **NTP** en nuestra propia red local, y quitando los que habían.

```bash
root@server:~# cat /etc/ntp.conf | egrep "pool.*debian|server 10"
server 10.0.0.1
# pool 0.debian.pool.ntp.org iburst
# pool 1.debian.pool.ntp.org iburst
# pool 2.debian.pool.ntp.org iburst
# pool 3.debian.pool.ntp.org iburst
root@server:~#
```

Como no, reiniciamos el servicio para que use la nueva configuración:

```bash
root@server:~# systemctl restart ntp
root@server:~#
```

Solo queda observar que estamos sincronizando contra el servidor solicitado.

```bash
root@server:~# ntpq -p
     remote           refid      st t when poll reach   delay   offset  jitter
==============================================================================
 10.0.0.1            10.0.0.1    4 u   28   64    7    0.277  -12.387   9.552
root@server:~#
```

## Servidor NTP

Para configurar un servidor **NTP** no se necesita nada adicional. El paquete que acabamos de instalar ya ha levantado un servidor **NTP** preparado para que lo usen otros servidores que lleguen a él vía red. De hecho, en el ejemplo estamos sincronizando contra otro servidor (10.0.0.1) que es idéntico al del ejemplo, solo que está sincronizando de otro servidor. A nivel de seguridad, hay que tener en cuenta que el protocolo **NTP** utiliza los puertos 123 TCP y UDP y solo se necesita permitir uno de estos dos a nivel de *firewall*.

El estrato 4 (en el ejemplo) significa que estamos sincronizando contra un servidor de estrato 4, que es uno que sincroniza de uno de estrato 3. Al final de la cadena, encontraremos un reloj GPS o atómico, que es un servidor de estrato 1. El protocolo **NTP** permite tener estratos hasta 15, significando el número 16 que no habría ninguna conectividad con el servidor especificado.
