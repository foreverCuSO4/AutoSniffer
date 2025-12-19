import os
import datetime

def get_file_metadata(file_path):
    """获取并返回文件的元数据字典。"""
    try:
        stat = os.stat(file_path)
        return {
            "size_bytes": stat.st_size,
            # st_ctime 在 Unix 上是最后元数据更改时间，在 Windows 上是创建时间
            "created_at": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"警告：无法读取文件 '{file_path}' 的元数据: {e}")
        return None

def get_directory_structure(path, base_path=None):
    """
    递归地为给定路径创建目录结构的字典。

    :param path: 要分析的目录或文件的路径。
    :return: 代表文件/目录结构的字典。
    """
    if not os.path.exists(path):
        return {"error": "路径不存在"}

    if base_path is None:
        base_path = path

    # 确定基本名称
    name = os.path.basename(path)
    try:
        relative_path = os.path.relpath(path, base_path)
    except Exception:
        relative_path = name

    # 处理文件的情况
    if os.path.isfile(path):
        structure = {
            "name": name,
            "type": "file",
            "relative_path": relative_path,
            "metadata": get_file_metadata(path)
        }
        return structure

    # 处理目录的情况
    elif os.path.isdir(path):
        structure = {
            "name": name,
            "type": "directory",
            "relative_path": relative_path,
            "children": []
        }
        try:
            # 遍历目录中的条目
            for item in os.listdir(path):
                child_path = os.path.join(path, item)
                # 对每个子项进行递归调用
                child_structure = get_directory_structure(child_path, base_path=base_path)
                if child_structure:
                    structure["children"].append(child_structure)
        except PermissionError:
            # 如果没有权限访问目录，则添加一个警告
            structure["warning"] = "无权访问"
        except Exception as e:
            structure["error"] = str(e)

        return structure
    
    # 处理其他类型（如链接等）
    else:
        return {
            "name": name,
            "type": "unknown"
        }
