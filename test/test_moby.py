"""Unit tests for moby."""

import functools
import io
import json
import logging
import tarfile
from unittest import mock

import docker
import pytest

import moby


@pytest.fixture
def build_image(
        image):
    """
    build_image function mock.

    The image fixture is returned when the build_image mock is called.

    """
    patch = mock.patch('moby.build_image', return_value=image)
    yield patch.start()
    patch.stop()


@pytest.fixture
def client():
    """A mocked docker client."""
    return mock.Mock(docker.APIClient)


@pytest.fixture
def config():
    """A config as parsed by load_config."""
    return {
        'envlist': ['first', 'second'],
        'first': mock.Mock(),
        'second': mock.Mock()
    }


@pytest.fixture
def container():
    """The container."""
    return 'container'


@pytest.fixture
def cwd(run_command):
    """
    The current directory.

    The run_command fixture is configured to return the cwd by default.

    """
    cwd = '/cwd'
    run_command.return_value = cwd
    return cwd


@pytest.fixture
def env(env_after,
        env_before,
        env_pull):
    """An environment dict."""
    env = {
        'run': ['spam', 'eggs']
    }
    if env_after:
        env['after'] = env_after
    if env_before:
        env['before'] = env_before
    if env_pull:
        env['pull'] = env_pull
    if env_push:
        env['push'] = env_push
    return env


@pytest.fixture(
    params=[0, 1],
    ids=['no_after', 'after'])
def env_after(request):
    """
    An after entry for the environment.

    The entry is optional.

    """
    if request.param:
        return {'run': ['after']}


@pytest.fixture(
    params=[0, 1],
    ids=['no_before', 'before'])
def env_before(request):
    """
    A before entry for the environment.

    The entry is optional.

    """
    if request.param:
        return {'run': ['before']}


@pytest.fixture(
    params=[0, 1],
    ids=['no_pull', 'pull'])
def env_pull(request):
    """
    A pull entry for the environment.

    The entry is optional.

    """
    if request.param:
        return {'run': ['pull']}


@pytest.fixture(
    params=[0, 1],
    ids=['no_push', 'push'])
def env_push(request):
    """
    A push entry for the environment.

    The entry is optional.

    """
    if request.param:
        return {'run': ['push']}


@pytest.fixture(
    params=[0, 1],
    ids=['exit_0', 'exit_1'])
def exit_code(request):
    """Possible exit codes."""
    return request.param


@pytest.fixture
def image():
    """image mock."""
    return 'image'


@pytest.fixture
def init_client(
        client):
    """
    init_client function mock.

    The mock returns the client when called.

    """
    patch = mock.patch('moby.init_client', return_value=client)
    yield patch.start()
    patch.stop()


@pytest.fixture
def init_logger(
        logger):
    """
    init_logger function mock.

    The mock returns the logger when called.

    """
    patch = mock.patch('moby.init_logger', return_value=logger)
    yield patch.start()
    patch.stop()


@pytest.fixture
def load_config(
        config):
    """load_config function mock."""
    patch = mock.patch('moby.load_config', return_value=config)
    yield patch.start()
    patch.stop()


@pytest.fixture
def log_formatter():
    """log formatter mock."""
    patch = mock.patch('logging.Formatter')
    yield patch.start()
    patch.stop()


@pytest.fixture
def log_handler():
    """log handler mock."""
    patch = mock.patch('logging.StreamHandler')
    yield patch.start()
    patch.stop()


@pytest.fixture
def logger():
    """logger mock."""
    return mock.Mock(logging.Logger)


@pytest.fixture(
    params=[None, logging.INFO],
    ids=['loglevel_default', 'loglevel_info'])
def level(request):
    """logging level param."""
    return request.param


@pytest.fixture
def pull():
    """pull function mock."""
    patch = mock.patch('moby.pull')
    yield patch.start()
    patch.stop()


@pytest.fixture
def push():
    """push function mock."""
    patch = mock.patch('moby.push')
    yield patch.start()
    patch.stop()


@pytest.fixture
def run_command():
    """run_command function mock."""
    patch = mock.patch('moby.run_command')
    yield patch.start()
    patch.stop()


@pytest.fixture
def run_env():
    """run_env function mock."""
    patch = mock.patch('moby.run_env')
    yield patch.start()
    patch.stop()


