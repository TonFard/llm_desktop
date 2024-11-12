import os
import subprocess
import time


def download_model_or_dataset(model_or_dataset_name, save_path, is_dataset=False, local_dir_use_symlinks=True):
    # 设置环境变量 HF_ENDPOINT
    os.environ['HF_ENDPOINT'] = "https://hf-mirror.com"
    command = ['huggingface-cli', 'download', '--resume-download', model_or_dataset_name]
    
    if is_dataset:
        command.extend(['--repo-type', 'dataset'])

    if not local_dir_use_symlinks:
        command.append('--local-dir-use-symlinks')
        command.append('False')

    command.append('--local-dir')
    command.append(save_path)

    while True:
        try:
            subprocess.run(command, check=True)
            # 如果下载成功，打印成功消息并退出循环
            if is_dataset:
                print("数据集下载成功！")
            else:
                print("模型下载成功！")
            break  # 成功后退出循环
        except subprocess.CalledProcessError as e:
            print(f"下载失败，正在重试：{e}")
            # 这里可以根据需要添加延时等待语句，如 
            time.sleep(3)

if __name__ == '__main__':
    model_or_dataset_name = "TencentBAC/Conan-embedding-v1"
    save_path = os.path.join(r"E:\PythonProject\rag", model_or_dataset_name)
    is_dataset = False  # 如果下载数据集，请将此值设置为 True
    local_dir_use_symlinks = True  # 是否使用符号链接
    
    download_model_or_dataset(model_or_dataset_name, save_path, is_dataset, local_dir_use_symlinks)


    