# 脚本按钮与原生尺寸弹窗

本约定对应 `assets/skin-script.js`，打包器的按钮元数据和说明文字必须与模板保持一致。

## 三个脚本按钮

- **应用桌宠**：只更新 manifest 包含的 images。
- **调整桌宠大小**：打开酒馆原生 Popup，分别控制宽屏和窄屏尺寸。
- **恢复内置**：把本皮肤包含的图片槽位置为 null，不恢复大小或其他设置。

不提供“恢复换肤前”按钮，不为此创建新的脚本变量备份。已有脚本变量不读取、不删除，导出保持 `export_with.data: false`。

## 尺寸的草稿与保存

1. 打开时读取 `deskPet.getAppearance().size`，从 `describe()` 读取 size.wide / size.narrow 的范围，从 `getDefaults().size` 读取默认值。不写死某个用户当前的尺寸。
2. 滑块与数字框双向同步。有效输入更新 draft，当前屏幕使用的宽屏/窄屏尺寸立即预览。
3. **预览不调用 updateAppearance**：它会保存设置。临时 stylesheet 只缩放 `.acu-desk-pet` 的 `__body` / `__peek` 视觉子层；根节点自带 translate 定位，不能直接缩放根节点，以免位置也被缩放。
4. 缩放比例是草稿尺寸 / 当前保存尺寸。视口变化时按宿主的宽窄屏规则重算。该比例是业务预览数据，不是主题变量。
5. “保存”时校验输入，提交最小 patch `{ size: { wide, narrow } }`，读回后清除预览。失败时保留弹窗和草稿并提示错误。
6. “取消”、关闭或脚本卸载时移除临时样式与监听；没有发生持久化写入，因此恢复原样。
7. 弹窗内的“恢复默认大小”只更新草稿并即时预览，不关闭弹窗。仍需保存才永久保留；取消可撤销。

默认值/范围和 DOM 类名都来自宿主；未来版本改动时先核对源码，不以注入全局样式或修改数据库源码掩盖兼容问题。

## 酒馆 UI 复用映射

- 使用宿主 `SillyTavern.getContext()` 暴露的 `Popup`、`POPUP_TYPE`、`POPUP_RESULT`。
- DOM 元素由 **host.document** 创建，避免脚本 iframe 与宿主 HTMLElement 的跨 realm 判断不匹配。
- 复用 `range-block`、`range-block-title`、`range-block-range-and-counter`、`range-block-range`、`range-block-counter`。
- 复用宿主的 `flex-container`、`flexFlowColumn`、`gap10px`、`width100p`、`margin0`、`marginBot5`、`opacity50` 等 utility class。
- 背景、边框、阴影、文字、聚焦轮廓和字体继承宿主 Popup/控件样式；不建立独立配色或新的弹窗框架。

| 宿主变量 | 本弹窗中的用途 | 状态 |
| --- | --- | --- |
| `--SmartThemeBodyColor` | 文字与滑块主体 | 继承当前主题 |
| `--SmartThemeBlurTintColor` | 原生弹窗背景 | 继承当前主题 |
| `--SmartThemeBorderColor` | 边框 | 继承当前主题 |
| `--SmartThemeShadowColor` | 原生阴影 | 继承当前主题 |
| `--mainFontSize` / `--mainFontFamily` | 字体和缩放 | 继承宿主 |
| `--black30a` | 数字输入框背景 | 复用原生控件 |
| `--interactable-outline-color` | 键盘焦点 | 复用原生控件 |

样式事实源是宿主 `public/style.css`、`public/css/st-tailwind.css` 和 `public/scripts/popup.js`。未新增主题令牌；整数像素步长、预览缩放比例、底部中心缩放原点属于业务/几何规则。

## 验证范围

按用户本轮要求安排检查。若用户明确要自行测试或不要门禁，交付后说明尚未实测，不主动打开其页面或改动现有桌宠设置。