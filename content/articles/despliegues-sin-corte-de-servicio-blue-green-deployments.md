Title: Despliegues sin corte de servicio: blue-green deployments
Slug: despliegues-sin-corte-de-servicio-blue-green-deployments
Date: 2018-05-28 10:00
Category: Operaciones
Tags: blue-green, deployment



Para muchas aplicaciones caseras, nos importa poco parar un servidor de aplicaciones o web. Sin embargo, en el mundo empresarial, un corte de servicio o *downtime* son palabras mayores, y normalmente vienen seguidos de un papeleo espectacular; otras veces se puede calmar la situación mediante el despido del pobre operador.

En un mundo *agile* en donde los despliegues son el pan de cada semana, nos interesa minimizar, o incluso suprimir, cualquier mención a la probabilidad de un *downtime*. Para esto existe un patrón que se llama [blue-green deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html).

La idea de fondo es muy simple: tenemos dos entornos iguales llamados **blue** y **green**, precedidos con un *proxy* o un balanceador que hace fácil dirigir el tráfico hacia uno u otro. Esto significa que podemos modificar uno de los entornos en caliente, sabiendo que **no es producción**. Solamente cuando el entorno secundario funciona bien podemos dirigir el tráfico hacia él, que **se convierte en producción**.

![Blue-green deployment]({static}/images/blue-green_deployments.jpg)

En caso de un error catastrófico no detectado, basta con volver a dirigir el tráfico al entorno anterior, que todavía tenemos funcional. Si no hubieran errores, podremos reinstalar este entorno anterior, en vistas a que pase a ser producción en un futuro cercano. Los montajes más habituales ofrecen ambos entornos, sirviendo dos puntos de entrada: uno como entorno de producción y el otro como entorno de pruebas.

## Un ejemplo práctico

Vamos a exponer una API de ejemplo que no hace nada en especial; es lo de menos en este momento. Vamos a poner dos servidores de aplicaciones por entorno y vamos a hacer balanceo de carga además de la función de dirección de tráfico. Estas son las decisiones de diseño de este ejemplo:

* Tenemos un servidor llamado *proxy* que va a ejecutar un **nginx** como balanceador y *switch*, aunque serviría otro (un **haproxy**, por ejemplo)
* El entorno **blue** se compone de dos servidores *blue1* y *blue2* escuchando en el puerto 8080
* El entorno **green** se compone de dos servidores *green1* y *green2* escuchando en el puerto 8080
* El puerto 80 del *proxy* será producción, y el puerto 8080 del mismo servidor servirá como entorno de pruebas

### El estado inicial

Tenemos una versión 1.0.0 en todos los servidores de aplicaciones. La API de ejemplo que ponemos nos muestra claramente la versión y el servidor que atendió la petición, para mayor claridad.

```bash
root@proxy:~# wget -qO- http://blue1:8080/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "blue1"}
root@proxy:~# wget -qO- http://blue2:8080/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "blue2"}
root@proxy:~# wget -qO- http://green1:8080/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "green1"}
root@proxy:~# wget -qO- http://green2:8080/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "green2"}
root@proxy:~# 
```

Decidimos que el entorno **blue** es actualmente producción, y por lo tanto, **green** es el entorno de pruebas. Simplemente necesitamos modificar la configuración del **nginx** para que apunte cada puerto al entorno que toca, por ejemplo:

```bash
root@proxy:~# cat /etc/nginx/conf.d/api.conf 
upstream blue {
	server blue1:8080;
	server blue2:8080;
}

upstream green {
	server green1:8080;
	server green2:8080;
}

server {
	listen 80;
	location / {
		proxy_pass http://blue;
	}
}

server {
	listen 8080;
	location / {
		proxy_pass http://green;
	}
}
root@proxy:~# 
```

Recargamos el **nginx** y ya tenemos lo que queríamos:

* Entorno de producción en el puerto 80, apuntando al entorno **blue**
* Entorno de pruebas en el puerto 8080, apuntando al entorno **green**

```bash
gerard@sirius:~/workspace$ curl http://proxy/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "blue1"}
gerard@sirius:~/workspace$ curl http://proxy/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "blue2"}
gerard@sirius:~/workspace$ curl http://proxy/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "blue1"}
gerard@sirius:~/workspace$ curl http://proxy/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "blue2"}
gerard@sirius:~/workspace$ 
```

```bash
gerard@sirius:~/workspace$ curl http://proxy:8080/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "green1"}
gerard@sirius:~/workspace$ curl http://proxy:8080/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "green2"}
gerard@sirius:~/workspace$ curl http://proxy:8080/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "green1"}
gerard@sirius:~/workspace$ curl http://proxy:8080/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "green2"}
gerard@sirius:~/workspace$ 
```

### Un despliegue fallido

Desplegamos una nueva versión en el entorno de pruebas, actualmente como entorno **green**. Eso significa deplegar nueva versión en *green1* y en *green2*. Como el entorno de producción es **blue**, cualquier desastre que pase en **green** no va a afectar a la operativa.

Tras subir **green** a la versión 1.1.0, vemos en el *endpoint* de pruebas que no funciona:

