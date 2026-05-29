import socket
import json
import os
import base64
from PIL import Image
import io

class Client:
    def __init__(self, host='127.0.0.1', port=12345):
        self.host = host
        self.port = port
        self.socket = None

    # 连接到服务器
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"[+] 已连接到服务器 {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[-] 连接失败: {e}")
            return False
        
    # 发送命令到服务器         
    def send_command(self, command, data=None):
        request = {'command': command}
        if data:
            request.update(data)
            
        try:
            self.socket.send(json.dumps(request).encode('utf-8'))
            response = self.socket.recv(4096 * 1024).decode('utf-8')  # 增大缓冲区以接收截图
            return json.loads(response)
        except Exception as e:
            print(f"[-] 发送命令失败: {e}")
            return None
        
    # 关闭连接        
    def close(self):
        if self.socket:
            self.socket.close()

    # 显示菜单        
    def show_menu(self):
        print("\n" + "="*50)
        print("远程控制客户端")
        print("="*50)
        print("1. 输出字符串")
        print("2. 关机 (60秒后)")
        print("3. 取消关机")
        print("4. 获取C盘文件列表")
        print("5. 截屏")
        print("6. 删除文件")
        print("7. 上传文件")
        print("8. 下载文件")
        print("0. 退出")
        print("="*50)

    # 修复Windows路径格式    
    def fix_windows_path(self, path):
        # 去除首尾空格和引号
        path = path.strip().strip('"').strip("'")
        # 将正斜杠替换为反斜杠
        path = path.replace('/', '\\')
        # 处理多个反斜杠
        while '\\\\' in path:
            path = path.replace('\\\\', '\\')
        return path

    # 运行客户端    
    def run(self):
        if not self.connect():
            return
            
        while True:
            self.show_menu()
            choice = input("\n请选择功能 (0-8): ").strip()
            
            if choice == '0':
                print("[*] 退出程序")
                break
                
            elif choice == '1':
                message = input("请输入要输出的字符串: ")
                response = self.send_command('echo', {'message': message})
                if response and response.get('status') == 'success':
                    print(f"[+] {response.get('message')}")
                else:
                    print(f"[-] 失败: {response.get('message') if response else '未知错误'}")
                    
            elif choice == '2':
                confirm = input("确认要关机吗？(y/n): ")
                if confirm.lower() == 'y':
                    response = self.send_command('shutdown')
                    if response and response.get('status') == 'success':
                        print(f"[+] {response.get('message')}")
                    else:
                        print(f"[-] 失败: {response.get('message') if response else '未知错误'}")
                        
            elif choice == '3':
                response = self.send_command('cancel_shutdown')
                if response and response.get('status') == 'success':
                    print(f"[+] {response.get('message')}")
                else:
                    print(f"[-] 失败: {response.get('message') if response else '未知错误'}")
                    
            elif choice == '4':
                response = self.send_command('list_c_drive')
                if response and response.get('status') == 'success':
                    files = response.get('files', [])
                    print(f"\nC盘文件列表 (共{len(files)}项):")
                    print("-"*80)
                    print(f"{'序号':<6}{'名称':<30}{'类型':<10}{'大小(字节)':<15}")
                    print("-"*80)
                    for i, file in enumerate(files, 1):
                        print(f"{i:<6}{file['name'][:30]:<30}{file['type']:<10}{file['size']:<15}")
                else:
                    print(f"[-] 获取失败: {response.get('message') if response else '未知错误'}")
                    
            elif choice == '5':
                print("[*] 正在截取屏幕...")
                response = self.send_command('screenshot')
                if response and response.get('status') == 'success':
                    img_data = base64.b64decode(response.get('image'))
                    img = Image.open(io.BytesIO(img_data))
                    filename = f"screenshot_{int(__import__('time').time())}.png"
                    img.save(filename)
                    print(f"[+] 截图已保存为: {filename}")
                else:
                    print(f"[-] 截屏失败: {response.get('message') if response else '未知错误'}")
                    
            elif choice == '6':
                # 先获取文件列表供用户选择
                response = self.send_command('list_c_drive')
                if response and response.get('status') == 'success':
                    files = response.get('files', [])
                    print(f"\nC盘文件列表:")
                    print(f"{'序号':<6}{'名称':<50}{'类型':<10}")
                    # 只显示文件（不显示目录）
                    file_index = 1
                    file_map = {}
                    for i, file in enumerate(files, 1):
                        if file['type'] == '文件':
                            print(f"{file_index:<6}{file['name'][:50]:<50}{file['type']:<10}")
                            file_map[file_index] = file['path']
                            file_index += 1
                    
                    if file_map:
                        choice_num = input(f"\n请选择要删除的文件序号 (1-{file_index-1}): ")
                        if choice_num.isdigit():
                            file_num = int(choice_num)
                            if file_num in file_map:
                                file_path = file_map[file_num]
                                confirm = input(f"确认要删除 {file_path} 吗？(y/n): ")
                                if confirm.lower() == 'y':
                                    delete_response = self.send_command('delete_file', {'file_path': file_path})
                                    if delete_response and delete_response.get('status') == 'success':
                                        print(f"[+] {delete_response.get('message')}")
                                    else:
                                        print(f"[-] 删除失败: {delete_response.get('message') if delete_response else '未知错误'}")
                            else:
                                print("[-] 无效的选择")
                        else:
                            print("[-] 请输入有效的数字")
                    else:
                        print("[-] C盘根目录没有文件")
                else:
                    print(f"[-] 获取文件列表失败: {response.get('message') if response else '未知错误'}")
                    
            elif choice == '7':
                local_file = input("请选择要上传的文件路径: ")
                try:
                    with open(local_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    response = self.send_command('upload', {'content': content})
                    if response and response.get('status') == 'success':
                        print(f"[+] {response.get('message')}")
                    else:
                        print(f"[-] 上传失败: {response.get('message') if response else '未知错误'}")
                except Exception as e:
                    print(f"[-] 读取文件失败: {e}")
                    
            elif choice == '8':
                # 先获取文件列表供用户选择
                response = self.send_command('list_c_drive')
                if response and response.get('status') == 'success':
                    files = response.get('files', [])
                    print(f"\nC盘文件列表:")
                    print("-"*80)
                    print(f"{'序号':<6}{'名称':<50}{'类型':<10}")
                    print("-"*80)
                    # 只显示文件（不显示目录）
                    file_index = 1
                    file_map = {}
                    for i, file in enumerate(files, 1):
                        if file['type'] == '文件':
                            print(f"{file_index:<6}{file['name'][:50]:<50}{file['type']:<10}")
                            file_map[file_index] = file['path']
                            file_index += 1
                    
                    if file_map:
                        choice_num = input(f"\n请选择要下载的文件序号 (1-{file_index-1}): ")
                        if choice_num.isdigit():
                            file_num = int(choice_num)
                            if file_num in file_map:
                                file_path = file_map[file_num]
                                download_response = self.send_command('download', {'file_path': file_path})
                                if download_response and download_response.get('status') == 'success':
                                    save_path = input("请输入保存路径 (例如: ./downloaded_file.txt): ")
                                    # 修复路径格式
                                    save_path = self.fix_windows_path(save_path)
                                    
                                    # 如果路径只是文件名，添加当前目录
                                    if not os.path.dirname(save_path):
                                        save_path = os.path.join('.', save_path)
                                    
                                    # 确保目录存在
                                    save_dir = os.path.dirname(save_path)
                                    if save_dir and not os.path.exists(save_dir):
                                        print(f"[*] 目录不存在，正在创建: {save_dir}")
                                        os.makedirs(save_dir, exist_ok=True)
                                    
                                    try:
                                        with open(save_path, 'w', encoding='utf-8') as f:
                                            f.write(download_response.get('content', ''))
                                        print(f"[+] 文件已保存为: {os.path.abspath(save_path)}")
                                    except Exception as e:
                                        print(f"[-] 保存文件失败: {e}")
                                else:
                                    print(f"[-] 下载失败: {download_response.get('message') if download_response else '未知错误'}")
                            else:
                                print("[-] 无效的选择")
                        else:
                            print("[-] 请输入有效的数字")
                    else:
                        print("[-] C盘根目录没有文件")
                else:
                    print(f"[-] 获取文件列表失败: {response.get('message') if response else '未知错误'}")
                    
            else:
                print("[-] 无效的选择，请重新输入")
            
        self.close()

if __name__ == '__main__':
    client = Client()
    client.run()