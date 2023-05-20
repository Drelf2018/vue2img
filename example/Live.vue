<template>
  <div class="outer">
    <div class="container">
      <h1>{{ uName }} 直播记录</h1>
      <p class="title">标题：{{ title }}</p>
      <p class="time">时间：{{ time }}</p>
      <p class="subtitle">基础数据</p>
      <div class="text">
        <span>
          营收：
          <span>{{ income }}</span>
        </span>
        <span>
          弹幕：
          <span>{{ danmakusCount }}</span>
        </span>
        <span>
          密度：
          <span>{{ density }}</span>
        </span>
        <span>
          礼物：
          <span style="color: #ffa8b4">{{ gift }}</span>
        </span>
        <span>
          航海：
          <span style="color: #84d49b">{{ guard }}</span>
        </span>
        <span>
          留言：
          <span style="color: #4ac2f6">{{ superchat }}</span>
        </span>
      </div>  
      <img class="line" :src="incomeLine" />
      <p class="subtitle">弹幕词云</p>
      <img style="margin: 10px 0 12px" :src="dm" />
      <span class="source">*数据来源：api.ukamnads.icu</span>
      <img v-if="nanami" class="nanami" :src="nanami" />
      <img v-else class="face" :src="face" />
    </div>
  </div>
</template>

<script setup>
</script>

<style>
.outer {
  background-color: #F6F6F6;
  /* font-family: "resource/font/HarmonyOS_Sans_SC_Bold.ttf"; */
}

.container {
  /* margin: 80px 2em 2em; */
  margin: 2em;
  padding: 1.5em 1.5em 17px;
  background-color: white;
  border-radius: 1em;
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
  /* font-family: "resource/font/HarmonyOS_Sans_SC_Regular.ttf"; */
  margin: 0 0 24px;
  color: #1D1D1F;
}

.subtitle {
  font-size: 40px;
  margin: 0 0 5px;
  color: #1D1D1F;
}

.text {
  font-size: 35px;
  color: #1D1D1F;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  /* font-family: "resource/font/HarmonyOS_Sans_SC_Regular.ttf"; */
}

.line {
  height: 50px;
  border-radius: 25px;
  margin: 7px 0 12px;
}

.source {
  /* font-family: "resource/font/HarmonyOS_Sans_SC_Regular.ttf"; */
  font-size:24px;
  color: grey;
  float:right;
  display: inline;
}

.nanami {
  position: absolute;
  top: 10px;
  left: calc(990px - 100%);
  height: 400px;
}

.face {
  position: absolute;
  /* top: calc(80px + 1em); */
  top: 3em;
  left: calc(100% + 4em - 150px);
  width: 150px;
}
</style>