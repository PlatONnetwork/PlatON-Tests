# -*- coding: utf-8 -*-
import time
from common.load_file import LoadFile
import json
import random
import string
from hexbytes import HexBytes


def get_blockhash(node, blocknumber=None):
    '''
    根据块高获取块hash
    :param node:
    :param blocknumber:
    :return:
    '''
    if not blocknumber:
        blocknumber = node.blockNumber
    blockinfo = node.eth.getBlock(blocknumber)
    blockhash = blockinfo.get('hash')
    blockhash = HexBytes(blockhash).hex()
    return blockhash

def int_to_bytes(value):
    return int(value).to_bytes(length=4, byteorder='big', signed=False)

def stop_node_by_node_id(node_list, nodeid):
    """
    根据节点id停止节点进程
    :param node_list: 节点列表
    :param nodeid:
    :return:
    """
    for node in node_list:
        if node.node_id == nodeid:
            node.stop()


def compare_two_dict(dict1, dict2, key_list=None):
    """
    比较两个字典value
    :param dict1:
    :param dict2:
    :param key_list: 比对字典key列表
    :return:
    """
    if key_list is None:
        key_list = ['blockNumber', 'amount']
    flag = True
    keys1 = dict1.keys()
    keys2 = dict2.keys()
    if len(key_list) != 0:
        for key in key_list:
            if key in keys1 and key in keys2:
                if dict1[key] == dict2[key]:
                    flag = True
                else:
                    flag = False
            else:
                raise Exception('key_list contains error key')
    else:
        raise Exception('key_list is null')
    return flag


def get_nodeinfo_by_id(node_config_list, nodeid):
    """
    根据节点ID查询节点信息
    :param node_config_list:
    :param nodeid:
    :return:
    """
    for node_config in node_config_list:
        if node_config["id"] == nodeid:
            return node_config
    return


def get_no_pledge_info(node_list):
    """
    获取未被质押的节点ID
    :return:
    """
    for node in node_list:
        result = node.web3.ppos.getCandidateInfo(node.node_id)
        if result['Code'] == 301204:
            return node
    return


def get_pledgelist(func):
    validator_info = func().get('Data')
    validator_list = []
    for info in validator_info:
        validator_list.append(info.get('NodeId'))
    return validator_list


def get_node_in_pledgelist(nodeid, func):
    """
    查看节点是否在列表中
    :param nodeid: 节点id
    :param func: 查询方法，1、当前质押节点列表 2、当前共识节点列表 3、实时验证人列表
    :return:
    """
    data_dict = func()
    for data in data_dict["Data"]:
        if data["NodeId"] == nodeid:
            return True
    return False


def get_param_by_file(*args, filename):
    """
    根据配置文件查询参数值
    :param args: 键
    :param filename: 配置文件路径
    :return:
    """
    dict_data = LoadFile(filename).get_data()
    return get_param_by_dict(dict_data, *args)


def get_param_by_dict(data, *args):
    """
    根据json数据查询参数值
    :param data: j字典
    :param args: 键
    :return:
    """
    i = 0
    if isinstance(data, dict):
        for key in args:
            data = data.get(key)
            i = i + 1
            if isinstance(data, dict) and i > len(args):
                raise Exception("输入的参数有误。")
        return data

    raise Exception("数据格式错误")


def update_param_by_file(key1, key2, key3, value, filename, newfilename):
    """
    修改config配置参数
    :param key1:
    :param key2:
    :param key3:
    :param value:
    :param filename:
    :param newfilename:
    :return:
    """
    data = LoadFile(filename).get_data()
    if key3 is None:
        data[key1][key2] = value
    else:
        data[key1][key2][key3] = value
    with open(newfilename, "w") as f:
        f.write(json.dumps(data, indent=4))


def update_param_by_dict(data, key1, key2, key3, value):
    """
    修改json参数
    :param data:
    :param key1:
    :param key2:
    :param key3:
    :param value:
    :return:
    """
    if isinstance(data, dict):
        if key3 is None:
            data[key1][key2] = value
        else:
            data[key1][key2][key3] = value
        return data
    return


def update_validator(genesis, node_num):
    """
    配置共识验证人数量和当前结算周期验证人数量
    :return:
    """
    tmp_data = update_param_by_dict(genesis, 'EconomicModel', 'Common', 'ValidatorCount', node_num)
    return update_param_by_dict(tmp_data, 'EconomicModel', 'Staking', 'EpochValidatorNum', node_num + 1)


def update_genesis(genesis):
    # 修改ppos参数
    tmp_data = update_param_by_dict(genesis, 'EconomicModel', 'Staking', 'StakeThreshold', 5000000000000000000000000)
    tmp_data = update_param_by_dict(tmp_data, 'EconomicModel', 'Slashing', 'PackAmountAbnormal', 2)
    tmp_data = update_param_by_dict(tmp_data, 'EconomicModel', 'Staking', 'UnStakeFreezeRatio', 1)
    return update_param_by_dict(tmp_data, 'EconomicModel', 'Slashing', 'EvidenceValidEpoch', 27)


def wait_block_number(node, block, interval=1):
    current_block = node.block_number
    timeout = int((block - current_block) * interval * 1.5) + int(time.time())
    while int(time.time()) < timeout:
        if node.block_number > block:
            break
        time.sleep(1)
    raise Exception("无法正常出块")


def get_validator_term(node):
    """
    获取任期最大的nodeID
    """
    msg = node.ppos.getValidatorList()
    term = []
    nodeid = []
    for i in msg["Data"]:
        term.append(i["ValidatorTerm"])
        nodeid.append(i["NodeId"])
    max_term = (max(term))
    term_nodeid_dict = dict(zip(term, nodeid))
    return term_nodeid_dict[max_term]


def get_max_staking_tx_index(node):
    """
    获取最大的交易索引的nodeID
    """
    msg = node.ppos.getValidatorList()
    staking_tx_index_list = []
    nodeid = []
    for i in msg["Data"]:
        staking_tx_index_list.append(i["StakingTxIndex"])
        nodeid.append(i["NodeId"])
    max_staking_tx_index = (max(staking_tx_index_list))
    term_nodeid_dict = dict(zip(staking_tx_index_list, nodeid))
    return term_nodeid_dict[max_staking_tx_index]

def gen_random_string(length):
    '''
    获取指定生成位数的随机数包含字母和数字
    :param length:
    :return: string
    '''
    len = length
    # 随机产生指定个数的字符
    num_of_numeric = random.randint(1, len - 1)

    # 剩下的都是字母
    num_of_letter = len - num_of_numeric

    # 随机生成数字
    numerics = [random.choice(string.digits) for i in range(num_of_numeric)]

    # 随机生成字母
    letters = [random.choice(string.ascii_letters) for i in range(num_of_letter)]

    # 结合两者
    all_chars = numerics + letters

    # 对序列随机排序
    random.shuffle(all_chars)

    # 生成最终字符串
    result = ''.join([i for i in all_chars]).lower()

    return result