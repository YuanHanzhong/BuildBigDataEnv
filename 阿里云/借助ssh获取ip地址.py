/*
每次使用mobaxterm连接阿里云市里的时候都会返回     │                        • MobaXterm 10.4 •                          │
     │            (SSH client, X-server and networking tools)             │
     │                                                                    │
     │ ➤ SSH session to atguigu@hadoop102                                 │
     │   • SSH compression : ✘                                            │
     │   • SSH-browser     : ✔                                            │
     │   • X11-forwarding  : ✘  (disabled in session settings)            │
     │   • DISPLAY         : 192.168.3.10:0.0                             │
     │                                                                    │
     │ ➤ For more info, ctrl+click on help or visit our website           │
     └────────────────────────────────────────────────────────────────────┘

Last login: Thu Apr 20 14:35:28 2023 from 120.245.114.128

Welcome to Alibaba Cloud Elastic Compute Service !
如果您想要使用Python模拟MobaXterm登录阿里云实例，可以使用Python的paramiko库来实现SSH连接。以下是一个示例代码，展示了如何使用paramiko库连接到阿里云实例，并获取欢迎信息和IP地址：
*/

