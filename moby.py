import io
import json
import logging
import posixpath
import tarfile

import docker
import yaml
import requests


END = '\033[0m'
BOLD = '\033[1m{}' + END


def build_image(client, logger):
    logger.info(BOLD.format('Building image...\n'))
    image = client.build(
        path='.')
    for line in image:
        line = json.loads(line.decode())
        logger.debug(line['stream'])
    image = line['stream'].strip().split()[-1]
    return image


def init_client():
    return docker.APIClient()


def init_logger(level=logging.INFO):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.terminator = ''

    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def load_config():
    with open('moby.yml', 'r') as config:
        config = yaml.load(config)
    return config


def pull(client, container, files, logger):
    cwd = run_command(client, container, 'pwd', logger, silent=True)
    for path in files:
        if not path.startswith('/'):
            path = posixpath.join(cwd, path)
        response = client.get_archive(container, path)[0]
        archive_file = io.BytesIO(response.read())
        archive = tarfile.open(fileobj=archive_file, mode='r')
        archive.extractall()



def push(client, container, files, logger):
    cwd = run_command(client, container, 'pwd', logger, silent=True)
    archive_file = io.BytesIO()
    archive = tarfile.open(fileobj=archive_file, mode='w')
    for path in files:
        archive.add(path)
    client.put_archive(container, cwd, archive_file.getvalue())


def run_command(client, container, command, logger, silent=False):
    if not silent:
        logger.info(BOLD.format('Running {!r}:\n'.format(command)))
    command = client.exec_create(
        container,
        command)
    out = io.StringIO()
    out_gen = client.exec_start(
        command,
        stream=True)
    for line in out_gen:
        line = line.decode()
        out.write(line)
        if not silent:
            logger.info(line)
    command = client.exec_inspect(command)
    exit_code = command['ExitCode']
    if exit_code:
        raise SystemExit(exit_code)
    return out.getvalue().strip()


def run_env(client, container, env, logger):
    if 'before' in env:
        run_env(client, container, env['before'], logger)

    if 'push' in env:
        push(client, container, env['push'], logger)

    for command in env.get('run', []):
        run_command(client, container, command, logger)

    if 'pull' in env:
        pull(client, container, env['pull'], logger)

    if 'after' in env:
        run_env(client, container, env['after'], logger)


def start_container(client, image, logger):
    logger.info(BOLD.format('Starting container...\n'))
    container = client.create_container(
        image,
        detach=True,
        entrypoint='cat',
        tty=True)
    client.start(container)
    return container


def stop_container(client, container, logger):
    logger.info(BOLD.format('Stopping container...\n'))
    client.stop(container)


def main():
    logger = init_logger()
    config = load_config()
    client = init_client()
    image = build_image(client, logger)
    container = start_container(client, image, logger)

    try:
        for env in config['envlist']:
            run_env(client, container, config[env], logger)
    finally:
        stop_container(client, container, logger)


if __name__ == '__main__':
    main()
