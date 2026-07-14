# Spark Excel Processor

使用 PySpark SQL 操作本地 Excel 文件，让 Excel 数据处理更便捷。

## 功能特性

- ✅ 支持读取单个或多个 Excel 文件
- ✅ 支持指定每个文件的 sheet_name（支持名称或索引）
- ✅ 自动创建临时视图，支持 Spark SQL 查询
- ✅ 支持多表关联查询和复杂数据分析
- ✅ 简洁易用的 API 接口
- ✅ 支持链式查询操作
- ✅ 查询结果智能预览（大数据集部分预览，小数据集全部预览）
- ✅ 支持导出查询结果到 Excel 文件
- ✅ 交互式导出路径选择（支持默认路径和自定义路径）
- ✅ 结果集缓存优化（避免导出时重复执行查询）
- ✅ 自动管理缓存生命周期（导出完成后自动释放）
- ✅ 支持注册自定义 UDF（Python 函数和 Java JAR 包）
- ✅ 支持 Pandas UDF（向量化 UDF，性能更高）

## 系统要求

### Java 版本要求

**PySpark 4.x 需要 Java 17 或更高版本。**

检查 Java 版本：
```bash
java -version
```

如果需要安装 Java 17：

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install openjdk-17-jdk
```

**macOS (使用 Homebrew):**
```bash
brew install openjdk@17
```

**CentOS/RHEL:**
```bash
sudo yum install java-17-openjdk-devel
```

安装后设置 JAVA_HOME：
```bash
# Linux/macOS
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64  # Linux
export JAVA_HOME=/usr/local/opt/openjdk@17  # macOS

# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64' >> ~/.bashrc
```

### Python 版本要求

- Python 3.13 或更高版本

## 安装

### 使用 uv（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd spark-excel-processor

# 安装依赖
uv sync
```

### 使用 pip

```bash
pip install pyspark openpyxl pandas
```

## 快速开始

### 1. 基础用法

```python
from spark_excel_processor import ExcelProcessor

# 创建处理器实例
with ExcelProcessor() as processor:
    # 加载 Excel 文件
    processor.load_excel(
        file_path="data/sales.xlsx",
        sheet_name="Sheet1",
        view_name="sales"
    )
    
    # 执行 SQL 查询
    processor.show("SELECT * FROM sales LIMIT 10")
    
    # 聚合查询
    processor.show("""
        SELECT 
            product_category,
            COUNT(*) as total_sales,
            SUM(amount) as total_amount
        FROM sales
        GROUP BY product_category
        ORDER BY total_amount DESC
    """)
```

### 2. 多文件处理

```python
from spark_excel_processor import ExcelProcessor

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
        "sheet_name": "Customers",
        "view_name": "customers"
    }
]

with ExcelProcessor() as processor:
    # 加载所有文件
    processor.load_multiple_excels(excel_configs)
    
    # 跨表关联查询
    processor.show("""
        SELECT 
            c.customer_name,
            s.product,
            s.amount
        FROM sales_q1 s
        JOIN customers c ON s.customer_id = c.customer_id
        ORDER BY s.amount DESC
    """)
    
    # 合并多个表的数据
    processor.show("""
        SELECT * FROM sales_q1
        UNION ALL
        SELECT * FROM sales_q2
        ORDER BY sale_date
    """)
```

### 3. 高级用法

```python
from spark_excel_processor import ExcelProcessor

with ExcelProcessor() as processor:
    # 加载数据
    processor.load_excel("data/orders.xlsx", "Orders", "orders")
    
    # 创建分析视图
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
    
    # 查询分析结果
    processor.show("SELECT * FROM sales_summary ORDER BY month, revenue DESC")
    
    # 获取 DataFrame 进行进一步处理
    df = processor.get_dataframe("orders")
    if df:
        print(f"数据行数: {df.count()}")
        print(f"列名: {df.columns}")
```

### 4. 查询结果预览与导出

```python
from spark_excel_processor import ExcelProcessor

with ExcelProcessor() as processor:
    # 加载数据
    processor.load_excel("data/sales.xlsx", "Sales", "sales")
    
    # 执行查询并预览（自动处理大数据集）
    result_df, total_count, is_truncated = processor.preview_query("""
        SELECT 
            product_category,
            COUNT(*) as order_count,
            SUM(total_amount) as total_revenue
        FROM sales
        GROUP BY product_category
        ORDER BY total_revenue DESC
    """)
    
    # 交互式导出（会询问用户导出路径）
    processor.query_and_export(
        "SELECT * FROM sales WHERE amount > 100",
        "data/sales.xlsx"
    )
    
    # 直接导出到指定路径
    processor.export_to_excel(result_df, "output/analysis_result.xlsx")
```

### 5. 命令行使用

