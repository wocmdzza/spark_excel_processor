#!/usr/bin/env python3
"""
Spark Excel Processor - 主程序入口

使用方法:
    python main.py [command] [options]

命令:
    demo        运行演示示例
    interactive 交互式模式
    query       执行单个 SQL 查询
    help        显示帮助信息
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 启用 readline 支持，解决方向键显示转义序列的问题
try:
    import readline
except ImportError:
    pass  # Windows 上可能没有 readline

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from spark_excel_processor import ExcelProcessor


def run_demo():
    """运行演示示例"""
    print("运行 Spark Excel Processor 演示...")
    
    # 创建示例数据目录
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    with ExcelProcessor() as processor:
        print("\n演示完成！")
        print("提示: 请将您的 Excel 文件放入 'data' 目录中")
        print("然后使用以下代码:")
        print("""
from spark_excel_processor import ExcelProcessor

with ExcelProcessor() as processor:
    processor.load_excel("data/your_file.xlsx", "Sheet1", "my_data")
    processor.show("SELECT * FROM my_data LIMIT 10")
        """)


def interactive_mode():
    """交互式模式"""
    print("进入交互式模式...")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'help' 查看可用命令")
    
    with ExcelProcessor() as processor:
        loaded_files = []
        last_query_result = None
        last_source_file = None
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit']:
                    print("退出交互式模式")
                    break
                
                if user_input.lower() == 'help':
                    print_help()
                    continue
                
                if user_input.lower() == 'status':
                    print(f"已加载的视图: {processor.get_view_names()}")
                    continue
                
                # 列出已注册的 UDF
                if user_input.lower() == 'udfs':
                    processor.print_udfs()
                    continue
                
                # 注销所有 UDF
                if user_input.lower().startswith('unregister-all-udfs'):
                    confirm = input("确认注销所有 UDF? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes', '是']:
                        processor.unregister_all_udfs()
                    continue
                
                # 执行 Python 代码
                if user_input.lower().startswith('exec'):
                    code = user_input[4:].strip()
                    if not code:
                        print("用法: exec <python_code>")
                        print("示例: exec def double_it(x): return x * 2")
                        continue
                    try:
                        exec(code, globals())
                        print("✓ 代码执行成功")
                    except Exception as e:
                        print(f"执行错误: {e}")
                    continue
                
                # 从文件加载函数
                if user_input.lower().startswith('load-udf'):
                    parts = user_input.split()
                    if len(parts) < 3:
                        print("用法: load-udf <file_path> <function_name> [alias]")
                        print("示例: load-udf my_module.py my_func")
                        print("      load-udf my_module.py my_func double_it")
                        continue
                    
                    file_path = parts[1]
                    func_name = parts[2]
                    alias = parts[3] if len(parts) > 3 else func_name
                    
                    if not os.path.exists(file_path):
                        print(f"错误: 文件不存在: {file_path}")
                        continue
                    
                    try:
                        import importlib.util
                        spec = importlib.util.spec_from_file_location("temp_module", file_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        func = getattr(module, func_name, None)
                        if func is None:
                            print(f"错误: 在文件 '{file_path}' 中找不到函数 '{func_name}'")
                            continue
                        
                        # 将函数添加到全局命名空间
                        globals()[alias] = func
                        print(f"✓ 已加载函数: {func_name} -> {alias}")
                        print("现在可以使用 register-python-udf 命令注册此函数")
                    except Exception as e:
                        print(f"加载错误: {e}")
                    continue
                
                # 删除视图
                if user_input.lower().startswith('drop'):
                    parts = user_input.split()
                    
                    # drop all - 删除所有视图
                    if len(parts) == 2 and parts[1].lower() == 'all':
                        confirm = input("确认删除所有视图? (y/n): ").strip().lower()
                        if confirm in ['y', 'yes', '是']:
                            processor.drop_all_views()
                        continue
                    
                    # drop <view_name> - 删除指定视图
                    if len(parts) < 2:
                        print("用法: drop <view_name> 或 drop all")
                        continue
                    
                    view_name = parts[1]
                    processor.drop_view(view_name)
                    continue
                
                # 注销指定 UDF
                if user_input.lower().startswith('unregister-udf'):
                    parts = user_input.split()
                    if len(parts) < 2:
                        print("用法: unregister-udf <udf_name>")
                        continue
                    processor.unregister_udf(parts[1])
                    continue
                
                # 注册 Python UDF
                if user_input.lower().startswith('register-python-udf'):
                    parts = user_input.split()
                    if len(parts) < 4:
                        print("用法: register-python-udf <name> <function_name> <return_type> [pandas]")
                        print("示例: register-python-udf double_it double_it integer")
                        print("      register-python-udf double_it double_it integer pandas")
                        continue
                    
                    udf_name = parts[1]
                    func_name = parts[2]
                    return_type = parts[3]
                    is_pandas = len(parts) > 4 and parts[4].lower() == 'pandas'
                    
                    # 从全局/本地变量获取函数
                    import __main__
                    func = getattr(__main__, func_name, None)
                    if func is None:
                        print(f"错误: 找不到函数 '{func_name}'")
                        print("请确保函数已定义在当前会话中")
                        continue
                    
                    try:
                        processor.register_python_udf(udf_name, func, return_type, is_pandas)
                    except Exception as e:
                        print(f"注册失败: {e}")
                    continue
                
                # 注册 Java UDF
                if user_input.lower().startswith('register-java-udf'):
                    parts = user_input.split()
                    if len(parts) < 3:
                        print("用法: register-java-udf <name> <java_class> [jar_path] [return_type]")
                        print("示例: register-java-udf my_udf com.example.MyUDF")
                        print("      register-java-udf my_udf com.example.MyUDF /path/to/udf.jar string")
                        continue
                    
                    udf_name = parts[1]
                    java_class = parts[2]
                    jar_path = parts[3] if len(parts) > 3 and parts[3].endswith('.jar') else None
                    return_type = parts[4] if len(parts) > 4 else None
                    
                    try:
                        processor.register_java_udf(udf_name, java_class, jar_path, return_type)
                    except Exception as e:
                        print(f"注册失败: {e}")
                    continue
                
                # 导出上一次查询结果
                if user_input.lower() == 'export':
                    if last_query_result is None:
                        print("错误: 没有可导出的查询结果。请先执行 SQL 查询。")
                        continue
                    
                    if last_source_file is None:
                        print("错误: 无法确定导出路径。请重新加载文件并查询。")
                        continue
                    
                    # 使用缓存的结果直接导出，不需要重新执行 SQL
                    try:
                        # 获取导出路径
                        source_dir = os.path.dirname(os.path.abspath(last_source_file))
                        default_filename = f"ret_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                        default_path = os.path.join(source_dir, default_filename)
                        
                        print(f"\n默认导出路径: {default_path}")
                        print("（直接回车使用默认路径，或输入自定义路径）")
                        
                        custom_path = input("导出路径: ").strip()
                        
                        if custom_path:
                            if os.path.isdir(custom_path):
                                output_path = os.path.join(custom_path, default_filename)
                            else:
                                output_path = custom_path
                                if not output_path.endswith('.xlsx'):
                                    output_path += '.xlsx'
                        else:
                            output_path = default_path
                        
                        # 使用缓存的结果导出
                        processor.export_to_excel(last_query_result, output_path)
                    except Exception as e:
                        print(f"导出失败: {e}")
                    continue
                
                # 尝试作为 SQL 查询执行
                if user_input.upper().startswith('SELECT') or \
                   user_input.upper().startswith('WITH') or \
                   user_input.upper().startswith('SHOW') or \
                   user_input.upper().startswith('DESCRIBE'):
                    
                    if not processor.get_view_names():
                        print("错误: 没有已加载的数据视图")
                        print("请先加载 Excel 文件:")
                        print("  load <file_path> [sheet_name] [view_name]")
                        continue
                    
                    try:
                        result_df, total_count, is_truncated = processor.preview_query(user_input)
                        last_query_result = result_df
                        last_query_sql = user_input
                    except Exception as e:
                        print(f"SQL 查询错误: {e}")
                
                # 加载 Excel 文件
                elif user_input.lower().startswith('load'):
                    parts = user_input.split()
                    if len(parts) < 2:
                        print("用法: load <file_path> [sheet_name_or_index] [view_name]")
                        print("  sheet_name_or_index: 工作表名称或索引（从0开始）")
                        continue
                    
                    file_path = parts[1]
                    sheet_name_str = parts[2] if len(parts) > 2 else "Sheet1"
                    view_name = parts[3] if len(parts) > 3 else None
                    
                    # 尝试将 sheet_name 解析为整数（索引）
                    try:
                        sheet_name = int(sheet_name_str)
                    except ValueError:
                        sheet_name = sheet_name_str
                    
                    try:
                        processor.load_excel(file_path, sheet_name, view_name)
                        loaded_files.append(file_path)
                        last_source_file = file_path
                    except Exception as e:
                        print(f"加载文件错误: {e}")
                
                # 查看 Excel 文件的工作表列表
                elif user_input.lower().startswith('sheets'):
                    parts = user_input.split()
                    if len(parts) < 2:
                        print("用法: sheets <file_path>")
                        continue
                    
                    file_path = parts[1]
                    try:
                        sheet_names = processor.get_sheet_names(file_path)
                        print(f"\n文件 '{file_path}' 的工作表列表:")
                        for i, name in enumerate(sheet_names):
                            print(f"  [{i}] {name}")
                    except Exception as e:
                        print(f"错误: {e}")
                
                else:
                    print("未知命令。输入 'help' 查看可用命令")
            
            except KeyboardInterrupt:
                print("\n退出交互式模式")
                break
            except EOFError:
                print("\n退出交互式模式")
                break


def print_help():
    """显示帮助信息"""
    print("""
