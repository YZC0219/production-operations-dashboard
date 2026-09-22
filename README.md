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

## 运行测试

```powershell
python -m pytest -q
```

## Excel 模板与导入

模板位于 `data/生产运营数据模板.xlsx`，也可在“数据导入”页面下载。模板必须包含“设备信息、生产记录、生产计划、订单信息、库存信息”五张工作表。上传后先校验预览，再点击确认导入。导入使用数据库事务，任一行失败时整次导入都会回滚。

建议先保留模板中的编号规则。设备引用的车间、生产记录和订单引用的产品，应当已存在于数据库中。

## S7-1200 实时连接示例

示例设备为 `M001`，IP 是 `192.168.1.10`，配置文件位于 `settings/plc_devices.json`。默认使用 `simulation` 驱动，因此没有 PLC 时也可以看到实时数值变化。确认 PLC 设置和变量地址后，把：

```json
"driver": "simulation"
```

改为：

```json
"driver": "s7"
```

然后重新启动 `python app.py`。示例只读 `DB1` 的 14 个字节：

- `DBB0`：设备状态，1=运行、2=停机、3=故障
- `DBD2`：实际产量，DInt
- `DBD6`：合格品数量，DInt
- `DBD10`：报废品数量，DInt

在 TIA Portal 中，需要为 CPU 启用“允许来自远程对象的 PUT/GET 通信访问”，并关闭该数据块的“优化的块访问”。电脑与 PLC 必须处于可互通网段，TCP 102 端口不可被防火墙阻止。机型、固件或安全策略不同时，应以现场 PLC 配置为准。

采集程序只读 PLC，不向 PLC 写入任何值。设备页每 2 秒获取一次最新结果；连接失败时显示“离线”和错误提示，不会影响其他页面运行。

## 常见错误

- `python` 不可用：安装 Python 3，并勾选“Add Python to PATH”。
- 无法激活虚拟环境：使用上面的临时执行策略命令。
- 页面没有数据：重新执行 `python scripts\generate_mock_data.py`。
- 端口被占用：关闭占用 5000 端口的程序，或修改 `app.py` 末尾端口。
- 图表不显示：ECharts 默认从公共 CDN 加载，请检查网络连接。
- Excel 导入失败：确认扩展名为 `.xlsx`、工作表和字段名与模板完全一致。

## 第一版限制

本版本不连接 PLC、MES、ERP 或 WMS，不提供秒级实时数据、复杂权限、在线支付、机器学习预测、Docker 或正式生产部署。刷新页面或重新导入 Excel 即可更新数据。

## 后续计划

可按需加入用户登录、操作日志、主数据维护、设备接口、定时采集、更多导出报表和正式服务器部署。接入真实系统前应补充身份验证、权限、备份及安全审计。
