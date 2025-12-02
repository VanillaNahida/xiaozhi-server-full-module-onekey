# -*- coding: utf-8 -*-
import os
import shutil
import sys
import time
from ruamel.yaml import YAML

def create_config_success_marker(project_root):
    """
    创建配置初始化成功标记文件
    """
    try:
        # 确保data目录存在
        data_dir = os.path.join(project_root, 'data')
        os.makedirs(data_dir, exist_ok=True)
        # 创建成功标记文件
        success_file_path = os.path.join(data_dir, '.config_init_success')
        with open(success_file_path, 'w', encoding='utf-8') as f:
            f.write(f"配置初始化成功\n日期: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✅ 配置初始化成功标记文件已创建: {success_file_path}")
        return True
    except Exception as e:
        print(f"警告：创建配置初始化成功标记文件失败: {str(e)}")
        return False


def check_config_file_exists(config_path):
    """
    检查配置文件是否存在
    """
    exists = os.path.exists(config_path)
    print(f"检查配置文件: {config_path} {'存在' if exists else '不存在'}")
    return exists


def read_config_file(config_path):
    """
    使用ruamel.yaml读取配置文件
    """
    try:
        yaml = YAML()
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.load(f)
        print(f"成功读取配置文件: {config_path}")
        return config_data
    except Exception as e:
        print(f"读取配置文件失败: {config_path}")
        print(f"错误信息: {str(e)}")
        raise


def has_manager_api_section(config_data):
    """
    检查配置文件是否包含完整的manager-api部分
    """
    if not isinstance(config_data, dict):
        print("配置文件数据格式错误：不是有效的字典格式")
        return False
    
    if 'manager-api' not in config_data:
        print("配置文件缺少 'manager-api' 部分")
        return False
    
    manager_api = config_data['manager-api']
    if not isinstance(manager_api, dict):
        print("'manager-api' 部分格式错误：不是有效的字典格式")
        return False
    
    # 检查是否包含url字段
    if 'url' not in manager_api or not manager_api['url']:
        print("'manager-api' 部分缺少或为空的 'url' 字段")
    
    # 检查是否包含secret字段
    if 'secret' not in manager_api or not manager_api['secret'] or manager_api['secret'] == '你的server.secret值':
        print("'manager-api' 部分缺少有效的 'secret' 字段")
    
    print("配置文件包含 'manager-api' 部分")
    return True


def prompt_for_upgrade():
    """
    提示用户是否升级到全模块版服务端
    """
    print("="*60)
    print("配置文件升级提示")
    print("="*60)
    print("检测到你的配置文件可能是单模块版服务端配置")
    print("升级到全模块版服务端可以获得更多功能支持")
    print("重要提示：")
    print("  - 升级后，原有的配置数据不会自动同步")
    print("  - 你需要在新的配置文件中手动设置相关参数")
    print("  - 升级前会自动备份当前配置文件变为 <原文件名>.old")
    print("="*60)
    
    while True:
        try:
            response = input("是否确认升级到全模块版服务端？(y/n)：").strip().lower()
            if response in ['y', 'yes']:
                print("用户确认升级")
                return True
            elif response in ['n', 'no']:
                print("用户取消升级")
                return False
            else:
                print("无效的输入，请输入 'y' 或 'n'")
        except KeyboardInterrupt:
            print("\n操作被用户中断")
            return False
        except Exception as e:
            print(f"输入处理错误: {e}")


def backup_and_replace_config(old_config_path, new_config_source, new_config_path):
    """
    备份旧配置并替换为新配置
    """
    try:
        print("开始配置文件升级流程...")
        
        # 检查新配置源文件是否存在
        if not os.path.exists(new_config_source):
            raise FileNotFoundError(f"新配置源文件不存在: {new_config_source}")
        
        # 备份旧配置
        backup_path = old_config_path + '.old'
        print(f"正在备份原配置文件至: {backup_path}...")
        shutil.copy2(old_config_path, backup_path)
        print(f"✅ 原配置文件已成功备份")
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(new_config_path), exist_ok=True)
        
        # 复制新配置
        print(f"正在复制新配置文件...")
        shutil.copy2(new_config_source, new_config_path)
        print(f"✅ 新配置文件已成功复制到: {new_config_path}")
        
        print("配置文件升级流程完成！")
        return True
        
    except Exception as e:
        print(f"配置文件升级失败: {str(e)}")
        # 如果备份成功但复制失败，尝试恢复
        if os.path.exists(backup_path):
            try:
                print("尝试恢复原配置文件...")
                shutil.copy2(backup_path, old_config_path)
                print("✅ 原配置文件已恢复")
            except:
                print("✗ 原配置文件恢复失败，请手动检查")
        return False


