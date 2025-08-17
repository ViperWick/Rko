#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CMOS 設計範例程式
包含常見的積體電路設計和分析工具
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import constants

class CMOSDesignExamples:
    """CMOS設計範例類"""
    
    def __init__(self):
        # 工藝參數 (180nm CMOS)
        self.V_dd = 1.8  # 電源電壓
        self.V_th_n = 0.5  # NMOS閾值電壓
        self.V_th_p = -0.5  # PMOS閾值電壓
        self.k_n = 200e-6  # NMOS工藝參數
        self.k_p = 80e-6   # PMOS工藝參數
        self.t_ox = 4e-9   # 氧化層厚度
        self.epsilon_ox = 3.9 * constants.epsilon_0  # 氧化層介電常數
    
    def design_inverter(self, W_n=1e-6, L_n=0.5e-6, W_p=2e-6, L_p=0.5e-6):
        """反相器設計"""
        print("💻 反相器設計")
        print("=" * 40)
        
        print(f"NMOS: W={W_n*1e6:.1f}μm, L={L_n*1e6:.1f}μm")
        print(f"PMOS: W={W_p*1e6:.1f}μm, L={L_p*1e6:.1f}μm")
        
        # 計算驅動電流
        I_drive_n = self.calculate_transistor_current(W_n, L_n, self.V_dd, self.V_dd/2, 'nmos')
        I_drive_p = self.calculate_transistor_current(W_p, L_p, self.V_dd, self.V_dd/2, 'pmos')
        
        print(f"NMOS驅動電流: {I_drive_n*1e6:.2f} μA")
        print(f"PMOS驅動電流: {I_drive_p*1e6:.2f} μA")
        
        # 計算延遲
        C_load = 1e-12  # 負載電容
        t_phl = 0.69 * C_load / I_drive_n  # 高到低延遲
        t_plh = 0.69 * C_load / I_drive_p  # 低到高延遲
        
        print(f"高到低延遲: {t_phl*1e9:.2f} ns")
        print(f"低到高延遲: {t_plh*1e9:.2f} ns")
        print(f"平均延遲: {(t_phl + t_plh)/2*1e9:.2f} ns")
        
        # 計算功耗
        P_dynamic = 0.5 * C_load * self.V_dd**2 * 1e9  # 動態功耗
        P_static = (I_drive_n + I_drive_p) * self.V_dd * 0.1  # 靜態功耗
        
        print(f"動態功耗: {P_dynamic*1e6:.2f} μW")
        print(f"靜態功耗: {P_static*1e6:.2f} μW")
        
        # 繪製傳輸特性
        self.plot_inverter_transfer_characteristic(W_n, L_n, W_p, L_p)
        
        return {
            't_phl': t_phl,
            't_plh': t_plh,
            'P_dynamic': P_dynamic,
            'P_static': P_static
        }
    
    def design_nand_gate(self, W_n=1e-6, L_n=0.5e-6, W_p=2e-6, L_p=0.5e-6):
        """NAND閘設計"""
        print("💻 NAND閘設計")
        print("=" * 40)
        
        # 串聯NMOS，並聯PMOS
        # 最壞情況：兩個NMOS都導通
        I_drive_n = self.calculate_transistor_current(W_n, L_n, self.V_dd, self.V_dd/2, 'nmos') / 2
        I_drive_p = self.calculate_transistor_current(W_p, L_p, self.V_dd, self.V_dd/2, 'pmos')
        
        print(f"NMOS驅動電流: {I_drive_n*1e6:.2f} μA")
        print(f"PMOS驅動電流: {I_drive_p*1e6:.2f} μA")
        
        # 計算延遲
        C_load = 1e-12
        t_phl = 0.69 * C_load / I_drive_n
        t_plh = 0.69 * C_load / I_drive_p
        
        print(f"高到低延遲: {t_phl*1e9:.2f} ns")
        print(f"低到高延遲: {t_plh*1e9:.2f} ns")
        
        return {
            't_phl': t_phl,
            't_plh': t_plh
        }
    
    def design_nor_gate(self, W_n=1e-6, L_n=0.5e-6, W_p=2e-6, L_p=0.5e-6):
        """NOR閘設計"""
        print("💻 NOR閘設計")
        print("=" * 40)
        
        # 並聯NMOS，串聯PMOS
        I_drive_n = self.calculate_transistor_current(W_n, L_n, self.V_dd, self.V_dd/2, 'nmos')
        I_drive_p = self.calculate_transistor_current(W_p, L_p, self.V_dd, self.V_dd/2, 'pmos') / 2
        
        print(f"NMOS驅動電流: {I_drive_n*1e6:.2f} μA")
        print(f"PMOS驅動電流: {I_drive_p*1e6:.2f} μA")
        
        # 計算延遲
        C_load = 1e-12
        t_phl = 0.69 * C_load / I_drive_n
        t_plh = 0.69 * C_load / I_drive_p
        
        print(f"高到低延遲: {t_phl*1e9:.2f} ns")
        print(f"低到高延遲: {t_plh*1e9:.2f} ns")
        
        return {
            't_phl': t_phl,
            't_plh': t_plh
        }
    
    def design_differential_amplifier(self, W=10e-6, L=1e-6, I_bias=100e-6):
        """差分放大器設計"""
        print("💻 差分放大器設計")
        print("=" * 40)
        
        print(f"晶體管尺寸: W={W*1e6:.1f}μm, L={L*1e6:.1f}μm")
        print(f"偏置電流: {I_bias*1e6:.1f} μA")
        
        # 計算跨導
        g_m = np.sqrt(2 * self.k_n * W/L * I_bias/2)
        print(f"跨導: {g_m*1e3:.2f} mS")
        
        # 計算增益
        R_load = 10e3  # 負載電阻
        A_v = -g_m * R_load
        print(f"電壓增益: {A_v:.1f}")
        
        # 計算頻寬
        C_load = 1e-12
        f_3db = 1 / (2 * np.pi * R_load * C_load)
        print(f"3dB頻寬: {f_3db/1e6:.1f} MHz")
        
        # 計算雜訊
        v_n2 = 4 * constants.k * 300 / g_m  # 熱雜訊
        print(f"輸入雜訊電壓: {np.sqrt(v_n2)*1e6:.2f} μV/√Hz")
        
        return {
            'g_m': g_m,
            'A_v': A_v,
            'f_3db': f_3db,
            'v_n': np.sqrt(v_n2)
        }
    
    def design_ring_oscillator(self, stages=5, W=1e-6, L=0.5e-6):
        """環形振盪器設計"""
        print("💻 環形振盪器設計")
        print("=" * 40)
        
        print(f"級數: {stages}")
        print(f"晶體管尺寸: W={W*1e6:.1f}μm, L={L*1e6:.1f}μm")
        
        # 計算每級延遲
        I_drive = self.calculate_transistor_current(W, L, self.V_dd, self.V_dd/2, 'nmos')
        C_load = 1e-12
        t_delay = 0.69 * C_load / I_drive
        
        # 計算振盪頻率
        f_osc = 1 / (2 * stages * t_delay)
        print(f"每級延遲: {t_delay*1e9:.2f} ns")
        print(f"振盪頻率: {f_osc/1e6:.1f} MHz")
        
        # 計算功耗
        P_dynamic = stages * 0.5 * C_load * self.V_dd**2 * f_osc
        print(f"動態功耗: {P_dynamic*1e6:.2f} μW")
        
        return {
            't_delay': t_delay,
            'f_osc': f_osc,
            'P_dynamic': P_dynamic
        }
    
    def calculate_transistor_current(self, W, L, V_gs, V_ds, transistor_type='nmos'):
        """計算晶體管電流"""
        if transistor_type == 'nmos':
            k = self.k_n
            V_th = self.V_th_n
        else:
            k = self.k_p
            V_th = self.V_th_p
        
        if V_ds < (V_gs - V_th):
            # 線性區
            I_d = k * (W/L) * ((V_gs - V_th) * V_ds - 0.5 * V_ds**2)
        else:
            # 飽和區
            I_d = 0.5 * k * (W/L) * (V_gs - V_th)**2
        
        return abs(I_d)
    
    def calculate_gate_capacitance(self, W, L):
        """計算閘極電容"""
        C_ox = self.epsilon_ox / self.t_ox
        C_g = C_ox * W * L
        return C_g
    
    def plot_inverter_transfer_characteristic(self, W_n, L_n, W_p, L_p):
        """繪製反相器傳輸特性"""
        V_in = np.linspace(0, self.V_dd, 100)
        V_out = []
        
        for v_in in V_in:
            if v_in < self.V_th_n:
                # NMOS截止，PMOS導通
                v_out = self.V_dd
            elif v_in > (self.V_dd + self.V_th_p):
                # PMOS截止，NMOS導通
                v_out = 0
            else:
                # 兩個晶體管都導通，計算平衡點
                I_n = self.calculate_transistor_current(W_n, L_n, v_in, v_out, 'nmos')
                I_p = self.calculate_transistor_current(W_p, L_p, self.V_dd - v_in, self.V_dd - v_out, 'pmos')
                
                # 簡化的平衡計算
                v_out = self.V_dd * I_n / (I_n + I_p)
            
            V_out.append(v_out)
        
        plt.figure(figsize=(10, 6))
        plt.plot(V_in, V_out)
        plt.xlabel('輸入電壓 (V)')
        plt.ylabel('輸出電壓 (V)')
        plt.title('反相器傳輸特性')
        plt.grid(True)
        plt.axhline(y=self.V_dd/2, color='r', linestyle='--', label='V_{DD}/2')
        plt.axvline(x=self.V_th_n, color='g', linestyle='--', label='V_{TH}')
        plt.legend()
        plt.show()
    
    def plot_power_consumption(self, frequency_range):
        """繪製功耗分析"""
        C_load = 1e-12
        P_dynamic = 0.5 * C_load * self.V_dd**2 * frequency_range
        
        plt.figure(figsize=(10, 6))
        plt.plot(frequency_range / 1e6, P_dynamic * 1e6)
        plt.xlabel('頻率 (MHz)')
        plt.ylabel('動態功耗 (μW)')
        plt.title('CMOS電路功耗分析')
        plt.grid(True)
        plt.show()
    
    def perform_drc_check(self, layout_data):
        """執行設計規則檢查"""
        print("🔍 設計規則檢查 (DRC)")
        print("=" * 40)
        
        violations = []
        
        # 檢查最小線寬
        min_width = 0.18e-6  # 180nm
        for layer, width in layout_data.get('widths', {}).items():
            if width < min_width:
                violations.append(f"層 {layer}: 線寬 {width*1e6:.2f}μm < 最小寬度 {min_width*1e6:.2f}μm")
        
        # 檢查最小間距
        min_spacing = 0.18e-6
        for layer, spacing in layout_data.get('spacings', {}).items():
            if spacing < min_spacing:
                violations.append(f"層 {layer}: 間距 {spacing*1e6:.2f}μm < 最小間距 {min_spacing*1e6:.2f}μm")
        
        # 檢查最小面積
        min_area = 0.12e-12  # 0.12μm²
        for layer, area in layout_data.get('areas', {}).items():
            if area < min_area:
                violations.append(f"層 {layer}: 面積 {area*1e12:.2f}μm² < 最小面積 {min_area*1e12:.2f}μm²")
        
        if violations:
            print("❌ 發現設計規則違反:")
            for violation in violations:
                print(f"  - {violation}")
        else:
            print("✅ 所有設計規則檢查通過")
        
        return len(violations) == 0
    
    def perform_lvs_check(self, netlist_data):
        """執行佈局與電路比對檢查"""
        print("🔍 佈局與電路比對檢查 (LVS)")
        print("=" * 40)
        
        # 簡化的LVS檢查
        schematic_nets = netlist_data.get('schematic', {}).get('nets', [])
        layout_nets = netlist_data.get('layout', {}).get('nets', [])
        
        print(f"電路圖網路數: {len(schematic_nets)}")
        print(f"佈局網路數: {len(layout_nets)}")
        
        # 檢查網路連接
        if len(schematic_nets) == len(layout_nets):
            print("✅ 網路數量匹配")
            
            # 檢查連接性
            for i, (schematic_net, layout_net) in enumerate(zip(schematic_nets, layout_nets)):
                if schematic_net['name'] == layout_net['name']:
                    print(f"✅ 網路 {schematic_net['name']} 匹配")
                else:
                    print(f"❌ 網路 {i} 不匹配")
                    return False
        else:
            print("❌ 網路數量不匹配")
            return False
        
        print("✅ LVS檢查通過")
        return True

