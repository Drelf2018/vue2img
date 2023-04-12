<template>
  <div class="outer">
    <div class="container">
      <h1>{{name}} 直播记录</h1>
      <span class="title">标题：{{title}}</span>
      <span class="time">时间：{{time}}</span>
      <span class="subtitle">基础数据</span>
      <div class="num">
        <span class="data">营收：{{d1}}</span>
        <span class="data">礼物：{{d2}}</span>
      </div>
      <div class="line"></div>
      <span class="subtitle">趋势图标</span>
      <span style="height: 395px"></span>
      <span class="subtitle">弹幕词云</span>
      <span style="height: 395px;margin: 0 0 20px;"></span>
    </div>
  </div>
</template>

<script></script>

<style>
.outer {
  background-color: #ffffffde;
}

.container {
  width: calc(100% - 8em);
  margin: 2em 2em;
  padding: 1em 2em;
  background-color: white;
  border-radius: 1em;
}

h1 {
  font-size: 50px;
  font-weight: Bold;
  margin: 0 0 20px;
}

.title {
  font-size: 32px;
  font-weight: Bold;
  margin: 0 0 5px;
}

.time {
  font-size: 28px;
  font-weight: Regular;
  margin: 0 0 20px;
  color: #1D1D1F;
}

.subtitle {
  font-size: 40px;
  font-weight: Bold;
  margin: 0 0 5px;
}

.data {
  font-size: 35px;
  font-weight: Regular;
  margin: 0 0 5px;
  color: #1D1D1F;
}

.num {
  margin: 0 0 20px;
}

.line {
  background-color: grey;
  height: 50px;
  border-radius: 25px;
  margin: 0 0 20px;
}
</style>