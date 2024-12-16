import requests
import os

def download_images():
    """下載產品相關圖片"""
    # 創建images目錄
    if not os.path.exists('images'):
        os.makedirs('images')
    
    # 圖片URL列表
    image_urls = {
        '5G基地台.png': 'https://example.com/5g-base-station.png',
        '小型基地台.png': 'https://example.com/small-cell.png',
        '網路設備.png': 'https://example.com/network-equipment.png',
        'WiFi6設備.png': 'https://example.com/wifi6-equipment.png',
        '天線.png': 'https://example.com/antenna.png',
        '濾波器.png': 'https://example.com/filter.png',
        '射頻元件.png': 'https://example.com/rf-component.png',
        '光通訊元件.png': 'https://example.com/optical-component.png'
    }
    
    for filename, url in image_urls.items():
        response = requests.get(url)
        if response.status_code == 200:
            with open(f'images/{filename}', 'wb') as f:
                f.write(response.content)
            print(f'已下載: {filename}')
        else:
            print(f'下載失敗: {filename}')

if __name__ == '__main__':
    download_images() 