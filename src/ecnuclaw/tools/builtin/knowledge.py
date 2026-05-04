from ecnuclaw.tools.base import Tool, ToolResult

KNOWLEDGE_BASE = [
    {"id": "math-01", "name": "整数加减法", "subject": "数学", "grade": "一年级",
     "description": "掌握10以内和20以内的加减法运算，理解加法和减法的含义。",
     "prerequisites": [], "related": ["数学-比较大小", "数学-认识数字"]},
    {"id": "math-02", "name": "乘法口诀表", "subject": "数学", "grade": "二年级",
     "description": "熟记九九乘法表，能熟练进行一位数乘法运算。",
     "prerequisites": ["整数加减法"], "related": ["数学-除法基础"]},
    {"id": "math-03", "name": "除法基础", "subject": "数学", "grade": "二年级",
     "description": "理解除法的含义，掌握表内除法和有余数的除法。",
     "prerequisites": ["乘法口诀表"], "related": ["数学-分数初步"]},
    {"id": "math-04", "name": "分数初步", "subject": "数学", "grade": "三年级",
     "description": "认识分数，理解分数的含义，会比较简单分数的大小，会简单的分数加减法。",
     "prerequisites": ["除法基础"], "related": ["数学-小数初步"]},
    {"id": "math-05", "name": "小数初步", "subject": "数学", "grade": "三年级",
     "description": "认识小数，理解小数的含义，会比较一位小数的大小，会一位小数的加减法。",
     "prerequisites": ["分数初步"], "related": ["数学-小数乘除法"]},
    {"id": "math-06", "name": "面积与周长", "subject": "数学", "grade": "三年级",
     "description": "认识面积和周长的概念，掌握长方形和正方形面积与周长的计算方法。",
     "prerequisites": ["整数加减法", "乘法口诀表"], "related": ["数学-三角形面积"]},
    {"id": "math-07", "name": "方程初步", "subject": "数学", "grade": "五年级",
     "description": "用字母表示数，理解等式的性质，能解简单的一元一次方程。",
     "prerequisites": ["小数初步", "分数初步"], "related": ["数学-一元一次方程"]},
    {"id": "math-08", "name": "一元一次方程", "subject": "数学", "grade": "六年级",
     "description": "系统学习一元一次方程的解法，能列方程解应用题。",
     "prerequisites": ["方程初步"], "related": ["数学-二元一次方程组"]},
    {"id": "math-09", "name": "比例与百分数", "subject": "数学", "grade": "六年级",
     "description": "理解比例的意义和基本性质，掌握百分数的概念和应用。",
     "prerequisites": ["分数初步", "小数初步"], "related": ["数学-统计与概率"]},
    {"id": "math-10", "name": "统计与概率", "subject": "数学", "grade": "六年级",
     "description": "认识条形统计图、折线统计图和扇形统计图，理解简单概率的概念。",
     "prerequisites": ["比例与百分数"], "related": ["数学-数据分析"]},
    {"id": "cn-01", "name": "拼音与识字", "subject": "语文", "grade": "一年级",
     "description": "掌握汉语拼音的声母、韵母和声调，认识常用汉字300-500个。",
     "prerequisites": [], "related": ["语文-简单阅读"]},
    {"id": "cn-02", "name": "简单阅读", "subject": "语文", "grade": "一年级",
     "description": "能读懂简单的短文，理解主要内容，回答简单问题。",
     "prerequisites": ["拼音与识字"], "related": ["语文-写话训练"]},
    {"id": "cn-03", "name": "写话训练", "subject": "语文", "grade": "二年级",
     "description": "能用几句连贯的话写清楚一件事或一个事物。",
     "prerequisites": ["简单阅读", "拼音与识字"], "related": ["语文-段落写作"]},
    {"id": "cn-04", "name": "段落写作", "subject": "语文", "grade": "三年级",
     "description": "能写一段完整的话，有明确的中心意思，语句通顺。",
     "prerequisites": ["写话训练"], "related": ["语文-记叙文写作"]},
    {"id": "cn-05", "name": "修辞手法", "subject": "语文", "grade": "四年级",
     "description": "学习比喻、拟人、排比、夸张等常见修辞手法，能在写作中运用。",
     "prerequisites": ["段落写作"], "related": ["语文-记叙文写作", "语文-古诗鉴赏"]},
    {"id": "cn-06", "name": "记叙文写作", "subject": "语文", "grade": "四年级",
     "description": "掌握记叙文的六要素，能写400字以上的记叙文，条理清楚。",
     "prerequisites": ["段落写作", "修辞手法"], "related": ["语文-说明文写作"]},
    {"id": "cn-07", "name": "古诗鉴赏", "subject": "语文", "grade": "五年级",
     "description": "学习古诗的意境和表达技巧，能背诵和默写课标要求的小学古诗。",
     "prerequisites": ["修辞手法"], "related": ["语文-文言文初步"]},
    {"id": "cn-08", "name": "说明文写作", "subject": "语文", "grade": "五年级",
     "description": "掌握说明文的基本结构和常用说明方法（举例子、列数字、打比方等）。",
     "prerequisites": ["记叙文写作"], "related": ["语文-议论文基础"]},
    {"id": "cn-09", "name": "文言文初步", "subject": "语文", "grade": "六年级",
     "description": "学习简单文言文的阅读方法，掌握常见文言实词和虚词的基本含义。",
     "prerequisites": ["古诗鉴赏"], "related": ["语文-古文阅读"]},
    {"id": "cn-10", "name": "议论文基础", "subject": "语文", "grade": "六年级",
     "description": "理解议论文的基本结构（提出论点、论证论点、得出结论），能写简单议论文。",
     "prerequisites": ["说明文写作"], "related": ["语文-阅读理解进阶"]},
    {"id": "sci-01", "name": "植物的认识", "subject": "科学", "grade": "一年级",
     "description": "认识常见植物的基本特征，了解植物的生长需要阳光和水。",
     "prerequisites": [], "related": ["科学-动物的认识"]},
    {"id": "sci-02", "name": "动物的认识", "subject": "科学", "grade": "一年级",
     "description": "认识常见动物及其基本特征，了解动物的基本生活习性。",
     "prerequisites": [], "related": ["科学-植物的认识"]},
    {"id": "sci-03", "name": "天气与季节", "subject": "科学", "grade": "二年级",
     "description": "观察和描述天气变化，了解四季的特征和变化规律。",
     "prerequisites": [], "related": ["科学-水的三态"]},
    {"id": "sci-04", "name": "水的三态", "subject": "科学", "grade": "三年级",
     "description": "了解水的固态（冰）、液态（水）、气态（水蒸气）以及三态之间的转化条件。",
     "prerequisites": ["天气与季节"], "related": ["科学-物质的状态"]},
    {"id": "sci-05", "name": "磁铁与磁性", "subject": "科学", "grade": "三年级",
     "description": "认识磁铁的基本性质，了解磁极间的相互作用（同极相斥、异极相吸）。",
     "prerequisites": [], "related": ["科学-电的基础"]},
    {"id": "sci-06", "name": "电的基础", "subject": "科学", "grade": "四年级",
     "description": "认识简单电路，了解电源、导线、用电器的作用，能组装简单电路。",
     "prerequisites": ["磁铁与磁性"], "related": ["科学-电磁现象"]},
    {"id": "sci-07", "name": "地球与太阳系", "subject": "科学", "grade": "四年级",
     "description": "了解地球的形状和大小，认识太阳系的基本构成，理解昼夜交替和四季成因。",
     "prerequisites": ["天气与季节"], "related": ["科学-月相变化"]},
    {"id": "sci-08", "name": "人体与健康", "subject": "科学", "grade": "四年级",
     "description": "了解人体的主要器官和系统，认识保持健康的基本方法。",
     "prerequisites": ["动物的认识"], "related": ["科学-营养与健康"]},
    {"id": "sci-09", "name": "生态系统", "subject": "科学", "grade": "五年级",
     "description": "理解食物链和食物网的概念，认识生态系统中生物之间的相互关系。",
     "prerequisites": ["植物的认识", "动物的认识"], "related": ["科学-环境保护"]},
    {"id": "sci-10", "name": "力与运动", "subject": "科学", "grade": "五年级",
     "description": "认识常见的力（重力、摩擦力、弹力），了解力与运动的关系。",
     "prerequisites": ["磁铁与磁性"], "related": ["科学-简单机械"]},
]