```bash
# query 命令（自动预览并询问导出）
uv run python main.py query -f data/sales.xlsx -s Sales -q "SELECT * FROM sales LIMIT 100"

# 使用索引指定工作表
uv run python main.py query -f data/sales.xlsx -s 0 -q "SELECT * FROM sales LIMIT 100"

# 交互式模式
uv run python main.py interactive
> sheets data/sales.xlsx           # 查看所有工作表
> load data/sales.xlsx Sales sales # 使用名称加载
> load data/sales.xlsx 0 sales     # 使用索引加载
> SELECT * FROM sales WHERE amount > 500
> export                           # 导出上一次查询结果
> drop sales                       # 删除指定视图释放内存
> drop all                         # 删除所有视图
```

### 6. 自定义 UDF

#### 注册 Python UDF

```python
from spark_excel_processor import ExcelProcessor

# 定义 Python 函数
def double_it(x):
    return x * 2

def calculate_tax(amount, rate=0.1):
    return amount * rate

with ExcelProcessor() as processor:
    # 加载数据
    processor.load_excel("data/sales.xlsx", "Sales", "sales")
    
    # 注册普通 UDF
    processor.register_python_udf("double_it", double_it, "integer")
    
    # 注册带默认参数的 UDF
    processor.register_python_udf("calculate_tax", calculate_tax, "double")
    
    # 使用 UDF 查询
    processor.show("SELECT product, amount, double_it(amount) as doubled FROM sales")
    processor.show("SELECT product, amount, calculate_tax(amount) as tax FROM sales")
```

#### 注册 Pandas UDF（向量化，性能更高）

```python
import pandas as pd
from pyspark.sql.types import LongType

# 定义 Pandas UDF 函数
def pandas_double(series: pd.Series) -> pd.Series:
    return series * 2

with ExcelProcessor() as processor:
    processor.load_excel("data/sales.xlsx", "Sales", "sales")
    
    # 注册 Pandas UDF
    processor.register_python_udf("pandas_double", pandas_double, LongType(), is_pandas_udf=True)
    
    # 使用 Pandas UDF
    processor.show("SELECT product, amount, pandas_double(amount) as doubled FROM sales")
```

#### 注册 Java UDF

```python
with ExcelProcessor() as processor:
    processor.load_excel("data/sales.xlsx", "Sales", "sales")
    
    # 注册 Java UDF（需要 JAR 文件）
    processor.register_java_udf(
        name="java_upper",
        java_class="com.example.StringUpperUDF",
        jar_path="/path/to/udf.jar",
        return_type="string"
    )
    
    # 使用 Java UDF
    processor.show("SELECT java_upper(product) as upper_product FROM sales")
```

#### 管理 UDF

```python
with ExcelProcessor() as processor:
    # 列出所有已注册的 UDF
    processor.print_udfs()
    
    # 获取 UDF 字典
    udfs = processor.list_udfs()
    
    # 注销指定 UDF
    processor.unregister_udf("double_it")
    
    # 注销所有 UDF
    processor.unregister_all_udfs()
```

#### 交互式模式中的 UDF 命令

```bash
uv run python main.py interactive
> register-python-udf double_it double_it integer          # 注册 Python UDF
> register-python-udf pandas_udf my_func string pandas     # 注册 Pandas UDF
> register-java-udf java_udf com.example.MyUDF /path.jar   # 注册 Java UDF
> udfs                                                      # 列出已注册 UDF
> unregister-udf double_it                                  # 注销指定 UDF
> unregister-all-udfs                                       # 注销所有 UDF
```

## API 参考

### ExcelProcessor 类

#### 初始化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| app_name | str | "SparkExcelProcessor" | Spark 应用名称 |
| master | str | "local[*]" | Spark master URL |

#### 主要方法

##### `load_excel(file_path, sheet_name, view_name, header, infer_schema)`

加载单个 Excel 文件并创建临时视图。

**参数:**
- `file_path` (str): Excel 文件路径
- `sheet_name` (str | int): 工作表名称（字符串）或索引（整数，从0开始），默认为 "Sheet1"
- `view_name` (str, optional): 临时视图名称，默认为文件名
- `header` (bool): 是否将第一行作为表头，默认为 True
- `infer_schema` (bool): 是否自动推断数据类型，默认为 True

**返回:** Spark DataFrame

**示例:**
```python
# 使用工作表名称
processor.load_excel("data/sales.xlsx", "Sales", "sales")

# 使用工作表索引
processor.load_excel("data/sales.xlsx", 0, "sales")
```

##### `get_sheet_names(file_path)`

获取 Excel 文件的所有工作表名称。

**参数:**
- `file_path` (str): Excel 文件路径

**返回:** List[str] 工作表名称列表

##### `load_multiple_excels(excel_configs)`

加载多个 Excel 文件并创建临时视图。

**参数:**
- `excel_configs` (List[Dict]): Excel 配置列表

