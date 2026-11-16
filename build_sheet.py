#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完形填空一页式全景批注讲义构建器

用法:
    python3 build_sheet.py DATA.json OUT.html

说明:
    - template.html 内含示例数据，构建时 sheet-data JSON 整体替换
    - 构建后自动做服务端数据自检，不通过则 exit 2 并逐条列出问题
"""
import json, os, re, sys

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(SKILL_DIR, 'template.html')


def main():
    if len(sys.argv) < 3:
        print('用法: python3 build_sheet.py DATA.json OUT.html')
        sys.exit(1)
    data_path, out_path = sys.argv[1], sys.argv[2]
    d = json.load(open(data_path, encoding='utf-8'))
    raw = open(TPL, encoding='utf-8').read()
    shell = re.sub(
        r'(<script id="sheet-data" type="application/json">).*?(</script>)',
        lambda m: m.group(1) + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + m.group(2),
        raw, flags=re.S)
    assert shell != raw, 'JSON 注入失败（模板中未找到 sheet-data）'
    open(out_path, 'w', encoding='utf-8').write(shell)

    msgs = validate(d)
    print('自检：', '全部通过' if not msgs else '')
    for m in msgs:
        print('  -', m)
    print('输出：', out_path, os.path.getsize(out_path), 'bytes')
    if msgs:
        sys.exit(2)


def validate(d):
    """与模板 JS 自检逻辑一致的服务端校验。"""
    msgs = []
    opts = d.get('options', [])
    nos = [o.get('no') for o in opts]
    for i in range(1, len(nos)):
        if nos[i] != nos[i - 1] + 1:
            msgs.append('题号不连续：%s → %s' % (nos[i - 1], nos[i]))
    seq = [f.get('no') for p in d.get('passage', []) for f in p if f.get('t') == 'b']
    if seq != nos:
        msgs.append('正文空序与选项题号不一致：正文 %s / 选项 %s' % (seq, nos))
    for o in opts:
        if o.get('key') not in ['A', 'B', 'C', 'D']:
            msgs.append('第 %s 题答案标记非法' % o.get('no'))
    if len(d.get('sections', [])) != 5:
        msgs.append('左栏意义段必须恰 5 段（当前 %d）' % len(d.get('sections', [])))
    plot = d.get('plot') or {}
    if plot.get('stages') and len(plot['stages']) != len(d.get('passage', [])):
        msgs.append('故事山阶段数（%d）与正文段数（%d）不一致'
                    % (len(plot['stages']), len(d.get('passage', []))))
    sent = d.get('sentences') or {}
    if sent:
        g = sent.get('good', [])
        if not (1 <= len(g) <= 3):
            msgs.append('续写佳句应为 1-3 句，当前 %d 句' % len(g))
        for i, x in enumerate(g, 1):
            if not x.get('imitate'):
                msgs.append('佳句 %d 缺少对应的仿写句 imitate' % i)
    for p in d.get('passage', []):
        for f in p:
            if f.get('t') == 'b' and (f.get('a') is None or f.get('zh') is None):
                msgs.append('空 %s 缺答案 a 或中文义 zh' % f.get('no'))
    return msgs


if __name__ == '__main__':
    main()
