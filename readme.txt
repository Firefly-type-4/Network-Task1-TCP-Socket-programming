TCP Socket 文本反转程序运行说明
========================================
程序概述
本程序是计算机网络课程设计Task1的Python实现，基于TCP Socket实现客户端-服务器架构的文本块反转服务。客户端将文件随机分块发送给服务器，服务器逐块反转文本并返回，客户端最终拼接生成完整的反转文件。程序严格遵循课程设计要求的报文格式和交互流程，支持多客户端并发访问，并生成可与Wireshark抓包相互印证的运行日志。

运行环境
- 操作系统：Windows 11
- Python版本：Python 3.13.1
- 网络环境：本地环回（127.0.0.1）

运行步骤
1. 服务器端运行
1. 将`reversetcpserver.py`文件放在任意目录
2. 打开终端/命令提示符，切换到文件所在目录
3. 执行命令启动服务器：

   python reversetcpserver.py <端口号>

   示例：

   python reversetcpserver.py 8888

4. 看到输出`Server listening on 0.0.0.0:8888`表示服务器启动成功，保持终端打开不要关闭

 2. 客户端运行
1. 将`reversetcpclient.py`和测试文件（如`test.txt`）放在同一目录
2. 打开新的终端/命令提示符，切换到文件所在目录
3. 执行命令启动客户端：

   python reversetcpclient.py <服务器IP> <服务器端口> <输入文件> <输出文件> <Lmin> <Lmax> <随机种子>

   本地测试示例：

   python reversetcpclient.py 127.0.0.1 8888 test.txt reversed_test.txt 50 100 42

4. 客户端终端会逐行打印每个块的反转结果，运行完成后显示成功提示

 3. 多客户端并发测试
保持服务器运行，打开多个新终端同时执行客户端命令即可，服务器会自动为每个客户端创建独立线程处理请求。

 命令行参数说明
 服务器端参数
| 参数 | 说明 | 示例 |
|------|------|------|
| 端口号 | 服务器监听的TCP端口（建议使用1024以上端口） | 8888 |

 客户端参数
| 参数 | 说明 | 示例 |
|------|------|------|
| 服务器IP | 服务器的IP地址，本地测试用127.0.0.1 | 127.0.0.1 |
| 服务器端口 | 与服务器启动时指定的端口一致 | 8888 |
| 输入文件 | 待反转的全英文ASCII文本文件路径 | test.txt |
| 输出文件 | 生成的完整反转文件路径 | reversed_test.txt |
| Lmin | 每个数据块的最小长度（字节） | 50 |
| Lmax | 每个数据块的最大长度（字节） | 100 |
| 随机种子 | 用于生成分块长度的随机数种子，相同种子会生成相同的分块序列 | 42 |

 提交文件清单
1. `reversetcpclient.py`：客户端程序源码
2. `reversetcpserver.py`：服务器程序源码
3. `test.txt`：测试用输入文件（全英文ASCII）
4. `reversed_test.txt`：反转后的输出文件
5. `client_run_log.txt`：客户端运行日志
6. `server_run_log.txt`：服务器运行日志
7. `tcp_packet_capture.doc`：Wireshark抓包截图及说明
8. `readme.txt`：本运行说明文档

 核心功能实现说明
 1. 报文格式（严格遵循课程设计要求）
所有字段均采用网络字节序（大端序）
| 报文类型 | Type值 | 报文结构 | 总长度 |
|----------|--------|----------|--------|
| Initialization | 1 | Type(2B) + 块数N(4B) | 6B |
| Agree | 2 | Type(2B) | 2B |
| ReverseRequest | 3 | Type(2B) + Length(4B) + 数据(Length B) | 6B + Length |
| ReverseAnswer | 4 | Type(2B) + Length(4B) + 反转数据(Length B) | 6B + Length |

 2. 分块算法
- 输入：文件总长度、Lmin、Lmax、随机种子
- 步骤：
  1. 使用指定种子初始化随机数生成器
  2. 循环生成[Lmin, Lmax]之间的随机整数作为块长度
  3. 当剩余字节数≤Lmax时，将剩余字节作为最后一块
  4. 块数N为生成的块长度列表的长度
- 示例：文件长度62字节，Lmin=50，Lmax=100，seed=42 → 生成块长度[62]，N=1

 3. 日志记录
- 日志文件：客户端生成`client_run_log.txt`，服务器生成`server_run_log.txt`
- 日志格式：`时间戳 [事件类型] 报文类型 from 源IP:源端口 to 目的IP:目的端口, length=长度 bytes`
- 时间戳精度：毫秒级，与Wireshark抓包时间戳可相互印证
- 记录事件：CONNECT、ACCEPT、SEND、RECV、DISCONNECT、START、STOP、ERROR

 4. 多客户端支持
服务器采用多线程模型，每个客户端连接创建一个独立线程处理，可同时支持2个及以上客户端并发请求，日志会交错记录不同客户端的交互过程。

 结果验证方法
1. 反转文件正确性验证：将生成的`reversed_test.txt`内容再次反转，应与原`test.txt`完全一致
2. 日志验证：客户端和服务器日志中的报文时间、类型、长度应一一对应
3. 抓包验证：
   - Wireshark选择环回网卡，设置过滤条件`tcp.port == 8888 and tcp.len > 0`
   - 调整时间显示格式为"日期和时间 + 秒：毫秒"
   - 抓包中的TCP段长度应与日志中的length字段完全相等
   - 抓包时间戳与日志时间戳误差应在10毫秒以内

问题排查
1. OSError: [WinError 10038] 在一个非套接字上尝试了一个操作
   - 原因：Windows系统套接字关闭后无法获取地址
   - 解决：已在代码中修复，使用提前保存的地址记录日志


 版本信息
- 版本：v1.0
- 最后更新：2026-06-10
- 兼容性：支持Windows、macOS、Linux全平台