**返回:** 字典，键为视图名称，值为 DataFrame

##### `query(sql)`

执行 Spark SQL 查询。

**参数:**
- `sql` (str): SQL 查询语句

**返回:** 查询结果 DataFrame

##### `show(sql, num_rows, truncate)`

执行 SQL 查询并显示结果。

**参数:**
- `sql` (str): SQL 查询语句
- `num_rows` (int): 显示的行数，默认为 20
- `truncate` (bool): 是否截断长字符串，默认为 True

##### `get_view_names()`

获取所有已创建的视图名称。

**返回:** List[str]

##### `get_dataframe(view_name)`

获取指定视图的 DataFrame。

**参数:**
- `view_name` (str): 视图名称

**返回:** Optional[DataFrame]

##### `drop_view(view_name)`

删除指定的临时视图并释放内存。

**参数:**
- `view_name` (str): 视图名称

**返回:** bool 是否删除成功

**示例:**
```python
processor.drop_view("sales")  # 删除名为 "sales" 的视图
```

##### `drop_all_views()`

删除所有临时视图并释放内存。

**返回:** int 成功删除的视图数量

**示例:**
```python
processor.drop_all_views()  # 删除所有视图
```

##### `describe_view(view_name)`

显示视图的结构信息。

**参数:**
- `view_name` (str): 视图名称

##### `preview_query(sql, preview_rows)`

执行 SQL 查询并预览结果（智能处理大数据集）。

**参数:**
- `sql` (str): SQL 查询语句
- `preview_rows` (int): 预览行数，默认为 20

**返回:** tuple (DataFrame, total_count, is_truncated)

##### `export_to_excel(df, output_path, sheet_name, index)`

将 DataFrame 导出到 Excel 文件。

**参数:**
- `df` (DataFrame): Spark DataFrame
- `output_path` (str): 输出文件路径
- `sheet_name` (str): 工作表名称，默认为 "Sheet1"
- `index` (bool): 是否包含索引，默认为 False

**返回:** 实际导出的文件路径

##### `query_and_export(sql, source_file_path, preview_rows)`

执行查询、预览并交互式导出。

**参数:**
- `sql` (str): SQL 查询语句
- `source_file_path` (str): 源 Excel 文件路径（用于确定默认导出目录）
- `preview_rows` (int): 预览行数，默认为 20

**返回:** 导出的文件路径，如果未导出则返回 None

##### `close()`

关闭 Spark 会话。

##### `register_python_udf(name, func, return_type, is_pandas_udf)`

注册 Python 函数为 UDF。

**参数:**
- `name` (str): UDF 名称（在 SQL 中使用的函数名）
- `func` (Callable): Python 函数
- `return_type` (str | DataType): 返回类型（如 "string", "integer", "double" 或 Spark DataType）
- `is_pandas_udf` (bool): 是否为 Pandas UDF（向量化 UDF，性能更高），默认为 False

**返回:** 注册的 UDF 名称

**示例:**
```python
def double_it(x):
    return x * 2

# 普通 UDF
processor.register_python_udf("double_it", double_it, "integer")

# Pandas UDF
processor.register_python_udf("pandas_udf", my_func, "string", is_pandas_udf=True)
```

##### `register_java_udf(name, java_class, jar_path, return_type)`

注册 Java JAR 中的 UDF。

**参数:**
- `name` (str): UDF 名称（在 SQL 中使用的函数名）
- `java_class` (str): Java 类的完整限定名（如 "com.example.MyUDF"）
- `jar_path` (str, optional): JAR 文件路径（可选，如果已添加到 classpath 则不需要）
- `return_type` (str | DataType, optional): 返回类型（可选，默认为 StringType）

**返回:** 注册的 UDF 名称

**示例:**
```python
processor.register_java_udf(
    name="java_udf",
    java_class="com.example.MyUDF",
    jar_path="/path/to/udf.jar",
    return_type="string"
)
```

##### `list_udfs()`

列出所有已注册的自定义 UDF。

**返回:** UDF 字典，键为 UDF 名称，值为 UDF 信息

##### `print_udfs()`

打印所有已注册的 UDF 信息。

##### `unregister_udf(name)`

注销指定的 UDF。

**参数:**
- `name` (str): UDF 名称

**返回:** bool 是否注销成功

##### `unregister_all_udfs()`

注销所有自定义 UDF。

**返回:** 成功注销的 UDF 数量

## 项目结构

```
spark-excel-processor/
├── spark_excel_processor.py  # 主程序文件
├── examples/                 # 示例脚本
│   └── basic_usage.py        # 基础使用示例
├── config_example.py         # 配置示例
├── main.py                   # 程序入口
├── pyproject.toml            # 项目配置
└── README.md                 # 项目文档
```

## 使用场景

