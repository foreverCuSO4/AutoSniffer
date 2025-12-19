import os
import subprocess
import tempfile
import time

def print_console_result(result):
    """以正确编码打印控制台结果"""
    # 打印执行结果
    if result['return_code'] == 0:
        print(f"✅ 脚本执行成功！")
    else:
        print(f"❌ 脚本执行失败，返回码: {result['return_code']}")
    
    # 处理标准输出
    if result['stdout'].strip():
        print(f"📋 标准输出:")
        # 逐行打印，避免一次性输出大文本导致的编码问题
        for line in result['stdout'].splitlines():
            if line.strip():
                print(f"   {line}")
    
    # 处理错误输出
    if result['stderr'].strip():
        print(f"⚠️  错误输出:")
        for line in result['stderr'].splitlines():
            if line.strip():
                print(f"   {line}")

def execute_cmd_with_powershell(script_content, working_dir=None, timeout=300, delete_temp=True):
    """
    使用PowerShell执行cmd脚本（更好的中文支持）
    """
    if working_dir is None:
        working_dir = os.getcwd()
    else:
        working_dir = os.path.abspath(working_dir)
        os.makedirs(working_dir, exist_ok=True)
    
    # 创建临时bat文件
    with tempfile.NamedTemporaryFile(
        suffix='.bat', 
        dir=working_dir, 
        delete=False,
        mode='w',
        encoding='utf-8-sig'  # UTF-8 with BOM
    ) as temp_file:
        temp_file.write(script_content)
        temp_bat_path = temp_file.name
    
    result = {
        'return_code': None,
        'stdout': '',
        'stderr': '',
        'executed_file': temp_bat_path
    }

    def _safe_remove(path: str):
        if not path or not os.path.exists(path):
            return
        # Windows may keep a short-lived handle; retry briefly.
        for _ in range(5):
            try:
                os.remove(path)
                return
            except PermissionError:
                time.sleep(0.1)
            except Exception:
                return
    
    try:
        # 使用PowerShell执行，强制UTF-8编码
        command = f'''
        $OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding
        & "{temp_bat_path}"
        '''
        
        # Prepare Windows-specific flags to hide console windows for child process
        startupinfo = None
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            # Avoid importing pywin32; rely on CREATE_NO_WINDOW instead
        except Exception:
            startupinfo = None

        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

        process = subprocess.Popen(
            [
                'powershell',
                '-NoProfile',
                '-NonInteractive',
                '-ExecutionPolicy', 'Bypass',
                '-WindowStyle', 'Hidden',
                '-Command', command
            ],
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            result['return_code'] = process.returncode
            result['stdout'] = stdout
            result['stderr'] = stderr
            
            print_console_result(result)
            
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                stdout, stderr = process.communicate(timeout=5)
                result['stdout'] = stdout or ''
                result['stderr'] = (stderr or '') + f"\n执行超时（{timeout}秒）"
            except Exception:
                result['stderr'] = f"执行超时（{timeout}秒）"
            result['return_code'] = -1
            
    except Exception as e:
        result['return_code'] = -1
        result['stderr'] = str(e)

    finally:
        if delete_temp:
            _safe_remove(temp_bat_path)
    
    return result