def get_server_secret():
    """
    获取并验证用户输入的server.secret
    """
    print("="*60)
    print("服务器密钥配置")
    print("="*60)
    print("请按照以下步骤操作：")
    print(" 1. 打开智控台")
    print(" 2. 使用管理员账号登录")
    print(" 3. 进入【参数管理】->【参数字典】页面")
    print(" 4. 找到【server.secret】参数")
    print(" 5. 复制其参数值")
    print(" 6. 将复制的值粘贴到下方输入框中")
    print("="*60)
    
    # 常见的UUID格式正则模式（简化版）
    import re
    uuid_pattern = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.IGNORECASE)
    
    attempts = 0
    max_attempts = 5
    
    while attempts < max_attempts:
        try:
            secret = input("请从智控台处复制server.secret，将其粘贴到此处，并按回车继续\n请输入服务器密钥：").strip()
            
            if not secret:
                print("错误：密钥不能为空")
                attempts += 1
                continue
            
            # 移除可能的额外空格或换行符
            secret = secret.strip()
            
            # 检查是否看起来像有效的UUID格式（大多数secret是UUID格式）
            if not uuid_pattern.match(secret) and len(secret) < 16:
                print("警告：输入的密钥看起来可能不是有效的server.secret格式")
                confirm = input("是否确认使用此密钥？(y/n)：").strip().lower()
                if confirm not in ['y', 'yes']:
                    continue
            
            print(f"✅ 服务器密钥已成功获取（长度: {len(secret)} 字符）")
            return secret
            
        except KeyboardInterrupt:
            print("\n操作被用户中断")
            return None
        except Exception as e:
            print(f"输入处理错误: {e}")
        
        attempts += 1
        if attempts < max_attempts:
            print(f"请重新输入，剩余尝试次数：{max_attempts - attempts}")
    
    print("错误：达到最大尝试次数，程序退出")
    raise SystemExit(1)


def update_server_secret(config_path, secret):
    """
    更新配置文件中的server.secret，保持原有格式，并确保替换"你的server.secret值"占位文本
    """
    try:
        print(f"正在更新配置文件中的服务器密钥: {config_path}...")
        
        # 读取原始文件内容，保持格式
        with open(config_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 查找secret行并替换，特别是替换"你的server.secret值"占位文本
        updated = False
        
        # 优先查找包含"你的server.secret值"的行并替换
        for i, line in enumerate(lines):
            if '你的server.secret值' in line:
                # 保留缩进格式
                indent = len(line) - len(line.lstrip())
                lines[i] = ' ' * indent + f'secret: {secret}\n'
                updated = True
                print(f'✅ 已成功写入服务器密钥到配置文件')
                break
        
        # 如果没有找到占位文本，则查找manager-api部分中的secret行
        if not updated:
            for i, line in enumerate(lines):
                if 'secret:' in line and 'manager-api:' in ''.join(lines[max(0, i-5):i+1]):
                    # 保留缩进格式
                    indent = len(line) - len(line.lstrip())
                    lines[i] = ' ' * indent + f'secret: {secret}\n'
                    updated = True
                    break
        
        # 如果没有找到secret行，尝试在manager-api部分添加
        if not updated:
            for i, line in enumerate(lines):
                if 'manager-api:' in line:
                    # 找到manager-api部分，在其下方添加secret
                    indent = 2  # 默认缩进
                    if i + 1 < len(lines):
                        next_line = lines[i+1]
                        if next_line.strip():
                            indent = len(next_line) - len(next_line.lstrip())
                    lines.insert(i+1, ' ' * indent + f'secret: {secret}\n')
                    updated = True
                    break
        
        # 如果还是没有找到，添加整个manager-api部分
        if not updated:
            lines.append('\nmanager-api:\n')
            lines.append('  url: http://127.0.0.1:8002/xiaozhi\n')
            lines.append(f'  secret: {secret}\n')
            updated = True
        
        # 写回文件
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("✅ 服务器密钥已成功更新到配置文件")
        return True
        
    except Exception as e:
        print(f"错误：更新服务器密钥失败: {str(e)}")
        # 尝试使用ruamel.yaml作为备选方法
        try:
            print("尝试使用备选方法更新配置...")
            yaml = YAML()
            yaml.preserve_quotes = True  # 保留引号格式
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.load(f)
            
            if 'manager-api' not in config_data:
                config_data['manager-api'] = {}
            
            config_data['manager-api']['secret'] = secret
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f)
            
            print("✅ 使用备选方法成功更新配置")
            return True
            
        except Exception as e2:
            print(f"错误：备选更新方法也失败: {str(e2)}")
            raise


