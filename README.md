
## 最新的配置
createBigData-202307.py[initBigData.sh]

backupHadoop.py


## 初始化系统

### mac 上执行, 为的是远程连接时不报错
```shell
initBigData.sh
```


### hadoop102上执行,运行此命令实现机器之间互通
```shell
init_ssh.sh # 先在 hadoop102 初始化,可以正常访问别的
xcall init_ssh.sh # 让其他的亦可以互相访问
```

#### 具体内容
```shell
#!/bin/bash

ssh-keygen -R hadoop102 # 删除已有的
ssh-keygen -R hadoop103 
ssh-keygen -R hadoop104 

ssh-keygen -R 172.29.16.12 # 还要删除相关 ip 地址
ssh-keygen -R 172.29.16.13
ssh-keygen -R 172.29.16.14

# ssh-keyscan用于手机远程主机的公钥,需要保证远程主机微启动状态

ssh-keyscan -H hadoop102 >> /home/atguigu/.ssh/known_hosts
ssh-keyscan -H hadoop103 >> /home/atguigu/.ssh/known_hosts
ssh-keyscan -H hadoop104 >> /home/atguigu/.ssh/known_hosts

ssh-keyscan -H hadoop102 >> /root/.ssh/known_hosts
ssh-keyscan -H hadoop103 >> /root/.ssh/known_hosts
ssh-keyscan -H hadoop104 >> /root/.ssh/known_hosts

# 脚本里用绝对路径
ssh-keyscan -H 172.29.16.12 >> /home/atguigu/.ssh/known_hosts # ip 地址也要加入
ssh-keyscan -H 172.29.16.13 >> /home/atguigu/.ssh/known_hosts
ssh-keyscan -H 172.29.16.14 >> /home/atguigu/.ssh/known_hosts

ssh-keyscan -H 172.29.16.12 >> /root/.ssh/known_hosts 
ssh-keyscan -H 172.29.16.13 >> /root/.ssh/known_hosts
ssh-keyscan -H 172.29.16.14 >> /root/.ssh/known_hosts

```

## 已经配置了重启后自动打通连接
crontab -e
```shell
# root添加联通
@reboot sleep 30 ; sudo /home/atguigu/bin/init_ssh.sh > /home/atguigu/log/init_ssh.log 2>&1
# atguigu添加联通 
@reboot sleep 30 ;  /home/atguigu/bin/init_ssh.sh > /home/atguigu/log/init_ssh.log 2>&1
````

## 启动集群
```shell
1startAll.sh
```