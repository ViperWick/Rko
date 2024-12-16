import http.server
import socketserver
import socket

# 獲取本機IP地址
def get_local_ip():
    try:
        # 建立一個臨時socket來獲取本機IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'localhost'

# 設置服務器
PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

# 獲取本機IP
local_ip = get_local_ip()

print(f"啟動服務器...")
print(f"\n可用網址：")
print(f"本機訪問：http://localhost:{PORT}")
print(f"區網訪問：http://{local_ip}:{PORT}")
print("\n可用系統：")
print(f"1. 選手報到系統：/QRCODE.html")
print(f"2. 主辦方掃描系統：/staff.html")
print(f"3. 後台管理系統：/admin.html")

# 允許外部訪問
with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print("\n服務器已啟動，按 Ctrl+C 可以關閉服務器")
    httpd.serve_forever() 