可用命令:
  load <file_path> [sheet_name_or_index] [view_name]  加载 Excel 文件
  sheets <file_path>                                   查看 Excel 文件的工作表列表
  status                                               显示已加载的视图
  drop <view_name>                                     删除指定视图
  drop all                                             删除所有视图
  export                                               导出上一次查询结果
  exec <python_code>                                   执行 Python 代码
  load-udf <file_path> <func_name> [alias]             从文件加载函数
  udfs                                                 列出所有已注册的 UDF
  register-python-udf <name> <func> <type> [pandas]    注册 Python UDF
  register-java-udf <name> <class> [jar] [type]        注册 Java UDF
  unregister-udf <name>                                注销指定 UDF
  unregister-all-udfs                                  注销所有 UDF
  help                                                 显示此帮助信息
  quit/exit                                            退出程序

load 命令说明:
  file_path: Excel 文件路径
  sheet_name_or_index: 工作表名称（如 "Sheet1"）或索引（如 0, 1, 2），默认为 "Sheet1"
  view_name: 自定义视图名称（可选）

示例:
  load data/sales.xlsx                    # 加载默认工作表 "Sheet1"
  load data/sales.xlsx Sales              # 加载名为 "Sales" 的工作表
  load data/sales.xlsx 0                  # 加载第一个工作表（索引 0）
  load data/sales.xlsx 1 my_view          # 加载第二个工作表，命名为 "my_view"
  sheets data/sales.xlsx                  # 查看文件的所有工作表
  drop sales                              # 删除名为 "sales" 的视图
  drop all                                # 删除所有视图（需确认）

