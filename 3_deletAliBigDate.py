from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import DeleteInstanceRequest

def delete_ecs_instance(access_key, secret_key, region_id, instance_id):
    client = AcsClient(access_key, secret_key, region_id)

    request = DeleteInstanceRequest.DeleteInstanceRequest()
    request.set_accept_format('json')
    request.set_InstanceId(instance_id)

    response = client.do_action_with_exception(request)
    return response

# 使用你的阿里云 Access Key ID, Access Key Secret, 区域 ID, 和实例 ID
ACCESS_KEY = 'YOUR_ACCESS_KEY'
SECRET_KEY = 'YOUR_SECRET_KEY'
REGION_ID = 'cn-zhangjiakou'
INSTANCE_ID = 'YOUR_INSTANCE_ID'

response = delete_ecs_instance(ACCESS_KEY, SECRET_KEY, REGION_ID, INSTANCE_ID)
print(response)
