import os
import csv
import re

def search_anaconda_words(root_path, output_csv):
    # 定义要查找的关键词
    anaconda_words = [
        'Anaconda', 'anaconda', 'miniconda',
        'anaconda3', 'Anaconda3', 'miniconda3'
    ]
    # 用于存储结果
    results = []
    
    # 遍历目录
    for root, dirs, files in os.walk(root_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # 尝试打开并读取文件
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    # 检查每一行
                    for line_num, line in enumerate(lines, 1):
                        # 检查是否包含关键词
                        for word in anaconda_words:
                            if re.search(r'\b' + re.escape(word) + r'\b', line):
                                results.append({
                                    'file_path': file_path,
                                    'line_number': line_num,
                                    'word': word
                                })
            except Exception as e:
                # 如果文件无法读取，记录错误并继续
                print(f"Error reading {file_path}: {str(e)}")
    
    # 将结果写入CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['file_path', 'line_number', 'word']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

def main():
    # 获取用户输入的路径
    root_path = '/home2/wxq/miniforge3/envs/'
    output_csv = "/home2/wxq/yxb/anaconda_search_results.csv"
    
    # 验证路径是否存在
    if not os.path.exists(root_path):
        print("路径不存在！")
        return
    
    print(f"开始扫描路径: {root_path}")
    search_anaconda_words(root_path, output_csv)
    print(f"扫描完成，结果已保存到: {output_csv}")

if __name__ == "__main__":
    main()