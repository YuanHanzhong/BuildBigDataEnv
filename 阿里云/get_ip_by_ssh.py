import paramiko
import re
import time


def ssh_login(host, port, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port, username, password)
        return ssh
    except paramiko.SSHException as e:
        print(f"SSH连接失败: {e}")
        return None


def get_last_login_ip(ssh):
    if ssh is None:
        return None

    try:
        stdin, stdout, stderr = ssh.exec_command("last -i -n 1")
        output = stdout.read().decode('utf-8')

        ip_regex = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        match = re.search(ip_regex, output)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"获取上次登录IP地址失败: {e}")

    return None


if __name__ == "__main__":
    host = "example.com"  # 替换为您的服务器地址
    port = 22  # SSH默认端口为22，如有更改请替换
    username = "username"  # 替换为您的用户名
    password = "password"  # 替换为您的密码

    ssh = ssh_login(host, port, username, password)
    if ssh:
        time.sleep(5)  # 等待5秒以确保登录成功
        last_login_ip = get_last_login_ip(ssh)
        if last_login_ip:
            print(f"上次登录IP地址是: {last_login_ip}")
        else:
            print("无法获取上次登录IP地址")
        ssh.close()
    else:
        print("无法连接到远程服务器")
