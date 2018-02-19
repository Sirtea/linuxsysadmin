Title: Configurando servidores con first time boot scripts
Slug: configurando-servidores-con-first-time-boot-scripts
Date: 2018-02-26 10:00
Category: Operaciones
Tags: systemd, script



Configurar servidores desde cero es una tarea muy pesada, una fuente de errores innecesaria y hace nuestros servidores difícilmente reproducibles. Los *setups* más básicos son siempre los mismos, y podemos configurar nuestros servidores para que ejecuten un *script* la primera vez que se (re)inicien, a falta de mejores herramientas.

De esta forma, podemos disponer fácilmente de un servidor de un tipo predefinido, especialmente en aquellos *hostings* que nos permitan *scripts* de inicialización, como por ejemplo, [Vultr](https://www.vultr.com/?ref=7251515).

El truco consiste en hacer que nuestro sistema de *init* ejecute nuestro *script*, solamente en el caso de que no se haya ejecutado ya. Para ello podemos usar el mismo fichero de *log* de la ejecución efectuada.


## Un ejemplo con systemd

De acuerdo a la documentación de **systemd**, existe un fichero que se ejecuta en cada *boot*, suponiendo que exista y que tenga los permisos adecuados. Se trata de */etc/rc.local*. Nos bastaría con crearlo y asignarle permisos de ejecución, y tendríamos el *script* ejecutándose en cada *boot*.

### El lanzador

Con un poco de lógica, podemos hacer lo sugerido: un *script* que ejecute algo y genere el *log* para que no se vuelva a ejecutar de nuevo. Sin embargo, parece adecuado disponer de un *framework* que separe la lógica de ejecución, del *script* ejecutado.

Esto nos permite distribuir nuestras imágenes base con el *script* y dejar al usuario la opción de poner o no un *script* de inicialización, y de que poner en él. Así pues, un posible ejemplo sería este:

```bash
root@firstboot:~# cat /etc/rc.local
#!/bin/sh

SCRIPT=/root/firstboot.sh
LOG=/root/firstboot.log

if [ -x "${SCRIPT}" ]; then
    if [ ! -e "${LOG}" ]; then
        ${SCRIPT} >${LOG} 2>&1
    fi
fi
root@firstboot:~#
```

Básicamente, preguntamos si el *script* existe y es ejecutable, y en ese caso, si no existe el log previamente generado. En caso afirmativo, ejecutamos el script y recogemos la salida, a modo de *log* y a modo de marca para no volver a lanzarlo.

Solo nos queda pendiente darle permisos de ejecución, porque sino, **systemd** lo ignoraría.

```bash
root@firstboot:~# chmod a+x /etc/rc.local
root@firstboot:~#
```

### Usando la plantilla

Hemos llegado a ese momento en el que clonamos la plantilla y tenemos que poner el *script* de inicialización. Siguiendo el *script* arriba mencionado, solo tenemos que poner un *script* que haga lo que nos interese. En este caso, con un *log* para ver que funciona, nos vale.

```bash
root@firstboot:~# cat firstboot.sh
#!/bin/bash

echo "First time boot. Running as:"
id
root@firstboot:~#
```

No os olvidéis de darle permisos de ejecución:

```bash
root@firstboot:~# chmod a+x firstboot.sh
root@firstboot:~#
```

Si reiniciamos el servidor podremos ver la magia: como hay un script y no hay *log*, se va a ejecutar, generando el *log*. Solo nos queda verlo en directo:

```bash
root@firstboot:~# cat firstboot.log
First time boot. Running as:
uid=0(root) gid=0(root) grupos=0(root)
root@firstboot:~#
```

Y por mucho que reiniciéis, no se va a volver a ejecutar, a menos claro, que eliminéis el fichero de *log*, dejando el *script* en su sitio.

### Uso práctico

En mi caso concreto, he creado *scripts* genéricos para instalar:

* Un servidor de **mongodb**
* Un servidor **uwsgi**
* Un frontal **nginx**
* Un balanceador **haproxy**

Así pues, cuando creo un proyecto nuevo, solo tengo que asignar los *script* correspondientes a cada instancia de mi *hosting*. Con algunas modificaciones a los ficheros de configuración y la aplicación propiamente dicha, tengo un entorno corriendo en tiempo record.
