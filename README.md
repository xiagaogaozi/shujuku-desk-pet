# 奶数据库桌宠工坊 · shujuku-desk-pet

为 [奶数据库（AlbusKen/shujuku）](https://github.com/AlbusKen/shujuku) 制作桌宠皮肤的 **Codex skill**。

给出角色描述、正侧面参考或现有素材，技能会指导 Codex 生成一致的透明姿态图片，并打包成可导入的酒馆助手脚本。继续使用奶数据库原有的点击、长按、拖动、睡眠、贴边和工作状态逻辑，不另外实现一套桌宠。

> 本仓库是制作工具，不是某个角色的成品皮肤。不包含示例桌宠、角色参考图、生成图片、个人配置、服务地址或密钥。

## 可以做什么

- **完整换肤**：参考版本支持 24 个主体姿态和 3 个贴边探头，共 27 个图片槽位；使用前核对目标宿主的实际 API。
- **原生透明底**：直接请求带 Alpha 的 PNG/WebP，不使用绿幕生成再抠图。
- **保持角色一致**：先确定 idle 基准图，再带参考生成动作；走路、进食配对保持一致。
- **局部修复**：修正多余肢体、姿态或比例时只更新指定图片，不重画其他已认可素材。
- **通用脚本打包**：生成导入 JSON、源码、独立图片、总览图和离线预览。
- **原生尺寸弹窗**：沿用酒馆 Popup 和控件样式，宽屏/窄屏大小可分别设置。
- **按需使用 API**：默认内置生图；只有明确授权后才使用用户自己的外部服务和凭据。

## 下载和安装

### 方法一：让 Codex 安装

把下面这段发给 Codex：

```text
使用 $skill-installer，从 https://github.com/xiagaogaozi/shujuku-desk-pet
安装仓库根目录的技能，目标技能名为 shujuku-desk-pet。
如果已经安装，请先保留原版本，不要直接覆盖我的修改。
```

本仓库的 `SKILL.md` 位于根目录，不是 `skills/` 子目录。直接调用系统安装器时，对应参数是：

```text
--repo xiagaogaozi/shujuku-desk-pet --path . --name shujuku-desk-pet --ref main
```

安装后在下一轮对话中调用技能；若界面未刷新，可重新打开对话。

### 方法二：下载 ZIP

1. 点击 [下载 main 分支 ZIP](https://github.com/xiagaogaozi/shujuku-desk-pet/archive/refs/heads/main.zip)，或在 GitHub 页面选择 **Code → Download ZIP**。
2. 解压，将包含 `SKILL.md` 的文件夹重命名为 `shujuku-desk-pet`。
3. 放入你的个人技能目录，通常为 `$CODEX_HOME/skills/`；未设置 CODEX_HOME 时通常为 `~/.codex/skills/`。
4. 确认最终结构是 `skills/shujuku-desk-pet/SKILL.md`，不要再套一层同名文件夹。

如果仓库为私有，需要先登录有访问权限的 GitHub 账号，才能下载或克隆。

### 方法三：Git 克隆

PowerShell 示例，目标目录已存在时会停止，不覆盖已有技能：

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
$skillRoot = Join-Path $codexHome 'skills'
$target = Join-Path $skillRoot 'shujuku-desk-pet'
if (Test-Path -LiteralPath $target) { throw '目标技能目录已存在，请先备份或选择更新方式。' }
New-Item -ItemType Directory -Path $skillRoot -Force | Out-Null
git clone https://github.com/xiagaogaozi/shujuku-desk-pet.git $target
```

Git 安装的副本可在备份个人修改后使用 `git pull --ff-only` 更新。

## 使用示例

提供角色参考图片，然后对 Codex 说：

```text
使用 $shujuku-desk-pet，把这张参考图制作成奶数据库桌宠。
保持角色原本的体型和肢体数量，生成完整姿态，直接输出透明背景。
打包酒馆助手导入脚本，先不要安装到我的酒馆。
```

局部修复：

```text
使用 $shujuku-desk-pet，只修正现有皮肤的 roll 姿态。
保留角色身份和打滚构图，修正肢体数量，其他图片不要改。
同步更新导入脚本和预览，保留原版本。
```

## 生成后的脚本按钮

| 位置 | 按钮 | 行为 |
| --- | --- | --- |
| 脚本按钮 | 应用桌宠 | 应用图片，不修改大小、位置、开关或气泡 |
| 脚本按钮 | 调整桌宠大小 | 打开酒馆原生弹窗 |
| 脚本按钮 | 恢复内置 | 只恢复对应内置图片，不重置大小 |
| 尺寸弹窗 | 恢复默认大小 | 立即预览默认值，仍需保存才永久生效 |
| 尺寸弹窗 | 保存 | 将宽屏/窄屏尺寸写入设置 |
| 尺寸弹窗 | 取消 / 关闭 | 撤销临时预览，恢复原样 |

拖动滑块或输入数字会立即预览当前屏幕使用的尺寸；没有保存就不会写入设置。尺寸范围、默认值来自奶数据库 API，而不是某个用户的本地配置。

停用脚本不会撤销已经保存的皮肤或大小。技能不会自动导入、启用或更换你正在使用的桌宠；实际应用依用户请求执行。

## 配套命令

需要 Python 3。`prepare` 只使用标准库；`build` 需要 Pillow，可在你选择的 Python 环境中安装：

```shell
python -m pip install Pillow
```

准备任务（路径由你自己选择）：

```shell
python scripts/pet_skin.py prepare --out <角色工作目录> --name <皮肤名称> --brief <角色描述> --reference <参考图片路径>
```

它会输出 manifest 和生图任务清单，**不会自行请求模型**。Codex 根据清单调用内置生图或已授权的 API，并将图片写入目标位置。

打包已完成的图片：

```shell
python scripts/pet_skin.py build --manifest <角色工作目录>/manifest.json --out <新的交付目录>
```

默认将源画布等比缩放/透明补边为 256×256，选择较小的无损 PNG/WebP，生成：

- 酒馆助手导入 JSON 与 `skin.js`
- `appearance-patch.json` 与 `images/`
- `contact-sheet.png`、`preview.html`、`asset-report.json`

输出目录非空时停止，避免覆盖已有交付。单个图片 URI 和全部图片 URI 的字符预算由打包器检查。图片语义、肢体数量和实际宿主行为仍需人工查看；格式检查不等于真实交互验收。

## 文件结构

```text
SKILL.md                        技能入口与工作流程
agents/openai.yaml              Codex 展示元数据
scripts/pet_skin.py             任务清单与图片打包
assets/skin-script.js           通用酒馆助手脚本模板，不含角色图片
assets/preview.html             通用离线素材预览模板
references/shujuku-contract.md  宿主槽位、动作、接口和限制
references/image-workflow.md    生图、保持一致与局部修复
references/api-image-workflow.md 已授权 API 调用与凭据边界
references/script-ui.md         尺寸预览/保存/取消和原生 UI 约定
```

## 隐私与发布边界

仓库只维护通用技能文件，并以 `.gitignore` 文件白名单限制意外加入的内容。角色工作目录应放在仓库之外。

以下内容不属于技能发行内容：

- 个人参考图、示例桌宠、生成姿态、含图片数据的成品脚本
- 任务 manifest、运行报告、日志、截图、预览成品和备份
- 本地设置、认证文件、服务专属地址、API Key、Token

最终皮肤脚本只需要图片和奶数据库 API，不携带制作者的生图密钥。外部生图需要用户自行授权和配置服务，可能产生费用。内置工具没有返回图片时，不会自动切换外部服务，也不会用旧图片伪装成本次产物。

本仓库不附带交互门禁工程。交互检查或回归按使用者当轮要求安排；要求自行测试时，技能会明确说明未做的验证。