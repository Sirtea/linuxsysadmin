Title: Un proxy DNS con dnsmasq
Slug: un-proxy-dns-con-dnsmasq
Date: 2016-02-01 08:30
Category: Sistemas
Tags: linux, debian, jessie, dnsmasq, cache, dns, dhcp



A veces nos puede interesar disponer de una servidor **DNS** para nombrar las máquinas de nuestra red privada, sin la complejidad de **BIND**. Otras, queremos acelerar el acceso a internet desde nuestra red; es interesante ver el tiempo que se pierde en la resolución **DNS**. Para eso disponemos de **dnsmasq**.

El servicio **dnsmasq** proporciona servicios como caché **DNS** y como servidor **DHCP**. Se trata de un *proxy* **DNS** que va a dirigir las consultas **DNS** contra el servidor configurado en el *proxy*, guardando una copia en *caché* para agilizar futuras consultas.

Es muy fácil de configurar y es bastante ligero. Se considera ideal para redes pequeñas con menos de 50 ordenadores.

En mi caso, resultó muy útil para solucionar el problema de **DNS** que me planteaba una red **Virtualbox** *solo anfitrión*, en donde se escondían mis máquinas virtuales con dirección IP estática. Resulta que me muevo entre varias zonas de trabajo, y que no hay ningún servidor **DNS** accesible desde todas; ir cambiando los **DNS** de todas las máquinas era trabajoso.

Con este problema, puse **dnsmasq** en mi anfitrión (que usaba **DHCP** y recibía el **DNS** automáticamente), y configuré todas las máquinas para que usaran el anfitrión como servidor **DNS**; nunca mas tuve que configurarlos.

## Instalación

La instalación en una máquina derivada de *Debian* es muy simple; está en los repositorios oficiales.

```bash
root@proxy:~# apt-get install dnsmasq
Leyendo lista de paquetes... Hecho
Creando árbol de dependencias       
Leyendo la información de estado... Hecho
Se instalarán los siguientes paquetes extras:
  dns-root-data dnsmasq-base libnetfilter-conntrack3
Paquetes sugeridos:
  resolvconf
Se instalarán los siguientes paquetes NUEVOS:
  dns-root-data dnsmasq dnsmasq-base libnetfilter-conntrack3
0 actualizados, 4 nuevos se instalarán, 0 para eliminar y 0 no actualizados.
Se necesita descargar 488 kB de archivos.
Se utilizarán 1.170 kB de espacio de disco adicional después de esta operación.
¿Desea continuar? [S/n] s
...
root@proxy:~# 
```

En caso de querer modificar la configuración, se debe editar el fichero */etc/dnsmasq.conf*, y luego reiniciar el servicio *dnsmasq*. En este mismo fichero se puede configurar el servicio **DHCP** (directiva *dhcp-range*), el servidor de nombres a dar al resto (la misma máquina de *dnsmasq*, por defecto), el servidor **NTP** o el *gateway*.

En mi caso, no vi necesario activar estos servicios, así que el fichero de configuración no se vio modificada. Así pues, con esto basta.

**TRUCO**: En caso de querer resolver localmente, *dnsmasq* sirve los nombres alojados en */etc/hosts*, a menos que se indique lo contrario en la configuración. Basta con modificar ese fichero.

## Comprobación y uso

Para comprobar que funciona, vamos a poner otra máquina, configurada para usar el nuevo servidor **DNS**:

```bash
root@client:~# cat /etc/resolv.conf 
nameserver 192.168.56.1
root@client:~# 
```

En principio basta con comprobar que resuelve el nombre de una petición cualquiera, por ejemplo, con un **ping**.

Sin embargo, podemos apreciar la mejora de la *caché* mediante una herramienta mas avanzada de resolución **DNS**, por ejemplo, con **dig**

```bash
root@client:~# dig www.linuxsysadmin.tk | grep "Query time"
;; Query time: 118 msec
root@client:~# dig www.linuxsysadmin.tk | grep "Query time"
;; Query time: 5 msec
root@client:~# dig www.linuxsysadmin.tk | grep "Query time"
;; Query time: 4 msec
root@client:~# 
```

Y con esto hemos cumplido; tenemos un *proxy caché* **DNS**, que nos agiliza las peticiones, nos resuelve localmente y nos evita ir cambiando el **DNS** cada vez que nos movemos de zona de trabajo.
