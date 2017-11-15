Title: Ejecutando procesos desde python con popen
Slug: ejecutando-procesos-desde-python-con-popen
Date: 2017-11-20 10:00
Category: Desarrollo
Tags: python, subprocess, popen



Algunas veces nos interesa lanzar comandos *bash*, pero necesitamos de la potencia de *python* para *parsear* la salida. En otras ocasiones queremos lanzar los comandos *bash* directamente desde *python* porque se hace desde una aplicación web. En estos casos nos viene muy bien el módulo *subprocess* que nos lo permite.

Aunque no quiero dar detalles porque la idea es todavia una prueba de concepto, en mi caso concreto se trataba de hacer una herramienta web muy simple para lanzar *backups* y *restores* sobre **mongodb**, usando los comandos *mongodump* y *mongorestore*.

En este artículo he decidido poner dos ejemplos muy simplificados, de forma que no nos distraigan de lo que relamente es importante; uno es sobre como lanzar comandos y recoger resultados, mientras que el otro es un poco más avanzado y nos permite concatenar varios comandos como haríamos en *bash*.

## Un ejemplo simple

Supongamos que queremos graficar la carga del sistema, tal como nos las da el comando *uptime*. Para ello tenemos que *parsear* y convertir en números los tres valores que el comando nos da. Por ello tenemos el siguiente *script*:

```bash
gerard@atlantis:~/projects/popen$ cat uptimes.py
#!/usr/bin/env python

from subprocess import Popen, PIPE, STDOUT

proc = Popen(['uptime'], stdout=PIPE, stderr=STDOUT)
out, err = proc.communicate()

uptimes = out.rstrip().split('load average: ')[1]
uptimes = uptimes.split(', ')
uptimes = [float(e.replace(',', '.')) for e in uptimes]

times = ['1 minute', '5 minutes', '15 minutes']
for i in xrange(3):
    print 'Last %s: %s' % (times[i], uptimes[i])
gerard@atlantis:~/projects/popen$
```

La parte importante se limita a dos líneas, que son las que crean la variable `proc` y la siguiente. Se ejecuta el comando especificado en el *array* del primer parámetro de `Popen`, sin indicar entrada estándar (no hay por defecto), redirigiendo la salida de error a la salida estándar, y dejando esta como `PIPE` la convertimos en un *stream*, que luego podemos enchufar a otro proceso o recoger con el método `communicate()`, que es el caso.

El resto es un mero ejercicio de *parsing*; con algunas funciones básicas de la clase *string* (*strip*, *split* y *replace*) y algunos *castings* a *float*, tenemos lo que nos interesa. La parte de graficar queda como ejercicio para el lector.

```bash
gerard@atlantis:~/projects/popen$ ./uptimes.py
Last 1 minute: 0.28
Last 5 minutes: 0.09
Last 15 minutes: 0.03
gerard@atlantis:~/projects/popen$
```

Y podemos ver que tenemos la respuesta esperada con los valores pelados, y listos para disponer de ellos como queramos.

## Un ejemplo concatenando varios procesos

Este ejemplo es posiblemente uno de los más inútiles que puedo mostrar. Simplemente se trata de hacer algo como `seq 1 100 | grep 3 | grep 5`. No es muy útil, pero nos va a ilustrar sobre como se hacen este tipo de cosntrucciones *bash*.

El truco consiste en hacer 3 procesos, para cada uno de los comandos, usando los *streams* declarados con `PIPE` para enchufarlos a la entrada estándar del siguiente comando:

* **p1** ejecutará el `seq 1 100`
* **p2** ejecutará un `grep 3` sobre la entrada estándar, que será la salida estándar de **p1**
* **p3** ejecutará un `grep 5` sobre la entrada estándar, que será la salida estándar de **p2**

Y así queda nuestro *script*:

```bash
gerard@atlantis:~/projects/popen$ cat seq.py
#!/usr/bin/env python

from subprocess import Popen, PIPE

p1 = Popen(['seq', '1', '100'], stdout=PIPE)
p2 = Popen(['grep', '3'], stdin=p1.stdout, stdout=PIPE)
p3 = Popen(['grep', '5'], stdin=p2.stdout, stdout=PIPE)
p1.stdout.close()
p2.stdout.close()
out = p3.communicate()[0].strip()

print out
gerard@atlantis:~/projects/popen$
```

Cabe indicar que el método `communicate()` se llama solamente en el último comando de la cadena, para esperar que acabe y recoger así su salida estándar y su salida de error, que en este caso, desechamos.

Solo queda comentar que los *streams* de salida de **p1** y de **p2** se cierran después de enchufarlos a **p3**, tal como sugiere la documentación, para evitar problemas en caso de que **p3** acabe antes que **p2**, o este acabe antes que **p1**.

A partir de aquí, solo nos queda comprobar que el resultado es el mismo, tanto en *bash*, como en *python*:

```bash
gerard@atlantis:~/projects/popen$ seq 1 100 | grep 3 | grep 5
35
53
gerard@atlantis:~/projects/popen$ ./seq.py
35
53
gerard@atlantis:~/projects/popen$
```

Y con esto ampliamos nuestra *toolbox* de recursos, de forma que podamos encarar futuros retos con nuevas opciones.
