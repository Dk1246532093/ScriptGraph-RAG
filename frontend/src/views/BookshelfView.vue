<template>
    <div class="bookshelf-view">
        <div class="page-header">
            <h2>我的书架</h2>
            <el-button type="primary" @click="showUploadDialog = true">
                <el-icon>
                    <Plus />
                </el-icon>上传小说
            </el-button>
        </div>

        <div class="search-bar">
            <el-input v-model="searchQuery" placeholder="搜索小说名称..." clearable :prefix-icon="Search" />
            <el-button type="primary" @click="handleSearch">搜索</el-button>
        </div>

        <div class="book-grid" v-loading="loading">
            <div v-for="book in filteredBooks" :key="book.id" class="book-card" @click="goToDetail(book.id)">
                <div class="book-cover">
                    <span class="book-title">{{ book.title }}</span>
                </div>
                <div class="book-info">
                    <h4>{{ book.title }}</h4>
                    <p>共 {{ book.chapterCount }} 章 · {{ book.status }}</p>
                </div>
            </div>

            <div class="book-card upload-card" @click="showUploadDialog = true">
                <div class="book-cover upload-cover">
                    <el-icon :size="48">
                        <Plus />
                    </el-icon>
                </div>
                <div class="book-info">
                    <h4>添加小说</h4>
                    <p>点击上传新小说</p>
                </div>
            </div>
        </div>

        <!-- 上传对话框 -->
        <el-dialog v-model="showUploadDialog" title="上传小说" width="500px">
            <el-form :model="uploadForm" label-width="80px">
                <el-form-item label="小说标题">
                    <el-input v-model="uploadForm.title" placeholder="请输入小说标题" />
                </el-form-item>
                <el-form-item label="选择文件">
                    <el-upload ref="uploadRef" action="#" :auto-upload="false" :on-change="handleFileChange" :limit="1"
                        accept=".txt">
                        <el-button type="primary">选择 TXT 文件</el-button>
                        <template #tip>
                            <div class="el-upload__tip">
                                只支持 .txt 格式文件
                            </div>
                        </template>
                    </el-upload>
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="showUploadDialog = false">取消</el-button>
                <el-button type="primary" @click="handleUpload" :loading="uploading">
                    上传
                </el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
    import { ref, computed, onMounted } from 'vue'
    import { useRouter } from 'vue-router'
    import { Plus, Search } from '@element-plus/icons-vue'
    import { ElMessage } from 'element-plus'
    import { getNovels, uploadNovel } from '@/api/novel'

    const router = useRouter()
    const loading = ref(false)
    const uploading = ref(false)
    const showUploadDialog = ref(false)
    const searchQuery = ref('')
    const books = ref([])
    const uploadRef = ref()

    const uploadForm = ref({
        title: '',
        file: null as File | null
    })

    const filteredBooks = computed(() => {
        if (!searchQuery.value) return books.value
        return books.value.filter(book =>
            book.title.toLowerCase().includes(searchQuery.value.toLowerCase())
        )
    })

    const fetchBooks = async () => {
        loading.value = true
        try {
            const res = await getNovels()
            books.value = res.data || []
        } catch (error: any) {
            const msg = error?.response?.data?.detail || error?.message || '获取书架失败'
            ElMessage.error(msg)
            console.error('获取书架错误:', error)
        } finally {
            loading.value = false
        }
    }

    const handleFileChange = (file: any) => {
        uploadForm.value.file = file.raw
        // 自动提取文件名作为标题
        if (!uploadForm.value.title && file.name) {
            uploadForm.value.title = file.name.replace('.txt', '')
        }
    }

    const handleUpload = async () => {
        if (!uploadForm.value.title) {
            ElMessage.warning('请输入小说标题')
            return
        }
        if (!uploadForm.value.file) {
            ElMessage.warning('请选择文件')
            return
        }

        uploading.value = true
        try {
            const formData = new FormData()
            formData.append('title', uploadForm.value.title)
            formData.append('file', uploadForm.value.file)

            console.log('DEBUG: FormData title=', uploadForm.value.title)
            console.log('DEBUG: FormData file=', uploadForm.value.file)

            // 检查 formData 内容
            for (let [key, value] of formData.entries()) {
                console.log('DEBUG: formData entry:', key, value)
            }

            await uploadNovel(formData)
            ElMessage.success('上传成功')
            showUploadDialog.value = false
            uploadForm.value = { title: '', file: null }
            uploadRef.value?.clearFiles()
            fetchBooks()
        } catch (error: any) {
            const msg = error?.response?.data?.detail || error?.message || '上传失败'
            ElMessage.error(msg)
            console.error('上传错误:', error)
        } finally {
            uploading.value = false
        }
    }

    const handleSearch = () => {
        // 搜索逻辑已在 computed 中实现
    }

    const goToDetail = (id: string) => {
        router.push(`/novel/${id}`)
    }

    onMounted(() => {
        fetchBooks()
    })
</script>

<style scoped>
    .bookshelf-view {
        padding: 20px 40px;
    }

    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
    }

    .page-header h2 {
        margin: 0;
        color: #333;
    }

    .search-bar {
        display: flex;
        gap: 15px;
        margin-bottom: 30px;
    }

    .search-bar .el-input {
        width: 300px;
    }

    .book-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 25px;
    }

    .book-card {
        background: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        overflow: hidden;
        cursor: pointer;
        transition: all 0.3s;
    }

    .book-card:hover {
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
        transform: translateY(-3px);
    }

    .book-cover {
        height: 220px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        padding: 20px;
    }

    .book-title {
        font-size: 18px;
        text-align: center;
        word-break: break-all;
    }

    .upload-cover {
        background: #f5f5f5;
        color: #999;
    }

    .book-info {
        padding: 15px;
    }

    .book-info h4 {
        margin: 0 0 8px 0;
        color: #333;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .book-info p {
        margin: 0;
        color: #999;
        font-size: 13px;
    }

    .upload-card:hover .upload-cover {
        color: #3498db;
    }
</style>