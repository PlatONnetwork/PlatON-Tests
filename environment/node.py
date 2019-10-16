
from common.connect import connect_web3, connect_linux, runCMDBySSH

from conf.settings import DEPLOY_PATH,PLATON_BIN_FILE,SUPERVISOR_TEMPLATE_FILE
import os
from common.log import log
import configparser
from client_sdk_python import HTTPProvider, Web3, WebsocketProvider



TMP_LOG = "./tmp_log"
LOG_PATH = "./bug_log"

class Node:
    def __init__(self,conf,node_conf):
        self.data_tmp_dir = None
        self.supervisor_service_id = None
        self.supervisor_conf_file_name = None
        self.id = node_conf.get("id")
        self.host = node_conf.get("host")
        self.port = node_conf.get("port")
        self.rpcport = node_conf.get("rpcport")
        self.username = node_conf.get("username")
        self.password = node_conf.get("password")
        self.blsprikey = node_conf.get("blsprikey")
        self.blspubkey = node_conf.get("blspubkey")
        self.nodekey = node_conf.get("nodekey")
        self.remoteDeployDir = node_conf.get("deplayDir")
        if not self.remoteDeployDir:
            self.remoteDeployDir = DEPLOY_PATH
        self.syncMode = node_conf.get("syncmode")
        self.rpctype = node_conf.get("rpctype")
        self.conf = conf
        self.remoteDeployDir = '{}/node-{}'.format(self.remoteDeployDir, self.port)
        self.remoteDataDir = '{}/data'.format(self.remoteDeployDir)
        self.remoteBinFile = '{}/platon'.format(self.remoteDeployDir)
        self.remoteGenesisFile = '{}/genesis.json'.format(self.remoteDeployDir)
        self.remoteConfigFile = '{}/config.json'.format(self.remoteDeployDir)
        self.remoteBlskeyFile = '{}/blskey'.format(self.remoteDataDir)
        self.remoteNodekeyFile = '{}/nodekey'.format(self.remoteDataDir)
        self.remoteStaticNodesFile = '{}/static-nodes.json'.format(self.remoteDeployDir)


        self.tmp_root_dir = os.path.join(self.conf.LOCAL_TMP_FILE_ROOT_DIR,"{}_{}".format(self.host, self.port))  # 生成的各个节点的data/supervesor数据，存放子目录
        self.supervisor_tmp_dir = os.path.join(self.tmp_root_dir, "supervisor")
        self.data_tmp_dir = os.path.join(self.tmp_root_dir, "data")
        self.supervisor_service_id = "node-" + str(self.port)  # supervisor服务启停节点的 ID
        self.supervisor_conf_file_name = "node-" + str(self.port) + ".conf"  # 生成的各个节点的supervesor配置文件名称

    def getEnodeUrl(self):
        return r"enode://" + self.id + "@" + self.host + ":" + str(self.port)

    def connect_node(self):
        url = "{}://{}:{}".format(self.rpctype, self.host, self.rpcport)
        collusion_w3 = connect_web3(url)
        return collusion_w3


    def generate_supervisor_node_conf_file(self):
        """
        生成supervisor部署platon的配置
        :param node:
        :return:
        """
        if not os.path.exists(self.supervisor_tmp_dir):
            os.makedirs(self.supervisor_tmp_dir)

        supervisorConfFile = self.supervisor_tmp_dir + "/" + self.supervisor_conf_file_name

        with open(supervisorConfFile, "w") as fp:
            fp.write("[program:" + self.supervisor_service_id + "]\n")
            cmd = "{}/platon --identity platon --datadir {}".format(self.remoteDeployDir, self.remoteDataDir)
            cmd = cmd + " --port {}".format(self.port)

            cmd = cmd + " --syncmode '{}'".format(self.syncMode)
            # if self.netType:
            #     cmd = cmd + " --" + self.netType

            # if node.get("mpcactor", None):
            #     cmd = cmd + " --mpc --mpc.actor {}".format(node.get("mpcactor"))
            # if node.get("vcactor", None):
            #     cmd = cmd + \
            #           " --vc --vc.actor {} --vc.password 88888888".format(
            #               node.get("vcactor"))

            cmd = cmd + " --debug --verbosity 5"
            if self.rpctype == "http":
                cmd = cmd + " --rpc --rpcaddr 0.0.0.0 --rpcport " + str(self.rpcport)
                cmd = cmd + " --rpcapi platon,debug,personal,admin,net,web3"
            else:
                cmd = cmd + " --ws --wsorigins '*' --wsaddr 0.0.0.0 --wsport " + str(self.rpcport)
                cmd = cmd + " --wsapi eth,debug,personal,admin,net,web3"

            cmd = cmd + " --txpool.nolocals"

            # 监控指标
            # if self.is_metrics:
            #     cmd = cmd + " --metrics"
            #     cmd = cmd + " --metrics.influxdb --metrics.influxdb.endpoint http://10.10.8.16:8086"
            #     cmd = cmd + " --metrics.influxdb.database platon"
            #     cmd = cmd + " --metrics.influxdb.host.tag {}:{}".format(self.host, str(self.port))

            cmd = cmd + " --gcmode archive --nodekey {}".format(self.remoteNodekeyFile)
            #cmd = cmd + " --config {}".format(self.remoteConfigFile)
            cmd = cmd + " --cbft.blskey {}".format(self.remoteBlskeyFile)

            fp.write("command=" + cmd + "\n")


            # go_fail_point = ""
            # if node.get("fail_point", None):
            #     go_fail_point = " GO_FAILPOINTS='{}' ".format(
            #         node.get("fail_point", None))
            # if go_fail_point:
            #     fp.write("environment=LD_LIBRARY_PATH={}/mpclib,{}\n".format(pwd, go_fail_point))
            # else:
            #     fp.write("environment=LD_LIBRARY_PATH={}/mpclib\n".format(pwd))

            fp.write("numprocs=1\n")
            fp.write("autostart=false\n")
            fp.write("startsecs=3\n")
            fp.write("startretries=3\n")
            fp.write("autorestart=unexpected\n")
            fp.write("exitcode=0\n")
            fp.write("stopsignal=TERM\n")
            fp.write("stopwaitsecs=10\n")
            fp.write("redirect_stderr=true\n")
            fp.write("stdout_logfile={}/log/platon.log\n".format(self.remoteDeployDir))
            fp.write("stdout_logfile_maxbytes=200MB\n")
            fp.write("stdout_logfile_backups=20\n")
            fp.close()

    def generateKeyFiles(self):
        if not os.path.exists(self.data_tmp_dir):
            os.makedirs(self.data_tmp_dir)
        blskey_file = os.path.join(self.data_tmp_dir, "blskey")
        with open(blskey_file, 'w', encoding="utf-8") as f:
            f.write(self.blsprikey)
            f.close()

        nodekey_file = os.path.join(self.data_tmp_dir, "nodekey")
        with open(nodekey_file, 'w', encoding="utf-8") as f:
            f.write(self.nodekey)
            f.close()


    def initNode(self):
        # connect_ssh
        self.ssh, self.sftp, self.transport = connect_linux(self.host, self.username, self.password, 22)

        pwd_list = runCMDBySSH(self.ssh, "pwd")
        pwd = pwd_list[0].strip("\r\n")

        if not os.path.isabs(self.remoteDeployDir):
            self.remoteDeployDir = pwd + "/" + self.remoteDeployDir
            self.remoteDataDir = pwd + "/" + self.remoteDataDir
            self.remoteBinFile = pwd + "/" + self.remoteBinFile
            self.remoteNodekeyFile = pwd + "/" + self.remoteNodekeyFile
            self.remoteBlskeyFile = pwd + "/" + self.remoteBlskeyFile


    def start(self, initChain):
        log.info("to stop PlatON {}:{}".format(self.host,self.port))
        self.stop()

        if initChain:
            log.info("to init PlatON chain")
            self.initPlatON()

        runCMDBySSH(self.ssh, "sudo -S -p '' supervisorctl update " + self.supervisor_service_id, self.password)
        runCMDBySSH(self.ssh, "sudo -S -p '' supervisorctl start " + self.supervisor_service_id, self.password)


    def clean(self):
        #time.sleep(0.5)
        runCMDBySSH(self.ssh, "sudo -S -p '' rm -rf {}".format(self.remoteDeployDir), self.password)
        runCMDBySSH(self.ssh, "mkdir -p {}".format(self.remoteDeployDir))
        runCMDBySSH(self.ssh, "mkdir -p {}".format(self.remoteDataDir))
        runCMDBySSH(self.ssh, 'mkdir -p {}/log'.format(self.remoteDeployDir))

    def clean_log(self):
        runCMDBySSH(self.ssh, "rm -rf {}/nohup.out".format(self.remoteDeployDir))
        runCMDBySSH(self.ssh, "rm -rf {}/log".format(self.remoteDeployDir))
        runCMDBySSH(self.ssh, 'mkdir -p {}/log'.format(self.remoteDeployDir))


    """
    以kill的方式停止节点，关闭后节点可以重启
    """
    def stop(self):
        log.info("关闭platon进程...")
        runCMDBySSH(self.ssh, "sudo -S -p '' supervisorctl stop {}".format(self.supervisor_service_id), self.password)

    def uploadAllFiles(self):
        log.info("uploadAllFiles:::::::::: {}".format(self.host))
        self.uploadBinFile()
        self.uploadGenesisFile()
        self.uploadStaticNodeFile()
        self.uploadConfigFile()
        self.uploadKeyFiles()
        self.upload_supervisor_node_conf_file()

    def uploadBinFile(self):
        if PLATON_BIN_FILE and os.path.exists(PLATON_BIN_FILE):
            remoteFile = os.path.join(self.remoteDeployDir, "platon").replace("\\", "/")
            self.sftp.put(PLATON_BIN_FILE, remoteFile)
            runCMDBySSH(self.ssh, 'chmod +x {}'.format(remoteFile))
            log.info("platon bin file uploaded to node: {}".format(self.host))
        else:
            log.error("platon bin file not found: {}".format(PLATON_BIN_FILE))

    def uploadGenesisFile(self):
        if self.conf.GENESIS_FILE and os.path.exists(self.conf.GENESIS_FILE):
            remoteFile = os.path.join(self.remoteDeployDir, "genesis.json").replace("\\", "/")
            self.sftp.put(self.conf.GENESIS_FILE, remoteFile)
            log.info("genesis.json uploaded to node: {}".format(self.host))
        else:
            log.warn("genesis.json not found: {}".format(self.conf.GENESIS_FILE))


    def uploadStaticNodeFile(self):
        if self.conf.STATIC_NODE_FILE and os.path.exists(self.conf.STATIC_NODE_FILE):
            remoteFile = os.path.join(self.remoteDeployDir, "static-nodes.json").replace("\\", "/")
            self.sftp.put(self.conf.STATIC_NODE_FILE, remoteFile)
            log.info("static-nodes.json uploaded to node: {}".format(self.host))
        else:
            log.warn("static-nodes.json not found: {}".format(self.conf.STATIC_NODE_FILE))

    def uploadConfigFile(self):
        if self.conf.CONFIG_JSON_FILE and os.path.exists(self.conf.CONFIG_JSON_FILE):
            remoteFile = os.path.join(self.remoteDeployDir, "config.json").replace("\\", "/")
            self.sftp.put(self.conf.CONFIG_JSON_FILE, remoteFile)
            log.info("config.json uploaded to node: {}".format(self.host))
        else:
            log.warn("config.json not found: {}".format(self.conf.CONFIG_JSON_FILE))



    def uploadKeyFiles(self):
        blskey_file = os.path.join(self.data_tmp_dir, "blskey")
        if os.path.exists(blskey_file):
            remoteFile = os.path.join(self.remoteDataDir, "blskey").replace("\\", "/")
            self.sftp.put(blskey_file, remoteFile)
            log.info("blskey uploaded to node: {}".format(self.host))

        nodekey_file = os.path.join(self.data_tmp_dir, "nodekey")
        if os.path.exists(nodekey_file):
            remoteFile = os.path.join(self.remoteDataDir, "nodekey").replace("\\", "/")
            self.sftp.put(nodekey_file, remoteFile)
            log.info("nodekey_file uploaded to node: {}".format(self.host))

    def upload_supervisor_node_conf_file(self):
        supervisorConfFile = self.supervisor_tmp_dir + "/" + self.supervisor_conf_file_name
        if os.path.exists(supervisorConfFile):
            runCMDBySSH(self.ssh, "rm -rf /tmp/{}".format(self.supervisor_conf_file_name))
            runCMDBySSH(self.ssh, "mkdir  /tmp")
            self.sftp.put(supervisorConfFile, "/tmp/{}".format(self.supervisor_conf_file_name))
            runCMDBySSH(self.ssh, "sudo -S -p '' cp /tmp/" + self.supervisor_conf_file_name + " /etc/supervisor/conf.d", self.password)
            log.info("supervisor startup config uploaded to node: {}".format(self.host))

    def backupLog(self):
        runCMDBySSH(self.ssh, "cd {};tar zcvf log.tar.gz ./log".format(self.remoteDeployDir))
        self.sftp.get("{}/log.tar.gz".format(self.remoteDeployDir), "{}/{}_{}.tar.gz".format(TMP_LOG, self.host, self.port))
        runCMDBySSH(self.ssh, "cd {};rm -rf ./log.tar.gz".format(self.remoteDeployDir))
        # self.transport.close()


    def genSupervisorConf(self):
        """
        更新supervisor配置
        :param node:
        :param sup_template:
        :param sup_tmp:
        :return:
        """
        template = configparser.ConfigParser()
        template.read(SUPERVISOR_TEMPLATE_FILE)
        template.set("inet_http_server", "username", self.username)
        template.set("inet_http_server", "password", self.password)
        template.set("supervisorctl", "username", self.username)
        template.set("supervisorctl", "password", self.password)

        with open(self.conf.SUPERVISOR_FILE, "w") as file:
            template.write(file)
            file.close()
        return self.conf.SUPERVISOR_FILE

    def judge_restart_supervisor(self, supervisor_pid_str):
        supervisor_pid = supervisor_pid_str[0].strip("\n")


        result = runCMDBySSH(self.ssh, "sudo -S -p '' supervisorctl stop {}".format(self.supervisor_service_id), self.password)

        if "node-{}".format(self.port) not in result[0]:

            runCMDBySSH(self.ssh, "sudo -S -p '' kill {}".format(supervisor_pid), self.password)
            runCMDBySSH(self.ssh, "sudo -S -p '' killall supervisord", self.password)
            runCMDBySSH(self.ssh, "sudo -S -p '' sudo apt remove supervisor -y", self.password)
            runCMDBySSH(self.ssh, "sudo -S -p '' apt update", self.password)
            runCMDBySSH(self.ssh, "sudo -S -p '' apt install -y supervisor", self.password)
            runCMDBySSH(self.ssh, "sudo -S -p '' cp ./tmp/supervisord.conf /etc/supervisor/", self.password)
            runCMDBySSH(self.ssh, "sudo -S -p '' /etc/init.d/supervisor start", self.password)


    def install_dependency(self):
        """
        配置服务器依赖
        :param nodedict:
        :param file:
        :return:
        """
        runCMDBySSH(self.ssh, "sudo -S -p '' ntpdate 0.centos.pool.ntp.org", self.password)
        #pwd_list = runCMDBySSH(self.ssh, "pwd")
        #pwd = pwd_list[0].strip("\r\n")
        #cmd = r"sudo -S -p '' sed -i '$a /usr/local/lib' /etc/ld.so.conf".format(pwd)
        runCMDBySSH(self.ssh, "sudo -S -p '' apt install llvm g++ libgmp-dev libssl-dev -y", self.password)
        #runCMDBySSH(self.ssh, cmd, self.password)
        #runCMDBySSH(self.ssh, "sudo -S -p '' ldconfig", self.password)


    def initPlatON(self):
        #cmd = '{} --datadir {} --config {} init {}'.format(self.remoteBinFile, self.remoteDataDir, self.remoteConfigFile, self.remoteGenesisFile)
        cmd = '{} --datadir {} init {}'.format(self.remoteBinFile, self.remoteDataDir, self.remoteGenesisFile)
        runCMDBySSH(self.ssh, cmd)


    def deploy_supervisor(self):
        """
        部署supervisor
        :param node:
        :return:
        """
        log.info("call deploy_supervisor() for node: {}".format(self.host))
        tmpConf = self.genSupervisorConf()
        runCMDBySSH(self.ssh, "mkdir -p ./tmp")
        self.sftp.put(tmpConf, "./tmp/supervisord.conf")

        supervisor_pid_str = runCMDBySSH(self.ssh, "ps -ef|grep supervisord|grep -v grep|awk {'print $2'}")

        log.info("supervisor_pid_str: {}".format(supervisor_pid_str))

        if len(supervisor_pid_str) > 0:
            self.judge_restart_supervisor(supervisor_pid_str)
        else:
            log.info("judge_restart_supervisor......1111111111..........")
            runCMDBySSH(self.ssh, "sudo -S -p '' apt update", self.password)
            runCMDBySSH(self.ssh, "sudo -S -p '' apt install -y supervisor", self.password)
            runCMDBySSH(self.ssh, "sudo -S -p '' cp ./tmp/supervisord.conf /etc/supervisor/", self.password)
            supervisor_pid_str = runCMDBySSH(self.ssh, "ps -ef|grep supervisord|grep -v grep|awk {'print $2'}")
            if len(supervisor_pid_str) > 0:
                log.info("judge_restart_supervisor......3333333333..........")
                self.judge_restart_supervisor(supervisor_pid_str)
            else:
                runCMDBySSH(self.ssh, "sudo -S -p '' /etc/init.d/supervisor start", self.password)


    def w3_connector(self, is_http = True):
        if is_http:
            url = "http://" + self.host + ':' + str(self.rpcport)
            w3 = Web3(HTTPProvider(url))
        else:
            url = "ws://" + self.host + ':' + str(self.rpcport)
            w3 = Web3(WebsocketProvider(url))
        return w3