# 生产运营与库存管理看板

一个适合中小型制造企业的本地生产运营看板。项目使用模拟数据展示设备、生产、质量、订单和库存情况，并支持通过 Excel 更新数据。所有界面和提示均为中文。

## 功能

- 生产总览：10 项 KPI、设备/产量/质量/订单/库存图表
- 设备状态：车间、状态和产品筛选
- 生产计划：完成率进度条和状态筛选
- 订单管理：临期橙色、逾期红色预警
- 库存管理：不足和过高预警
- Excel 导入：格式与字段校验、预览、事务化导入
- 自适应电脑和手机屏幕
- 西门子 S7-1200 实时采集示例：2 秒轮询、自动重连、在线/离线状态
- 用户登录及管理员、操作员、只读用户三级权限
- 关键操作日志、车间/产品/设备主数据维护
- 设备、生产、计划、订单、库存及审计日志 Excel 导出
- 数据库在线备份和基础安全检查
- 网页 PLC 配置中心、TCP 连接测试和多设备管理
- 实时报警确认/恢复、24 小时设备历史采样和 OEE
- 每日自动备份、保留周期清理、Waitress 与 Windows 服务部署

## 技术栈

Python 3、Flask、SQLite、Pandas、openpyxl、HTML/CSS/JavaScript、ECharts。

## 项目目录

`app.py` 是启动入口；`database.py` 管理数据库；`services/` 存放业务逻辑；`scripts/` 存放初始化和模拟数据脚本；`templates/` 与 `static/` 存放页面资源；`tests/` 存放测试；`data/` 存放 Excel 模板。

## Windows 安装与启动

在 VS Code 中打开本项目目录，然后在 PowerShell 依次执行：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts\init_database.py
python scripts\generate_mock_data.py
python app.py
```

若 PowerShell 禁止激活脚本，可先执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

浏览器访问：<http://127.0.0.1:5000>

首次登录账户：

```text
用户名：admin
初始密码：Admin@123456
```

首次登录后系统会强制修改密码。新密码至少 10 位，并同时包含字母和数字。

## 用户角色与权限

| 功能 | 管理员 | 操作员 | 只读用户 |
|---|---:|---:|---:|
| 查看生产看板和业务数据 | 是 | 是 | 是 |
| 导出业务报表 | 是 | 是 | 是 |
| Excel 数据导入 | 是 | 是 | 否 |
| 维护车间、产品和设备主数据 | 是 | 是 | 否 |
| 创建用户、查看操作日志 | 是 | 否 | 否 |
| 创建数据库备份、安全检查 | 是 | 否 | 否 |

管理员可以在“用户与日志”页面创建账户。新账户首次登录时同样必须修改初始密码。登录、数据导入、主数据修改、用户创建、报表导出和数据库备份均写入操作日志。

## 报表、定时采集与备份

- “报表导出”页面可生成设备、生产记录、生产计划、订单和库存 Excel 文件；管理员还可导出操作日志。
- PLC 采集线程随应用启动，默认每 2 秒采集一次。周期和设备配置位于 `settings/plc_devices.json`。
- 管理员可在“备份与审计”页面创建 SQLite 一致性备份。浏览器会下载备份文件，服务器副本保存在 `backups/`，该目录不会提交到 Git。
- 安全检查会提示管理员账户、初始密码、审计记录和数据库备份状态。

## 第三阶段：现场运行功能

### 设备接入配置中心

管理员可在“设备接入配置”页面添加多台 PLC，配置设备编号、IP、驱动、Rack、Slot、TCP 端口、DB 号和读取范围，并测试 TCP 连接。保存后采集线程会自动读取新配置，无需修改源代码。

真实 PLC 使用 `s7` 驱动，试运行使用 `simulation`。设备配置的新增与修改会写入操作日志。

### 实时报警中心

系统会根据采集结果自动生成 PLC 离线和设备故障报警。报警支持“活动、已确认、已恢复”三个状态，管理员和操作员可以填写处理说明并确认；设备恢复后系统自动关闭报警。报警页面每 5 秒刷新。

### 设备历史与 OEE

系统保存最近 90 天的设备采样，OEE 页面显示最近 24 小时指标：

```text
时间开动率 = 运行采样数 / 全部采样数
性能开动率 = 实时产量 / 今日计划产量
质量率 = 合格品数量 / 实际产量
OEE = 时间开动率 × 性能开动率 × 质量率
```

示例 OEE 用于试运行验证。正式投产时应结合班次、计划停机和产品标准节拍完善计算口径。

### 自动备份

管理员可在“备份与审计”页面设置每天执行小时和保留天数。后台任务默认每天凌晨 2 点执行，保留 30 天，并自动清理过期备份。备份文件保存在 `backups/`。

## 正式启动与 Windows 服务

日常开发仍可使用 `python app.py`。局域网试运行建议使用 Waitress：

```powershell
$env:DASHBOARD_SECRET_KEY="请替换为足够长的随机字符串"
.venv\Scripts\python.exe run_production.py
```

Waitress 默认监听 `0.0.0.0:5000`，同一局域网的电脑可以通过服务器 IP 访问。开放网络访问前必须配置 Windows 防火墙、可信网段和 HTTPS 反向代理。

安装为 Windows 服务时，以管理员身份打开 PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\install_service.ps1
```

服务名称为 `ProductionOperationsDashboard`，启动类型为自动。常用维护命令：

```powershell
.venv\Scripts\python.exe scripts\windows_service.py stop
.venv\Scripts\python.exe scripts\windows_service.py start
.venv\Scripts\python.exe scripts\windows_service.py remove
```

