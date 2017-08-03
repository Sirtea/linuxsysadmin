Title: Evitando problemas de concurrencia múltiple con flock
Slug: evitando-problemas-de-concurrencia-multiple-con-flock
Date: 2017-08-07 10:00
Category: Sistemas
Tags: flock



Cuando trabajas con procesos en *background*, es fácil que algunos de los procesos hagan algo que necesite exclusividad, no siendo seguro ejecutar varios de estos procesos a la vez. Por ejemplo, archivos que se descomprimen, se procesan y luego se borran; si usan la misma carpeta suele ser un problema.

No vamos a entrar en como se lanzan estos procesos, pero vamos a dar énfasis en que no deben ejecutarse a la vez. Para ello, vamos a suponer que tenemos un proceso que nos interesa ejecutar en exclusividad. Voy a sustituir este proceso por un *script*, para que no nos distraigamos del punto importante.

```bash
gerard@aldebaran:~/flock_test$ cat process.sh 
#!/bin/bash

echo "$(date +%H:%M:%S) - Starting process in terminal $1"
sleep 5
echo "$(date +%H:%M:%S) - Process ended in terminal $1"
gerard@aldebaran:~/flock_test$ 
```

Muchos de los desarrolladores os propondrían miles de soluciones para evitar este caso, pero si buscamos en la *toolbox* de Linux, podemos encontrar herramientas útiles. En mi caso concreto encontré el comando **flock**, que actúa bloqueando un comando, en base a la existencia de un fichero de *lock*.

## Ejecutando casi concurrentemente

Para conseguirlo, voy a abrir dos terminales, uno para cada proceso. El *script* va a recibir el numero de terminal por un parámetro, que voy a poner manualmente.

Vamos al primer terminal, y ejecutamos nuestro *script*:

```bash
gerard@aldebaran:~/flock_test$ ./process.sh 1
12:43:38 - Starting process in terminal 1
12:43:43 - Process ended in terminal 1
gerard@aldebaran:~/flock_test$ 
```

Antes de que acabe, cambio al otro terminal y ejecuto lo mismo:

```bash
gerard@aldebaran:~/flock_test$ ./process.sh 2
12:43:40 - Starting process in terminal 2
12:43:45 - Process ended in terminal 2
gerard@aldebaran:~/flock_test$ 
```

Si juntamos las líneas de *log* y las ordenamos, vemos claramente que los procesos estuvieron en algún momento ejecutándose a la vez.

```bash
12:43:38 - Starting process in terminal 1
12:43:40 - Starting process in terminal 2
12:43:43 - Process ended in terminal 1
12:43:45 - Process ended in terminal 2
```

En este caso, no parece peligroso que se ejecuten a la vez, pero hay que usar la imaginación y creernos que podrían dar problemas ejecutados a la vez.

## Ejecución exclusiva con flock

Como puede interesarnos que no se ejecuten a la vez, podemos utilizar el comando **flock** para conseguir que ambos procesos esperen ordenadamente la posibilidad de ejecutarse.

El comando **flock** esperaría la inexistencia de un *lock* en el fichero indicado, momento en el que pondría dicho *lock* para asegurar que ningún otro proceso pudiera ejecutarse. Lo siguiente sería ejecutar nuestro *script*, y finalmente, eliminar el *lock* puesto. Otro proceso concurrente quedaría a la espera de la liberación de *lock* antes de poder proceder, de manera similar al anterior.

El proceso va a ser el mismo: ejecutamos el *script* en ambos terminales, prefijado esta vez por el comando **flock** y el fichero sobre el que se va a poner el *lock*. Pasamos a juntar las líneas de ambos terminales por brevedad:

```bash
12:44:59 - Starting process in terminal 1
12:45:04 - Process ended in terminal 1
12:45:04 - Starting process in terminal 2
12:45:09 - Process ended in terminal 2
```

Y con esto podemos ver que el proceso del terminal 2 ha tenido que esperar a que el comando **flock** en el primer terminal acabara, antes de poder proceder a ejecutar su *script*. Con eso se garantiza la exclusividad de ejecución y los problemas que podría haber derivados de esta situación.

En un caso de *boom* de procesos, podríamos ver un grupo de procesos esperando sin lanzar sus respectivos *scripts*, mientras que uno solo de ello estaría ejecutando en exclusividad.
