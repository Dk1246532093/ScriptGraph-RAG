<template>
  <div class="app">
    <nav class="navbar">
      <div class="nav-brand">
        <router-link to="/">ScriptGraph-RAG</router-link>
      </div>
      <ul class="nav-links">
        <li><router-link to="/">首页</router-link></li>
        <li><router-link to="/bookshelf">书架</router-link></li>
        <li><router-link to="/knowledge-graph">知识图谱</router-link></li>
        <li><router-link to="/script">剧本生成</router-link></li>
      </ul>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
  // 根组件
</script>

<style>
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
      'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  .app {
    min-height: 100vh;
  }

  .navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 40px;
    height: 60px;
    background-color: #2c3e50;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .nav-brand a {
    color: #fff;
    font-size: 20px;
    font-weight: bold;
    text-decoration: none;
  }

  .nav-links {
    display: flex;
    list-style: none;
    gap: 30px;
  }

  .nav-links a {
    color: #ecf0f1;
    text-decoration: none;
    font-size: 15px;
    padding: 8px 16px;
    border-radius: 4px;
    transition: all 0.3s ease;
  }

  .nav-links a:hover {
    background-color: #34495e;
    color: #fff;
  }

  .nav-links a.router-link-active {
    background-color: #3498db;
    color: #fff;
  }

  .main-content {
    padding: 20px 40px;
  }
</style>