1. **数据整合**: 将多个 Excel 文件的数据整合到一起进行分析
2. **数据清洗**: 使用 SQL 对 Excel 数据进行清洗和转换
3. **报表生成**: 从 Excel 数据生成各种统计报表
4. **数据分析**: 对 Excel 数据进行复杂的统计分析
5. **数据验证**: 验证 Excel 数据的完整性和准确性

## 示例查询

### 基础查询

```sql
-- 查询所有数据
SELECT * FROM sales

-- 条件查询
SELECT * FROM sales WHERE amount > 1000

-- 排序查询
SELECT * FROM sales ORDER BY amount DESC

-- 分页查询
SELECT * FROM sales LIMIT 10 OFFSET 20
```

### 聚合查询

```sql
-- 统计总销售额
SELECT SUM(amount) as total_sales FROM sales

-- 按类别统计
SELECT 
    category,
    COUNT(*) as count,
    SUM(amount) as total,
    AVG(amount) as average
FROM sales
GROUP BY category

-- 多条件聚合
SELECT 
    category,
    region,
    SUM(amount) as total
FROM sales
GROUP BY category, region
HAVING SUM(amount) > 10000
```

### 多表关联

```sql
-- 内连接
SELECT 
    s.product,
    c.customer_name,
    s.amount
FROM sales s
INNER JOIN customers c ON s.customer_id = c.customer_id

-- 左连接
SELECT 
    s.product,
    COALESCE(c.customer_name, 'Unknown') as customer_name,
    s.amount
FROM sales s
LEFT JOIN customers c ON s.customer_id = c.customer_id

-- 多表关联
SELECT 
    s.product,
    c.customer_name,
    p.product_name,
    s.amount
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
JOIN products p ON s.product_id = p.product_id
```

### 窗口函数

```sql
-- 排名查询
SELECT 
    product,
    amount,
    RANK() OVER (ORDER BY amount DESC) as rank
FROM sales

-- 累计求和
SELECT 
    product,
    amount,
    SUM(amount) OVER (ORDER BY sale_date) as cumulative_sum
FROM sales

-- 同比分析
SELECT 
    product,
    amount,
    LAG(amount) OVER (PARTITION BY product ORDER BY sale_date) as prev_amount,
    amount - LAG(amount) OVER (PARTITION BY product ORDER BY sale_date) as growth
FROM sales
```

### 使用自定义 UDF

```sql
-- 使用注册的 Python UDF
SELECT 
    product,
    amount,
    double_it(amount) as doubled_amount,
    calculate_tax(amount, 0.13) as tax
FROM sales

-- 使用 Pandas UDF
SELECT 
    product,
    amount,
    pandas_double(amount) as doubled
FROM sales

-- 在聚合中使用 UDF
SELECT 
    category,
    SUM(double_it(amount)) as total_doubled
FROM sales
GROUP BY category

-- 在条件中使用 UDF
SELECT * FROM sales
WHERE calculate_tax(amount) > 100
```

## 注意事项

1. **内存管理**: 处理大文件时注意 Spark 内存配置
2. **文件路径**: 确保 Excel 文件路径正确且有读取权限
3. **数据类型**: 复杂数据类型可能需要特殊处理
4. **性能优化**: 大数据量时建议使用 `local[*]` 或集群模式
5. **缓存管理**: 
   - 查询结果会自动缓存，导出时不会重复执行查询
   - 缓存在以下情况自动释放：导出完成后、用户取消导出、关闭处理器
   - 处理大数据集时注意内存使用，缓存会占用内存空间
6. **UDF 使用**:
   - Python UDF 性能较低，大数据量建议使用 Pandas UDF
   - Java UDF 需要确保 JAR 文件路径正确且类名完整
   - UDF 名称会自动转换为小写，避免使用特殊字符
   - Pandas UDF 需要正确指定输入输出类型

## 故障排除

### 常见问题

**Q: 出现 "File not found" 错误**
A: 检查文件路径是否正确，确保文件存在且有读取权限。

**Q: 内存不足错误**
A: 增加 Spark 内存配置：
```python
processor = ExcelProcessor()
processor.spark.conf.set("spark.driver.memory", "8g")
```

**Q: 数据类型转换错误**
A: 尝试禁用自动类型推断：
```python
processor.load_excel("file.xlsx", infer_schema=False)
```

**Q: 中文乱码问题**
A: 确保 Excel 文件编码正确，PySpark 通常能自动处理 UTF-8编码。

**Q: 注册 Python UDF 时找不到函数**
A: 确保函数在当前会话中已定义，交互式模式下函数需要在注册前定义。

**Q: Java UDF 注册失败**
A: 检查 JAR 文件路径是否正确，类名是否完整（包括包名）。

**Q: Pandas UDF 类型错误**
A: 确保函数的输入输出类型与注册时指定的类型匹配，使用正确的 Pandas 类型。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
