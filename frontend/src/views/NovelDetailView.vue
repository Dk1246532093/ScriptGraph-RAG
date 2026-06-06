<template>
  <div class="novel-detail-view">
    <div class="novel-container">
      <!-- 左侧章节列表 -->
      <div class="novel-sidebar">
        <div class="novel-info">
          <div class="novel-cover">{{ novel.title?.[0] }}</div>
          <h3>{{ novel.title }}</h3>
          <p>共 {{ novel.chapterCount }} 章</p>
        </div>
        <el-scrollbar class="chapter-scrollbar">
          <div
            v-for="chapter in chapters"
            :key="chapter.id"
            class="chapter-item"
            :class="{ active: currentChapter?.id === chapter.id }"
            @click="selectChapter(chapter)"
          >
            {{ chapter.title }}
          </div>
        </el-scrollbar>
      </div>

      <!-- 右侧内容区 -->
      <div class="novel-main">
        <div class="novel-actions">
          <el-button type="primary" @click="goToScriptGen">
            <el-icon><Document /></el-icon>生成剧本
          </el-button>
          <el-button @click="goBack">
            <el-icon><ArrowLeft /></el-icon>返回书架
          </el-button>
        </div>

        <div class="chapter-content" v-loading="contentLoading">
          <h2 v-if="currentChapter">{{ currentChapter.title }}</h2>
          <div class="content-text" v-html="formattedContent"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Document, ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getNovelDetail, getChapterContent } from '@/api/novel'

const route = useRoute()
const router = useRouter()
const novelId = route.params.id as string

const novel = ref<any>({})
const chapters = ref<any[]>([])
const currentChapter = ref<any>(null)
const chapterContent = ref('')
const loading = ref(false)
const contentLoading = ref(false)

const formattedContent = computed(() => {
  if (!chapterContent.value) return ''
  // 将换行符转换为 <br>
  return chapterContent.value.replace(/\n/g, '<br>')
})

const fetchNovelDetail = async () => {
  loading.value = true
  try {
    const res = await getNovelDetail(novelId)
    novel.value = res.data
    chapters.value = res.data.chapters || []
    
    // 默认选择第一章
    if (chapters.value.length > 0 && !currentChapter.value) {
      selectChapter(chapters.value[0])
    }
  } catch (error) {
    ElMessage.error('获取小说详情失败')
  } finally {
    loading.value = false
  }
}

const selectChapter = async (chapter: any) => {
  currentChapter.value = chapter
  contentLoading.value = true
  try {
    const res = await getChapterContent(novelId, chapter.id)
    chapterContent.value = res.data.content
  } catch (error) {
    ElMessage.error('获取章节内容失败')
  } finally {
    contentLoading.value = false
  }
}

const goToScriptGen = () => {
  router.push({
    path: '/script-gen',
    query: { novelId }
  })
}

const goBack = () => {
  router.push('/bookshelf')
}

onMounted(() => {
  fetchNovelDetail()
})
</script>

<style scoped>
.novel-detail-view {
  height: calc(100vh - 60px);
}

.novel-container {
  display: flex;
  height: 100%;
}

.novel-sidebar {
  width: 280px;
  background: #f8f9fa;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}

.novel-info {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #e0e0e0;
}

.novel-cover {
  width: 100px;
  height: 130px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  margin: 0 auto 15px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 36px;
  font-weight: bold;
}

.novel-info h3 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 16px;
}

.novel-info p {
  margin: 0;
  color: #999;
  font-size: 13px;
}

.chapter-scrollbar {
  flex: 1;
}

.chapter-item {
  padding: 12px 20px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  color: #555;
  transition: all 0.2s;
}

.chapter-item:hover {
  background: #e9ecef;
}

.chapter-item.active {
  background: #3498db;
  color: #fff;
}

.novel-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.novel-actions {
  padding: 15px 30px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  gap: 10px;
}

.chapter-content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  background: #fff;
}

.chapter-content h2 {
  margin: 0 0 30px 0;
  color: #333;
  font-size: 24px;
  text-align: center;
}

.content-text {
  line-height: 2;
  color: #333;
  font-size: 16px;
  max-width: 800px;
  margin: 0 auto;
}
</style>
