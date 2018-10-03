Title: He acabado migrando de python 2 a 3
Slug: he-acabado-migrando-de-python-2-a-3
Date: 2018-10-08 10:00
Category: Miscelánea
Tags: python, migración



He sido fan de **python** desde hace muchos años. Inicialmente lo empecé a utilizar porque, junto a **bash**, era la herramienta que venía por defecto en todos los servidores que administraba. Pero con el tiempo salió la versión 3, incompatible con la 2; al final me ha tocado migrar forzadamente.

La primera versión de **python** salió en 1991, y la segunda versión se publicó en el año 2000. Cuando salió la versión 3 en el año 2008 se decidieron cambios en el lenguaje que lo hicieron incompatible con al versión 2, mucho más extendida. Como en el 2010 salió la versión 2.7, todos creimos que seguiríamos usando la segunda versión.

Las librerías existentes en la versión 2 tuvieron que adaptarse para soportar la nueva versión y la antigua, y habiendo cientos de ellas, el proceso encontró una severa resistencia, aunque con el tiempo casi todas las librerías han pasado por el aro.

Los desarrolladores tardaron todavía más en migrar de versión, puesto que les faltaban las librerías habituales en la nueva versión; en el mundo de sistemas la resistencia fue todavía mayor: casi todas las distribuciones usaban por defecto la versión 2, y los lentos ciclos de lanzamiento de sus versiones no ayudaron a mejorar la situación.

Yo fuí uno de esos usuarios de **python** que creían que **python 3** estaba condenado al fracaso, y me dije a mí mismo que nunca iba a migrar de versión. Los motivos fueron varios:

* Los sistemas operativos usaban **python 2** por defecto, con la notable excepción de **ArchLinux**
* Algunas de las herramientas de sistemas, como **fabric** o **ansible** carecían de soporte para **python 3**
* El código *legacy* de mi sitio de trabajo seguía en **python 2**
* Algunos proyectos necesitaban de librerías o *frameworks* que no estaban portados, como **django**

**Me equivocaba**

La fecha de jubilación de **python 2** ha llegado; la versión 2.7 era solamente un intento de acercar gramáticas hacia la versión 3. El final de la segunda versión es inapelable, con incluso [un contador de marcha atrás](https://pythonclock.org/).

Si hay que elegir una versión, en [el sitio web](https://wiki.python.org/moin/Python2orPython3) son claros:

> Python 2.x is legacy, Python 3.x is the present and future of the language  

Todos los puntos que me aferraban a la segunda versión se están diluyendo:

* Aunque los sistemas operativos siguen teniendo la versión 2 por defecto, pero:
	* El modelo de trabajo con contenedores nos desacopla de las necesidades del sistema principal
	* Siempre hay un servicio que necesita la 3; esto nos proporciona ambas versiones
* Todas las herramientas necesarias para un DevOps soportan **python 3**
* En mi nuevo trabajo no se desarrolla en **python**, y en las compañías que lo hacen, se migra controladamente utilizando contenedores
* Las librerías y *frameworks* principales ya funcionan en **python 3**
	* **Django** lo soporta desde la versión 1.5
	* Solamente un puñado de librerías [no han sido portadas](https://python3wos.appspot.com/)

Las grandes compañías (**Google**, **Facebook**, **Instagram**...) han apostado fuerte por la nueva versión, que no para de recibir mejoras de rendimiento y funcionalidad. Visto el panorama, he decidido migrar yo también todas mis imágenes y proyectos a **python 3** antes de que sea tarde para hacerlo. **Es el momento**.
