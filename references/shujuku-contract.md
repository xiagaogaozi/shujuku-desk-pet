# 原生桌宠能力与换肤协议

核对日期：2026-10-15。上游源码参考提交为 `422e498d46d3c4e306186debd971c99fb84fe767`；以下为该提交的源码事实，未来使用先做能力发现。

## 证据入口

- 仓库：https://github.com/AlbusKen/shujuku
- `src/shared/desk-pet-appearance.ts`：图片槽、配置字段、默认值和字符限额。
- `src/presentation-v2/components/DeskPet.vue`：切图状态机、指针事件、动效和探头布局。
- `src/presentation/bootstrap/api-groups/desk-pet-appearance-api.ts`：对外接口。
- `src/service/settings/desk-pet-appearance-settings.ts`：保存、失败恢复与立即刷新。
- `src/shared/appearance-schema.ts`：图片 URL、字段、patch 的严格校验。
- `src/presentation-v2/composables/useTaskActivity.ts`：任务汇总为 busy。
- `src/presentation/bootstrap/api-registry.ts`：API 放在宿主窗口。
- 酒馆助手的 `src/type/scripts.ts`、`@types/iframe/script.d.ts`、`@types/iframe/event.d.ts`、`@types/function/variables.d.ts`：导入结构、按钮和脚本变量 API。

源码固定链接的结构为 `https://github.com/AlbusKen/shujuku/blob/422e498d46d3c4e306186debd971c99fb84fe767/` 加上述相对路径。

## 27 个图片槽

每个槽位对应 `<img src>`，可独立替换；图片加上宿主 CSS/位移/时序组成动作，不是每个槽各有一行精灵帧。

| 图片键 | 用途与触发 |
| --- | --- |
| `idle` | 默认待机；带呼吸动效 |
| `blink` | 眨眼；单眨与双眨共享此图 |
| `look-left` / `look-right` | 向屏幕左/右看；张望与瞥视共用 |
| `walk-a` / `walk-b` | 走路两步交替；原图朝右，向左时宿主镜像 |
| `roll` | 打滚；单图由 CSS 旋转并伴随横向移动 |
| `eat-a` / `eat-b` | 进食配对，咬/嚼交替 |
| `yawn` | 待机随机打哈欠 |
| `snore` / `sit-snore` | 无互动后随机二选一睡姿 |
| `working` | 任一宿主任务 busy 时工作；不是脚步奔跑 |
| `struggle` | 拖拽中显示被拎起挣扎 |
| `shy` | 普通单击的害羞反应 |
| `tickle` | 1,200 ms 内累计至少 3 次点击，怕痒 |
| `angry` | 2,600 ms 内累计至少 6 次点击，启动生气连段 |
| `happy` | 按住不拖动超过 550 ms，保持被摸舒服姿态；正常松手后 900 ms 余韵 |
| `dizzy` | 拖拽时横向折返至少 4 次，松手后眩晕 |
| `surprised` | 睡着时被按下并点醒的惊吓反应 |
| `wave` | 鼠标进入桌宠区域时招呼；默认冷却 30 秒，忙碌/睡眠/其他反应时不抢占 |
| `huff` | 生气连段第二段：哈气 |
| `pound` | 生气连段第三段：锤屏幕 |
| `knockdown` | 生气连段第四段：自己被震倒 |
| `peek` | 贴边缩入后的普通探头 |
| `peek-original` | 同角色稀有探头，默认 1% 概率，不要求换回内置奶龙 |
| `peek-sleepy` | 缩入期间睡着的探头 |

正常主体姿态优先级：拖动 > 互动反应 > busy 工作 > 睡眠 > 待机动作。贴边缩入时走独立探头显示分支，不是额外主体姿态。

### 组合动作与默认节奏

- 待机动作每 15～20 秒抽取一次，仅在不忙、不拖动、不处于反应/睡眠/缩入时执行。
- 权重：blink 16、doubleBlink 8、lookAround 14、walk 18、roll 10、eat 14、yawn 10、glance 10。它们可以调权重，不能用这个配置任意添加新的状态机动作。
- 单眨 160 ms；双眨 `blink 140 → idle 110 → blink 140`。
- 张望 `look-left 1300 → idle 250 → look-right 1300`；单侧瞥视 1800 ms。
- 散步交替 12 步，每步 230 ms、8 px；打滚 6 步，每步 170 ms、15 px。
- 散步/打滚受贴边状态、空地和减少动态效果设置约束，不能做时回退为张望或眨眼。
- 进食 `eat-a 900 → eat-b 650 → eat-a 450 → eat-b 900`；哈欠 1500 ms。
- 默认无互动 60 秒后睡着，睡姿各 50%；busy 会醒来。
- 生气连段 `angry 2200 → huff 1000 → pound 1300 → knockdown 2200 ms`，连段中普通点按不打断。
- 贴边默认 4 秒后缩入；强行推进边缘可立即缩入。缩入中默认每 30 秒重抽稀有造型，鼠标悬停/点按可探出。

