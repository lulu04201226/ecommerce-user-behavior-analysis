# 数据接入说明

本公开仓库不包含完整原始数据。原因是当前数据文件缺少可核验的公开来源、许可证和生成说明。

## 所需字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `new_user` | 0/1 | 新老用户访问标记 |
| `age` | number | 年龄 |
| `sex` | string | 性别 |
| `market` | string | 市场编码 |
| `device` | string | 访问设备 |
| `operative_system` | string | 操作系统 |
| `source` | string | 来源渠道 |
| `total_pages_visited` | number | 访问页数 |
| `home_page` | 0/1 | 首页到达 |
| `listing_page` | 0/1 | 列表页到达 |
| `product_page` | 0/1 | 商品页到达 |
| `payment_page` | 0/1 | 支付页到达 |
| `confirmation_page` | 0/1 | 确认页到达 |

## 接入方式

1. 将有合法使用权限的数据保存为 `data/raw/user_behavior.csv`。
2. 保证字段名称与上表一致，或在数据准备脚本中完成映射。
3. 使用 UTF-8 编码保存 CSV。
4. 运行 `python src/01_prepare_data.py`。

分析粒度为访问记录，不能将记录数表述为去重用户数。