exec 命令说明:
  执行 Python 代码，可用于定义 UDF 函数
  
  示例:
    exec def double_it(x): return x * 2
    exec def calculate_tax(amount, rate=0.1): return amount * rate
    exec import math; def sqrt(x): return math.sqrt(x)

load-udf 命令说明:
  从 Python 文件加载函数到当前会话
  
  file_path: Python 文件路径
  func_name: 函数名称
  alias: 可选，函数别名（默认使用原函数名）
  
  示例:
    load-udf my_module.py my_func
    load-udf my_module.py my_func double_it
    load-udf /path/to/utils.py calculate_tax tax

UDF 命令说明:
  register-python-udf: 注册 Python 函数为 UDF
    name: UDF 名称（SQL 中使用的函数名）
    func: Python 函数名（需已在当前会话中定义）
    type: 返回类型（string, integer, double 等）
    pandas: 可选，使用 Pandas UDF 提升性能

  register-java-udf: 注册 Java JAR 中的 UDF
    name: UDF 名称（SQL 中使用的函数名）
    class: Java 类的完整限定名
    jar: JAR 文件路径（可选）
    type: 返回类型（可选，默认 string）

  示例:
    exec def double_it(x): return x * 2
    register-python-udf double_it double_it integer
    register-python-udf my_pandas_udf my_func string pandas
    register-java-udf java_udf com.example.MyUDF /path/to/udf.jar string
    unregister-udf double_it
    udfs                                    # 查看已注册的 UDF

