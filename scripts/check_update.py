import os
import re
import sys
import subprocess
from typing import Tuple, List
import pop_window_pyside as pwp
# import pop_window as pw

# 获取脚本所在目录的上级目录
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 内嵌Git客户端路径
git_path = os.path.join(script_dir, "runtime", "git-2.48.1", "cmd", "git.exe")
# 内嵌Python路径
python_path = os.path.join(script_dir, "runtime", "conda_env", "python.exe")

# 尝试导入gitpython库，如果不存在则安装
try:
    import git
except ImportError:
    print("正在安装gitpython库...")
    subprocess.run([python_path, "-m", "pip", "install", "gitpython"], check=True)
    import git


# 将git目录添加到环境变量中
git_dir = os.path.dirname(git_path)
if git_dir not in os.environ["PATH"]:
    os.environ["PATH"] = git_dir + ";" + os.environ["PATH"]
    print(f"已将Git目录 {git_dir} 添加到环境变量")


def run_git_command(args, cwd=None):
    """执行 Git 命令并实时显示输出"""
    # 优先使用gitpython库
    try:
        print(f"\n执行命令: git {' '.join(args)}")
        print("-" * 60)
        
        # 初始化git仓库对象
        repo = git.Repo(cwd)
        
        # 根据不同的命令执行相应的操作
        if args[0] == 'fetch':
            if len(args) > 1 and args[1] == '--all':
                # 执行fetch --all
                repo.remotes.origin.fetch(prune=True)
                print("已从所有远程分支获取更新")
        else:
            # 对于其他命令，仍然使用subprocess执行
            process = subprocess.Popen(
                ['git'] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=cwd
            )
            
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    cleaned = output.strip()
                    print(cleaned)
                    output_lines.append(cleaned)
            
            print("-" * 60)
            return process.poll(), '\n'.join(output_lines)
        
        print("-" * 60)
        return 0, "命令执行成功"
    except Exception as e:
        # 如果gitpython执行失败，回退到使用subprocess
        print(f"gitpython执行失败: {e}")
        print("回退到使用subprocess执行命令...")
        
        process = subprocess.Popen(
            ['git'] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=cwd
        )
        
        output_lines = []
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                cleaned = output.strip()
                print(cleaned)
                output_lines.append(cleaned)
        
        print("-" * 60)
        return process.poll(), '\n'.join(output_lines)
    
def fetch_remote() -> bool:
    try:
        # 从所有远程存储库中抓取更改
        print("从所有远程存储库中抓取更改……")
        print(script_dir)
        
        # 使用gitpython库执行fetch --all
        repo = git.Repo(script_dir)
        repo.remotes.origin.fetch(prune=True)
        print("已成功从所有远程分支获取更新")
        return True
    except Exception as e:
        print(f'gitpython执行失败: {e}')
        print("回退到使用subprocess执行命令...")
        
        # 如果gitpython执行失败，回退到使用subprocess
        try:
            output = subprocess.run(['git', 'fetch', '--all'], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=script_dir)
            print(output.stdout.decode())
            return True
        except subprocess.CalledProcessError as e:
            print(f'远程仓库更新失败: {e.output.decode()}')
            return False

def get_branch_commits(branch_name: str) -> Tuple[List[str], List[str]]:
    try:
        # 使用gitpython库获取提交记录
        repo = git.Repo(script_dir)
        
        # 获取本地分支提交历史
        local_commits = [commit.hexsha for commit in repo.iter_commits(branch_name)]
        
        # 获取远程分支提交历史
        remote_branch = f'origin/{branch_name}'
        if remote_branch in repo.refs:
            remote_commits = [commit.hexsha for commit in repo.iter_commits(remote_branch)]
        else:
            # 如果当前分支的远程分支不存在，尝试使用origin/master
            if branch_name != "master":
                master_remote = "origin/master"
                if master_remote in repo.refs:
                    print(f"远程分支 {remote_branch} 不存在，尝试使用 {master_remote}")
                    remote_commits = [commit.hexsha for commit in repo.iter_commits(master_remote)]
                else:
                    # 如果origin/master也不存在，使用subprocess回退
                    print(f"远程分支 {remote_branch} 和 {master_remote} 都不存在，使用subprocess回退")
                    try:
                        remote = subprocess.check_output(
                            ['git', 'log', '--pretty=format:%H', remote_branch],
                            text=True,
                            cwd=script_dir
                        ).splitlines()
                        return local_commits, remote
                    except subprocess.CalledProcessError as e:
                        print(f'获取远程提交记录失败: {e.output}')
                        return local_commits, []
            else:
                # 当前分支是master，直接使用subprocess回退
                print(f"远程分支 {remote_branch} 不存在，使用subprocess回退")
                try:
                    remote = subprocess.check_output(
                        ['git', 'log', '--pretty=format:%H', remote_branch],
                        text=True,
                        cwd=script_dir
                    ).splitlines()
                    return local_commits, remote
                except subprocess.CalledProcessError as e:
                    print(f'获取远程提交记录失败: {e.output}')
                    return local_commits, []
        
        return local_commits, remote_commits
    except Exception as e:
        print(f'获取提交记录失败: {e}')
        return [], []

