Title: Forzar rangos de IPs prohibidas para Docker
Slug: forzar-rangos-de-ips-prohibidas-para-docker
Date: 2019-02-19 19:00
Category: Operaciones
Tags: docker, proxy



Tras cambiar de oficina en mi trabajo, vuelvo a tener el dudoso honor de trabajar tras un *proxy*. Como viene siendo habitual, me puse un servidor **Virtualbox** con **Debian** para disponer de las opciones que una máquina auxiliar me ofrece, pero no fue hasta instalar **Docker** que estalló el desastre.

Y el caso es que tenía el servidor básico funcionando, bien configurado, con acceso a internet y sin problemas. Fuí a instalar **Docker** y todo parecía correcto, con las configuraciones de *proxy* adecuadas. De repente intento comprobar la red solicitando una página web cualquiera, y... ¡sorpresa!

```bash
gerard@shangrila:~$ curl http://www.google.es/
curl: (7) Failed to connect to proxy.acme.biz port 3128: No existe ninguna ruta hasta el `host'
gerard@shangrila:~$
```

Por supuesto, lo primero tras un error de este estilo es mirar la tabla de rutas, a ver que es lo que aplica para resolver esta ruta:

```bash
gerard@shangrila:~$ ip route
default via 10.0.2.2 dev enp0s3
10.0.2.0/24 dev enp0s3 proto kernel scope link src 10.0.2.15
169.254.0.0/16 dev enp0s3 scope link metric 1000
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown
gerard@shangrila:~$
```

Y es que la IP del *proxy* es privada, estando en el rango 172.17.x.x; concretamente estaba en la 172.17.10.20. De esta forma, todas las peticiones al *proxy* caen en la última ruta, y entran en el dominio de **Docker**, que por supuesto, no tiene ningún contenedor con esa dirección IP.

Visto esto solo queda instruir a **Docker** para que no haga uso de ese rango. Parece difícil, pero no lo es; **Docker** decide que el rango está ocupado o no mirando la tabla de rutas, con mejor o menor acierto.

El truco es simple: consiste en hacer creer a **Docker** que ese bloque está ocupado, añadiendo algo a la tabla de rutas. En principio, la regla caería en la zona **default**, saldría por el dispositivo **enp0s3** y utilizaría el *gateway* **10.0.2.2**. Hagamos un bloque con el rango 172.17.0.0/16 que haga exactamente eso.

Lo primero es parar el servicio de **Docker**, y eliminar su carpeta de datos en `/var/lib/docker`. Esto nos permitirá trabajar sin **Docker** recuerde nada en el inicio y que olvide cualquier red que ya haya podido crear.

**AVISO**: Esto va a eliminar configuraciones, imágenes, redes, volúmenes y contenedores; yo partía de un servidor vacío.

```bash
gerard@shangrila:~$ sudo service docker stop
[sudo] password for gerard:
gerard@shangrila:~$ sudo rm -R /var/lib/docker/
gerard@shangrila:~$
```

Tenemos que conseguir preconfigurar una ruta, que es relativamente simple y bien documentado; en mi caso concreto se trata de un servidor **Debian** y la documentación me hizo añadir la ruta en `/etc/network/interfaces`:

```bash
gerard@shangrila:~$ cat /etc/network/interfaces
...
allow-hotplug enp0s3
iface enp0s3 inet dhcp
        post-up ip route add 172.17.0.0/16 dev enp0s3 via 10.0.2.2
...
gerard@shangrila:~$
```

Para descartar los cambios residuales y aplicar los nuevos, me limité a reiniciar el servidor.

```bash
gerard@shangrila:~$ sudo reboot
```

Tras el reinicio, se puede ver que la ruta ha aplicado, y que **Docker** ha tenido que configurarse en otro rango libre:

```bash
gerard@shangrila:~$ ip route
default via 10.0.2.2 dev enp0s3
10.0.2.0/24 dev enp0s3 proto kernel scope link src 10.0.2.15
169.254.0.0/16 dev enp0s3 scope link metric 1000
172.17.0.0/16 via 10.0.2.2 dev enp0s3
172.18.0.0/16 dev docker0 proto kernel scope link src 172.18.0.1 linkdown
gerard@shangrila:~$
```

```bash
gerard@shangrila:~$ docker inspect bridge
[
    {
        "Name": "bridge",
...
        "IPAM": {
            "Driver": "default",
            "Options": null,
            "Config": [
                {
                    "Subnet": "172.18.0.0/16"
                }
            ]
        },
...
    }
]
gerard@shangrila:~$
```

Solo nos queda comprobar que el problema inicial, que era la falta de acceso a internet, se ha solucionado.

```bash
gerard@shangrila:~$ curl -I http://www.google.es/
HTTP/1.1 200 OK
...
X-Cache: MISS from proxy.acme.biz
X-Cache-Lookup: MISS from proxy.acme.biz:3128
Via: 1.1 proxy.acme.biz (squid)
Connection: keep-alive

gerard@shangrila:~$
```

Y con esto hemos acabado.
