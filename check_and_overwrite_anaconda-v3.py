import subprocess
import json
import os

# 定义 Anaconda 和 Miniconda 相关的频道（不包含 conda-forge）
ANACONDA_CHANNELS = [
    "defaults", "repo.anaconda.com", "repo.anaconda.cloud", "anaconda", "anaconda.org",
    "main", "free", "r", "pkgs/main", "pkgs/free", "pkgs/r",
    "mirror.tuna.tsinghua.edu.cn/anaconda", "mirrors.tuna.tsinghua.edu.cn/anaconda",
    "mirrors.ustc.edu.cn/anaconda", "mirrors.aliyun.com/anaconda",
    "mirrors.sustech.edu.cn/anaconda", "mirrors.bfsu.edu.cn/anaconda",
    "mirrors.hit.edu.cn/anaconda", "repo.continuum.io", "conda.anaconda.org",
    "mirrors.tuna.tsinghua.edu.cn/miniconda", "mirrors.ustc.edu.cn/miniconda",
    "mirrors.aliyun.com/miniconda",
]

def run_command(cmd):
    """执行命令并返回输出，失败时抛出异常"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Command failed: {cmd}\nError: {result.stderr}")
    return result.stdout.strip()

def get_env_list():
    """获取所有虚拟环境"""
    try:
        output = run_command("conda env list --json")
        env_data = json.loads(output)
        return env_data["envs"]
    except Exception as e:
        raise Exception(f"Failed to get environment list: {e}")

def check_package_availability(pkg_name):
    """检查 conda-forge 是否有该包"""
    try:
        cmd = f"conda search -c conda-forge {pkg_name} --json"
        output = run_command(cmd)
        search_result = json.loads(output)
        if pkg_name in search_result and len(search_result[pkg_name]) > 0:
            return True
        return False
    except Exception as e:
        print(f"Failed to check availability of {pkg_name} in conda-forge: {e}")
        return False

def check_and_update_env(env_path):
    """检查并用 conda-forge 覆盖安装 Anaconda 包"""
    env_name = os.path.basename(env_path) if "envs" in env_path else "base"
    cmd = f"conda run -p {env_path} conda list --show-channel --json"
    try:
        output = run_command(cmd)
        packages = json.loads(output)
    except Exception as e:
        print(f"Error checking {env_name}: {e}")
        return env_name, [], False, [], []

    # 只收集真正的 Anaconda 或镜像相关的包（排除 conda-forge）
    anaconda_packages = []
    for pkg in packages:
        channel = pkg.get("channel", "unknown")
        if "conda-forge" in channel:
            continue  # 跳过 conda-forge 的包
        if any(anaconda_chan in channel for anaconda_chan in ANACONDA_CHANNELS):
            anaconda_packages.append({
                "name": pkg["name"],
                "version": pkg["version"],
                "channel": channel
            })

    # 用 conda-forge 覆盖安装
    updated = False
    successful_updates = []  # 记录成功更新的包 (包名, 版本)
    failed_updates = []      # 记录需要手动更新的包 (包名, 版本)
    if anaconda_packages:
        print(f"\nProcessing {env_name} ({env_path})...")
        for pkg in anaconda_packages:
            pkg_name = pkg["name"]
            pkg_version = pkg["version"]
            print(f"Found {pkg_name} ({pkg_version}) from {pkg['channel']}...")

            if check_package_availability(pkg_name):
                print(f"{pkg_name} is available in conda-forge, attempting to overwrite...")
                install_cmd = f"conda run -p {env_path} conda install -y -c conda-forge {pkg_name}"
                try:
                    install_output = run_command(install_cmd)
                    print(f"Successfully overwritten {pkg_name} with conda-forge version.")
                    successful_updates.append((pkg_name, pkg_version))
                    updated = True
                except Exception as e:
                    print(f"Failed to overwrite {pkg_name} with conda-forge: {e}")
                    failed_updates.append((pkg_name, pkg_version))
            else:
                print(f"{pkg_name} not found in conda-forge, skipping update. Manual replacement required.")
                failed_updates.append((pkg_name, pkg_version))

    return env_name, anaconda_packages, updated, successful_updates, failed_updates

def main():
    try:
        envs = get_env_list()
        print(f"Found {len(envs)} environments: {envs}")
    except Exception as e:
        print(f"Error: {e}")
        return

    stats = {}
    total_anaconda_pkgs = 0
    envs_with_anaconda = 0
    update_summary = {}  # 按环境记录更新结果

    for env_path in envs:
        env_name, anaconda_pkgs, updated, successful_updates, failed_updates = check_and_update_env(env_path)
        stats[env_name] = {
            "path": env_path,
            "anaconda_packages": anaconda_pkgs,
            "has_anaconda": len(anaconda_pkgs) > 0,
            "updated": updated
        }
        if len(anaconda_pkgs) > 0:
            envs_with_anaconda += 1
            total_anaconda_pkgs += len(anaconda_pkgs)
        # 记录每个环境的更新结果
        update_summary[env_name] = {
            "successful": successful_updates,
            "failed": failed_updates
        }

    print("\n=== Anaconda/Miniconda Package Statistics and Updates ===")
    for env_name, data in stats.items():
        if data["has_anaconda"]:
            print(f"\nEnvironment: {env_name} ({data['path']})")
            print(f"Found {len(data['anaconda_packages'])} Anaconda/Miniconda-related packages:")
            for pkg in data["anaconda_packages"]:
                print(f"  - {pkg['name']} ({pkg['version']}) from {pkg['channel']}")
            if data["updated"]:
                print("  -> Packages overwritten with conda-forge versions.")
            else:
                print("  -> Update failed or partially completed, some packages may remain.")

    if envs_with_anaconda == 0:
        print("\nNo environments use Anaconda/Miniconda-related packages.")

    print(f"\nSummary: {total_anaconda_pkgs} Anaconda/Miniconda-related packages across {envs_with_anaconda} environments.")

    # 按环境总结更新结果
    print("\n=== Update Summary by Environment ===")
    for env_name, summary in update_summary.items():
        print(f"\nEnvironment: {env_name}")
        # 成功更新的包
        if summary["successful"]:
            print("  Successfully updated packages:")
            for pkg_name, pkg_version in summary["successful"]:
                print(f"    - {pkg_name} ({pkg_version})")
        else:
            print("  No packages were successfully updated.")
        # 需要手动更新的包
        if summary["failed"]:
            print("  Packages that need manual update:")
            for pkg_name, pkg_version in summary["failed"]:
                print(f"    - {pkg_name} ({pkg_version})")
        else:
            print("  No packages need manual update.")

    # 保存到文件
    with open("anaconda_overwrite_stats.txt", "w", encoding="utf-8") as f:
        f.write("=== Anaconda/Miniconda Package Statistics and Updates ===\n")
        for env_name, data in stats.items():
            if data["has_anaconda"]:
                f.write(f"\nEnvironment: {env_name} ({data['path']})\n")
                f.write(f"Found {len(data['anaconda_packages'])} Anaconda/Miniconda-related packages:\n")
                for pkg in data["anaconda_packages"]:
                    f.write(f"  - {pkg['name']} ({pkg['version']}) from {pkg['channel']}\n")
                if data["updated"]:
                    f.write("  -> Packages overwritten with conda-forge versions.\n")
                else:
                    f.write("  -> Update failed or partially completed, some packages may remain.\n")
        if envs_with_anaconda == 0:
            f.write("\nNo environments use Anaconda/Miniconda-related packages.\n")
        f.write(f"\nSummary: {total_anaconda_pkgs} Anaconda/Miniconda-related packages across {envs_with_anaconda} environments.\n")

        # 按环境保存更新总结
        f.write("\n=== Update Summary by Environment ===\n")
        for env_name, summary in update_summary.items():
            f.write(f"\nEnvironment: {env_name}\n")
            if summary["successful"]:
                f.write("  Successfully updated packages:\n")
                for pkg_name, pkg_version in summary["successful"]:
                    f.write(f"    - {pkg_name} ({pkg_version})\n")
            else:
                f.write("  No packages were successfully updated.\n")
            if summary["failed"]:
                f.write("  Packages that need manual update:\n")
                for pkg_name, pkg_version in summary["failed"]:
                    f.write(f"    - {pkg_name} ({pkg_version})\n")
            else:
                f.write("  No packages need manual update.\n")

    print("Results saved to 'anaconda_overwrite_stats.txt'")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Script failed: {e}")