@pytest.fixture(
    params=[True, False],
    ids=['silent', 'not_silent'])
def silent(request):
    """Bool to toggle the silent flag."""
    return request.param


@pytest.fixture
def start_container(
        container):
    """start_container function mock."""
    patch = mock.patch('moby.start_container', return_value=container)
    yield patch.start()
    patch.stop()


@pytest.fixture
def stop_container():
    """stop_container function mock."""
    patch = mock.patch('moby.stop_container')
    yield patch.start()
    patch.stop()


def test_build_image(
        client,
        logger):
    """
    Test building an image.

    The client should be used to build the image. The created image should
    be returned.

    """
    output = (
        json.dumps({'stream': line}).encode()
        for line in ['build\n', 'output\n', 'The image: 1234\n']
    )
    client.build.return_value = (line for line in output)
    result = moby.build_image(client, logger)
    assert result == '1234'
    client.build.assert_called_once_with(
        path='.')
    logger.info.assert_has_calls([
        mock.call('\033[1mBuilding image...\n\033[0m'),
    ])
    logger.debug.assert_has_calls([
        mock.call('build\n'),
        mock.call('output\n'),
        mock.call('The image: 1234\n'),
    ])


def test_init_client():
    """Test initialising a docker client."""
    with mock.patch('docker.APIClient') as apiclient:
        result = moby.init_client()

    assert result == apiclient.return_value
    apiclient.assert_called_once_with()


def test_init_logger(
        log_formatter,
        level,
        log_handler,
        logger):
    """
    Test initialising the logger.

    The logger should be initialised on the info level. The default terminator
    should be removed.

    """
    with mock.patch('logging.getLogger', return_value=logger) as getlogger:
        if level:
            result = moby.init_logger(level=level)
        else:
            result = moby.init_logger()
    level = level or logging.INFO
    assert result == logger
    getlogger.assert_called_once_with(moby.__name__)
    logger.setLevel.assert_called_once_with(level)

    log_handler.assert_called_once_with()
    log_handler = log_handler.return_value
    log_handler.setLevel.assert_called_once_with(level)
    assert log_handler.terminator == ''

    log_formatter.assert_called_once_with('%(message)s')
    log_formatter = log_formatter.return_value
    log_handler.setFormatter.assert_called_once_with(log_formatter)

    logger.addHandler.assert_called_once_with(log_handler)


def test_load_config():
    """
    Test loading the config file.

    The file `moby.yaml` should be opened and passed to `yaml.load`. The
    result should be returned.

    """
    config = mock.Mock()
    _open = mock.mock_open()
    with mock.patch('moby.open', _open, create=True):
        with mock.patch('yaml.load', return_value=config) as load:
            result = moby.load_config()
    assert result == config
    _open.assert_called_once_with('moby.yml', 'r')
    load.assert_called_once_with(_open.return_value)


def test_pull(
        client,
        container,
        cwd,
        logger,
        run_command):
    """
    Test pulling files from a container.

    Each file should be downloaded and extracted to the current working dir.

    """
    files = [
        'relative',
        '/abso/lute'
    ]

    tar_stream = io.BytesIO()
    tar = tarfile.open(fileobj=tar_stream, mode='w')
    for f in files:
        tarinfo = tarfile.TarInfo(name=f)
        tar.addfile(tarinfo, fileobj=io.BytesIO())
    tar_stream.seek(0)
    client.get_archive.return_value = (tar_stream, {})

    tar_mocks = [mock.Mock(tarfile.TarFile) for f in files]
    with mock.patch('tarfile.open', side_effect=tar_mocks):
        moby.pull(client, container, files, logger)

    run_command.assert_called_once_with(
        client, container, 'pwd', logger, silent=True)
    client.get_archive.assert_has_calls([
        mock.call(container, '/'.join([cwd, 'relative'])),
        mock.call(container, '/abso/lute')
    ])
    for tar_mock in tar_mocks:
        tar_mock.extractall.assert_called_once_with()