点击次数、长按门槛、摇晃折返数和上述固定子帧节奏不在外观 API 中；调它们属于另一个“修改行为”任务，不是换图。

## 图像与画布要点

- 实测内置图多数 256×256，idle/working 为 256×244；宿主不硬性限定图片像素。
- 默认展示宽屏 88 px、窄屏（≤640 px）64 px；允许 32～256 px。
- 自定义图保留宿主 CSS 动效，但不会套内置素材 `--pose-fit` 的额外体型补偿，所以体型统一需在制作阶段处理。
- `walk-a/b`、`roll` 由宿主水平镜像；不支持分别提供左右行走图。非对称文字、徽章和持物也会镜像，应提前说明。
- 三张探头共用同一朝向：向上、下缘平切；下边不旋转，上边 180°，右边 −90°，左边 +90°。不需要四套方向图。透明留白及裁切必须按宿主布局观察，不要把普通全身 idle 直接当探头。
- PNG / WebP 静态透明图适合当前流程。API 的 data:image 校验也允许 gif/apng 等格式，但换图接口不提供逐帧控制；本打包器拒绝静默展平动画。

## 可定制层次

1. **图片**：27 槽全换或明确子集；传 null 还原该槽内置图。
2. **尺寸/节奏**：`size.wide/narrow/peekDepthRatio/peekOriginalDepthRatio`；`motion.enabled/idleActionMinMs/idleActionSpreadMs/idleActionWeights/snoreAfterMs/tuckDelayMs/peekRotateMs/peekOriginalChance/waveCooldownMs/reactionMs`。用 describe 查范围。
3. **角色化文案**：`jokes.mode/heading/items`；`statusWords.mode/groups`。mode 可为 append 或 replace，空自定义仍回退内置。状态词分 table、plan、polish、continuation、simulation、import、index、skill、generic 九组；这是文字分组，不是九张独立工作姿态。
4. **独立气泡外观**：`AutoCardUpdaterAPI.noticeBubble` 下的 colors、fontSize、fontFamily、borderRadius、size、anchor、dock、carousel。
5. **位置/开关**：位置另有 getPosition/setPosition/resetPosition；启用开关在 features 名称空间。默认换肤不动这些设置。

没有原生 `playPose()`、16 向注视或 Pets 的 failed/waiting/review 自动图片接口。可以把现有槽画成符合角色的等价情绪，不能把新键塞进 images 假装支持新触发。

## 公开接口

```javascript
const api = window.parent.AutoCardUpdaterAPI; // 实际脚本先安全探测 parent / top / 当前 window
const pet = api.deskPet;
pet.imageKeys();       // 当前支持的精确键
pet.describe();        // 字段说明/范围
pet.getDefaults();
pet.getAppearance();   // 默认值 + 覆盖项，每次返回新对象
pet.getOverrides();    // 稀疏覆盖项
pet.getIssues();       // 已存无效字段；不要读取后隐式覆盖它们
pet.updateAppearance({ images: { idle: 'data:image/png;base64,...' } });
pet.resetAppearance('images.idle'); // 仅移除该槽的覆盖；不要无参清空全部设置
```

update 是深层 patch，保存后即时刷新；不要改 read 返回的对象后假定已保存。无效字段会在下一次写入时被丢弃，所以模板遇到 getIssues 非空会先停止。

URL 可用 http(s)、站内相对路径或 data:image；file:、blob:、javascript: 不可用。不要填本地 Windows 路径或临时生图链接。内嵌 data URI 无需上传公共图床，也避免过期。

限额是字符串字符：单张 1,048,576，总和 4,194,304（含 data URI 前缀与 Base64）。整份设置每次保存都会写盘，不能把几百 MB 图集塞入。总限制包括局部更新未碰的其他槽位。

## 酒馆助手导入、尺寸与恢复

导出外层为 `type: script`、id、name、enabled、content、info、button、data、export_with；button.buttons 项为 `{name, visible}`。使用 `eventOn(getButtonEvent(name), callback)` 注册按钮。

通用模板的三个按钮是“应用桌宠 / 调整桌宠大小 / 恢复内置”。应用图片只写 images；尺寸弹窗先做临时视觉预览，只有保存才调用 `updateAppearance({ size: { wide, narrow } })`。不会创建新的换肤前脚本变量备份，也不删除既有变量。

“恢复内置”仅将本皮肤涉及的 images 槽位置为 null，不重置 size/motion/jokes/noticeBubble。保存图片具有持久性，停用脚本不能撤销它。

尺寸 UI、取消和恢复默认的细节见 [script-ui.md](script-ui.md)。`export_with.data` 保持 false，避免导出已有脚本变量。
