注意事项（必看）

指令的使用

指令的使用需要注意 Backup Applet、Primary Safety，如果当前要使用的指令不在相应的状态下，则需要先执行 select_primary_safety, select_backup_applet 这两个指令切换到相应的状态下。
安全通道的使用

安全通道的使用需要注意，如果当前没有打开安全通道，则需要先打开安全通道，如果已经打开了安全通道，则不需要再次打开。
如果要使用 select_primary_safety, select_backup_applet 这两个指令切换安安全域，则需要先关闭安全通道，然后再切换状态，最后再打开安全通道。
使用安全通道时 nativeGPCBuildSafeAPDU、nativeGPCParseSafeAPDUResponse 这两个函数需要配合使用，使用时需要注意。不然会出现通信异常。
 
OneKey Lite Command 命令

如果不使用 native 库的 nativeGPCBuildAPDU、nativeGPCBuildSafeAPDU 构造命令，Command + <Data length> + Data 才是完整的命令
下面 Result 都是由 2 字节状态码 和 Data 组成。 9000 状态码代表成功。
下面步骤描述里面的结果是指 Data
开启安全通道的一步 verify_certificate

V1

[ ] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0x2A, 0x18, 0x10
# Data
crt
# Result
<None>
V2

[ ] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0x2A, 0x18, 0x10
# Data
crt
# Result
<None>
开启安全通道的一步 verify_auth_data

V1

[ ] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0x82, 0x18, 0x15
# Data
authData
# Result
auth
V2

[ ] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0x82, 0x18, 0x15
# Data
authData
# Result
auth
获取设备证书 get_device_certificate

V1

[ ] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0xCA, 0xBF, 0x21
# Data
A60483021518
# Result
certificate
V2

[ ] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0xCA, 0xBF, 0x21
# Data
A60483021518
# Result
certificate
select_primary_safety

V1

[ ] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x00, 0xA4, 0x04, 0x00
# Result
<None>
V2

[ ] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x00, 0xA4, 0x04, 0x00
# Result
<None>
select_backup_applet

V1

[ ] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x00, 0xA4, 0x04, 0x00
# Data
D156000132834001
# Result
<None>
V2

[ ] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x00, 0xA4, 0x04, 0x00
# Data
6f6e656b65792e6261636b757001
# Result
<None>
是否存在备份 get_backup_status

V1

[x] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0x6A, 0x00, 0x00
# Result: V1 版本这里可能有问题，需要再次测试
0x02 不存在备份
0x02 存在备份
V2

[x] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0x6A, 0x00, 0x00
# Result
0x00 不存在备份
0x02 存在备份
是否设置 PIN get_pin_status

V1

[ ] Select Backup Applet
[x] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0xCB, 0x80, 0x00
# Data
DFFF028105
# Result
0x02 没有设置 PIN
0x00 设置过 PIN
V2

[x] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0xCB, 0x80, 0x00
# Data
DFFF028105
# Result
0x02 没有设置 PIN
0x01 设置过 PIN
获取序列号 get_serial_number

V1

[ ] Select Backup Applet
[x] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0xCB, 0x80, 0x00
# Data
DFFF028101
# Result
SN
V2

[x] Select Backup Applet
[ ] Select Primary Safety
[-] Safe channel: 不会主动开启并使用安全通道，如果当前安全通道已打开，则需要用安全通道



# Command
0x80, 0xCB, 0x80, 0x00
# Data
DFFF028101
# Result
SN
获取密码的重试次数 get_pin_retry_count

V1

[ ] Select Backup Applet
[x] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0xCB, 0x80, 0x00
# Data
DFFF028102
# Result
16Hex Count
V2

[x] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0xCB, 0x80, 0x00
# Data
DFFF028102
# Result
16Hex Count
重置卡片 reset_card

V1

[ ] Select Backup Applet
[x] Select Primary Safety
[x] Safe channel



# Command
0x80, 0xCB, 0x80, 0x00
# Data
DFFE028205
# Result
<None>
V2

[x] Select Backup Applet
[ ] Select Primary Safety
[x] Safe channel



# Command
0x80, 0xCB, 0x80, 0x00
# Data
DFFE028205
# Result
<None>
验证 Pin verify_pin

V1

[x] Select Backup Applet
[ ] Select Primary Safety
[x] Safe channel



