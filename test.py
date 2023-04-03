from vue2img import createApp

data = {
    "img1": "https://yun.nana7mi.link/7mi.webp",
    "img2": "https://yun.nana7mi.link/afternoon.webp",
    "text": "测试用文本"
}
createApp(1000).mount(path=".\Test.vue", data=data).show()