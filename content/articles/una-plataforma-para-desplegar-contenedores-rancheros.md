Title: Una plataforma para desplegar contenedores: RancherOS
Slug: una-plataforma-para-desplegar-contenedores-rancheros
Date: 2018-01-15 10:00
Category: Sistemas
Tags: docker, cluster, rancher



Aquellos que seguís este *blog* de forma regular, habréis notado mi predilección por los contenedores **docker**, en gran parte porque es con lo que trabajo en mi día a día. Hartos de usar la plataforma *custom* que tenemos en la compañía buscamos una nueva, que simplifique el trabajo que hacemos.

Lo que tenemos actualmente es una amalgama de *hosts* en donde desplegamos contenedores, en algunos servicios, y en otros los servicios que nos permiten hacer un *routing* adecuado, por ejemplo, *proxies* reversos, balanceadores y *firewalls*.

Sin embargo, estos contenedores se ven entre sí, así como a los *hosts* que los levantan. A todo esto, el conjunto de servicios desplegados empezaba a impactar en la capacidad de mantenerla. En especial, la demanda de segregación de red de algún cliente nos hizo buscar alternativas de forma acelerada.

Aunque no es nuestro futuro inmediato, salimos del paso con una solución completa que se llama [Rancher](http://rancher.com/). Su filosofía es muy simple: necesitamos un servidor de control que tenga una foto del *cluster* (por supuesto un contenedor **docker**, y un conjunto de servidores que añadan recursos al mismo (mediante otro servidor **docker** que corre un agente). De hecho, en el *deploy* más simple, basta con tener ambas cosas en la misma máquina.

Para despliegues mas profesionales, disponen de un fichero *.iso* para instalar un sistema operativo para ejecutar solamente **Rancher**, que tiene lo básico para ejecutar **Docker** y levanta sus servicios como contenedores.

## Instalación de Rancher

### Servidor

Para levantar el servidor de **Rancher** vamos a seguir los pasos de [la instalación](http://docs.rancher.com/rancher/latest/en/installing-rancher/installing-server/). Tan simple como levantar un contenedor.

```bash
gerard@aldebaran:~$ docker run -d --restart=unless-stopped -p 8080:8080 rancher/server
```

Este contenedor nos ofrece la base de datos de control y una bonita interfaz de usuario en el puerto 8080 para administrar nuestro *cluster*.

Solo nos queda ver la interfaz de administración para comprobar que funciona, en <http://localhost:8080/>.

![Rancher panel]({static}/images/rancher-panel.png)

### Hosts

En la interfaz de administración vemos una pestaña "Infraestructure" en donde podemos seleccionar "Hosts". Si le damos al botón "Add Host", veremos que añadir un *host* es trivial; a la larga todo se reduce en levantar otro contenedor *rancher/agent* en ese *host*, para que nuestro servidor lo reconozca y le pueda enviar órdenes.

## Conceptos básicos de Rancher

Si jugamos un rato con la interfaz, vamos a ver varios conceptos, que aquí se resumen:

* **Entornos**: Agrupaciones lógicas de recursos (*hosts*). Cada entorno tiene sus propios *hosts*. Solo hay conectividad de contenedores cuando están en el mismo entorno, dentro de **Rancher**.
* **Stacks**: Agrupaciones lógicas de servicios, se despliegan en un entorno concreto.
* **Servicios**: Un servicio es la unidad mínima escalable, y se compone de un *primary service* (un contenedor) y de cualquier número de *sidekick containers*. Esta es la unidad mínima escalable. Se garantiza que todos los contenedores de este servicio se van a desplegar en un solo *host*, y en caso de escalarlo, este *pack* se repite en otros *hosts* de acuerdo con las leyes de afinidad. Solo se pueden usar volúmenes de un contenedor en el mismo servicio.
* **Balanceadores**: Básicamente se trata de contenedores *haproxy* que nos permiten poner un balanceador sin tener que crear nosotros un servicio especializado.
* **Catálogo**: Es un conjunto de plantillas de servicios prefabricados que podemos usar para crear nuestras propias *stacks*. Podemos añadir nuestra *stack* para el fácil despliegue de *stacks* genéricas, por ejemplo bases de datos o herramientas de monitorización.

La parte importante es que podemos declarar nuestros contenedores dentro de los servicios de la misma forma que lo hacemos en **docker**, pero con un bonito formulario web.

**TRUCO**: Los servicios se pueden actualizar usando nuevas versiones de nuestros contenedores. **Rancher** va a crear un nuevo conjunto de servicios sin eliminar los antiguos. A *posteriori* podemos hacer un "Finish upgrade", que eliminaría los viejos contenedores asumiendo que nos gusta el resultado, o podemos hacer un "Rollback", que eliminaría los contenedores nuevos para dejar los viejos, en caso de que la nueva versión no nos satisfaga.

## Un caso práctico

Supongamos que tenemos una web con datos financieros, con acceso por parte de muchos visitantes y con un entrada de nuevos datos a la base de datos mediante carga de ficheros por SFTP.

Vamos a suponer que trabajamos en un entorno de test, específico para este proyecto por aislamiento de red; eso nos simplifica las decisiones. En un futuro se podría crear otro entorno para producción o para otro proyecto, pero de momento nos vale. También es posible hacer entornos compartidos para varios proyectos.

Algunas decisiones de diseño:

* Nuestra aplicación es un solo contenedor, que vamos a escalar para soportar la carga.
* Vamos a balancear la carga entre todos los contenedores de aplicación.
* La base de datos va a ir separada en otro contenedor, que todas las instancias de la aplicación puedan ver.
* El sistema de inyección de datos se va a componer de 3 contenedores: uno para el SFTP, uno para el volumen de datos y otro para el procesador de dichos datos.

Y con este *setup*, podemos empezar a construir nuestro entorno. no importa cuantos *stacks* hagamos, pero seguramente, la base de datos tendrá su propio *stack* porque lo pondremos directamente del catálogo. Podemos poner todo el resto en un solo *stack* o separarlos por subsistemas (web balanceada, bases de datos, inyector de datos).

1. La parte mas fácil es la base de datos. Creamos un servicio simple para que todos lo utilicen.
2. Los contenedores de aplicación van a ser otro servicio. Que sean servicios individuales nos permite escalarlos individualmente del resto de componentes.
3. Creamos un balanceador para el servicio de aplicación. En este punto ya deberíamos poder acceder al entorno, aunque sin la entrada de datos.
4. Los contenedores del sistema de inyección de datos deben formar parte de un único servicio, porque es la única forma de que puedan montar los volúmenes del contenedor de datos. Dejaremos este servicio escalado a 1, que nos va a poner un contenedor de cada en una sola de las máquinas. No es importante que contenedor es el primario, pero vamos a poner el SFTP por un sencillo motivo: solo los contenedores primarios pueden ser el objetivo del balanceador, que de momento no pondremos, pero tal vez algún día lo queramos.

Y con esto tendremos nuestro proyecto corriendo. Es el momento de guardar las *stacks* en el catálogo, ya que eso va a simplificar el *deploy* cuando creemos otro entorno.
