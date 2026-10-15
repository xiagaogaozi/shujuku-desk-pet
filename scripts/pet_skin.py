#!/usr/bin/env python3
"""Prepare image-generation jobs and package local art for shujuku; never writes host settings."""
import argparse
import base64
import io
import json
import re
import uuid
from pathlib import Path

# Snapshot: AlbusKen/shujuku 422e498d46d3c4e306186debd971c99fb84fe767 (2026-10-15).
POSES = {
    'idle': ('待机', 'Relaxed neutral standing pose, eyes open, no strong gesture.'),
    'blink': ('眨眼', 'Same stance as idle, eyes softly closed in a blink.'),
    'look-left': ('向左看', 'Look toward screen-left with eyes and head; maintain body registration.'),
    'look-right': ('向右看', 'Look toward screen-right with eyes and head; maintain body registration.'),
    'walk-a': ('散步 A', 'Move toward screen-right using the reference character\'s existing feet or natural locomotion; first step. Never invent extra legs.'),
    'walk-b': ('散步 B', 'Complement the approved walk-a step toward screen-right with the same anatomy, scale and camera.'),
    'roll': ('打滚', 'Compact curled rolling pose; the host rotates this entire image. Preserve the exact reference limb count; no extra feet or limb-like bumps.'),
    'eat-a': ('进食 A', 'Hold a small character-appropriate snack at the mouth, before a bite.'),
    'eat-b': ('进食 B', 'Same snack and stance, chewing after a bite; keep the body registered.'),
    'yawn': ('哈欠', 'Wide sleepy yawn, a natural stretch, readable at small size.'),
    'snore': ('打呼噜', 'Relaxed asleep, eyes closed; no floating Z letters.'),
    'sit-snore': ('坐着睡', 'Clearly seated and asleep, visibly distinct from the other sleeping pose.'),
    'working': ('工作', 'Focused busy working or thinking, not running with feet.'),
    'struggle': ('被提起', 'Suspended as if gently lifted from the top, limbs dangling or struggling.'),
    'shy': ('害羞', 'Bashful reaction to a tap, tucked posture and shy expression.'),
    'tickle': ('怕痒', 'Laughing and squirming from tickling, readable facial expression.'),
    'angry': ('生气', 'Irritated angry stance, beginning of a comic tantrum.'),
    'happy': ('被摸舒服', 'Contented reaction to petting, relaxed delighted face.'),
    'dizzy': ('晕眩', 'Unsteady dizzy pose, expression conveys dizziness without detached effects.'),
    'surprised': ('惊醒', 'Startled awake, wide eyes and gathered limbs; host supplies upward movement.'),
    'wave': ('挥手', 'Friendly greeting using existing anatomy only: an attached limb if present, otherwise a body tilt or another natural gesture.'),
    'huff': ('气呼呼', 'Puffed cheeks and a frustrated huff, middle of the tantrum.'),
    'pound': ('锤屏幕', 'Comic forward-directed thump using existing anatomy only; an armless character can lean its body or lift an existing foot.'),
    'knockdown': ('震倒', 'Reclining or fallen backward after own thump; do not enlarge the lying body.'),
    'peek': ('普通探头', 'Peeking head facing up from the bottom edge, a flat lower cut; no drawn wall.'),
    'peek-original': ('稀有探头', 'Rare playful variant of the same upward-facing bottom-edge peeking head.'),
    'peek-sleepy': ('困倦探头', 'Sleepy version of the same upward-facing bottom-edge peeking head, eyes closed.'),
}
ROOT = Path(__file__).resolve().parents[1]
SINGLE_LIMIT = 1024 * 1024
TOTAL_LIMIT = 4 * 1024 * 1024


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=4), encoding='utf-8')


