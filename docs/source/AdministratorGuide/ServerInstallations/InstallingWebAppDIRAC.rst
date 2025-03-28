.. _installwebappdirac:

=======================
Installing WebAppDIRAC
=======================

The first section describes the install procedure of the web framework. The configuration of the web app will be presented in the next sections.
While not mandatory, NGINX (nginx.com) can be used to improve the performance of the web framework.
The installation and configuration of NGINX will be presented in the last section.


Requirements
------------

Please follow the :ref:`server_requirements` instructions to setup the machine. In principle there is no magic to install the web portal. It has to be installed as another DIRAC component.
When the machine is ready you can start to install of the web portal. But before that you need the install_site.sh script and a minimal configuration file.

Getting the install script
~~~~~~~~~~~~~~~~~~~~~~~~~~
You can find the instructions for getting the install_site.sh  script at the end of the :ref:`server_requirements` section.

Configuration file
~~~~~~~~~~~~~~~~~~
You can use a standard configuration file, for example from the :ref:`install_primary_server`. Please make sure that the following lines are present in the
configuration file::

  Extensions = WebApp
  WebApp = yes

Installation configuration::

  LocalInstallation
  {
    #  These are options for the installation of the DIRAC software
    #
    #  DIRAC release version (this is an example, you should find out the current
    #  production release)
    Release = v7r2p8
    #  To install the Server version of DIRAC (the default is client)
    InstallType = server
    #  If this flag is set to yes, each DIRAC update will be installed
    #  in a separate directory, not overriding the previous ones
    UseVersionsDir = yes
    #  The directory of the DIRAC software installation
    TargetPath = /opt/dirac
    #  DIRAC extension to be installed
    # (WebApp is required if you are installing the Portal on this server).
    #  Only modules not defined as default to install in their projects need to be defined here:
    #   i.e. LHCb, LHCbWeb for LHCb for example: Extensions = WebAppDIRAC,LHCb,LHCbWeb
    Extensions = WebApp
    Project = DIRAC
    WebPortal = yes
    WebApp = yes
    # Note: This service is only needed, if does not exist on the machine used to install the WebApp
    Services = Framework/SystemAdministrator
    UseServerCertificate = yes
    SkipCADownload = yes
    Setup = your setup # for example: LHCb-Certification
    ConfigurationMaster = no
    ConfigurationServer = your configuration service
  }


Before you start the installation please make sure that you have the host certificate in the /opt/dirac/etc directory.
More info in the Server Certificates section in :ref:`server_requirements`.

Create the configuration file and copy the lines above the this file::

  vim /home/dirac/DIRAC/install.cfg

Download and run the installation script (use -v key for specifying a version, look at the help output)::

  cd /home/dirac/DIRAC
  curl -O https://raw.githubusercontent.com/DIRACGrid/management/master/install_site.sh
  chmod +x install_site.sh
  ./install_site.sh install.cfg
  source /opt/dirac/bashrc

Note: If you do not have the /home/dirac/DIRAC directory, please have a look the instructions given in the :ref:`server_requirements` section.


Checks to be done after the installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the installation is successful, you will see the following lines::

  Status of installed components:

    Name                          Runit Uptime PID
  ====================================================
  1 Web_WebApp                    Run   6      19887
  2 Framework_SystemAdministrator Run   2      19941

Make sure that the portal is listening in the correct port.

Without NGinx::

  tail -200f /opt/dirac/runit/Web/WebApp/log/current

  2016-06-02 12:44:18 UTC WebApp/Web   INFO: Configuring in developer mode...
  2016-06-02 12:44:18 UTC WebApp/Web NOTICE: Configuring HTTP on port 8080
  2016-06-02 12:44:18 UTC WebApp/Web NOTICE: Configuring HTTPS on port 8443
  2016-06-02 12:44:19 UTC WebApp/Web ALWAYS: Listening on https://0.0.0.0:8443/DIRAC/ and http://0.0.0.0:8080/DIRAC/

Using Nginx::

  tail -200f /opt/dirac/runit/Web/WebApp/log/current

  2016-06-02 12:35:46 UTC WebApp/Web NOTICE: Configuring HTTP on port 8000
  2016-06-02 12:35:46 UTC WebApp/Web ALWAYS: Listening on http://0.0.0.0:8000/DIRAC/

If you are not using NGINX and the web server is listening on 8000, please edit configuration to add /WebApp/Balancer=None.
Make sure that the configuration /opt/dirac/pro/etc/dirac.cfg file is correct. It contains Extensions=WebApp. For example::

  DIRAC
  {
    Setup = LHCb-Certification
    Configuration
    {
      Servers =
    }
    Security
    {
    }
    Extensions = WebApp
    Setups
    {
      LHCb-Certification
      {
        Configuration = LHCb-Certification
        Framework = LHCb-Certification
      }
    }
  }

