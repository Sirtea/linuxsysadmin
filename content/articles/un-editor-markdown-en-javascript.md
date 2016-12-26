Title: Un editor Markdown en javascript
Slug: un-editor-markdown-en-javascript
Date: 2017-01-02 12:00
Category: Miscelánea
Tags: editor, markdown, javascript



Cuando utilizas el lenguaje **markdown** de forma casi diaria, es muy probable que tengas editores dedicados para tal tarea. Sin embargo, es muy probable que la idea a escribir nos venga mientras estamos utilizando un ordenador distinto del habitual, en el que es posible que no tengamos nuestro editor favorito.

Aunque la sintaxis de **markdown** es tan simple que no se necesita un editor particular, podemos salir del paso con un editor web, de los que existen cientos. Luego podemos transferirnos el resultado usando un servicio en la nube o directamente enviándolo por *email*.

Si queremos crear un formulario para integrar en una aplicación web, podemos utilizar un complemento *javascript* que nos va a convertir un *textarea* de HTML en un editor magnífico. Este editor se llama [SimpleMDE](https://simplemde.com/).

La misma página web oficial incluye una demostración que nos da una idea de como se vería nuestro editor. Para simplificar este ejemplo, pongo un código HTML mínimo con el esqueleto de la página, con algunos complementos auxiliares activados, así como de la *feature* de iluminación de sintaxis.

```html
<!DOCTYPE html>

<html>

<head>
	<meta charset=utf-8 />
	<title>Markdown editor</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/highlight.js/latest/styles/github.min.css">
    <script src="https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.js"></script>
    <script src="https://cdn.jsdelivr.net/highlight.js/latest/highlight.min.js"></script>
</head>

<body>
    <div style="width: 80%; margin: auto;">
        <h1>Markdown editor</h1>
        <textarea></textarea>
        <script>
            var simplemde = new SimpleMDE({
                renderingConfig: {
                    codeSyntaxHighlighting: true,
                },
                showIcons: ["code", "table"],
            });
        </script>
    </div>
</body>

</html>
```

Por supuesto, los archivos *.css* y los *.js* se pueden servir localmente, previa descarga, si la situación lo hiciera necesario o recomendable.

Os pongo una imagen para ver como queda; posiblemente acabe integrado en un proyecto futuro.

![Editor SimpleMDE]({filename}/images/editor_simpleMDE.jpg)
