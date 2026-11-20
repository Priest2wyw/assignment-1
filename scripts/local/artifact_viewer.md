# JSON 轨迹查看器

在仓库根目录启动（只使用 Python 标准库）：

```bash
python scripts/local/artifact_viewer.py --host 0.0.0.0 --port 8105
```

浏览器打开 `http://服务器IP:8105`。默认读取仓库的 `artifacts/`，包括
子目录内的 JSON。文件保留在服务器上，查看器不会改写它们。

- 文件下拉框：选择运行轨迹或其他 JSON 文件。
- 压缩表格：展示全部压缩记录、前后 token 估算、缩减比例和摘要预览。
- 文件字段：查看完整文件、任意顶层字段或数组中的单个元素。
- 压缩详情：选择单次压缩及其任意字段，查看完整原始内容。
- 重新读取文件：刷新当前文件；刷新列表：发现新文件。
- 复制内容：复制当前格式化的字段值。

缩减比例为 `1 - after / before`，概览展示有效记录的算术平均值，
不代表 API 总 token 节省比例。实际总成本还需计入摘要请求。
Agent 当前在运行退出时保存轨迹，因此页面可能暂时显示上一次运行。

服务没有登录认证，仅应在可信网络使用；它只提供指定 artifacts 根目录
内的 JSON 文件，不提供仓库的 `.env` 等文件。可用 `--root` 指定其他目录。

运行补充测试：

```bash
.venv/bin/python -m pytest -q scripts/local/test_artifact_viewer.py
```
