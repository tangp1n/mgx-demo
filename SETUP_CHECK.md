# 配置检查和安装指南

## ✅ 检查结果

### 后端 (Python)

**语法检查**: ✅ 通过
- `backend/src/config.py` - 语法正确
- `backend/src/main.py` - 语法正确
- `backend/src/models/user.py` - 语法正确

**配置文件**: ✅ 完整
- `backend/requirements.txt` - 存在，包含所有必要依赖
- `backend/pyproject.toml` - 存在，配置正确
- `backend/.flake8` - 存在，配置正确

**需要安装的依赖**:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 前端 (React/TypeScript)

**配置文件**: ✅ 完整
- `fe/package.json` - 存在，包含所有必要依赖
- `fe/tsconfig.json` - 存在，配置正确
- `fe/.eslintrc.json` - 存在，配置正确

**需要安装的依赖**:
```bash
cd fe
npm install
```

## 🚀 启动步骤

### 1. 后端启动

```bash
cd backend
source venv/bin/activate  # 如果还没激活虚拟环境
# 确保 MongoDB 正在运行
# 可选：创建 .env 文件（从 .env.example 复制）
uvicorn src.main:app --reload --port 8000
```

后端将在 `http://localhost:8000` 启动

### 2. 前端启动

```bash
cd fe
# 确保 .env 文件存在（从 .env.example 复制）
npm start
```

前端将在 `http://localhost:3000` 启动

## ⚠️ 注意事项

1. **MongoDB**: 需要先启动 MongoDB 服务
   - 本地: `mongod` 或 `brew services start mongodb-community`
   - 或使用 MongoDB Atlas

2. **环境变量**:
   - 后端: `backend/.env` (从 `.env.example` 复制)
   - 前端: `fe/.env` (从 `.env.example` 复制)

3. **Python 版本**: 需要 Python 3.11+ (当前系统: Python 3.9.6 - 可能需要升级)

4. **Node 版本**: 需要 Node.js 18+ (当前系统: v22.16.0 ✅)

## 📝 发现的问题

1. **Python 版本**: 当前系统 Python 是 3.9.6，但计划要求 3.11+。建议升级 Python 或使用 pyenv。

2. **虚拟环境**: 需要创建 `backend/venv/`

3. **依赖未安装**: 需要安装 Python 和 Node.js 依赖

## 🔍 快速检查命令

```bash
# 检查后端语法
cd backend
python3 -c "import ast; ast.parse(open('src/main.py').read()); print('OK')"

# 检查前端配置
cd fe
node --version
npm --version
```