def test_push(
        client,
        container,
        cwd,
        logger,
        run_command):
    """
    Test pushing files to a container.

    Files should be put in a tarfile and pushed to the container using the
    client.

    """
    files = [
        'relative',
        '/abso/lute'
    ]

    with mock.patch('tarfile.open') as tar_mock:
        moby.push(client, container, files, logger)
    run_command.assert_called_once_with(
        client, container, 'pwd', logger, silent=True)
    tar_mock.assert_called_once_with(fileobj=mock.ANY, mode='w')
    archive_file = tar_mock.call_args[1]['fileobj']
    tar_mock.return_value.add.assert_has_calls([
        mock.call(f) for f in files
    ])
    client.put_archive.assert_called_once_with(
        container, cwd, archive_file.getvalue())


def test_run_command(
        client,
        container,
        exit_code,
        logger,
        silent):
    """
    Test running a command in a container.

    The command should be ran in the conatiner using the client. The output of
    the command should be returned.

    """
    client.exec_start.return_value = (
        line for line in [b'first\n', b'second\n'])
    client.exec_inspect.return_value = {'ExitCode': exit_code}

    run_command = functools.partial(
        moby.run_command,
        client,
        container,
        'command',
        logger,
        silent=silent)
    if exit_code:
        with pytest.raises(SystemExit) as excinfo:
            run_command()
        assert excinfo.value.args == (exit_code,)
    else:
        result = run_command()
        assert result == 'first\nsecond'
    client.exec_create.assert_called_once_with(
        container,
        'command')
    client.exec_start.assert_called_once_with(
        client.exec_create.return_value,
        stream=True)
    client.exec_inspect.assert_called_once_with(
        client.exec_create.return_value)
    if not silent:
        logger.info.assert_has_calls([
            mock.call('\033[1mRunning \'command\':\n\033[0m'),
            mock.call('first\n'),
            mock.call('second\n')])


def test_run_env(
        container,
        client,
        env,
        logger,
        pull,
        push,
        run_command):
    """
    Test running an environment.

    The `run` entry in the envrionment should be passed to `run_command`.
    When the environment contains a `before` or `after` entry, `run_env`
    should be called with these entries.
    When the environment contains a `push` element, `push` should be called
    with this entry. When it contains a `pull` element, `pull` should be
    called with it.

    """
    with mock.patch('moby.run_env', wraps=moby.run_env) as run_env:
        moby.run_env(client, container, env, logger)

    run_command_calls = [
        mock.call(client, container, command, logger)
        for command in env['run']
    ]
    run_command.assert_has_calls(run_command_calls)

    run_env_calls = [
        mock.call(client, container, env, logger)
    ]
    if 'before' in env:
        run_env_calls.append(
            mock.call(client, container, env['before'], logger))
    if 'after' in env:
        run_env_calls.append(
            mock.call(client, container, env['after'], logger))
    run_env.assert_has_calls(run_env_calls)
    if 'push' in env:
        push.assert_called_once_with(client, container, env['push'], logger)
    if 'pull' in env:
        pull.assert_called_once_with(client, container, env['pull'], logger)


def test_start_container(
        client,
        logger):
    """
    Test starting a container.

    The client should be used to create a container using the image. The
    created container should be started using the client.

    """
    image = 'image'
    container = moby.start_container(client, image, logger)
    assert container == client.create_container.return_value
    client.create_container.assert_called_once_with(
        image,
        detach=True,
        entrypoint='cat',
        tty=True)
    client.start.assert_called_once_with(container)
    logger.info.assert_called_once_with(
        '\033[1mStarting container...\n\033[0m')


def test_stop_container(
        client,
        container,
        logger):
    """
    Test stopping a container.

    The client should be used to stop the container.

    """
    moby.stop_container(client, container, logger)
    client.stop.assert_called_once_with(container)
    logger.info.assert_called_once_with(
        '\033[1mStopping container...\n\033[0m')


def test_main(
        build_image,
        client,
        config,
        container,
        image,
        init_client,
        init_logger,
        load_config,
        logger,
        run_env,
        start_container,
        stop_container):
    """Test the main entrypoint."""
    moby.main()
    init_logger.assert_called_once_with()
    load_config.assert_called_once_with()
    init_client.assert_called_once_with()
    build_image.assert_called_once_with(client, logger)
    start_container.assert_called_once_with(client, image, logger)
    run_env.calls == [
        mock.call(client, container, config[env], logger)
        for env in config['envlist']
    ]
    stop_container.assert_called_once_with(client, container, logger)
