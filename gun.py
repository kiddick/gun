import datetime
import os
import errno
import re
import socket
import subprocess
import time

from contextlib import closing
from string import Template

import yaml
import click


def symlink_force(target, name):
    try:
        os.symlink(target, name)
    except OSError as err:
        if err.errno == errno.EEXIST:
            os.remove(name)
            os.symlink(target, name)
        else:
            raise err


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
    symlink_force(os.path.join('/etc/nginx/sites-available', name),
                  os.path.join('/etc/nginx/sites-enabled', name))


def read_template(name):
    with open(name, 'r') as filein:
        return Template(filein.read())


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


@click.group(invoke_without_command=True)
@click.argument('config', nargs=1, type=click.File('r'))
@click.pass_context
def cli(ctx, config):
    if not ctx.obj:
        ctx.obj = {}
    ctx.obj['config'] = config
    if ctx.invoked_subcommand is None:
        src = read_template('template.conf')
        data = read_settings(config)
        data['ip'] = get_ip()

        save_nginx_conf(data['name'], src.substitute(data))

        site_available = read_template('site_available.conf')
        save_sites_config(data['name'], site_available.substitute(data))
    else:
        click.echo('{} is running..'.format(ctx.invoked_subcommand))


@cli.command()
@click.pass_context
def ngrok(ctx):
    data = read_settings(ctx.obj['config'])
    mkdir(os.path.join(data['app_name'], 'ngrok'))
    ip_address = get_ip()
    paths = (data['app_name'], 'ngrok', 'ngrok.log')
    logfile = os.path.join(*paths)
    if os.path.isfile(logfile):
        os.rename(
            logfile,
            logfile[:-4] + datetime.datetime.now().strftime('%d-%m-%y_%H:%M'))
    subprocess.call(
        (data['ngrok'] + ' http {ip}:{port} -log=stdout -log-level=debug' +
         ' > {logfile} &').format(ip=ip_address,
                                  port=data['port'],
                                  logfile=logfile),
        shell=True
    )
    time.sleep(1.2)
    with open(logfile, 'r') as lf:
        data = lf.read().replace('\n', '')
    try:
        ngrok_host = re.search(r'Hostname:\w+.\w+.\w+', data).group(0)[9:]
        with open(os.path.join(data['app_name'], 'ngrok.host'), 'w') as nh:
            nh.write(ngrok_host)
    except Exception:
        pass

if __name__ == '__main__':
    cli()
