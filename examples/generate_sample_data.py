#!/usr/bin/env python3
"""
生成示例 Excel 数据用于测试

此脚本会创建几个示例 Excel 文件，用于演示 Spark Excel Processor 的功能
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


def create_sales_data(num_rows: int = 100) -> pd.DataFrame:
    """创建销售数据"""
    np.random.seed(42)
    
    # 生成日期范围
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=np.random.randint(0, 365)) for _ in range(num_rows)]
    
    # 产品类别
    categories = ['电子产品', '服装', '食品', '家居', '运动']
    
    # 生成数据
    data = {
        'order_id': [f'ORD{str(i).zfill(6)}' for i in range(1, num_rows + 1)],
        'customer_id': [f'CUST{str(np.random.randint(1, 51)).zfill(4)}' for _ in range(num_rows)],
        'product_category': np.random.choice(categories, num_rows),
        'product_name': [f'产品{np.random.randint(1, 100)}' for _ in range(num_rows)],
        'quantity': np.random.randint(1, 10, num_rows),
        'unit_price': np.round(np.random.uniform(10, 1000, num_rows), 2),
        'total_amount': None,  # 将计算得出
        'order_date': dates,
        'status': np.random.choice(['已完成', '处理中', '已取消'], num_rows, p=[0.7, 0.2, 0.1])
    }
    
    df = pd.DataFrame(data)
    df['total_amount'] = df['quantity'] * df['unit_price']
    
    return df


def create_customer_data(num_rows: int = 50) -> pd.DataFrame:
    """创建客户数据"""
    np.random.seed(42)
    
    regions = ['华北', '华东', '华南', '华中', '西南', '西北', '东北']
    
    data = {
        'customer_id': [f'CUST{str(i).zfill(4)}' for i in range(1, num_rows + 1)],
        'customer_name': [f'客户{i}' for i in range(1, num_rows + 1)],
        'region': np.random.choice(regions, num_rows),
        'city': [f'城市{np.random.randint(1, 20)}' for _ in range(num_rows)],
        'registration_date': [
            datetime(2020, 1, 1) + timedelta(days=np.random.randint(0, 1000))
            for _ in range(num_rows)
        ],
        'customer_type': np.random.choice(['个人', '企业', 'VIP'], num_rows, p=[0.5, 0.3, 0.2]),
        'credit_limit': np.round(np.random.uniform(1000, 100000, num_rows), 2)
    }
    
    return pd.DataFrame(data)


def create_product_data(num_rows: int = 30) -> pd.DataFrame:
    """创建产品数据"""
    np.random.seed(42)
    
    categories = ['电子产品', '服装', '食品', '家居', '运动']
    brands = ['品牌A', '品牌B', '品牌C', '品牌D', '品牌E']
    
    data = {
        'product_id': [f'PROD{str(i).zfill(4)}' for i in range(1, num_rows + 1)],
        'product_name': [f'产品{i}' for i in range(1, num_rows + 1)],
        'category': np.random.choice(categories, num_rows),
        'brand': np.random.choice(brands, num_rows),
        'cost_price': np.round(np.random.uniform(5, 500, num_rows), 2),
        'selling_price': np.round(np.random.uniform(10, 1000, num_rows), 2),
        'stock_quantity': np.random.randint(0, 1000, num_rows),
        'min_stock_level': np.random.randint(10, 100, num_rows)
    }
    
    return pd.DataFrame(data)


def create_multi_sheet_data() -> dict:
    """创建多工作表数据"""
    # Q1 销售数据
    q1_data = create_sales_data(50)
    q1_data['quarter'] = 'Q1'
    
    # Q2 销售数据
    q2_data = create_sales_data(50)
    q2_data['quarter'] = 'Q2'
    # 调整日期到 Q2
    q2_data['order_date'] = q2_data['order_date'].apply(
        lambda x: x.replace(month=x.month + 3) if x.month <= 9 else x
    )
    
    return {
        'Q1': q1_data,
        'Q2': q2_data
    }


def save_to_excel(data: pd.DataFrame, file_path: str, sheet_name: str = 'Sheet1') -> None:
    """保存数据到 Excel 文件"""
    # 确保目录存在
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    # 保存到 Excel
    data.to_excel(file_path, sheet_name=sheet_name, index=False)
    print(f"已创建: {file_path} (工作表: {sheet_name})")


def main():
    """生成所有示例数据"""
    print("生成示例 Excel 数据...")
    print("="*50)
    
    # 创建 data 目录
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # 1. 销售数据
    sales_df = create_sales_data(100)
    save_to_excel(sales_df, "data/sales.xlsx", "Sales")
    
    # 2. 客户数据
    customer_df = create_customer_data(50)
    save_to_excel(customer_df, "data/customers.xlsx", "Customers")
    
    # 3. 产品数据
    product_df = create_product_data(30)
    save_to_excel(product_df, "data/products.xlsx", "Products")
    
    # 4. 多工作表数据
    multi_sheet_data = create_multi_sheet_data()
    
    # 保存多工作表 Excel
    with pd.ExcelWriter("data/quarterly_sales.xlsx") as writer:
        for sheet_name, df in multi_sheet_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"已创建: data/quarterly_sales.xlsx (工作表: {sheet_name})")
    
    # 5. 库存数据
    inventory_data = {
        'product_id': [f'PROD{str(i).zfill(4)}' for i in range(1, 21)],
        'product_name': [f'产品{i}' for i in range(1, 21)],
        'current_stock': np.random.randint(0, 500, 20),
        'min_stock_level': np.random.randint(10, 50, 20),
        'monthly_sales': np.random.randint(5, 100, 20),
        'last_restock_date': [
            datetime(2023, 6, 1) + timedelta(days=np.random.randint(0, 30))
            for _ in range(20)
        ]
    }
    inventory_df = pd.DataFrame(inventory_data)
    save_to_excel(inventory_df, "data/inventory.xlsx", "Inventory")
    
    print("\n" + "="*50)
    print("示例数据生成完成！")
    print("\n生成的文件:")
    for file_path in sorted(data_dir.glob("*.xlsx")):
        print(f"  - {file_path}")
    
    print("\n使用方法:")
    print("""
from spark_excel_processor import ExcelProcessor

with ExcelProcessor() as processor:
    # 加载销售数据
    processor.load_excel("data/sales.xlsx", "Sales", "sales")
    
    # 查询数据
    processor.show("SELECT * FROM sales LIMIT 10")
    
    # 聚合分析
    processor.show(\"\"\"
        SELECT 
            product_category,
            COUNT(*) as order_count,
            SUM(total_amount) as total_revenue
        FROM sales
        GROUP BY product_category
        ORDER BY total_revenue DESC
    \"\"\")
    """)


if __name__ == "__main__":
    main()
