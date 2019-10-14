import pytest

from common.global_var import initGlobal
from environment.test_env_impl import TestEnvironment, create_env_impl


@pytest.fixture(scope="module")
def consensus_test_env(global_test_env):
    with open("/etc/passwd") as f:
        yield f.readlines()


def pytest_addoption(parser):
    parser.addoption("--nodeFile", action="store",  help="nodeFile: the node config file")
    parser.addoption("--accountFile", action="store", help="accountFile: the accounts file")
    parser.addoption("--initChain", action="store_true", default=False, dest="initChain", help="nodeConfig: default to init chain data")
    parser.addoption("--startAll", action="store_true", default=False, dest="startAll", help="startAll: default to start all nodes")
    parser.addoption("--httpRpc", action="store_true", default=False, dest="httpRpc", help="httpRpc: default to HTTP PRC")
    parser.addoption("--installDependency", action="store_true", default=False, dest="installDependency", help="installDependency: default do not install dependencies")
    parser.addoption("--installSuperVisor", action="store_true", default=False, dest="installSuperVisor", help="installSuperVisor: default do not install supervisor service")

# py.test test_start.py -s --concmode=asyncnet --nodeFile "deploy/4_node.yml" --accountFile "deploy/accounts.yml" --initChain --startAll --httpRpc
@pytest.fixture(scope="session", autouse=False)
def global_test_env(request):
    initGlobal()

    nodeFile = request.config.getoption("--nodeFile")
    accountFile = request.config.getoption("--accountFile")
    initChain = request.config.getoption("--initChain")
    _ = request.config.getoption("--startAll")
    _ = request.config.getoption("--httpRpc")
    installDependency = request.config.getoption("--installDependency")
    installSuperVisor = request.config.getoption("--installSuperVisor")

    env = create_env_impl(nodeFile, accountFile, init_chain=initChain, install_supervisor=installDependency, install_dependency=installSuperVisor)

    yield env

    #todo
    #env.shutdown()


