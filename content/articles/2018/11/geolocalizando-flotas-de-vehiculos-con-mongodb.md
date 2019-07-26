---
title: "Geolocalizando flotas de vehículos con MongoDB"
slug: "geolocalizando-flotas-de-vehiculos-con-mongodb"
date: 2018-11-26
categories: ['Desarrollo']
tags: ['geolocalización', 'mongodb', 'python']
---

Soy un aficionado a las películas bélicas, especialmente las referentes a la Segunda Guerra Mundial. Una de las imágenes más impactantes es cuando salen los centros de mando, donde los generales tienen una mesa con un mapa y la disposición de sus fuerzas, que se actualizan cuando llegan los mensajeros.<!--more-->

Trasladando el problema fuera del ambiente bélico, y adaptando a las tecnologías actuales, veríamos que esta imagen es una bonita aproximación para un sistema de geolocalización:

* Una base de datos para guardar la posición y tamaño de tus unidades
* Un *feed* periódico de actualizaciones, por ejemplo vía REST
* Y por supuesto con una encriptación SSL, que rebaja a un broma la criptografía del momento

Por supuesto, hoy en día no tenemos un conflicto bélico tan grande como para justificar este sistema, pero algunos clientes están interesados en geolocalizar flotas de vehículos, o en poner sus instalaciones en un mapa, con vistas a darse a conocer.

Dependiendo de si el punto de referencia es móvil o no, y de si los puntos a geolocalizar se mueven o no, damos pie a una variedad muy interesante de problemas que podemos resolver:

* Un sistema de control de flotas de camiones, taxis o barcos
* Una aplicación turística para nuestro móvil
* Recordatorio de sitios en donde hemos aparcado el coche o guardado objetos
* Seguimiento de personas u objetivos

Para no alargar innecesariamente, vamos a suponer que estamos haciendo un control de flotas de vehículos; será más fácil hacerse a la idea de esta manera.

Trabajar con un modelo de geolocalización plano es fácil, pero no práctico; además, muchos motores de datos nos ofrecen el modelo esférico de forma fácil. Hay varias bases de datos que trabajan bien con modelos de geolocalización esféricos, como por ejemplo **PostgreSQL**, **Redis** o **MongoDB**.

Personalmente soy un apasionado de las bases de datos **NoSQL**, así que me limito a considerar **Redis** y **MongoDB**. He descartado **Redis** por el gran conocimiento de **MongoDB** del que dispongo, y por una letra pequeña del comando **Redis** [GEOADD](https://redis.io/commands/geoadd):

> Valid latitudes are from -85.05112878 to 85.05112878 degrees.

¿Y que pasa si trabajamos cerca de los polos? Mejor vamos a lo seguro y seguimos con **MongoDB**.

## Centrándonos en el problema con MongoDB

Dicen que **MongoDB** es una base de datos *schemaless*. Pocas aplicaciones tienen esto: herencia, versiones distintas de documentos, ... Una aplicación decente va a tener un *schema* más o menos fijo y si tratamos de geolocalización, más todavía.

El modelo esférico **MongoDB** exije el uso de un estándar de documentos para los [objetos GeoJSON](https://docs.mongodb.com/manual/reference/geojson/). Me gustan especialmente los de tipo **Point** (aunque es mi opinión personal).

De esta forma, podemos construir nuestros documentos con un campo tipo **Point** para determinar su posición. Consultar la posición de un vehículo desde un centro de mando, o buscar un taxi disponible a una distancia aceptable desde el punto en donde tengamos al solicitante, se vuelve un problema trivial. Ya de paso, podemos calcular la distancia al vehículo por el mismo precio.

### Guardando un documento posicional

Un documento con un campo "posición" solo necesita que dicha "posición" se guarde como un **Point**. Sin embargo, para poder lanzar consultas geoespaciales, se necesita un índice especial: el índice `2dphere` (más información [aquí](https://docs.mongodb.com/manual/core/2dsphere/)). Por supuesto, este índice puede ser compuesto con otros campos.

Como ejemplo de inserción podemos poner el siguiente:

```python3
def save_vehicle(name, lon, lat):
	db.vehicles.create_index([('location', pymongo.GEOSPHERE)])
	doc = {
		'name': name,
		'location': {
			'type': 'Point',
			'coordinates': [lon, lat],
		}
	}
	db.vehicles.insert_one(doc)
```

**NOTA**: La operación `create_index` reemplaza la anterior `ensure_index`, y por lo tanto, no va a hacer nada si el índice ya existiera.

Un posible *update* debería respetar la forma del **Point** presente en el campo "location", pero el índice ya estaría presente.

### Consultando documentos cercanos con su distancia

**MongoDB** nos ofrece una serie de [operadores de geolocalización](https://docs.mongodb.com/manual/geospatial-queries/#geospatial-query-operators). Básicamente se nos permite buscar puntos cercanos, puntos dentro de cierta área, e incluso polígonos que intersectan con otros. Aplicando al mundo de los puntos, solo aplican las dos primeras.

Buscar objetos en una cierta área es muy interesante para limitar resultados a "zonas visibles", especialmente para confeccionar mapas. La operación de cercanía no es tan útil; nos da objetos cercanos ordenados por cercanía, pero no nos proporciona la distancia a la que están.

Esto casi nos obliga a utilizar el *aggregation framework* para realizar el mismo trabajo. Nuestras queries se vuelven un poco más complejas, pero nos proporciona la distancia de los objetos al punto de referencia.

Por ejemplo, para buscar un taxi disponible, podríamos hacer algo como lo siguiente:

```python3
point = {
    'type': 'Point',
    'coordinates': [lon, lat],
}
pipeline = [
    {
        '$geoNear': {
            'query': {'available': True},
            'near': point,
            'distanceField': 'dist',
            'distanceMultiplier': 0.001,
            'spherical': True,
        },
    },
]
cursor = db.taxis.aggregate(pipeline)
```

En este caso buscamos taxis con disponibilidad, por cercanía al punto `point` y guardando la distancia en el campo `dist`, con un multiplicador de 0,001 que, básicamente, lo pasa a kilometros.

Estos son los campos más útiles:

* `query` &rarr; El primer filtro que se realiza; solo se van a considerar los documentos que cumplan con esta *query*
* `near` &rarr; El punto de referencia, del que buscamos documentos cercanos
* `minDistance` &rarr; La distancia mínima a la que tiene que estar un punto (opcional)
* `maxDistance` &rarr; La distancia máxima a la que tiene que estar un punto (opcional)
* `distanceField` &rarr; La respuesta va a incluir este campo adicional, con la distancia calculada
* `distanceMultiplier` &rarr; Normalmente, la distancia calculada es en metros, y podemos multiplicar por una constante para sacar un valor más útil

Y con esto tenemos las herramientas necesarias para construir nuestra siguiente gran aplicación.