SQL 查询示例:
  SELECT * FROM my_view LIMIT 10
  SELECT COUNT(*) FROM my_view
  SELECT column1, SUM(column2) FROM my_view GROUP BY column1
  SELECT double_it(amount) FROM my_view   # 使用注册的 UDF

导出功能:
  - 执行 SQL 查询后会自动预览结果
  - 系统会询问是否需要导出
  - 可以选择默认路径或自定义路径
  - 默认文件名格式: ret_YYYYMMDD_HHMM.xlsx

提示:
  - 首先使用 'load' 命令加载 Excel 文件
  - 然后使用 SQL 查询数据
  - 查询后可使用 'export' 命令导出结果
  - 视图名称默认为文件名（不含扩展名）
  - 不再需要的视图可以使用 'drop' 命令删除以释放内存
  - 可以使用 'exec' 或 'load-udf' 定义函数，然后注册为 UDF
  - 可以注册自定义 UDF 扩展 SQL 函数能力
    """)


def execute_query(query: str, file_path: str, sheet_name: str = "Sheet1", view_name: str = None):
    """执行单个 SQL 查询并支持导出"""
    with ExcelProcessor() as processor:
        # 加载文件
        processor.load_excel(file_path, sheet_name, view_name)
        
        # 执行查询、预览并支持导出
        processor.query_and_export(query, file_path)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Spark Excel Processor - 使用 PySpark SQL 处理 Excel 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py demo                          运行演示
  python main.py interactive                   交互式模式
  python main.py query -f data.xlsx -q "SELECT * FROM data LIMIT 10"

导出功能:
  query 命令会自动预览查询结果并询问是否导出
  默认导出到源 Excel 文件同级目录，文件名格式: ret_YYYYMMDD_HHMM.xlsx
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # demo 命令
    subparsers.add_parser('demo', help='运行演示示例')
    
    # interactive 命令
    subparsers.add_parser('interactive', help='交互式模式')
    subparsers.add_parser('i', help='交互式模式（简写）')
    
    # query 命令
    query_parser = subparsers.add_parser('query', help='执行 SQL 查询')
    query_parser.add_argument('-f', '--file', required=True, help='Excel 文件路径')
    query_parser.add_argument('-s', '--sheet', default='Sheet1', help='工作表名称')
    query_parser.add_argument('-v', '--view', help='视图名称')
    query_parser.add_argument('-q', '--query', required=True, help='SQL 查询语句')
    
    args = parser.parse_args()
    
    if args.command == 'demo':
        run_demo()
    elif args.command in ['interactive', 'i']:
        interactive_mode()
    elif args.command == 'query':
        execute_query(args.query, args.file, args.sheet, args.view)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
