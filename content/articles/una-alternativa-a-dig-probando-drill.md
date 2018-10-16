Title: Una alternativa a dig: probando drill
Slug: una-alternativa-a-dig-probando-drill
Date: 2018-10-22 10:00
Category: Operaciones
Tags: drill, dig, dns



Cuando trabajas con terceras partes, los problemas relacionados con la resolución DNS son demasiado habituales. Muchas veces utilizan DNS internos y cuando nos pasan los datos de conexión remota, no funciona nada. En estos casos, el procedimiento suele pasar por verificar primero la resolución DNS antes que la conectividad remota.

Para todas aquellas verificaciones que se lanzan contra los DNS, mi herramienta favorita *era* **dig**. Es completa, veraz, y te da toda la información de una sola pasada.

Sin embargo, el otro día encontré su talón de aquiles: para no instalar nada en mi máquina, utilicé un contenedor de **docker**, por supesto con **Alpine Linux**. Para aquellos que no lo sepáis, **Alpine Linux** usa una implementación de funciones DNS algo distinta de la habitual, y ello causa problemas relacionados con DNS.

Aunque mejor lo mostramos en un ejemplo: partiremos de un contenedor **Alpine Linux**.

```bash
gerard@atlantis:~$ docker run -ti --rm alpine:3.8
/ #
```

## El problema

En este punto, el contenedor no tiene la herramienta **dig** instalada, aunque lo podemos corregir de forma fácil:

```bash
/ # apk add --no-cache bind-tools
fetch http://dl-cdn.alpinelinux.org/alpine/v3.8/main/x86_64/APKINDEX.tar.gz
fetch http://dl-cdn.alpinelinux.org/alpine/v3.8/community/x86_64/APKINDEX.tar.gz
(1/5) Installing libgcc (6.4.0-r8)
(2/5) Installing json-c (0.13.1-r0)
(3/5) Installing libxml2 (2.9.8-r0)
(4/5) Installing bind-libs (9.12.2_p1-r0)
(5/5) Installing bind-tools (9.12.2_p1-r0)
Executing busybox-1.28.4-r1.trigger
OK: 9 MiB in 18 packages
/ #
```

Lanzamos una *query* DNS bastante normal, y obtenemos los resultados.

```bash
/ # dig www.google.com

; <<>> DiG 9.12.2-P1 <<>> www.google.com
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: FORMERR, id: 60730
;; flags: qr rd; QUERY: 1, ANSWER: 0, AUTHORITY: 0, ADDITIONAL: 1
...
/ #
```

Leemos la respuesta y vemos algo raro: "ANSWER: 0". No, no se ha acabado el mundo, Google funciona bien, pero nuestra herramienta no.

Esto pasa porque **musl libc** se limita a lanzar la *query* contra el primer servidor DNS de nuestro `/etc/resolv.conf`, que no es el único.

## La alternativa

Estaba yo a punto de tirar la toalla y usar un contenedor con otra distribución, pero topé casi por casualidad con otra herramienta: **drill**.

> The name drill is a pun on dig. With drill you should be able get even more information than with dig.

Se trata de una versión mejorada de **dig**, así que vale la pena intentarlo de nuevo:

```bash
/ # apk add --no-cache drill
fetch http://dl-cdn.alpinelinux.org/alpine/v3.8/main/x86_64/APKINDEX.tar.gz
fetch http://dl-cdn.alpinelinux.org/alpine/v3.8/community/x86_64/APKINDEX.tar.gz
(1/2) Installing ldns (1.7.0-r0)
(2/2) Installing drill (1.7.0-r0)
Executing busybox-1.28.4-r1.trigger
OK: 10 MiB in 20 packages
/ #
```

La misma *query* nos da un resultado correcto:

```bash
/ # drill www.google.com
;; ->>HEADER<<- opcode: QUERY, rcode: NOERROR, id: 46447
;; flags: qr rd ra ; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0
;; QUESTION SECTION:
;; www.google.com.      IN      A

;; ANSWER SECTION:
www.google.com. 97      IN      A       216.58.201.228
...
/ #
```

## Conclusión

Tenemos dos herramientas para consulta de DNS, que son **dig** y **drill**. Considerando que **drill** es más completa y más correcta que **dig**, no hay siquiera punto de comparación.

A nivel de dependencias necesarias, **drill** también sobresale: necesita menos paquetes y nos da contenedores más pequeños:

```bash
gerard@atlantis:~$ docker ps -s
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES               SIZE
e4fa4f7afb11        alpine:3.8          "/bin/sh"           40 seconds ago      Up 39 seconds                           dig                 5.05MB (virtual 9.47MB)
9f9a7b248f62        alpine:3.8          "/bin/sh"           43 seconds ago      Up 42 seconds                           drill               1.7MB (virtual 6.12MB)
gerard@atlantis:~$
```

Así pues, bienvenido **drill** y hasta otra **dig**.