Update using :ref:`dirac-admin-sysadmin-cli <dirac-admin-sysadmin-cli>`.


Web configuration
-----------------

To configure the web framework use **WebApp** configuration section. It also contains the schema of the menu under Schema section, which is used by the users.
Section has the following structure::

  WebApp
  {
    # Set if need to use balancer, [nginx] in case you have installed nginx
    Balancer = None
    #NumProcesses = 1

    # [PROTOCOL_SSLv2, PROTOCOL_SSLv23, PROTOCOL_SSLv3, PROTOCOL_TLSv1] in case you do not want to use the default protocol
    #SSLProtocol = ""

    # Theme of the web portal: [tabs] or [desktop]
    Theme = tabs

    Schema
    {
      Help = link|http://dirac.readthedocs.io/en/latest/UserGuide/index.html
      Tools
      {
        Application Wizard = DIRAC.ApplicationWizard
        Job Launchpad = DIRAC.JobLaunchpad
        Notepad = DIRAC.Notepad
        Proxy Upload = DIRAC.ProxyUpload
      }
      Applications
      {
        Accounting = DIRAC.Accounting
        Activity Monitor = DIRAC.ActivityMonitor
        Component History = DIRAC.ComponentHistory
        Configuration Manager = DIRAC.ConfigurationManager
        Downtimes = DIRAC.Downtimes
        File Catalog = DIRAC.FileCatalog
        Job Monitor = DIRAC.JobMonitor
        Job Summary = DIRAC.JobSummary
        Pilot Monitor = DIRAC.PilotMonitor
        Pilot Summary = DIRAC.PilotSummary
        Proxy Manager = DIRAC.ProxyManager
        Public State Manager = DIRAC.PublicStateManager
        Registry Manager = DIRAC.RegistryManager
        Request Monitor = DIRAC.RequestMonitor
        Resource Summary = DIRAC.ResourceSummary
        Site Summary = DIRAC.SiteSummary
        Space Occupancy = DIRAC.SpaceOccupancy
        System Administration = DIRAC.SystemAdministration
        Transformation Monitor = DIRAC.TransformationMonitor
        #ExampleApp = DIRAC.ExampleApp
      }
      DIRAC = link|http://diracgrid.org
    }
  }


Define external links::

  Web
  {
    Lemon Host Monitor
    {
      volhcb01 = link|https://lemonweb.cern.ch/lemon-web/info.php?entity=lbvobox01&detailed=yes
    }
  }

The example of the configuration which provided by the developer present in /opt/dirac/pro/WebAppDIRAC/WebApp/web.cfg location.

Note: To use the web portal, please fill in the configuration, namely the WebApp section, according to the example above.


Running multiple web instances
------------------------------

If you want to run more than one instance, you have to use NGIX. The configuration of NGINX is described in the next section.

You can define the number of processes in the configuration::

  # the number of instances, you want to run (by default the NumProcesses is 1). The processes will listen on 8000, 8001, ... 800n.
  NumProcesses = 4
  Balancer = nginx

You can check the number of instances in the log file (runit/Web/WebApp/log/current)::

  2018-05-09 13:48:28 UTC WebApp/Web NOTICE: Configuring HTTP on port 8000
  2018-05-09 13:48:28 UTC WebApp/Web NOTICE: Configuring HTTP on port 8001
  2018-05-09 13:48:28 UTC WebApp/Web NOTICE: Configuring HTTP on port 8002
  2018-05-09 13:48:28 UTC WebApp/Web NOTICE: Configuring HTTP on port 8003
  2018-05-09 13:48:28 UTC WebApp/Web ALWAYS: Listening on http://0.0.0.0:8002/DIRAC/
  2018-05-09 13:48:28 UTC WebApp/Web ALWAYS: Listening on http://0.0.0.0:8000/DIRAC/
  2018-05-09 13:48:28 UTC WebApp/Web ALWAYS: Listening on http://0.0.0.0:8001/DIRAC/
  2018-05-09 13:48:28 UTC WebApp/Web ALWAYS: Listening on http://0.0.0.0:8003/DIRAC/

You have to configure NGINX to forward the requests to that ports::

  upstream tornadoserver {
    # One for every tornado instance you're running that you want to balance
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
  }

Note: you can run NGINX in a separate machine.


Install NGINX
-------------

Note: you can run NGINX in a separate machine.

The official site of NGINX is the following: `<http://nginx.org/>`_
The required NGINX version has to be grater than 1.4.

Install Nginx using your package manager of your operating system. At this point, you should be able to install the pre-built Nginx package with dynamic module support::

  yum update -y
  yum install nginx -y
  systemctl enable nginx
  systemctl start nginx

