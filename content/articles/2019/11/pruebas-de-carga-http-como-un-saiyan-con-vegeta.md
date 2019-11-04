---
title: "Pruebas de carga HTTP como un Saiyan con Vegeta"
slug: "pruebas-de-carga-http-como-un-saiyan-con-vegeta"
date: "2019-11-04"
categories: ['Operaciones']
tags: ['toolbox', 'vegeta', 'go', 'carga', 'benchmark']
---

Hacía tiempo que no hacía pruebas de carga contra una web, pero como no podía
ser de otra forma, me cayó una petición de este tipo el otro día. Reconociendo
que el venerable `ab` se quedaba corto, decidí buscar una alternativa viable;
encontré una que me sacó una sonrisa: **vegeta**.<!--more-->

> **HTTP load testing tool and library. It's over 9000!**  
> Vegeta is a versatile HTTP load testing tool built out of a need to drill HTTP services
> with a constant request rate. It can be used both as a command line utility and a library.

Para los que no la conozcáis, la podéis encontrar [aquí][1]. Siguiendo la moda
actual, está escrita en **go** y no hay que instalar nada; ya de paso, en la
sección de *releases*, podéis encontrar binarios precompilados.

Como es un binario estático, no necesita librerías ni paquetería extra, y lo podemos
"dejar tirado" en alguna carpeta personal. En mi caso, lo he dejado en `~/bin/`
porque la tengo en el *path* y así no necesito indicar la ruta en cada invocación.

```bash
gerard@atlantis:~$ wget https://github.com/tsenart/vegeta/releases/download/v12.7.0/vegeta-12.7.0-linux-amd64.tar.gz
...
gerard@atlantis:~$ tar xf vegeta-12.7.0-linux-amd64.tar.gz -C bin/ vegeta
gerard@atlantis:~$ 
```

El protocolo de uso se basa en dos grandes pilares:

* `vegeta attack` &rarr; Ejecuta el test de carga y genera un fichero binario de resultados
* `vegeta report` &rarr; Analiza el fichero binario para agrupar resultados y convertirlo en legible

**TRUCO**: De hecho, ambos se pueden concatenar para no necesitar el fichero intermedio.

El objetivo del ataque se especifica por entrada estándar o por parámetro; el formato
es similar a la cabecera *HTTP request*: método y URL.

```bash
gerard@atlantis:~$ echo "GET http://localhost:8000" | vegeta attack -duration 5s | vegeta report
Requests      [total, rate, throughput]  250, 50.20, 50.17
Duration      [total, attack, wait]      4.982561765s, 4.979865973s, 2.695792ms
Latencies     [mean, 50, 95, 99, max]    2.628218ms, 2.618314ms, 2.894038ms, 3.791979ms, 3.951445ms
Bytes In      [total, mean]              461500, 1846.00
Bytes Out     [total, mean]              0, 0.00
Success       [ratio]                    100.00%
Status Codes  [code:count]               200:250  
Error Set:
gerard@atlantis:~$ 
```

En principio, el ataque tiene un número de peticiones por segundo predeterminado
(parámetro `-rate`, por defecto 50/1s), pero es interesante recalcar que indicar "0"
hace un ataque al máximo, para testear el límite de nuestro servidor, aunque entonces
se nos solicitan más parámetros...

```bash
gerard@atlantis:~$ echo "GET http://localhost:8000" | vegeta attack -duration 5s -rate 0 -max-workers 10 | vegeta report
Requests      [total, rate, throughput]  7749, 1549.75, 906.78
Duration      [total, attack, wait]      8.54561648s, 5.00014542s, 3.54547106s
Latencies     [mean, 50, 95, 99, max]    7.340269ms, 3.917375ms, 4.127071ms, 4.300204ms, 7.299045058s
Bytes In      [total, mean]              16815330, 2170.00
Bytes Out     [total, mean]              0, 0.00
Success       [ratio]                    100.00%
Status Codes  [code:count]               200:7749  
Error Set:
gerard@atlantis:~$ 
```

Considerando que se trata de un `python3 -m http.server` levantado temporalmente
para escribir el artículo, y que no es un servidor pensado para ser estresado, no
parecen unos números tan malos: 1549 peticiones por segundo. Ahora solo falta
utilizarlo para unas pruebas un poco más reales...

[1]: https://github.com/tsenart/vegeta
