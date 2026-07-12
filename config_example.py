"""
配置文件示例

此文件展示了如何配置 Spark Excel Processor 的各种参数
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class ExcelFileConfig:
    """单个 Excel 文件的配置"""
    file_path: str
    sheet_name: str = "Sheet1"
    view_name: Optional[str] = None
    header: bool = True
    infer_schema: bool = True
    
    def __post_init__(self):
        """验证配置"""
        if not self.file_path:
            raise ValueError("file_path 不能为空")
        
        # 如果未指定视图名称，使用文件名
        if self.view_name is None:
            self.view_name = Path(self.file_path).stem


@dataclass
class SparkConfig:
    """Spark 会话配置"""
    app_name: str = "SparkExcelProcessor"
    master: str = "local[*]"
    driver_memory: str = "4g"
    executor_memory: str = "4g"
    max_result_size: str = "2g"
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典格式"""
        return {
            "spark.app.name": self.app_name,
            "spark.master": self.master,
            "spark.driver.memory": self.driver_memory,
            "spark.executor.memory": self.executor_memory,
            "spark.driver.maxResultSize": self.max_result_size
        }


@dataclass
class ProcessorConfig:
    """处理器整体配置"""
    spark: SparkConfig
    excel_files: List[ExcelFileConfig]
    output_dir: str = "output"
    log_level: str = "INFO"
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'ProcessorConfig':
        """从字典创建配置"""
        spark_config = SparkConfig(**config_dict.get("spark", {}))
        
        excel_files = []
        for excel_config in config_dict.get("excel_files", []):
            excel_files.append(ExcelFileConfig(**excel_config))
        
        return cls(
            spark=spark_config,
            excel_files=excel_files,
            output_dir=config_dict.get("output_dir", "output"),
            log_level=config_dict.get("log_level", "INFO")
        )


# 预定义的配置模板
CONFIG_TEMPLATES = {
    # 基础配置：适合小数据量
    "basic": {
        "spark": {
            "app_name": "SparkExcelBasic",
            "master": "local[2]",
            "driver_memory": "2g"
        },
        "output_dir": "output",
        "log_level": "INFO"
    },
    
    # 高性能配置：适合大数据量
    "performance": {
        "spark": {
            "app_name": "SparkExcelPerformance",
            "master": "local[*]",
            "driver_memory": "8g",
            "executor_memory": "8g",
            "max_result_size": "4g"
        },
        "output_dir": "output",
        "log_level": "WARN"
    },
    
    # 调试配置：详细日志
    "debug": {
        "spark": {
            "app_name": "SparkExcelDebug",
            "master": "local[1]",
            "driver_memory": "2g"
        },
        "output_dir": "debug_output",
        "log_level": "DEBUG"
    }
}


def get_config(template_name: str = "basic") -> Dict:
    """
    获取预定义的配置模板
    
    Args:
        template_name: 配置模板名称，可选值: basic, performance, debug
        
    Returns:
        配置字典
    """
    if template_name not in CONFIG_TEMPLATES:
        raise ValueError(f"未知的配置模板: {template_name}。可选值: {list(CONFIG_TEMPLATES.keys())}")
    
    return CONFIG_TEMPLATES[template_name].copy()


def create_custom_config(
    app_name: str = "MySparkApp",
    master: str = "local[*]",
    driver_memory: str = "4g",
    output_dir: str = "output",
    log_level: str = "INFO"
) -> Dict:
    """
    创建自定义配置
    
    Args:
        app_name: 应用名称
        master: Spark master URL
        driver_memory: 驱动内存
        output_dir: 输出目录
        log_level: 日志级别
        
    Returns:
        配置字典
    """
    return {
        "spark": {
            "app_name": app_name,
            "master": master,
            "driver_memory": driver_memory
        },
        "output_dir": output_dir,
        "log_level": log_level
    }


# 使用示例
if __name__ == "__main__":
    # 示例1: 使用预定义配置
    config = get_config("performance")
    print("性能配置:", config)
    
    # 示例2: 创建自定义配置
    custom_config = create_custom_config(
        app_name="SalesAnalysis",
        driver_memory="8g",
        output_dir="sales_output"
    )
    print("自定义配置:", custom_config)
    
    # 示例3: 创建完整的处理器配置
    processor_config = ProcessorConfig(
        spark=SparkConfig(
            app_name="FullExample",
            master="local[4]",
            driver_memory="8g"
        ),
        excel_files=[
            ExcelFileConfig("data/sales.xlsx", "Sheet1", "sales"),
            ExcelFileConfig("data/customers.xlsx", "Customers", "customers")
        ],
        output_dir="analysis_output",
        log_level="INFO"
    )
    print("处理器配置:", processor_config)
