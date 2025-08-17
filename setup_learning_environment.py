#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IBM 量子計算工程師學習環境設置腳本
自動安裝和配置所需的工具和資源
"""

import os
import sys
import subprocess
import platform
import json
from datetime import datetime

class LearningEnvironmentSetup:
    """學習環境設置類"""
    
    def __init__(self):
        self.system = platform.system()
        self.python_version = sys.version_info
        self.setup_log = []
        
    def log_message(self, message, level="INFO"):
        """記錄設置日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.setup_log.append(log_entry)
        print(log_entry)
    
    def check_python_version(self):
        """檢查Python版本"""
        self.log_message("檢查Python版本...")
        
        if self.python_version.major < 3 or (self.python_version.major == 3 and self.python_version.minor < 8):
            self.log_message("❌ Python版本過舊，需要Python 3.8或更高版本", "ERROR")
            return False
        
        self.log_message(f"✅ Python版本: {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        return True
    
    def install_python_packages(self):
        """安裝Python套件"""
        self.log_message("安裝Python套件...")
        
        packages = [
            "numpy",
            "scipy", 
            "matplotlib",
            "pandas",
            "qiskit",
            "requests",
            "jupyter",
            "ipython",
            "tqdm",
            "colorama"
        ]
        
        for package in packages:
            try:
                self.log_message(f"安裝 {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                self.log_message(f"✅ {package} 安裝成功")
            except subprocess.CalledProcessError as e:
                self.log_message(f"❌ {package} 安裝失敗: {e}", "ERROR")
                return False
        
        return True
    
    def create_virtual_environment(self):
        """創建虛擬環境"""
        self.log_message("創建虛擬環境...")
        
        venv_name = "quantum_learning_env"
        
        try:
            # 檢查是否已存在虛擬環境
            if os.path.exists(venv_name):
                self.log_message(f"虛擬環境 {venv_name} 已存在")
                return True
            
            # 創建虛擬環境
            subprocess.check_call([sys.executable, "-m", "venv", venv_name])
            self.log_message(f"✅ 虛擬環境 {venv_name} 創建成功")
            
            # 激活腳本
            if self.system == "Windows":
                activate_script = os.path.join(venv_name, "Scripts", "activate.bat")
            else:
                activate_script = os.path.join(venv_name, "bin", "activate")
            
            self.log_message(f"虛擬環境激活腳本: {activate_script}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log_message(f"❌ 虛擬環境創建失敗: {e}", "ERROR")
            return False
    
    def setup_git_repository(self):
        """設置Git倉庫"""
        self.log_message("設置Git倉庫...")
        
        try:
            # 初始化Git倉庫
            if not os.path.exists(".git"):
                subprocess.check_call(["git", "init"])
                self.log_message("✅ Git倉庫初始化成功")
            
            # 創建.gitignore文件
            gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
quantum_learning_env/
venv/
ENV/

# Jupyter Notebook
.ipynb_checkpoints

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Learning Progress
learning_progress.json
*.log
"""
            
            with open(".gitignore", "w", encoding="utf-8") as f:
                f.write(gitignore_content.strip())
            
            self.log_message("✅ .gitignore文件創建成功")
            
            # 添加文件到Git
            subprocess.check_call(["git", "add", "."])
            subprocess.check_call(["git", "commit", "-m", "Initial commit: IBM Quantum Learning Environment"])
            
            self.log_message("✅ Git初始提交完成")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log_message(f"❌ Git設置失敗: {e}", "ERROR")
            return False
    
    def create_project_structure(self):
        """創建專案結構"""
        self.log_message("創建專案結構...")
        
        directories = [
            "quantum_examples",
            "microwave_examples", 
            "cmos_examples",
            "projects",
            "resources",
            "docs",
            "tests"
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.log_message(f"✅ 創建目錄: {directory}")
        
        # 創建README文件
        readme_content = """# IBM 量子計算工程師學習專案

## 專案概述
這個專案包含了IBM量子計算工程師職位所需的學習資源和工具。

## 目錄結構
- `quantum_examples/`: 量子計算範例程式
- `microwave_examples/`: 微波工程範例程式
- `cmos_examples/`: CMOS設計範例程式
- `projects/`: 實作專案
- `resources/`: 學習資源
- `docs/`: 文檔
- `tests/`: 測試程式

## 快速開始
1. 安裝依賴: `pip install -r requirements.txt`
2. 運行主工具: `python quantum_learning_tools.py`
3. 運行微波設計範例: `python microwave_design_examples.py`
4. 運行CMOS設計範例: `python cmos_design_examples.py`

## 學習路徑
請參考 `quantum_engineering_learning_plan.html` 了解完整的學習計劃。

## 進度追蹤
使用 `quantum_learning_tools.py` 中的進度追蹤功能來記錄學習進度。
"""
        
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        self.log_message("✅ README.md文件創建成功")
        return True
    
    def download_learning_resources(self):
        """下載學習資源"""
        self.log_message("下載學習資源...")
        
        resources = {
            "qiskit_textbook": "https://qiskit.org/textbook/",
            "ibm_quantum_learning": "https://learning.quantum-computing.ibm.com/",
            "ibm_quantum_experience": "https://quantum-computing.ibm.com/",
            "coursera_quantum": "https://www.coursera.org/search?query=quantum%20computing",
            "edx_quantum": "https://www.edx.org/search?q=quantum%20computing"
        }
        
        # 創建資源列表文件
        resources_content = "# 學習資源列表\n\n"
        
        for name, url in resources.items():
            resources_content += f"## {name.replace('_', ' ').title()}\n"
            resources_content += f"URL: {url}\n\n"
        
        with open("resources/learning_resources.md", "w", encoding="utf-8") as f:
            f.write(resources_content)
        
        self.log_message("✅ 學習資源列表創建成功")
        return True
    
    def create_sample_projects(self):
        """創建範例專案"""
        self.log_message("創建範例專案...")
        
        # 量子計算範例
        quantum_project = {
            "name": "量子比特控制系統",
            "description": "設計一個簡單的量子比特控制系統",
            "files": ["quantum_control.py", "quantum_measurement.py"],
            "requirements": ["qiskit", "numpy", "matplotlib"]
        }
        
        # 微波工程範例
        microwave_project = {
            "name": "低雜訊放大器設計",
            "description": "設計一個2.4GHz低雜訊放大器",
            "files": ["lna_design.py", "matching_network.py"],
            "requirements": ["numpy", "scipy", "matplotlib"]
        }
        
        # CMOS設計範例
        cmos_project = {
            "name": "反相器鏈設計",
            "description": "設計一個多級反相器鏈",
            "files": ["inverter_chain.py", "timing_analysis.py"],
            "requirements": ["numpy", "matplotlib"]
        }
        
        projects = [quantum_project, microwave_project, cmos_project]
        
        for i, project in enumerate(projects, 1):
            project_dir = f"projects/project_{i}_{project['name'].replace(' ', '_')}"
            os.makedirs(project_dir, exist_ok=True)
            
            # 創建專案描述文件
            project_readme = f"""# {project['name']}

## 描述
{project['description']}

## 文件
{chr(10).join(f"- {file}" for file in project['files'])}

## 依賴
{chr(10).join(f"- {req}" for req in project['requirements'])}

## 使用方法
1. 安裝依賴: `pip install {' '.join(project['requirements'])}`
2. 運行主程式: `python {project['files'][0]}`

## 學習目標
- 理解相關理論基礎
- 掌握實作技巧
- 完成性能分析
"""
            
            with open(f"{project_dir}/README.md", "w", encoding="utf-8") as f:
                f.write(project_readme)
            
            self.log_message(f"✅ 創建專案: {project['name']}")
        
        return True
    
    def create_learning_schedule(self):
        """創建學習計劃"""
        self.log_message("創建學習計劃...")
        
        schedule = {
            "phase_1": {
                "name": "基礎技能建立",
                "duration": "6-8個月",
                "topics": [
                    "數學與物理基礎",
                    "Python程式設計",
                    "Linux系統操作",
                    "Git版本控制"
                ],
                "weekly_hours": 20
            },
            "phase_2": {
                "name": "微波工程專業",
                "duration": "8-10個月",
                "topics": [
                    "微波理論基礎",
                    "射頻電路設計",
                    "模擬軟體學習",
                    "測量技術實作"
                ],
                "weekly_hours": 25
            },
            "phase_3": {
                "name": "CMOS設計與PDK",
                "duration": "6-8個月",
                "topics": [
                    "CMOS製程基礎",
                    "物理驗證技術",
                    "EDA工具學習",
                    "PDK開發實作"
                ],
                "weekly_hours": 20
            },
            "phase_4": {
                "name": "量子硬體專業",
                "duration": "8-12個月",
                "topics": [
                    "量子物理深入",
                    "量子比特設計",
                    "低溫電子學",
                    "量子控制系統"
                ],
                "weekly_hours": 25
            },
            "phase_5": {
                "name": "實作專案與作品集",
                "duration": "4-6個月",
                "topics": [
                    "專案實作",
                    "作品集建立",
                    "社群參與",
                    "求職準備"
                ],
                "weekly_hours": 30
            }
        }
        
        with open("learning_schedule.json", "w", encoding="utf-8") as f:
            json.dump(schedule, f, ensure_ascii=False, indent=2)
        
        self.log_message("✅ 學習計劃創建成功")
        return True
    
    def run_tests(self):
        """運行測試"""
        self.log_message("運行環境測試...")
        
        try:
            # 測試Python套件導入
            import numpy as np
            import matplotlib.pyplot as plt
            import qiskit
            import pandas as pd
            
            self.log_message("✅ 所有Python套件導入成功")
            
            # 測試基本功能
            test_array = np.array([1, 2, 3, 4, 5])
            self.log_message(f"✅ NumPy測試: {test_array.mean()}")
            
            # 測試Qiskit
            from qiskit import QuantumCircuit
            qc = QuantumCircuit(2, 2)
            self.log_message("✅ Qiskit測試: 量子電路創建成功")
            
            return True
            
        except ImportError as e:
            self.log_message(f"❌ 套件導入失敗: {e}", "ERROR")
            return False
    
    def save_setup_log(self):
        """保存設置日誌"""
        with open("setup_log.txt", "w", encoding="utf-8") as f:
            for log_entry in self.setup_log:
                f.write(log_entry + "\n")
        
        self.log_message("✅ 設置日誌已保存到 setup_log.txt")
    
    def setup_complete_environment(self):
        """完整環境設置"""
        self.log_message("開始IBM量子計算工程師學習環境設置")
        self.log_message("=" * 60)
        
        steps = [
            ("檢查Python版本", self.check_python_version),
            ("創建虛擬環境", self.create_virtual_environment),
            ("安裝Python套件", self.install_python_packages),
            ("創建專案結構", self.create_project_structure),
            ("設置Git倉庫", self.setup_git_repository),
            ("下載學習資源", self.download_learning_resources),
            ("創建範例專案", self.create_sample_projects),
            ("創建學習計劃", self.create_learning_schedule),
            ("運行環境測試", self.run_tests)
        ]
        
        success_count = 0
        total_steps = len(steps)
        
        for step_name, step_function in steps:
            self.log_message(f"\n執行步驟: {step_name}")
            try:
                if step_function():
                    success_count += 1
                    self.log_message(f"✅ {step_name} 完成")
                else:
                    self.log_message(f"❌ {step_name} 失敗", "ERROR")
            except Exception as e:
                self.log_message(f"❌ {step_name} 發生錯誤: {e}", "ERROR")
        
        # 保存設置日誌
        self.save_setup_log()
        
        # 顯示設置結果
        self.log_message("\n" + "=" * 60)
        self.log_message(f"環境設置完成！成功步驟: {success_count}/{total_steps}")
        
        if success_count == total_steps:
            self.log_message("🎉 所有設置步驟成功完成！")
            self.log_message("\n下一步操作:")
            self.log_message("1. 激活虛擬環境: source quantum_learning_env/bin/activate (Linux/Mac)")
            self.log_message("2. 激活虛擬環境: quantum_learning_env\\Scripts\\activate (Windows)")
            self.log_message("3. 運行主工具: python quantum_learning_tools.py")
            self.log_message("4. 查看學習計劃: quantum_engineering_learning_plan.html")
        else:
            self.log_message("⚠️ 部分設置步驟失敗，請檢查錯誤日誌")
        
        return success_count == total_steps

def main():
    """主函數"""
    print("🚀 IBM 量子計算工程師學習環境設置")
    print("=" * 60)
    
    setup = LearningEnvironmentSetup()
    
    # 詢問用戶是否繼續
    response = input("是否開始設置學習環境？(y/n): ").lower()
    
    if response == 'y':
        setup.setup_complete_environment()
    else:
        print("設置已取消")

if __name__ == "__main__":
    main() 