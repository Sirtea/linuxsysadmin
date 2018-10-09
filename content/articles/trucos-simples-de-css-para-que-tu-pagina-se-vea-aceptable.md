Title: Trucos simples de CSS para que tu página se vea aceptable
Slug: trucos-simples-de-css-para-que-tu-pagina-se-vea-aceptable
Date: 2018-10-16 10:00
Category: Desarrollo
Tags: CSS, básico



Todos estamos hartos de ver páginas web con distracciones por todos lados: anuncios, *popups*, menús desplegables y horribles *scripts* de *javascript*. Eso hace que el contenido no llegue al usuario final y por lo tanto, no se queden con ganas de volver. Eso no significa tener una página HTML básica.

Para aquellas páginas que estén más interesadas en ser leídas que en aportar beneficios, no se necesita nada de esto; la simplicidad en estos casos es un plus: no se necesita prácticamente nada más que títulos, párrafos e imágenes.

Todos sabemos que una página web que solo use *tags* de HTML, no es atractiva visualmente, pero está libre de distracciones completamente. Podemos ver [un ejemplo](/2018/10/trucos-simples-de-css-para-que-tu-pagina-se-vea-aceptable/css_basic_skeleton.html) de este tipo de páginas.

A partir de este esqueleto, se puede complicar el diseño tanto como queramos, hasta llegar a la ilegibilidad. Sin embargo, hay un punto medio que se puede conseguir con pocos conocimientos de CSS y, aún así, dar sensación de profesionalidad y de simpleza buscada adrede. Para los impacientes, podemos ver el resultado [aquí](/2018/10/trucos-simples-de-css-para-que-tu-pagina-se-vea-aceptable/css_basic_styled.html).

## Centrar el contenido

Lo primero que se nota es una sensación de agobio: nos faltan márgenes a ambos lados del texto. Podemos limitar el contenido a un ancho máximo, de forma que se vea espacio en las pantallas grandes, pero no se desperdicie en pantallas más pequeñas. Luego podemos dejar qu se calcule el margen de forma automática.

```CSS
body { max-width: 800px; margin: auto }
```

## Cambiar la fuente del texto

La fuente por defecto que llevan los navegadores es poco agradable a la vista; con cambiar la fuente es suficiente. Podemos poner una fuente propia, una de **Google Fonts** o simplemente usar una família para que el navegador utilize la que le venga en gana.

```CSS
body { font-family: sans-serif }
```

## Añadir un toque de color

Este punto es conflictivo; con elegancia le puede dar a la página mejor aspecto visual, pero rápidamente nos puede cegar o distraer. Personalmente opino que un color pálido le da un punto de color, sin quitarle importancia al contenido.

```CSS
body { background-color: #EFE }
```

## Subrayar los títulos

Es fácil que los títulos se camuflen entre el contenido, y por eso los queremos remarcar. El uso de `text-decoration: underline` no basta: se puede confundir con un enlace. A mí me gustan los subrayados que van de una punta a la otra de la página, y esto se puede simular con el borde inferior del título.

```CSS
h1 { border-bottom: 0.1rem #000 solid }
```

## Estilizar los párrafos

El estilo básico de los párrafos tiene, a mi parecer, dos fallos: los párrafos con "sierras" laterales me distraen y prefiero justificarlos, y el escaso espacio entre líneas los hace ilegibles. Podemos corregir ambos con reglas simples de CSS.

```CSS
p { text-align: justify; line-height: 1.5rem }
```

## Centrar las imágenes

Los elementos de imágenes son interpretados como elementos *inline*, y se pueden poner de forma consecutiva en un párrafo o título. Para mí esto no tiene sentido y evita que se puedan centrar. Las imágenes deberían estar solas, para que se lleven el protagonismo para el que las hemos puesto. Un pegote de imágenes no es bonito.

```CSS
img { display: block; margin: auto }
```

## Otros elementos

La clave para no complicar más el diseño es no estilizar aquello que no necesitemos. Sin embargo, algunos tipos de contenido pueden necesitar otros tipos de elementos HTML, como las listas, citaciones o código; seguro que váis a querer estilizar enlaces, cursivas y negritas.

El único consejo que os puedo dar es el de no recargar: quitar el subrayado o el cambio de color en un enlace es aceptable; cambiar los círculos de las listas por cuadrados es aceptable; poner puntos personalizados con imágenes propias y parpadeantes, no lo es.

**Usad la cabeza.**
