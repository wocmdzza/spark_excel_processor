#!/usr/bin/env python3
"""
示例脚本：演示如何使用 Spark Excel Processor

此脚本展示了几种常见的使用场景：
1. 加载单个 Excel 文件
2. 加载多个 Excel 文件
3. 执行各种 SQL 查询
4. 数据导出
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from spark_excel_processor import ExcelProcessor


def example_single_file():
    """示例1: 加载单个 Excel 文件"""
    print("\n" + "="*60)
    print("示例1: 加载单个 Excel 文件")
    print("="*60)
    
    # 假设有一个 sales.xlsx 文件
    with ExcelProcessor() as processor:
        # 加载单个文件
        df = processor.load_excel(
            file_path="data/sales.xlsx",
            sheet_name="Sheet1",
            view_name="sales"
        )
        
        # 查看数据结构
        processor.describe_view("sales")
        
        # 执行查询
        print("\n查询所有数据:")
        processor.show("SELECT * FROM sales")
        
        print("\n统计查询:")
        processor.show("""
            SELECT 
                COUNT(*) as total_records,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount
            FROM sales
        """)


def example_multiple_files():
    """示例2: 加载多个 Excel 文件"""
    print("\n" + "="*60)
    print("示例2: 加载多个 Excel 文件")
    print("="*60)
    
    # 配置多个 Excel 文件
    excel_configs = [
        {
            "file_path": "data/sales_2023.xlsx",
            "sheet_name": "Q1",
            "view_name": "sales_q1"
        },
        {
            "file_path": "data/sales_2023.xlsx",
            "sheet_name": "Q2",
            "view_name": "sales_q2"
        },
        {
            "file_path": "data/customers.xlsx",
            "sheet_name": "Sheet1",
            "view_name": "customers"
        }
    ]
    
    with ExcelProcessor() as processor:
        # 加载所有配置的文件
        processor.load_multiple_excels(excel_configs)
        
        # 查看所有视图
        print(f"\n已创建的视图: {processor.get_view_names()}")
        
        # 跨视图查询
        print("\n合并 Q1 和 Q2 销售数据:")
        processor.show("""
            SELECT * FROM sales_q1
            UNION ALL
            SELECT * FROM sales_q2
            ORDER BY sale_date
        """)
        
        # 关联查询
        print("\n销售数据关联客户信息:")
        processor.show("""
            SELECT 
                c.customer_name,
                c.region,
                s.product,
                s.amount,
                s.sale_date
            FROM sales_q1 s
            LEFT JOIN customers c ON s.customer_id = c.customer_id
            ORDER BY s.amount DESC
            LIMIT 20
        """)


def example_data_analysis():
    """示例3: 数据分析场景"""
    print("\n" + "="*60)
    print("示例3: 数据分析场景")
    print("="*60)
    
    with ExcelProcessor() as processor:
        # 加载数据
        processor.load_excel("data/orders.xlsx", "Orders", "orders")
        
        # 1. 月度销售趋势
        print("\n月度销售趋势:")
        processor.show("""
            SELECT 
                DATE_FORMAT(order_date, 'yyyy-MM') as month,
                COUNT(*) as order_count,
                SUM(total_amount) as monthly_revenue
            FROM orders
            GROUP BY DATE_FORMAT(order_date, 'yyyy-MM')
            ORDER BY month
        """)
        
        # 2. 产品类别分析
        print("\n产品类别销售分析:")
        processor.show("""
            SELECT 
                product_category,
                COUNT(*) as order_count,
                SUM(quantity) as total_quantity,
                SUM(total_amount) as total_revenue,
                AVG(unit_price) as avg_price
            FROM orders
            GROUP BY product_category
            ORDER BY total_revenue DESC
        """)
        
        # 3. 客户价值分析
        print("\n客户价值分析 (Top 10):")
        processor.show("""
            SELECT 
                customer_id,
                COUNT(*) as order_count,
                SUM(total_amount) as total_spent,
                AVG(total_amount) as avg_order_value,
                MIN(order_date) as first_order,
                MAX(order_date) as last_order
            FROM orders
            GROUP BY customer_id
            ORDER BY total_spent DESC
            LIMIT 10
        """)
        
        # 4. 创建分析结果视图
        print("\n创建销售汇总视图:")
        processor.query("""
            CREATE OR REPLACE TEMP VIEW sales_summary AS
            SELECT 
                product_category,
                DATE_FORMAT(order_date, 'yyyy-MM') as month,
                COUNT(*) as order_count,
                SUM(total_amount) as revenue
            FROM orders
            GROUP BY product_category, DATE_FORMAT(order_date, 'yyyy-MM')
        """)
        
        # 查询汇总结果
        processor.show("SELECT * FROM sales_summary ORDER BY month, revenue DESC")


def example_custom_queries():
    """示例4: 自定义查询"""
    print("\n" + "="*60)
    print("示例4: 自定义查询")
    print("="*60)
    
    with ExcelProcessor() as processor:
        # 加载数据
        processor.load_excel("data/inventory.xlsx", "Sheet1", "inventory")
        
        # 用户可以在这里输入自定义查询
        custom_queries = [
            # 库存预警查询
            """
            SELECT 
                product_name,
                current_stock,
                min_stock_level,
                CASE 
                    WHEN current_stock < min_stock_level THEN '库存不足'
                    WHEN current_stock < min_stock_level * 1.5 THEN '库存偏低'
                    ELSE '库存正常'
                END as stock_status
            FROM inventory
            ORDER BY current_stock / min_stock_level
            """,
            
            # 库存周转分析
            """
            SELECT 
                product_category,
                AVG(current_stock) as avg_stock,
                AVG(monthly_sales) as avg_monthly_sales,
                CASE 
                    WHEN AVG(monthly_sales) > 0 
                    THEN AVG(current_stock) / AVG(monthly_sales)
                    ELSE 0 
                END as stock_months
            FROM inventory
            GROUP BY product_category
            ORDER BY stock_months
            """
        ]
        
        for i, query in enumerate(custom_queries, 1):
            print(f"\n自定义查询 {i}:")
            processor.show(query)


def main():
    """主函数，运行所有示例"""
    print("Spark Excel Processor - 使用示例")
    print("="*60)
    
    # 检查示例数据文件是否存在
    data_dir = Path("data")
    if not data_dir.exists():
        print("提示: 未找到示例数据目录 'data/'")
        print("请创建示例 Excel 文件或修改示例中的文件路径")
        print("\n您可以:")
        print("1. 创建 'data' 目录并放入 Excel 文件")
        print("2. 修改示例脚本中的文件路径")
        print("3. 使用您的实际数据文件")
        return
    
    try:
        # 运行各个示例
        example_single_file()
        example_multiple_files()
        example_data_analysis()
        example_custom_queries()
        
        print("\n" + "="*60)
        print("所有示例执行完成！")
        print("="*60)
        
    except FileNotFoundError as e:
        print(f"\n错误: {e}")
        print("请确保示例数据文件存在")
    except Exception as e:
        print(f"\n执行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
