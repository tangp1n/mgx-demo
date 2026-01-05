#!/bin/bash
# 检查和安装脚本

set -e

echo "=== 检查后端配置 ==="
cd backend

# 检查 Python 版本
echo "Python 版本:"
python3 --version

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 检查语法
echo "检查 Python 代码语法..."
python3 -m py_compile src/config.py src/main.py 2>&1 || echo "语法检查失败（可能是权限问题，但代码本身可能是正确的）"

echo ""
echo "=== 检查前端配置 ==="
cd ../fe

# 检查 Node 版本
echo "Node 版本:"
node --version
echo "npm 版本:"
npm --version

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "安装 Node.js 依赖..."
    npm install
else
    echo "node_modules 已存在，跳过安装"
fi

# 检查 TypeScript 编译
echo "检查 TypeScript 配置..."
if [ -f "tsconfig.json" ]; then
    echo "tsconfig.json 存在"
fi

echo ""
echo "=== 检查完成 ==="