def main():
    """主函數 - 演示CMOS設計範例"""
    print("💻 CMOS設計範例")
    print("=" * 50)
    
    designer = CMOSDesignExamples()
    
    while True:
        print("\n🔧 請選擇設計範例：")
        print("1. 反相器設計")
        print("2. NAND閘設計")
        print("3. NOR閘設計")
        print("4. 差分放大器設計")
        print("5. 環形振盪器設計")
        print("6. 設計規則檢查 (DRC)")
        print("7. 佈局與電路比對 (LVS)")
        print("8. 退出")
        
        choice = input("\n請輸入選項 (1-8): ")
        
        if choice == '1':
            W_n = float(input("請輸入NMOS寬度 (μm): ")) * 1e-6
            L_n = float(input("請輸入NMOS長度 (μm): ")) * 1e-6
            W_p = float(input("請輸入PMOS寬度 (μm): ")) * 1e-6
            L_p = float(input("請輸入PMOS長度 (μm): ")) * 1e-6
            designer.design_inverter(W_n, L_n, W_p, L_p)
            
        elif choice == '2':
            W_n = float(input("請輸入NMOS寬度 (μm): ")) * 1e-6
            L_n = float(input("請輸入NMOS長度 (μm): ")) * 1e-6
            W_p = float(input("請輸入PMOS寬度 (μm): ")) * 1e-6
            L_p = float(input("請輸入PMOS長度 (μm): ")) * 1e-6
            designer.design_nand_gate(W_n, L_n, W_p, L_p)
            
        elif choice == '3':
            W_n = float(input("請輸入NMOS寬度 (μm): ")) * 1e-6
            L_n = float(input("請輸入NMOS長度 (μm): ")) * 1e-6
            W_p = float(input("請輸入PMOS寬度 (μm): ")) * 1e-6
            L_p = float(input("請輸入PMOS長度 (μm): ")) * 1e-6
            designer.design_nor_gate(W_n, L_n, W_p, L_p)
            
        elif choice == '4':
            W = float(input("請輸入晶體管寬度 (μm): ")) * 1e-6
            L = float(input("請輸入晶體管長度 (μm): ")) * 1e-6
            I_bias = float(input("請輸入偏置電流 (μA): ")) * 1e-6
            designer.design_differential_amplifier(W, L, I_bias)
            
        elif choice == '5':
            stages = int(input("請輸入振盪器級數: "))
            W = float(input("請輸入晶體管寬度 (μm): ")) * 1e-6
            L = float(input("請輸入晶體管長度 (μm): ")) * 1e-6
            designer.design_ring_oscillator(stages, W, L)
            
        elif choice == '6':
            # 模擬佈局數據
            layout_data = {
                'widths': {'poly': 0.2e-6, 'metal1': 0.15e-6},
                'spacings': {'poly': 0.2e-6, 'metal1': 0.18e-6},
                'areas': {'poly': 0.15e-12, 'metal1': 0.2e-12}
            }
            designer.perform_drc_check(layout_data)
            
        elif choice == '7':
            # 模擬網表數據
            netlist_data = {
                'schematic': {
                    'nets': [
                        {'name': 'VDD', 'connections': ['PMOS1.S', 'PMOS2.S']},
                        {'name': 'VSS', 'connections': ['NMOS1.S', 'NMOS2.S']},
                        {'name': 'OUT', 'connections': ['PMOS1.D', 'NMOS1.D']}
                    ]
                },
                'layout': {
                    'nets': [
                        {'name': 'VDD', 'connections': ['PMOS1.S', 'PMOS2.S']},
                        {'name': 'VSS', 'connections': ['NMOS1.S', 'NMOS2.S']},
                        {'name': 'OUT', 'connections': ['PMOS1.D', 'NMOS1.D']}
                    ]
                }
            }
            designer.perform_lvs_check(netlist_data)
            
        elif choice == '8':
            print("\n👋 感謝使用CMOS設計範例！")
            break
        else:
            print("❌ 無效選項，請重新選擇")

if __name__ == "__main__":
    main() 