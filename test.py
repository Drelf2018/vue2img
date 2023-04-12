from vue2img import createApp, word2cloud, radiusMask
from danmakus import ukamnads
from PIL import Image


data = {
    "name": "七海Nana7mi",
    "title": "玩空之要塞：启航！！",
    "time": "01/20 18:59 - 01/20 21:04",
    "d1": "9628",
    "d2": "8306"
}
img = createApp(1000).mount(path=".\Live.vue", data=data).export().canvas
bg = Image.new("L", (850, 395), "black")
wc = word2cloud(ukamnads.sd(434334701), bg)
img.paste(wc, (75, 940), wc.getchannel("A"))
img.show()