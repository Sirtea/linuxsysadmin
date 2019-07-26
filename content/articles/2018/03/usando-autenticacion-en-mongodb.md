---
title: "Usando autenticación en MongoDB"
slug: "usando-autenticacion-en-mongodb"
date: 2018-03-26
categories: ['Sistemas']
tags: ['mongodb', 'autenticación']
---

Usar autenticación en las bases de datos de nuestros entornos, por muy privados que sean, suele ser una buena idea. Nos sirve para separar los accesos a un servicio compartido y evitar sobreescrituras cuando accidentalmente dos servicios usan la misma base de datos por un error de algún usuario despistado.<!--more-->

No es la primera vez que un *cluster* compartido entre varios proyectos acaba con la destrucción de datos accidental; el uso habitual de *copy-paste* en nuestros *docker-compose.yml* o en otros ficheros de configuración, nos plantea un posible riesgo cuando alguien se olvida de cambiar el nombre de la base de datos.

Estos casos son fácilmente evitables si las plantillas contienen unos parámetros de **usuario** y **password** no usables, y solamente la correcta combinación de ambos con la base de datos dan acceso a los datos. De esta forma, las diferentes bases de datos serian accesibles por diferentes usuarios y haría falta conocer todos los datos de acceso para usar la base de datos de otra aplicación.

## Preparación

En **MongoDB**, los usuarios pertenecen a una base de datos, y no son globales. Esto significa que tenemos que crearlos en una base de datos concreta y que cualquiera que quiera autenticarse debe hacerlo contra la base de datos que contenga su usuario. La autorización en sí garantiza mediante la aplicación de diferentes *roles*, a nivel de base de datos o a nivel global.

Como decisión de diseño, vamos a poner todos los usuarios en la misma base de datos, que va a ser *admin*. Para ello necesitamos abrir un cliente a la base de datos, que por simplicidad va a ser el *shell* básico, binario `mongo`.

### Crear un usuario de administración

Se trata simplemente de crear un usuario, con el *role* suficiente para hacer las tareas necesarias. Como se trata de un usuario muy exclusivo, le voy a dar el *role root*, que básicamente me lo permite hacer todo. Podéis adaptar vuestro comando eligiendo el *role* que más os convenga, según [la documentación](https://docs.mongodb.com/manual/reference/built-in-roles/#built-in-roles).
```
> use admin
switched to db admin
> db.createUser(
...   {
...     user: "admin",
...     pwd: "s3cr3t",
...     roles: [ { role: "root", db: "admin" } ]
...   }
... )
Successfully added user: {
        "user" : "admin",
        "roles" : [
                {
                        "role" : "root",
                        "db" : "admin"
                }
        ]
}
>
```

**TRUCO**: Aunque el *role root* permite actuar en todas las bases de datos, hay que indicarle una cualquiera para que la especificación JSON sea correcta.

### Activar la autenticación

Lo único necesario para que **MongoDB** requiera autenticación es un parámetro de configuración, sea:

* El *flag* `--auth` cuando levantamos el servidor
* El parámetro de configuración `security.authorization: enabled` en el fichero de configuración

Hay que reiniciar el proceso para que use este nuevo parámetro, tanto para activarlo como para desactivarlo. A partir de este punto, todas las operaciones a la base de datos, van a necesitar que la sesión esté autenticada, y que dicho usuario tenga el *role* necesario para hacer lo que pide.

**TRUCO**: Hay una [excepción de localhost](https://docs.mongodb.com/manual/core/security-users/#localhost-exception); si no hay ningún usuario en la base de datos y nos conectamos a ella desde *localhost*, no va a ser necesaria ninguna autenticación. Usando esta excepción podemos levantar el servicio siempre con `--auth` o `security.authorization` y crear el superusuario *a posteriori*, sin reiniciar nada.

## Uso

Ha llegado el momento de poner una aplicación nueva que use nuestro servicio de **MongoDB**. Esa aplicación necesita su propio espacio de datos, lo que significa que necesita:

* Una base de datos propia, que **MongoDB** creará automáticamente cuando haga falta
* Un usuario con acceso a esa base de datos (y a ninguna más)

### Añadir un usuario nuevo

Otra vez nos limitamos a crear un usuario, pero esta vez le vamos a dar el *role readWrite* sobre su base de datos. Abrimos una sesión en el *mongo shell*, autenticándonos en la base de datos *admin* con un usuario con capacidad de crear usuarios, por ejemplo el que creamos antes: **admin**.

```
> use admin
switched to db admin
> db.auth("admin", "s3cr3t")
1
> db.createUser(
...   {
...     user: "myapp",
...     pwd: "myapp1234",
...     roles: [ { role: "readWrite", db: "myapp" } ]
...   }
... )
Successfully added user: {
        "user" : "myapp",
        "roles" : [
                {
                        "role" : "readWrite",
                        "db" : "myapp"
                }
        ]
}
>
```

Y con esto es suficiente, puesto que la base de datos se crea automáticamente cuando tenga alguna colección. En este caso, el usuario y la base de datos coinciden; esto es otra decisión de diseño.

### Configuración de la aplicación

Cada cliente de **MongoDB** tiene sus propias formas para autenticarse; podemos ver el uso de la función `db.auth()` por parte del *mongo shell*, en el ejemplo anterior. La documentación es extensa en este punto.

Lo importante es que la autenticación se hace con el usuario y contraseña proporcionados, **en la base de datos _admin_**. El uso regular de la base de datos se hace **en la base de datos de la aplicación**.

Todas las librerías tienen una forma común muy cómoda para indicar la base de datos destino: la [URL de mongodb](https://docs.mongodb.com/manual/reference/connection-string/). En ellas se nos permite especificar la base de datos de uso y la de autenticación (parámetro `authSource`), así como el usuario y la contraseña.

Para el ejemplo anterior, la URL quedaría así, suponiendo que el servicio está en el *host* **mongo**: `mongodb://myapp:myapp1234@mongo:27017/myapp?authSource=admin`
