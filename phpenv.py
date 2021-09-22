import os
import sys
from pathlib import Path
import subprocess
from shutil import copy2, Error, which

parsed_args = dict()

def main():
    parse_args()

    if "help" in parsed_args:
        help()

    if "create" in parsed_args:
       create()
    
    elif "start" in parsed_args:
        start_env()
    
    else:
        help()
        

def help():
    print()
    print("Usage: phpenv.py [command] [flags]")
    print("commands:")
    print("create [-d, -o]  (creates the docker folder/file structure)")
    print("                 ('-d' forces deletion of the original files after successful copy)")
    print("                 ('-o' forces overwrite if the file being copied exitsts)")
    print("start            (starts the docker process [docker-compose up])")
    print("help             (displays this help menu)")
    print("\neg. phpenv.py create -d")


def create():
    print("creating docker implementation")

    create_dir_struct()

    path = os.getcwd()
    delete_copies = ("-d" in parsed_args)
    overwrite = ("-o" in parsed_args)

    try:
        print("copying to src/public")
        copy_tree(path, os.path.join(path, f"{COPY_FOLDER_NAME}/src/public"),delete_copies=delete_copies,overwrite=overwrite)
    except FileExistsError:
        print("skipping copy to src/public")

    print("completed project setup")


# Parse the arguments, add them to a global dictionary
def parse_args():
    args = sys.argv[1:]

    for cmd in args:
        if (cmd.find("=") > 0):
            split = cmd.split("=")
            parsed_args[split[0]] = split[1]
        else: parsed_args[cmd] = None


# Set up the folders/files of the docker-php project
def create_dir_struct():
    # Set up working directory
    path = os.path.join(os.getcwd(), COPY_FOLDER_NAME)
    create_path(path)

    compose_path = os.path.join(path, "docker-compose.yml")
    create_file(compose_path, DOCKER_COMPOSE_FILE_DATA)

    # Setup folder structure
    joined_path = os.path.join(path, "docker/php/sites-available")
    create_path(joined_path)
    joined_path = os.path.join(path, "src/public")
    create_path(joined_path)
    joined_path = os.path.join(path, "src/private/db")
    create_path(joined_path)

    # Create Dockerfile file for php
    php_docker_file = os.path.join(path, "docker/php/Dockerfile")
    create_file(php_docker_file, PHP_DOCKER_FILE_DATA)

    # Create default apache2.conf file
    apache2_conf_file = os.path.join(path, "docker/php/apache2.conf")
    create_file(apache2_conf_file, APACHE2_CONF_FILE_DATA)

    # Create virtual host config file to set public as document root
    sites_conf_file = os.path.join(path, "docker/php/sites-available/000-default.conf")
    create_file(sites_conf_file, DEFAULT_CONF_FILE_DATA)


def start_env():
    if which("docker-compose"):
        print("starting containers")
        os.chdir(os.path.join(os.getcwd(), COPY_FOLDER_NAME))
        subprocess.run(["docker-compose", "up"])
    else:
        print("ERROR: Docker is not installed on your system. Please install Docker Desktop, found here:\nhttps://www.docker.com/products/docker-desktop")
        print("(If you are on Windows, you'll need to make sure Enable Hyper-V Windows Features or the Install required Windows components for WSL 2 option is selected on the configuration page.")


# Creates the given path, skips if it already exists
def create_path(path):
    name = os.path.basename(path)
    if not os.path.exists(path):
        print(f"creating {name} directory")
        Path(path).mkdir(parents=True,exist_ok=True)
    else:
        print(f"skipping create of {name}: exists")


# Creates the given file, skips if exists without data, or adds data to existing file
def create_file(file_path, data=None):
    name = os.path.basename(file_path)
    if not os.path.exists(file_path):
        with open(file_path, "w+") as file:
            print(f"creating {name}")
            if not data: pass
            else:
                print(f"skipping create of {name}: exists")
                file.write(data)
            file.close()
    else:
        if data:
            if os.stat(file_path).st_size == 0:
                print(f"writing data to {name}")
                with open(file_path, "w") as file:
                    file.write(data)
                    file.close()
        else: print(f"skipping create of {name}: exists")


def copy_tree(src, dest, ignore=None, delete_copies=False,overwrite=False):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = set.union(ignore, {COPY_FOLDER_NAME})
    else:
        ignored_names = {COPY_FOLDER_NAME}
    
    if not os.path.isdir(dest):
        os.makedirs(dest)
    
    errors = []

    for name in names:
        if name in ignored_names: continue
        srcname = os.path.join(src, name)
        destname = os.path.join(dest, name)

        try:
            if os.path.isdir(srcname):
                copy_tree(srcname, destname, ignore, delete_copies, overwrite)
                if delete_copies:
                    if len(os.listdir(srcname)) == 0:
                        print(f"deleting directory {srcname}")
                        os.rmdir(srcname)
                    else:
                        print(f"skipping deletion of {srcname}; directory full")
                
            else:
                if os.path.exists(destname) and not overwrite:
                    print(f"skipping copy of {name}: already exists")
                    if delete_copies:
                        if (os.path.exists(srcname)):
                            print(f"deleting {srcname}")
                            os.remove(srcname)
                else:
                    try:
                        print(f"copying {name}")
                        copy2(srcname, destname)
                        if delete_copies:
                            print(f"deleting {srcname}")
                            os.remove(srcname)
                    except EnvironmentError:
                        print(f"failed to copy {name}")
                    
        except (IOError, os.error) as e:
            errors.append((srcname, destname, str(e)))
        except Error as err:
            errors.extend(err.args[0])


