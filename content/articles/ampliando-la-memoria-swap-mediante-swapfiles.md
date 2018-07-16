Title: Ampliando la memoria swap mediante swapfiles
Slug: ampliando-la-memoria-swap-mediante-swapfiles
Date: 2018-07-23 09:00
Category: Operaciones
Tags: memoria, swap, swapfile



Como ya sabéis, para escribir artículos, utilizo **VirtualBox**. Últimamente no paro de clonar la misma imagen base una y otra vez, lo que me da un particionado idéntico. Sin embargo, cuando se trata de memoria *swap*, no todas las instáncias clonadas necesitan la misma *swap* y cambiarlo no es fácil.

Si nos fijamos en la última versión de **Ubuntu** podremos ver que una instalación básica **no lleva partición _swap_**. Lo que lleva es un fichero predimensionado que es utilizado como memoria *swap*.

Hay detractores de este método, pero lo que no podemos negar es que es una forma muy cómoda de añadir más *swap* o redimensionarla (casi) en caliente. Muchos proveedores de máquinas virtuales cloud ni siquiera nos dan una partición *swap*, así que conocer este método nos puede ser muy útil.

## Creando un swapfile

Supongamos que tenemos un servidor sin memoria *swap*:

```bash
gerard@cloudserver:~$ free -m
              total        used        free      shared  buff/cache   available
Mem:            492          32         409           0          50         446
Swap:             0           0           0
gerard@cloudserver:~$ cat /proc/swaps
Filename                                Type            Size    Used    Priority
gerard@cloudserver:~$
```

Para ir bien, un servidor no debería utilizarla, ya que impacta en el rendimiento, al ser más lento el disco que la memoria. Hay ocasiones en las que es legítimo usarla de forma temporal, o es preferible tenerla para evitar que nos tiren procesos por falta de memoria.

Así pues, decidimos poner *swap*, pero no tenemos un particionado que nos lo permita; vamos a recurrir a un *swapfile*, que no es otra cosa que un fichero normal que es utilizado como dispositivo de bloques para ejercer de memoria *swap*.

Para ello necesitamos un fichero del tamaño de la *swap* que necesitemos, con las únicas restricciones de pertenecer a *root* y con permisos de lectura y escritura para el propio *root*. Vamos a crearlo:

```bash
gerard@cloudserver:~$ sudo dd if=/dev/zero of=/swapfile bs=1M count=512
512+0 registros leídos
512+0 registros escritos
536870912 bytes (537 MB, 512 MiB) copied, 0,841317 s, 638 MB/s
gerard@cloudserver:~$ sudo chown root:root /swapfile
gerard@cloudserver:~$ sudo chmod 600 /swapfile
gerard@cloudserver:~$
```

Con esto tenemos nuestro dispositivo de bloques. Lo siguiente es "formatearlo" como *swap*. Esto se hace con el comando `mkswap`.

```bash
gerard@cloudserver:~$ sudo mkswap /swapfile
Configurando espacio de intercambio versión 1, tamaño = 512 MiB (536866816 bytes)
sin etiqueta, UUID=612fd4be-2ea4-4561-ab7d-81b33df5b7e5
gerard@cloudserver:~$
```

Solo queda activarlo, con el comando `swapon`.

```bash
gerard@cloudserver:~$ sudo swapon /swapfile
gerard@cloudserver:~$ free -m
              total        used        free      shared  buff/cache   available
Mem:            492          32           6           0         453         446
Swap:           511           0         511
gerard@cloudserver:~$ cat /proc/swaps
Filename                                Type            Size    Used    Priority
/swapfile                               file            524284  0       -1
gerard@cloudserver:~$
```

Como nos gusta el resultado, configuramos el fichero `/etc/fstab` para que se active automáticamente tras cada reinicio:

```bash
gerard@cloudserver:~$ grep swapfile /etc/fstab
/swapfile none swap defaults 0 0
gerard@cloudserver:~$
```

## Ampliando el swapfile

Nos quedamos cortos de *swap* y decidimos que necesitamos agrandar nuestra *swap*. Solamente tenemos que desactivar el fichero, redimensionarlo, formatearlo y volver a activarlo; sin complicaciones:

```bash
gerard@cloudserver:~$ sudo swapoff /swapfile
gerard@cloudserver:~$ sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
1024+0 registros leídos
1024+0 registros escritos
1073741824 bytes (1,1 GB, 1,0 GiB) copied, 1,82175 s, 589 MB/s
gerard@cloudserver:~$ sudo mkswap /swapfile
Configurando espacio de intercambio versión 1, tamaño = 1024 MiB (1073737728 bytes)
sin etiqueta, UUID=fb036b45-6fca-4ff2-acb6-9ae585f08c74
gerard@cloudserver:~$ sudo swapon /swapfile
gerard@cloudserver:~$
```

Y ya tenemos 1Gb de *swap*, sin sorpresas:

```bash
gerard@cloudserver:~$ free -m
              total        used        free      shared  buff/cache   available
Mem:            492          32           6           0         453         446
Swap:          1023           0        1023
gerard@cloudserver:~$ cat /proc/swaps
Filename                                Type            Size    Used    Priority
/swapfile                               file            1048572 0       -1
gerard@cloudserver:~$
```

En un futuro cercano, decidimos que hay que poner más *swap*. Ahora tenemos un nuevo problema: la *swap* existente no se puede desactivar porque no hay memoria en donde mover lo que hay en *swap*.

Eso no supone más problema, porque la memoria *swap* es una masa que se forma a partir de varios dispositivos, así que podemos añadir otro, de la misma manera:

```bash
gerard@cloudserver:~$ sudo dd if=/dev/zero of=/swapfile2 bs=1M count=3072
3072+0 registros leídos
3072+0 registros escritos
3221225472 bytes (3,2 GB, 3,0 GiB) copied, 5,16648 s, 623 MB/s
gerard@cloudserver:~$ sudo chown root:root /swapfile2
gerard@cloudserver:~$ sudo chmod 600 /swapfile2
gerard@cloudserver:~$ sudo swapon /swapfile2
swapon: /swapfile2: fallo al obtener la cabecera de intercambio
sin etiqueta, UUID=a35f5fdb-d0fe-4a8d-aecc-c03362128990
gerard@cloudserver:~$ sudo swapon /swapfile2
gerard@cloudserver:~$
```

Y como esperamos, ahora tenemos un total de 4Gb de *swap*:

```bash
gerard@cloudserver:~$ free -m
              total        used        free      shared  buff/cache   available
Mem:            492          32           6           0         452         446
Swap:          4095           0        4095
gerard@cloudserver:~$ cat /proc/swaps
Filename                                Type            Size    Used    Priority
/swapfile                               file            1048572 0       -1
/swapfile2                              file            3145724 0       -2
gerard@cloudserver:~$
```

En este punto ya podríamos desactivar la primera *swap*, ya sea para ampliarla, o para eliminarla. El contenido que tenía pasaría ahora a la segunda *swap* en donde hemos creado espacio. Nada nos impide ampliar el primer fichero para eliminar el segundo, haciendo que la segunda *swap* fuera solo un apaño temporal.
