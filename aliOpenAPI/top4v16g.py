#!/usr/bin/env python
# coding=utf-8
import json
import time
import traceback
import os
from datetime import datetime, timedelta

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkecs.request.v20140526.RunInstancesRequest import RunInstancesRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.CreateImageRequest import CreateImageRequest

RUNNING_STATUS = 'Running'
CHECK_INTERVAL = 3
CHECK_TIMEOUT = 180
IMAGE_CREATION_WAIT_TIME = 10  # Wait time before creating an image (in minutes)


class AliyunRunInstancesExample(object):

    def __init__(self):
        self.access_id = os.environ.get('AccessKey')
        self.access_secret = os.environ.get('AccessSecret')
        self.region_id = 'cn-zhangjiakou'
        self.image_id = 'm-8vb0r5yi4hy3utcx6al7'
        self.instance_type = 'ecs.hfg6.xlarge'
        self.vswitch_id = 'vsw-8vbi4ohmz5c1nsoasmnkl'
        self.instance_name = 'winTop'
        self.password_inherit = True
        self.amount = 1
        self.internet_max_bandwidth_out = 100
        self.host_name = 'win'
        self.io_optimized = 'optimized'
        self.system_disk_size = '80'
        self.system_disk_category = 'cloud_auto'

        self.client = AcsClient(self.access_id, self.access_secret, self.region_id)

    def run(self):
        try:
            hours = int(input("请输入您需要使用的小时数："))
            auto_release_time = datetime.utcnow() + timedelta(hours=hours)
            image_creation_time = auto_release_time - timedelta(minutes=IMAGE_CREATION_WAIT_TIME)
            self.auto_release_time = auto_release_time.strftime("%Y-%m-%dT%H:%M:%SZ")

            print(f'镜像将在 {image_creation_time} 创建，ECS将在 {auto_release_time} 释放。')

            ids = self.run_instances()
            self._check_instances_status(ids)
            time.sleep((image_creation_time - datetime.utcnow()).total_seconds())
            image_id = self.create_image(ids[0])
            print(f'镜像已成功创建，镜像id为：{image_id}')

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
        request = RunInstancesRequest()
        request.set_InstanceType(self.instance_type)
        request.set_ImageId(self.image_id)
        request.set_VSwitchId(self.vswitch_id)
        request.set_InstanceName(self.instance_name)
        request.set_PasswordInherit(self.password_inherit)
        request.set_Amount(self.amount)
        request.set_InternetMaxBandwidthOut(self.internet_max_bandwidth_out)
        request.set_HostName(self.host_name)
        request.set_IoOptimized(self.io_optimized)
        request.set_SystemDiskSize(self.system_disk_size)
        request.set_SystemDiskCategory(self.system_disk_category)
        request.set_AutoReleaseTime(self.auto_release_time)

        response = self.client.do_action_with_exception(request)
        data = json.loads(response)
        instance_ids = data['InstanceIdSets']['InstanceIdSet']
        print('Success. Instance creation succeed. InstanceIds: {}'.format(', '.join(instance_ids)))
        return instance_ids

    def _check_instances_status(self, instance_ids):
        start = time.time()
        while True:
            request = DescribeInstancesRequest()
            request.set_InstanceIds(json.dumps(instance_ids))
            response = self.client.do_action_with_exception(request)
            data = json.loads(response)

            for instance in data['Instances']['Instance']:
                if RUNNING_STATUS in instance['Status']:
                    instance_ids.remove(instance['InstanceId'])
                    print('Instance bootup succeed: {}'.format(instance['InstanceId']))

            if not instance_ids:
                print('All instances are running')
                break

            if time.time() - start > CHECK_TIMEOUT:
                print('Instances boot up check timeout')
                break

            time.sleep(CHECK_INTERVAL)

    def create_image(self, instance_id):
        request = CreateImageRequest()
        request.set_InstanceId(instance_id)
        request.set_ImageName(f'{self.instance_name}_image')

        response = self.client.do_action_with_exception(request)
        data = json.loads(response)
        image_id = data['ImageId']
        return image_id


if __name__ == '__main__':
    AliyunRunInstancesExample().run()
