"""
世界模型範例啟動器 — 從專案根目錄執行，避免中文路徑問題
雙擊 run.bat 或執行: python run_world_model.py
"""
import os
import sys

root = os.path.dirname(os.path.abspath(__file__))

# 優先使用已知的世界模型目錄（避免誤匹配其他資料夾）
world_model_dirs = [
    os.path.join(root, "世界模型"),
    os.path.join(root, "world_model"),
]
# 若不存在，則搜尋包含 examples.py + world_model.py 的目錄
for d in world_model_dirs:
    if os.path.isdir(d):
        examples_path = os.path.join(d, "examples.py")
        if os.path.exists(examples_path) and os.path.exists(os.path.join(d, "world_model.py")):
            sys.path.insert(0, d)
            os.chdir(d)
            with open(examples_path, encoding="utf-8") as f:
                exec(compile(f.read(), examples_path, "exec"))
            sys.exit(0)

for name in os.listdir(root):
    path = os.path.join(root, name)
    if os.path.isdir(path):
        examples_path = os.path.join(path, "examples.py")
        world_model_path = os.path.join(path, "world_model.py")
        if os.path.exists(examples_path) and os.path.exists(world_model_path):
            sys.path.insert(0, path)
            os.chdir(path)
            with open(examples_path, encoding="utf-8") as f:
                exec(compile(f.read(), examples_path, "exec"))
            sys.exit(0)

print("找不到 世界模型 目錄或 examples.py")
sys.exit(1)
