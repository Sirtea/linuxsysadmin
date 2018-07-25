Title: Una oda a Alpine Linux
Slug: una-oda-a-alpine-linux
Date: 2018-07-30 09:00
Category: Miscelánea
Tags: alpine, linux



Hace unos días salió la *release* 3.8 de **Alpine Linux**. Por problemas varios en el *build*, la imagen de **docker** se hizo esperar bastante, y como la paciencia no es una de mis virtudes, decidí darle un intento en una máquina virtual **Virtualbox**, quedando gratamente complacido con el resultado obtenido.

El primer paso es descargar la imagen de [la pagina de descargas](https://alpinelinux.org/downloads/). En esta página hay que elegir la variante de la imagen y la variante del procesador; aplicando a mi máquina y sabiendo que voy a ejecutarlo como máquina virtual, he elegido [esta](http://dl-cdn.alpinelinux.org/alpine/v3.8/releases/x86_64/alpine-virt-3.8.0-x86_64.iso).

Se trata de un fichero `.iso` de 32mb que, a su vez, es un *livecd* con el instalador incorporado. Es una distribución muy ligera, así que con una máquina virtual de 256mb de memoria funciona de sobras para la instalación base con SSH y nada más; modificaremos este valor cuando necesitemos más memoria para otro tipo de carga de trabajo.

Iniciamos la máquina virtual con el CD montado, y obtenemos un *shell*, previo *login* con el usuario **root** y sin contraseña. En este momento, estamos consumiendo 33mb de memoria (sin *buffers*), lo que nos deja con más de 200mb disponibles para nuestro uso.

Como *livecd* es muy bonito, pero lo que queremos es **instalar**. Esto se consigue con el *script* `setup-alpine`. Sin embargo, si nos leemos [la documentación](https://wiki.alpinelinux.org/wiki/Alpine_setup_scripts#setup-disk) de los *scripts* de la instalación veremos varias cosas:

* Por defecto, se crean 3 particiones:
    * La partición raíz, montada en `/`
    * Una partición para los ficheros de *boot*, montados en `/boot`
    * Una partición de *swap*
* El instalador se puede parametrizar con variables de entorno
    * Podemos modificar el tamaño de la particion `/boot`, pero no eliminarla con `BOOT_SIZE`
    * Podemos modificar el tamaño de la partición *swap* con `SWAP_SIZE`, incluso eliminándola con tamaño 0

**NOTA**: Como pretendo modificar la *swap* a posteriori, prefiero [crear un *swapfile*]({filename}/articles/ampliando-la-memoria-swap-mediante-swapfiles.md), y por lo tanto voy a anular la partición *swap* indicando tamaño 0.

Lanzamos el comando `SWAP_SIZE=0 setup-alpine` para realizar la instalación. El proceso en sí mismo no tiene ninguna complicación y está listo en menos de 5 minutos; solo voy a detallar las opciones que he ido usando:

1. **Teclado**: El que tengáis; pongo "es"
2. **Hostname**: De momento "alpine"; cuando clone la máquina ya lo cambiaré
3. **Red**: Lo que os haga falta; yo he usado *eth0* en modo *dhcp*
4. **Zona horaria**: Algo como "Europe" y luego "Madrid"
5. **Mirrors de _apk_**: Pongo "f"; es un proceso lento, pero a la larga vale la pena
6. **Servidor de SSH**: Voy a lo seguro, "openssh"
7. **Clente de NTP**: Dejo el que viene por defecto "chrony"
8. **Disco a usar**: El que tengáis, yo pongo "sda", usado como "sys", que es instalación tradicional

Y con esto estamos. Reiniciamos sin el *live cd* y ya estamos en nuestro nuevo y flamante servidor **Alpine Linux**, que nos ocupa 26mb de memoria solamente.

## Siguientes pasos

La instalación base está realmente bien, aunque algunas modificaciones nos van a venir muy bien; algunas son muy evidentes y otras son para nota.

### Usuario nominal y sudo

Por defecto, **Alpine Linux** solo crea el usuario **root**, que encima, no puede entrar por SSH usando contraseña. Esto nos deja sin acceso al servidor.

Siguiendo el estilo **Ubuntu**, vamos a crear un usuario nominal con permisos de **sudo**, y vamos a bloquear al usuario **root**.

```bash
alpine:~# apk add sudo
...
alpine:~# adduser gerard
...
alpine:~#
```

**Alpine Linux** viene por defecto con el grupo **wheel**, pero no con el grupo **sudo**. Así pues, vamos a habilitar **sudo** para todos los usuarios del grupo **wheel**, al que añadiremos a nuestro usuario.

```bash
alpine:~# cat /etc/sudoers | grep ^%wheel
%wheel ALL=(ALL) ALL
alpine:~# adduser gerard wheel
alpine:~#
```

Y nos logamos al servidor con el usuario nominal. Probamos que podemos hacer **sudo** y si es así, bloqueamos el usuario **root**.

```bash
alpine:~$ id
uid=1000(gerard) gid=1000(gerard) groups=10(wheel),1000(gerard)
alpine:~$ sudo id
[sudo] password for gerard:
uid=0(root) gid=0(root) groups=0(root),1(bin),2(daemon),3(sys),4(adm),6(disk),10(wheel),11(floppy),20(dialout),26(tape),27(video)
alpine:~$
```

```bash
alpine:~$ sudo passwd -l root
passwd: password for root changed by root
alpine:~$
```

### Creación de un swapfile

Como pretendíamos clonar esta imagen base, se decidió deshabilitar la partición *swap* con `SWAP_SIZE=0`. Esto nos deja si memoria *swap*, y no es recomendable. Para poder redimensionar la memoria *swap* en cada clon, lo fácil es [crear la *swap* en un fichero]({filename}/articles/ampliando-la-memoria-swap-mediante-swapfiles.md).

Para ello solo hay que crear un fichero para tal uso, con el tamaño deseado y perteciendo a **root**, con permisos 600. Lo formateamos como *swap* y ya lo tenemos preparado.

```bash
alpine:~$ sudo dd if=/dev/zero of=/swapfile bs=1M count=512
...
alpine:~$ sudo chown 600 /swapfile
alpine:~$ sudo mkswap /swapfile
...
alpine:~$
```

Para que se monte automáticamente en cada *boot*, se necesitan dos cosas: ponerlo en `/etc/fstab` y tener el servicio **swap** activado en **boot time**.

```bash
alpine:~$ grep swap /etc/fstab
/swapfile none swap sw 0 0
alpine:~$ sudo rc-update add swap
 * service swap added to runlevel default
alpine:~$
```

En el siguiente reinicio, la memoria *swap* se activará sola. Para los que no tengáis paciencia para reiniciar, podéis levantar el servicio directamente.

```bash
alpine:~$ sudo rc-service swap start
 * Activating swap devices ...                                                                                           [ ok ]
alpine:~$ free -m
             total       used       free     shared    buffers     cached
Mem:           238        231          6          0          5        196
-/+ buffers/cache:         29        208
Swap:          511          0        511
alpine:~$
```

Los clones pueden limitarse a desactivar la *swap* con `swapoff`, recrear `/swapfile` con el tamaño y los permisos adecuados, lanzar el `mkswap` y volver a activarla con `swapon`.

### Limpiar configuraciones

Los ficheros de configuración son bastante correctos, pero no está de más revisar algunos de ellos, especialmente si clonamos esta máquina hay que cambiarlos en el clon:

* `/etc/hostname`
* `/etc/hosts`
* `/etc/network/interfaces`
* `/etc/resolv.conf`
* `/etc/apk/repositories`

### Carpetas ~/bin de usuario

Es muy útil que los usuarios tengan una carpeta `bin` en su carpeta personal, para poner *scripts* u otras utilidades. Eso se puede conseguir de dos formas: una global, o por usuario.

#### De forma global

Útil cuando queremos que se aplique a todos los usuarios; podemos editar `/etc/profile`, o aprovecharnos de que se incluye todos los ficheros `.sh` en `/etc/profile.d/`.

```bash
alpine:~$ cat /etc/profile.d/local_bin.sh
if [[ -d ~/bin ]]; then
    export PATH=~/bin:$PATH
fi
alpine:~$
```

Este fichero necesita acabar en `.sh`, pero no necesita permisos de ejecución; se incluye usando `source`.

#### De forma local

El *shell* que viene con **Alpine Linux** respeta la convención de leer el fichero `.profile`. Podemos hacer el cambio individualmente para cada usuario; recordad que no se hace solo.

```bash
alpine:~$ cat .profile
if [[ -d ~/bin ]]; then
    export PATH=~/bin:$PATH
fi
alpine:~$
```

## Conclusión

En este punto tengo un servidor mínimo con **Alpine Linux**, que usa 27mb de memoria, ocupa 130mb de disco (*swapfile* aparte) y con un magnífico gestor de paquetes, al que no le falta de nada.

Los paquetes de la distribución no están a la última (tenéis la opción de la rama *edge*), pero aún así están más actualizados que en **Debian**, con un *focus* importante en la seguridad. Si se instala un paquete, por ejemplo **docker**, las dependencias son muy correctas, y no se trae ni **python**, ni **gcc**, ni **git**, a diferencia de **Debian**. Esto reduce la superficie de ataque y las herramientas disponibles en caso de intrusión.

Yo lo he utilizado como nodo de un *docker swarm*, con un disco de tamaño adecuado montado en `/var/lib/docker` y un poco más de memoria disponible. Es un caso de éxito sin precedentes.