If it is successful installed::

  Verifying: nginx-1.16.1-1.el6.ngx.x86_64                                                                                                                                                                                                                    1/1
  Installed:
    nginx.x86_64 0:1.16.1-1.el6.ngx

.. _configure_nginx:

Configure NGINX
~~~~~~~~~~~~~~~

You have to find the nginx.conf file. You can see which configuration is used in /etc/init.d/nginx. For example::

  vim /etc/nginx/nginx.conf

Make sure there is a line 'include /etc/nginx/conf.d/\*.conf;', then create a site.conf under /etc/nginx/conf.d/. Example content of the site.conf (please modify it for your own installation!)::

  upstream tornadoserver {
    # One for every tornado instance you're running that you want to balance
    server 127.0.0.1:8000;
  }

  server {
    # Use always HTTPS
    listen 80 default_server;
    listen [::]:80 default_server;
    # Your server name if you have weird network config. Otherwise leave commented
    #server_name your.server.domain;
    return 301 https://$server_name$request_uri;
  }

  server {
    # Enabling HTTP/2
    listen 443 ssl http2 default_server;      # For IPv4
    listen [::]:443 ssl http2 default_server; # For IPv6
    server_name your.server.domain;           # Server domain name

    ssl_prefer_server_ciphers On;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+3DES:!aNULL:!MD5:!DSS;

    # Certs that will be shown to the user connecting to the web.
    # Preferably NOT grid certs. Use something that the user cert will not complain about
    ssl_certificate     /opt/dirac/etc/grid-security/hostcert.pem;
    ssl_certificate_key /opt/dirac/etc/grid-security/hostkey.pem;

    ssl_session_tickets off;

    # Diffie-Hellman parameter for DHE ciphersuites, recommended 2048 bits
    # Generate your DH parameters with OpenSSL:
    # ~ cd /etc/nginx/ssl
    # ~ openssl dhparam -out dhparam.pem 4096
    ssl_dhparam /etc/nginx/ssl/dhparam.pem;

    # HSTS (ngx_http_headers_module is required) (15768000 seconds = 6 months)
    add_header Strict-Transport-Security max-age=15768000;

    # To secure NGINX from Click-jacking attack
    add_header X-Frame-Options SAMEORIGIN always;

    # OCSP Stapling --- fetch OCSP records from URL in ssl_certificate and cache them
    ssl_stapling on;
    ssl_stapling_verify on;

    # verify chain of trust of OCSP response using Root CA and Intermediate certs
    #ssl_trusted_certificate /path/to/root_CA_cert_plus_intermediates;

    # DNS resolver for stapling so that the resolver defaults to Google’s DNS
    resolver 8.8.4.4 8.8.8.8;

    ssl_client_certificate /opt/dirac/pro/etc/grid-security/cas.pem;
    # ssl_crl /opt/dirac/pro/etc/grid-security/allRevokedCerts.pem;
    ssl_verify_client optional;
    ssl_verify_depth 10;
    ssl_session_cache shared:SSL:10m;

    root /opt/dirac/pro;

    location ~ ^/[a-zA-Z]+/(s:.*/g:.*/)?static/(.+\.(jpg|jpeg|gif|png|bmp|ico|pdf))$ {
      alias /opt/dirac/webRoot/resources/;
      # Add one more for every static path. For instance for LHCbWebDIRAC:
      # try_files LHCbWebDIRAC/$2 WebAppDIRAC/$2 /;
      try_files WebAppDIRAC/$2 DIRACWebAppResources/$2 /;
      # Prior to v7r3 this should be slightly different:
      #   alias /opt/dirac/pro/;
      #   try_files WebAppDIRAC/WebApp/static/$2 /;
      # The new-style is mandatory for Python 3 based installations/
      expires 10d;
      gzip_static on;
      gzip_disable "MSIE [1-6]\.";
      add_header Cache-Control public;
      break;
    }

    location ~ ^/[a-zA-Z]+/(s:.*/g:.*/)?static/(.+)$ {
      alias /opt/dirac/webRoot/resources/;
      # Add one more for every static path. For instance for LHCbWebDIRAC:
      # try_files LHCbWebDIRAC/$2 WebAppDIRAC/$2 /;
      try_files WebAppDIRAC/$2 DIRACWebAppResources/$2 /;
      # Prior to v7r3 this should be slightly different:
      #   alias /opt/dirac/pro/;
      #   try_files WebAppDIRAC/WebApp/static/$2 /;
      # The new-style is mandatory for Python 3 based installations/
      expires 1d;
      gzip_static on;
      gzip_disable "MSIE [1-6]\.";
      add_header Cache-Control public;
      break;
    }

    location ~ /DIRAC/ {
      proxy_pass_header Server;
      proxy_set_header Host $http_host;
      proxy_redirect off;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Scheme $scheme;
      proxy_pass http://tornadoserver;
      proxy_read_timeout 3600;
      proxy_send_timeout 3600;

      proxy_set_header X-Ssl_client_verify $ssl_client_verify;
      proxy_set_header X-Ssl_client_s_dn $ssl_client_s_dn;
      proxy_set_header X-Ssl_client_i_dn $ssl_client_i_dn;
      # pass escaped certificate pem to DIRAC
      proxy_set_header X-SSL-CERT $ssl_client_escaped_cert;

      gzip on;
      gzip_proxied any;
      gzip_comp_level 9;
      gzip_types text/plain text/css application/javascript application/xml application/json;

      # WebSocket support (nginx 1.4)
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";

      break;
    }

    location / {
      rewrite ^ https://$server_name/DIRAC/ permanent;
    }
  }

