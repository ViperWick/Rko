import http.server
import socketserver
import webbrowser
from pathlib import Path

# HTML內容
HTML_CONTENT = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>簡易HTML編輯器</title>
    <style>
        body {
            margin: 20px;
            font-family: Arial, sans-serif;
        }
        .container {
            display: flex;
            gap: 20px;
        }
        #editor {
            width: 45%;
            height: 400px;
            padding: 10px;
            border: 1px solid #ccc;
        }
        #preview {
            width: 45%;
            height: 400px;
            border: 1px solid #ccc;
            padding: 10px;
            overflow: auto;
        }
        button {
            margin: 10px 0;
            padding: 8px 15px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <h2>簡易HTML編輯器</h2>
    <button onclick="updatePreview()">預覽</button>
    <div class="container">
        <textarea id="editor" placeholder="在這裡輸入HTML代碼"></textarea>
        <div id="preview"></div>
    </div>

    <script>
        function updatePreview() {
            const editor = document.getElementById('editor');
            const preview = document.getElementById('preview');
            preview.innerHTML = editor.value;
        }
    </script>
</body>
</html>
"""

# 創建自定義的請求處理器
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())
        else:
            super().do_GET()

# 設置服務器
PORT = 8000
Handler = MyHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"服務器運行在 http://localhost:{PORT}")
    # 自動打開瀏覽器
    webbrowser.open(f'http://localhost:{PORT}')
    # 啟動服務器
    httpd.serve_forever() 