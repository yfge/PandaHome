# P2P 打洞与中继回退

PandaHome 使用官方 frp 的 **XTCP** 连接两端，打洞失败时可自动回退到
**STCP** 服务器中继。当前提供 TCP 服务访问，管理入口为 `/p2p`，独立于
UPnP/DDNS 和 `/access` 的公网发布流程。它不自动安装 frp、部署云服务器、
开放路由器端口或创建 DNS 记录。

访问者需要在外出的电脑上运行 `frpc`，再通过本机端口访问家中的服务。
例如，家中的 `192.168.1.10:8080` 可映射为外出电脑的
`http://127.0.0.1:18080`。它没有生成一个任意浏览器都能直接访问的公网网址。
两端客户端和公网协调服务器的职责见 [frp 官方 XTCP 示例](https://gofrp.org/en/docs/examples/xtcp/)。

## 连接流程

1. PandaHome 运行家庭侧 `frpc`，向用户提供的公网 `frps` 注册服务。
2. 访问者运行下载的 visitor 配置，同样连接 `frps`，并监听
   `127.0.0.1:<bind_port>`。监听地址固定为本机回环地址。
3. visitor 使用 `keepTunnelOpen = true`，主动尝试建立并保持 XTCP 通道；
   应用连接本地端口时可复用已经建立的通道，由双方直接传输。
4. 服务开启中继回退时，建立连接超过 `P2P_FALLBACK_TIMEOUT_MS` 后可通过
   STCP 中继承接本次连接。之后的新连接仍可使用已经建立的 P2P 通道。

STCP 回退 visitor 使用 `bindPort = -1`，不额外监听本地端口。
关闭服务的中继回退选项后，仅尝试 XTCP，打洞失败时连接失败。
回退行为和超时的含义见 [frp XTCP 说明](https://gofrp.org/en/docs/features/xtcp/)。

## 准备公网 frps

需要一台家庭侧和访问侧都能连接的公网服务器。首次部署时，从
[frp 官方发布页](https://github.com/fatedier/frp/releases/tag/v0.71.1)
下载对应操作系统和 CPU 的压缩包，解压 `frps`、`frpc`。建议服务器、家庭侧、
访问侧固定使用同一版本；这里的配置示例采用 v0.71.1，其他版本需另行验证。
二进制应由运行服务的账号可执行。

在服务器上创建 `frps.toml`，将占位 token 替换为随机且足够长的值：

```toml
bindPort = 7000
auth.method = "token"
auth.token = "replace-with-a-long-random-token"
transport.tls.force = true
```

先检查配置，再启动进程：

```bash
chmod 600 frps.toml
./frps --version
./frps verify -c ./frps.toml
./frps -c ./frps.toml
```

允许服务器防火墙和云安全组接收 TCP 7000，或你实际配置的 `bindPort`。
此处使用 TCP 连接 `frps`，无需为每项服务分配公网业务端口。STCP 也是通过
双方客户端访问，见 [frp STCP 说明](https://gofrp.org/en/docs/features/stcp-sudp/)。
更完整的鉴权配置见 [frp 服务端配置](https://gofrp.org/en/docs/reference/server-configures/)。

### TLS 与服务器身份

上面的最小配置强制传输加密，但未配置证书时，frps 使用自动生成的证书。
frp 默认客户端 TLS 不验证该证书，因此不能据此确认服务器身份。
远程使用应配置自己的服务器证书和可信 CA：

```toml
# 添加到服务器的 frps.toml
transport.tls.certFile = "/etc/frp/server.crt"
transport.tls.keyFile = "/etc/frp/server.key"
```

家庭侧配置 `P2P_TLS_TRUSTED_CA_FILE` 指向签发服务器证书的 CA PEM 文件；
若连接地址与证书名称不同，用 `P2P_TLS_SERVER_NAME` 指定证书中合法的 DNS 名称。
PandaHome 将信任设置写入家庭侧配置，并让下载的 visitor 引用同目录的
`frps-ca.crt`。管理员可在页面下载 CA，或使用 `GET /api/p2p/ca`，与
`visitor.toml` 一起交给访问者。CA 证书可以分发，服务器私钥不得分发。
证书信任与双向验证的完整说明见 [frp TLS 文档](https://gofrp.org/en/docs/features/common/network/network-tls/)。

## 配置 PandaHome 家庭侧

将 `frpc` 放入后端运行账号的 `PATH`，或者设置它的绝对路径。
在 `api/.env` 中配置独立的 P2P 变量：

```dotenv
P2P_SERVER_ADDR=frps.example.com
P2P_SERVER_PORT=7000
P2P_TOKEN=replace-with-the-same-frps-token
P2P_BINARY=/usr/local/bin/frpc
P2P_STATE_DIR=~/.local/state/pandahome
P2P_STUN_SERVER=stun.easyvoip.com:3478
P2P_FALLBACK_TIMEOUT_MS=1500
P2P_RETRY_INTERVAL_SECONDS=10
P2P_TLS_TRUSTED_CA_FILE=/etc/frp/ca.crt
P2P_TLS_SERVER_NAME=frps.example.com
```

| 变量 | 默认值 | 作用 |
| --- | --- | --- |
| `P2P_SERVER_ADDR` | 空 | 公网 frps 地址，配置后才能启动服务 |
| `P2P_SERVER_PORT` | `7000` | frps TCP 监听端口 |
| `P2P_TOKEN` | 空 | 与 frps 一致的共享鉴权 token |
| `P2P_BINARY` | `frpc` | 官方客户端可执行文件名或路径 |
| `P2P_STATE_DIR` | `~/.local/state/pandahome` | 状态根目录，P2P 配置存于其 `p2p/frp/` 子目录 |
| `P2P_STUN_SERVER` | `stun.easyvoip.com:3478` | 两端使用的 STUN 服务 |
| `P2P_FALLBACK_TIMEOUT_MS` | `1500` | visitor 等待 XTCP 后尝试 STCP 的时间，毫秒 |
| `P2P_RETRY_INTERVAL_SECONDS` | `10` | 后端恢复已启用服务的检查间隔，秒 |
| `P2P_TLS_TRUSTED_CA_FILE` | 空 | 家庭侧用于验证 frps 证书的 CA PEM 文件路径 |
| `P2P_TLS_SERVER_NAME` | 空 | 可选的 TLS 服务器证书名称 |

STUN 配置字段见 [frp 客户端配置](https://gofrp.org/en/docs/reference/client-configures/)。
环境变量修改后重启后端。运行账号必须能读取二进制、CA 文件并写入状态目录；
后台会恢复数据库中已启用的服务，无需一直打开管理页面。

在仓库根目录更新依赖后，执行数据库迁移：

```bash
cd api
alembic upgrade head
```

P2P 服务保存于 `p2p_services`，每项服务具有独立访问密钥。
登录管理员账号，打开 `/p2p`，添加服务名称、家庭侧可达的 IPv4 地址、TCP 端口，
并选择是否启用、是否允许中继回退。地址可用 `127.0.0.1`，表示运行后端的主机。
后端以一个独立 `frpc` 进程管理全部 P2P 服务，并在失败后重试；
不要再手动启动同一份家庭侧配置。该进程与 `/access` 的公网中继进程隔离。

## 进程与部署约束

每个 `P2P_STATE_DIR` 仅支持一个后端进程、一个 worker。生产启动时使用单 worker，
不要让多个后端实例、多个 worker 或其他手动 `frpc` 共用同一份 P2P 状态目录和
服务配置。进程内的协调锁不提供跨进程所有权互斥。

在 macOS/Linux 等 POSIX 系统上，P2P 的进程链为：
`后端 → 守护进程 G → 看护进程 W（独立会话）→ frpc`。
W 是 `frpc` 的唯一创建者，G 监控 W，W 监控后端与 G，约每 `0.05` 秒检查一次。
后端和 G 的身份由启动前确定的 **PID 与进程创建时间** 共同识别，避免仅凭一个
可能被重新分配的 PID 判断原进程仍然存活。

正常清理时，W 先向 `frpc` 发送终止信号，等待最多 `1` 秒，再按需强制终止并
等待最多 `1` 秒。G 给 W 最多 `2` 秒退出时间，随后强制清理 W 所拥有的整个
进程组。G 在进程组清理完成前保留尚未回收的 W 会话首进程，之后才回收它，
避免进程组标识被重用后误操作其他进程。它不会接管其他手动启动的 `frpc`。

这条启动链覆盖后端被 `SIGKILL`、G 或 W 其中一个被单独 `SIGKILL`，以及后端
停止等待超时后强制终止 G 的情况。清理有等待上限，并依赖剩余监控进程能够
正常获得调度；它不是瞬时完成，也不保证在全部监控进程同时丢失后仍能清理。
外部服务监督器需要能够停止完整进程树，以处理这种边界情况。公网中转与 P2P
共用这条启动链，各自的配置目录、守护进程和进程组仍然独立。

后端重新启动后会重新读取数据库、恢复已启用服务；仅有旧配置文件不表示旧服务
应该继续运行。改变任意 P2P 服务导致共享进程重启时，其他 P2P 连接也会中断，
具体影响见下文。

## 从外部电脑访问

1. 在另一网络的电脑上准备兼容的 `frpc`。
2. 管理员为服务下载 visitor TOML，另存为 `visitor.toml`，指定未占用的本地端口，
   例如 `18080`。
3. 配置了 CA 时，也下载 `frps-ca.crt`，保存在 visitor 配置所在目录。
4. 以下假设 `frpc` 二进制也在该目录，在该目录执行：

   ```bash
   chmod 600 visitor.toml
   ./frpc --version
   ./frpc verify -c ./visitor.toml
   ./frpc -c ./visitor.toml
   ```

5. 另开终端或浏览器连接本机端口，例如 `http://127.0.0.1:18080`。
   代理 SSH 等服务时，使用相应客户端，例如 `ssh -p 18080 user@127.0.0.1`。

visitor 的本地监听及回退配置见 [frp visitor 配置](https://gofrp.org/en/docs/reference/visitor/)。
HTTP 应用如果强制原域名、HTTPS 证书名称或重定向，仍需按该应用的要求配置客户端；
TCP 转发不会改写业务 URL 或替应用完成登录。

visitor 配置同时包含 **frps 的共享 token 和该服务的访问密钥**。
仅分发给可信任的访问者，通过私密渠道传输并限制文件读取权限。
共享 frps token 本身不是“仅访问此服务”的凭据；对不互信的使用者，应隔离
frps 实例或另行设计服务器鉴权策略。保持 `.env`、数据库、生成配置和备份私有，
不要把它们提交到仓库或粘贴进日志。

修改服务目标、回退设置、服务器参数或轮换密钥后，重新下载并重启 visitor。
P2P 服务共用一个家庭侧进程。改变目标、回退设置、启用状态或密钥时，若仍有
已启用服务，后端重启该 P2P 进程；没有已启用服务时停止它。因此这些操作也会
中断其他 P2P 服务的现有连接，`/access` 的公网中继不受此进程重启影响。
轮换密钥后旧配置不能再建立该服务的新连接，但不能把配置删除或密钥轮换当成
业务系统全部已有会话的即时撤销保证。客户端已保存的文件不会被远程删除。

## 网络条件与结果判断

- CGNAT 不等于一定无法打洞。双方 NAT 行为、防火墙、UDP 可用性都会影响结果。
- XTCP 通道使用 UDP 传输；两端需要能访问 STUN，并允许打洞所需的 UDP 收发。
  严格 NAT、多层 NAT 或 UDP 被屏蔽时可能失败。仅放通 frps 的 TCP 端口不保证直连。
- STCP 回退需要双方持续连通 frps，其带宽和流量消耗由中继服务器承担。
  可先开启回退保证可用，再在另一网络单独验证直连。
- 家庭侧受管进程运行表示客户端正在尝试注册或等待连接。页面的“等待连接”不是
  “已成功打洞”；`connection_type = unknown` 表示后端没有获得某次 visitor 连接的路径证据。
- 本地 TCP 目标检查、frps 注册、visitor 访问成功、确认 XTCP 直连是不同层次的证据。
  启用回退时，访问成功也可能经过 STCP。需要结合访问侧日志或实际网络观测判断。

打洞成功率限制来自 [frp 官方 XTCP 说明](https://gofrp.org/en/docs/features/xtcp/)，
不能仅凭家庭网络有无公网 IPv4 下结论。

## 管理 API

以下接口全部要求当前有效的管理员 Bearer token，普通用户不能读取配置、下载
凭据或触发运行操作。完整请求和响应以 FastAPI `/docs` 为准。

| 方法与路径 | 作用 |
| --- | --- |
| `GET /api/p2p` | 提供方配置状态、服务列表和运行状态，不返回访问密钥 |
| `POST /api/p2p/services` | 创建服务，字段包括 `name`、`local_ip`、`local_port`、启用和回退设置 |
| `PUT /api/p2p/services/{id}` | 更新服务配置 |
| `DELETE /api/p2p/services/{id}` | 删除服务并重建剩余 P2P 配置；没有服务时停止进程 |
| `POST /api/p2p/reconcile` | 立即协调已保存配置和进程状态 |
| `POST /api/p2p/services/{id}/rotate-key` | 轮换服务访问密钥 |
| `GET /api/p2p/services/{id}/visitor?bind_port=18080` | 下载原始 visitor TOML，包含凭据 |
| `GET /api/p2p/ca` | 配置 CA 时下载公开 CA 证书 |

## 排查顺序

1. 确认两端 `frpc` 和 `frps` 版本、配置校验、服务器地址、TCP 端口与 token 一致。
2. 配置 CA 时检查路径、证书有效期、SAN 名称，以及 visitor 工作目录中的 CA 文件。
3. 从后端所在主机确认目标 IPv4 和 TCP 端口可达；回环地址只指向该主机自身。
4. 从另一网络启动 visitor 并实际连接本地端口；日志里要区分 XTCP 和 STCP。
5. 回退可用但 XTCP 失败时，检查双方 UDP/STUN 访问和 NAT 条件。关闭回退可辅助
   验证纯 XTCP，但这会降低可用性；排查后按需求恢复。

PandaHome 不根据进程存活编造连接路径，也不将配置校验或本机联通测试称为
真实跨网打洞验收。

## 本机进程守护回归

安装后端测试依赖后，在仓库根目录运行：

```bash
python -m pytest -q api/tests/test_process_guard.py api/tests/test_p2p_service.py api/tests/test_relay.py
```

其中 `test_process_guard.py` 创建真实 Python 子进程和本机 TCP 监听，验证正常
终止、后端或单个监控进程被强制终止、启动中断、忽略终止信号的原生进程、
停止超时后的强制清理、进程创建时间不匹配，以及两个服务的进程组清理隔离。
其他两个测试文件同时检查公网中转与 P2P 使用共享启动契约，没有重复包装。
这些测试不需要 frp 二进制，不访问真实路由器，也不证明 frps 注册或 NAT 打洞。

## 本机原生 frp 测试

开发者可准备解压后的 frp 目录，其中包含可执行的 `frpc` 和 `frps`，然后在
仓库根目录显式启用原生测试：

```bash
PANDAHOME_FRP_BIN_DIR=/path/to/extracted/frp python -m pytest -q api/tests/test_p2p_native.py
```

该测试使用本机环回地址运行服务和客户端，验证生成配置与真实 frp 进程的配合；
它不经过家庭 NAT、运营商 CGNAT 或外部网络，不能证明真实跨网打洞成功。
跨网验收仍需在另一网络运行 visitor、访问实际服务，并确认连接路径。
