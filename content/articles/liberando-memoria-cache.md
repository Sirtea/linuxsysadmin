Title: Liberando memoria caché
Slug: liberando-memoria-cache
Date: 2015-11-02 14:00
Category: Operaciones
Tags: linux, kernel, memory manager, drop caches



A veces nos encontramos que nuestro sistema linux parece tener la
memoria *virtual* ocupada, cuando no tenemos nada de memoria *RSS*;
esto no es un problema, ya que por la forma de funcionar del
*memory manager* de linux, se conserva "por si acaso" y se libera
cuando realmente se necesita.

```bash
gerard@desktop:~$ free -m
             total       used       free     shared    buffers     cached
Mem:          3858       3226        632          0        114       2545
-/+ buffers/cache:        566       3291
Swap:         2381          0       2381
gerard@desktop:~$ 
```

Sin embargo este detalle nos puede resultar molesto y puede que queramos
**liberar** esa memoria de verdad, por ejemplo, para comparar memoria
real ocupada por el sistema o sencillamente porque así lo queremos.

En este caso no tenemos mas remedio que solicitar el *memory manager*
que la libere, escribiendo en el fichero de control habilitado para ello,
de acuerdo a la [documentación del *kernel* de linux](https://www.kernel.org/doc/Documentation/sysctl/vm.txt).

```bash
drop_caches

Writing to this will cause the kernel to drop clean caches, as well as
reclaimable slab objects like dentries and inodes.  Once dropped, their
memory becomes free.

To free pagecache:
    echo 1 > /proc/sys/vm/drop_caches
To free reclaimable slab objects (includes dentries and inodes):
    echo 2 > /proc/sys/vm/drop_caches
To free slab objects and pagecache:
    echo 3 > /proc/sys/vm/drop_caches

This is a non-destructive operation and will not free any dirty objects.
To increase the number of objects freed by this operation, the user may run
`sync' prior to writing to /proc/sys/vm/drop_caches.  This will minimize the
number of dirty objects on the system and create more candidates to be
dropped.
```

Este fichero viene por defecto con permisos de escritura solamente para
el usuario **root** y no se puede escribir sin el mismo. Como no queremos
trabajar con el usuario **root**, vamos a usar el comando *sudo* con un
usuario normal:

```bash
gerard@desktop:~$ sudo bash -c "echo 3 > /proc/sys/vm/drop_caches"
gerard@desktop:~$ 
```

Alternativamente, podemos utilizar el comando *tee* para realizar la
misma operación, sin el envoltorio de *bash*:

```bash
gerard@desktop:~$ echo 3 | sudo tee /proc/sys/vm/drop_caches
3
gerard@desktop:~$ 
```

Y finalmente nuestra memoria queda vacía de todo aquello que no era
indispensable para la ejecución del sistema.

```bash
gerard@desktop:~$ free -m
             total       used       free     shared    buffers     cached
Mem:          3858        752       3105          0          2        207
-/+ buffers/cache:        542       3315
Swap:         2381          0       2381
gerard@desktop:~$ 
```

¡Acabamos de liberar 2 gigabytes de memoria!

**CUIDADO**: Esta operación puede afectar el rendimiento puntual del
sistema, ya que en caso de volver a necesitar la información *cacheada*,
deberá volver a recargar la memoria, probablemente desde disco.
