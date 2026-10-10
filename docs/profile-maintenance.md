# 主页维护

## 图片

README 的横幅、技术栈图标与统计卡片全部保存在 `assets/` 中，使用相对路径。
新增图片时补全 `alt`，避免依赖访问计数、动态图标或统计图服务。
图标来源、固定版本与 MIT 许可见 `assets/icons/NOTICE.md` 和 `assets/icons/LICENSE`。

## 统计口径与更新

- `PUBLIC REPOS`：GitHub API 返回的公开仓库总数，包含 fork 与本主页仓库。
- `OWN REPOS`：排除 fork 与本主页后的公开仓库数，不代表全部代码均为原创。
- `MAIN LANGS`：上述自建仓库的非空主要语言种类数。
- `LANGUAGE MIX`：按每个自建仓库的主要语言计数，不按代码字节或熟练程度计算。
  超过六种语言时，前五种单独显示，其余合并为 `Other`；SVG 描述保留全部明细。

`Update profile stats` 每天约在北京时间 10:17 运行（GitHub 排队可能延迟），
也可以从 Actions 页面手动运行。仅统计数据变化时提交，避免产生无意义的更新。
API 请求失败会使工作流失败，既有卡片仍然保留。README 使用定期更新的仓库文件，
不需要访客在打开主页时请求第三方统计服务。

## 本地检查

只需要 Python 3.9 或更高版本与标准库，无须安装包：

```sh
python3 scripts/check_profile.py
python3 -m unittest discover -s tests -v
python3 scripts/generate_profile_stats.py --username itsVicOC
```

生成统计卡片需要访问 GitHub API；设置 `GITHUB_TOKEN` 可以提高请求额度。
Pull Request 会自动校验本地图片路径、SVG 外部依赖与语言分布计算。
