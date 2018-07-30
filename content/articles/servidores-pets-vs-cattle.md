Title: Servidores "pets vs cattle"
Slug: servidores-pets-vs-cattle
Date: 2018-08-06 09:00
Category: Miscelánea
Tags: pets vs cattle



Es muy divertido ir a una reunión con gente de negocio y decir algo como "tratamos los servidores como ganado". La cara que suelen poner es épica, en parte porque no conocen lo que eso significa, y en parte porque asocian ese término en otros ámbitos, como el ámbito ganadero.

En el paradigma *legacy* de tratar a los servidores, cuando un servidor se estropeaba o hacía cosas raras, todos teníamos que correr; se hacía lo imposible para restablecer ese mismo servidor. Hoy en día las cosas cambian: es más fácil crear un servidor nuevo y tenerlo listo de forma automatizada.

## Pets vs cattle (mascotas vs ganado)

**Randy Bias** narra la historia del término afirmando que probablemente se originó en 2011 o 2012, cuando **Bill Baker** utilizó la analogía para describir las estrategias arquitectónicas de "escalado vertical" frente a "escalado horizontal". **Bias** adoptó esta analogía en sus patrones arquitectónicos en la nube:

> In the old way of doing things, we treat our servers like pets, for example Bob the mail server. If Bob goes down, it’s all hands on deck. The CEO can’t get his email and it’s the end of the world. In the new way, servers are numbered, like cattle in a herd. For example, www001 to www100. When one server goes down, it’s taken out back, shot, and replaced on the line.

![Pets vs cattle]({filename}/images/pets_vs_cattle.jpg)

## ¿Pero que son exactamente "mascotas" y "ganado"?

En el mundo actual, no nos importan demasiado los servidores; no es importante que funcione un servidor, sino dar servicio. Queremos algo como "4 instancias de la API" o "2 servidores con mi tienda online".

De hecho, algunos servicios *cloud* van tan lejos como vender *serverless* o *function as a service*, en donde no hay servidores, sino código. Con que se garantize que tu código se ejecute, basta; no nos importa donde, solo que se haga.

Esto nos permite poner más valor a nuestro servicio y menos preocupaciones respecto a la infraestructura donde se ejecuta, lo que suele traducirse en un coste más acotado; podemos prescindir de operadores en favor de más desarrolladores o QAs.

### Pets (mascotas)

Se trata de servidores que son irremplazables; si se estropea, corremos todos, y hay que restaurar el servicio *in-situ*. En palabras de **Bias**, sería algo así:

> Servers or server pairs that are treated as indispensable or unique systems that can never be down. Typically they are manually built, managed, and “hand fed”. Examples include mainframes, solitary servers, HA loadbalancers/firewalls (active/active or active/passive), database systems designed as master/slave (active/passive), and so on.

### Cattle (ganado)

Son servidores que son fácilmente reemplazables; normalmente su pérdida importa poco y podemos reemplazarlos provisionando uno nuevo, normalmente de forma automatizada.

> Arrays of more than two servers, that are built using automated tools, and are designed for failure, where no one, two, or even three servers are irreplaceable. Typically, during failure events no human intervention is required as the array exhibits attributes of “routing around failures” by restarting failed servers or replicating data through strategies like triple replication or erasure coding. Examples include web server arrays, multi-master datastores such as Cassandra clusters, multiple racks of gear put together in clusters, and just about anything that is load-balanced and multi-master.

***¿Son tus servidores mascotas o ganado?***
