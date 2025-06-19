# API 总览

主要模块包含:

* [`core`](core/README.md): 核心调度层, 定义并导出抓取 (Fetcher)、解析 (Parser)、导出 (Exporter) 与下载 (Downloader) 四个协议, 并通过工厂函数动态实例化各站点实现。

* [`models`](models.md): 全局数据模型与类型别名定义, 包含章节、配置、枚举等结构化类型。

* [`utils`](utils.md): 通用工具函数集合, 涵盖文件读写、JSON 操作、时间计算、网络下载等辅助功能。
