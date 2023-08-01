import json
import os
import time
import datetime
from dateutil import tz
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.JoinSecurityGroupRequest import JoinSecurityGroupRequest
import logging

from aliyunsdkcore import client
from aliyunsdkecs.request.v20140526.RunInstancesRequest import RunInstancesRequest
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkecs.request.v20140526 import (
    CreateInstanceRequest,
    AllocatePublicIpAddressRequest,
    StartInstanceRequest,
    DescribeInstancesRequest,
    ModifyInstanceAutoReleaseTimeRequest,
)
import requests
import re
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest


# 实例的资源规格
instance_type = 'ecs.u1-c1m8.large'
# 实例的计费方式
instance_charge_type = 'PostPaid'
# 是否为I/O优化实例
io_optimized = 'optimized'
# 后付费实例的抢占策略
spot_strategy = 'SpotAsPriceGo'
# 系统盘大小
system_disk_size = '40'
# 系统盘的磁盘种类
system_disk_category = 'cloud_essd'
# 性能级别
system_disk_performance_level = 'PL0'

# 要加入的安全组列表
security_group_ids = ["sg-8vbap91nk99v1ypw280a"]


vswitch_id = "vsw-8vbi4ohmz5c1nsoasmnkl"
image_ids = [
    # 注意这里镜像对应的顺序


    "m-8vb7wngs19qmgbakig6r",  # hadoop102
    "m-8vbdbtsinp5isj43k0bp",  # hadoop103
    "m-8vb5b1bouhav6de5gqtb"  # hadoop104

]

# 配置访问密钥和密钥ID
ACCESS_KEY_ID = os.environ.get('ACCESS_KEY_ID')
ACCESS_SECRET = os.environ.get('ACCESS_SECRET')

# 设置地区
region_id = "cn-zhangjiakou"

# 初始化客户端
client = AcsClient(ACCESS_KEY_ID, ACCESS_SECRET, region_id)

# 镜像和实例名称对应关系
image_to_instance_name_map = {
    image_ids[0]: "hadoop102",
    image_ids[1]: "hadoop103",
    image_ids[2]: "hadoop104"
}

# 内网地址和实例对应关系
image_to_private_ip_map = {
    image_ids[0]: "172.29.16.12",
    image_ids[1]: "172.29.16.13",
    image_ids[2]: "172.29.16.14"
}

# 实例列表
created_instance_ids = []

# 确保实例正常运行，在进行分配公网等操作，避免出现没有资源的情况。


def wait_instance_running(instance_id):
    while True:
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_accept_format("json")
        request.set_InstanceIds(json.dumps([instance_id]))

        response = client.do_action_with_exception(request)
        response_dict = json.loads(response)

        if ("Instances" in response_dict
                and "Instance" in response_dict["Instances"]
                and len(response_dict["Instances"]["Instance"]) > 0):
            instance = response_dict["Instances"]["Instance"][0]
            if instance["Status"] == "Running":
                print(f"Instance {instance_id} is running.")
                break
            else:
                print(
                    f"Instance {instance_id} is {instance['Status']}. Waiting..."
                )
        else:
            print("Unexpected response:", response_dict)

        time.sleep(10)


# 创建实例
def create_instance(image_id, instance_name):
    request = RunInstancesRequest()
    request.set_accept_format("json")
    request.set_InstanceType(instance_type)
    request.set_ImageId(image_id)
    request.set_SecurityGroupId(security_group_ids[0])
    request.set_VSwitchId(vswitch_id)
    request.set_InstanceName(instance_name)
    request.set_PrivateIpAddress(image_to_private_ip_map[image_id])
    request.set_InternetMaxBandwidthOut(100)  # set to an appropriate value


    # 设置云盘类型
    request.set_SystemDiskCategory("cloud_ssd")
    request.set_SystemDiskSize(40)

    # 付费模式: 抢占式实例
    request.set_InstanceChargeType("PostPaid")
    # 单台实例规格上限价: 使用自动出价
    request.set_SpotStrategy("SpotWithPriceLimit")



    try:
        response = client.do_action_with_exception(request)
        response_dict = json.loads(response)
        if 'InstanceIdSets' in response_dict and 'InstanceIdSet' in response_dict[
                'InstanceIdSets']:
            return response_dict["InstanceIdSets"]["InstanceIdSet"][0]
        else:
            print("Unexpected response:", response_dict)
            return None
    except ServerException as e:
        print("Create instance failed: ", e.get_error_msg())


# 启动实例
def start_instance(instance_id):
    request = StartInstanceRequest.StartInstanceRequest()
    request.set_accept_format("json")
    request.set_InstanceId(instance_id)

    try:
        response = client.do_action_with_exception(request)
    except ServerException as e:
        print("Start instance failed: ", e.get_error_message())


# 分配公网 IP
def allocate_public_ip(instance_id):
    request = AllocatePublicIpAddressRequest.AllocatePublicIpAddressRequest()
    request.set_accept_format("json")
    request.set_InstanceId(instance_id)

    try:
        response = client.do_action_with_exception(request)
        response_dict = json.loads(response)
        return response_dict["IpAddress"]
    except ServerException as e:
        print("Allocate public IP failed: ", e.get_error_message())


# 添加安全组
def add_security_group(instance_id, security_group_id):
    request = JoinSecurityGroupRequest()
    request.set_accept_format("json")
    request.set_InstanceId(instance_id)
    request.set_SecurityGroupId(security_group_id)

    try:
        response = client.do_action_with_exception(request)
    except ServerException as e:
        print("Add security group failed: ", e.get_error_message())


if __name__ == "__main__":
    # 创建并启动实例
    for image_id in image_ids:
        instance_name = image_to_instance_name_map[image_id]
        print("Creating instance:", instance_name)
        instance_id = create_instance(image_id, instance_name)
        created_instance_ids.append(instance_id)

    print("Created instances:", created_instance_ids)

    # 等待所有实例运行
    for instance_id in created_instance_ids:
        print("Waiting for instance {} to be running...".format(instance_id))
        wait_instance_running(instance_id)


    # 分配公网 IP
    def allocate_public_ip(instance_id):
        request = AllocatePublicIpAddressRequest.AllocatePublicIpAddressRequest()
        request.set_accept_format("json")
        request.set_InstanceId(instance_id)

        try:
            response = client.do_action_with_exception(request)
            response_dict = json.loads(response)
            return response_dict["IpAddress"]
        except ServerException as e:
            print("Allocate public IP failed: ", e.get_error_msg())


        # 添加安全组
        for security_group_id in security_group_ids[1:]:
            print("Adding security group", security_group_id, "to instance",
                  instance_id)
            add_security_group(instance_id, security_group_id)

    print("Finished!")
