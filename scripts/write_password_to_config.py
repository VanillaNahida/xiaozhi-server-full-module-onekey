import ruamel.yaml
import os
import json

def write_password_to_config(sql_password):
    # 获取脚本所在目录的上一级目录
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 定义配置文件路径
    config_file = os.path.join(script_dir, "src", "main", "manager-api", "src", "main", "resources", "application-dev.yml")

    # 创建ruamel.yaml实例，保留注释和格式
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True  # 保留引号
    yaml.indent(mapping=2, sequence=4, offset=2)  # 设置缩进

    # 读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.load(f)

    # 更新配置文件中的MySQL密码
    if config and 'spring' in config and 'datasource' in config['spring'] and 'druid' in config['spring']['datasource']:
        config['spring']['datasource']['druid']['password'] = sql_password
        
        # 写回配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f)
        
        print(f"✅ MySQL密码已成功写入到配置文件: {config_file}")
    else:
        print("❌ 配置文件格式不正确，无法更新MySQL密码")

if __name__ == "__main__":
    write_password_to_config("123456")
    print("✅ 写入测试密码完成")