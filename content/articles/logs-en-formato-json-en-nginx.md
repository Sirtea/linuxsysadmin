Title: Logs en formato JSON en Nginx
Slug: logs-en-formato-json-en-nginx
Date: 2017-06-06 10:00
Category: Operaciones
Tags: logs, nginx, logstash



Vimos en un artículo anterior como trabajar con herramientas para agregar los *logs* en un mismo servidor, para su consulta. Algunos formatos de *logs* necesitan complejas formas de *parseado* para que puedan servir de base para nuestra consulta, y en el caso de **logstash** nos conviene un formato **JSON** válido.

Hay muchos servicios con complejos formatos de *log*, pero suelen tener formas para cambiarlos y ahorrarnos así una tediosa expresión regular al configurar **logstash**. Este es el caso de **nginx**.

```bash
172.17.0.1 - - [10/Mar/2017:10:26:59 +0000] "GET / HTTP/1.1" 200 1966 "-" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36"
172.17.0.1 - - [10/Mar/2017:10:26:59 +0000] "GET /favicon.ico HTTP/1.1" 404 571 "http://172.17.0.2/" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36"
```

Solo por echar un vistazo en internet, vemos que hay varias opciones, siendo la que más me gusta [esta opción](https://github.com/jiaz/nginx-http-json-log). Sin embargo es un módulo de terceros y no suele venir compilado en ninguna distribución conocida.

Como no es plan ponerse a compilar, podemos encontrar una solución más fácil en [la documentación de nginx](http://nginx.org/en/docs/http/ngx_http_log_module.html), que aunque no es la más correcta, nos sirve para salir del paso.

Se trata de crear un formato de *log* personalizado, que podemos utilizar en todos nuestros sitios, y que **logstash** sabe *parsear* de serie.

Para ello vamos a modificar nuestra configuración para crear un nuevo formato de *log* llamado *logstash_json*, que debe ir obligatoriamente dentro del bloque *http* (directiva *log_format*). Luego podemos utilizar ese formato en cualquier bloque *http*, *server* o *location* que nos convenga (directiva *access_log*).

A nivel de ejemplo, os pongo a continuación una configuración muy simple, con ambas directivas:

```bash
gerard@server:~/docker/nginx$ cat nginx.conf 
worker_processes 1;
events {
	worker_connections 1024;
}
http {
	include mime.types;
	default_type application/octet-stream;
	sendfile on;
	keepalive_timeout 65;

	log_format logstash_json '{ "@timestamp": "$time_iso8601", '
        	                 '"@fields": { '
                	         '"remote_addr": "$remote_addr", '
                        	 '"remote_user": "$remote_user", '
	                         '"body_bytes_sent": "$body_bytes_sent", '
        	                 '"request_time": "$request_time", '
                	         '"status": "$status", '
                        	 '"request": "$request", '
	                         '"request_method": "$request_method", '
        	                 '"http_referrer": "$http_referer", '
                	         '"http_user_agent": "$http_user_agent" } }';
	access_log /var/log/nginx/access.log logstash_json;

	include conf.d/*;
}
gerard@server:~/docker/nginx$ 
```

Tras consultar los *logs* tras algunas consultas, vemos que sale un formato correctamente formado.

```bash
{ "@timestamp": "2017-03-10T10:38:37+00:00", "@fields": { "remote_addr": "172.17.0.1", "remote_user": "-", "body_bytes_sent": "0", "request_time": "0.000", "status": "304", "request": "GET / HTTP/1.1", "request_method": "GET", "http_referrer": "-", "http_user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36" } }
{ "@timestamp": "2017-03-10T10:38:56+00:00", "@fields": { "remote_addr": "172.17.0.1", "remote_user": "-", "body_bytes_sent": "571", "request_time": "0.000", "status": "404", "request": "GET /nonexistent HTTP/1.1", "request_method": "GET", "http_referrer": "-", "http_user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36" } }
```

Para comprobar que el formato es correcto, y ya de paso verlo más bonito, podemos utilizar cualquier herramienta para validar formato JSON. Como ya sabéis que yo soy un fan del terminal, voy a hacerlo en **python**.

```bash
gerard@server:~/docker/nginx$ echo '{ "@timestamp": "2017-03-10T10:38:37+00:00", "@fields": { "remote_addr": "172.17.0.1", "remote_user": "-", "body_bytes_sent": "0", "request_time": "0.000", "status": "304", "request": "GET / HTTP/1.1", "request_method": "GET", "http_referrer": "-", "http_user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36" } }' | python -m json.tool
{
    "@fields": {
        "body_bytes_sent": "0",
        "http_referrer": "-",
        "http_user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36",
        "remote_addr": "172.17.0.1",
        "remote_user": "-",
        "request": "GET / HTTP/1.1",
        "request_method": "GET",
        "request_time": "0.000",
        "status": "304"
    },
    "@timestamp": "2017-03-10T10:38:37+00:00"
}
gerard@server:~/docker/nginx$ 
```

Y con esto ya podemos configurar nuestro **logstash**.
