#!/usr/bin/env python
# coding=utf-8
from datetime import datetime, timedelta
import json
import os
import time
import traceback

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkecs.request.v20140526.RunInstancesRequest import RunInstancesRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.CreateImageRequest import CreateImageRequest

RUNNING_STATUS = 'Running'
CHECK_INTERVAL = 3
CHECK_TIMEOUT = 180
IMAGE_NAME_PREFIX = 'auto_'
IMAGE_CREATION_TIME_OFFSET = 10 * 60


class AliyunRunInstancesExample(object):

    def __init__(self):
        self.access_id = os.environ.get('AccessKey')
        self.access_secret = os.environ.get('AccessSecret')
        # 获取用户输入的小时数
        self.user_hours = int(input("请输入开通几个小时（输入数字后按2次回车）："))

        # 安全组
        self.security_group_ids = ['sg-8vbap91nk99v1ypw280a']
        # 是否只预检此次请求。true：发送检查请求，不会创建实例，也不会产生费用；false：发送正常请求，通过检查后直接创建实例，并直接产生费用
        self.dry_run = False
        # 实例所属的地域ID
        self.region_id = 'cn-zhangjiakou'
        # 实例的资源规格
        # self.instance_type = 'ecs.hfg6.xlarge'
        self.instance_type = 'ecs.u1-c1m4.large'
        # 实例的计费方式
        self.instance_charge_type = 'PostPaid'
        # 镜像ID
        self.image_id = 'm-8vb0r5yi4hy3utcx6al7'
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
        # 实例名称
        self.instance_name = 'winTop'
        # 是否使用镜像预设的密码
        self.password_inherit = True
        # 指定创建ECS实例的数量
        self.amount = 1
        # 公网出带宽最大值
        self.internet_max_bandwidth_out = 100
        # 云服务器的主机名
        self.host_name = 'win'
        # 是否为I/O优化实例
        self.io_optimized = 'optimized'

        # 系统盘大小
        self.system_disk_size = '80'
        # 系统盘的磁盘种类
        self.system_disk_category = 'cloud_auto'

        self.client = AcsClient(self.access_id, self.access_secret, self.region_id)

    def run(self):
        try:
            ids = self.run_instances()
            self._check_instances_status(ids)
            self.create_image_before_release(ids)

        except ClientException as e:
            print('Fail. Something with your connection with Aliyun go incorrect.'
                  ' Code: {code}, Message: {msg}'
                  .format(code=e.error_code, msg=e.message))
        except ServerException as e:
            print('Fail. Business error.'
                  ' Code: {code}, Message: {msg}'
                  .format(code=e.error_code, msg=e.message))
        except Exception:
            print('Unhandled error')
            print(traceback.format_exc())


    def run_instances(self):
        """
        调用创建实例的API，得到实例ID后继续查询实例状态
        :return:instance_ids 需要检查的实例ID
        """
        request = RunInstancesRequest()

        request.set_DryRun(self.dry_run)
        security_group_ids_str = ','.join(self.security_group_ids)
        request.set_SecurityGroupId(security_group_ids_str)

        request.set_InstanceType(self.instance_type)
        request.set_InstanceChargeType(self.instance_charge_type)
        request.set_ImageId(self.image_id)
        request.set_Period(self.period)
        request.set_PeriodUnit(self.period_unit)
        request.set_ZoneId(self.zone_id)
        request.set_InternetChargeType(self.internet_charge_type)
        request.set_VSwitchId(self.vswitch_id)
        request.set_InstanceName(self.instance_name)
        request.set_PasswordInherit(self.password_inherit)
        request.set_Amount(self.amount)
        request.set_InternetMaxBandwidthOut(self.internet_max_bandwidth_out)
        request.set_HostName(self.host_name)
        request.set_IoOptimized(self.io_optimized)



        # 根据用户输入的小时数计算释放时间
        auto_release_time = datetime.utcnow() + timedelta(hours=self.user_hours)
        request.set_AutoReleaseTime(auto_release_time.strftime('%Y-%m-%dT%H:%M:%SZ'))

        request.set_SystemDiskSize(self.system_disk_size)
        request.set_SystemDiskCategory(self.system_disk_category)

        body = self.client.do_action_with_exception(request)
        data = json.loads(body)
        instance_ids = data['InstanceIdSets']['InstanceIdSet']
        print('Success. Instance creation succeed. InstanceIds: {}'.format(', '.join(instance_ids)))
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

# 在释放前 10 分钟创建镜像
    def create_image_before_release(self, instance_ids):
        for instance_id in instance_ids:
            request = CreateImageRequest()
            request.set_InstanceId(instance_id)
            image_name = IMAGE_NAME_PREFIX + datetime.utcnow().strftime('%Y%m%d')
            request.set_ImageName(image_name)
            request.set_NoReboot(True)

            # 计算镜像创建时间
            image_creation_time = datetime.utcnow() + timedelta(hours=self.user_hours) - timedelta(seconds=IMAGE_CREATION_TIME_OFFSET)
            image_creation_timestamp = time.mktime(image_creation_time.timetuple())

            # 等待镜像创建时间
            time.sleep(max(image_creation_timestamp - time.time(), 0))

            # 创建镜像
            try:
                body = self.client.do_action_with_exception(request)
                data = json.loads(body)
                image_id = data['ImageId']
                print(f'Success. Image creation succeeded. ImageId: {image_id}')
            except ClientException as e:
                print(f'ClientException occurred. Error: {e.error_code}, Message: {e.message}')
            except ServerException as e:
                print(f'ServerException occurred. Error: {e.error_code}, Message: {e.message}')
            except Exception:
                print(f'Unexpected exception occurred: {traceback.format_exc()}')
if __name__ == '__main__':
    AliyunRunInstancesExample().run()
