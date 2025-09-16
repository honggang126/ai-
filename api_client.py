import json
import requests
from PyQt5.QtCore import QThread, pyqtSignal

class ApiCallThread(QThread):
    """API调用线程，支持流式响应"""
    progress = pyqtSignal(int)  # 进度信号
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, api_type, api_url, api_key, prompt, model_name, api_format=None, custom_headers=None):
        super().__init__()
        self.api_type = api_type
        self.api_url = api_url
        self.api_key = api_key
        self.prompt = prompt
        self.model_name = model_name
        self.api_format = api_format
        self.custom_headers = custom_headers
        self.response_text = ""  # 存储响应内容
        self.running = True  # 控制线程运行的标志

    def run(self):
        try:
            if self.api_type == "Ollama":
                self._call_ollama_api()
            elif self.api_type == "SiliconFlow":
                self._call_siliconflow_api()
            elif self.api_type == "自定义":
                self._call_custom_api()
            else:
                self.error.emit(f"不支持的API类型: {self.api_type}")
                return
            
            # 完成所有响应
            self.finished.emit(self.response_text, "success")
            
        except Exception as e:
            self.error.emit(f"发生错误: {str(e)}")
    
    def _call_ollama_api(self):
        """调用Ollama API"""
        headers = {"Content-Type": "application/json"}
        data = {
            "model": self.model_name,
            "prompt": self.prompt,
            "stream": True,  # 启用流式传输
            "max_tokens": 5000,
            "temperature": 0.7
        }
        
        # 流式请求
        with requests.post(self.api_url, headers=headers, 
                          data=json.dumps(data), stream=True) as response:
            if response.status_code != 200:
                self.error.emit(f"API调用失败: {response.status_code} - {response.text}")
                return
                
            # 处理流式响应
            total_chars = 0
            for line in response.iter_lines():
                if not self.running:  # 检查是否应该停止
                    return
                    
                if line:
                    # 修复JSON解析错误：尝试直接提取response字段
                    try:
                        # 尝试解析为JSON
                        chunk = json.loads(line.decode('utf-8'))
                        if 'response' in chunk and chunk['response'] is not None:
                            self.response_text += chunk['response']
                            total_chars += len(chunk['response'])
                            # 计算进度（假设最大5000字符）
                            progress = min(100, int(total_chars / 5000 * 100))
                            self.progress.emit(progress)
                    except json.JSONDecodeError:
                        # 如果不是完整JSON，尝试直接提取文本内容
                        line_str = line.decode('utf-8')
                        if 'response' in line_str:
                            # 尝试提取response内容
                            try:
                                start_idx = line_str.find('"response":"') + len('"response":"')
                                end_idx = line_str.find('"', start_idx)
                                response_chunk = line_str[start_idx:end_idx]
                                self.response_text += response_chunk
                                total_chars += len(response_chunk)
                                progress = min(100, int(total_chars / 5000 * 100))
                                self.progress.emit(progress)
                            except:
                                # 如果提取失败，忽略这一行
                                pass
    
    def _call_siliconflow_api(self):
        """调用SiliconFlow API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": self.prompt
                }
            ],
            "stream": True,  # 启用流式传输
            "max_tokens": 5000,
            "temperature": 0.7
        }
        
        # 流式请求
        with requests.post(self.api_url, headers=headers, 
                          data=json.dumps(data), stream=True) as response:
            if response.status_code != 200:
                self.error.emit(f"API调用失败: {response.status_code} - {response.text}")
                return
                
            # 处理流式响应
            total_chars = 0
            for line in response.iter_lines():
                if not self.running:  # 检查是否应该停止
                    return
                    
                if line:
                    # 处理SiliconFlow的流式响应格式
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]  # 移除"data: "前缀
                        
                    if line_str == "[DONE]":
                        break
                        
                    try:
                        # 尝试解析为JSON
                        chunk = json.loads(line_str)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            choice = chunk['choices'][0]
                            if 'delta' in choice and 'content' in choice['delta']:
                                content = choice['delta']['content']
                                if content is not None:  # 检查content是否为None
                                    self.response_text += content
                                    total_chars += len(content)
                                    # 计算进度（假设最大5000字符）
                                    progress = min(100, int(total_chars / 5000 * 100))
                                    self.progress.emit(progress)
                    except json.JSONDecodeError:
                        # 如果不是完整JSON，尝试直接提取内容
                        if '"content":"' in line_str:
                            try:
                                start_idx = line_str.find('"content":"') + len('"content":"')
                                end_idx = line_str.find('"', start_idx)
                                content = line_str[start_idx:end_idx]
                                if content is not None:  # 检查content是否为None
                                    self.response_text += content
                                    total_chars += len(content)
                                    # 计算进度（假设最大5000字符）
                                    progress = min(100, int(total_chars / 5000 * 100))
                                    self.progress.emit(progress)
                            except:
                                # 如果提取失败，忽略这一行
                                pass
    
    def _call_custom_api(self):
        """调用自定义API"""
        print(f"开始调用自定义API: {self.api_url}")
        print(f"API格式: {self.api_format}")
        
        try:
            # 解析自定义请求头
            headers = {"Content-Type": "application/json"}
            if self.custom_headers:
                try:
                    custom_headers = json.loads(self.custom_headers)
                    headers.update(custom_headers)
                    print(f"自定义请求头: {headers}")
                except json.JSONDecodeError:
                    print("警告：自定义请求头格式错误，请确保是有效的JSON格式")
                    self.error.emit("自定义请求头格式错误，请确保是有效的JSON格式")
                    return
            else:
                print("使用默认请求头")
            
            # 根据API格式构建请求数据
            if self.api_format == "OpenAI格式":
                data = {
                    "model": self.model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": self.prompt
                        }
                    ],
                    "stream": True,  # 启用流式传输
                    "max_tokens": 5000,
                    "temperature": 0.7
                }
            else:  # Ollama格式
                data = {
                    "model": self.model_name,
                    "prompt": self.prompt,
                    "stream": True,  # 启用流式传输
                    "max_tokens": 5000,
                    "temperature": 0.7
                }
            
            print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")
            
            # 流式请求
            print("发送API请求...")
            with requests.post(self.api_url, headers=headers, 
                              data=json.dumps(data), stream=True) as response:
                print(f"响应状态码: {response.status_code}")
                if response.status_code != 200:
                    error_msg = f"API调用失败: {response.status_code} - {response.text}"
                    print(error_msg)
                    self.error.emit(error_msg)
                    return
                    
                # 处理流式响应
                print("开始处理流式响应...")
                total_chars = 0
                for line in response.iter_lines():
                    if not self.running:  # 检查是否应该停止
                        print("API调用被停止")
                        return
                        
                    if line:
                        # 根据API格式处理响应
                        if self.api_format == "OpenAI格式":
                            # 处理OpenAI格式的流式响应
                            line_str = line.decode('utf-8')
                            if line_str.startswith("data: "):
                                line_str = line_str[6:]  # 移除"data: "前缀
                                
                            if line_str == "[DONE]":
                                print("OpenAI API响应完成")
                                break
                                
                            try:
                                # 尝试解析为JSON
                                chunk = json.loads(line_str)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    choice = chunk['choices'][0]
                                    if 'delta' in choice and 'content' in choice['delta']:
                                        content = choice['delta']['content']
                                        if content is not None:  # 检查content是否为None
                                            self.response_text += content
                                            total_chars += len(content)
                                            # 计算进度（假设最大5000字符）
                                            progress = min(100, int(total_chars / 5000 * 100))
                                            self.progress.emit(progress)
                            except json.JSONDecodeError:
                                # 如果不是完整JSON，尝试直接提取内容
                                if '"content":"' in line_str:
                                    try:
                                        start_idx = line_str.find('"content":"') + len('"content":"')
                                        end_idx = line_str.find('"', start_idx)
                                        content = line_str[start_idx:end_idx]
                                        if content is not None:  # 检查content是否为None
                                            self.response_text += content
                                            total_chars += len(content)
                                            # 计算进度（假设最大5000字符）
                                            progress = min(100, int(total_chars / 5000 * 100))
                                            self.progress.emit(progress)
                                    except:
                                        # 如果提取失败，忽略这一行
                                        pass
                        else:  # Ollama格式
                            # 处理Ollama格式的流式响应
                            try:
                                # 尝试解析为JSON
                                chunk = json.loads(line.decode('utf-8'))
                                if 'response' in chunk and chunk['response'] is not None:
                                    self.response_text += chunk['response']
                                    total_chars += len(chunk['response'])
                                    # 计算进度（假设最大5000字符）
                                    progress = min(100, int(total_chars / 5000 * 100))
                                    self.progress.emit(progress)
                            except json.JSONDecodeError:
                                # 如果不是完整JSON，尝试直接提取文本内容
                                line_str = line.decode('utf-8')
                                if 'response' in line_str:
                                    # 尝试提取response内容
                                    try:
                                        start_idx = line_str.find('"response":"') + len('"response":"')
                                        end_idx = line_str.find('"', start_idx)
                                        response_chunk = line_str[start_idx:end_idx]
                                        self.response_text += response_chunk
                                        total_chars += len(response_chunk)
                                        progress = min(100, int(total_chars / 5000 * 100))
                                        self.progress.emit(progress)
                                    except:
                                        # 如果提取失败，忽略这一行
                                        pass
        except Exception as e:
            error_msg = f"自定义API调用错误: {str(e)}"
            print(error_msg)
            self.error.emit(error_msg)