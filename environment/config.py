from common.abspath import abspath
from conf import settings as conf
from conf.settings import ConfTmpDir


class TestConfig:
    def __init__(self, conf_tmp: ConfTmpDir, install_supervisor=True, install_dependency=True, init_chain=True, is_need_static=True):
        # 本地必须文件
        self.platon_bin_file = conf.PLATON_BIN_FILE
        self.genesis_file = conf.GENESIS_FILE
        self.supervisor_file = conf.SUPERVISOR_FILE
        self.node_file = conf.NODE_FILE
        self.address_file = conf.ADDRESS_FILE
        self.account_file = conf.ACCOUNT_FILE
        self.config_json_file = conf.CONFIG_JSON_FILE
        # 本地缓存目录
        self.root_tmp = conf_tmp.tmp_root_path
        self.node_tmp = conf_tmp.LOCAL_TMP_FILE_FOR_NODE
        self.server_tmp = conf_tmp.LOCAL_TMP_FILE_FOR_SERVER
        self.env_tmp = conf_tmp.LOCAL_TMP_FILE_FOR_ENV
        self.genesis_tmp = conf_tmp.GENESIS_FILE
        self.static_node_tmp = conf_tmp.STATIC_NODE_FILE
        self.config_json_tmp = conf_tmp.CONFIG_JSON_FILE

        # 服务器依赖安装
        self.install_supervisor = install_supervisor
        self.install_dependency = install_dependency

        # 链部署定制
        self.init_chain = init_chain
        self.is_need_static = is_need_static
        self.log_level = 4
        self.syncmode = "full"
        self.append_cmd = ""

        # 最大线程数
        self.max_worker = 30

        # 环境id
        self.env_id = None

        # 服务器远程目录
        self.deploy_path = conf.DEPLOY_PATH
        self.remote_supervisor_tmp = "{}/tmp/supervisor/".format(self.deploy_path)
        self.remote_compression_tmp_path = "{}/tmp/env/".format(self.deploy_path)

        # 日志相关
        self.bug_log = abspath("./bug_log")
        self.tmp_log = abspath("./tmp_log")