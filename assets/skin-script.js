// Standalone Tavern Helper skin; image and size changes run only after explicit button actions.
(() => {
  'use strict';
  const skin = /*__SKIN_CONFIG__*/ null;
  if (!skin) throw new Error('请先用 pet_skin.py build 打包此模板。');
  const keys = Object.keys(skin.images);
  let busy = false;

  function resolveHost() {
    for (const candidate of [window.parent, window.top, window]) {
      try {
        if (candidate?.AutoCardUpdaterAPI?.deskPet) return candidate;
      } catch { /* Only same-origin host windows are supported. */ }
    }
    throw new Error('未找到奶数据库桌宠 API；请先启用支持 deskPet 的奶数据库版本，再点击按钮。');
  }

  function getApi(host) {
    const api = host.AutoCardUpdaterAPI.deskPet;
    for (const method of ['imageKeys', 'getAppearance', 'getIssues', 'updateAppearance']) {
      if (typeof api[method] !== 'function') throw new Error(`桌宠 API 缺少 ${method}，停止换肤。`);
    }
    const supported = api.imageKeys();
    const unknown = keys.filter(key => !supported.includes(key));
    if (unknown.length) throw new Error(`当前数据库不支持图片槽位：${unknown.join(', ')}`);
    if (api.getIssues().length) throw new Error('现有桌宠设置存在无效字段；为避免写入时丢弃它们，停止换肤，请先检查 deskPet.getIssues()。');
    return api;
  }

  function notify(host, message, error = false) {
    const toast = host?.toastr?.[error ? 'error' : 'success'];
    if (typeof toast === 'function') toast(message, skin.name);
    else (host || window).alert(`${skin.name}\n${message}`);
  }

  async function preload(host, images) {
    await Promise.all(Object.entries(images).filter(([, src]) => src !== null).map(([key, src]) =>
      new Promise((resolve, reject) => {
        const image = new host.Image();
        const timer = setTimeout(() => finish(new Error(`图片加载超时：${key}`)), 15000);
        function finish(error) {
          clearTimeout(timer);
          image.onload = image.onerror = null;
          error ? reject(error) : resolve();
        }
        image.onload = () => finish(image.naturalWidth ? null : new Error(`图片为空：${key}`));
        image.onerror = () => finish(new Error(`无法加载图片：${key}`));
        image.src = src;
      })
    ));
  }

  async function writeImages(host, api, images) {
    await preload(host, images);
    await api.updateAppearance({ images });
    const current = api.getAppearance().images;
    if (Object.entries(images).some(([key, value]) => current[key] !== value)) {
      throw new Error('写入后的读回与素材不一致，请检查桌宠设置，不要反复应用。');
    }
  }

  async function apply(host, api) {
    await writeImages(host, api, skin.images);
    notify(host, '桌宠图片已应用；动作逻辑、位置、大小和气泡设置保持不变。');
  }

  async function adjustSize(host, api) {
    const context = host.SillyTavern?.getContext?.();
    if (!context?.Popup || !context?.POPUP_TYPE || !context?.POPUP_RESULT) {
      throw new Error('未找到酒馆原生弹窗接口，请更新酒馆后再调整大小。');
    }
    if (typeof api.describe !== 'function' || typeof api.getDefaults !== 'function') {
      throw new Error('当前奶数据库未提供尺寸字段说明或默认值。');
    }
    const fields = api.describe();
    const current = api.getAppearance().size;
    const defaults = api.getDefaults().size;
    const draft = { wide: current.wide, narrow: current.narrow };
    const doc = host.document;
    const content = doc.createElement('div');
    content.className = 'flex-container flexFlowColumn gap10px';
    const heading = doc.createElement('h3');
    heading.className = 'margin0';
    heading.textContent = '调整桌宠大小';
    const hint = doc.createElement('small');
    hint.className = 'opacity50';
    hint.textContent = '拖动或输入后立即预览。保存后永久保留，取消则恢复原样。';
    const previewHint = doc.createElement('small');
    previewHint.className = 'opacity50';
    content.append(heading, hint);
    const controls = [];
    const previewStyle = doc.createElement('style');
    previewStyle.dataset.shujukuDeskPetSizePreview = skin.id;

    function updatePreview() {
      const active = host.innerWidth <= 640 ? 'narrow' : 'wide';
      const actualSize = api.getAppearance().size[active];
      const factor = draft[active] / actualSize;
      // Scale only visual children: scaling the translated root would also move the pet.
      // This is a temporary DOM preview; no settings API is called while dragging.
      previewStyle.textContent = `.acu-desk-pet > .acu-desk-pet__body,
        .acu-desk-pet > .acu-desk-pet__peek {
          scale: ${factor};
          transform-origin: 50% 100%;
        }`;
      previewHint.textContent = `当前屏幕预览${active === 'wide' ? '宽屏' : '窄屏'}尺寸：${draft[active]}px。恢复默认后也需保存才会永久生效。`;
    }

    function clearPreview() {
      previewStyle.remove();
      host.removeEventListener('resize', updatePreview);
      window.removeEventListener('pagehide', clearPreview);
    }

    for (const [key, title] of [['wide', '桌面 / 宽屏'], ['narrow', '手机 / 窄屏（≤640px）']]) {
      const field = fields.find(item => item.path === `size.${key}`);
      if (!field || !Number.isFinite(field.min) || !Number.isFinite(field.max)) {
        throw new Error(`当前奶数据库未提供 size.${key} 的可用范围。`);
      }
      const row = doc.createElement('div');
      row.className = 'range-block width100p';
      const label = doc.createElement('label');
      label.className = 'range-block-title marginBot5';
      label.textContent = `${title} · ${field.min}–${field.max}px`;
      const line = doc.createElement('div');
      line.className = 'range-block-range-and-counter width100p';
      const track = doc.createElement('div');
      track.className = 'range-block-range';
      const counter = doc.createElement('div');
      counter.className = 'range-block-counter';
      const range = doc.createElement('input');
      range.type = 'range';
      range.id = `${skin.id}-size-${key}`;
      label.htmlFor = range.id;
      const number = doc.createElement('input');
      number.type = 'number';
      number.required = true;
      number.setAttribute('aria-label', `${title}大小（像素）`);
      for (const input of [range, number]) {
        input.min = String(field.min);
        input.max = String(field.max);
        input.step = '1';
        input.value = String(draft[key]);
      }
      range.addEventListener('input', () => {
        number.value = range.value;
        draft[key] = Number(range.value);
        updatePreview();
      });
      number.addEventListener('input', () => {
        if (!number.validity.valid) return;
        range.value = number.value;
        draft[key] = Number(number.value);
        updatePreview();
      });
      track.append(range);
      counter.append(number);
      line.append(track, counter);
      row.append(label, line);
      content.append(row);
      controls.push({ key, range, number });
    }
    content.append(previewHint);
    let savedSize = null;
    const popup = new context.Popup(content, context.POPUP_TYPE.TEXT, '', {
      okButton: '保存',
      cancelButton: '取消',
      allowVerticalScrolling: true,
      customButtons: [{
        text: '恢复默认大小',
        tooltip: '预览默认大小；点击保存后永久保留，取消可撤销。',
        action: () => {
          for (const { key, range, number } of controls) {
            draft[key] = defaults[key];
            range.value = number.value = String(defaults[key]);
          }
          updatePreview();
        },
      }],
      onClosing: async dialog => {
        if (dialog.result !== context.POPUP_RESULT.AFFIRMATIVE) {
          clearPreview();
          return true;
        }
        for (const { number } of controls) if (!number.reportValidity()) return false;
        const size = Object.fromEntries(controls.map(({ key, number }) => [key, Number(number.value)]));
        try {
          if (Object.keys(size).some(key => size[key] !== api.getAppearance().size[key])) {
            await api.updateAppearance({ size });
            const readback = api.getAppearance().size;
            if (Object.keys(size).some(key => readback[key] !== size[key])) throw new Error('尺寸保存后读回不一致。');
          }
          savedSize = size;
          clearPreview();
          return true;
        } catch (error) {
          updatePreview();
          notify(host, String(error?.message || error), true);
          return false;
        }
      },
    });
    doc.head.append(previewStyle);
    host.addEventListener('resize', updatePreview);
    window.addEventListener('pagehide', clearPreview, { once: true });
    updatePreview();
    try {
      await popup.show();
    } finally {
      clearPreview();
    }
    if (savedSize) notify(host, `大小已保存：宽屏 ${savedSize.wide}px，窄屏 ${savedSize.narrow}px。`);
  }

  async function reset(host, api) {
    if (!host.confirm(`把本皮肤包含的 ${keys.length} 个槽位恢复为奶数据库内置图？其他外观和设置不变。`)) return;
    await writeImages(host, api, Object.fromEntries(keys.map(key => [key, null])));
    notify(host, '本皮肤对应槽位已恢复内置图片。');
  }

  if (typeof eventOn !== 'function' || typeof getButtonEvent !== 'function') {
    throw new Error('请作为酒馆助手脚本导入，不是浏览器油猴脚本或角色消息 HTML。');
  }
  const handles = Object.entries({ '应用桌宠': apply, '调整桌宠大小': adjustSize, '恢复内置': reset }).map(([name, action]) =>
    eventOn(getButtonEvent(name), async () => {
      if (busy) return;
      busy = true;
      let host;
      try { host = resolveHost(); await action(host, getApi(host)); }
      catch (error) { console.error('[shujuku-desk-pet]', error); notify(host, String(error?.message || error), true); }
      finally { busy = false; }
    })
  );
  window.addEventListener('pagehide', () => handles.forEach(handle => handle.stop()), { once: true });
  // Image changes persist; size previews are transient until the user explicitly saves.
})();