#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/run_batch_from_dir.py

交互式/命令行运行器，用于指定一个目录并调用 `scripts/batch_import_v2.py` 批量导入该目录下的 PDF。

用法：
  python scripts/run_batch_from_dir.py /absolute/path/to/pdf_dir
  或直接运行且按提示输入目录。

实现细节：
  - 将在仓库根目录下创建/更新 `data/test_pdfs` 符号链接指向指定目录（与 `batch_import_v2.py` 的查找逻辑兼容）。
  - 通过动态加载 `batch_import_v2.py` 并调用其 `main()` 函数来执行导入。

注意：保持在项目根目录运行该脚本以保证相对路径一致。
"""

import sys
import os
from pathlib import Path
import argparse
import importlib.util
import shutil


def create_symlink(target_dir: Path, link_path: Path):
    """创建或替换符号链接"""
    if link_path.exists() or link_path.is_symlink():
        try:
            # 删除现有文件或链接
            if link_path.is_dir() and not link_path.is_symlink():
                # 若为真实目录，先备份重命名
                backup = link_path.with_name(link_path.name + "_backup")
                shutil.move(str(link_path), str(backup))
            else:
                link_path.unlink()
        except Exception as e:
            print(f"无法移除已有的 {link_path}: {e}")
            raise

    # 创建父目录
    link_path.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(str(target_dir), str(link_path))
    print(f"已创建符号链接: {link_path} -> {target_dir}")


def load_and_run_batch_script(script_path: Path) -> int:
    """动态加载并运行 batch_import_v2.py 的 main()。返回 main() 的返回值。"""
    if not script_path.exists():
        print(f"找不到脚本: {script_path}")
        return 2

    spec = importlib.util.spec_from_file_location("batch_import_v2", str(script_path))
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"加载脚本失败: {e}")
        raise

    if hasattr(module, "main"):
        return module.main()
    else:
        print("目标脚本没有找到 main() 函数。尝试作为脚本执行。")
        return 3


def parse_args():
    p = argparse.ArgumentParser(description="从指定目录批量导入 PDF（调用 scripts/batch_import_v2.py）")
    p.add_argument("pdf_dir", nargs="?", help="要导入的 PDF 所在目录（绝对或相对路径）")
    return p.parse_args()


def main():
    args = parse_args()

    if args.pdf_dir:
        pdf_dir = Path(args.pdf_dir).expanduser().resolve()
    else:
        val = input("请输入要批量导入的目录路径: ").strip()
        if not val:
            print("未输入路径，退出。")
            return 1
        pdf_dir = Path(val).expanduser().resolve()

    if not pdf_dir.exists() or not pdf_dir.is_dir():
        print(f"目录不存在或不是目录: {pdf_dir}")
        return 1

    # 目标链接位置（与 batch_import_v2.py 的 find_test_pdfs 兼容）
    workspace_root = Path(__file__).parent.parent.resolve()
    link_path = workspace_root / "data" / "test_pdfs"

    try:
        create_symlink(pdf_dir, link_path)
    except Exception as e:
        print(f"创建符号链接失败: {e}")
        return 1

    # 调用 batch_import_v2
    script_path = Path(__file__).parent / "batch_import_v2.py"

    # 保证工作目录为仓库根，以便 batch_import_v2 使用相对路径
    os.chdir(str(workspace_root))
    print(f"切换工作目录到 {workspace_root} 并调用 {script_path.name} ...")

    # 仅使用指定的 data/test_pdfs（避免同时扫描 PdfData）
    os.environ['ONLY_USE_TEST_DIR'] = '1'

    return load_and_run_batch_script(script_path)


if __name__ == '__main__':
    sys.exit(main())
