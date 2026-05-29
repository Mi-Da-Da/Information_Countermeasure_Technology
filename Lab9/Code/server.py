import socket
import threading
import os
import subprocess
import pyautogui
import base64
from io import BytesIO
import json
import sys

class Server:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.server_socket = None
        self.shutdown_scheduled = False
        self.shutdown_timer = None

    # 启动服务器    
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[*] 服务器启动在 {self.host}:{self.port}")
        print("[*] 等待客户端连接...")
        
        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"[+] 客户端连接来自: {client_address}")
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_handler.start()
            except Exception as e:
                print(f"[-] 连接错误: {e}")

    # 处理客户端请求            
    def handle_client(self, client_socket):
        try:
            while True:
                # 接收数据
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break
                    
                request = json.loads(data)
                command = request.get('command')
                
                print(f"[*] 收到命令: {command}")
                
                # 处理不同的命令
                if command == 'echo':
                    response = self.echo(request.get('message', ''))
                elif command == 'shutdown':
                    response = self.shutdown()
                elif command == 'cancel_shutdown':
                    response = self.cancel_shutdown()
                elif command == 'list_c_drive':
                    response = self.list_c_drive()
                elif command == 'screenshot':
                    response = self.screenshot()
                elif command == 'delete_file':
                    response = self.delete_file(request.get('file_path', ''))
                elif command == 'upload':
                    response = self.upload_file(request.get('content', ''))
                elif command == 'download':
                    response = self.download_file(request.get('file_path', ''))
                else:
                    response = {'status': 'error', 'message': '未知命令'}
                    
                # 发送响应
                client_socket.send(json.dumps(response).encode('utf-8'))
                
        except Exception as e:
            print(f"[-] 处理客户端请求时出错: {e}")
        finally:
            client_socket.close()

    # 输出字符串        
    def echo(self, message):
        print(f"[服务端输出]: {message}")
        return {'status': 'success', 'message': f'已输出: {message}'}
    
    # 60秒后关机
    def shutdown(self):
        if self.shutdown_scheduled:
            return {'status': 'error', 'message': '关机已计划，请勿重复设置'}
        
        self.shutdown_scheduled = True
        print("[*] 计划在60秒后关机...")
        
        def shutdown_system():
            try:
                # 等待60秒，但每隔5秒检查一次是否被取消
                for i in range(12):  # 60/5 = 12次
                    if not self.shutdown_scheduled:
                        print("[*] 关机任务已被取消")
                        return
                
                # 如果还没有被取消，执行关机
                if self.shutdown_scheduled:
                    print("[*] 正在执行关机...")
                    # Windows系统
                    try:
                        # 尝试使用shutdown命令
                        subprocess.run(['shutdown', '/s', '/t', '60'], 
                                        capture_output=True, text=True, check=False)
                        print("[*] 已发送关机命令")
                    except Exception as e:
                        print(f"[-] 关机命令执行失败: {e}")
            except Exception as e:
                print(f"[-] 关机过程中出错: {e}")
        
        # 启动关机线程
        self.shutdown_timer = threading.Thread(target=shutdown_system, daemon=True)
        self.shutdown_timer.start()
        
        return {'status': 'success', 'message': '系统将在60秒后关机'}
    
    # 取消关机
    def cancel_shutdown(self):
        if not self.shutdown_scheduled:
            return {'status': 'error', 'message': '没有计划中的关机任务'}
        
        self.shutdown_scheduled = False
        print("[*] 已取消关机计划")
        
        if sys.platform == 'win32':
            os.system('shutdown /a')
        
        return {'status': 'success', 'message': '已取消关机'}
    
    # 获取C盘文件列表
    def list_c_drive(self):
        try:
            files = []
            path = 'C:\\Users\\LIANXIANG\\Desktop'
                
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    item_type = '目录' if os.path.isdir(item_path) else '文件'
                    size = os.path.getsize(item_path) if os.path.isfile(item_path) else 0
                    files.append({
                        'name': item,
                        'type': item_type,
                        'size': size,
                        'path': item_path
                    })
                except:
                    continue
                    
            return {'status': 'success', 'files': files}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    # 截取桌面截图
    def screenshot(self):
        try:
            screenshot = pyautogui.screenshot()
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return {'status': 'success', 'image': img_str}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    # 删除文件
    def delete_file(self, file_path):
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
                return {'status': 'success', 'message': f'已删除文件: {file_path}'}
            else:
                return {'status': 'error', 'message': '文件不存在或不是文件'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    # 上传文件并保存
    def upload_file(self, content):
        try:
            with open('C:\\Users\\LIANXIANG\\Desktop\\receive.txt', 'w', encoding='utf-8') as f:
                f.write(content)
            return {'status': 'success', 'message': '文件已保存为 receive.txt'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    # 下载文件内容
    def download_file(self, file_path):
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {'status': 'success', 'content': content, 'filename': os.path.basename(file_path)}
            else:
                return {'status': 'error', 'message': '文件不存在或不是文件'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

if __name__ == '__main__':
    server = Server()
    server.start()