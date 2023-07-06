import requests


def get_public_ip():
    url = 'https://api.ipify.org'  # 从ipify.org获取公网IP地址
    response = requests.get(url)
    ip_str = response.text
    start_index = ip_str.find(":") + 2  # 找到冒号的位置并向后移动两个字符
    end_index = len(ip_str)
    ip_address = ip_str[start_index:end_index]
    return ip_address


print(get_public_ip())
