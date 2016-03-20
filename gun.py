import os
import socket
from contextlib import closing
from string import Template

import yaml
import click


def read_settings(config):
    return yaml.load(config)


def get_ip():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as sckt:
        sckt.connect(("gmail.com", 80))
        return sckt.getsockname()[0]


def save_nginx_conf(name, data):
    with open(os.path.join('/etc/init', name + '.conf'), 'w') as ngnix_conf:
        ngnix_conf.write(data)


def save_sites_config(name, data):
    with open(os.path.join('/etc/nginx/sites-available', name),
              'w') as ngnix_conf:
        ngnix_conf.write(data)
    os.symlink(os.path.join('/etc/nginx/sites-available', name),
               os.path.join('/etc/nginx/sites-enabled', name))


def read_template(name):
    with open(name, 'r') as filein:
        return Template(filein.read())


@click.command()
@click.argument('config', nargs=1, type=click.File('r'))
def fill_template(config):

    src = read_template('template.conf')
    data = read_settings(config)
    data['ip'] = get_ip()

    save_nginx_conf(data['name'], src.substitute(data))

    site_available = read_template('site_available.conf')
    save_sites_config(data['name'], site_available.substitute(data))


if __name__ == '__main__':
    fill_template()
