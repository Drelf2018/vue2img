# vue2img

将 vue 文件编译为图片

### 使用

先切换目录到 ./example 下，运行 `live.py` 就可以利用同目录下 `Live.vue` 模板生成一张图片并展示。

```python
# uid 可改 数据来源 danmakus.com
App = LiveTemplate(path="Live.vue", uid=434334701)
# 除了 show() 还可以 export() 详见源码 ./vue2img/app.py
app = createApp(App).mount().show()
```