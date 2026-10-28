# PandaHome UE/UI 独立审查

审查日期：2026-10-28 至 2026-10-29（Asia/Shanghai）。最新状态：**UI独立验收通过，总签收恢复；原4项P2及UPnP两轮追加焦点问题全部闭环。** Access追加保持通过，UPnP最终受影响验收对应提交`4efe286d9afc595f440adfd258fbf354ab6127f2`。下方待修记录均为历史，最新结论以[Final UPnP menu acceptance](#final-upnp-menu-acceptance)为准。四条真实路由均可达；未发现本轮截图中的P0/P1或需要重设计的视觉阻塞。

最终冻结runtime SHA256为`ae4fe9555c8d9057476a577e44ed5854e0ebec9c5088b4a661271e4b2fa0db1e`，测试SHA256为`5626b4602582e4dcba5ebf580fad1a668674d499d8049ef82417a29716aac9fb`；原UPnP owner三路径私有交付见[ready.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a1831d-1a81-7ae2-aef0-34e6c0e417b7/upnp-pending-menu-20261028-174135/ready.json)，Access交付owner已审查提交。reviewer从冻结来源复制唯一runtime文件，独立构建、浏览器复验与结束指纹均通过，没有修改产品代码、共享index或提交。

## Final UPnP menu acceptance

2026-10-29最终受影响复验：**通过，无未关闭UE/UI阻塞；恢复总签收。** 原先确诊的pending外层菜单抢焦点P2关闭，原快速关闭48条证据保留，不扩展其它已冻结产品域。

默认`npm run build`通过（Turbopack、TypeScript、11页生成），真实生产`/upnp` HTTP200且无重定向，build ID为`WNuxYqgUqqLz8nAwYvWDA`。冻结来源、隔离副本、复验后工作区、提交`4efe286`的runtime内容一致；Access两文件仍与批准的原SHA一致。测试文件的`5626...c9fb`也与该提交一致。见[构建日志](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/production-build.log)、[生产路由/build ID](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/production-build-and-route.json)、[冻结指纹](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/source-freeze.json)、[复验后与提交指纹](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/source-consistency.json)。

| 受影响检查 | 独立结果 | 证据 |
| --- | --- | --- |
| 原EN390 Edit503 Home路径 | 3/3通过：两次Escape退出弹窗/菜单，原生Tab到真实Home A；释放503后40/350ms均保持Home，无迟到trigger focus调用 | [原生时间线与focus调用记录](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/pending-menu-reproduction.json) |
| 提交中关闭完整矩阵 | 48/48通过：EN/ZH×390/1440×Add/Edit/Delete×503/成功×导航/不导航；24个导航目标均为真实Home/首页链接，40/350ms不抢回；无旧dialog/disabled焦点；未导航时恢复Add/原菜单项，末行删除成功返回Add | [48组结果与逐键记录](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/pending-results.json) |
| 原inline503、草稿与重试 | 12/12通过：EN/ZH×390/1440×Add/Edit/Delete错误均位于当前弹窗可见视口且获焦；草稿保留，继续编辑不被旧错误抢焦点；12次成功重试正常关闭 | [错误/草稿/请求体结果](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/error-gateway-results.json) |
| 第二网关目标隔离 | 上述12组均显式选择192.168.2.1，WAN与映射展示一致；每次GET/POST/DELETE携带该device_url，默认网关未变 | [完整DOM与请求](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/error-gateway-states.json) |
| 普通菜单Escape | EN/ZH×390/1440共4/4通过，Arrow导航后Escape仍返回Actions按钮 | [普通菜单结果](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/ordinary-menu-results.json) |

25张本轮PNG均逐张通过`view_image`检查，见[图片与SHA索引](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/screenshots.json)、[最终汇总](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/acceptance-summary.json)、[回放脚本](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/replay/upnp-menu-final-probe.mjs)。pending首轮7组通过后因驱动4次Tab上限仍停在隐藏guard而中断，已保留原日志；改为明确退出菜单并导航到实际可用控件后，接续完成余下41组，未改源码且没有将guard算作有效目标。

API全部mock；成功重试和网关隔离证明界面/请求处理，不证明真实路由器、DNS、frp或公网连通。原快速48在上一候选`55e5...cc6d`的完整证据保持通过；本次唯一新增guard所影响的pending/普通菜单/错误路径如上复验，不把旧截图误作新源码截图。自己的独立生产3110、Chrome9239已停止，端口清空。

![最终修复后，原生导航Home在503结束后保持焦点](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/pending-edit-menu-fixed-3.png)

![最终中文手机编辑失败：错误获焦、草稿保留、可重试](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-menu-final/error-edit-zh-390.png)

## Scope and evidence

审查目标：用户在桌面与 390px 手机宽度下，以 EN/ZH 识别公网发布、配置指南、多网关端口映射与私有 P2P 的状态，完成添加/取消/删除确认，并在失败时知道如何恢复。

- 四条实际 Next 页面：`/access`、`/access/setup`、`/upnp`、`/p2p`；16 组语言与视口组合。
- `/access`、`/upnp`、`/p2p` 的加载、空列表、503、403、普通用户状态；新增表单、校验、删除确认、键盘 Enter/Tab/Escape、切换第二台路由器。
- 隔离副本 `/tmp/pandahome-ue-ui-20261028/web`，独立预览端口 3109，Chrome headless 独立 profile 与 CDP 9239。内置浏览器入口未提供，Chrome connector 的 9222 返回 404，因此使用独立 Chrome 原生 CDP。未操作其他聊天的页面或开发服务。
- API 在当前页面初始化时由 fetch mock 拦截；请求记录保存在证据 JSON。没有调用真实 DNS、UPnP、frp 或生产写入。
- 截图均为本轮 Chrome 捕获，保存后用 `view_image` 检查。初始源码快照与复验源码分开记录，避免将旧图视作最终提交证据。
- 全套索引：[matrix.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/matrix.json)、[interactions.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/interactions.json)、[failure-interactions.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/failure-interactions.json)、[源码摘要](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/source-snapshot-sha256.json)、[回放脚本](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/replay/cdp.mjs)。

优先级：P0/P1 为阻断或重大破坏；P2 为可稳定复现的重要交互/无障碍缺陷，建议本次验收前关闭；纯个人审美偏好不列问题。

## UPnP candidate follow-up — historical pending menu focus P2

历史候选结论：源码`55e5ae736126a6d07be06eb133b206b9160950696c7aeff6eecac645894acc6d`当时已修复原快速关闭，但新增提交中退出外层菜单的P2使签收暂停。**该P2现已由`ae4...`/`4efe286`修复并在上方Final UPnP menu acceptance独立关闭。** 以下保留修复前证据；只由原UPnP owner整改，reviewer未改产品、index或commit。

本次从owner私有冻结文件复制唯一runtime改动`web/src/components/upnp/mapping-list.tsx`到隔离Next副本，默认`npm run build`通过，生产build ID`hJ1dWJWXRYleKwDWo9j-l`，实际`/upnp` HTTP200。复验前后源码SHA不变，内容与提交`e8be058`一致；Access原两SHA也保持。见[生产构建日志](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/production-build.log)、[路由与build ID](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/production-build-and-route.json)、[冻结指纹](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/source-freeze.json)、[复验后与提交指纹](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/source-consistency.json)。

原快速路径已关闭：EN/ZH×390/1440×Add/Edit/Delete×Escape立即Tab、Escape20ms后Tab、Cancel立即Tab、Cancel立即Shift+Tab，共48/48通过；另捕获24条稳定关闭同键基线。立即Escape组实际间隔1.0–4.3ms，20ms组22.0–25.1ms，Cancel组2.7–7.3ms；即时、40ms、350ms均无旧dialog焦点、无迟到回拉，并与稳定基线一致。编辑/删除保留原菜单项，随后的Arrow与Escape行为也与基线一致；取消无写请求。12张快速路径截图均逐张查看。见[原生48条时间线](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/rapid-sequences.json)、[稳定基线](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/stable-baselines.json)。

**新增P2最小复现（EN390，重复3/3）：**

1. 进入`/upnp`，从映射菜单打开Edit，保存有效草稿；mock暂停编辑流程的首个DELETE响应，入口仍disabled。
2. Escape关闭表单，再Escape关闭外层映射菜单，连续Tab到可见的Home链接。本次3次Tab间隔约10ms；中间Radix隐藏focus-guard不算有效导航目标。
3. 确认焦点已在真实`A: Home`，释放503。40ms仍在Home、busy已结束；350ms却被拉回`Actions for NAS Web 管理`。

第三次原生时间线：Escape表单2312.4ms→Escape菜单2316.6ms→Tab到Home2344.6ms→释放503为2359.2ms→40ms观测Home2401.7ms→2503.7ms焦点跳回映射菜单按钮。三次Home至被抢回间隔135.0–180.2ms。预期是保留用户已到达的Home；只有BODY或内部guard仍无有效用户目标时，完成写入后才恢复合理入口。

已捕获`HTMLElement.focus`调用栈，回拉来自生产chunk `baa220319755c73a.js:1:48886`。对应代码为Radix DropdownMenuContent默认`onCloseAutoFocus`中的`triggerRef.current?.focus()`；与本候选新加的pending恢复effect区分明确。见[3次原生事件/焦点调用栈](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/pending-menu-reproduction.json)、[DOM与请求](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/pending-menu-states.json)、[栈与依赖源码对应](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/focus-origin.json)、[最小回放](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/replay/upnp-pending-menu-probe.mjs)。3张复现截图均逐张查看；截图显示最终被拉回位置，Home与毫秒顺序以DOM/事件记录为依据。

最小整改建议位置：[mapping-list.tsx:469](/Users/geyunfei/dev/yfge/PandaHome/web/src/components/upnp/mapping-list.tsx:469)的`DropdownMenuContent`。关闭后的自动恢复需尊重用户已经导航到菜单外有效控件；正常BODY/guard场景仍保留返回触发按钮的行为，避免破坏原菜单键盘路径。此处仅为review建议，由原owner实现并自测。

pending完整矩阵在第6组真实失败处停止，前5组通过；未将剩余组合或尚未执行的本轮inline503/第二网关回归写为通过。两次更早驱动过宽断言的原始记录也已保留：一次误把隐藏focus-guard当有效导航，一次在busy尚未结束的40ms点强制要求恢复。修正这两项后，以上真实Home抢回仍独立重复3/3，不能归因于驱动。

当时全部API使用mock，暂停与释放的是本地模拟响应，无真实DNS、路由器或网络写入，独立进程已停止。此处计划的pending菜单P2及必要同类路径、inline错误/草稿重试/第二网关回归现已在最终复验完成；原快速48条证据保留。

![候选中原Escape立即Tab已正常前进到映射操作按钮](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/rapid-add-en-390.png)

![新增pending菜单P2：Home已获焦后，迟到回调又拉回映射按钮](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-fix/pending-edit-menu-race-3.png)

## UPnP rapid-close follow-up — historical initial race

2026-10-29历史记录：当时UI-01的UPnP快速关闭路径重新打开。该初始race已由候选48/48关闭，后续[历史pending菜单P2](#upnp-candidate-follow-up--historical-pending-menu-focus-p2)也已在最终复验关闭。当时只复现EN、390×844、UPnP新增弹窗三组连续操作，每组重复3次，共9/9稳定复现；未扩展P2P或其它产品路径。以下保留修复前证据。

复现步骤：打开真实生产`/upnp`页面，以Enter打开Add Mapping；①Escape后立即Tab；②Escape后固定等待20ms再Tab；③聚焦Cancel，以Enter取消后立即Tab。两键间没有等待焦点恢复。分别在Tab后即时、40ms、350ms读取焦点并记录原生keydown/focusin时间线。

| 序列 | 实际两键间隔 | 即时与40ms焦点 | 350ms焦点 | 重复 |
| --- | --- | --- | --- | --- |
| Escape→立即Tab | 1.5–2.9ms | 已关闭但仍退出动画中的`#upnp-protocol` | Add Mapping | 3/3 |
| Escape→20ms→Tab | 23.2–24.2ms | 已关闭但仍退出动画中的`#upnp-protocol` | Add Mapping | 3/3 |
| Cancel Enter→立即Tab | 3.7–7.3ms | 已关闭但仍退出动画中的Add提交按钮 | Add Mapping | 3/3 |

实际：用户下一次Tab先进入关闭中的弹窗控件，197.2–344.4ms（相对关闭按键）之后迟到恢复回调再把焦点拉回Add Mapping。第一组精确时间线：Escape在3046.3ms，Tab在3049.2ms，3050.4ms进入`#upnp-protocol`，3251.9ms被拉回Add Mapping。对照：等待稳定关闭后Tab正常到`Actions for NAS Web 管理`；因此预期是在关闭时恢复触发点，让连续Tab到达映射操作按钮并保持，不被迟到回调覆盖。

源码依据与建议定位：[mapping-list.tsx:58](/Users/geyunfei/dev/yfge/PandaHome/web/src/components/upnp/mapping-list.tsx:58)的恢复方法本身同步，但[表单回调:491](/Users/geyunfei/dev/yfge/PandaHome/web/src/components/upnp/mapping-list.tsx:491)只由Radix `onCloseAutoFocus`调用；弹窗退出动画结束前仍存在于DOM。关闭处理与延迟回调需共同保证用户后续移动焦点后不会被拉回。删除共用的回调也由owner作为受影响路径复验，本次未以未测路径推定缺陷。

本次复用已构建的隔离production，未重新构建、未改产品代码。build ID为`WOBdL5D_-_0tZlSGzLxvh`；`mapping-list.tsx` SHA256为`b3ad45e3f9119d83f20db14ada8b22e1801ec0b4ab9332b7abd8e6029bb1a056`，副本、工作区与`63c4b99`内容一致，复验前后未变。另核对form-dialog、dialog-error和共享Dialog源码均一致。见[冻结指纹](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-probe/source-freeze.json)、[结束指纹](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-probe/source-consistency.json)。

证据：[9组结果](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-probe/probe-summary.json)、[原生逐键焦点时间线](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-probe/sequences.json)、[DOM与请求](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-probe/states.json)、[回放](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-probe/replay/upnp-rapid-probe.mjs)。4张截图均逐张打开检查；截图显示最终焦点，毫秒顺序以事件JSON为依据。全部API mock且无写请求，不证明真实设备行为。独立3110/9239进程已停止，端口无本轮监听。

该历史race的快速导航门槛已由候选48/48完成；新增pending菜单P2与剩余受影响回归也已由Final UPnP menu acceptance关闭，总签收恢复。

![稳定关闭后Tab的对照，焦点在映射操作按钮](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-probe/baseline-stable-close-tab.png)

![快速Escape后Tab的实际结果，迟到回调把焦点拉回Add Mapping](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/upnp-rapid-probe/escape-gap0-after350.png)

## Access follow-up acceptance

2026-10-29（Asia/Shanghai）受影响复验结论：**通过，可验收；没有新增UI阻塞。** 本次只覆盖公网表单的错误聚焦与快速关闭，不重测其它冻结域。本节的两个SHA256及 `access-followup/` 证据覆盖下节初轮快照中的对应Access文件；原始截图、完整矩阵和其它域批准记录保留。

| 冻结文件 | 验收SHA256 |
| --- | --- |
| `web/src/app/access/page-client.tsx` | `be49002172f5d7491e20f156a96940a340687d0a51d5a237cf571fbdd95f62b8` |
| `web/src/components/access/service-form.tsx` | `5afefaced7fff1eab93807f367a2d4da3c861ce049ab47a54c2f38e33f7d14b1` |

复制前、隔离生产副本、复验后三处指纹均与批准值一致；默认 `npm run build` 再次通过。以冻结源码SHA作为验收基准，不等待commit整理；复验时HEAD `ffbeaa8` 尚未包含这两个冻结文件的全部最终内容，因此不把该HEAD误作UI基准。见[复验前冻结记录](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/access-followup/source-freeze.json)、[复验后指纹/构建记录](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/access-followup/source-consistency.json)。

1. EN/ZH×1440/390×新增/编辑/删除，分别连续发送 Escape→Tab（无等待、固定20ms）、取消→立即Tab、X关闭→立即Tab，共48组。零等待组实际两键间隔2.1–8.3ms；**两键之间没有等待焦点稳定**。48组均先恢复原触发控件，再正常前进；即时、40ms、350ms三次观测位置一致，没有迟到回调把焦点拉回。删除取消均未发送DELETE。见[逐键/焦点时间线](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/access-followup/rapid-sequences.json)、[步骤DOM](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/access-followup/rapid-states.json)。
2. EN/ZH×1440/390×新增/编辑，共8组合：空名称、无效IPv4、首次503、再次失败重试共32次错误检查均聚焦当前可见的 `role=alert`。无效草稿没有发起写请求；503前后草稿一致。见[错误步骤和焦点](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/access-followup/error-states.json)。
3. 校验后修改名称、修正IP、保存失败后继续修改名称，共24次检查均保持当前输入焦点，没有旧错误effect抢焦点。每组合在两次mock保存失败后成功重试，POST/PUT的目标与最终草稿正确，表单关闭并返回原触发点，共8次成功重试。见[组合结果及请求体](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/access-followup/error-results.json)、[验收汇总](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/access-followup/acceptance-summary.json)。
4. 28张新增截图已逐张打开检查；本次独立生产服务3110与专用Chrome9239已停止，端口无本轮残留。回放脚本保存在[follow-up replay](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/access-followup/replay/access-followup-rapid.mjs)。

![新增关闭后立即Tab，焦点已前进到网络检测，迟到回调没有拉回](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/access-followup/rapid-add-en-390.png)

![中文手机编辑保存失败，当前alert已获得焦点并完整可见](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/access-followup/save-error-edit-zh-390.png)

本轮API全部mock，成功重试证明界面处理与请求草稿正确，不证明后端持久化或真实DNS更新。Access owner负责的真实临时DNS创建/解析/删除，以及另行处理的DDNS漏RR问题，都属于独立后端/真实网络证据，不纳入本UI回执。

## Final acceptance

本节保留初轮完整范围验收，最新Access两文件与快速键盘/错误聚焦结论以上方Access follow-up acceptance及末尾独立提交复验为准；UPnP两轮追加问题现均关闭，以Final UPnP menu acceptance为准。

初轮历史结论：当时完整范围内4项P2在等待焦点稳定的检查中关闭。后续UPnP两轮race曾使签收暂停，现已全部独立闭环，**当前UI总签收恢复**；下文记录与`final-*`证据保留。

| 项目 | 最终独立结果 | 证据 |
| --- | --- | --- |
| 默认生产构建 | `npm run build` 通过，Turbopack/TypeScript/11页生成成功 | [构建与HTTP结果](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-production-build-and-routes.json) |
| 四条真实路由 | HTTP均200且无locale前缀重定向；16组EN/ZH×1440/390页面标题、根语言和布局宽度正确 | [生产矩阵](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-matrix.json) |
| UI-01 焦点 | 公网、UPnP、P2P的新增/编辑/删除取消，共18条EN390/ZH1440焦点路径通过；菜单打开的弹窗回到原菜单项，Escape再回操作菜单按钮 | [焦点与确认](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-controls.json) |
| UI-02 语言 | 实际语言菜单EN→ZH→EN及各自刷新保持通过，文档根语言与正文一致 | [语言切换和刷新](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-route-language-interactions.json) |
| UI-03 UPnP错误 | EN/ZH手机新增、编辑、删除失败均在弹窗内可见并聚焦错误；有效输入不再残留旧必填错误 | [新增/删除错误](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-errors.json)、[编辑错误](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-gateway-edit.json) |
| UI-04 P2P错误 | EN/ZH手机保存失败提示位于当前视口404–470px且在保存按钮旁；焦点移入错误，草稿保留 | [失败反馈](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-errors.json) |
| 多网关隔离 | 第二网关WAN/映射一致；列表和编辑的DELETE请求均携带第二网关device_url | [网关选择/请求](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-gateway-edit.json) |
| 初轮源码一致性 | 构建前105文件快照；复验后92个非测试、非系统元数据文件仍一致，变化仅为系统元数据和P2P测试文件 | [源码指纹](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-source-sha256.json)、[复验后比较](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-source-consistency.json) |

最终生产副本为 `/tmp/pandahome-ue-ui-20261028/final-web`，未复制环境文件；依赖在独立目录中通过文件硬链接复用，构建未写入共享 `.next`。所有修复后PNG已保存并逐张打开检查。审查结束后已停止自己的预览/Chrome子进程。

修复后关键画面：

![UI-01 修复后焦点返回添加按钮](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-focus-access-en-390.png)

![UI-03 修复后UPnP错误在当前弹窗内清晰可见](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-error-upnp-create-en.png)

![UI-04 修复后P2P错误在保存按钮附近可见](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/final-error-p2p-save-en.png)

## Findings and acceptance

### UI-01 · P2 · 关闭公网/UPnP弹窗后的焦点恢复（已关闭，含UPnP两轮追加复验）

复现：在 `/access` 聚焦 Add service，或在 `/upnp` 聚焦 Add Mapping；Enter 打开弹窗；输入框获得焦点；Escape 关闭；再按 Tab。

实际：关闭后 `document.activeElement` 为 BODY；Tab 跳到顶部 Home。在手机 UPnP 中，页面从 scrollY 334 回到 0。键盘用户失去刚才的操作位置。`interactions.json` 的 `access editor escape focus`、`upnp editor escape focus` 与随后的 Tab 记录可复现。

建议位置：`web/src/components/access/service-form.tsx`、`web/src/app/access/page-client.tsx`、`web/src/components/upnp/mapping-form-dialog.tsx`、`web/src/components/upnp/mapping-list.tsx`。手动控制 Dialog 时明确记录触发控件，并在关闭后恢复焦点；删除确认也按同一规则核查。

P2P补充：新增表单取消、内联删除确认取消后的焦点也为BODY；新增取消后下一次Tab仍可到Add service，因此不单独增加优先级。最终仍逐模块验证恢复到Add/Edit/Delete原触发控件。建议位置另含`web/src/components/p2p/p2p-manager.tsx`和`web/src/components/p2p/service-card.tsx`。

验收：新增、编辑、删除确认通过 Escape/取消关闭后，焦点返回原触发按钮，下一次 Tab 从该位置继续；不因焦点恢复跳到顶部；桌面、390px、EN/ZH 一致。

证据：[新增表单](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/33-access-form-mobile.png)、[公网关闭后错误焦点](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/34-access-after-dialog-escape-tab.png)、[UPnP关闭后错误焦点](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/39-upnp-after-dialog-escape-tab.png)。

![UI-01 UPnP 关闭弹窗后 Tab 回到页首](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/39-upnp-after-dialog-escape-tab.png)

### UI-02 · P2 · 英文页面的文档语言仍标记为中文（已关闭）

复现：切换 English 或以保存的英文偏好刷新任意审查页面；读取根元素语言。

实际：正文与按钮已为英文，`document.documentElement.lang` 仍为 `zh`。`failure-interactions.json` 每条英文记录的 `lang` 为 `zh`；根布局硬编码语言，语言 Provider 未同步文档语言。该问题影响屏幕阅读器的语言选择，不能从截图外观单独判断。

建议位置：`web/src/app/layout.tsx` 与 `web/src/components/providers/language-provider.tsx`。让当前 locale 同步文档根语言。

验收：EN 为 `en`，ZH 为 `zh`；切换后和刷新后均正确；界面内容与根语言保持一致。无需以此声称完整 WCAG 合规。

修复复验：同步主PM的语言Provider修复到独立副本；实际Next页面分别以已保存的EN、ZH、EN偏好重新加载，根语言/正文标题/存储值全部一致，390px通过。证据：[language-recheck.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/language-recheck.json)、[修复后英文截图](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/49-english-language-after-fix.png)。随后已在最终生产复验中验证实际菜单切换与两种语言各自的刷新恢复，见Final acceptance。

### UI-03 · P2 · UPnP 保存失败的错误提示被仍打开的弹窗遮住（已关闭）

复现：在 `/upnp` 打开 Add Mapping，填写有效 IPv4 和端口；令 POST 返回 503；提交。

实际：表单保留，但唯一失败反馈位于页面顶部 toast，弹窗遮挡绝大部分错误信息。截图仅露出 Failed 顶缘，用户看不到原因和恢复方向。toast 容器与 Dialog overlay 同为 z-50，且表单没有内联提交错误。此交互来自共享 UPnP 表单，应在多网关验收中一起覆盖。

建议位置：`web/src/components/upnp/mapping-list.tsx`、`web/src/components/upnp/mapping-form-dialog.tsx`，以及删除确认对应组件。优先把失败原因放在当前弹窗内，保留用户输入并允许重试；仅调整层级也须验证可读性和辅助技术可达性。

验收：新增/编辑/删除失败时，当前弹窗内可直接读到错误；错误与按钮均可键盘到达；保持输入/目标路由器；成功前不关闭或误报成功。

证据：[保存失败被遮挡](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/46-upnp-save-failure-mobile.png)、[校验对照](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/45-upnp-required-validation.png)、[公网503内联反馈对照](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/48-access-save-failure-mobile.png)。

![UI-03 UPnP 保存失败提示被弹窗覆盖](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/46-upnp-save-failure-mobile.png)

### UI-04 · P2 · 手机 P2P 保存失败后错误出现在当前视口之外（已关闭）

复现：390×844 的 `/p2p`，Add service，填写名称与有效主机参数，滚动到 Save service 并提交；令 POST 返回 503。

实际：表单保留，按钮重新可用，但错误只插在表单上方，提交后错误边界为 top=-133、bottom=-93（视口之外）；当前截图完全看不到失败反馈。DOM 有 role=alert，但未改变视觉用户当前看到的内容。`failure-interactions.json` 中 `p2p failed save` 保留了边界和请求。

建议位置：`web/src/components/p2p/p2p-manager.tsx`、`web/src/components/p2p/service-form.tsx`。将保存错误传入当前表单，在保存按钮附近展示，并按需要聚焦错误或保持焦点。全局加载错误仍可保留在页面。

验收：390px 下无需向上寻找即可看到保存失败原因；草稿保留、可重试；不与后台加载错误混淆；EN/ZH一致。

证据：[提交后实际视口](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/42-p2p-save-failure-mobile.png)、[全页定位错误在表单上方](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/43-p2p-save-failure-full.png)。

![UI-04 P2P 保存失败后的视口没有错误反馈](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/42-p2p-save-failure-mobile.png)

## Numbered flow and healthy observations

1. 打开公网服务，查看网络建议、待验证入口及服务操作；EN/ZH、1440px/390px 无整页横向溢出。配置成功与外网验证清楚区分。证据：[中文桌面](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/02-access-zh-1440-healthy-admin.png)、[英文手机](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/05-access-en-390-healthy-admin.png)。
2. 打开配置指南并阅读直连、中转与外网验证步骤；正文在手机重排，返回操作清楚。证据：[中文手机](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/07-access-setup-zh-390-healthy-admin.png)、[英文手机](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/09-access-setup-en-390-healthy-admin.png)。管理员配置项 disclosure 已在最终生产复验中通过键盘Enter展开，见final-17-setup-expanded.png。
3. 打开 UPnP 并切换第二台路由器；选择值、WAN 状态和列表请求的 device_url 一致。映射条目在手机纵向重排。证据：[有数据的完整手机页面](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/44-upnp-populated-full.png)、[第二台路由状态](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/37-upnp-second-router-mobile.png)。
4. 打开 P2P，检查家庭代理与访客配置说明；“运行中”明确未宣称打洞成功。名称、地址与端口可读，移动端按钮正常换行。证据：[中文手机](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/15-p2p-zh-390-healthy-admin.png)、[英文手机](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/17-p2p-en-390-healthy-admin.png)。
5. 打开三个模块新增表单；标签清楚，错误保留输入；公网自定义校验和 UPnP 必填校验可见；P2P表单第一次Tab可达名称。失败反馈缺陷见UI-03/04。证据：[公网校验](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/47-access-required-validation.png)、[UPnP校验](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/45-upnp-required-validation.png)、[P2P键盘表单](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/40-p2p-form-keyboard-mobile.png)。
6. 打开公网和P2P删除确认，没有在首次点击时立即发出 DELETE；公网对话框默认焦点为取消，P2P采用内联二次确认。证据：[公网删除确认](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/35-access-delete-mobile.png)、[P2P删除确认](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/41-p2p-delete-mobile.png)。
7. 加载时显示骨架或状态并禁用相关操作，空列表有添加入口；503有重试路径；公网普通用户显示管理员要求，P2P普通用户只显示权限说明。证据：[加载](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/18-access-en-390-loading-admin.png)、[空列表](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/19-access-en-390-empty-admin.png)、[失败](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/20-access-en-390-failure-admin.png)、[公网权限](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/30-access-zh-390-forbidden-user.png)、[P2P权限](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18323-4d6f-7cb1-819a-cf6e1cab4dab/ue-ui-review/32-p2p-zh-390-forbidden-user.png)。

## Limits and remaining verification

- 这轮是实际 Next 页面加 mock API 的浏览器体验证据，不证明真实路由器、DNS、frp 打洞、中转或生产部署可用。
- 初始10–13号UPnP截图的fixture曾误用裸数组，实际显示空列表；这些图片不作为有映射条目的验收证据，已以36/37/44号更正。初次未正确发出Enter字符的交互试跑已废弃，interactions.json与33–41号图来自修正后的实际键盘事件。
- 最终代码持续由三位owner修改；初始副本不是最终提交快照。旧middleware在dev模式未触发重定向，首轮没有据此关闭生产路由阻塞；最终已在独立生产构建中通过原始HTTP和浏览器导航验证四路由均无locale重定向。
- 未运行真实设备、屏幕阅读器、iOS/Android软键盘、系统缩放、所有对比度组合；不声明完整无障碍认证。首轮截图中的dev指示器属于开发模式，最终生产截图已无该指示器。
- 四项P2与生产路由均已闭环；没有待整改的审查事项。项目经理仍需将本报告与后端、部署/真实网络证据分别汇总，不应把本轮mock浏览器通过表述为真实网络接通。


## Independent committed Access recheck — e3775d1

2026-10-29（Asia/Shanghai），由 `access_ui` 独立复核 agent 对主协调者当前焦点小修重新执行，结论：**通过；本次 Access 快速关闭及错误修正阻塞已关闭，未发现新增 UE/UI 阻塞。** 本节基准是完整提交 `e3775d12ab216544d627eda74a5aaf96196a9a42`，独立运行结果优先于此前尚未按提交对齐的 Access 记录；保留全部原始截图与前后证据。本节没有重复主协调者的运行结果作为独立证据。

审查目标是键盘用户关闭公网新增、编辑、删除确认后，继续操作原来的位置；保存失败后能读到错误、保留草稿、修正输入并重试。只复验受影响 `/access`，未扩大其它产品域。

- **隔离与来源。** 从 `git archive e3775d1 web` 创建 `/tmp/pandahome-independent-e3775d1-jz3vccz9/web`，使用独立 `.next`、既有依赖的 APFS 克隆副本、生产端口 3127、专用 Chrome profile/CDP 9253。四个 Access 源码/测试文件均逐字比对提交内容，运行前后 SHA256 不变。为完成 Next.js 16 全量构建，单独复制已审查的域名记录 promised-params 修复；这是构建依赖覆盖，不是 Access 产品变更，路径与指纹详列 [provenance.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/provenance.json) 和 [source-consistency.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/source-consistency.json)。没有复制环境凭据、共享构建产物或使用共享浏览器。
- **构建和测试。** 默认生产 `npm run build` 通过（Next.js 16.1.6、Turbopack、TypeScript、11 个页面）；冻结副本上的两个 Access 测试文件独立运行共 42 项通过。见 [build.log](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/build.log)、[component-tests.log](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/component-tests.log)。
- **浏览器。** Chrome 156.0.8078.48，EN/ZH × 390×844 / 1440×1100；接口在浏览器内由新载入的 mock 拦截。新脚本和输出均写入新目录，未覆盖原证据。

1. **关闭位置与继续导航。** 主矩阵保存 172 条状态记录，检查新增/编辑 Escape、503 后 Escape、取消、X、删除确认和空列表新增共 48 组关闭。关闭后先返回原按钮；新增/编辑的下一次 Tab 分别进入网络检测/删除按钮，删除确认与空列表新增另用 Shift+Tab 检查反向导航。取消确认没有发出 DELETE。见 [results.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/results.json)、[主矩阵汇总](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/summary.json)。
2. **无等待关闭时序。** 另运行独立的原生逐键矩阵，共 48 组新增/编辑/删除 Escape、取消、X 后 Tab；36 组没有人为等待，两键实际间隔 2.0–7.9ms。即时、40ms、350ms 的焦点保持一致，没有迟到 autofocus 回拉。删除按钮位于页末时，向前 Tab 可离开文档；因此“回到原删除位置”的正向证据是上一步明确的 Delete→Escape→Shift+Tab→Edit，不把页末向前 Tab 的 BODY 状态解释成新增表单的回归。见 [逐键时间线](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/rapid-native/rapid-sequences.json)、[原生矩阵日志](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/rapid-native/run.log)。
3. **503、草稿与重试。** 新增/编辑各覆盖 EN/ZH 和两种宽度，共 8 组合、16 次 mock 503；错误位于当前表单并获得焦点，在视口内可读，草稿保留，随后 8 次成功重试关闭表单并返回原按钮。见 [主运行记录](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/results.json)。
4. **旧错误之后完整修正。** 再单独运行 8 个新增/编辑组合：503 后清空名称并提交，确认本地校验不发送写请求；使用原生 `Input.insertText` 逐字输入完整修正名称，等待 300ms 后焦点仍在名称输入框，未重现只输入首字 `F` 后被旧错误抢焦点。最终 8 次重试的 POST/PUT 请求体与完整修正值一致。与上一步合计 16 次成功 mock 重试。见 [correction-results.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/correction-results.json)、[correction-states.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/correction-states.json)。补充脚本首次因 CDP 返回 DOM 对象出现序列化错误，在产品交互前停止，已保留 [driver error](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/correction-driver-error.log)，修正脚本返回值后完整重跑通过。
5. **截图与收尾。** 28 张本轮 PNG 均逐张通过 `view_image` 打开检查；索引包含 SHA256，见 [screenshots.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/screenshots.json)。本轮生产服务与 Chrome 已停止，3127/9253 无本轮监听残留。总结果见 [acceptance-summary.json](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/acceptance-summary.json)。

![本轮独立英文手机：新增关闭后立即 Tab，焦点进入网络检测](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/rapid-native/rapid-add-en-390.png)

![本轮独立中文手机：编辑保存失败，错误在当前视口获得焦点](/Users/geyunfei/.codex-profiles/original/visualizations/2026/10/28/01a18313-cae5-7420-bc89-6bd65f48116a/access-independent-e3775d1-jz3vccz9/edit-failure-zh-390.png)

证据边界：这是独立生产渲染、浏览器键盘与 mock API 的 UI 验收。未执行真实 DNS、路由器、frp、公网访问或生产写入；不据此证明后端持久化、公网连通、真实设备或完整屏幕阅读器合规。真实 DDNS 修复/清理证据仍由对应后端交付独立承担。该 agent 没有修改产品代码、暂存或提交；两份审查文档更新后释放给 Access 交付 owner，由其提交最终文档与集成证据，主 PM 协调独立 review。
