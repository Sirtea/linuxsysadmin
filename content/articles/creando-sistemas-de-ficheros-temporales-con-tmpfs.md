Title: Creando sistemas de ficheros temporales con tmpfs
Slug: creando-sistemas-de-ficheros-temporales-con-tmpfs
Date: 2015-11-16 23:15
Category: Operaciones
Tags: linux, tmpfs



A veces nos podemos encontrar con un sistema de ficheros lleno que no nos permite completar alguna acción por falta de espacio en disco. En un caso así, existe la posibilidad de sacar un sistema de ficheros completo de memoria, de una forma temporal, usando el sistema de ficheros *tmpfs*. Otra opción es la de tener un sistema de ficheros temporal, en donde podamos dejar ficheros cuya persistencia no sea necesaria entre reinicios.

El primer paso es tener un *punto de montaje*, que sea la carpeta en la que se va a montar el nuevo sistema de fichero. Por ejemplo podemos usar el punto de montaje */mnt/auxiliar*; empezaremos creándolo.

```bash
root@server:~# mkdir /mnt/auxiliar
root@server:~# 
```

Observemos como la carpeta creada se construye sobre el mismo dispositivo que la partición raíz:

```bash
root@server:~# df -h /mnt/auxiliar/
S.ficheros     Tamaño Usados  Disp Uso% Montado en
/dev/sda1        2,0G   640M  1,2G  35% /
root@server:~# 
```

## Creando el sistema de ficheros de forma temporal

Como prueba de concepto, podemos crear este sistema de ficheros de forma temporal. En caso de no salir bien, los efectos no serían permanentes.

```bash
root@server:~# mount -o size=100M -t tmpfs auxiliar /mnt/auxiliar/
root@server:~# 
```

Podemos ver como la carpeta pertenece ahora a un sistema de ficheros nuevo:

```bash
root@server:~# df -h /mnt/auxiliar/
S.ficheros     Tamaño Usados  Disp Uso% Montado en
auxiliar            100M      0  100M   0% /mnt/auxiliar
root@server:~# 
```

Cuando nos cansemos del nuevo sistema de ficheros, haya cumplido con su utilidad y ya no necesitemos su contenido, la podemos desmontar; vamos a perder todos los ficheros dentro del sistema de ficheros temporal.

```bash
root@server:~# umount /mnt/auxiliar/
root@server:~# 
```

## Haciendo el cambio permanente

Si nos interesa que este sistema de fichero se *monte* y se *desmonte* cada vez que la máquina se inicie y se apague, basta con usar el mecanismo estándar de todo sistema de ficheros *Linux*: el fichero */etc/fstab*. Basta con añadir una línea nueva con las especificaciones de este punto de montaje, por ejemplo en el final del mismo.

```bash
root@server:~# tail -1 /etc/fstab 
auxiliar /mnt/auxiliar tmpfs size=100M 0 0
root@server:~# 
```

Con este cambio es suficiente para las sesiones venideras. En caso de querer disponer inmediatamente del sistema de ficheros podemos solicitar el montaje con un comando *mount* normal, comando que va a usar las especificaciones del fichero */etc/fstab*.

```bash
root@server:~# mount /mnt/auxiliar
root@server:~# 
```

Y con esto queda completado nuestro objetivo.
