"""
Moby is a tool to automate interaction with docker.

Using a config file `moby.cfg`, moby automates interaction with docker.
Files can be uploaded to and downloaded from a container and commands can be
run in the container.

Common args
***********

Most functions expect common args. They are documented here to prevent needless
repetition.

* client (.docker.APIClient): The docker client to use.
* logger (.logging.Logger): The logger to use to log build info.


"""

import io
import json
import logging
import posixpath
import tarfile

import docker
import yaml


END = '\033[0m'
BOLD = '\033[1m{}' + END


def build_image(client, logger):
    """
    Build the docker image.

    Build the docker image from the Dockerfile in the current directory.

    Returns:
        str: The id of the built image.

    """
    logger.info(BOLD.format('Building image...\n'))
    image = client.build(
        path='.')
    for line in image:
        line = json.loads(line.decode())
        logger.debug(line['stream'])
    image = line['stream'].strip().split()[-1]
    return image


def init_client():
    """
    Initialise the docker client.

    Returns:
        .docker.APIClient: The docker client.

    """
    return docker.APIClient()


def init_logger(level=logging.INFO):
    """
    Initialise the logger.

    Configure and initialise a logger. The logger is configured to log at the
    given level. Newlines are omitted so no double newlines are logged.
    The logger is configured to log to stdout.

    Args:
        level (int): The level the logger should log on.

    Returns:
        .logging.Logger: The initialised logger.

    """
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
    """
    Load the moby config.

    Load and parse the `moby.yml` config.

    Returns:
        dict: The parsed config.

    """
    with open('moby.yml', 'r') as config:
        config = yaml.load(config)
    return config


def pull(client, container, files, logger):
    """
    Pull files from the container.

    Pull files from the container to the current directory of the host.
    Filenames can be relative or absolute, if relative they are expected to be
    relative to the current working dir of the container.

    Args:
        container (str): The id of the container.
        files (list): A list of filenames (`str`) to download.

    """
    cwd = run_command(client, container, 'pwd', logger, silent=True)
    for path in files:
        if not path.startswith('/'):
            path = posixpath.join(cwd, path)
        response = client.get_archive(container, path)[0]
        archive_file = io.BytesIO(response.read())
        archive = tarfile.open(fileobj=archive_file, mode='r')
        archive.extractall()


def push(client, container, files, logger):
    """
    Push files to the container.

    Push files to the current working directory of the container.

    Args:
        container (str): The id of the container.
        files (list): A list of filenames (`str`) to upload.

    """
    cwd = run_command(client, container, 'pwd', logger, silent=True)
    archive_file = io.BytesIO()
    archive = tarfile.open(fileobj=archive_file, mode='w')
    for path in files:
        archive.add(path)
    client.put_archive(container, cwd, archive_file.getvalue())


def run_command(client, container, command, logger, silent=False):
    """
    Run a command in a running container.

    Args:
        container (str): The id of the container.
        command (str): The command to run.

    Keyword Args:
        silent (bool): Whether or not to suppress logging.

    Returns:
        str: The output of the command.

    Raises:
        SystemExit: When the command fails a SystemExit is raised with the
            same exit code.

    """
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
    """
    Run an environment.

    Run the environment following this sequence of entries:

    #. `before`
    #. `push`
    #. `run` **Required**
    #. `pull`
    #. `after`

    Args:
        container (str): The id of the container.
        env (dict): The environment to run.

    """
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
    """
    Start a container.

    Use an image to start a container.

    Args:
        image (str): The id of the image.

    Returns:
        str: The container id.

    """
    logger.info(BOLD.format('Starting container...\n'))
    container = client.create_container(
        image,
        detach=True,
        entrypoint='cat',
        tty=True)
    client.start(container)
    return container


def stop_container(client, container, logger):
    """
    Stop a running container.

    Args:
        container (str): The id of the container.

    """
    logger.info(BOLD.format('Stopping container...\n'))
    client.stop(container)


def main():
    """
    The main entry point of moby.

    This function ties it all together.

    """
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