def main():
    """
    主函数：初始化智控台配置文件
    """
    print("="*60)
    print("小智服务端配置文件初始化工具")
    print("="*60)
    
    try:
        # 获取脚本所在目录的绝对路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建项目根目录路径 (根据目录结构，上一级目录即为项目根目录)
        # 脚本在scripts目录下，scripts目录在项目根目录下
        project_root = os.path.abspath(os.path.join(script_dir, '..'))
        # 动态定义文件路径
        config_path = os.path.join(project_root, 'src', 'main', 'xiaozhi-server', 'data', '.config.yaml')
        config_source_path = os.path.join(project_root, 'src', 'main', 'xiaozhi-server', 'config_from_api.yaml')
        
        print(f"配置文件路径: {config_path}")
        print(f"配置源文件路径: {config_source_path}")
        
        # 检查配置文件是否存在
        if not check_config_file_exists(config_path):
            print(f"配置文件不存在: {config_path}")
            # 如果配置文件不存在，尝试使用新配置
            if os.path.exists(config_source_path):
                print("正在创建新的配置文件...")
                # 确保data目录存在
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                shutil.copy2(config_source_path, config_path)
                print(f"✅ 已创建新的配置文件: {config_path}")
                # 提示用户输入server.secret
                secret = get_server_secret()
                if update_server_secret(config_path, secret):
                    # 成功更新密钥后创建标记文件
                    create_config_success_marker(project_root)
            else:
                print(f"错误：配置源文件不存在: {config_source_path}")
                print("请检查小智服务端安装是否完整")
            return
        
        # 读取配置文件
        print("正在读取配置文件...")
        config_data = read_config_file(config_path)
        
        if not config_data:
            print("错误：配置文件内容为空")
            return
        
        # 检查是否包含manager-api部分
        if not has_manager_api_section(config_data):
            # 提示用户升级
            if prompt_for_upgrade():
                # 备份并替换配置
                if backup_and_replace_config(config_path, config_source_path, config_path):
                    # 获取并更新server.secret
                    secret = get_server_secret()
                    if update_server_secret(config_path, secret):
                        # 成功更新密钥后创建标记文件
                        create_config_success_marker(project_root)
                        print("\n🎉 配置文件初始化完成！")
                else:
                    print("\n❌ 配置文件升级失败，请手动检查")
            else:
                print("已取消升级操作")
        else:
            # 配置文件已包含manager-api部分，检查是否需要更新secret
            manager_api = config_data['manager-api']
            secret_needs_update = False
            
            if not isinstance(manager_api, dict):
                print("错误：manager-api部分格式错误")
                secret_needs_update = True
            elif 'secret' not in manager_api:
                print("发现manager-api部分缺少secret字段")
                secret_needs_update = True
            elif not manager_api['secret']:
                print("发现secret字段为空")
                secret_needs_update = True
            elif manager_api['secret'] == '你的server.secret值':
                print("发现secret字段为默认值")
                secret_needs_update = True
            else:
                print("✅ 配置文件中的secret字段已存在且有效")
            
            if secret_needs_update:
                secret = get_server_secret()
                if update_server_secret(config_path, secret):
                    # 成功更新密钥后创建标记文件
                    create_config_success_marker(project_root)
                    print("\n🎉 配置文件更新完成！")
            else:
                print("配置文件已包含完整的manager-api配置")
                
                # 询问用户是否需要更新secret
                print("\n📋 是否需要更新配置文件中的server.secret?")
                print("   - 输入'y'或'yes'将重新配置secret")
                print("   - 留空或输入其他内容将保持当前secret不变")
                try:
                    response = input("请输入操作选择 (留空不更新): ").strip().lower()
                    
                    if response in ['yes', 'y']:
                        print("\n🔄 正在更新服务器密钥...")
                        secret = get_server_secret()
                        if secret is not None and update_server_secret(config_path, secret):
                            # 成功更新密钥后创建标记文件
                            create_config_success_marker(project_root)
                            print("\n🎉 服务器密钥更新完成！")
                        else:
                            print("\n✅ 已取消服务器密钥更新")
                    else:
                        print("\n✅ 配置检查完成，保持当前配置不变")
                except KeyboardInterrupt:
                    print("\n✅ 已取消操作，保持当前配置不变")
        
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        print("配置文件初始化已取消")
        return
    except Exception as e:
        print(f"\n❌ 配置文件初始化过程中发生错误: {str(e)}")
        import traceback
        print("详细错误信息:")
        traceback.print_exc()
        print("\n请检查错误信息并尝试手动配置")
        return
    
    # 如果程序执行到这里，说明没有进行配置更新但配置已经完整
    # 检查是否需要创建标记文件
    data_dir = os.path.join(project_root, 'data')
    success_file_path = os.path.join(data_dir, '.config_init_success')
    if not os.path.exists(success_file_path):
        create_config_success_marker(project_root)
    
    print("="*30)
    print("配置文件初始化工具执行完毕！")
    print("="*30)


if __name__ == '__main__':
    main()
    print("初始化完成，5秒后自动退出。")
    time.sleep(5)