# Command
0x80, 0x20, 0x00, 0x00
# Data pin 必须为 6 位，int to HexString
# 不使用 nativeGPCBuildAPDU、nativeGPCBuildSafeAPDU 构造命令，还要加一个 length
06<pinHex>
# Result
xxxx
V2

[x] Select Backup Applet
[ ] Select Primary Safety
[x] Safe channel



# Command
0x80, 0x20, 0x00, 0x00
# Data pin 必须为 6 位，int to HexString
# 不使用 nativeGPCBuildAPDU、nativeGPCBuildSafeAPDU 构造命令，还要加一个 length
06<pinHex>
# Result
<None>
SW: 
0x9000 表⽰成功
6983 表⽰ PIN 重试次数为 0，已经锁定
63Cx 表⽰还有校验原 PIN 失败，剩余 x 次重试次数
设置 Pin、重置 Pin setup_new_pin

会重置 Pin，清空备份内容
V1

[ ] Select Backup Applet
[x] Select Primary Safety
[x] Safe channel



# Command
0x80, 0xCB, 0x80, 0x00
# Data pin 必须为 6 位
DFFE0B8204080006<pinHex>
# Data 由来
command1 = 00<New Pin length><6 New Pin>
command2 = 8204<command1 length>command1
Data = DFFE<command2 length>command2
# Result
<None>
V2

[x] Select Backup Applet
[ ] Select Primary Safety
[x] Safe channel



# Command
0x80, 0xCB, 0x80, 0x00
# Data pin 必须为 6 位
DFFE0B8204080006<pinHex>
# Result
<None>
修改 Pin change_pin

V1

[ ] Select Backup Applet
[x] Select Primary Safety
[x] Safe channel



# Command
0x80, 0xCB, 0x80, 0x00
# Data
dffe1182040e06<6 Old Pin>06<6 New Pin>
# Data 由来
command1 = <Old Pin length><6 Old Pin><New Pin length><6 New Pin>
command2 = 8204<command1 length>command1
Data = DFFE<command2 length>command2
# Result
<None>
SW: 
0x9000 表⽰成功
6983 表⽰ PIN 重试次数为 0，已经锁定
63Cx 表⽰还有校验原 PIN 失败，剩余 x 次重试次数
V2

[x] Select Backup Applet
[ ] Select Primary Safety
[x] Safe channel



# Command
0x80, 0xCB, 0x80, 0x00
# Data
dffe1182040e06<6 Old Pin>06<6 New Pin>
# Result
<None>
SW: 
0x9000 表⽰成功
6983 表⽰ PIN 重试次数为 0，已经锁定
63Cx 表⽰还有校验原 PIN 失败，剩余 x 次重试次数
备份数据 backup_data

打开通道后需要先调用 verify_pin
V1

[x] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0x3B, 0x00, 0x00
# Data
<data>
# Result
<None>
V2

[x] Select Backup Applet
[ ] Select Primary Safety
[x] Safe channel



# Command
0x80, 0x3B, 0x00, 0x00
# Data
<data>
# Result
<None>
导出数据 export_data

打开通道后需要先调用 verify_pin
V1

[x] Select Backup Applet
[ ] Select Primary Safety
[ ] Safe channel



# Command
0x80, 0x4B, 0x00, 0x00
# Result
<Data>
V2

[x] Select Backup Applet
[ ] Select Primary Safety
[x] Safe channel



# Command
0x80, 0x4B, 0x00, 0x00
# Result
<Data>
OneKey Lite 业务逻辑

备份流程

检查连接状态，如果连接失败，则抛出异常。
如果不是覆写操作且卡片已备份过，则抛出异常。
如果是覆写操作且是 V2 卡，则 verify_pin 进行 PIN 码验证并使用 setup_new_pin 清空卡片。
如果卡片是新卡，则先 setup_new_pin 设置 Pin，设置失败则抛出异常。
进行 PIN 码验证，验证失败则根据操作类型进行处理。
备份助记词到卡片中，返回备份结果。
恢复流程

检查连接状态和卡片状态，如果连接失败或卡片未初始化，则抛出对应的异常。
调用 verify_pin PIN 码验证函数，如果验证失败，则检查 PIN 的状态抛出对应的异常，如果验证成功，则继续。
从卡片中获取备份数据，并检查备份数据是否存在，如果不存在，则抛出异常，如果存在，则将其返回。
重置流程

