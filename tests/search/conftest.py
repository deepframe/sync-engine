from tests.util.base import config, db, log, absolute_path


def pytest_generate_tests(metafunc):
    if 'db' in metafunc.fixturenames:
        dumpfile = absolute_path(config()['BASE_DUMP'])
        savedb = False

        metafunc.parametrize('db', [(dumpfile, savedb)], indirect=True)