```bash
gerard@sirius:~/workspace$ curl http://proxy:8080/fake/
{"status": "500", "message": "Errors everywhere...", "version": "1.1.0", "server": "green1"}
gerard@sirius:~/workspace$ curl http://proxy:8080/fake/
{"status": "500", "message": "Errors everywhere...", "version": "1.1.0", "server": "green2"}
gerard@sirius:~/workspace$ 
```

Pero no pasa nada; el entorno de producción sigue apuntando a **blue**, que no hemos modificado y por lo tanto, sigue funcionando con la versión anterior.

```bash
gerard@sirius:~/workspace$ curl http://proxy/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "blue1"}
gerard@sirius:~/workspace$ curl http://proxy/fake/
{"status": "200", "message": "Everything is OK", "version": "1.0.0", "server": "blue2"}
gerard@sirius:~/workspace$ 
```

Basta con no cambiar la configuración del **nginx** en el servidor *proxy* para no exponer el desastre más allá del entorno de pruebas. Si algún manazas hubiera cambiado ya la configuración del *proxy*, el *rollback* consistiría en modificar de nuevo la configuración del *proxy*.

### Un despliegue con éxito

Tras investigar el problema de la nueva versión, se localiza un *bug* que causa los errores y se escribe un *hotfix*, que se libera como version 1.1.1; supongamos que tenemos éxito.

```bash
gerard@sirius:~/workspace$ curl http://proxy:8080/fake/
{"status": "200", "message": "Everything is OK", "version": "1.1.1", "server": "green1"}
gerard@sirius:~/workspace$ curl http://proxy:8080/fake/
{"status": "200", "message": "Everything is OK", "version": "1.1.1", "server": "green2"}
gerard@sirius:~/workspace$ 
```

Basta con modificar la configuración del *proxy* para que producción apunte a **green**, en donde tenemos la nueva versión estable. En el caso de la configuración expuesta anteriormente, bastaría con cambiar las directivas `proxy_pass`.

```bash
root@proxy:~# cat /etc/nginx/conf.d/api.conf 
upstream blue {
	server blue1:8080;
	server blue2:8080;
}

upstream green {
	server green1:8080;
	server green2:8080;
}

server {
	listen 80;
	location / {
		proxy_pass http://green;
	}
}

server {
	listen 8080;
	location / {
		proxy_pass http://blue;
	}
}
root@proxy:~# nginx -s reload
2018/05/07 17:43:26 [notice] 21#21: signal process started
root@proxy:~# 
```

Puesto que un *reload* del **nginx** no provoca pérdida de paquetes ni de peticiones, solo queda ver que las peticiones del entorno de producción son atendidas en los servidores *green1* y *green2*.

```bash
gerard@sirius:~/workspace$ curl http://proxy/fake/
{"status": "200", "message": "Everything is OK", "version": "1.1.1", "server": "green1"}
gerard@sirius:~/workspace$ curl http://proxy/fake/
{"status": "200", "message": "Everything is OK", "version": "1.1.1", "server": "green2"}
gerard@sirius:~/workspace$ 
```

En este punto, el estado de nuestro servicio ha cambiado; ahora tenemos:

* Entorno de producción en el puerto 80, apuntando al entorno **green**, con versión 1.1.1
* Entorno de pruebas en el puerto 8080, apuntando al entorno **blue**, con versión 1.0.0

Por lo tanto, los nuevos despliegues se harían en el entorno **blue**, que ha dejado de ser el entorno de producción en favor del entorno **green**. Como pequeño detalle, sería interesante subir **blue** a la versión nueva, para tener ambos entornos idénticos, como punto de partida para una posible nueva versión.

## Y que pasa con las bases de datos?

En realidad es un problema que no solo atañe a las bases de datos; otras partes *stateful* como sistemas de ficheros, colas y APIs remotas también deben ser tratadas en este caso. Este es un tema que no queda bien reflejado, habiendo dos corrientes enfrentadas que defienden sus puntos de vista:

* Bases de datos duplicadas
* Bases de datos compartidas

En caso de duplicar la base de datos en ambos entornos, ganamos la posibilidad de modificarla en nuestros *tests*, ya que las pruebas en el entorno de pruebas no van a afectar al entorno de producción. El problema en este punto es que tenemos la necesidad de mantenerlas sincronizadas, pudiendo ser un proceso lento en caso de un conjunto de datos grande.

Si compartimos la base de datos entre los entornos **blue** y **green**, nos ahorramos la sincronización, a costa de no poder modificar nada en el entorno de pruebas, ya que estaríamos modificando los mismos datos que se usan en el entorno de producción.

Un punto espinoso en esta configuración compartido son las migraciones de la base de datos; hacerlas antes causaría *downtime* en la versión anterior hasta instalar la nueva versión, y hacerlas después causaría *downtime* en la nueva versión hasta poder hacer la migración. La solución más aceptada es hacer una *release* intermedia, capaz de trabajar con la base de datos migrada y sin migrar; sería responsabilidad de esta *release* intermedia detectar si la base de datos está migrada o no, y suplir las carencias mediante lógica específica.