def prepare(args):
    folder = Path(args.out).resolve()
    if (folder / 'manifest.json').exists():
        raise ValueError('manifest.json already exists; reuse it or select a new run directory.')
    keys = args.keys.split(',') if args.keys else list(POSES)
    if not keys or len(set(keys)) != len(keys) or set(keys) - POSES.keys():
        raise ValueError('Unknown or duplicate keys; use the exact keys in the contract.')
    (folder / 'frames').mkdir(parents=True, exist_ok=True)
    sources = [str(Path(p).resolve()) for p in args.reference]
    for source in sources:
        if not Path(source).is_file():
            raise ValueError(f'Reference does not exist: {source}')
    manifest = {
        'schemaVersion': 1, 'id': str(uuid.uuid4()), 'name': args.name,
        'brief': args.brief, 'style': args.style,
        'baselineCommit': '422e498d46d3c4e306186debd971c99fb84fe767',
        'images': {key: f'frames/{key}.png' for key in keys},
    }
    write_json(folder / 'manifest.json', manifest)
    # The canonical idle image is generated/reused first even for a partial replacement.
    jobs = []
    for key in ['idle'] + [key for key in keys if key != 'idle']:
        invariant = (
            'One isolated desktop-pet pose, directly generated native transparent alpha PNG/WebP. '
            'No green/blue/magenta screen, colored backdrop, chroma key, background removal or painted checkerboard. '
            'No grid, labels, text, '
            'watermark, scenery, cast shadow or detached motion marks. Preserve character identity, '
            'palette, proportions, material and perspective from references. Consistent square canvas, '
            'body scale and baseline; enough padding for limbs. No atlas or animation strip. '
            'Preserve the reference anatomy and exact limb count. Do not add arms, feet, ears or tails to perform an action. '
        )
        dependencies = [] if key == 'idle' else ['idle']
        references = sources.copy() if key == 'idle' else [str(folder / 'frames/idle.png'), *sources]
        pose_prompt = POSES[key][1]
        pair = {'walk-b': 'walk-a', 'eat-b': 'eat-a'}.get(key)
        if pair in keys:
            dependencies.append(pair)
            references.append(str(folder / 'frames' / f'{pair}.png'))
            pose_prompt += f' Match the approved {pair} reference and change only the complementary action.'
        jobs.append({
            'key': key, 'label': POSES[key][0],
            'output': str(folder / 'frames' / f'{key}.png'),
            'depends_on': dependencies,
            'references': references,
            'backgroundPolicy': 'native-transparent-alpha-only',
            'prompt': f'{invariant}Character: {args.brief}. Style: {args.style}. Pose: {pose_prompt}',
        })
    write_json(folder / 'imagegen-jobs.json', jobs)
    print(json.dumps({'manifest': str(folder / 'manifest.json'), 'jobs': len(jobs),
                      'note': 'Preparation only; use built-in image_gen, or the imagegen CLI after explicit API authorization.'}, ensure_ascii=False))


