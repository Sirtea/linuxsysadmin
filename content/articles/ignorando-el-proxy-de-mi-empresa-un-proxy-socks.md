Title: Ignorando el proxy de mi empresa: un proxy SOCKS
Slug: ignorando-el-proxy-de-mi-empresa-un-proxy-socks
Date: 2017-07-31 10:00
Category: Operaciones
Tags: ssh, proxy, socks



Tenemos en el trabajo uno de esos *enginjerks* que lanzan acciones *random* para justificar su trabajo. Cortó el acceso a *Dropbox*, en donde tengo cosas útiles para mi trabajo. Harto de encender los datos móviles de mi móvil para ir sincronizando ficheros, me he montado un proxy **SOCKS** para mí.

Se trata de una tocada de narices tener que encender los datos móviles de mi *smartphone* para sincronizar la carpeta de *Dropbox* periódicamente. También es completamente inútil como medida de seguridad, puesto que muevo con frecuencia mi ordenador portátil por obligaciones profesionales.

Sin embargo, hay un acceso más allá de los puertos 80 y 443; se trata del puerto 22, específicamente hacia un servidor bastión que nos sirve para acceder a los entornos en donde corren nuestras aplicaciones. Por supuesto están fuera de nuestra infraestructura.

La idea es muy simple: levantamos un *proxy SOCKS* en la máquina remota (con pleno acceso a internet), en un puerto al que podamos llegar con nuestro ordenador; configuramos nuestro ordenador para usar ese *proxy* remoto. Alternativamente, como no tengo más puertos por los que pasar, puedo levantar el puerto del *proxy* en mi mismo ordenador, de la misma forma que los túneles SSH.

## Un ejemplo práctico

Vamos a suponer que tenemos dos máquinas; también vamos a suponer que levantamos el *proxy SOCKS* en nuestro escritorio:

* **alphacentauri**: Es nuestra máquina remota, tiene instalado **SSH** y tiene acceso libre a internet.
* **capella**: es nuestro escritorio, en donde desarrollamos nuestro trabajo.

El responsable de levantar el *proxy SOCKS* es el mismo SSH. Para ello basta el *flag -D*.

```bash
gerard@capella:~$ ssh -N -D 9999 proxy@alphacentauri -p 2222 -f
Warning: Permanently added 'alphacentauri:2222' (ECDSA) to the list of known hosts.
gerard@capella:~$ 
```

Hay una serie de consideraciones en este comando:

* Existe un usuario *proxy* en *alphacentauri*. Es un usuario normal y tenemos autenticación por par de claves (opcional, pero muy cómodo).
* Por cortesía del *flag -N* no vamos a abrir un terminal.
* El *flag -f* nos levanta el *proxy* en *background*, que nos evita bloquear el terminal pero exige el par de claves.
* El servidor SSH en *alphacentauri* escucha en el puerto 2222, y por eso usamos el *flag -p*.
* Gracias al *flag -D*, el *proxy* se levanta en el puerto 9999, escuchando en *localhost* (por defecto).

A partir de este momento, todas las conexiones que usen *localhost:9999* como *proxy SOCKS*, van a acceder a internet como lo hace la máquina *alphacentauri*.

Sin más esperas, vamos al cliente de *dropbox*; podemos configurar el *proxy* en "Preferencias > Proxies". Basta con indicar la opción "Tipo de proxy" como "SOCKS5" y el servidor como "127.0.0.1:9999".

Como ya sabemos que los túneles SSH se caen, os recomiendo altamente usar un mecanismo de levantamiento automático, como *autossh* o directamente [usando SystemD]({filename}/articles/levantando-tuneles-ssh-con-systemd.md).