def format_commit_date(commit_date_str):
    """将Git提交日期格式转换为中文显示格式"""
    # 定义月份和星期的映射字典
    month_map = {
        'Jan': '1月', 'Feb': '2月', 'Mar': '3月', 'Apr': '4月',
        'May': '5月', 'Jun': '6月', 'Jul': '7月', 'Aug': '8月',
        'Sep': '9月', 'Oct': '10月', 'Nov': '11月', 'Dec': '12月'
    }
    weekday_map = {
        'Mon': '星期一', 'Tue': '星期二', 'Wed': '星期三',
        'Thu': '星期四', 'Fri': '星期五', 'Sat': '星期六', 'Sun': '星期日'
    }

    # 提取各部分日期时间信息
    weekday_en = commit_date_str[0]
    month_en = commit_date_str[1]
    day = commit_date_str[2]
    time = commit_date_str[3]
    year = commit_date_str[4]

    # 转换为中文格式
    weekday_zh = weekday_map.get(weekday_en, weekday_en)
    month_zh = month_map.get(month_en, month_en)

    # 按要求的格式重组
    formatted_date = f'{year}年{month_zh}{day}日 {weekday_zh} {time}'
    
    return formatted_date

def check_updates():
    print("检查更新中……")
    # 使用gitpython库获取当前远程仓库URL
    try:
        repo = git.Repo(script_dir)
        original_remote_url = repo.remotes.origin.url
    except Exception as e:
        print(f'gitpython获取远程URL失败: {e}')
        print("回退到使用subprocess执行命令...")
        # 如果gitpython执行失败，回退到使用subprocess
        original_remote_url = subprocess.check_output(
            ['git', 'config', '--get', f'remote.origin.url'],
            text=True,
            cwd=script_dir
        ).strip()
    
    # 设置临时加速URL
    print("使用加速地址检查更新……")
    fast_remote_url = "https://ghfast.top/https://github.com/VanillaNahida/xiaozhi-server-onekey"
    subprocess.run(['git', 'remote', 'set-url', 'origin', fast_remote_url], check=True, cwd=script_dir)
    
    try:
        # 使用gitpython库执行fetch --all
        repo = git.Repo(script_dir)
        print("\n执行命令: git fetch --all")
        print("-" * 60)
        repo.remotes.origin.fetch(prune=True)
        print("已从所有远程分支获取更新")
        print("-" * 60)

        # 使用gitpython库获取当前分支
        current_branch = repo.active_branch.name
        

        local_commits, remote_commits = get_branch_commits(current_branch)

        if not remote_commits:
            print('远程分支不存在或无提交')
            return

        latest_remote = remote_commits[0]
        print(f'远程最新提交: {latest_remote}')

        if latest_remote not in local_commits:
            commit_range = f'{local_commits[0]}..{latest_remote}'
            # 计算新增的提交数量（远程有而本地没有的提交）
            new_commits = [commit for commit in remote_commits if commit not in local_commits]
            print(f'❗发现新版本！请运行更新脚本获取最新版一键包！')
            print(f'\n❗新增 {len(new_commits)} 个新提交：\n{"="*50}')
            # 获取详细提交信息
            try:
                repo = git.Repo(script_dir)
                # 构建提交信息
                print(f'\n\033[33m[提交详细信息]\033[0m')
                for commit in repo.iter_commits(commit_range):
                    formatted_date = format_commit_date(commit.committed_datetime.strftime("%a %b %d %H:%M:%S %Y %z").split())
                    print(f"提交日期: {formatted_date}")
                    print(f"Commit Hash: {commit.hexsha}")
                    print(f"作者: {commit.author.name} <{commit.author.email}>")
                    print(f"提交信息：\n    {commit.message.strip()}")
                    print(f"分支信息: {', '.join(ref.name for ref in commit.refs)}")
                    print()
            except Exception as e:
                print(f'gitpython获取提交信息失败: {e}')
                print("回退到使用subprocess执行命令...")
                # 如果gitpython执行失败，回退到使用subprocess
                log_output = subprocess.check_output(
                    ['git', 'log', commit_range, 
                     '--pretty=format:Commit Hash: %C(yellow)%H%Creset %C(cyan)%Creset%n作者: %C(green)%an <%ae>%Creset%n提交信息：%n    %s%n分支信息: %C(auto)%d%Creset'],
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    cwd=script_dir
                )
                # 获取提交日期
                commit_date_str = subprocess.check_output(
                    ['git', 'log', commit_range, '--pretty=format:%cd'],
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    cwd=script_dir
                ).strip().rsplit()
                print(f'\n\033[33m[提交详细信息]\033[0m\n提交日期: {format_commit_date(commit_date_str)}\n{log_output}\n')
            # 调用函数并打印结果
            formatted_date = format_commit_date(commit_date_str)
            print(f'\n\033[33m[提交详细信息]\033[0m\n提交日期: {formatted_date}\n{log_output}\n')
            print(f'{"="*50}\n建议关闭窗口后，运行更新脚本获取一键包最新版！')
            # 显示弹窗并获取用户选择结果
            update_result = pwp.show_github_release()
            # 如果用户选择了立即更新，退出程序
            if update_result:
                sys.exit(1)
            # 如果用户选择了暂不更新，继续执行而不退出
        else:
            print('\n🎉 恭喜！你的本地一键包已是最新版本！')
            # 使用gitpython库获取最新提交信息
            try:
                repo = git.Repo(script_dir)
                latest_commit_obj = repo.head.commit
                formatted_date = format_commit_date(latest_commit_obj.committed_datetime.strftime("%a %b %d %H:%M:%S %Y %z").split())
                print(f'\n当前最新提交: \n提交日期: {formatted_date}')
                print(f"Commit Hash: {latest_commit_obj.hexsha}")
                print(f"作者: {latest_commit_obj.author.name} <{latest_commit_obj.author.email}>")
                print(f"提交信息：\n    {latest_commit_obj.message.strip()}")
                print(f"分支信息: {', '.join(ref.name for ref in latest_commit_obj.refs)}")
            except Exception as e:
                print(f'gitpython获取最新提交信息失败: {e}')
                print("回退到使用subprocess执行命令...")
                # 如果gitpython执行失败，回退到使用subprocess
                latest_commit = subprocess.check_output(
                    ['git', 'log', '-1', '--pretty=format:Commit Hash: %C(yellow)%H%Creset %C(cyan)%Creset%n作者: %C(green)%an <%ae>%Creset%n提交信息：%n    %s%n分支信息: %C(auto)%d%Creset'],
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    cwd=script_dir
                )

                # 提交日期格式化
                commit_date_str = subprocess.check_output(
                    ['git', 'log', '-1', '--pretty=format:%cd'],
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    cwd=script_dir
                ).strip().rsplit()
                print(f'\n当前最新提交: \n提交日期: {format_commit_date(commit_date_str)}\n{latest_commit}')

            # 调用函数并打印结果
            formatted_date = format_commit_date(commit_date_str)
            print(f'\n当前最新提交: \n提交日期: {formatted_date}\n{latest_commit}')
    
    finally:
        # 恢复原始远程URL
        print("恢复原始远程地址……")
        subprocess.run(['git', 'remote', 'set-url', 'origin', original_remote_url], check=True, cwd=script_dir)
    
    print("\n检查完毕！正在启动小智AI服务端……")

