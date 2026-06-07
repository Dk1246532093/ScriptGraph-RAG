# 剧本 YAML Schema 设计文档

## 概述

本文档定义了 AI 小说转剧本系统生成的 YAML 格式剧本的数据结构规范。该 Schema 专为影视拍摄场景设计，支持从高层场景描述到具体台词细节的完整剧本信息表达。

---

## Schema 设计原则

### 1. 层次化结构（Hierarchical Structure）

**设计原因**：影视剧本天然具有层次结构，从场景(Scene)到节拍(Beat)再到台词(Line)，这种层级关系与拍摄团队的组织方式一致。

- **场景(Scene)**：对应一个拍摄地点和时间的连续段落
- **节拍(Beat)**：场景内的剧情转折单元，对应导演的拍摄镜头规划
- **台词(Line)**：单个角色的表演单元，包含动作、表情、语言等要素

### 2. 分离关注点（Separation of Concerns）

**设计原因**：将视觉信息（动作、表情）与听觉信息（台词、语气）分离，便于不同部门（摄影、录音、演员）快速定位所需信息。

```yaml
# 视觉信息（演员表演、摄影参考）
expression: "痛苦但坚忍"  # 表情
action: "伏在枣红马背上，背后插着一支长箭"  # 动作

# 听觉信息（录音、配音参考）
voice:
  emotion: "强忍疼痛"  # 情绪基调
  tone: "低沉、喘息"   # 语气特征
  text: "虹妹……别回头，快走……"  # 实际台词
```

### 3. 可追溯性（Traceability）

**设计原因**：AI 生成的内容需要保留来源信息，便于后期审查和修改时了解生成上下文。

- `generated_at`：生成时间戳
- `novel_title` / `novel_id`：源小说信息
- `script_id`：唯一标识，便于版本管理

### 4. 可读性与机器处理平衡

**设计原因**：剧本需要同时满足人类阅读（导演、演员）和机器处理（导入其他系统）的需求。

- 使用 YAML 而非 JSON：更易于人类阅读和手写修改
- 保留结构化字段：便于程序解析和导入专业编剧软件

---

## YAML Schema 定义

### 根级别结构

```yaml
# 剧本元数据
script_id: "uuid-string"           # 唯一标识符，UUID v4
novel_title: "小说名称"             # 源小说标题
novel_id: "novel-uuid"             # 源小说ID
generated_at: "2026-06-07T21:58:23" # ISO 8601 格式生成时间
version: "1.0"                     # Schema 版本

# 剧本内容
scenes: []                         # 场景数组，包含所有场景
```

### Scene（场景）对象

```yaml
scene_id: "scene_1"               # 场景唯一标识（scene_序号）
title: "大漠追杀"                  # 场景标题（简短描述）
location: "回疆大漠"               # 拍摄地点
summary: "李三夫妇为保高昌迷宫地图被吕梁三杰追杀..."  # 场景概述（戏剧作用）
beats: []                         # 节拍数组
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| `scene_id` | string | 是 | 场景唯一标识，格式 `scene_N` |
| `title` | string | 是 | 场景标题，3-10字概括场景内容 |
| `location` | string | 是 | 拍摄地点，用于场地勘景 |
| `summary` | string | 否 | 场景概述，说明戏剧作用和剧情要点 |
| `beats` | array | 是 | 场景内的节拍列表 |

### Beat（节拍）对象

```yaml
beat_id: "beat_1"                 # 节拍唯一标识（beat_序号）
title: "中箭逃亡"                  # 节拍标题
theme: "逃亡、牺牲"                # 主题（如：爱情、冲突、牺牲）
location: "黄沙大漠"               # 具体地点（场景内的具体位置）
atmosphere: "紧张、悲壮"           # 氛围描述（用于灯光、美术参考）
characters: ["白马李三", "上官虹"]  # 出场角色列表
script: []                        # 台词数组
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| `beat_id` | string | 是 | 节拍唯一标识，格式 `beat_N` |
| `title` | string | 是 | 节拍标题，描述该节拍的核心事件 |
| `theme` | string | 否 | 主题标签，用于分析剧本结构 |
| `location` | string | 否 | 场景内的具体位置，用于机位规划 |
| `atmosphere` | string | 否 | 氛围关键词，指导灯光和表演风格 |
| `characters` | array | 否 | 出场角色列表，用于调度规划 |
| `script` | array | 是 | 该节拍的台词列表 |

