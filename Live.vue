<template>
  <div class="outer">
    <div class="container">
      <h1>{{ uName }} 直播记录</h1>
      <p class="title">标题：{{ title }}</p>
      <p class="time">时间：{{ time }}</p>
      <p class="subtitle">基础数据</p>
      <div class="text">
        <span class="data">营收：</span>
        <span class="data">弹幕：</span>
        <span class="data">密度：</span>
      </div>
      <div class="text">
        <span class="data">礼物：</span>
        <span class="data">航海：</span>
        <span class="data">留言：</span>
      </div>
      <div class="text">
        <span class="line1" style="left: 150px;">{{ totalIncome }}</span>
        <span class="line1" style="left: 375px;">{{ danmakusCount }}</span>
        <span class="line1" style="left: 600px;">{{ density }}</span>
      </div>
      <div class="text">
        <span class="line2" style="left: 150px; color: #ffa8b4">{{ gift }}</span>
        <span class="line2" style="left: 375px; color: #84d49b">{{ guard }}</span>
        <span class="line2" style="left: 600px; color: #4ac2f6">{{ superchat }}</span>
      </div>      
      <img class="line" :src="income" />
      <p class="subtitle">弹幕词云</p>
      <img style="margin: 10px 0 2px" :src="dm" />
      <span style="font-size:24px;color: grey;float:right;display: inline;">*数据来源：api.ukamnads.icu</span>
      <img class="nanami" :src="nanami" />
    </div>
  </div>
</template>

<script setup>
</script>

<style>
.container {
  width: calc(100% - 7em);
  margin: 100px 2em 2em;
  padding: 1.5em 1.5em 7px;
  background-color: white;
  border-radius: 1em;
  font-weight: Bold;
}

h1 {
  font-size: 50px;
  margin: 0 0 24px;
}

.title {
  font-size: 32px;
  margin: 0 0 5px;
}

.time {
  font-size: 28px;
  font-weight: Regular;
  margin: 0 0 24px;
  color: #1D1D1F;
}

.subtitle {
  font-size: 40px;
  margin: 0 0 5px;
}

.text {
  font-size: 35px;
  font-weight: Regular;
}

.line1 {
  position: absolute;
  top: 345px;
  background-color: #00000000;
}

.line2 {
  position: absolute;
  top: 388px;
  background-color: #00000000;
}

.data + .data {
  margin: 0 0 5px 120px;
}

.data {
  margin: 0 0 5px;
  color: #1D1D1F;
  display: inline-block;
}

.line {
  height: 50px;
  border-radius: 25px;
  margin: 7px 0 12px;
}

.nanami {
  position: absolute;
  top: 10px;
  left: 700px;
  width: 250px;
}
</style>