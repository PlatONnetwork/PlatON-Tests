import pytest

from common.global_var import initGlobal
from environment.test_env_impl import TestEnvironment
from common import download
from common.log import log

from conf.settings import PLATON_BIN_FILE



@pytest.fixture(scope="module")
def consensus_test_env(global_test_env):
    with open("/etc/passwd") as f:
        yield f.readlines()


def pytest_addoption(parser):
    parser.addoption("--platon_url", action="store",  help="platon_url: url to download platon bin")
    parser.addoption("--nodeFile", action="store",  help="nodeFile: the node config file")
    parser.addoption("--accountFile", action="store", help="accountFile: the accounts file")
    parser.addoption("--initChain", action="store_true", default=False, dest="initChain", help="nodeConfig: default to init chain data")
    parser.addoption("--startAll", action="store_true", default=False, dest="startAll", help="startAll: default to start all nodes")
    parser.addoption("--installDependency", action="store_true", default=False, dest="installDependency", help="installDependency: default do not install dependencies")
    parser.addoption("--installSuperVisor", action="store_true", default=False, dest="installSuperVisor", help="installSuperVisor: default do not install supervisor service")

# py.test test_start.py -s --concmode=asyncnet --nodeFile "deploy/4_node.yml" --accountFile "deploy/accounts.yml" --initChain --startAll
@pytest.fixture(scope="session", autouse=True)
def global_test_env(request):

    log.info("global_test_env>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    nodeFile = request.config.getoption("--nodeFile")
    accountFile = request.config.getoption("--accountFile")
    initChain = request.config.getoption("--initChain")
    startAll = request.config.getoption("--startAll")
    installDependency = request.config.getoption("--installDependency")
    installSuperVisor = request.config.getoption("--installSuperVisor")
    plant_url = request.config.getoption("--platon_url")
    if plant_url:
        download.download_platon(plant_url)
    env = create_env_impl(PLATON_BIN_FILE, nodeFile,'global', accountFile, initChain, startAll, installDependency, installSuperVisor)


    yield env

    #todo
    #env.shutdown()

'''
@pytest.fixture(scope="function")
def custom_test_env():
    def _custom_test_env(conf):
        _ = conf.get("binFile")
        nodeFile = conf.get("nodeFile")
        genesisFile = conf.get("genesisFile")
        accountFile = conf.get("accountFile")
        initChain = conf.get("initChain")
        _ = conf.get("startAll")
        _ = conf.get("isHttpRpc")
        return create_env_impl(node_file=nodeFile, account_file=accountFile, init_chain=initChain)
    yield _custom_test_env
   # _custom_test_env.shutdown()
'''



def create_env_impl(binfile, nodeFile, confdir, accountFile,initChain=True, startAll=True, installDependency=False, installSuperVisor=False)->TestEnvironment:
    env = TestEnvironment(node_file=nodeFile, bin_file=binfile, confdir=confdir, account_file=accountFile, init_chain=initChain, startAll=startAll, 
    install_dependency=installDependency, install_supervisor=installSuperVisor)
    print(env.install_dependency)
    print(env.install_supervisor)
    env.deploy_all()
    env.start_all()
    return env

