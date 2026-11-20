#!/usr/bin/env python3
"""Prompt 工作台模板库管理（纯 Python 标准库）。

数据文件优先级：--store 参数 > 环境变量 PROMPT_STORE > ~/.prompt-workbench/store.json
退出码：0 成功；1 一般错误（不存在/重名/库损坏等）；2 render 缺少变量。
"""
import argparse
import difflib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

VAR_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def die(msg, code=1):
    print(f"错误: {msg}", file=sys.stderr)
    sys.exit(code)


def store_path(args):
    p = (args.store or os.environ.get("PROMPT_STORE")
         or str(Path.home() / ".prompt-workbench" / "store.json"))
    return Path(p)


def load(path):
    if not path.exists():
        return {"templates": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        die(f"模板库损坏，请检查 {path}: {e}")
    if not isinstance(data, dict) or not isinstance(data.get("templates"), dict):
        die(f"模板库格式不正确（缺少 templates 字段）: {path}")
    return data


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def get_tpl(data, name):
    tpl = data["templates"].get(name)
    if tpl is None:
        die(f"模板不存在: {name}")
    return tpl


def read_body(args):
    if getattr(args, "body", None) is not None:
        return args.body
    if getattr(args, "file", None):
        p = Path(args.file)
        if not p.is_file():
            die(f"文件不存在: {p}")
        return p.read_text(encoding="utf-8")
    die("必须提供 --body 或 --file")


def variables(body):
    seen = []
    for m in VAR_RE.finditer(body):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def first_line(text):
    return text.strip().splitlines()[0][:60] if text.strip() else "(空)"


def get_version(tpl, v):
    for item in tpl["versions"]:
        if item["v"] == v:
            return item
    die(f"版本不存在: v{v}（现有 1–{len(tpl['versions'])}）")


def cmd_add(args, data, path):
    if args.name in data["templates"]:
        die(f"模板已存在: {args.name}（修改请用 edit）")
    body = read_body(args)
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    data["templates"][args.name] = {
        "tags": tags,
        "created": now(),
        "versions": [{"v": 1, "time": now(), "body": body}],
    }
    save(path, data)
    vs = variables(body)
    print(f"已新增模板 {args.name}（v1），变量: {', '.join(vs) if vs else '无'}")


def cmd_list(args, data, path):
    tpls = data["templates"]
    if not tpls:
        print("模板库为空")
        return
    for name in sorted(tpls):
        tpl = tpls[name]
        cur = tpl["versions"][-1]
        tags = ",".join(tpl["tags"]) or "-"
        vs = variables(cur["body"])
        print(f"{name}  [v{cur['v']}]  tags={tags}  变量={','.join(vs) or '无'}")
        print(f"    {first_line(cur['body'])}")


def cmd_show(args, data, path):
    tpl = get_tpl(data, args.name)
    cur = tpl["versions"][-1]
    print(f"# {args.name}（当前 v{cur['v']}，共 {len(tpl['versions'])} 个版本，"
          f"tags={','.join(tpl['tags']) or '-'}）")
    print(cur["body"])


def cmd_edit(args, data, path):
    tpl = get_tpl(data, args.name)
    body = read_body(args)
    v = len(tpl["versions"]) + 1
    tpl["versions"].append({"v": v, "time": now(), "body": body})
    save(path, data)
    print(f"已更新 {args.name} → v{v}（历史版本保留），变量: {', '.join(variables(body)) or '无'}")


def cmd_versions(args, data, path):
    tpl = get_tpl(data, args.name)
    for item in tpl["versions"]:
        print(f"v{item['v']}  {item['time']}  {first_line(item['body'])}")


def cmd_diff(args, data, path):
    tpl = get_tpl(data, args.name)
    a = get_version(tpl, args.a)["body"].splitlines()
    b = get_version(tpl, args.b)["body"].splitlines()
    lines = list(difflib.unified_diff(a, b, fromfile=f"v{args.a}", tofile=f"v{args.b}", lineterm=""))
    print("\n".join(lines) if lines else "两个版本内容相同")


def cmd_render(args, data, path):
    tpl = get_tpl(data, args.name)
    item = get_version(tpl, args.version) if args.version else tpl["versions"][-1]
    vals = {}
    for kv in args.var or []:
        if "=" not in kv:
            die(f"--var 需要 键=值 格式: {kv}")
        k, v = kv.split("=", 1)
        vals[k.strip()] = v
    missing = [v for v in variables(item["body"]) if v not in vals]
    if missing:
        die(f"缺少变量: {', '.join(missing)}", code=2)
    print(VAR_RE.sub(lambda m: vals[m.group(1)], item["body"]))


def cmd_delete(args, data, path):
    get_tpl(data, args.name)
    del data["templates"][args.name]
    save(path, data)
    print(f"已删除模板 {args.name}")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--store", help="模板库 JSON 路径（默认 ~/.prompt-workbench/store.json）")
    parser = argparse.ArgumentParser(description="Prompt 工作台模板库管理", parents=[common])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add", parents=[common], help="新增模板")
    p.add_argument("--name", required=True)
    p.add_argument("--body")
    p.add_argument("--file")
    p.add_argument("--tags", help="逗号分隔标签")

    sub.add_parser("list", parents=[common], help="列出全部模板")

    p = sub.add_parser("show", parents=[common], help="查看模板当前版本全文")
    p.add_argument("--name", required=True)

    p = sub.add_parser("edit", parents=[common], help="编辑模板（追加新版本）")
    p.add_argument("--name", required=True)
    p.add_argument("--body")
    p.add_argument("--file")

    p = sub.add_parser("versions", parents=[common], help="列出版本历史")
    p.add_argument("--name", required=True)

    p = sub.add_parser("diff", parents=[common], help="对比两个版本")
    p.add_argument("--name", required=True)
    p.add_argument("--a", type=int, required=True)
    p.add_argument("--b", type=int, required=True)

    p = sub.add_parser("render", parents=[common], help="填充变量输出最终提示词")
    p.add_argument("--name", required=True)
    p.add_argument("--version", type=int)
    p.add_argument("--var", action="append", help="键=值，可重复")

    p = sub.add_parser("delete", parents=[common], help="删除模板")
    p.add_argument("--name", required=True)

    args = parser.parse_args()
    path = store_path(args)
    data = load(path)
    handlers = {
        "add": cmd_add, "list": cmd_list, "show": cmd_show, "edit": cmd_edit,
        "versions": cmd_versions, "diff": cmd_diff, "render": cmd_render,
        "delete": cmd_delete,
    }
    handlers[args.cmd](args, data, path)


if __name__ == "__main__":
    main()
