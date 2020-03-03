---
title: "Reduciendo el consumo de memoria en MongoDB"
slug: "reduciendo-el-consumo-de-memoria-en-mongodb"
date: "2020-03-03"
categories: ['Operaciones']
tags: ['mongodb', 'memoria', 'oom killer']
---

Cuando tenemos un servidor **mongodb** en un entorno productivo solemos dedicar
una máquina entera a la tarea, y no nos importa que consuma toda la memoria
disponible. Sin embargo, en entornos de prueba o de preproducción solemos hacer
convivir este servicio con otros procesos, y suelen tener conflictos de memoria.
<!--more-->

Y es que si ponemos un servidor con **mongodb**, uno o más servidores de aplicaciones
con varias aplicaciones y algún proceso auxiliar, el consumo de memoria se dispara;
el resultado suele ser la caída de algún proceso cuando entra en funcionamiento
el *OOM Killer* y empieza a matar procesos.

El asunto es que **mongodb** es una base de datos como todas las demás: intentará
ocupar toda la memoria necesaria para *cachear* datos y tenerlos a mano para la
siguiente vez que los pidan, con el fin de obtener un alto rendimiento. Sin embargo,
en este tipo de entorno compartido, el rendimiento no es tan necesario, y el coste
en máquinas es limitado...

La basta mayoría de la memoria que **mongodb** tiende a ocupar es por la *caché*
de datos del disco. Asumiendo que estamos utilizando el *storage engine* **WiredTiger**,
este valor [se calcula][1] desde las especificaciones de la máquina:

> Starting in MongoDB 3.4, the default WiredTiger internal cache size is the larger of either:
> 
> \* 50% of (RAM - 1 GB), or  
> \* 256 MB.

Si no nos importa tener un rendimiento menor podemos dedicar menos tamaño a la
*caché* de disco modificando el parámetro de la configuración, que podemos
encontrar como `storage.wiredTiger.engineConfig.cacheSizeGB`. Por supuesto, también
podemos incrementar el parámetro para dedicar más memoria y obtener un rendimiento
mayor en máquinas en las que nos lo podamos permitir.

Veamos un ejemplo; supongamos que tenemos dos servidores con **mongodb**:

* **servidorA** &rarr; 1 GB de memoria y solamente con el proceso **mongodb**.
* **servidorB** &rarr; 4 GB de memoria y **mongodb** convive con 8 aplicaciones varias.

Los valores por defecto serían los siguientes:

* **servidorA** &rarr; 256 MB (la fórmula daría 0, que es menor de 256 MB).
* **servidorB** &rarr; 1.5 GB (la mitad de 4-1, superior al mínimo de 256 MB).

Sin embargo, dadas las circunstancias de nuestro entorno, esto no tiene sentido;
el **servidorA** no necesita dejar memoria libre para ningún otro proceso, y el
**servidorB** dejaría al resto de procesos con una memoria mínima.

Supongamos ahora que queremos limitar el **servidorB** a 512 MB; para ello necesitamos
modificar su fichero de configuración para cambiar el parámetro antes mencionado:

```bash
gerard@servidorB:~$ cat /etc/mongod.conf 
...
storage:
...
  wiredTiger:
    engineConfig:
      cacheSizeGB: 0.5
...
gerard@servidorB:~$ 
```

Antes de aplicar los cambios, voy a verificar lo que hay, para poder comparar *a posteriori*:

```bash
gerard@servidorB:~$ echo "db.serverStatus()" | mongo | grep "maximum bytes configured"
			"maximum bytes configured" : 1531969536,
gerard@servidorB:~$ 
```

Para aplicar este parámetro solo necesitamos reinciar el proceso `mongod`, que
podemos hacer fácilmente delegando la operación en el gestor de procesos del sistema;
por estar en una máquina **Debian 10**, se trataría de **SystemD**.

```bash
gerard@servidorB:~$ sudo systemctl restart mongod
gerard@servidorB:~$ 
```

Y solo nos quedaría ver que el límite queda activado:

```bash
gerard@servidorB:~$ echo "db.serverStatus()" | mongo | grep "maximum bytes configured"
			"maximum bytes configured" : 536870912,
gerard@servidorB:~$ 
```

Y con esto liberamos 1 GB de memoria para el uso de las aplicaciones que conviven
en nuestro sobrecargado servidor. Si las aplicaciones están bien dimensionadas, no
deberíamos volver a ver pasar a nuestro amigo el *OOM Killer*...

[1]: https://docs.mongodb.com/manual/reference/configuration-options/#storage.wiredTiger.engineConfig.cacheSizeGB