You can start NGINX now
~~~~~~~~~~~~~~~~~~~~~~~

Start, Stop and restart nginx::

  /etc/init.d/nginx start|stop|restart

You have to add to the /WebApp section the following lines in order to use NGINX::

  DevelopMode = False
  StaticResourceLinkDir = /opt/dirac/webRoot/resources
  Balancer = nginx
  NumProcesses = 1

In that case one process will be used and this process is listening on 8000 port. You can try to use the web portal. For example: http://your.server.domain/DIRAC/.

SELinux rules
~~~~~~~~~~~~~

If you get 502 Bad Gateway error, you need to generate rules for SELinux. You can see the error in /var/log/nginx/error.log::

  016/06/02 15:55:24 [crit] 20317#20317: *4 connect() to 127.0.0.1:8000 failed (13: Permission denied) while connecting to upstream, client: xxx.xxx.xxx.xxx, server: your.server.domain, request: "GET /DIRAC/?view=tabs&theme=Grey&url_state=1| HTTP/1.1", upstream: "http://127.0.0.1:8000/DIRAC/?view=tabs&theme=Grey&url_state=1|", host: "your.server.domain"

Generate the rule::

  grep nginx /var/log/audit/audit.log | audit2allow -M nginx
  semodule -i nginx.pp

Refresh the page


WebDav
------

Optionally you can organize a file server to upload and download files.

Provide WebDav module
~~~~~~~~~~~~~~~~~~~~~

Install the required development tools of your operating system to be able to compile the WebDAV dynamic module for Nginx::

  yum groupinstall "Development Tools" -y
  yum install yum-utils pcre-devel zlib-devel libxslt-devel libxml2-devel -y

Download Nginx and the module source code. You need to determine which Nginx version is running on your server like this::

  nginx -v
  nginx version: nginx/1.16.1

Download the source code corresponding to the installed version::

  wget http://nginx.org/download/nginx-1.16.1.tar.gz

Clone the module repository::

  git clone https://github.com/arut/nginx-dav-ext-module

Change to the Nginx source code directory, compile the module, and copy it to the standard directory for the Nginx modules::

  cd nginx-1.16.1
  ./configure --with-compat --with-http_dav_module --add-dynamic-module=../nginx-dav-ext-module/
  make modules
  cp objs/ngx_http_dav_ext_module.so /etc/nginx/modules/

Configure WebDav
~~~~~~~~~~~~~~~~

To describe your WebDav server, please, add these locations to the NGINX configuration::

  # The same directory must exist with 'rw' permissions for all
  location /files {
    # Access for GET requests without certificate
    if ($request_method = GET) {
      # Webdav sever
      error_page 418 = @webdav;
      return 418;
    }

    # For not GET requests access only with client certificate verification
    if ($ssl_client_verify = NONE) {
      return 403 'certificate not found';
    }
    if ($ssl_client_verify != SUCCESS) {
      return 403 'certificate verify failed';
    }

    # Webdav sever
    error_page 418 = @webdav;
    return 418;
  }

  location @webdav {
    satisfy any;
    # Read access for all
    limit_except GET {
      # Here need to add hosts IPs that allowed to make requests, except GET
      # First, need to add the IP host used by the master CS.
      #allow XXX.XXX.XXX.XXX;
      deny  all;
    }
    client_max_body_size 1g;
    root /opt/dirac/webRoot/www/;
    # Access settings
    dav_access group:rw all:rw;
    # Allow all posible methods
    dav_methods PUT DELETE MKCOL COPY MOVE;
    # For webdav clients (Cyberduck and Monosnap)
    dav_ext_methods PROPFIND OPTIONS;
    # Clients can create paths
    create_full_put_path on;
    charset utf-8;
    autoindex on;
    break;
  }

Make sure the directory exists with the necessary permissions::

  mkdir /opt/dirac/webRoot/www/files
  chmod 666 /opt/dirac/webRoot/www/files
  chown dirac:dirac /opt/dirac/webRoot/www/files
