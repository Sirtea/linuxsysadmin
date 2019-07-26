---
title: "Python como una calculadora estadística"
slug: "python-como-una-calculadora-estadistica"
date: 2016-10-17
categories: ['Desarrollo']
tags: ['linux', 'python', 'media', 'desviación estándar']
---

El otro día me encontraba en mi trabajo con otra petición muy especial: se necesitaba un *check* para **Nagios** que contara las apariciones de cierto tipo de errores en un fichero de *log*. Ese *check* debía saltar en función de cuán alejado estaba el valor de las últimas 100 muestras.<!--more-->

Guardar una muestra de valores en un fichero no supone ningún problema en **Linux**. Sin embargo, hacer cálculos estadísticos en **bash** es un suicidio. Eso nos obligaba a utilizar un lenguaje mas elaborado, pero existente en todas las máquinas: **python**. Sin embargo, el módulo **numpy** no estaba en todas las máquinas interesadas; instalarlo no era una opción. Así que me tocó programarlo a mí.

Desempolvando mis apuntes de estadística en forma de [Wikipedia](https://en.wikipedia.org/wiki/Standard_deviation), tenemos lo siguiente:

> For a finite set of numbers, the standard deviation is found by taking the square root of the average of the squared deviations of the values from their average value.

Para los matemáticos, también hay la fórmula, aunque para mi, con el ejemplo me vale.

## Un caso concreto

Tenemos el conjunto de valores del ejemplo: 2, 4, 4, 4, 5, 5, 7, 9. Vamos a necesitar su valor medio, que es 5 (la suma de los valores entre el número de valores).

Obtenemos un nuevo conjunto de desviaciones de los valores respecto a la media: (2-5), (4-5), (4-5), (4-5), (5-5), (5-5), (7-5), (9-5). Para resumir, queda -3, -1, -1, -1, 0, 0, 2, 4.

El siguiente paso es obtener los cuadrados de las desviaciones anteriores: 9, 1, 1, 1, 0, 0, 4, 16.

De ese conjunto se saca la media y ya tenemos el cuadrado desviación estándar: (9+1+1+1+0+0+4+16)/8 = 32/8 = 4.

Finalmente hacemos la raíz cuadrada y obtenemos la desviación estándar: 2.

## Un script que calcule por nosotros

Vamos a simplificar el proceso anterior simplificando el proceso con 3 funciones:

* Media
* Cuadrado de la desviación de un valor concreto
* Raíz cuadrada

La media se utiliza al principio para calcular las desviaciones, y al final, para hacer la media de las desviaciones cuadradas. La otra función va a ser una que nos dé la desviación de un valor al cuadrado, dado su media y el valor mismo.

Con estas funciones es muy fácil de escribir un código legible, que vamos a guardar en un fichero *some_math.py*:

```python
#!/usr/bin/env python

import math

def average(samples):
    return sum(samples)*1.0 / len(samples)

def stdev(samples):
    avg = average(samples)
    variance = map(lambda x: (x - avg)**2, samples)
    return math.sqrt(average(variance))

values = [2, 4, 4, 4, 5, 5, 7, 9]
print 'Average:', average(values)
print 'StDev:', stdev(values)
```

Y solamente nos queda comprobar que funciona, previa concesión de permisos de ejecución.

```
gerard@aldebaran:~$ ./some_math.py 
Average: 5.0
StDev: 2.0
gerard@aldebaran:~$ 
```

Elegante y efectivo...
