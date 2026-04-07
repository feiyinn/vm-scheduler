# vm-scheduler

在 Fedora 43 宿主机上，用 `systemd timer` 调度 libvirt Windows 11 VM 的定时开关机，并在执行前通过数据库中的交易日历判断“今天是否为交易日”。

当前设计目标：

- 支持任意多个 libvirt VM 的统一调度管理
- 只在交易日执行开关机
- 使用独立 Git 项目托管全部部署脚本、Python 代码和 `systemd` 模板
- 后续可以通过自动化部署脚本在不同宿主机上重复安装

当前默认上线参数：

- PostgreSQL 主机：`treasure-code-simu:15432`
- 数据库：`trading_db`
- Schema：`trading`
- 交易日历表：`trading.md_trading_calendar`
- 交易日规则：`SH` 与 `SZ` 同日均为交易日
- 开机时间：`08:55`
- 关机时间：`15:05`
- 示例目标 VM：`ths-books`、`ths-books-prod`

## 目录结构

```text
vm-scheduler/
├── config/
│   └── config.example.yaml
├── pyproject.toml
├── README.md
├── scripts/
│   ├── install.sh
│   └── uninstall.sh
├── systemd/
│   ├── vm-scheduler-start.service
│   ├── vm-scheduler-start.timer
│   ├── vm-scheduler-stop.service
│   └── vm-scheduler-stop.timer
└── src/
    └── vm_scheduler/
        ├── __init__.py
        ├── cli.py
        ├── config.py
        ├── database.py
        ├── logging_utils.py
        ├── scheduler.py
        └── virsh.py
```

## 工作方式

1. `systemd timer` 在配置时间触发 `start` 或 `stop` service。
2. service 调用 Python CLI。
3. CLI 从 `/etc/vm-scheduler/config.yaml` 读取配置。
4. 程序查询交易日历数据库。
5. 若是交易日，则依次执行 `virsh start` / `virsh shutdown`。
6. 若非交易日，则记录日志并跳过。
7. 若配置了多 VM 间隔，则在相邻 VM 操作之间等待指定秒数，降低宿主机瞬时负载。

## 配置

先复制示例配置：

```bash
sudo mkdir -p /etc/vm-scheduler
sudo cp config/config.example.yaml /etc/vm-scheduler/config.yaml
```

然后按实际情况检查数据库密码、SQL、定时规则和 VM 名称。

当前实现支持在 `start_targets` 和 `stop_targets` 中配置任意数量的 VM。
示例配置默认包含两个 VM，仅作为上线初始样例。

你也可以配置多 VM 的统一开关机间隔：

- `virsh.start_interval_seconds`
- `virsh.stop_interval_seconds`

例如：

```yaml
virsh:
  binary: "/usr/bin/virsh"
  shutdown_mode: "shutdown"
  start_mode: "start"
  start_interval_seconds: 60
  stop_interval_seconds: 30
```

这表示：

- 多台 VM 开机时，当前一台启动命令发出后，等待 60 秒再处理下一台
- 多台 VM 关机时，当前一台关机命令发出后，等待 30 秒再处理下一台

## 安装

```bash
cd vm-scheduler
sudo ./scripts/install.sh
```

安装脚本会：

- 创建 `/opt/vm-scheduler`
- 用 `uv` 建立项目虚拟环境
- 拷贝代码和示例配置
- 安装 `systemd` unit
- `daemon-reload`
- 启用并启动两个 timer

## 卸载

```bash
sudo ./scripts/uninstall.sh
```

卸载脚本会停止并移除：

- `vm-scheduler-start.timer`
- `vm-scheduler-stop.timer`
- `/opt/vm-scheduler`
- `/etc/vm-scheduler`

## 调整时间

默认定时器：

- 开机：工作日 `08:55`
- 关机：工作日 `15:05`

如果你需要盘后任务，可以直接修改：

- `systemd/vm-scheduler-start.timer`
- `systemd/vm-scheduler-stop.timer`

然后重新执行安装脚本，或手动复制 unit 并执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart vm-scheduler-start.timer vm-scheduler-stop.timer
```

## 交易日 SQL 说明

项目当前已经按你的现有交易日历实现预置默认 SQL。

默认 SQL：

```sql
SELECT bool_and(is_trading_day)
FROM trading.md_trading_calendar
WHERE trade_date = %(today)s
  AND exchange IN ('SH', 'SZ')
```

这与参考代码逻辑一致：只有上交所和深交所当天都可交易，才会执行 VM 开关机。

## 手动测试

```bash
/opt/vm-scheduler/.venv/bin/vm-scheduler start --config /etc/vm-scheduler/config.yaml
/opt/vm-scheduler/.venv/bin/vm-scheduler stop --config /etc/vm-scheduler/config.yaml
```

只做交易日判断但不真正执行 `virsh`：

```bash
/opt/vm-scheduler/.venv/bin/vm-scheduler start --config /etc/vm-scheduler/config.yaml --dry-run
```

## 多 VM 策略

当前版本支持：

- 所有开机目标使用同一个开机触发时间
- 所有关机目标使用同一个关机触发时间
- 多 VM 串行执行，避免并发触发
- 通过统一间隔配置降低多台 Windows VM 连续启动带来的瞬时冲击

当前版本不支持：

- 每台 VM 单独定义不同 timer 时间
- 每台 VM 使用不同间隔

## 后续扩展建议

- 按宿主机拆分多份配置，例如 `config.prod.yaml`、`config.dev.yaml`
- 将密码从 YAML 中移到环境变量或 `systemd` 的 `EnvironmentFile`
- 为不同 VM 组定义不同的开关机时间
- 增加节假日前缩短交易时段的特殊处理
