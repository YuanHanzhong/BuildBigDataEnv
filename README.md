
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
$ cat init_ssh.sh
#!/bin/bash

ssh-keygen -R hadoop102 # 删除已有的
ssh-keygen -R hadoop103 
ssh-keygen -R hadoop104 

ssh-keygen -R 172.29.16.12 # 还要删除相关 ip 地址
ssh-keygen -R 172.29.16.13
ssh-keygen -R 172.29.16.14


ssh-keyscan -H hadoop102 >> ~/.ssh/known_hosts
ssh-keyscan -H hadoop103 >> ~/.ssh/known_hosts
ssh-keyscan -H hadoop104 >> ~/.ssh/known_hosts

```

## 启动集群
```shell
1startAll.sh
```