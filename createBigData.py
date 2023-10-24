#!/usr/bin/env python
# coding=utf-8
import json
import os
import time
import traceback
from datetime import datetime, timedelta
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkecs.request.v20140526.RunInstancesRequest import RunInstancesRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest

RUNNING_STATUS = 'Running'
CHECK_INTERVAL = 3
CHECK_TIMEOUT = 180

# 自动释放
release_time = datetime.utcnow() + timedelta(hours=4)

image_ids = [
    "m-8vb00hvct8u7i75y2856",  # hadoop102
    "m-8vbh0v3t5jgxluq0x32i",  # hadoop103
    "m-8vb6to1o71lzvzc5x6gu"  # hadoop104,
]

class AliyunRunInstancesExample(object):

    def __init__(self):
        self.access_id = os.environ.get('ACCESS_KEY_ID')
        self.access_secret = os.environ.get('ACCESS_SECRET')

        # 镜像和实例名称对应关系
        self.image_to_instance_name_map = {
            image_ids[0]: "hadoop102",
            image_ids[1]: "hadoop103",
            image_ids[2]: "hadoop104"
        }

        # 内网地址和实例对应关系
        self.image_to_private_ip_map = {
            image_ids[0]: "172.29.16.12",
            image_ids[1]: "172.29.16.13",
            image_ids[2]: "172.29.16.14"
        }

        # 是否只预检此次请求。true：发送检查请求，不会创建实例，也不会产生费用；false：发送正常请求，通过检查后直接创建实例，并直接产生费用
        self.dry_run = False
        # 实例所属的地域ID
        self.region_id = 'cn-zhangjiakou'
        # 实例的资源规格
        # ecs.u1-c1m8.large     这个实例的性能高
        self.instance_type = 'ecs.u1-c1m8.large'
        # 实例的计费方式
        self.instance_charge_type = 'PostPaid'
        # 指定新创建实例所属于的安全组ID
        # self.security_group_id = 'sg-8vbap91nk99v1ypw280a' # 这个比较安全, 没有开 10000端口
        self.security_group_id = 'sg-8vbj0mxp8vz2qwc5hpy0' # 这个不安全, 打开了所有的大数据常用端口, 容易被挖矿



        # 购买资源的时长
        self.period = 1
        # 购买资源的时长单位
        self.period_unit = 'Hourly'
        # 实例所属的可用区编号
        self.zone_id = 'random'
        # 网络计费类型
        self.internet_charge_type = 'PayByTraffic'
        # 虚拟交换机ID
        self.vswitch_id = 'vsw-8vbi4ohmz5c1nsoasmnkl'

        # 是否使用镜像预设的密码
        self.password_inherit = True
        # 指定创建ECS实例的数量
        self.amount = 1
        # 公网出带宽最大值
        self.internet_max_bandwidth_out = 100

        # 是否为I/O优化实例
        self.io_optimized = 'optimized'
        # 后付费实例的抢占策略
        self.spot_strategy = 'SpotAsPriceGo'
        # 系统盘大小
        self.system_disk_size = '40'
        # 系统盘的磁盘种类
        # cloud_efficiency      高效云盘
        # cloud_essd            弹性 ssd
        # cloud_ssd             普通 ssd
        self.system_disk_category = 'cloud_essd'

        # 性能级别,
        # 1. 使用 ESSD 的时候才可以选择,
        # 2. 并还需要把下面相关设置打开
        # 3. 选择这个的时候, 实例常常被自动释放, 改用普通 ssd
        self.system_disk_performance_level = 'PL1'

        self.client = AcsClient(self.access_id, self.access_secret, self.region_id)

    def get_public_ips(self, instance_ids):
        """
        获取实例的公网IP并打印
        :param instance_ids: 实例ID列表
        """
        request = DescribeInstancesRequest()
        request.set_InstanceIds(json.dumps(instance_ids))
        body = self.client.do_action_with_exception(request)
        data = json.loads(body)
        for instance in data['Instances']['Instance']:
            # 获取实例的公网IP
            public_ip_address = instance['PublicIpAddress']['IpAddress'][0]
            # 从实例中获取主机名
            hostname = instance['HostName']
            print(f"{public_ip_address} {hostname}")

    def run(self):
        try:
            # 初始化一个空列表来存储所有实例的ID
            all_instance_ids = []

            # 遍历每一个镜像ID
            for image_id in image_ids:
                # 获取与当前镜像ID对应的实例名称和私有IP地址
                self.instance_name = self.image_to_instance_name_map[image_id]
                self.private_ip_address = self.image_to_private_ip_map[image_id]
                # 设置当前的镜像ID
                self.image_id = image_id

                # 运行实例并获取实例ID
                ids = self.run_instances()

                # 将实例ID添加到所有实例ID的列表中
                all_instance_ids.extend(ids)

                # 检查实例的状态，直到所有实例都处于运行状态
                self._check_instances_status(ids)

            # 在所有实例创建并运行后，获取它们的公网IP
            self.get_public_ips(all_instance_ids)

        # 处理异常
        except ClientException as e:
            print('失败。与阿里云的连接出现问题。'
                  '代码：{code}，消息：{msg}'
                  .format(code=e.error_code, msg=e.message))
        except ServerException as e:
            print('失败。业务错误。'
                  '代码：{code}，消息：{msg}'
                  .format(code=e.error_code, msg=e.message))
        except Exception:
            print('未处理的错误')
            print(traceback.format_exc())

    def run_instances(self):
        """
        调用创建实例的API，得到实例ID后继续查询实例状态
        :return:instance_ids 需要检查的实例ID
        """
        request = RunInstancesRequest()

        # 设置自动释放时间
        request.set_AutoReleaseTime(release_time.strftime('%Y-%m-%dT%H:%M:%SZ'))

        # 是否只预检此次请求。true：发送检查请求，不会创建实例，也不会产生费用；false：发送正常请求，通过检查后直接创建实例，并直接产生费用
        request.set_DryRun(self.dry_run)

        # 实例的资源规格
        request.set_InstanceType(self.instance_type)
        # 实例的计费方式
        request.set_InstanceChargeType(self.instance_charge_type)
        # 镜像ID
        request.set_ImageId(self.image_id)
        # 指定新创建实例所属于的安全组ID
        request.set_SecurityGroupId(self.security_group_id)
        # 购买资源的时长
        request.set_Period(self.period)
        # 购买资源的时长单位
        request.set_PeriodUnit(self.period_unit)
        # 实例所属的可用区编号
        request.set_ZoneId(self.zone_id)
        # 网络计费类型
        request.set_InternetChargeType(self.internet_charge_type)
        # 虚拟交换机ID
        request.set_VSwitchId(self.vswitch_id)
        # 实例名称
        request.set_InstanceName(self.image_to_instance_name_map[self.image_id])
        # 是否使用镜像预设的密码
        request.set_PasswordInherit(self.password_inherit)
        # 指定创建ECS实例的数量
        request.set_Amount(self.amount)
        # 公网出带宽最大值
        request.set_InternetMaxBandwidthOut(self.internet_max_bandwidth_out)
        # 云服务器的主机名
        request.set_HostName(self.image_to_instance_name_map[self.image_id])
        # 是否为I/O优化实例
        request.set_IoOptimized(self.io_optimized)
        # 后付费实例的抢占策略
        request.set_SpotStrategy(self.spot_strategy)


        # 系统盘大小
        if self.image_to_instance_name_map[self.image_id] == "hadoop102":
            self.system_disk_size = '50'

        request.set_SystemDiskSize(self.system_disk_size)
        # 系统盘的磁盘种类
        request.set_SystemDiskCategory(self.system_disk_category)


        # 性能级别, 使用 SSD 的时候才可以设置
        request.set_SystemDiskPerformanceLevel(self.system_disk_performance_level)


        # 设置私有 IP 地址
        request.set_PrivateIpAddress(self.private_ip_address)

        body = self.client.do_action_with_exception(request)
        data = json.loads(body)

        instance_ids = data['InstanceIdSets']['InstanceIdSet']
        for instance_id in instance_ids:
            instance_name = self.image_to_instance_name_map.get(self.image_id)
            print('实例创建成功。实例ID：{}，实例名：{}'.format(instance_id, instance_name))
        return instance_ids

    def _check_instances_status(self, instance_ids):
        """
        每3秒中检查一次实例的状态，超时时间设为3分钟。
        :param instance_ids 需要检查的实例ID
        :return:
        """
        start = time.time()
        while True:
            request = DescribeInstancesRequest()
            request.set_InstanceIds(json.dumps(instance_ids))
            body = self.client.do_action_with_exception(request)
            data = json.loads(body)
            for instance in data['Instances']['Instance']:
                if RUNNING_STATUS in instance['Status']:
                    instance_ids.remove(instance['InstanceId'])
                    print('Instance boot successfully: {}'.format(instance['InstanceId']))

            if not instance_ids:
                print('Instances all boot successfully')
                break

            if time.time() - start > CHECK_TIMEOUT:
                print('Instances boot failed within {timeout}s: {ids}'
                      .format(timeout=CHECK_TIMEOUT, ids=', '.join(instance_ids)))
                break

            time.sleep(CHECK_INTERVAL)



if __name__ == '__main__':
    AliyunRunInstancesExample().run()
