#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微波工程設計範例程式
包含常見的微波電路設計和計算
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import constants
import scikit_rf as skrf

class MicrowaveDesignExamples:
    """微波工程設計範例類"""
    
    def __init__(self):
        self.c = constants.c  # 光速
        self.epsilon_0 = constants.epsilon_0  # 真空介電常數
        self.mu_0 = constants.mu_0  # 真空磁導率
        self.Z_0 = 50  # 特性阻抗
    
    def design_low_noise_amplifier(self, frequency, gain_db=20, noise_figure=2):
        """低雜訊放大器設計"""
        print("🔊 低雜訊放大器設計")
        print("=" * 40)
        
        # 基本參數
        f_ghz = frequency / 1e9
        print(f"工作頻率: {f_ghz:.2f} GHz")
        print(f"目標增益: {gain_db} dB")
        print(f"目標雜訊指數: {noise_figure} dB")
        
        # 簡化的LNA設計計算
        # 輸入匹配網路
        Z_in = 50 + 10j  # 假設的輸入阻抗
        Z_match = self.calculate_matching_network(Z_in, self.Z_0)
        
        # 輸出匹配網路
        Z_out = 30 - 5j  # 假設的輸出阻抗
        Z_out_match = self.calculate_matching_network(Z_out, self.Z_0)
        
        print(f"\n輸入匹配網路阻抗: {Z_match:.2f} + {Z_match.imag:.2f}j Ω")
        print(f"輸出匹配網路阻抗: {Z_out_match:.2f} + {Z_out_match.imag:.2f}j Ω")
        
        # 繪製頻率響應
        self.plot_frequency_response(frequency, gain_db, noise_figure)
        
        return {
            'frequency': frequency,
            'gain': gain_db,
            'noise_figure': noise_figure,
            'input_match': Z_match,
            'output_match': Z_out_match
        }
    
    def design_power_amplifier(self, frequency, power_output_dbm=30):
        """功率放大器設計"""
        print("🔊 功率放大器設計")
        print("=" * 40)
        
        f_ghz = frequency / 1e9
        print(f"工作頻率: {f_ghz:.2f} GHz")
        print(f"輸出功率: {power_output_dbm} dBm")
        
        # 功率計算
        P_out_w = 10**(power_output_dbm/10) / 1000  # 轉換為瓦特
        V_out_rms = np.sqrt(P_out_w * self.Z_0)
        I_out_rms = V_out_rms / self.Z_0
        
        print(f"輸出電壓 (RMS): {V_out_rms:.2f} V")
        print(f"輸出電流 (RMS): {I_out_rms*1000:.2f} mA")
        
        # 效率計算
        efficiency = 0.6  # 假設效率
        P_dc = P_out_w / efficiency
        print(f"直流功耗: {P_dc:.2f} W")
        print(f"效率: {efficiency*100:.1f}%")
        
        # 繪製功率曲線
        self.plot_power_curves(power_output_dbm)
        
        return {
            'frequency': frequency,
            'power_output': power_output_dbm,
            'voltage_rms': V_out_rms,
            'current_rms': I_out_rms,
            'efficiency': efficiency
        }
    
    def design_mixer(self, rf_freq, lo_freq, if_freq):
        """混頻器設計"""
        print("🔊 混頻器設計")
        print("=" * 40)
        
        print(f"射頻頻率: {rf_freq/1e9:.2f} GHz")
        print(f"本地振盪頻率: {lo_freq/1e9:.2f} GHz")
        print(f"中頻頻率: {if_freq/1e9:.2f} GHz")
        
        # 檢查頻率關係
        if abs(rf_freq - lo_freq) == if_freq:
            print("✅ 頻率關係正確 (下變頻)")
        elif abs(rf_freq + lo_freq) == if_freq:
            print("✅ 頻率關係正確 (上變頻)")
        else:
            print("❌ 頻率關係不正確")
        
        # 轉換損耗計算
        conversion_loss = 6.5  # dB
        print(f"轉換損耗: {conversion_loss} dB")
        
        # 隔離度
        rf_lo_isolation = 25  # dB
        rf_if_isolation = 30  # dB
        lo_if_isolation = 35  # dB
        
        print(f"RF-LO 隔離度: {rf_lo_isolation} dB")
        print(f"RF-IF 隔離度: {rf_if_isolation} dB")
        print(f"LO-IF 隔離度: {lo_if_isolation} dB")
        
        return {
            'rf_frequency': rf_freq,
            'lo_frequency': lo_freq,
            'if_frequency': if_freq,
            'conversion_loss': conversion_loss,
            'isolation': {
                'rf_lo': rf_lo_isolation,
                'rf_if': rf_if_isolation,
                'lo_if': lo_if_isolation
            }
        }
    
    def design_filter(self, filter_type, center_freq, bandwidth, order=3):
        """濾波器設計"""
        print("🔊 濾波器設計")
        print("=" * 40)
        
        print(f"濾波器類型: {filter_type}")
        print(f"中心頻率: {center_freq/1e9:.2f} GHz")
        print(f"頻寬: {bandwidth/1e6:.2f} MHz")
        print(f"階數: {order}")
        
        # 品質因數
        Q = center_freq / bandwidth
        print(f"品質因數 Q: {Q:.1f}")
        
        # 根據濾波器類型計算元件值
        if filter_type.lower() == 'lowpass':
            cutoff_freq = center_freq + bandwidth/2
            components = self.calculate_lowpass_filter(cutoff_freq, order)
        elif filter_type.lower() == 'bandpass':
            components = self.calculate_bandpass_filter(center_freq, bandwidth, order)
        elif filter_type.lower() == 'highpass':
            cutoff_freq = center_freq - bandwidth/2
            components = self.calculate_highpass_filter(cutoff_freq, order)
        else:
            print("❌ 不支援的濾波器類型")
            return None
        
        print(f"\n濾波器元件值:")
        for i, comp in enumerate(components):
            print(f"元件 {i+1}: {comp['value']:.2e} {comp['unit']}")
        
        # 繪製頻率響應
        self.plot_filter_response(filter_type, center_freq, bandwidth, order)
        
        return components
    
    def calculate_matching_network(self, Z_load, Z_source):
        """計算匹配網路"""
        # 簡化的匹配網路計算
        gamma = (Z_load - Z_source) / (Z_load + Z_source)
        Z_match = Z_source * (1 + gamma) / (1 - gamma)
        return Z_match
    
    def calculate_lowpass_filter(self, cutoff_freq, order):
        """計算低通濾波器元件值"""
        # 使用巴特沃斯濾波器設計
        components = []
        for i in range(order):
            if i % 2 == 0:  # 電容
                C = 1 / (2 * np.pi * cutoff_freq * self.Z_0)
                components.append({'value': C, 'unit': 'F', 'type': 'capacitor'})
            else:  # 電感
                L = self.Z_0 / (2 * np.pi * cutoff_freq)
                components.append({'value': L, 'unit': 'H', 'type': 'inductor'})
        return components
    
    def calculate_bandpass_filter(self, center_freq, bandwidth, order):
        """計算帶通濾波器元件值"""
        components = []
        Q = center_freq / bandwidth
        
        for i in range(order):
            # 並聯諧振電路
            L = self.Z_0 / (2 * np.pi * center_freq)
            C = 1 / ((2 * np.pi * center_freq)**2 * L)
            components.append({'value': L, 'unit': 'H', 'type': 'inductor'})
            components.append({'value': C, 'unit': 'F', 'type': 'capacitor'})
        
        return components
    
    def calculate_highpass_filter(self, cutoff_freq, order):
        """計算高通濾波器元件值"""
        components = []
        for i in range(order):
            if i % 2 == 0:  # 電感
                L = self.Z_0 / (2 * np.pi * cutoff_freq)
                components.append({'value': L, 'unit': 'H', 'type': 'inductor'})
            else:  # 電容
                C = 1 / (2 * np.pi * cutoff_freq * self.Z_0)
                components.append({'value': C, 'unit': 'F', 'type': 'capacitor'})
        return components
    
    def plot_frequency_response(self, frequency, gain_db, noise_figure):
        """繪製頻率響應"""
        freq_range = np.linspace(frequency * 0.8, frequency * 1.2, 100)
        
        # 簡化的頻率響應模型
        gain_response = gain_db * np.exp(-((freq_range - frequency) / (frequency * 0.1))**2)
        noise_response = noise_figure + 0.5 * ((freq_range - frequency) / (frequency * 0.1))**2
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # 增益響應
        ax1.plot(freq_range / 1e9, gain_response)
        ax1.set_xlabel('頻率 (GHz)')
        ax1.set_ylabel('增益 (dB)')
        ax1.set_title('LNA 增益響應')
        ax1.grid(True)
        
        # 雜訊指數響應
        ax2.plot(freq_range / 1e9, noise_response)
        ax2.set_xlabel('頻率 (GHz)')
        ax2.set_ylabel('雜訊指數 (dB)')
        ax2.set_title('LNA 雜訊指數響應')
        ax2.grid(True)
        
        plt.tight_layout()
        plt.show()
    
    def plot_power_curves(self, power_output_dbm):
        """繪製功率曲線"""
        input_power = np.linspace(-20, 20, 100)
        output_power = input_power + 20  # 假設20dB增益
        
        # 飽和效應
        saturation_point = 15
        for i in range(len(output_power)):
            if input_power[i] > saturation_point:
                output_power[i] = saturation_point + 20 - (input_power[i] - saturation_point) * 0.5
        
        plt.figure(figsize=(10, 6))
        plt.plot(input_power, output_power)
        plt.xlabel('輸入功率 (dBm)')
        plt.ylabel('輸出功率 (dBm)')
        plt.title('功率放大器特性曲線')
        plt.grid(True)
        plt.axhline(y=power_output_dbm, color='r', linestyle='--', label=f'目標功率: {power_output_dbm} dBm')
        plt.legend()
        plt.show()
    
    def plot_filter_response(self, filter_type, center_freq, bandwidth, order):
        """繪製濾波器響應"""
        freq_range = np.linspace(center_freq * 0.5, center_freq * 1.5, 200)
        
        if filter_type.lower() == 'lowpass':
            cutoff = center_freq + bandwidth/2
            response = 1 / (1 + (freq_range / cutoff)**(2*order))
        elif filter_type.lower() == 'bandpass':
            response = 1 / (1 + ((freq_range - center_freq) / (bandwidth/2))**(2*order))
        elif filter_type.lower() == 'highpass':
            cutoff = center_freq - bandwidth/2
            response = 1 / (1 + (cutoff / freq_range)**(2*order))
        else:
            return
        
        # 轉換為dB
        response_db = 20 * np.log10(response)
        
        plt.figure(figsize=(10, 6))
        plt.plot(freq_range / 1e9, response_db)
        plt.xlabel('頻率 (GHz)')
        plt.ylabel('響應 (dB)')
        plt.title(f'{filter_type} 濾波器頻率響應')
        plt.grid(True)
        plt.axhline(y=-3, color='r', linestyle='--', label='-3dB 點')
        plt.legend()
        plt.show()

