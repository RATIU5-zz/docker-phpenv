# docker-phpenv
Script that creates a docker container for PHP

Usage: phpenv.py [command] [flags]
commands:
create [-d, -o]  (creates the docker folder/file structure)
                 ('-d' forces deletion of the original files after successful copy)
                 ('-o' forces overwrite if the file being copied exitsts)
start            (starts the docker process [docker-compose up])
help             (displays this help menu)

eg. phpenv.py create -d
