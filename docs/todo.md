## TODO

以下为后续计划与优化方向:

- **新增站点支持**
  - [刺猬猫](https://www.ciweimao.com/)
  - [纵横中文网](https://www.zongheng.com/)
  - [轻之国度](https://www.lightnovel.fun)
  - [轻小说文库](https://www.wenku8.net/)
    - 需要 `cf_clearance` cookie

- **新增搜索相关站点**
  - 起点中文网 (需实现起点相关 cookies)
  - 哔哩轻小说 (搜索功能还需要 `cf_clearance` cookie, 已实现 `haha`)
  - 神凑轻小说 (搜索功能需要 `cf_clearance` cookie)
  - 名著阅读 (搜索功能需要 `cf_clearance` cookie)
  - 一笔阁 (搜索功能需要 `cf_clearance` cookie)

- **功能与性能优化**
  - 完善广告过滤规则
  - 整理并精简命令行参数
  - 提供图片压缩选项 (例如 `caesium`)
  - 提供可定制的导出模板 (例如 `Jinja2`)
