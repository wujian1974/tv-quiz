window.QUIZ_DATA = {
  "version": 2,
  "generated_at": "2026-11-16 20:11:58",
  "source": "错题库卡片 + 教材补充题",
  "rules": {
    "choice": "全部题目为四选一，电视端用方向键移焦点、确定键作答",
    "shuffle": "每次出题打乱选项顺序并重算正确答案位置",
    "no_image": "绝不使用 archive/ 原卷照片：上面有孩子作答和老师红笔勾叉，等于泄答案",
    "audit": "每题 opt_from 记录干扰项来源；open_ended=true 的题答案是参考例文，非唯一解",
    "pick": "抽题按间隔重复：出错多的、久没见的优先，不按「待重做」筛（本库几乎全是重做过）",
    "textbook": "补充题出自 ima 知识库五年级上册教材，按 config.json 的 textbook_units 限定已学范围；语文1-4单元、数学1-4单元、英语Unit1-3"
  },
  "stats": {
    "cards_total": 28,
    "questions": 97,
    "original": 3,
    "converted": 22,
    "math": 35,
    "chinese": 42,
    "english": 20,
    "card_questions": 25,
    "textbook": 72,
    "excluded": 3,
    "textbook_skipped": 0
  },
  "questions": [
    {
      "id": "20261030-math-001",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "计算 9.3-1.58-6.6：第一步 9.3-1.58 应该等于多少？",
      "options": [
        "7.72",
        "7.82",
        "7.62",
        "8.72"
      ],
      "answer_index": 0,
      "explain": "9.3-1.58=7.72，再算 7.72-6.6=1.12。孩子写成 7.82，最后得数 1.12 是碰巧对上的，过程其实错了。",
      "opt_from": "7.82=孩子当时的错答；7.62、8.72 是退位减法常见的两种算错",
      "tags": [
        "小数减法",
        "退位减法",
        "连减运算"
      ],
      "source": "数学单元卷《小数的意义和加减法》三、计算下面各题（第1页第2小题）"
    },
    {
      "id": "20261030-math-002",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "计算：4+(6.7-2.81)-1.9，得数是多少？",
      "options": [
        "5.99",
        "65.99",
        "7.89",
        "1.12"
      ],
      "answer_index": 0,
      "explain": "6.7-2.81=3.89，4+3.89-1.9=7.89-1.9=5.99。孩子最后写成 65.99，多写了一个 6。",
      "opt_from": "65.99=孩子错答；7.89=同题中间步骤；1.12=同单元另一道错题的得数",
      "tags": [
        "小数加减混合运算",
        "小数点对位"
      ],
      "source": "数学单元卷《小数的意义和加减法》三、计算下面各题（第1页第3小题）"
    },
    {
      "id": "20261030-math-003",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "简算 1.9+19.9+199.9+1999.9：把它们凑成 2+20+200+2000 后，这四个数相加得多少？",
      "options": [
        "2222",
        "22222",
        "2220",
        "2221"
      ],
      "answer_index": 0,
      "explain": "2+20+200+2000=2222，再减去多补的 0.1×4=0.4，得 2221.6。孩子把 2222 抄成了 22222。",
      "opt_from": "22222=孩子抄错的数；2220、2221 是少算一位或多减的常见错",
      "tags": [
        "小数凑整简算"
      ],
      "source": "数学单元卷《小数的意义和加减法》四、简算（第1页第1小题）"
    },
    {
      "id": "20261030-math-004",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "计数器上的数是 21.444。千分位上的 4 表示 4 个多少？（本单元要求写小数形式）",
      "options": [
        "0.001",
        "0.01",
        "0.1",
        "0.0001"
      ],
      "answer_index": 0,
      "explain": "千分之一写成小数是 0.001，百分之一是 0.01，十分之一是 0.1。孩子三个空都写了中文读法，卷面要求填小数形式。",
      "opt_from": "0.01、0.1 是同题另外两空的真实答案；0.0001 是多移一位的常见错",
      "tags": [
        "小数的数位",
        "计数单位"
      ],
      "source": "数学单元卷《小数的意义和加减法》五、填空（第2页第2题）"
    },
    {
      "id": "20261030-math-005",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "数轴 0 到 4，每 1 大格平均分成 10 小格。0.8 应该标在哪里？",
      "options": [
        "0 和 1 之间的第 8 小格",
        "0 和 1 之间的第 3 小格",
        "3 和 4 之间的第 9 小格",
        "1 和 2 之间的第 8 小格"
      ],
      "answer_index": 0,
      "explain": "0.8 在 0 和 1 之间第 8 小格，3.9 在 3 和 4 之间第 9 小格。孩子 A=1.8、B=3.2 都写对了，扣分是漏了在数轴上标点这个要求。",
      "opt_from": "第 3 项取自同题另一个要标的位置，其余为相邻整数区间的常见混淆",
      "tags": [
        "小数的数轴表示"
      ],
      "source": "数学单元卷《小数的意义和加减法》五、填空（第2页第3题）",
      "figure_note": "原题配数轴图；卡片里有重画的干净 SVG，电视端可选用，切勿用原卷照片"
    },
    {
      "id": "20261030-math-006",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "一个两位小数，十分位上的数比百分位大 2；交换这两个数字后与原数相加得 8.88。原数是多少？",
      "options": [
        "4.53",
        "4.35",
        "4.26",
        "4.62"
      ],
      "answer_index": 0,
      "explain": "4.53+4.35=8.88。4.35 正是交换后的那个数，不是原数；孩子试过 4.26、4.35 都不对。",
      "opt_from": "4.35、4.26 都是孩子当时试过的答案；4.62 是把「大 2」关系写反",
      "tags": [
        "小数数位",
        "竖式数字谜推理"
      ],
      "source": "数学单元卷《小数的意义和加减法》五、填空（第2页第6题）"
    },
    {
      "id": "20261030-math-007",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "竖式谜 6.27+2.27 的得数是多少？",
      "options": [
        "8.54",
        "8.64",
        "7.54",
        "9.54"
      ],
      "answer_index": 0,
      "explain": "6.27+2.27=8.54（唯一解）。孩子把方框填成 3、2、3，算成了 6.37+2.23。",
      "opt_from": "8.64 是进位多算一次；7.54、9.54 是个位少算或多算 1",
      "tags": [
        "小数加减法竖式谜",
        "进位与退位"
      ],
      "source": "数学单元卷《小数的意义和加减法》八、数字谜（第4页）"
    },
    {
      "id": "20261102-math-001",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "一组发芽 m 粒，二组比一组的 2 倍少 3 粒。式子 2m-3-m 表示什么？",
      "options": [
        "二组比一组多发芽的种子数",
        "一组发芽的种子数",
        "二组发芽的种子数",
        "两组一共发芽的种子数"
      ],
      "answer_index": 0,
      "explain": "2m-3 是二组，再减去一组的 m，剩下的是二组比一组多出的部分，即 m-3 粒。孩子填成了「第 1 组发芽数量」。",
      "opt_from": "第 2 项=孩子当时的错答；另外两项是同一情境里容易混的另外两个量",
      "tags": [
        "用字母表示数",
        "式子的意义",
        "含字母式子的化简"
      ],
      "source": "数学《五数上BS·第四单元综合素养练》 一、填空（第1页第7题）"
    },
    {
      "id": "20261102-math-002",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "魔盒输入 3 输出 9、输入 8 输出 24、输入 15 输出 45。题目指定用字母 a 表示输入的数，魔盒的秘密该写成哪个式子？",
      "options": [
        "3a",
        "3n",
        "a+3",
        "a×a×a"
      ],
      "answer_index": 0,
      "explain": "输出总是输入的 3 倍，题目指定用 a，所以必须写 3a。孩子写成 3n，倍数对了但字母没按题目要求。",
      "opt_from": "3n=孩子错答；a+3、a×a×a 是同期另一道选择题里的真实干扰项",
      "tags": [
        "用字母表示数",
        "找规律"
      ],
      "source": "数学《五数上BS·第四单元综合素养练》 一、填空（第1页第8题）"
    },
    {
      "id": "20261102-math-003",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "声音每秒传 340 米。人离山崖 s 米，喊一声到听见回声要多少秒？",
      "options": [
        "2s÷340",
        "340s",
        "s÷340",
        "340÷s"
      ],
      "answer_index": 0,
      "explain": "声音要走一个来回，总路程 2s 米，所以时间=2s÷340（也就是 s÷170）。孩子写成 340s，把速度和距离乘在一起了。",
      "opt_from": "340s=孩子错答；s÷340 是只算了一趟；340÷s 是把单位写反",
      "tags": [
        "用字母表示数",
        "行程问题",
        "回声"
      ],
      "source": "数学《五数上BS·第四单元综合素养练》 一、填空（第1页第10题）"
    },
    {
      "id": "20261102-math-004",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "摆 1 个八边形要 8 根小棒，往后每多摆一个只添 7 根（相邻两个共用一条边）。摆 n 个共要多少根？",
      "options": [
        "7n+1",
        "8+7n",
        "8n",
        "7n"
      ],
      "answer_index": 0,
      "explain": "8+7×(n-1)=7n+1。把 n=1 代进去验算：8+7n 得 15，可摆 1 个只要 8 根。孩子写的正是 8+7n。",
      "opt_from": "8+7n=孩子错答；8n、7n 是没扣掉共用边的常见写法",
      "tags": [
        "用字母表示数",
        "图形规律",
        "找规律"
      ],
      "source": "数学《五数上BS·第四单元综合素养练》 一、填空（第1页第12题）"
    },
    {
      "id": "20261102-math-005",
      "subject": "数学",
      "type": "choice4",
      "level": "original",
      "enabled": true,
      "stem": "一定与 3a（a＞0）相等的是（　）。",
      "options": [
        "a+3",
        "a×a×a",
        "a 的平方",
        "a+a+a"
      ],
      "answer_index": 3,
      "explain": "D。3a 表示 3 个 a 相加，就是 a+a+a。B 是 a×a×a＝a 的立方，C 是 a 的平方，A 是 a 与 3 相加，都不等于 3a",
      "opt_from": "原题自带的 A/B/C/D 选项，原样照搬",
      "tags": [
        "用字母表示数",
        "3a 与 a 的立方的区别"
      ],
      "source": "数学《五数上BS·第四单元综合素养练》 二、选择（第2页第1题）"
    },
    {
      "id": "20261102-math-009",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "日历上框出 2×2 的四个数：同一行相邻差 1，上下两行同一列差 7。哪一组能表示这四个数？",
      "options": [
        "a、a+1、a+7、a+8",
        "a、b、c、d",
        "A、A+1、B、B+1",
        "只写具体数字，不用字母"
      ],
      "answer_index": 0,
      "explain": "同行差 1、隔行差 7，所以是 a、a+1、a+7、a+8（对应原卷选项 D）。孩子在括号里写了 BD 两个字母，单选写两个等于没答。",
      "opt_from": "三个干扰项分别对应卡片里对原卷 A、B、C 三个选项的原话描述",
      "tags": [
        "用字母表示数",
        "日历中的规律"
      ],
      "source": "数学《五数上BS·第四单元综合素养练》 二、选择（第2页第5题）"
    },
    {
      "id": "20261102-math-010",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "日历上框出 3×3 的 9 个数，正中间是 x。左上角那个数是几？",
      "options": [
        "x-8",
        "x-7",
        "x-1",
        "x+8"
      ],
      "answer_index": 0,
      "explain": "往左上角走，先减 1 再减 7，一共减 8。x-7 只是正上方那个数，孩子就填了 x-7。",
      "opt_from": "x-7=孩子错答；x-1、x+8 分别是左边和右下角，都是同题里的真实答案",
      "tags": [
        "用字母表示数",
        "日历中的规律"
      ],
      "source": "数学《五数上BS·第四单元综合素养练》 附加题（第4页第1小题）"
    },
    {
      "id": "20261102-math-011",
      "subject": "数学",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "日历上 3×3 框出的 9 个数，和是 153，中间数是 17。第一行应该是哪三个数？",
      "options": [
        "9、10、11",
        "10、11、12",
        "8、9、10",
        "9、17、25"
      ],
      "answer_index": 0,
      "explain": "17 正上方是 10，左上角再往左一格是 9，所以第一行 9、10、11。孩子写成 10、11、12，整组加起来是 156。",
      "opt_from": "10、11、12=孩子当时的错答；其余为相邻或同列的数字组合",
      "tags": [
        "用字母表示数",
        "日历中的规律",
        "9 的倍数"
      ],
      "source": "数学《五数上BS·第四单元综合素养练》 附加题（第4页第3小题）"
    },
    {
      "id": "20261103-chinese-001",
      "subject": "语文",
      "type": "choice4",
      "level": "original",
      "enabled": true,
      "stem": "下面选项中，加点字读音完全相同的一项是（　　）\n说明：每组三个词里加点的是同一个字，本单用【　】把它标出来。",
      "options": [
        "【任】丘　【任】县　【任】职",
        "勉【强】　【强】迫　牵【强】",
        "桂【冠】　【冠】军　夺【冠】",
        "【削】弱　瘦【削】　【削】面"
      ],
      "answer_index": 1,
      "explain": "B。B 组三个词的「强」都读 qiǎng（勉强 miǎn qiǎng、强迫 qiǎng pò、牵强 qiān qiǎng）。A 组「任丘」「任县」是地名读 Rén，「任职」读 rèn，不完全相同；C 组「桂冠」读 guān，「冠军」「夺冠」读 guàn；D 组「削弱」读 xuē，「瘦削」「削面」读 xiāo。",
      "opt_from": "原题自带的 A/B/C/D 选项，原样照搬",
      "tags": [
        "多音字",
        "字音辨析"
      ],
      "source": "语文五上《2026-2027学年度五年级上册语文第二单元作业设计》 第1页 一、选择题 第1题"
    },
    {
      "id": "20261103-chinese-002",
      "subject": "语文",
      "type": "choice4",
      "level": "original",
      "enabled": true,
      "stem": "读下面的语句，对其主要意思概括最恰当的一项是（　　）\n夏天的夜晚，爷爷把躺椅摆在浓密的葡萄架下，躺在了躺椅上，旁边是冒着热气的茶。这时候，爷爷边听着戏，边摇着蒲扇，边喝着热茶，真是快乐无比呀！",
      "options": [
        "夏天的夜晚很美。",
        "爷爷躺在葡萄架下。",
        "爷爷听戏喝茶。",
        "爷爷悠然自得。"
      ],
      "answer_index": 3,
      "explain": "D。这段话列举听戏、摇蒲扇、喝茶等多个举动，落点在「真是快乐无比呀」，概括的是爷爷整体的状态——悠然自得。C 只复述了其中两个动作，不是「最恰当」的概括。",
      "opt_from": "原题自带的 A/B/C/D 选项，原样照搬",
      "tags": [
        "概括主要意思",
        "抓关键词句"
      ],
      "source": "语文五上《2026-2027学年度五年级上册语文第二单元作业设计》 第1页 一、选择题 第3题"
    },
    {
      "id": "20261103-chinese-003",
      "subject": "语文",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "读拼音写词语：fēng suǒ。下面哪个写法是正确的？",
      "options": [
        "封锁",
        "封琐",
        "封索",
        "风锁"
      ],
      "answer_index": 0,
      "explain": "「锁」是金字旁，右边部件不能丢笔画。这一题孩子被红笔判错 6 个字：荡、锁、广、阔、移、乱。",
      "opt_from": "干扰项为金字旁相近、读音相同或同音替代的常见错字，依据卡片批注里的部件要点",
      "tags": [
        "读拼音写词语",
        "生字书写",
        "第二单元生字"
      ],
      "source": "语文五上《2026-2027学年度五年级上册语文第二单元作业设计》 第1~2页 二、填空题 第5题 读拼音写词语"
    },
    {
      "id": "20261103-chinese-004",
      "subject": "语文",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "补全岳飞《满江红》里的名句：「莫等闲，__________，空悲切。」",
      "options": [
        "白了少年头",
        "白了少年华",
        "少壮不努力",
        "白了少年头，空悲切"
      ],
      "answer_index": 0,
      "explain": "「莫等闲，白了少年头，空悲切」。孩子三句内容都写对了，扣分疑在「勉励」「朝夕」两处的书写，卡片按规矩记为待核对。",
      "opt_from": "「白了少年华」为改字、「少壮不努力」是串到另一首惜时名句、末项是把后句一起抄进空里",
      "tags": [
        "名言默写",
        "日积月累"
      ],
      "source": "语文五上《2026-2027学年度五年级上册语文第二单元作业设计》 第2页 第6题 按要求完成练习（名句填空）"
    },
    {
      "id": "20261103-chinese-005",
      "subject": "语文",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "照样子写「上课铃响后教室里的情景」，哪一句写得最具体？",
      "options": [
        "教室里立刻安静下来，同学们坐得端端正正，眼睛一眨不眨地盯着黑板，手里的笔飞快地记着笔记。",
        "上课铃响了，教室里没有了一点声音，等老师过来，上课了，同学拿笔。",
        "上课铃响了，大家都很安静。",
        "上课了，同学们在教室里学习。"
      ],
      "answer_index": 0,
      "explain": "第 1 句是卡片里的参考例文，写出了一连串看得见的动作。开放题没有唯一答案，这里比的是「具体」和「笼统」。",
      "opt_from": "第 2 句=孩子当时的原句；第 3、4 句是把原句改得更笼统，用来作对比",
      "tags": [
        "写话",
        "细节描写",
        "全神贯注"
      ],
      "source": "语文五上《2026-2027学年度五年级上册语文第二单元作业设计》 第2页 三、语言表达 第7题",
      "open_ended": true
    },
    {
      "id": "20261103-chinese-006",
      "subject": "语文",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "《什么比猎豹的速度更快》阅读链接：游隼发现猎物后为什么「不降反升」？",
      "options": [
        "先快速升上高空占领制高点，再近似垂直地高速俯冲而下",
        "先飞高看清猎物，再慢慢滑翔下去",
        "先升高躲开天敌，再回过头捕食",
        "先升到高空，等亲鸟来教它怎么俯冲"
      ],
      "answer_index": 0,
      "explain": "原文：先快速升上高空，占领制高点，再以每秒 75~100 米近似垂直俯冲。孩子写成「他要先占领高点」，红笔把「他」改成「它」，并在「高点」前补了「制」。",
      "opt_from": "三个干扰项是对「不降反升」的常见误解，都围绕原文事实设计",
      "tags": [
        "阅读理解-提取信息",
        "代词使用"
      ],
      "source": "语文五上《2026-2027学年度五年级上册语文第二单元作业设计》 第3页 四、阅读 第8题《什么比猎豹的速度更快》 第(3)小题"
    },
    {
      "id": "20261103-chinese-007",
      "subject": "语文",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "读到「对着以超音速移动的人大喊，他听不见」，下面哪个问题最值得提出来探究？",
      "options": [
        "为什么对着以超音速移动的人大喊，他听不见？",
        "那个人叫什么名字？",
        "声音是什么颜色的？",
        "这段话一共有多少个字？"
      ],
      "answer_index": 0,
      "explain": "卡片里的问题示例就是这一问。好问题要冲着内容里的「为什么」去，孩子提的方向是对的，只是把「为什么」重复写了两遍。",
      "opt_from": "另外三项是三种典型的「不算问题」的提问，用来对比",
      "tags": [
        "阅读策略-提出问题",
        "提高阅读速度"
      ],
      "source": "语文五上《2026-2027学年度五年级上册语文第二单元作业设计》 第3页 四、阅读 第8题《什么比猎豹的速度更快》 第(5)小题"
    },
    {
      "id": "20261103-chinese-008",
      "subject": "语文",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "《中国刺绣》按「什么是刺绣 →（　）→ 刺绣历史 → …」列提纲，第②段「刺绣起源很早」这一格该填什么？",
      "options": [
        "刺绣起源",
        "关于刺绣的介绍",
        "刺绣有哪些种类",
        "刺绣用的针和线"
      ],
      "answer_index": 0,
      "explain": "每格要压成 4~6 个字的方面短语：什么是刺绣 → 刺绣起源 → 刺绣历史 → 刺绣种类 → 刺绣实际用途。孩子第一格写成了描述性长句。",
      "opt_from": "第 2 项接近孩子当时的写法；后两项取自同一提纲里的其它方面",
      "tags": [
        "阅读理解-归纳要点",
        "说明文结构"
      ],
      "source": "语文五上《2026-2027学年度五年级上册语文第二单元作业设计》 第3~4页 四、阅读 第9题《中国刺绣》 第(2)小题"
    },
    {
      "id": "20261103-chinese-009",
      "subject": "语文",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "第④段写：按材料可分丝绣、羽毛绣、发绣；按地域又有苏绣、粤绣、湘绣、蜀绣。这段主要用了什么说明方法？",
      "options": [
        "举例子",
        "列数字",
        "打比方",
        "作比较"
      ],
      "answer_index": 0,
      "explain": "用具体例子说明「种类多样、流派众多」。孩子「举例子」判断对了，但好处写重复了、没点出说明了什么特点。格式：运用……的说明方法，具体准确地说明了……（特点）。",
      "opt_from": "另外三项都是小学阶段真实存在的说明方法",
      "tags": [
        "说明方法",
        "举例子",
        "答题格式"
      ],
      "source": "语文五上《2026-2027学年度五年级上册语文第二单元作业设计》 第4页 四、阅读 第9题《中国刺绣》 第(4)小题"
    },
    {
      "id": "20261103-chinese-010",
      "subject": "语文",
      "type": "choice4",
      "level": "converted",
      "enabled": true,
      "stem": "如果向外国朋友介绍中国刺绣，哪一句开头最得体、信息最全？",
      "options": [
        "中国刺绣是我国的国粹，起源很早，距今已有几千年历史，种类也很多。",
        "中国刺绣起源于虞舜之时，历史时间长，种类多如湘秀、留秀等13种。",
        "刺绣很好看，我很喜欢。",
        "你要不要买一块刺绣带回去？"
      ],
      "answer_index": 0,
      "explain": "第 1 句取自参考例文，先点明身份和特点。孩子那句把「湘绣」写成「湘秀」，还有别的错别字。开放题没有唯一答案，这里比的是得体与信息完整。",
      "opt_from": "第 2 句=孩子当时的原句（错别字原样保留）；后两句是口语化和跑题的写法",
      "tags": [
        "写话-介绍事物",
        "结合原文",
        "错别字"
      ],
      "source": "语文五上《2026-2027学年度五年级上册语文第二单元作业设计》 第4页 四、阅读 第9题《中国刺绣》 第(5)小题",
      "open_ended": true
    },
    {
      "id": "RD5A-CH-R01",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "读《猛醒》片段答问题：断臂乞丐上门乞讨，女主人指着门前一堆砖说：「你帮我把这堆砖搬到屋后去吧。」她让乞丐做的事是什么？",
      "options": [
        "把门前的砖搬到屋后",
        "把屋后的砖搬回门前",
        "给庭院里的花浇水",
        "把空袖子缝补好"
      ],
      "answer_index": 0,
      "explain": "女主人指着门前一堆砖，让乞丐搬到屋后，没有直接给钱。",
      "opt_from": "其他三项都改错了搬砖的地点或事情",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "短文《猛醒》",
        "细节理解"
      ],
      "source": "ima 知识库 · 【11】5年级短文阅读练习20篇.pdf"
    },
    {
      "id": "RD5A-CH-R02",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "读《猛醒》片段答问题：乞丐生气地说：「我只有一只手，你还忍心叫我搬砖。不愿意给就不给，何必捉弄人呢？」他生气是因为什么？",
      "options": [
        "嫌砖堆太重搬不动",
        "以为女主人故意捉弄他",
        "想先吃点东西再干活",
        "找不到砖要搬到哪里"
      ],
      "answer_index": 1,
      "explain": "乞丐以为女主人不愿施舍，故意拿搬砖来捉弄他。",
      "opt_from": "干扰项都是乞丐可能有的想法，但他说的是「何必捉弄人」",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "短文《猛醒》",
        "细节理解"
      ],
      "source": "ima 知识库 · 【11】5年级短文阅读练习20篇.pdf"
    },
    {
      "id": "RD5A-CH-R03",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "读《猛醒》片段答问题：女主人并不生气，俯身搬起砖来，她故意只用一只手搬了一趟。她这样做是想说明什么？",
      "options": [
        "自己比乞丐力气大",
        "一只手也能把活干成",
        "砖其实一点也不重",
        "搬砖比给钱更省事"
      ],
      "answer_index": 1,
      "explain": "女主人用一只手搬砖，是想让乞丐看到：不是非要两只手才能做事。",
      "opt_from": "干扰项都把女主人的示范理解成别的动机",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "短文《猛醒》",
        "细节理解"
      ],
      "source": "ima 知识库 · 【11】5年级短文阅读练习20篇.pdf"
    },
    {
      "id": "RD5A-CH-R04",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《猛醒》的阅读提示问：同情、帮助什么样的人，怎么帮助人？结合短文，女主人帮助乞丐的方式是什么？",
      "options": [
        "直接给钱让他离开",
        "让他靠劳动找回自尊",
        "替他向邻居求助",
        "把他介绍到工厂上班"
      ],
      "answer_index": 1,
      "explain": "女主人没有直接施舍，而是让他搬砖，让他明白靠自己也能生活。",
      "opt_from": "干扰项都是常见的施舍或安排方式，与文中「让他干活」不同",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "短文《猛醒》",
        "中心理解"
      ],
      "source": "ima 知识库 · 【11】5年级短文阅读练习20篇.pdf"
    },
    {
      "id": "RD5A-CH-R05",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "按《阅读理解12条万能公式》，概括记叙文的主要内容，常用哪个格式？",
      "options": [
        "时间+地点+人+事",
        "说明对象+特点",
        "论点+论据",
        "起因+经过+结果"
      ],
      "answer_index": 0,
      "explain": "资料写明：记叙文要回答清楚（什么时间、什么地点）什么人做什么事，格式是（时间+地点）+人+事。",
      "opt_from": "B 是说明文格式，C 是议论文思路，D 看着合理但不是资料给的格式",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "答题方法",
        "记叙文"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册语文阅读理解12条万能公式.pdf"
    },
    {
      "id": "RD5A-CH-R06",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "按《阅读理解12条万能公式》，概括说明文的主要内容，格式是什么？",
      "options": [
        "说明（介绍）+说明对象+说明内容（特点）",
        "时间+地点+人+事",
        "用什么论证方法证明了论点",
        "人物+事件+结果"
      ],
      "answer_index": 0,
      "explain": "资料写明：说明文要回答清楚说明对象是什么、它的特点是什么。",
      "opt_from": "其他三项分别是记叙文和议论文的格式",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "答题方法",
        "说明文"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册语文阅读理解12条万能公式.pdf"
    },
    {
      "id": "RD5A-CH-R07",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "按《阅读理解12条万能公式》，概括议论文的主要内容，格式是什么？",
      "options": [
        "用什么论证方法证明了（论证了）+论点",
        "说明对象+特点",
        "时间+地点+人+事",
        "先总写后分写"
      ],
      "answer_index": 0,
      "explain": "资料写明：议论文要回答清楚议论的问题和作者的观点。",
      "opt_from": "B 是说明文格式，C 是记叙文格式，D 说的是结构不是内容格式",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "答题方法",
        "议论文"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册语文阅读理解12条万能公式.pdf"
    },
    {
      "id": "RD5A-CH-R08",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "做阅读理解时，遇到「谈谈你的收获、启发」这类题，资料建议主要根据什么来答？",
      "options": [
        "文章的中心",
        "自己的随便想象",
        "题目有几个字",
        "作者的出生年份"
      ],
      "answer_index": 0,
      "explain": "资料说：很多问答题都是根据中心解答的，有些文章可以直接在文中找到中心句。",
      "opt_from": "干扰项都不是答题依据，B 看着像开放题但实际不能脱离中心",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "答题方法",
        "中心理解"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册语文阅读理解12条万能公式.pdf"
    },
    {
      "id": "RD5A-CH-R09",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "按《阅读理解12条万能公式》的说法，写人文章的中心通常是什么？",
      "options": [
        "赞美主人公的优秀品质",
        "介绍一件物品的用途",
        "说明一种自然现象",
        "记录一天的气温变化"
      ],
      "answer_index": 0,
      "explain": "资料写明：写人主要是赞美主人公的某些优秀品质。",
      "opt_from": "其余三项分别对应说明文、写景或观察记录，不是写人文章的中心",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "答题方法",
        "写人文章"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册语文阅读理解12条万能公式.pdf"
    },
    {
      "id": "RD5A-CH-R10",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "读句子答问题：「白鹭是一首精巧的诗。」《白鹭》开头写这句话，在全文中的作用是什么？",
      "options": [
        "总领全文",
        "总结全文",
        "承上启下",
        "设置悬念"
      ],
      "answer_index": 0,
      "explain": "早读晚默资料写明：这句话在文中的作用是总领全文。",
      "opt_from": "结尾那句才是总结，B/C/D 都不是资料给的作用",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "课内阅读",
        "句子作用"
      ],
      "source": "ima 知识库 · 【40】五年级上册语文期末复习必备—早读晚默.pdf"
    },
    {
      "id": "RD5A-CH-R11",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《白鹭》结尾写「白鹭实在是一首诗，一首韵在骨子里的散文诗」，与开头相呼应。全文结构是什么？",
      "options": [
        "总分总",
        "分总分",
        "并列式",
        "递进式"
      ],
      "answer_index": 0,
      "explain": "资料写明：开头总领、结尾总结，所以本文结构是总分总。",
      "opt_from": "另外三种结构都不符合开头总起、结尾总结的写法",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "课内阅读",
        "文章结构"
      ],
      "source": "ima 知识库 · 【40】五年级上册语文期末复习必备—早读晚默.pdf"
    },
    {
      "id": "RD5A-CH-R12",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "读《蝉》的译文答问题：「蝉正是因为在高处它的声音才能传得远，并非是凭借秋风的力量。」对应哪两句诗？",
      "options": [
        "垂緌饮清露，流响出疏桐",
        "居高声自远，非是藉秋风",
        "七夕今宵看碧霄，牵牛织女渡河桥",
        "死去元知万事空，但悲不见九州同"
      ],
      "answer_index": 1,
      "explain": "资料里的译文说的正是「居高声自远，非是藉秋风」。",
      "opt_from": "其他三项都是同册日积月累里的其他诗句，不是这段译文对应的两句",
      "unit": "五上语文阅读理解",
      "tags": [
        "阅读理解",
        "课内阅读",
        "诗文理解"
      ],
      "source": "ima 知识库 · 【2025秋新版】【五年级上册语文】全册日积月累及解释.pdf"
    },
    {
      "id": "TB5A-CH-001",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《白鹭》的作者是谁？",
      "options": [
        "许地山",
        "冯骥才",
        "郭沫若",
        "琦君"
      ],
      "answer_index": 2,
      "explain": "《白鹭》作者郭沫若。另外三位是第一单元其他课文的作者。",
      "opt_from": "三个干扰项都是第一单元其他课文的真实作者，不是编的人名",
      "unit": "五上语文1-4单元",
      "tags": [
        "作者",
        "第一单元"
      ],
      "source": "ima 知识库 · 【40】五年级上册语文期末复习必备—早读晚默.pdf"
    },
    {
      "id": "TB5A-CH-002",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《白鹭》开头总领全文的是哪一句？",
      "options": [
        "白鹭实在是一首诗，一首韵在骨子里的散文诗。",
        "白鹭是一首精巧的诗。",
        "色素的配合，身段的大小，一切都很适宜。",
        "那雪白的蓑毛，那全身的流线型结构。"
      ],
      "answer_index": 1,
      "explain": "开头「白鹭是一首精巧的诗」总领全文，结尾那句是总结，全文为总分总结构。",
      "opt_from": "干扰项都是课文里的原句，分别取自结尾总结句和描写白鹭外形的句子",
      "unit": "五上语文1-4单元",
      "tags": [
        "课文理解",
        "第一单元"
      ],
      "source": "ima 知识库 · 【40】五年级上册语文期末复习必备—早读晚默.pdf"
    },
    {
      "id": "TB5A-CH-003",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《落花生》的作者是谁？",
      "options": [
        "郭沫若",
        "冯骥才",
        "琦君",
        "许地山"
      ],
      "answer_index": 3,
      "explain": "《落花生》作者许地山，笔名落华生，课文用借物喻人的写法讲做人的道理。",
      "opt_from": "干扰项为同单元其他课文作者",
      "unit": "五上语文1-4单元",
      "tags": [
        "作者",
        "第一单元"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级语文上册《第一单元》高频考点汇总！.pdf"
    },
    {
      "id": "TB5A-CH-004",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《落花生》按什么顺序写？",
      "options": [
        "种花生→收花生→尝花生→议花生",
        "议花生→种花生→收花生→尝花生",
        "收花生→种花生→议花生→尝花生",
        "尝花生→议花生→种花生→收花生"
      ],
      "answer_index": 0,
      "explain": "课文按事情发展顺序写，重点落在「议花生」，由花生的特点讲出做人的道理。",
      "opt_from": "干扰项是把四个真实环节调换顺序，不是编造的情节",
      "unit": "五上语文1-4单元",
      "tags": [
        "课文理解",
        "第一单元"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级语文上册《第一单元》高频考点汇总！.pdf"
    },
    {
      "id": "TB5A-CH-005",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《落花生》借花生告诉我们什么道理？",
      "options": [
        "做人要像桃子石榴那样把果实高高挂在枝上",
        "花生的好处是价钱便宜、人人爱吃",
        "人要做有用的人，不要做只讲体面而对别人没有好处的人",
        "种花生要比收花生更辛苦"
      ],
      "answer_index": 2,
      "explain": "父亲的话点明中心：要做有用的人，不要只讲体面而对别人没有好处。",
      "opt_from": "干扰项取自课文里出现过的桃子石榴、价钱便宜、种收花生等真实内容",
      "unit": "五上语文1-4单元",
      "tags": [
        "中心思想",
        "第一单元"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级语文上册《第一单元》高频考点汇总！.pdf"
    },
    {
      "id": "TB5A-CH-006",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《桂花雨》的作者是谁？",
      "options": [
        "许地山",
        "琦君",
        "冯骥才",
        "郭沫若"
      ],
      "answer_index": 1,
      "explain": "《桂花雨》作者琦君，写的是童年摇桂花的回忆和思乡之情。",
      "opt_from": "干扰项为同单元其他课文作者",
      "unit": "五上语文1-4单元",
      "tags": [
        "作者",
        "第一单元"
      ],
      "source": "ima 知识库 · 五年级语文上册全册看拼音写词语.pdf"
    },
    {
      "id": "TB5A-CH-007",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《珍珠鸟》的作者是谁？",
      "options": [
        "郭沫若",
        "许地山",
        "冯骥才",
        "琦君"
      ],
      "answer_index": 2,
      "explain": "《珍珠鸟》作者冯骥才，写小鸟由怕人到信赖人的变化。",
      "opt_from": "干扰项为同单元其他课文作者",
      "unit": "五上语文1-4单元",
      "tags": [
        "作者",
        "第一单元"
      ],
      "source": "ima 知识库 · 【40】五年级上册语文期末复习必备—早读晚默.pdf"
    },
    {
      "id": "TB5A-CH-008",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《珍珠鸟》点明中心的是哪一句？",
      "options": [
        "白鹭是一首精巧的诗",
        "人要做有用的人",
        "搭石，构成了家乡的一道风景",
        "信赖，往往创造出美好的境界"
      ],
      "answer_index": 3,
      "explain": "结尾「信赖，往往创造出美好的境界」是全文中心句。",
      "opt_from": "干扰项是第一、二单元课文里的真实中心句",
      "unit": "五上语文1-4单元",
      "tags": [
        "中心思想",
        "第一单元"
      ],
      "source": "ima 知识库 · 【40】五年级上册语文期末复习必备—早读晚默.pdf"
    },
    {
      "id": "TB5A-CH-009",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《搭石》借摆搭石、走搭石赞美了什么？",
      "options": [
        "搭石结实耐用不容易坏",
        "乡亲们无私奉献、一心为他人着想",
        "家乡秋天的风景很美",
        "作者小时候走路的本领"
      ],
      "answer_index": 1,
      "explain": "课文借小小的搭石，赞颂乡亲们默默无闻、一心为他人着想的美好品德。",
      "opt_from": "干扰项都取自课文里真实写到的搭石、秋景、走搭石",
      "unit": "五上语文1-4单元",
      "tags": [
        "中心思想",
        "第二单元"
      ],
      "source": "ima 知识库 · 【40】五年级上册语文期末复习必备—早读晚默.pdf"
    },
    {
      "id": "TB5A-CH-010",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《将相和》里的「将」和「相」分别是谁？",
      "options": [
        "廉颇、蔺相如",
        "蔺相如、廉颇",
        "赵王、秦王",
        "秦王、赵王"
      ],
      "answer_index": 0,
      "explain": "「将」是廉颇，「相」是蔺相如，两人由不和到和好，共同卫国。",
      "opt_from": "干扰项是把两位主角次序调换，以及课文里另外两位国君",
      "unit": "五上语文1-4单元",
      "tags": [
        "课文理解",
        "第二单元"
      ],
      "source": "ima 知识库 · 五年级（上）语文一课一练学习单（前7页）.pdf"
    },
    {
      "id": "TB5A-CH-011",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《将相和》由哪三个小故事组成？",
      "options": [
        "负荆请罪、完璧归赵、纸上谈兵",
        "渑池会面、负荆请罪、围魏救赵",
        "完璧归赵、渑池会面、负荆请罪",
        "完璧归赵、负荆请罪、草木皆兵"
      ],
      "answer_index": 2,
      "explain": "三个故事依次是完璧归赵、渑池会面、负荆请罪，前两个写「和」的缘由，后一个写「和」的结果。",
      "opt_from": "干扰项混入另外三个真实成语故事名，考查能否分辨哪些出自本篇",
      "unit": "五上语文1-4单元",
      "tags": [
        "课文理解",
        "第二单元"
      ],
      "source": "ima 知识库 · 【38】五年级上册语文1-8单元单元知识点归纳梳理.pdf"
    },
    {
      "id": "TB5A-CH-012",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《猎人海力布》里，海力布最后变成了什么？",
      "options": [
        "一座高山",
        "一只小鸟",
        "一股泉水",
        "一块石头"
      ],
      "answer_index": 3,
      "explain": "他为救乡亲说出秘密，自己变成了一块石头，是个舍己为人的民间故事。",
      "opt_from": "干扰项取自故事里出现过的山、鸟、泉水等真实事物",
      "unit": "五上语文1-4单元",
      "tags": [
        "民间故事",
        "第三单元"
      ],
      "source": "ima 知识库 · 【38】五年级上册语文1-8单元单元知识点归纳梳理.pdf"
    },
    {
      "id": "TB5A-CH-013",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "古诗《示儿》的作者是谁？",
      "options": [
        "林升",
        "陆游",
        "龚自珍",
        "杜甫"
      ],
      "answer_index": 1,
      "explain": "《示儿》是南宋诗人陆游的临终绝笔，盼的是王师北定中原。",
      "opt_from": "干扰项中林升写《题临安邸》、龚自珍写《己亥杂诗》，都是同单元古诗的真实作者",
      "unit": "五上语文1-4单元",
      "tags": [
        "古诗",
        "第四单元"
      ],
      "source": "ima 知识库 · 【38】五年级上册语文1-8单元单元知识点归纳梳理.pdf"
    },
    {
      "id": "TB5A-CH-014",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《题临安邸》的作者是谁？",
      "options": [
        "陆游",
        "苏轼",
        "林升",
        "龚自珍"
      ],
      "answer_index": 2,
      "explain": "《题临安邸》是宋代诗人林升写在旅店墙上的讽喻诗。",
      "opt_from": "干扰项为同单元古诗作者和一位真实宋代诗人",
      "unit": "五上语文1-4单元",
      "tags": [
        "古诗",
        "第四单元"
      ],
      "source": "ima 知识库 · 【38】五年级上册语文1-8单元单元知识点归纳梳理.pdf"
    },
    {
      "id": "TB5A-CH-015",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "「我劝天公重抖擞」的下一句是？",
      "options": [
        "不拘一格降人才",
        "万马齐喑究可哀",
        "九州生气恃风雷",
        "化作春泥更护花"
      ],
      "answer_index": 0,
      "explain": "出自龚自珍《己亥杂诗》：「我劝天公重抖擞，不拘一格降人才。」",
      "opt_from": "前三个干扰项都是同一首诗里的原句，最后一个是龚自珍另一首名句",
      "unit": "五上语文1-4单元",
      "tags": [
        "古诗",
        "第四单元"
      ],
      "source": "ima 知识库 · 【38】五年级上册语文1-8单元单元知识点归纳梳理.pdf"
    },
    {
      "id": "TB5A-CH-016",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《示儿》中叮嘱儿子的临终心愿是哪两句？",
      "options": [
        "死去元知万事空，但悲不见九州同",
        "山重水复疑无路，柳暗花明又一村",
        "暖风熏得游人醉，直把杭州作汴州",
        "王师北定中原日，家祭无忘告乃翁"
      ],
      "answer_index": 3,
      "explain": "「王师北定中原日，家祭无忘告乃翁」写出他至死盼统一的心愿。",
      "opt_from": "干扰项分别是《示儿》首句、陆游另一首名句、《题临安邸》名句",
      "unit": "五上语文1-4单元",
      "tags": [
        "古诗",
        "第四单元"
      ],
      "source": "ima 知识库 · 【38】五年级上册语文1-8单元单元知识点归纳梳理.pdf"
    },
    {
      "id": "TB5A-CH-017",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《少年中国说》（节选）的作者是谁？",
      "options": [
        "鲁迅",
        "梁启超",
        "康有为",
        "孙中山"
      ],
      "answer_index": 1,
      "explain": "作者梁启超，文章写「故今日之责任，不在他人，而全在我少年」。",
      "opt_from": "干扰项都是同一时代真实人物，考查作者归属",
      "unit": "五上语文1-4单元",
      "tags": [
        "课文理解",
        "第四单元"
      ],
      "source": "ima 知识库 · 【38】五年级上册语文1-8单元单元知识点归纳梳理.pdf"
    },
    {
      "id": "TB5A-CH-018",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "「红日初升，其道大光」出自哪篇课文？",
      "options": [
        "《白鹭》",
        "《示儿》",
        "《少年中国说》",
        "《圆明园的毁灭》"
      ],
      "answer_index": 2,
      "explain": "出自《少年中国说》节选，用一连串比喻赞美少年中国。",
      "opt_from": "干扰项都是第四单元或第一单元的真实课文名",
      "unit": "五上语文1-4单元",
      "tags": [
        "课文理解",
        "第四单元"
      ],
      "source": "ima 知识库 · 【38】五年级上册语文1-8单元单元知识点归纳梳理.pdf"
    },
    {
      "id": "TB5A-CH-019",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《圆明园的毁灭》在写法上有什么特点？",
      "options": [
        "先写昔日辉煌，再写惨遭毁灭",
        "先写毁灭，再补叙昔日辉煌",
        "只写被毁灭的详细经过",
        "只写园林建筑的样子"
      ],
      "answer_index": 0,
      "explain": "题目是「毁灭」，却用大量篇幅写昔日辉煌，用反差激起痛惜与愤慨。",
      "opt_from": "干扰项都是对同一篇课文写法的合理但错误的猜测",
      "unit": "五上语文1-4单元",
      "tags": [
        "写法",
        "第四单元"
      ],
      "source": "ima 知识库 · 【2025秋新版】【五年级上册语文】第5-8单元各课中心思想总结.pdf"
    },
    {
      "id": "TB5A-CH-020",
      "subject": "语文",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "《白鹭》一课里「匣子」的「匣」读什么？",
      "options": [
        "jiá",
        "xiā",
        "jiǎ",
        "xiá"
      ],
      "answer_index": 3,
      "explain": "读 xiá。第一单元易读错的字还有嗜好 shì、垂蔓 màn、便宜 pián。",
      "opt_from": "干扰项取自一课一练里给出的形近、音近误读",
      "unit": "五上语文1-4单元",
      "tags": [
        "字音",
        "第一单元"
      ],
      "source": "ima 知识库 · 五年级（上）语文一课一练学习单（前7页）.pdf"
    },
    {
      "id": "TB5A-EN-001",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "「乐于助人的」是哪个单词？",
      "options": [
        "hard-working",
        "polite",
        "helpful",
        "clever"
      ],
      "answer_index": 2,
      "explain": "helpful 乐于助人的。这几个都是 Unit 1 描述人物性格的重点单词。",
      "opt_from": "干扰项都是 Unit 1 单词表里真实存在的性格词",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "单词"
      ],
      "source": "ima 知识库 · 【2025秋新版】【五年级上册英语】期中复习知识点归纳.pdf"
    },
    {
      "id": "TB5A-EN-002",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "「严格的」是哪个单词？",
      "options": [
        "strict",
        "shy",
        "kind",
        "funny"
      ],
      "answer_index": 0,
      "explain": "strict 严格的，Unit 1 常用来描述老师。",
      "opt_from": "干扰项都是 Unit 1 的性格词",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "单词"
      ],
      "source": "ima 知识库 · 【2025秋新版】【五年级上册英语】期中复习知识点归纳.pdf"
    },
    {
      "id": "TB5A-EN-003",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "「勤奋的」是哪个单词？",
      "options": [
        "helpful",
        "polite",
        "young",
        "hard-working"
      ],
      "answer_index": 3,
      "explain": "hard-working 勤奋的，注意中间有连字符。",
      "opt_from": "干扰项都是 Unit 1 单词表里的真实单词",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "单词"
      ],
      "source": "ima 知识库 · 【2025秋新版】【五年级上册英语】期中复习知识点归纳.pdf"
    },
    {
      "id": "TB5A-EN-004",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "「有礼貌的」是哪个单词？",
      "options": [
        "shy",
        "polite",
        "old",
        "young"
      ],
      "answer_index": 1,
      "explain": "polite 有礼貌的；shy 是害羞的，别弄混。",
      "opt_from": "干扰项都是 Unit 1 单词表里的真实单词",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "单词"
      ],
      "source": "ima 知识库 · 【2025秋新版】【五年级上册英语】期中复习知识点归纳.pdf"
    },
    {
      "id": "TB5A-EN-005",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "「年轻的」是哪个单词？",
      "options": [
        "old",
        "funny",
        "young",
        "kind"
      ],
      "answer_index": 2,
      "explain": "young 年轻的，反义词是 old 年老的。",
      "opt_from": "干扰项都是 Unit 1 单词表里的真实单词",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "单词"
      ],
      "source": "ima 知识库 · 【2025秋新版】【五年级上册英语】期中复习知识点归纳.pdf"
    },
    {
      "id": "TB5A-EN-006",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "—What's she like? 合适的回答是？",
      "options": [
        "She's kind.",
        "She likes cats.",
        "She is a teacher.",
        "Yes, she is."
      ],
      "answer_index": 0,
      "explain": "What's ... like? 问的是性格或样子，用 He's / She's + 形容词回答。",
      "opt_from": "干扰项分别是答「喜欢什么」「职业」「一般疑问句」三种常见答非所问",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "句型"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册英语 1-3单元知识点汇总.pdf"
    },
    {
      "id": "TB5A-EN-007",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "—Is he young? 正确的否定回答是？",
      "options": [
        "No, he is.",
        "Yes, he isn't.",
        "No, she isn't.",
        "No, he isn't."
      ],
      "answer_index": 3,
      "explain": "Is he...? 的否定回答是 No, he isn't. 人称和 be 动词都要对上。",
      "opt_from": "干扰项分别是前后不一致、人称错、肯定否定混搭三种典型错误",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "句型"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册英语 常用表达重点句型.pdf"
    },
    {
      "id": "TB5A-EN-008",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "—What do you have on Thursdays? 合适的回答是？",
      "options": [
        "It's Thursday.",
        "I have maths, English and music.",
        "I often read books.",
        "Yes, I do."
      ],
      "answer_index": 1,
      "explain": "问星期四有什么课，要回答具体课程；I have maths, English and music.",
      "opt_from": "干扰项分别是回答星期、回答平常做什么、回答一般疑问句",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit2",
        "句型"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册英语 常用表达重点句型.pdf"
    },
    {
      "id": "TB5A-EN-009",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "—What day is it today? 合适的回答是？",
      "options": [
        "It's 8:00.",
        "It's hot.",
        "It's Monday.",
        "I have maths."
      ],
      "answer_index": 2,
      "explain": "问今天星期几，回答 It's + 星期名，如 It's Monday.",
      "opt_from": "干扰项分别答成时间、天气、课程，都是同单元句型里出现过的答句",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit2",
        "句型"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级英语上册《期末重要句型》整理！.pdf"
    },
    {
      "id": "TB5A-EN-010",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "—Do you often read books? 正确的肯定回答是？",
      "options": [
        "Yes, I do.",
        "Yes, I am.",
        "Yes, I have.",
        "Yes, I does."
      ],
      "answer_index": 0,
      "explain": "Do you...? 用 do 提问就用 do 回答：Yes, I do.",
      "opt_from": "干扰项是 be 动词、have、第三人称单数三种助动词用错",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit2",
        "句型"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级英语上册 1-6各单元重点知识+语法.pdf"
    },
    {
      "id": "TB5A-EN-011",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "「星期三」是哪个单词？",
      "options": [
        "Tuesday",
        "Thursday",
        "Monday",
        "Wednesday"
      ],
      "answer_index": 3,
      "explain": "Wednesday 星期三，拼写里有个不发音的 d，最容易写错。",
      "opt_from": "干扰项都是 Unit 2 星期词表里真实存在的词",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit2",
        "单词"
      ],
      "source": "ima 知识库 · 【2025秋新版】【五年级上册英语】期中复习知识点归纳.pdf"
    },
    {
      "id": "TB5A-EN-012",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "「星期四」是哪个单词？",
      "options": [
        "Tuesday",
        "Thursday",
        "Wednesday",
        "Friday"
      ],
      "answer_index": 1,
      "explain": "Thursday 星期四；Tuesday 是星期二，两个词长得很像。",
      "opt_from": "干扰项都是 Unit 2 星期词表里真实存在的词",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit2",
        "单词"
      ],
      "source": "ima 知识库 · 【2025秋新版】【五年级上册英语】期中复习知识点归纳.pdf"
    },
    {
      "id": "TB5A-EN-013",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "I ___ helpful at home. 填哪个？",
      "options": [
        "is",
        "are",
        "am",
        "be"
      ],
      "answer_index": 2,
      "explain": "I 后面用 am：I am helpful at home.",
      "opt_from": "干扰项是 be 动词另外三种形式",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "be动词"
      ],
      "source": "ima 知识库 · 【9】【英语】【通用】五年级英语上册英语每日一练小纸条.pdf"
    },
    {
      "id": "TB5A-EN-014",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "He ___ very kind. 填哪个？",
      "options": [
        "is",
        "am",
        "are",
        "be"
      ],
      "answer_index": 0,
      "explain": "He / She / it 后面用 is。",
      "opt_from": "干扰项是 be 动词另外三种形式",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "be动词"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级英语上册 1-6各单元重点知识+语法.pdf"
    },
    {
      "id": "TB5A-EN-015",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "We ___ good friends. 填哪个？",
      "options": [
        "is",
        "am",
        "be",
        "are"
      ],
      "answer_index": 3,
      "explain": "We / you / they 后面用 are：We are good friends.",
      "opt_from": "干扰项是 be 动词另外三种形式",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "be动词"
      ],
      "source": "ima 知识库 · 【9】【英语】【通用】五年级英语上册英语每日一练小纸条.pdf"
    },
    {
      "id": "TB5A-EN-016",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "Mr Zhou will ___ our new maths teacher. 填哪个？",
      "options": [
        "is",
        "be",
        "are",
        "am"
      ],
      "answer_index": 1,
      "explain": "will 后面要接动词原形，所以用 be。",
      "opt_from": "干扰项是把 will 后面当成一般现在时填的三种 be 动词形式",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "语法"
      ],
      "source": "ima 知识库 · 【9】【英语】【通用】五年级英语上册英语每日一练小纸条.pdf"
    },
    {
      "id": "TB5A-EN-017",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "The old man is ___ (fun). 该怎么填？",
      "options": [
        "fun",
        "funnily",
        "funny",
        "funner"
      ],
      "answer_index": 2,
      "explain": "be 动词后要用形容词 funny，意思是「风趣的、滑稽的」。",
      "opt_from": "干扰项是原词、副词和按中文习惯造的比较级",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "词形"
      ],
      "source": "ima 知识库 · 【9】【英语】【通用】五年级英语上册英语每日一练小纸条.pdf"
    },
    {
      "id": "TB5A-EN-018",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "Lily can cook food and wash clothes. She is very ___.",
      "options": [
        "helpful",
        "shy",
        "strict",
        "young"
      ],
      "answer_index": 0,
      "explain": "会做饭、会洗衣服，说明她 helpful（乐于助人的）。",
      "opt_from": "干扰项都是 Unit 1 真实性格词，但和句子意思对不上",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit1",
        "单词"
      ],
      "source": "ima 知识库 · 【9】【英语】【通用】五年级英语上册英语每日一练小纸条.pdf"
    },
    {
      "id": "TB5A-EN-019",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "—What's your favourite food? 合适的回答是？",
      "options": [
        "It's Monday.",
        "She's kind.",
        "Yes, I do.",
        "Sandwiches."
      ],
      "answer_index": 3,
      "explain": "问最喜欢的食物，直接答食物名，如 Sandwiches.",
      "opt_from": "干扰项分别是星期、人物性格、一般疑问句三种答非所问",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit3",
        "句型"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册英语重点句型及语法.pdf"
    },
    {
      "id": "TB5A-EN-020",
      "subject": "英语",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "I'm ___. I'd like some water. 填哪个？",
      "options": [
        "hungry",
        "thirsty",
        "thirty",
        "tasty"
      ],
      "answer_index": 1,
      "explain": "想喝水说明渴了，thirsty 口渴的；thirty 是「三十」，只差一个字母。",
      "opt_from": "干扰项是 Unit 3 食物话题里真实出现或形近的词",
      "unit": "五上英语Unit1-3",
      "tags": [
        "Unit3",
        "单词"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册英语重点句型及语法.pdf"
    },
    {
      "id": "TB5A-MA-001",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "0.8×0.5 等于多少？",
      "options": [
        "0.04",
        "0.4",
        "4",
        "0.004"
      ],
      "answer_index": 1,
      "explain": "8×5=40，两个因数共两位小数，所以积是 0.40，也就是 0.4。",
      "opt_from": "干扰项是小数点位置点错的三种常见结果",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数乘法"
      ],
      "source": "ima 知识库 · 前四页【先锋教辅】五年级上册数学专项练习每日一练人教版(3).pdf"
    },
    {
      "id": "TB5A-MA-002",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "7.4×0.9 的积是几位小数？",
      "options": [
        "一位",
        "三位",
        "两位",
        "整数"
      ],
      "answer_index": 2,
      "explain": "两个因数各有一位小数，积 6.66 是两位小数。",
      "opt_from": "干扰项是数小数位数时常见的三种错答",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数乘法"
      ],
      "source": "ima 知识库 · 五年级（上）数学第一单元测试卷1《人教版》.pdf"
    },
    {
      "id": "TB5A-MA-003",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "已知 32×18=576，那么 18×3.2 等于多少？",
      "options": [
        "57.6",
        "5.76",
        "576",
        "0.576"
      ],
      "answer_index": 0,
      "explain": "一个因数缩小到原来的 1/10，积也缩小到 1/10，得 57.6。",
      "opt_from": "干扰项是按积的变化规律点错小数点的结果",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数乘法",
        "积的变化规律"
      ],
      "source": "ima 知识库 · 五年级（上）数学第一单元测试卷1《人教版》.pdf"
    },
    {
      "id": "TB5A-MA-004",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "3.2×0.18 等于多少？",
      "options": [
        "5.76",
        "57.6",
        "0.0576",
        "0.576"
      ],
      "answer_index": 3,
      "explain": "32×18=576，两个因数共三位小数，所以积是 0.576。",
      "opt_from": "干扰项是小数点位置点错的三种结果",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数乘法"
      ],
      "source": "ima 知识库 · 五年级（上）数学第一单元测试卷1《人教版》.pdf"
    },
    {
      "id": "TB5A-MA-005",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "9.6÷0.8 等于多少？",
      "options": [
        "1.2",
        "12",
        "120",
        "0.12"
      ],
      "answer_index": 1,
      "explain": "除数和被除数同时扩大 10 倍，变成 96÷8=12。",
      "opt_from": "干扰项是商的小数点点错的常见结果",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数除法"
      ],
      "source": "ima 知识库 · 前四页【先锋教辅】五年级上册数学专项练习每日一练人教版(3).pdf"
    },
    {
      "id": "TB5A-MA-006",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "6.5÷1.25 等于多少？",
      "options": [
        "52",
        "0.52",
        "5.2",
        "5.02"
      ],
      "answer_index": 2,
      "explain": "同时扩大 100 倍得 650÷125=5.2。",
      "opt_from": "干扰项来自商的小数点位置与数字抄写错误",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数除法"
      ],
      "source": "ima 知识库 · 前四页【先锋教辅】五年级上册数学专项练习每日一练人教版(3).pdf"
    },
    {
      "id": "TB5A-MA-007",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "12 个西红柿重 5.4 千克，平均每个重多少？",
      "options": [
        "0.45 千克",
        "0.54 千克",
        "4.5 千克",
        "0.045 千克"
      ],
      "answer_index": 0,
      "explain": "5.4÷12=0.45 千克，这是「求每份数」的典型题。",
      "opt_from": "干扰项是把 5.4÷12 算错小数点或抄成 5.4÷10 的结果",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数除法",
        "应用题"
      ],
      "source": "ima 知识库 · 【35】五年级上册数学小数除法专项练习-空白.pdf"
    },
    {
      "id": "TB5A-MA-008",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "每个蛋糕用 0.32 千克面粉，4.8 千克面粉能做几个？",
      "options": [
        "1.5 个",
        "150 个",
        "12 个",
        "15 个"
      ],
      "answer_index": 3,
      "explain": "4.8÷0.32=15 个，这是「求份数」的问题。",
      "opt_from": "干扰项是小数点位置算错和用 4.8÷0.4 估出来的结果",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数除法",
        "应用题"
      ],
      "source": "ima 知识库 · 【35】五年级上册数学小数除法专项练习-空白.pdf"
    },
    {
      "id": "TB5A-MA-009",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "0.08×10 等于多少？",
      "options": [
        "8",
        "0.8",
        "0.008",
        "80"
      ],
      "answer_index": 1,
      "explain": "乘 10，小数点向右移一位，得 0.8。",
      "opt_from": "干扰项是小数点移错方向的三种结果",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数乘法"
      ],
      "source": "ima 知识库 · 前四页【先锋教辅】五年级上册数学专项练习每日一练人教版(3).pdf"
    },
    {
      "id": "TB5A-MA-010",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "1.5×0.7 等于多少？",
      "options": [
        "10.5",
        "0.105",
        "1.05",
        "1.5"
      ],
      "answer_index": 2,
      "explain": "15×7=105，两个因数共两位小数，得 1.05。",
      "opt_from": "干扰项是小数位数数错和忘记相乘的结果",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数乘法"
      ],
      "source": "ima 知识库 · 前四页【先锋教辅】五年级上册数学专项练习每日一练人教版(3).pdf"
    },
    {
      "id": "TB5A-MA-011",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "7.8×2.2 等于多少？",
      "options": [
        "17.16",
        "15.16",
        "171.6",
        "16.16"
      ],
      "answer_index": 0,
      "explain": "78×22=1716，两个因数共两位小数，得 17.16。",
      "opt_from": "干扰项来自进位算错和小数点点错",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数乘法",
        "竖式"
      ],
      "source": "ima 知识库 · 前四页【先锋教辅】五年级上册数学专项练习每日一练人教版(3).pdf"
    },
    {
      "id": "TB5A-MA-012",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "一个数（0 除外）乘小于 1 的数，积会怎样？",
      "options": [
        "比原数大",
        "和原数相等",
        "一定等于 0",
        "比原数小"
      ],
      "answer_index": 3,
      "explain": "乘小于 1 的数，积比原数小；乘大于 1 的数，积比原数大。",
      "opt_from": "干扰项是这条规律记反或记混的三种说法",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数乘法",
        "规律"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册数学公式大全.pdf"
    },
    {
      "id": "TB5A-MA-013",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "被除数不变，除数扩大到原来的 10 倍，商会怎样？",
      "options": [
        "扩大到 10 倍",
        "缩小到原来的 1/10",
        "不变",
        "扩大到 100 倍"
      ],
      "answer_index": 1,
      "explain": "除数越大商越小，除数扩大 10 倍，商反而缩小到 1/10。",
      "opt_from": "干扰项是把商的变化规律记反或记成不变的三种说法",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数除法",
        "规律"
      ],
      "source": "ima 知识库 · 【2025秋新版】五年级上册数学公式大全.pdf"
    },
    {
      "id": "TB5A-MA-014",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "用数对表示位置，写作 (3, 5)，表示什么？",
      "options": [
        "第 5 列第 3 行",
        "第 3 行第 5 列",
        "第 3 列第 5 行",
        "第 8 列第 5 行"
      ],
      "answer_index": 2,
      "explain": "数对先写列、再写行，(3,5) 是第 3 列第 5 行。",
      "opt_from": "干扰项是把列行次序颠倒、以及把两个数相加的常见错误",
      "unit": "五上数学1-4单元",
      "tags": [
        "位置",
        "数对"
      ],
      "source": "ima 知识库 · 五年级（上）数学第一单元测试卷1《人教版》.pdf"
    },
    {
      "id": "TB5A-MA-015",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "点 (4, 2) 向右平移 2 格后，数对变成什么？",
      "options": [
        "(6, 2)",
        "(4, 4)",
        "(2, 2)",
        "(4, 0)"
      ],
      "answer_index": 0,
      "explain": "向右平移只改列数，4+2=6，行数不变，得 (6,2)。",
      "opt_from": "干扰项分别是向上、向左、向下平移的结果",
      "unit": "五上数学1-4单元",
      "tags": [
        "位置",
        "平移"
      ],
      "source": "ima 知识库 · 五年级（上）数学第一单元测试卷1《人教版》.pdf"
    },
    {
      "id": "TB5A-MA-016",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "盒子里有 5 个红球、1 个白球，任意摸一个，结果怎样？",
      "options": [
        "摸到白球的可能性大",
        "两种可能性一样大",
        "一定摸到红球",
        "摸到红球的可能性大"
      ],
      "answer_index": 3,
      "explain": "红球多，摸到红球的可能性大，但不是「一定」，白球仍可能被摸到。",
      "opt_from": "干扰项是可能性这一单元里最典型的三种错答",
      "unit": "五上数学1-4单元",
      "tags": [
        "可能性"
      ],
      "source": "ima 知识库 · 【34】五年级上册数学期中期末常考应用题专项练习题.pdf"
    },
    {
      "id": "TB5A-MA-017",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "抛一枚均匀硬币，正面朝上的可能性是多少？",
      "options": [
        "1",
        "1/2",
        "0",
        "1/4"
      ],
      "answer_index": 1,
      "explain": "只有正反两种等可能结果，正面占其中一种，所以是 1/2。",
      "opt_from": "干扰项是把「一定」「不可能」和多抛一次的结果混进来",
      "unit": "五上数学1-4单元",
      "tags": [
        "可能性"
      ],
      "source": "ima 知识库 · 【34】五年级上册数学期中期末常考应用题专项练习题.pdf"
    },
    {
      "id": "TB5A-MA-018",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "1÷3 的商是多少？",
      "options": [
        "0.3",
        "3",
        "0.333…",
        "0.13"
      ],
      "answer_index": 2,
      "explain": "除不尽，商是循环小数 0.333…，3 不断重复。",
      "opt_from": "干扰项是把循环小数截断、把被除数当商、以及抄错数字",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数除法",
        "循环小数"
      ],
      "source": "ima 知识库 · 【35】五年级上册数学小数除法专项练习-空白.pdf"
    },
    {
      "id": "TB5A-MA-019",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "3.996 保留两位小数约是多少？",
      "options": [
        "4.00",
        "3.99",
        "3.90",
        "4.0"
      ],
      "answer_index": 0,
      "explain": "第三位小数是 6，要进一，连续进位得 4.00；保留两位小数末尾的 0 不能省。",
      "opt_from": "干扰项分别是没进位、进位出错、以及只写一位小数的常见错答",
      "unit": "五上数学1-4单元",
      "tags": [
        "近似数",
        "四舍五入"
      ],
      "source": "ima 知识库 · 五年级下册数学期末必背公式整理归纳.pdf"
    },
    {
      "id": "TB5A-MA-020",
      "subject": "数学",
      "type": "choice4",
      "level": "textbook",
      "enabled": true,
      "stem": "水费 12 吨以内每吨 2.5 元，用水 11 吨要交多少钱？",
      "options": [
        "30 元",
        "25 元",
        "41.8 元",
        "27.5 元"
      ],
      "answer_index": 3,
      "explain": "11 吨全在 12 吨以内，11×2.5=27.5 元，不用分段。",
      "opt_from": "干扰项是按 12 吨算、按 10 吨算、以及误用 3.8 元高价的结果",
      "unit": "五上数学1-4单元",
      "tags": [
        "小数乘法",
        "分段计费"
      ],
      "source": "ima 知识库 · 【34】五年级上册数学期中期末常考应用题专项练习题.pdf"
    }
  ],
  "excluded": [
    {
      "id": "20261102-chinese-001",
      "reason": "家长 2026-11-02 指示：本题已当面讲解，从练习单撤掉，不再重做"
    },
    {
      "id": "20261102-chinese-002",
      "reason": "家长 2026-11-02 指示：整篇《化龙门》撤掉，不再重做"
    },
    {
      "id": "20261102-math-008",
      "reason": "家长 2026-11-02 指示：天平题已当面讲解，就当是做对了，不再重做"
    }
  ]
};