def main():
    """主函數 - 演示微波設計範例"""
    print("🔬 微波工程設計範例")
    print("=" * 50)
    
    designer = MicrowaveDesignExamples()
    
    while True:
        print("\n📡 請選擇設計範例：")
        print("1. 低雜訊放大器 (LNA)")
        print("2. 功率放大器 (PA)")
        print("3. 混頻器設計")
        print("4. 濾波器設計")
        print("5. 退出")
        
        choice = input("\n請輸入選項 (1-5): ")
        
        if choice == '1':
            freq = float(input("請輸入頻率 (GHz): ")) * 1e9
            gain = float(input("請輸入目標增益 (dB): "))
            nf = float(input("請輸入目標雜訊指數 (dB): "))
            designer.design_low_noise_amplifier(freq, gain, nf)
            
        elif choice == '2':
            freq = float(input("請輸入頻率 (GHz): ")) * 1e9
            power = float(input("請輸入輸出功率 (dBm): "))
            designer.design_power_amplifier(freq, power)
            
        elif choice == '3':
            rf_freq = float(input("請輸入射頻頻率 (GHz): ")) * 1e9
            lo_freq = float(input("請輸入本地振盪頻率 (GHz): ")) * 1e9
            if_freq = float(input("請輸入中頻頻率 (GHz): ")) * 1e9
            designer.design_mixer(rf_freq, lo_freq, if_freq)
            
        elif choice == '4':
            filter_type = input("請輸入濾波器類型 (lowpass/bandpass/highpass): ")
            center_freq = float(input("請輸入中心頻率 (GHz): ")) * 1e9
            bandwidth = float(input("請輸入頻寬 (MHz): ")) * 1e6
            order = int(input("請輸入濾波器階數: "))
            designer.design_filter(filter_type, center_freq, bandwidth, order)
            
        elif choice == '5':
            print("\n👋 感謝使用微波設計範例！")
            break
        else:
            print("❌ 無效選項，請重新選擇")

if __name__ == "__main__":
    main() 