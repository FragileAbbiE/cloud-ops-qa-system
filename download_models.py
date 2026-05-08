import os

# --- 核心提速代码：强制开启 hf_transfer ---
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1' 
# ----------------------------------------

# 设置镜像源
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from huggingface_hub import snapshot_download

# 设置模型缓存目录
models_dir = '/root/autodl-tmp/cloud-ops-qa-system/models'

print("开始下载 Qwen2.5-7B-Instruct 模型...")
snapshot_download(
    repo_id="Qwen/Qwen2.5-7B-Instruct",
    local_dir=f"{models_dir}/qwen2.5-7b-instruct"
)

print("模型下载完成！")