def build(args):
    from PIL import Image, ImageDraw, ImageOps
    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    images_spec = manifest['images']
    if not isinstance(images_spec, dict) or not images_spec or set(images_spec) - POSES.keys():
        raise ValueError('manifest.images must map supported keys to local image files.')
    uuid.UUID(manifest['id'])
    if not isinstance(manifest['name'], str) or not manifest['name'].strip():
        raise ValueError('A skin name is required.')
    if not 64 <= args.size <= 512:
        raise ValueError('--size must be between 64 and 512 pixels (this is a packaging choice, not an API limit).')
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output directory is not empty; choose a new delivery version.')
    payload, normalized, files, report = {}, {}, {}, []
    for key, relative in images_spec.items():
        source = Path(relative)
        if not source.is_absolute():
            source = manifest_path.parent / source
        if not source.is_file():
            raise ValueError(f'Missing artwork: {key} ({source})')
        with Image.open(source) as original:
            if getattr(original, 'n_frames', 1) != 1:
                raise ValueError(f'{key}: animated source is not silently flattened; use a static pose.')
            original.load()
            rgba = original.convert('RGBA')
        low, high = rgba.getchannel('A').getextrema()
        if high == 0 or low == 255:
            raise ValueError(f'{key}: blank or fully opaque image; regenerate with native transparent alpha, not background removal.')
        # Preserve source canvas geometry. Do not independently fit each body's bounding box.
        fitted = ImageOps.contain(rgba, (args.size, args.size), Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (args.size, args.size))
        canvas.alpha_composite(fitted, ((args.size - fitted.width) // 2, (args.size - fitted.height) // 2))
        choices = []
        for fmt, mime, options in [('PNG', 'png', {'optimize': True}), ('WEBP', 'webp', {'lossless': True, 'method': 6})]:
            buffer = io.BytesIO()
            canvas.save(buffer, fmt, **options)
            choices.append((buffer.getvalue(), mime))
        data, mime = min(choices, key=lambda item: len(item[0]))
        uri = f'data:image/{mime};base64,' + base64.b64encode(data).decode('ascii')
        if len(uri) > SINGLE_LIMIT:
            raise ValueError(f'{key}: exceeds the per-image character limit.')
        payload[key], normalized[key], files[key] = uri, canvas, (data, mime)
        report.append({'key': key, 'source': str(source), 'inputSize': list(rgba.size),
                       'outputSize': list(canvas.size), 'bytes': len(data), 'uriCharacters': len(uri)})
    total = sum(map(len, payload.values()))
    if total > TOTAL_LIMIT:
        raise ValueError(f'Image URLs total {total} characters, exceeds {TOTAL_LIMIT}; reduce resolution.')
    config = {'id': manifest['id'], 'name': manifest['name'], 'images': payload}
    template = (ROOT / 'assets/skin-script.js').read_text(encoding='utf-8')
    code = template.replace('/*__SKIN_CONFIG__*/ null', json.dumps(config, ensure_ascii=False))
    export = {
        'type': 'script', 'enabled': True, 'id': manifest['id'], 'name': manifest['name'],
        'content': code,
        'info': '奶数据库桌宠换肤。点击“应用桌宠”更换图片；“调整桌宠大小”打开酒馆原生弹窗。'
                '拖动滑块或输入数值立即临时预览，保存才永久生效，取消恢复原样。'
                '弹窗内“恢复默认大小”预览默认值，仍需保存。“恢复内置”只还原图片，不重置大小。',
        'button': {'enabled': True, 'buttons': [{'name': name, 'visible': True} for name in
                                               ['应用桌宠', '调整桌宠大小', '恢复内置']]},
        'data': {}, 'export_with': {'data': False, 'button': True},
    }
    safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '-', manifest['name']).strip(' .') or 'pet-skin'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'images').mkdir()
    for key, (data, mime) in files.items():
        (out / 'images' / f'{key}.{mime}').write_bytes(data)
    (out / 'skin.js').write_text(code, encoding='utf-8')
    export_path = out / f'酒馆助手脚本-{safe_name}.json'
    write_json(export_path, export)
    write_json(out / 'appearance-patch.json', {'images': payload})
    write_json(out / 'asset-report.json', {'imageCount': len(payload), 'totalUriCharacters': total,
                                         'limit': TOTAL_LIMIT, 'assets': report,
                                         'verification': 'encoding and limits only; not live Tavern acceptance'})
    preview = (ROOT / 'assets/preview.html').read_text(encoding='utf-8')
    # Escape '<' so a skin name cannot end the HTML script element.
    preview_data = json.dumps(config, ensure_ascii=False).replace('<', '\\u003c')
    (out / 'preview.html').write_text(preview.replace('/*__SKIN_CONFIG__*/ null', preview_data), encoding='utf-8')
    columns, cell_w, cell_h = 6, 160, 184
    sheet = Image.new('RGB', (columns * cell_w, ((len(normalized) + columns - 1) // columns) * cell_h), '#e9edf1')
    draw = ImageDraw.Draw(sheet)
    for i, (key, image) in enumerate(normalized.items()):
        x, y = (i % columns) * cell_w, (i // columns) * cell_h
        for cy in range(y + 4, y + 148, 12):
            for cx in range(x + 8, x + 152, 12):
                draw.rectangle((cx, cy, cx + 11, cy + 11), fill='#ffffff' if ((cx-x)//12 + (cy-y)//12) % 2 else '#d8dce0')
        thumb = image.copy()
        thumb.thumbnail((136, 136), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x + (cell_w - thumb.width)//2, y + 8 + (136-thumb.height)//2), thumb)
        draw.text((x + 10, y + 154), key, fill='#202631')
    sheet.save(out / 'contact-sheet.png')
    print(json.dumps({'script': str(export_path), 'preview': str(out / 'preview.html'),
                      'images': len(payload), 'totalUriCharacters': total}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare', help='Write manifest and imagegen jobs; does not call an image API.')
    p.add_argument('--out', required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--brief', required=True)
    p.add_argument('--style', default='clean chibi illustration')
    p.add_argument('--reference', action='append', default=[])
    p.add_argument('--keys', help='Comma-separated subset; default is all 27 slots.')
    p.set_defaults(run=prepare)
    b = commands.add_parser('build', help='Package approved local static images; Pillow is required.')
    b.add_argument('--manifest', required=True)
    b.add_argument('--out', required=True)
    b.add_argument('--size', type=int, default=256)
    b.set_defaults(run=build)
    args = parser.parse_args()
    try:
        args.run(args)
    except (ValueError, KeyError, OSError, ImportError) as exc:
        parser.exit(1, f'Error: {exc}\n')


if __name__ == '__main__':
    main()