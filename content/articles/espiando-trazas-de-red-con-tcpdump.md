Title: Espiando trazas de red con tcpdump
Slug: espiando-trazas-de-red-con-tcpdump
Date: 2017-08-14 10:00
Category: Operaciones
Tags: tcpdump, red, trazas, evidencias



No suelen haber errores de conexión en los entornos que administro; sin embargo, alguna vez los hay. Esto supone un marrón, porque la red es ese elemento que escapa a mi gestión; la gente que se dedica a eso suele negar estos problemas argumentando cualquier excusa. Para eso está **tcpdump**.

Las pocas veces que tengo que recurrir a esto para conseguir evidencias siempre es una fiesta, porque como no lo utilizo de forma habitual, me olvido fácilmente de los parámetros más básicos. Y esto pretende ser una chuleta para el futuro.

Normalmente solo me encargo de capturar los paquetes en un fichero de formato *.pcap*, dejando a otro más experto en el tema el gusto de interpretarlos. Claro que muchas otras veces son usados como evidencias sin análisis previo...

## Elegir la interfaz a usar

Usaremos el *flag -i* para indicar la interfaz (o todas con *any*), pudiendo consultar las disponibles con el flag *-D*.

```bash
tcpdump -D
tcpdump -i eth0
tcpdump -i any
```

## Filtrar por varios criterios

Como el tamaño del fichero final crece descontroladamente, vale la pena usar filtros, que en **tcpdump** son combinaciones de *expresiones*.

Una *expresión* puede ser de 3 tipos:

* **De tipo**: *host* (ej. 172.16.0.3), *net* (ej. 10.0.0.0/8) y *port* (ej. 443)
* **De dirección**: *src*, *dst* o nada (que significa ambas)
* **De protocolo**: *tcp*, *udp* o *icmp*

**NOTA**: Esta lista no está completa. Revisad las páginas *man* para más detalles.

Así pues, para filtrar el tráfico que se origina en una red local 192.168.1.0/24, podríamos usar algo como:

```bash
tcpdump -i any src net 192.168.1.0/24
```

Podemos combinar grupos de expresiones con los operadores *not*, *or* y *and*, con uso de paréntesis para priorizar operadores.

```bash
tcpdump src 10.0.2.4 and (dst port 3389 or 22)
```

## Captura de un fichero para su uso posterior

Ver los paquetes en local es una opción válida, pero dependiendo del volumen de tráfico capturado puede resultar en dejarse la vista. En estos casos es más fácil guardar el resultado en un fichero que luego pueda ser leído, por el mismo **tcpdump** (con el *flag -r*), o por una cómoda aplicación de escritorio, como por ejemplo, [Wireshark](https://www.wireshark.org/).

En este caso, basta con utilizar un *flag* que le indique que tiene que guardar un fichero. Este *flag* es el *flag -w*.

```bash
tcpdump -i eth0 tcp -w traffic.pcap
```

***Y con estas pinceladas básicas, podemos aportar evidencias para que el experto se lo mire***