使用 resetCard 重置卡片，如果重置失败，则抛出异常。
修改 Pin 流程

检查连接状态和卡片状态，如果连接失败或卡片未初始化，则抛出对应的异常。
调用 change_pin 修改 Pin，如果修改失败，则抛出异常。
开启安全通道

检查是否已经打开了安全通道，如果已经打开，则直接返回。
get_device_certificate 获取设备证书信息，如果获取失败，则返回 false。
返回的信息可以通过原生库方法 nativeGPCTLVDecode 为 JSON 字符串



{
  "response":"",
  "wRet":0
}
上一步的 response 通过原生库方法 nativeGPCParseCertificate 转成 JSON 字符串



{
  "sn":"",
  "subjectID":"",
}
准备 lite 的通信证书，详见 1Password — Password Manager for Teams, Businesses, and Families 



{
  "scpID": "1107",
  "keyUsage": "3C",
  "keyType": "88",
  "keyLength": 16,
  "hostID": "8080808080808080",
  "crt": "xxxx",
  "sk": "xxxx",
  "cardGroupID": "01020304"
}
将第三步 JSON 的 cardGroupID 换成第二步获取到的 subjectID，把整个 JSON 字符串当参数，传给原生库的 nativeGPCInitialize 函数初始化安全通道，如果返回值 0 是成功，其他是失败。
将第三步获取到的 crt 当作参数传给验证证书的指令 verify_certificate，并发送到 NFC 卡上，如果返回结果为 9000 则成功，其他为失败。
调用原生库的 nativeGPCBuildMutualAuthData 函数生成认证数据（String），把生成认证数据当做数据调用 verify_auth_data，如果结果为空或者返回值不是 9000 则失败。
将第六步的返回结果当参数，调用原生库的 nativeGPCOpenSecureChannel 函数打开安全通道，如果返回值不为 0，则返回 false。
打开安全通道成功，将 hasOpenSafeChannel 置为 true，返回 true。
关闭安全通道

检查是否已经打开了安全通道，如果没有打开，则直接返回。
调用原生库的 nativeGPCFinalize() 函数关闭安全通道，如果返回值不为 0，则返回 false。
PIN 码验证

检查连接状态和卡片状态，如果连接失败或卡片未初始化，则抛出对应的异常。
调用 verify_pin PIN 码验证函数，如果验证成功，则继续。
如果验证失败，则检查 PIN 的状态抛出对应的异常。
连接失败则抛出 ConnectionFailException 异常。

错误码 6983 表示卡片已经锁定

则自动执行 reset_card 重置卡片。
如果重置失败则抛出 CardLockException 异常。
成功则返回 UpperErrorAutoResetException。
错误码 63Cx 表示还有校验原 PIN 失败，剩余 x 次重试次数

则抛出 PasswordWrongException 异常。
并通过 CardState 返回剩余重试次数。
其他错误码表示 Pin 码验证异常

get_pin_retry_count 验证是否锁卡.
如果已经锁卡则自动执行 reset_card 重置卡片。成功则返回 UpperErrorAutoResetException，如果失败则抛出 CardLockException 异常。
如果没有锁卡则抛出 PasswordWrongException 异常。 并通过 CardState 返回剩余重试次数。
OneKey Lite 通信错误码




1000：InitChannelException，初始化异常。
1001：NotExistsNFC，没有 NFC 设备。
1002：NotEnableNFC，没有开启 NFC 设备。
1003：NotNFCPermission，没有使用 NFC 的权限。
2001：ConnectionFailException，连接失败。
2002：InterruptException，操作中断（可能是连接问题）。
2003：DeviceMismatchException，连接设备不匹配。
2004：UserCancelExceptions，用户主动取消。
3001：PasswordWrongException，密码错误。
3002：InputPasswordEmptyException，输入密码为空。
3003：PasswordEmptyException，未设置过密码。
3004：InitPasswordException，设置初始化密码错误。
3005：CardLockException，密码重试次数太多已经锁死。
3006：UpperErrorAutoResetException，密码重试次数太多已经自动重制卡片。
4000：ExecFailureException，未知的命令执行失败。
4001：InitializedException，已经备份过内容。
4002：NotInitializedException，没有备份过内容。