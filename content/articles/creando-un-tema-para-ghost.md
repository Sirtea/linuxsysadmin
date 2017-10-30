Title: Creando un tema para Ghost
Slug: creando-un-tema-para-ghost
Date: 2016-12-05 08:00
Category: Miscelánea
Tags: ghost, blog, tema



Ya vimos lo fácil que resulta de empezar un *blog* con **Ghost**. El tema que viene por defecto es muy simple y bastante legible, pero nos puede interesar cambiarlo, por ejemplo para poner publicidad. Existen temas de pago y gratuitos ya hechos, pero hoy voy a explicar como hacer uno.

Vamos a partir de una instalación limpia de **Ghost**, pero ejemplo como se indica en [otro artículo]({filename}/articles/ghost-un-motor-para-hacer-blogs.md). Es especialmente importante desarrollar el tema en una instancia que corra en modo *development*, así no va a *cachear* las plantillas y nos va a ahorrar reiniciar el proceso.

Es muy útil mapear la carpeta */usr/lib/ghost/* del contenedor a una carpeta local, si estamos usando **Docker**. De esta manera podemos editar el tema cómodamente en nuestro sistema de ficheros y con las herramientas con las que más cómodos nos sintamos.

```bash
gerard@aldebaran:~/workspace$ docker run -d -p 2368:2368 -v /home/gerard/workspace/content:/var/lib/ghost ghost
343d065878fb910a9f2b5b51be4a337d2e93db2e66cbff6800c2cb96a758f733
gerard@aldebaran:~/workspace$ 
```

Una vez hayamos creado el tema, nos lo podemos descargar y aplicarlo a nuestra instancia productiva, sin necesidad de reiniciar nada. A fin de cuentas, en el fichero *.zip* solo hay plantillas y ficheros de respaldo del tema.

Las plantillas están escritas en un motor de plantillas llamado [Handlebars](http://handlebarsjs.com/), y podemos encontrar un resume enfocado a **Ghost** en [la documentación](https://themes.ghost.org/docs/handlebars). Como convención, todos los ficheros *.hbs* en un tema de **Ghost** son plantillas en este lenguaje.

El uso de una instancia nueva nos viene muy bien, porque tenemos un índice y un *post*, que nos permitirán ver como evoluciona nuestro *blog*, a medida que avanzamos en el artículo.

* Índice -> <http://localhost:2368/>
* Post -> <http://localhost:2368/welcome-to-ghost/>

## Un tema vacío

Vamos a crear una carpeta local temporal con los ficheros requeridos, que luego vamos a comprimir en fichero *.zip* para poder cargarlo en la interfaz de administración. Una vez **Ghost** ya reconozca nuestro tema, no vamos a tener que reiniciar ningún proceso nunca.

De acuerdo a la [documentación de Ghost](https://themes.ghost.org/docs/structure), se necesitan un mínimo de 3 ficheros, que son el *package.json*, *index.hbs* y *post.hbs*. Podemos encontrar la descripción de cada fichero en otro apartado de [la documentación](https://themes.ghost.org/docs/templates).

Voy a poner lo justo para que se pueda cargar el tema, aunque no sea muy funcional, para ir creciendo a partir de aquí.

```bash
gerard@aldebaran:~/workspace$ tree minimal_theme/
minimal_theme/
├── index.hbs
├── package.json
└── post.hbs

0 directories, 3 files
gerard@aldebaran:~/workspace$ cat minimal_theme/package.json 
{
  "name": "minimal_theme",
  "version": "0.0.0"
}
gerard@aldebaran:~/workspace$ cat minimal_theme/index.hbs 
INDEX
gerard@aldebaran:~/workspace$ cat minimal_theme/post.hbs 
POST
gerard@aldebaran:~/workspace$ 
```

Para cargarlo cómodamente desde la interfaz web, lo necesitamos en formato *.zip*. De hecho, la carpeta contenedora tampoco nos importa, así que la podemos borrar.

```bash
gerard@aldebaran:~/workspace$ cd minimal_theme/
gerard@aldebaran:~/workspace/minimal_theme$ zip -r ../minimal_theme.zip *
  adding: index.hbs (stored 0%)
  adding: package.json (deflated 10%)
  adding: post.hbs (stored 0%)
gerard@aldebaran:~/workspace/minimal_theme$ cd ..
gerard@aldebaran:~/workspace$ rm -R minimal_theme/
gerard@aldebaran:~/workspace$ 
```

Es importante mencionar que el fichero *.zip* no debe contener la carpeta contenedora, sino sus ficheros. Para entendernos, los 3 ficheros deben quedar en la raíz del fichero comprimido.

```bash
gerard@aldebaran:~/workspace$ unzip -l minimal_theme.zip 
Archive:  minimal_theme.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
        6  2016-09-23 12:41   index.hbs
       52  2016-09-23 12:41   package.json
        5  2016-09-23 12:41   post.hbs
---------                     -------
       63                     3 files
gerard@aldebaran:~/workspace$ 
```

Lo cargamos desde la interfaz de administración, en *Settings / General / Themes / Upload a theme*. La idea es que a partir de ahora vamos a editar el tema desde la carpeta */var/lib/ghost/themes/minimal_theme/*; como yo he usado un volumen local, lo voy a editar cómodamente desde */home/gerard/workspace/content/themes/minimal_theme/*. Cuando tengamos algo digno de ser guardado, lo podemos descargar en la misma sección de la interfaz administrativa, en formato *.zip*.

En este punto, deberíamos ver una página principal con el contenido "INDEX" y la página del *post* de bienvenida como "POST", porque la plantilla no hace nada con los objetos que recibe de **Ghost**. Vamos a continuar mejorando estas plantillas en los siguientes apartados.

## Plantilla base e inyección de plantillas parciales

Las plantillas deberían sacar contenido HTML. Como ya sabemos, hay muchos elementos comunes que se van a repetir en todas las plantillas, por ejemplo, los *tags* propios de HTML, como el *&lt;html&gt;*, el *&lt;head&gt;* o el *&lt;body&gt;*.

La solución mas elegante para este problema es la herencia de plantillas. La idea es que nuestra plantilla se va a insertar en una mas general, de forma que todas tengan un esqueleto común.

También tenemos la opción de tener trozos de plantilla preparados para ser incluidos en otras plantillas, por ejemplo, la cabecera, el código de seguimiento o el contador de visitas. Estos trozos se llaman *partials* y tienen una carpeta con el mismo nombre.

Para ver como funcionan ambos, vamos a crear un esqueleto HTML. Este esqueleto va a incluir un *partial* con la cabecera del *blog*. De esta forma conseguimos separar conceptos, para que sea mas legible y mas fácil de modificar a *posteriori*.

Para ello vamos a crear nuevos ficheros, que son la plantilla base *default.hbs* y la plantilla de la cabecera en *partials/header.hbs*.

```bash
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ tree
.
├── partials
│   └── header.hbs
├── default.hbs
├── index.hbs
├── package.json
└── post.hbs

1 directory, 5 files
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ 
```

El primer paso consiste en indicar a las plantillas antes creadas que queremos que hereden de la plantilla *default*, con el símbolo `{{!< default}}`.

```bash
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ cat index.hbs 
{{!< default}}

INDEX
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ cat post.hbs 
{{!< default}}

POST
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ 
```

Lo siguiente es escribir una plantilla *default.hbs*. Esta plantilla debe contener la expresión *handlebars* `{{{body}}}`, que es donde se va a insertar la plantilla real.

```bash
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ cat default.hbs 
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <title>Title</title>
{{ghost_head}}
  </head>
  <body>
{{> header}}
{{{body}}}
{{ghost_foot}}
  </body>
</html>
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ 
```

Vamos a fijarnos en 3 expresiones nuevas, que son `{{> header}}`, `{{ghost_head}}` y `{{ghost_foot}}`. La primera sirve para insertar un *partial*, que va a ser el resultado de procesar *partials/header.hbs*. Las otras dos, aunque no son estrictamente necesarias, son recomendadas por la documentación de **Ghost**. Básicamente incluyen algunos *metatags* y cualquier *snippet* que pongamos como *Code Injection* en el panel de administración web.

Solo faltaría poner algo de código en el *partial* de la cabecera para que sea útil incluirlo. Vamos a pecar otra vez de simplicidad.

```bash
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ cat partials/header.hbs 
<h1>Title</h1>
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ 
```

**AVISO**: Si miramos el *blog* ahora, veremos que da un error 500. Esto es debido a que **Ghost** no ha cargado los nuevos ficheros. Como solución, basta con activar otro tema, y volver a activar el nuestro.

## Usando variables en las plantillas

Cada plantilla dispone de sus variables para que las usemos. Algunas de las variables están disponibles para todas las plantillas. De esta forma podemos generar contenido HTML real a partir de lo que hay en la base de datos de **Ghost**.

Vamos a empezar con el título del *blog*, visible en el *tag* `title` de la plantilla *default.hbs* y en la cabecera *partials/header.hbs*. Para poner el título real del *blog* (tal como se define en la interfaz de administración), vamos a usar la variable `{{@blog.title}}`. Podéis encontrar todas las variables disponibles en la documentación.

```bash
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ cat default.hbs 
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <title>{{@blog.title}}</title>
{{ghost_head}}
  </head>
  <body>
{{> header}}
{{{body}}}
{{ghost_foot}}
  </body>
</html>
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ cat partials/header.hbs 
<h1>{{@blog.title}}</h1>
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ 
```

Para las otras plantillas, el truco consiste en localizar que variables tenemos disponibles. Podemos encontrar el contexto para cada plantilla en la barra lateral de la configuración, en el *Context Reference*.

En el caso de la plantilla *index.hbs*, podemos mirar en [su contexto](https://themes.ghost.org/docs/index-context). De ahí se deduce que tenemos una variable *posts* que solo tenemos que iterar para listar cada uno, de la forma que mas nos guste. Siguiendo el enlace a [post object](https://themes.ghost.org/docs/post-context#post-object-attributes), podemos ver qué campos hay para dibujar en la plantilla. Vamos a utilizar el *title* y el *excerpt* (título del *post* y un resumen del mismo).

```bash
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ cat index.hbs 
{{!< default}}

{{#foreach posts}}
<h2>{{title}}</h2>
<p>{{excerpt}}</p>
{{/foreach}}
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ 
```

Simple, pero suficiente. Por brevedad, no se ha incluido ningún trato del la variable `{{pagination}}`. Si hacéis temas en el futuro, vais a tener que utilizarla.

La plantilla *post.hbs*, de similar forma, obtiene la variable *post* y un ejemplo de como iterarla. Su documentación de contexto está [aquí](https://themes.ghost.org/docs/post-context). Vamos a pintar el título del artículo y su contenido (*title* y *content* respectivamente).

```bash
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ cat post.hbs 
{{!< default}}

{{#post}}
<h2>{{title}}</h2>
{{content}}
{{/post}}      
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ 
```
Nuevamente, un ejemplo simple y breve; no soy diseñador gráfico. Pero se entiende, ¿no?

## Hojas de estilo, javascript y otros ficheros auxiliares

Cuando escribimos un tema, muchas veces necesitamos de otros ficheros, mas allá del contenido HTML. En la jerga de **Ghost** se llaman *assets* y nos ofrece una forma muy fácil de hacerlo. Tenemos un *helper* llamado *asset* que podemos usar. Un *asset* puede ser una hoja de estilo, un fichero *javascript*, una imagen, una fuente y en general, cualquier tipo de recurso.

Para demostrar como se usa, vamos a incluir una hoja de estilo en nuestro tema. Como queremos que esté disponible en todas las páginas, la podemos poner en la plantilla base. La idea es que va a ser el código HTML normal, pero en vez de dar la ruta nosotros, vamos a poner `{{asset "css/style.css"}}`.

```bash
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ cat default.hbs 
<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <title>{{@blog.title}}</title>
    <link rel="stylesheet" type="text/css" href="{{asset "css/style.css"}}" />
{{ghost_head}}
  </head>
  <body>
{{> header}}
{{{body}}}
{{ghost_foot}}
  </body>
</html>
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ 
```

Como le hemos indicado que queremos el *asset* localizado en *css/style.css*, tenemos que crear esta estructura dentro de la carpeta *assets*, que crearemos también si no la tenemos. El fichero *.css* va a ser bastante simple, para no aburrir con detalles de diseño.

```bash
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ cat assets/css/style.css 
body {
    background-color: cyan;
}
gerard@aldebaran:~/workspace/content/themes/minimal_theme$ 
```

Sinceramente espero que seáis mejores en el diseño gráfico que yo... Aunque lo importante es que si miramos el *blog*, se ha aplicado el estilo definido. Podéis añadir mas *assets* hasta que os canséis de ello.

## A partir de aquí...

Como detalle final, solo queda decir que podéis generar mas plantillas, que van a ser cargadas en el orden de preferencia, como se indica en [la documentación](https://themes.ghost.org/docs/context-overview#section-context-table). Fijaos en las columnas *URL* y *Template*.

Por ejemplo, la plantilla que se usa para la URL */tag/ghost* sería *tag-ghost.hbs*; en caso de no haber dicha plantilla, se utilizaría *tag.hbs*; en caso de fallar ambas (como es el caso de este tutorial), se utilizaría *index.hbs* (que está porque es una de las requeridas).

Ya tenéis todas las herramientas necesarias para escribir y para entender temas de **Ghost**. Con un poco de esfuerzo y ganas, os puede quedar un tema propio genial.

En este punto, me voy a la interfaz de administración, y me descargo mi tema, a modo de *backup*. Si os interesa, os lo dejo [aquí]({filename}/downloads/minimal_theme.zip).