COPY_FOLDER_NAME = "phpenv"

DOCKER_COMPOSE_FILE_DATA = """
version: \"3.9\"
services:
    php:
        container_name: php-apache
        build:
            context: ./docker/php
            dockerfile: Dockerfile
        volumes:
            - ./docker/php/sites-available/:/etc/apache2/sites-available
            - ./docker/php/apache2.conf:/etc/apache2/apache2.conf
            - ./src:/var/www/html/
        ports:
            - 8080:80
    mysql:
        container_name: db
        image: mysql
        restart: always
        ports:
            - 9906:3306
        environment:
            MYSQL_ROOT_PASSWORD: abc123
        volumes:
            - ./src/private/db:/docker-entrypoint-initdb.d
"""

PHP_DOCKER_FILE_DATA = """
FROM php:8.0-apache
RUN docker-php-ext-install mysqli && docker-php-ext-enable mysqli
RUN apt-get update && apt-get upgrade -y
"""

APACHE2_CONF_FILE_DATA = """
# This is the main Apache server configuration file.  It contains the
# configuration directives that give the server its instructions.
# See http://httpd.apache.org/docs/2.4/ for detailed information about
# the directives and /usr/share/doc/apache2/README.Debian about Debian specific
# hints.
#
#
# Summary of how the Apache 2 configuration works in Debian:
# The Apache 2 web server configuration in Debian is quite different to
# upstream's suggested way to configure the web server. This is because Debian's
# default Apache2 installation attempts to make adding and removing modules,
# virtual hosts, and extra configuration directives as flexible as possible, in
# order to make automating the changes and administering the server as easy as
# possible.

# It is split into several files forming the configuration hierarchy outlined
# below, all located in the /etc/apache2/ directory:
#
#       /etc/apache2/
#       |-- apache2.conf
#       |       `--  ports.conf
#       |-- mods-enabled
#       |       |-- *.load
#       |       `-- *.conf
#       |-- conf-enabled
#       |       `-- *.conf
#       `-- sites-enabled
#               `-- *.conf
#
#
# * apache2.conf is the main configuration file (this file). It puts the pieces
#   together by including all remaining configuration files when starting up the
#   web server.
#
# * ports.conf is always included from the main configuration file. It is
#   supposed to determine listening ports for incoming connections which can be
#   customized anytime.
#
# * Configuration files in the mods-enabled/, conf-enabled/ and sites-enabled/
#   directories contain particular configuration snippets which manage modules,
#   global configuration fragments, or virtual host configurations,
#   respectively.
#
#   They are activated by symlinking available configuration files from their
#   respective *-available/ counterparts. These should be managed by using our
#   helpers a2enmod/a2dismod, a2ensite/a2dissite and a2enconf/a2disconf. See
#   their respective man pages for detailed information.
#
# * The binary is called apache2. Due to the use of environment variables, in
#   the default configuration, apache2 needs to be started/stopped with
#   /etc/init.d/apache2 or apache2ctl. Calling /usr/bin/apache2 directly will not
#   work with the default configuration.


# Global configuration
#

#
# ServerRoot: The top of the directory tree under which the server's
# configuration, error, and log files are kept.
#
# NOTE!  If you intend to place this on an NFS (or otherwise network)
# mounted filesystem then please read the Mutex documentation (available
# at <URL:http://httpd.apache.org/docs/2.4/mod/core.html#mutex>);
# you will save yourself a lot of trouble.
#
# Do NOT add a slash at the end of the directory path.
#
#ServerRoot "/etc/apache2"

#
# The accept serialization lock file MUST BE STORED ON A LOCAL DISK.
#
#Mutex file:${APACHE_LOCK_DIR} default

#
# The directory where shm and other runtime files will be stored.
#

DefaultRuntimeDir ${APACHE_RUN_DIR}

#
# PidFile: The file in which the server should record its process
# identification number when it starts.
# This needs to be set in /etc/apache2/envvars
#
PidFile ${APACHE_PID_FILE}

#
# Timeout: The number of seconds before receives and sends time out.
#
Timeout 300

#
# KeepAlive: Whether or not to allow persistent connections (more than
# one request per connection). Set to "Off" to deactivate.
#
KeepAlive On

#
# MaxKeepAliveRequests: The maximum number of requests to allow
# during a persistent connection. Set to 0 to allow an unlimited amount.
# We recommend you leave this number high, for maximum performance.
#
MaxKeepAliveRequests 100

#
# KeepAliveTimeout: Number of seconds to wait for the next request from the
# same client on the same connection.
#
KeepAliveTimeout 5


# These need to be set in /etc/apache2/envvars
User ${APACHE_RUN_USER}
Group ${APACHE_RUN_GROUP}

#
# HostnameLookups: Log the names of clients or just their IP addresses
# e.g., www.apache.org (on) or 204.62.129.132 (off).
# The default is off because it'd be overall better for the net if people
# had to knowingly turn this feature on, since enabling it means that
# each client request will result in AT LEAST one lookup request to the
# nameserver.
#
HostnameLookups Off

# ErrorLog: The location of the error log file.
# If you do not specify an ErrorLog directive within a <VirtualHost>
# container, error messages relating to that virtual host will be
# logged here.  If you *do* define an error logfile for a <VirtualHost>
# container, that host's errors will be logged there and not here.
#
ErrorLog ${APACHE_LOG_DIR}/error.log

#
# LogLevel: Control the severity of messages logged to the error_log.
# Available values: trace8, ..., trace1, debug, info, notice, warn,
# error, crit, alert, emerg.
# It is also possible to configure the log level for particular modules, e.g.
# "LogLevel info ssl:warn"
#
LogLevel warn

# Include module configuration:
IncludeOptional mods-enabled/*.load
IncludeOptional mods-enabled/*.conf

# Include list of ports to listen on
Include ports.conf


# Sets the default security model of the Apache2 HTTPD server. It does
# not allow access to the root filesystem outside of /usr/share and /var/www.
# The former is used by web applications packaged in Debian,
# the latter may be used for local directories served by the web server. If
# your system is serving content from a sub-directory in /srv you must allow
# access here, or in any related virtual host.
<Directory />
        Options FollowSymLinks
        AllowOverride None
        Require all denied
</Directory>

<Directory /usr/share>
        AllowOverride None
        Require all granted
</Directory>

<Directory /var/www/>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
</Directory>

#<Directory /srv/>
#       Options Indexes FollowSymLinks
#       AllowOverride None
#       Require all granted
#</Directory>




# AccessFileName: The name of the file to look for in each directory
# for additional configuration directives.  See also the AllowOverride
# directive.
#
AccessFileName .htaccess

#
# The following lines prevent .htaccess and .htpasswd files from being
# viewed by Web clients.
#
<FilesMatch "^\.ht">
        Require all denied
</FilesMatch>


#
# The following directives define some format nicknames for use with
# a CustomLog directive.
#
# These deviate from the Common Log Format definitions in that they use %O
# (the actual bytes sent including headers) instead of %b (the size of the
# requested file), because the latter makes it impossible to detect partial
# requests.
#
# Note that the use of %{X-Forwarded-For}i instead of %h is not recommended.
# Use mod_remoteip instead.
#
LogFormat "%v:%p %h %l %u %t \\\"%r\\\" %>s %O \\\"%{Referer}i\\\" \\\"%{User-Agent}i\\\"" vhost_combined
LogFormat "%h %l %u %t \\\"%r\\\" %>s %O \\\"%{Referer}i\\\" \\\"%{User-Agent}i\\\"" combined
LogFormat "%h %l %u %t \\\"%r\\\" %>s %O" common
LogFormat "%{Referer}i -> %U" referer
LogFormat "%{User-agent}i" agent

# Include of directories ignores editors' and dpkg's backup files,
# see README.Debian for details.

# Include generic snippets of statements
IncludeOptional conf-enabled/*.conf

# Include the virtual host configurations:
IncludeOptional sites-enabled/*.conf

# vim: syntax=apache ts=4 sw=4 sts=4 sr noet
#"""

DEFAULT_CONF_FILE_DATA = """
<VirtualHost *:80>
        # The ServerName directive sets the request scheme, hostname and port that
        # the server uses to identify itself. This is used when creating
        # redirection URLs. In the context of virtual hosts, the ServerName
        # specifies what hostname must appear in the request's Host: header to
        # match this virtual host. For the default virtual host (this file) this
        # value is not decisive as it is used as a last resort host regardless.
        # However, you must set it for any further virtual host explicitly.
        #ServerName www.example.com

        ServerAdmin webmaster@localhost
        DocumentRoot /var/www/html/public

        # Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
        # error, crit, alert, emerg.
        # It is also possible to configure the loglevel for particular
        # modules, e.g.
        #LogLevel info ssl:warn

        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined

        # For most configuration files from conf-available/, which are
        # enabled or disabled at a global level, it is possible to
        # include a line for only one particular virtual host. For example the
        # following line enables the CGI configuration for this host only
        # after it has been globally disabled with "a2disconf".
        #Include conf-available/serve-cgi-bin.conf
</VirtualHost>"""


if __name__ == "__main__":
    main()
    print("\n")