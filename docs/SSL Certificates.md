### Haemosphere Version 5 Documenation

SSL Configuration
-------------
The SSL Configuration allows the application to be loaded safely on the browser. The SSL Certificates must be loaded to the NGINX Server configuration. To allow other users to access the instance, add the public key of the user to the authorized_keys in the instance. Once the instance is created, no new pairs of keys could be added to the NECTAR's dasboard and so all the new keys have to be added to the instance via the authorized keys.

To access the authorized keys, 

`cd ~/.ssh`

and then `vi authorized_keys` and add the new public key at the end of the file. That will help provide access to the instance.

#####Install Certbot (which is the Lets Encrypt Client)

`sudo yum install certbot `

`install python-certbot-nginx`

#####Obtain SSL Certificates

`certbot -d prod.haemosphere.org -d www.prod.haemosphere.org --manual --preferred-challenges dns certonly`

After performing this step, one will be prompted to verify the domain. At this stage, reach out to Helpdesk (Tim Ryan [ryan.t@wehi.edu.au]) and request to add the record to the domain DNS and after receiving confirmation, wait for 30 minutes for the DNS propagation. Then, press confirm and your certificates will be issued.

Certificate is saved at: `/etc/letsencrypt/live/prod.haemosphere.org/fullchain.pem`
Key is saved at:     `/etc/letsencrypt/live/prod.haemosphere.org/privkey.pem`

#####Configure NGINX Server

The process ends by configuring the new certificates in the NGINX Configuration.

`cd /etc/nginx/sites-enabled/`

`vi myapp.conf`

Here is a sample configuration file for prod server:

```javascript
upstream myapp-site {
    server 127.0.0.1:5000;
    keepalive 500;
}

server {
    listen 80;
    server_name www.prod.haemosphere.org prod.haemosphere.org
    # optional ssl configuration

    listen [::]:443 ssl;
   # ssl_certificate /path/to/ssl/pem_file;
   #  ssl_certificate_key /path/to/ssl/certificate_key;

    # end of optional ssl configuration
    ssl_certificate /etc/letsencrypt/live/haemosphere.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/haemosphere.org/privkey.pem;
   # server_name  example.com;
   #   server_name  localhost;
   server_name _;

  #  access_log  /home/example/env/access.log;

    location / {
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host 127.0.0.1:5000;
        proxy_set_header X-Forwarded-Port 5000;

        client_max_body_size    10m;
        client_body_buffer_size 128k;
        proxy_connect_timeout   60s;
        proxy_send_timeout      90s;
        proxy_read_timeout      90s;
        proxy_buffering         off;
        proxy_temp_file_write_size 64k;
        proxy_pass http://127.0.0.1:5000;
        proxy_redirect          off;
    }
}
```

Here is the nginx configuration file:

`vi nginx.conf`

```javascript
# For more information on configuration, see:
#   * Official English Documentation: http://nginx.org/en/docs/
#   * Official Russian Documentation: http://nginx.org/ru/docs/

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

# Load dynamic modules. See /usr/share/doc/nginx/README.dynamic.
include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  /var/log/nginx/access.log  main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 2048;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # Load modular configuration files from the /etc/nginx/conf.d directory.
    # See http://nginx.org/en/docs/ngx_core_module.html#include
    # for more information.
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;

    server {
        listen       80 default_server;
        listen       [::]:80 default_server;
        server_name  www.prod.haemosphere.org prod.haemosphere.org;
        root         /usr/share/nginx/html;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

        ssl_certificate /etc/letsencrypt/live/haemosphere.org/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/haemosphere.org/privkey.pem;

        location / {
        proxy_pass http://127.0.0.1:5000 ;
        }

        error_page 404 /404.html;
            location = /40x.html {
        }

        error_page 500 502 503 504 /50x.html;
            location = /50x.html {
        }
    }
	# Settings for a TLS enabled server.
#
#    server {
#        listen       443 ssl http2 default_server;
#        listen       [::]:443 ssl http2 default_server;
#        server_name  _;
#        root         /usr/share/nginx/html;
#
#        ssl_certificate "/etc/pki/nginx/server.crt";
#        ssl_certificate_key "/etc/pki/nginx/private/server.key";
#        ssl_session_cache shared:SSL:1m;
#        ssl_session_timeout  10m;
#        ssl_ciphers PROFILE=SYSTEM;
#        ssl_prefer_server_ciphers on;
#
#        # Load configuration files for the default server block.
#        include /etc/nginx/default.d/*.conf;
#
#        location / {
#        }
#
#        error_page 404 /404.html;
#            location = /40x.html {
#        }
#
#        error_page 500 502 503 504 /50x.html;
#            location = /50x.html {
#        }
#    }


server {
        listen       443 ssl;
        listen [::]:443 ssl ipv6only=on; # managed by Certbot
        server_name  www.prod.haemosphere.org prod.haemosphere.org;
        root         /usr/share/nginx/html;

        # Load configuration files for the default server block.
        include /etc/nginx/default.d/*.conf;

        ssl_certificate /etc/letsencrypt/live/prod.haemosphere.org/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/prod.haemosphere.org/privkey.pem;

        location / {
        proxy_pass http://127.0.0.1:5000 ;
        }

        error_page 404 /404.html;
            location = /40x.html {
        }

        error_page 500 502 503 504 /50x.html;
            location = /50x.html {
        }
    }


}
```