正式部署前应通过环境变量设置独立的会话密钥：

```powershell
$env:DASHBOARD_SECRET_KEY="请替换为足够长的随机字符串"
python app.py
```

## 运行测试

```powershell
python -m pytest -q
```

## Excel 模板与导入

模板位于 `data/生产运营数据模板.xlsx`，也可在“数据导入”页面下载。模板必须包含“设备信息、生产记录、生产计划、订单信息、库存信息”五张工作表。上传后先校验预览，再点击确认导入。导入使用数据库事务，任一行失败时整次导入都会回滚。

建议先保留模板中的编号规则。设备引用的车间、生产记录和订单引用的产品，应当已存在于数据库中。

## S7-1200 真实设备连接

本项目通过以太网读取 S7-1200 PLC，而不是直接控制机器。采集服务只读 PLC 数据，不会向 PLC 写入命令，因此不会改变设备的运行状态。

示例设备是 `M001`，默认 PLC 地址是 `192.168.1.10`，配置文件位于 `settings/plc_devices.json`。默认使用 `simulation` 驱动，因此没有 PLC 时也可以验证页面的实时刷新。

### 1. 检查电脑和 PLC 网络

运行看板的电脑需要与 PLC 处在可互通的网络中。例如 PLC 是 `192.168.1.10`，可将电脑的有线网卡设置为 `192.168.1.100`、子网掩码 `255.255.255.0`。在 PowerShell 执行：

```powershell
ping 192.168.1.10
```

收到回复后再配置软件。现场网络有 VLAN、交换机隔离或防火墙时，还需要保证 TCP `102` 端口可访问。

### 2. 在 TIA Portal 配置 PLC

由 PLC 工程师在 CPU 属性中启用“允许来自远程对象的 PUT/GET 通信访问”。然后新建一个供看板读取的数据块，例如 `DB1_看板数据`，并关闭该数据块的“优化的块访问”。

建议不要让看板读取控制逻辑中的内部变量；单独使用一个只用于上报数据的数据块，后续维护更安全。

### 3. 建立 PLC 数据映射

示例读取 DB1 的 14 个字节。请在 PLC 程序中把真实运行信号和计数结果写入下列变量：

| 变量名 | PLC 地址 | 类型 | 说明 |
|---|---|---|---|
| `MachineStatus` | `DB1.DBB0` | Byte | `1` 运行、`2` 停机、`3` 故障 |
| `ActualQuantity` | `DB1.DBD2` | DInt | 当前累计实际产量 |
| `QualifiedQuantity` | `DB1.DBD6` | DInt | 当前累计合格品数 |
| `DefectiveQuantity` | `DB1.DBD10` | DInt | 当前累计报废品数 |

如果现场的 DB 号或地址不同，请同步修改 `plc_devices.json` 中的 `db_number`、`read_start`、`read_size` 和 `mapping` 字段。变量类型必须与 PLC 工程一致；示例中的产量均为 32 位有符号整数（DInt）。

### 4. 切换到真实 PLC 模式

确认网络、PUT/GET 和地址映射无误后，打开 `settings/plc_devices.json`，把：

```json
"driver": "simulation"
```

改为：

```json
"driver": "s7"
```

重启 `python app.py` 后，打开“设备状态”页面。连接成功时，`M001` 的“数据来源”显示为 `PLC`，“连接”显示为 `在线`。服务每 2 秒采集一次；断开或读取失败时显示“离线”和错误提示，但不会影响其他页面。

### 5. 增加更多设备

在 `devices` 数组中复制一份设备配置，并修改 `machine_code`、IP、DB 号和变量地址。`machine_code` 必须先存在于“设备信息”中，例如 `M002`。每台设备都可采用不同的 PLC 地址和数据块。

## 常见错误

- `python` 不可用：安装 Python 3，并勾选“Add Python to PATH”。
- 无法激活虚拟环境：使用上面的临时执行策略命令。
- 页面没有数据：重新执行 `python scripts\generate_mock_data.py`。
- 端口被占用：关闭占用 5000 端口的程序，或修改 `app.py` 末尾端口。
- 图表不显示：ECharts 默认从公共 CDN 加载，请检查网络连接。
- Excel 导入失败：确认扩展名为 `.xlsx`、工作表和字段名与模板完全一致。
- PLC 显示“离线”：先执行 `ping PLC地址`；再检查 PLC IP、电脑网卡、TCP 102、防火墙以及 PUT/GET 是否启用。
- PLC 已连接但数值不正确：核对 DB 是否关闭“优化的块访问”，以及 DB 号、字节偏移、DInt/Byte 类型是否与 `plc_devices.json` 一致。
- 提示没有权限读取：由 PLC 工程师检查 CPU 保护等级和 PUT/GET 通信访问设置。
- 登录后只能进入修改密码页面：这是首次登录保护，修改初始密码后即可进入系统。
- 提示“没有操作权限”：当前账户角色不允许执行该功能，请联系管理员调整账户。

## 第一版限制

本版本已提供 S7-1200 的只读轮询示例，但不包含 PLC 程序编写、MES/ERP/WMS 集成、秒级以下采集、复杂权限、在线支付、机器学习预测、Docker 或正式生产部署。真实投产前应由设备和自动化工程师完成现场安全评审。

## 后续计划

后续可加入账户禁用与密码重置、细粒度菜单权限、日志归档、自动定时备份、报表条件筛选、HTTPS、反向代理和正式服务器部署。接入真实生产系统前还应进行网络隔离、漏洞扫描、恢复演练和现场安全评审。