**设计说明**：
- **theme 字段**：帮助导演理解每个节拍的核心情感，便于把握节奏
- **atmosphere 字段**：为灯光师、美术师提供氛围参考
- **location 子字段**：一个场景可能有多个拍摄位置（如"大漠"场景内的"沙丘"、"岩石后"）

### Line（台词）对象

```yaml
character: "白马李三"              # 角色名
expression: "痛苦但坚忍"           # 表情描述
action: "伏在枣红马背上，背后插着一支长箭，鲜血沿马背滴入黄沙"  # 动作描述
voice:                            # 声音信息对象
  emotion: "强忍疼痛"              # 情绪状态
  tone: "低沉、喘息"               # 语气特征
  text: "虹妹……别回头，快走……"     # 实际台词内容
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| `character` | string | 是 | 说话角色的名称 |
| `expression` | string | 否 | 表情描述，指导演员面部表情 |
| `action` | string | 否 | 动作描述，可以是动作、神态或镜头提示 |
| `voice` | object | 否 | 声音相关信息 |
| `voice.emotion` | string | 否 | 情绪状态（如：愤怒、悲伤、喜悦）|
| `voice.tone` | string | 否 | 语气特征（如：低沉、尖锐、颤抖）|
| `voice.text` | string | 是 | 实际台词文本 |

**设计说明**：

1. **expression vs voice.emotion**：
   - `expression`：外在可见的表情（面部）
   - `voice.emotion`：内在情绪状态，可能影响声音的多个维度
   - 区分原因：演员可能面无表情但声音充满情绪（内敛表演）

2. **action 字段的灵活性**：
   - 可以是演员动作（"拔剑"）
   - 可以是神态描述（"眼中闪过一丝犹豫"）
   - 可以是镜头指示（"特写脸部"）

3. **voice 对象封装**：
   - 将声音相关属性封装，便于声音后期部门提取信息
   - 为未来扩展（如语速、音量）预留空间

---

## 完整示例

```yaml
script_id: "0aa63a0b-d6d5-42ad-9dbe-3b94ba6f0f2f"
novel_title: "白马啸西风"
novel_id: "novel_001"
generated_at: "2026-06-07T21:58:23"
version: "1.0"

scenes:
  - scene_id: "scene_1"
    title: "大漠追杀"
    location: "回疆大漠"
    summary: "李三夫妇为保高昌迷宫地图被吕梁三杰追杀"
    beats:
      - beat_id: "beat_1"
        title: "中箭逃亡"
        theme: "逃亡、牺牲"
        location: "黄沙大漠"
        atmosphere: "紧张、悲壮"
        characters:
          - "白马李三"
          - "上官虹"
          - "李文秀"
        script:
          - character: "白马李三"
            expression: "痛苦但坚忍"
            action: "伏在枣红马背上，背后插着一支长箭，鲜血沿马背滴入黄沙"
            voice:
              emotion: "强忍疼痛"
              tone: "低沉、喘息"
              text: "（内心独白）不能拔箭...一拔就倒下了..."

          - character: "上官虹"
            expression: "焦急、忧心"
            action: "骑马在前，怀中搂着七八岁的李文秀，不停回头张望"
            voice:
              emotion: "担忧"
              tone: "急促"
              text: "大哥！撑住！敌人快追上来了！"

  - scene_id: "scene_2"
    title: "风沙湮灭"
    location: "回疆大漠"
    summary: "李文秀骑马逃亡，追兵不断换马追赶"
    beats:
      - beat_id: "beat_1"
        title: "追与逃"
        theme: "逃亡与追捕"
        location: "回疆大漠，广袤沙地"
        atmosphere: "紧张、压抑、疲惫"
        characters:
          - "李文秀"
          - "霍元龙"
          - "陈达海"
        script:
          - character: "霍元龙"
            expression: "凶狠而专注"
            action: "策马飞奔，目光锁定远方黑点"
            voice:
              emotion: "急切"
              tone: "低沉而有力"
              text: "换马！那白马快撑不住了！"
```

---

## Schema 版本历史

### v1.0（当前版本）
- 基础结构：Scene → Beat → Line 三级嵌套
- 支持字段：角色、表情、动作、情绪、语气、台词
- 元数据：script_id, novel_title, generated_at