def start_onekey():
    """
    启动小智AI全模块带智控台一键包。
    """
    base_dir = os.path.join(script_dir)
    wrapped = rf'start "小智AI全模块服务端" "{python_path}" scripts\main.py'
    subprocess.Popen(wrapped, cwd=base_dir, shell=True)

def check_path_for_chinese():
    """
    检查路径是否有中文
    """
    # 获取当前工作目录
    current_path = os.getcwd()
    # 检查路径是否包含中文字符（Unicode范围）
    has_chinese = bool(re.search(r'[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]', current_path))
    # 输出结果
    if has_chinese:
        print(f"警告，当前路径包含中文等特殊字符: {current_path}\n已自动退出，请将一键包移动到非中文目录再启动！")
        return False
    else:
        return True
        
if __name__ == '__main__':
    # 检查路径合法性
    if not check_path_for_chinese():
        sys.exit()
    if not os.path.exists("./data/.is_first_run"):
        print("检测到首次运行一键包，正在打开说明。")
        if not pwp.first_run():
            print("用户已取消，程序退出。")
            sys.exit()

    os.system("cls")

    if os.path.exists("skip_update.txt"):
        print("检测到 skip_update.txt，跳过更新检查。")
    else:
        check_updates()
    # 启动一键包
    start_onekey()
