"""
Spark Excel Processor - 使用 PySpark SQL 处理 Excel 文件

支持功能：
- 读取单个或多个 Excel 文件
- 指定每个文件的 sheet_name
- 创建临时视图供 Spark SQL 查询
- 支持链式查询和数据分析
- 支持查询结果预览和导出
- 支持注册自定义 UDF（Python 函数和 Java JAR）
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union, Any, Callable
from enum import Enum

import pandas as pd
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, DataType


class UDFType(Enum):
    """UDF 类型枚举"""
    PYTHON = "python"
    JAVA = "java"


class ExcelProcessor:
    """
    PySpark Excel 处理器
    支持读取 Excel 文件并创建临时视图，使用 Spark SQL 进行数据处理
    """
    
    def __init__(self, app_name: str = "SparkExcelProcessor", master: str = "local[*]"):
        """
        初始化 Spark 会话
        
        Args:
            app_name: Spark 应用名称
            master: Spark master URL
        """
        self.spark = SparkSession.builder \
            .appName(app_name) \
            .master(master) \
            .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
            .getOrCreate()
        
        # 存储已加载的 DataFrame 和视图名称
        self._loaded_views: Dict[str, DataFrame] = {}
        self._cached_result: Optional[DataFrame] = None
        self._cached_sql: Optional[str] = None
        self._registered_udfs: Dict[str, Dict[str, Any]] = {}
        
        print(f"Spark Excel Processor 已初始化")
        print(f"Spark版本: {self.spark.version}")
        print(f"应用名称: {app_name}")
    
    def load_excel(
        self,
        file_path: str,
        sheet_name: Union[str, int] = "Sheet1",
        view_name: Optional[str] = None,
        header: bool = True,
        infer_schema: bool = True
    ) -> DataFrame:
        """
        加载单个 Excel 文件并创建临时视图
        
        Args:
            file_path: Excel 文件路径
            sheet_name: 工作表名称（字符串）或索引（整数，从0开始），默认为 "Sheet1"
            view_name: 临时视图名称，默认为文件名（不含扩展名）
            header: 是否将第一行作为表头
            infer_schema: 是否自动推断数据类型
            
        Returns:
            Spark DataFrame
        """
        # 验证文件存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 如果未指定视图名称，使用文件名（不含扩展名）
        if view_name is None:
            view_name = Path(file_path).stem
        
        # 清理视图名称，使其符合 SQL 标识符规范
        view_name = self._sanitize_view_name(view_name)
        
        # 解析 sheet_name（支持名称或索引）
        actual_sheet_name = self._resolve_sheet_name(file_path, sheet_name)
        
        print(f"正在加载 Excel 文件: {file_path}")
        print(f"工作表: {actual_sheet_name}")
        print(f"视图名称: {view_name}")
        
        # 使用 pandas 读取 Excel，然后转换为 Spark DataFrame
        try:
            pandas_df = pd.read_excel(
                file_path,
                sheet_name=actual_sheet_name,
                header=0 if header else None
            )
            
            # 如果没有表头，创建默认列名
            if not header:
                pandas_df.columns = [f"col_{i}" for i in range(len(pandas_df.columns))]
            
            # 转换为 Spark DataFrame
            spark_df = self.spark.createDataFrame(pandas_df)
            
            # 创建临时视图
            spark_df.createOrReplaceTempView(view_name)
            
            # 存储引用
            self._loaded_views[view_name] = spark_df
            
            print(f"成功创建临时视图: {view_name}")
            print(f"数据形状: {spark_df.count()} 行, {len(spark_df.columns)} 列")
            print(f"列名: {spark_df.columns}")
            
            return spark_df
            
        except Exception as e:
            print(f"加载 Excel 文件失败: {e}")
            raise
    
    def load_multiple_excels(
        self,
        excel_configs: List[Dict[str, Any]]
    ) -> Dict[str, DataFrame]:
        """
        加载多个 Excel 文件并创建临时视图
        
        Args:
            excel_configs: Excel 配置列表，每个配置是一个字典，包含：
                - file_path: Excel 文件路径
                - sheet_name: 工作表名称（可选，默认为 "Sheet1"）
                - view_name: 视图名称（可选，默认为文件名）
                
        Returns:
            字典，键为视图名称，值为 DataFrame
        """
        results = {}
        
        for i, config in enumerate(excel_configs, 1):
            print(f"\n处理第 {i}/{len(excel_configs)} 个文件")
            
            file_path = config.get("file_path")
            sheet_name = config.get("sheet_name", "Sheet1")
            view_name = config.get("view_name")
            
            if not file_path:
                print(f"警告: 第 {i} 个配置缺少 file_path，跳过")
                continue
            
            try:
                df = self.load_excel(file_path, sheet_name, view_name)
                view_name = view_name or Path(file_path).stem
                results[self._sanitize_view_name(view_name)] = df
            except Exception as e:
                print(f"错误: 加载文件 {file_path} 失败: {e}")
                continue
        
        print(f"\n成功加载 {len(results)} 个 Excel 文件")
        return results
    
    def query(self, sql: str) -> DataFrame:
        """
        执行 Spark SQL 查询
        
        Args:
            sql: SQL 查询语句
            
        Returns:
            查询结果 DataFrame
        """
        print(f"执行 SQL 查询:")
        print(f"  {sql}")
        
        try:
            result = self.spark.sql(sql)
            return result
        except Exception as e:
            print(f"SQL 查询失败: {e}")
            raise
    
    def show(self, sql: str, num_rows: int = 20, truncate: bool = True) -> None:
        """
        执行 SQL 查询并显示结果
        
        Args:
            sql: SQL 查询语句
            num_rows: 显示的行数
            truncate: 是否截断长字符串
        """
        result = self.query(sql)
        result.show(num_rows, truncate)
    
    def get_view_names(self) -> List[str]:
        """获取所有已创建的视图名称"""
        return list(self._loaded_views.keys())
    
    def get_dataframe(self, view_name: str) -> Optional[DataFrame]:
        """获取指定视图的 DataFrame"""
        return self._loaded_views.get(view_name)
    
    def drop_view(self, view_name: str) -> bool:
        """
        删除指定的临时视图
        
        Args:
            view_name: 视图名称
            
        Returns:
            是否删除成功
        """
        # 清理视图名称
        view_name = self._sanitize_view_name(view_name)
        
        if view_name not in self._loaded_views:
            print(f"视图 '{view_name}' 不存在")
            return False
        
        try:
            # 从 Spark 中注销视图
            self.spark.catalog.dropTempView(view_name)
            
            # 从缓存中移除
            df = self._loaded_views.pop(view_name)
            
            # 释放 DataFrame 缓存（如果有）
            try:
                df.unpersist()
            except Exception:
                pass
            
            print(f"✓ 已删除视图: {view_name}")
            return True
        except Exception as e:
            print(f"删除视图失败: {e}")
            return False
    
    def drop_all_views(self) -> int:
        """
        删除所有临时视图
        
        Returns:
            成功删除的视图数量
        """
        view_names = list(self._loaded_views.keys())
        dropped_count = 0
        
        for view_name in view_names:
            if self.drop_view(view_name):
                dropped_count += 1
        
        print(f"\n共删除 {dropped_count}/{len(view_names)} 个视图")
        return dropped_count
    
    def describe_view(self, view_name: str) -> None:
        """显示视图的结构信息"""
        if view_name not in self._loaded_views:
            print(f"视图 {view_name} 不存在")
            return
        
        df = self._loaded_views[view_name]
        print(f"\n视图 '{view_name}' 的结构:")
        df.printSchema()
        
        print(f"\n统计信息:")
        df.describe().show()
    
    def preview_query(self, sql: str, preview_rows: int = 20, use_cache: bool = True) -> tuple:
        """
        执行 SQL 查询并预览结果
        
        Args:
            sql: SQL 查询语句
            preview_rows: 预览行数（当结果集过大时）
            use_cache: 是否缓存结果集（用于后续导出）
            
        Returns:
            tuple: (DataFrame, total_count, is_truncated)
        """
        # 释放之前的缓存（如果有）
        self._unpersist_cache()
        
        result = self.query(sql)
        
        # 缓存结果集以提高后续导出性能
        if use_cache:
            result = result.cache()
            self._cached_result = result
            self._cached_sql = sql
        
        total_count = result.count()
        is_truncated = total_count > preview_rows
        
        print(f"\n查询结果预览:")
        print(f"总行数: {total_count}")
        if is_truncated:
            print(f"显示前 {preview_rows} 行（结果集较大）")
        else:
            print(f"显示全部 {total_count} 行")
        print("-" * 50)
        
        result.show(preview_rows, truncate=False)
        
        return result, total_count, is_truncated
    
    def _unpersist_cache(self) -> None:
        """释放缓存的 DataFrame"""
        if self._cached_result is not None:
            try:
                self._cached_result.unpersist()
                self._cached_result = None
                self._cached_sql = None
            except Exception:
                # 忽略释放失败的情况
                pass
    
    def export_to_excel(
        self,
        df: DataFrame,
        output_path: str,
        sheet_name: str = "Sheet1",
        index: bool = False
    ) -> str:
        """
        将 DataFrame 导出到 Excel 文件
        
        Args:
            df: Spark DataFrame
            output_path: 输出文件路径
            sheet_name: 工作表名称
            index: 是否包含索引
            
        Returns:
            实际导出的文件路径
        """
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 转换为 Pandas DataFrame 并导出
        pandas_df = df.toPandas()
        pandas_df.to_excel(output_path, sheet_name=sheet_name, index=index)
        
        print(f"\n✓ 导出成功!")
        print(f"文件路径: {output_path}")
        print(f"工作表: {sheet_name}")
        print(f"行数: {len(pandas_df)}")
        print(f"列数: {len(pandas_df.columns)}")
        
        return output_path
    
    def query_and_export(
        self,
        sql: str,
        source_file_path: str,
        preview_rows: int = 20
    ) -> Optional[str]:
        """
        执行查询、预览并交互式导出
        
        Args:
            sql: SQL 查询语句
            source_file_path: 源 Excel 文件路径（用于确定默认导出目录）
            preview_rows: 预览行数
            
        Returns:
            导出的文件路径，如果未导出则返回 None
        """
        # 执行查询并预览（会自动缓存结果）
        result_df, total_count, is_truncated = self.preview_query(sql, preview_rows, use_cache=True)
        
        # 询问是否导出
        print("\n" + "=" * 50)
        while True:
            export_choice = input("是否需要导出结果到 Excel? (y/n): ").strip().lower()
            if export_choice in ['y', 'yes', '是', 'Y']:
                break
            elif export_choice in ['n', 'no', '否', 'N']:
                print("已跳过导出")
                # 释放缓存
                self._unpersist_cache()
                return None
            else:
                print("请输入 y 或 n")
        
        # 获取导出路径
        source_dir = os.path.dirname(os.path.abspath(source_file_path))
        default_filename = f"ret_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        default_path = os.path.join(source_dir, default_filename)
        
        print(f"\n默认导出路径: {default_path}")
        print("（直接回车使用默认路径，或输入自定义路径）")
        
        custom_path = input("导出路径: ").strip()
        
        if custom_path:
            # 用户提供了自定义路径
            if os.path.isdir(custom_path):
                # 如果输入的是目录，使用默认文件名
                output_path = os.path.join(custom_path, default_filename)
            else:
                output_path = custom_path
                # 确保有 .xlsx 扩展名
                if not output_path.endswith('.xlsx'):
                    output_path += '.xlsx'
        else:
            # 使用默认路径
            output_path = default_path
        
        try:
            # 导出文件
            return self.export_to_excel(result_df, output_path)
        finally:
            # 无论导出成功或失败，都释放缓存
            self._unpersist_cache()
    
    def _resolve_sheet_name(self, file_path: str, sheet_name: Union[str, int]) -> str:
        """
        解析 sheet_name 参数，支持名称或索引
        
        Args:
            file_path: Excel 文件路径
            sheet_name: 工作表名称（字符串）或索引（整数）
            
        Returns:
            实际的工作表名称
        """
        # 如果是整数，通过索引获取 sheet 名称
        if isinstance(sheet_name, int):
            try:
                # 获取 Excel 文件的所有 sheet 名称
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names
                
                if sheet_name < 0 or sheet_name >= len(sheet_names):
                    raise ValueError(
                        f"Sheet 索引 {sheet_name} 超出范围。"
                        f"该文件共有 {len(sheet_names)} 个工作表（索引 0-{len(sheet_names)-1}）"
                    )
                
                actual_name = sheet_names[sheet_name]
                print(f"通过索引 {sheet_name} 获取工作表: {actual_name}")
                return actual_name
            except Exception as e:
                if isinstance(e, ValueError):
                    raise
                raise ValueError(f"无法读取 Excel 文件的 sheet 列表: {e}")
        
        # 如果是字符串，直接返回
        return sheet_name
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """
        获取 Excel 文件的所有工作表名称
        
        Args:
            file_path: Excel 文件路径
            
        Returns:
            工作表名称列表
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        try:
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception as e:
            raise ValueError(f"无法读取 Excel 文件的 sheet 列表: {e}")
    
    def _sanitize_view_name(self, name: str) -> str:
        """
        清理视图名称，使其符合 SQL 标识符规范
        
        Args:
            name: 原始名称
            
        Returns:
            清理后的名称
        """
        # 移除或替换非法字符
        import re
        # 只保留字母、数字和下划线
        sanitized = re.sub(r'[^\w]', '_', name)
        # 确保以字母或下划线开头
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        return sanitized.lower()
    
    def register_python_udf(
        self,
        name: str,
        func: Callable,
        return_type: Union[str, DataType],
        is_pandas_udf: bool = False
    ) -> str:
        """
        注册 Python 函数为 UDF
        
        Args:
            name: UDF 名称（在 SQL 中使用的函数名）
            func: Python 函数
            return_type: 返回类型（如 "string", "integer", "double" 或 Spark DataType）
            is_pandas_udf: 是否为 Pandas UDF（向量化 UDF，性能更高）
            
        Returns:
            注册的 UDF 名称
            
        示例:
            def double_it(x):
                return x * 2
            
            processor.register_python_udf("double_it", double_it, "integer")
            processor.show("SELECT double_it(amount) FROM sales")
        """
        udf_name = self._sanitize_view_name(name)
        
        try:
            if isinstance(return_type, str):
                from pyspark.sql.types import _parse_datatype_string
                spark_return_type = _parse_datatype_string(return_type)
            else:
                spark_return_type = return_type
            
            if is_pandas_udf:
                from pyspark.sql.functions import pandas_udf
                registered_func = pandas_udf(func, spark_return_type)
                self.spark.udf.register(udf_name, registered_func)
            else:
                from pyspark.sql.functions import udf as spark_udf
                registered_func = spark_udf(func, spark_return_type)
                self.spark.udf.register(udf_name, registered_func)
            
            self._registered_udfs[udf_name] = {
                "type": UDFType.PYTHON,
                "function": func,
                "return_type": str(return_type),
                "is_pandas_udf": is_pandas_udf
            }
            
            print(f"✓ 已注册 Python UDF: {udf_name}")
            print(f"  返回类型: {return_type}")
            print(f"  Pandas UDF: {is_pandas_udf}")
            
            return udf_name
            
        except Exception as e:
            print(f"注册 Python UDF 失败: {e}")
            raise
    
    def register_java_udf(
        self,
        name: str,
        java_class: str,
        jar_path: Optional[str] = None,
        return_type: Optional[Union[str, DataType]] = None
    ) -> str:
        """
        注册 Java JAR 中的 UDF
        
        Args:
            name: UDF 名称（在 SQL 中使用的函数名）
            java_class: Java 类的完整限定名（如 "com.example.MyUDF"）
            jar_path: JAR 文件路径（可选，如果已添加到 classpath 则不需要）
            return_type: 返回类型（可选，默认为 StringType）
            
        Returns:
            注册的 UDF 名称
            
        示例:
            processor.register_java_udf(
                "my_java_udf",
                "com.example.MyUDF",
                "/path/to/udf.jar",
                "string"
            )
            processor.show("SELECT my_java_udf(name) FROM sales")
        """
        udf_name = self._sanitize_view_name(name)
        
        try:
            if jar_path:
                if not os.path.exists(jar_path):
                    raise FileNotFoundError(f"JAR 文件不存在: {jar_path}")
                self.spark.sparkContext.addJar(jar_path)
                print(f"  已添加 JAR: {jar_path}")
            
            if return_type is not None:
                if isinstance(return_type, str):
                    from pyspark.sql.types import _parse_datatype_string
                    spark_return_type = _parse_datatype_string(return_type)
                else:
                    spark_return_type = return_type
            else:
                from pyspark.sql.types import StringType
                spark_return_type = StringType()
            
            self.spark.udf.registerJavaFunction(udf_name, java_class, spark_return_type)
            
            self._registered_udfs[udf_name] = {
                "type": UDFType.JAVA,
                "java_class": java_class,
                "jar_path": jar_path,
                "return_type": str(spark_return_type)
            }
            
            print(f"✓ 已注册 Java UDF: {udf_name}")
            print(f"  Java 类: {java_class}")
            if jar_path:
                print(f"  JAR 路径: {jar_path}")
            print(f"  返回类型: {spark_return_type}")
            
            return udf_name
            
        except Exception as e:
            print(f"注册 Java UDF 失败: {e}")
            raise
    
    def list_udfs(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有已注册的自定义 UDF
        
        Returns:
            UDF 字典，键为 UDF 名称，值为 UDF 信息
        """
        return self._registered_udfs.copy()
    
    def print_udfs(self) -> None:
        """打印所有已注册的 UDF 信息"""
        if not self._registered_udfs:
            print("没有已注册的自定义 UDF")
            return
        
        print("\n已注册的自定义 UDF:")
        print("-" * 60)
        
        for name, info in self._registered_udfs.items():
            udf_type = info["type"]
            print(f"\n  名称: {name}")
            print(f"  类型: {udf_type.value}")
            
            if udf_type == UDFType.PYTHON:
                print(f"  函数: {info['function'].__name__}")
                print(f"  Pandas UDF: {info['is_pandas_udf']}")
            else:
                print(f"  Java 类: {info['java_class']}")
                if info.get('jar_path'):
                    print(f"  JAR 路径: {info['jar_path']}")
            
            print(f"  返回类型: {info['return_type']}")
        
        print("-" * 60)
        print(f"共 {len(self._registered_udfs)} 个 UDF")
    
    def unregister_udf(self, name: str) -> bool:
        """
        注销指定的 UDF
        
        Args:
            name: UDF 名称
            
        Returns:
            是否注销成功
        """
        udf_name = self._sanitize_view_name(name)
        
        if udf_name not in self._registered_udfs:
            print(f"UDF '{udf_name}' 不存在")
            return False
        
        try:
            self.spark.udf.unregister(udf_name)
            del self._registered_udfs[udf_name]
            
            print(f"✓ 已注销 UDF: {udf_name}")
            return True
            
        except Exception as e:
            print(f"注销 UDF 失败: {e}")
            return False
    
    def unregister_all_udfs(self) -> int:
        """
        注销所有自定义 UDF
        
        Returns:
            成功注销的 UDF 数量
        """
        udf_names = list(self._registered_udfs.keys())
        unregistered_count = 0
        
        for udf_name in udf_names:
            if self.unregister_udf(udf_name):
                unregistered_count += 1
        
        print(f"\n共注销 {unregistered_count}/{len(udf_names)} 个 UDF")
        return unregistered_count
    
    def close(self) -> None:
        """关闭 Spark 会话"""
        # 释放缓存
        self._unpersist_cache()
        
        if self.spark:
            self.spark.stop()
            print("Spark 会话已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """示例用法"""
    # 示例Excel文件路径（需要替换为实际路径）
    excel_files = [
        {
            "file_path": "data/sales.xlsx",
            "sheet_name": "Sheet1",
            "view_name": "sales"
        },
        {
            "file_path": "data/customers.xlsx", 
            "sheet_name": "Customers",
            "view_name": "customers"
        }
    ]
    
    # 使用上下文管理器
    with ExcelProcessor() as processor:
        # 加载多个 Excel 文件
        processor.load_multiple_excels(excel_files)
        
        # 查看所有视图
        print(f"\n已创建的视图: {processor.get_view_names()}")
        
        # 示例 SQL 查询
        print("\n=== 示例查询 ===")
        
        # 查询销售数据
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
        
        # 多表关联查询（如果有 customers 视图）
        if "customers" in processor.get_view_names():
            processor.show("""
                SELECT 
                    c.customer_name,
                    s.product,
                    s.amount,
                    s.sale_date
                FROM sales s
                JOIN customers c ON s.customer_id = c.customer_id
                ORDER BY s.amount DESC
                LIMIT 20
            """)


if __name__ == "__main__":
    main()
