Title: Deshaciéndome del historial de comandos en Bash
Slug: deshaciendome-del-historial-de-comandos-en-bash
Date: 2018-08-27 10:00
Category: Operaciones
Tags: bash, histfile



Muchas veces me pregunto para qué necesito guardar un histórico de comandos en mis sesiones de **bash**. Como no soy nada repetitivo con los comandos que uso, solo se trata de basura acumulándose en `~/.bash_history`, y un riesgo innecesario de que otros usuarios puedan chafardear los comandos que voy utilizando.

¿Pero como funciona el mecanismo de *history* en **bash**?

1. Cuando inicias sesión en **bash**, se lee la lista del historial de comandos desde el fichero `~/.bash_history`. Concretamente el fichero es el que indica el parámetro del *shell* `HISTFILE`.
2. Cada vez que escribes un comando, la lista en memoria se actualiza con el nuevo comando, quedando limitado por el parámetro de *shell* `HISTSIZE`.
3. Al salir de la sesión, las últimas `HISTFILESIZE` líneas de la historia se escriben en `HISTFILE`, para su uso en sesiones posteriores.

## Eliminar el historial de comandos

Con esto en mente podemos hacer algunas modificaciones en los parámetros del *shell* mediante el comando `set` que puede tener consecuencias en el comportamiento del historial de comandos:

* Hacer un `unset` de `HISTFILE` va a causar que el histórico no se guarde en ningún fichero.
* Hacer un `set` de `HISTSIZE` a un valor dado, nos va a limitar los comandos recordados en la sesión de **bash** actual.
* Hacer un `set` de `HISTFILESIZE` a un valor dado, va a limitar el número de comandos que se recuerden entre sesiones.

Considero interesante que los comandos se recuerden en esta sesión, pero no quiero que se guarden entre sesiones. En estos casos podemos limitar a 0 el valor de `HISTFILESIZE`, con lo que el fichero `.bash_history` quedaría vacío; otra opción es hacer un `unset` de `HISTFILE` para que el fichero no se guarde, y por lo tanto lo podamos eliminar sin que se recree.

Para hacer estos `set` y `unset` permanentes, voy a utilizar el fichero `.bashrc`, que nos permite ejecutarlos automáticamente en cada incio de sesión de **bash**.

```bash
gerard@server:~$ tail -1 .bashrc
unset HISTFILE
gerard@server:~$ . .bashrc
gerard@server:~$ rm .bash_history
gerard@server:~$
```

Y con esto no vamos a volver a ver el molesto fichero, aunque mantenemos el historial de la sesión actual, que por defecto en **Debian** se indica en el mismo fichero:

```bash
gerard@server:~$ cat .bashrc
...
# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=1000
HISTFILESIZE=2000
...
unset HISTFILE
gerard@server:~$
```

En este caso recordaríamos un máximo de 1000 comandos durante la sesión, pero no entre sesiones.

## Otros shells

Ya hemos visto como se puede hacer con **bash**, pero no siempre tenemos un *shell* tan configurable; yo mismo utilizo mucho **Alpine Linux** y su *shell* no admite estas variables.

Si os pasa esto, tenéis dos opciones:

* Quitar todos los permisos de escritura en el fichero, para que la lista no se pueda escribir en el mismo (con lo que se perdería entre sesiones)
* Sustituir el fichero `.ash_history` o similar por un *soft link* a `/dev/null`; esto hará que no se escriba nada y, si se lee, devolverá 0 bytes (interpretado como 0 comandos).
