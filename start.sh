#!/bin/bash
# Spark Excel Processor - 快速启动脚本

set -e

echo "Spark Excel Processor - 快速启动"
echo "================================"

# 检查是否安装了 uv
if ! command -v uv &> /dev/null; then
    echo "错误: 未找到 uv。请先安装 uv:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "pyproject.toml" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
uv sync

# 生成示例数据（如果不存在）
if [ ! -d "data" ]; then
    echo "生成示例数据..."
    uv run python examples/generate_sample_data.py
fi

echo ""
echo "项目准备完成！"
echo ""
echo "使用方法:"
echo " 1. 交互式模式: uv run python main.py interactive"
echo " 2. 运行演示: uv run python main.py demo"
echo " 3. 使用示例脚本: uv run python examples/basic_usage.py"
echo ""
echo "快速测试:"
echo '  uv run python -c """'
echo 'from spark_excel_processor import ExcelProcessor'
echo ''
echo 'with ExcelProcessor() as processor:'
echo '    processor.load_excel("data/sales.xlsx", "Sales", "sales")'
echo '    processor.show("SELECT * FROM sales LIMIT 5")'
echo '"""'