class KnowledgeTool(Tool):
    name = "knowledge"
    description = "K-12 knowledge point retrieval. Search by keyword, subject (数学/语文/科学), and grade level."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search keyword for knowledge point name or description.",
            },
            "subject": {
                "type": "string",
                "description": "Filter by subject: 数学, 语文, or 科学.",
            },
            "grade": {
                "type": "string",
                "description": "Filter by grade level, e.g. 一年级, 二年级.",
            },
        },
        "required": ["query"],
    }

    def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query", "").strip().lower()
        subject = kwargs.get("subject", "").strip()
        grade = kwargs.get("grade", "").strip()

        if not query:
            return ToolResult(success=False, output="", error="No query provided")

        results = []
        for kp in KNOWLEDGE_BASE:
            if subject and kp["subject"] != subject:
                continue
            if grade and kp["grade"] != grade:
                continue

            searchable = f"{kp['name']} {kp['description']} {' '.join(kp.get('related', []))} {' '.join(kp.get('prerequisites', []))}".lower()
            if query in searchable:
                results.append(kp)

        if not results:
            subjects = sorted(set(kp["subject"] for kp in KNOWLEDGE_BASE))
            return ToolResult(
                success=False, output="",
                error=f"No knowledge points found for '{query}'.",
                metadata={"available_subjects": subjects},
            )

        output_parts = []
        for kp in results:
            lines = [
                f"【{kp['name']}】",
                f"学科: {kp['subject']}",
                f"年级: {kp['grade']}",
                f"描述: {kp['description']}",
            ]
            if kp.get("prerequisites"):
                lines.append(f"前置知识: {', '.join(kp['prerequisites'])}")
            if kp.get("related"):
                lines.append(f"相关知识: {', '.join(kp['related'])}")
            output_parts.append("\n".join(lines))

        return ToolResult(
            success=True,
            output="\n\n---\n\n".join(output_parts),
            metadata={"count": len(results), "results": results},
        )
