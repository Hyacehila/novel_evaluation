# MarketFictionBench：面向中英双语商业小说生成能力的 Benchmark 综述与方案

更新时间：`2026-04-06`

## 0. 文档目的

这是一份单文件、自包含的总文档，目标是同时解决两件事：

1. 综述现有 AI 写作能力，尤其是故事生成、小说生成、长文本创作、主观偏好评测相关的 Benchmark / Dataset / Evaluation 方向。
2. 在当前仓库 `novel_evaluation` 已有能力基础上，提出一个更有研究价值、也更接近真实编辑决策的 `MarketFictionBench` 方案。

这份文档默认读者是：

- 正在做 LLM 写作评测的研究者
- 想把当前项目从“工业稿件评分工具”扩展为“公开 benchmark 设计”的你自己
- 未来可能参与标注、实验、judge 训练或数据发布的协作者

本文不是产品文档，也不是 API 说明。它是一份研究与方案合一的设计文稿。

## 1. 执行摘要

### 1.1 一句话结论

如果你的目标是衡量“模型生成作品的商业性”，那么最值得做的，不是再做一个泛写作 benchmark，也不是单纯做中文网文打分，而是做一个 `中英双语 + 短篇到中篇分档 + target market slot 显式建模 + 专家 pairwise acquisition preference 主榜 + 8 轴/4-lens 诊断榜` 的商业小说 benchmark。

### 1.2 为什么当前仓库值得作为出发点

当前仓库并不是从零开始。它已经具备三类非常稀缺的资产：

- 一套明确服务于“商业性”而不是“纯文学性”的 8 轴评价语言
- 一套把“通用质量”和“题材内判断”分开的 4-lens 结构
- 一套 `outline + story` 联合评估的 pipeline 思路

这三点恰好是大量公开写作 benchmark 没有做好、或者根本没想做的。

### 1.3 为什么不能直接把当前项目原样公开成 benchmark

因为当前项目的根本定位仍然是：

- 中文网文工业场景
- 对已有稿件做多阶段评分
- 单任务、单结果对象、单产品链路

而公开 benchmark 需要的是：

- 标准化 brief
- 标准化 submission
- 人工绝对评分 + pairwise 排序
- 中英双语对齐
- 可公开发布的数据组织与版权策略

所以正确方向不是“直接把产品改成 benchmark”，而是“抽取其中最有价值的评价语言，重组为一套独立 benchmark”。

## 2. 当前仓库到底提供了什么可迁移资产

当前仓库 `novel_evaluation` 的正式定位是“网络小说打分器”。从结构上看，它的主链路是：

- `input_screening`
- `type_classification`
- `rubric_evaluation`
- `type_lens_evaluation`
- `consistency_check`
- `aggregation`
- `final_projection`

它不是生成器，而是评估器。这个差异非常重要，因为你后续设计 benchmark 时，必须明确区分：

- “生成任务定义”
- “评测任务定义”

当前仓库真正值得迁移的是后者。

### 2.1 8 个通用评价轴

当前项目在 `packages/schemas/common/enums.py` 中定义了 8 个商业导向轴：

- `hookRetention`
- `serialMomentum`
- `characterDrive`
- `narrativeControl`
- `pacingPayoff`
- `settingDifferentiation`
- `platformFit`
- `commercialPotential`

这 8 个轴非常有价值，因为它们隐含了一种行业视角：

- 不是“语言好不好看”而已
- 不是“逻辑通不通”而已
- 而是“这篇东西是否能抓人、推人追读、支撑连载、形成平台转化、具备商业开发可能”

这比很多现有 benchmark 更接近真实编辑与内容平台的判断方式。

### 2.2 类型化 4-lens

当前项目不是只做通用打分。它还做了 genre-specific 透镜：

- 通用 8 轴回答“整体是否成立”
- 类型 4-lens 回答“在这个题材内部，它是否成立”

这点很重要，因为创意写作能力不能只做完全通用化评测。一个好的 romance 和一个好的 progression fantasy，本来就不应该用完全同构的细粒度标准去衡量。

### 2.3 `outline + story` 联合评估

当前仓库并不只是看正文。它本质上已经在强调：

- 大纲是否成立
- 正文是否兑现大纲
- 二者是否一致

这点对未来 benchmark 极关键。很多公开写作 benchmark 只看终稿文本，但在真实写作工作流中：

- outline 是计划能力
- story 是执行能力
- consistency 是计划与执行的闭环能力

如果 benchmark 不保留 outline 层，很多真正有研究价值的写作能力会被压扁成“语言表面质量”。

### 2.4 不能直接复用的部分

虽然当前仓库很有价值，但有几块不能原样搬过去：

- 类型命名过于中文网文化
- 整套产品默认是中文单语
- 当前 `overall score` 更适合产品展示，不适合公共排行榜主榜
- 当前数据形态面向用户上传稿件，不面向标准化 benchmark 输入

因此，未来 benchmark 必须是“继承评价思想”，而不是“继承现有产品接口”。

## 3. 现有写作 Benchmark / Dataset 的总体景观

如果把近年的相关工作按“它们到底在评什么”来分，可以大致分成五类。

### 3.1 基础故事数据集与经典故事任务

代表工作：

- [WritingPrompts: Building a Dataset for Reading Comprehension and Character-based Story Generation](https://aclanthology.org/P18-1082/)
- [A Corpus and Cloze Evaluation for Deeper Understanding of Commonsense Stories](https://aclanthology.org/N16-1098/)

这类工作的核心贡献是把“故事”从非结构化创意产物，变成可以被机器学习系统处理的标准任务。

它们解决了下面这些基础问题：

- prompt 到 story 的任务化
- 大规模叙事样本收集
- 短篇故事理解与补全
- story generation 不同于 factual generation 的边界

但从你的目标看，它们有三个明显不足：

- 几乎不讨论商业性
- 几乎不讨论市场 slot
- 大多不关心 outline 和 serial 化结构

因此，这些工作更适合作为“故事生成 benchmark 的祖先”，而不是直接拿来做你要的目标。

### 3.2 多语言与中文长文本写作 benchmark

代表工作：

- [MTG](https://arxiv.org/abs/2108.07140)
- [LOT](https://arxiv.org/abs/2108.12960)
- [LongWriter: Unleashing 10,000+ Word Generation from Long Context LLMs](https://arxiv.org/abs/2408.07055)
- [WebNovelBench: Placing LLM Novelists on the Web Novel Distribution](https://arxiv.org/abs/2505.14818)
- [ConStory-Bench / Lost in Stories](https://arxiv.org/abs/2603.05890)

这一类工作离你的兴趣更近，因为它们已经开始面对：

- 中文场景
- 长文本生成
- 小说或类小说任务
- 长文的一致性与规划问题

其中几篇工作的启发尤其直接。

#### MTG / LOT 的启发

这类工作证明：

- 多语言文本生成 benchmark 是可行的
- 中文长文本任务不能简单照搬英文短任务

但它们的目标还是“生成能力总评估”更强，而不是“商业小说能力评估”。

#### LongWriter / LongBench-Write 的启发

`LongWriter` 的关键价值不在于“让模型写得更长”本身，而在于它提醒了一个事实：

> 生成超长输出本身是一个独立问题，不能被短输出能力自然外推。

对你来说，这意味着：

- 长度应该成为一个明确维度
- 但不能让“长度”喧宾夺主，压过“作品是否值得看”

也就是说，长度是 benchmark 的条件变量，不是 benchmark 的核心价值本身。

#### WebNovelBench 的启发

`WebNovelBench` 是最接近你当前项目语境的公开工作之一。它的重要性在于：

- 明确面向中文网文
- 明确面向长篇故事生成
- 明确试图用多维度方式评估叙事质量

但它仍然更偏向“长篇网文生成能力”评估，而不是“编辑会不会签”的商业决策评估。

#### ConStory-Bench 的启发

这类工作对你最大的提醒是：

> 中长篇故事中，一致性问题是第一类灾难性失败，而不是边角问题。

这非常支持你把 `B4/B5` 设计成：

- 分章协议
- 章节表
- rolling memory card

而不是“一口气生成 5 万到 10 万字全文”。

### 3.3 主观写作质量、偏好与 judge 方向

代表工作：

- [StoryER](https://aclanthology.org/2022.emnlp-main.114/)
- [STORYWARS](https://arxiv.org/abs/2305.08152)
- [WritingBench](https://arxiv.org/abs/2503.05244)
- [LitBench](https://arxiv.org/abs/2507.00769)
- [WritingPreferenceBench](https://arxiv.org/abs/2510.14616)

这一类工作最重要的结论不是具体分数，而是评测哲学：

#### 结论 1：创意写作不能只用自动指标

BLEU、ROUGE、甚至很多 embedding similarity，对创意写作都非常弱，因为：

- 一篇好故事并不需要靠近某个 reference 才成立
- 新颖性和参考重合率往往冲突
- 商业抓力更不是 lexical overlap 能表达的

#### 结论 2：单一绝对分通常不稳定

故事与小说的主观性很强。很多时候：

- 评分人对“3 分”和“4 分”的边界并不稳定
- 但对“这两篇里我更愿意签哪篇”的判断更稳定

因此，pairwise preference 往往比单一绝对分更适合作为主榜信号。

#### 结论 3：文学性不等于商业性

这点对你尤其关键。

很多写作 benchmark 隐含的目标更接近：

- 风格
- 文学感
- 语言高级度
- 文学性偏好

但你要解决的问题是：

- 开头能不能抓人
- 题材卖点是否明确
- 是否适配特定市场
- 是否值得持续投入

所以你不能把“creative writing”简单理解成“文学性越强越好”。

### 3.4 面向小说本体的 benchmark

代表工作：

- [Towards A “Novel” Benchmark](https://aclanthology.org/2025.findings-acl.1114/)

这类工作比通用写作 benchmark 更贴近小说，但通常仍然没有把下面这些点同时做成正式问题：

- 平台或 market slot
- 连载转化结构
- 商业 acquisition preference
- outline-aware 评估

所以它们是强相关邻居，但还不是你的直接终点。

### 3.5 一个简短判断

综上，现有公开工作已经覆盖了：

- 故事生成
- 多语言生成
- 中文长文本
- 小说体写作
- 长文一致性
- 主观偏好评测

但是没有一条公开 benchmark 明确把以下四点结合起来：

1. 中英双语
2. 短篇到中篇分档
3. 商业 acquisition preference 为主榜
4. `outline + story + 8 axes + 4 lenses + market slot`

这就是 `MarketFictionBench` 的真正切口。

## 3.6 扩展综述：逐篇论文解读

这一节按“与小说评价问题的距离”来组织。需要先说明一点：并不是所有文献都在做你现在定义下的“商业小说评价 benchmark”。有些工作更偏故事生成数据集，有些偏自动评价器，有些偏长篇一致性，有些偏文学质量或小说理解。但它们共同构成了你设计 `MarketFictionBench` 时必须对照的现有版图。下面每篇都说明它的正式 venue、核心问题、方法特点以及它和你方案的关键差别。

### 3.6.1 Fan, Lewis, Dauphin 2018, ACL Long Papers

论文：[`Hierarchical Neural Story Generation`](https://aclanthology.org/P18-1082/)  
Venue：ACL 2018 Long Papers  
核心对象：`WritingPrompts` 数据集与层级式故事生成

这篇文章的重要性在于，它几乎奠定了后续“prompt 到 story”这一开放式叙事生成任务的标准范式。作者从 Reddit 的 `WritingPrompts` 社区收集了约 30 万组 prompt-story 对，平均故事长度已经达到中等篇幅，不再只是极短句级别的 completion。它试图解决的不是“小说商业性”问题，而是“模型如何在长于一句话或一段话的场景下生成更连贯、更相关、且更长的故事”。它的最大特点有两点：第一，用大规模人类写作社区数据把故事生成任务真正做成了主流 benchmark；第二，它把 hierarchical generation 作为关键建模方向，即先建较高层结构，再展开正文。与 `MarketFictionBench` 的关系是，这篇文章给你提供了任务化起点，但它没有 market slot、没有商业偏好主榜、没有类型诊断层，也没有把 outline 作为正式 submission contract，而只是把“分层生成”当作模型结构问题来处理。

### 3.6.2 Mostafazadeh et al. 2016, NAACL-HLT

论文：[`A Corpus and Cloze Evaluation for Deeper Understanding of Commonsense Stories`](https://aclanthology.org/N16-1098/)  
Venue：NAACL-HLT 2016  
核心对象：`ROCStories` 与 `Story Cloze Test`

这篇工作并不是小说生成 benchmark，但它对叙事理解研究影响极大，因为它把“故事理解”正式落成了一个可量化的测试框架。作者构建了 5 万篇五句式常识故事，并据此定义 Story Cloze Test，让模型从候选结尾中选出合理结尾。它试图解决的核心问题是：系统是否真正理解事件之间的常识关系、时间关系与因果推进，而不是只会做表面词汇匹配。它的特点是结构清晰、任务定义明确、评测稳定，因此极适合作为 narrative understanding 的早期标准基线。与 `MarketFictionBench` 相比，`ROCStories` 的优势在于问题非常干净，适合研究基础叙事推理；但它也非常明显地不足以覆盖你要的目标，因为它文本太短、几乎没有题材内商业逻辑、没有连载感、没有大纲-正文关系，更没有“编辑会不会签”这一类真实世界决策目标。

### 3.6.3 Akoury et al. 2020, EMNLP

论文：[`STORIUM: A Dataset and Evaluation Platform for Machine-in-the-Loop Story Generation`](https://aclanthology.org/2020.emnlp-main.525/)  
Venue：EMNLP 2020  
核心对象：来自 STORIUM 社区的协作式故事数据与评测平台

`STORIUM` 的独特之处在于，它不是单纯扔给模型一个 prompt 然后看输出，而是把故事写作放回到“人与系统协作”的环境里。论文指出，开放式故事生成有两个根本痛点：一是输入上下文常常不够丰富，二是自动评估和众包评估都不稳定。为解决这个问题，作者利用在线协作故事社区的真实写作过程，提供更复杂的上下文、角色卡、设定与后续人工编辑信号，并用用户真实编辑和反馈来构造更可信的评价闭环。它和 `MarketFictionBench` 的不同在于，它更重视人机共创场景下的“可用建议生成”，而不是标准化的公共排行榜；它强调编辑后效果和平台交互信号，而不是中英双语、市场 slot 或商业 acquisition preference。但它对你非常有启发，因为它证明了“创意写作的评价不能脱离真实工作流”，这正支持你坚持把 `outline + story` 放进正式 benchmark contract。

### 3.6.4 Guan et al. 2021, ACL-IJCNLP

论文：[`OpenMEVA: A Benchmark for Evaluating Open-ended Story Generation Metrics`](https://aclanthology.org/2021.acl-long.500/)  
Venue：ACL-IJCNLP 2021 Long Papers  
核心对象：开放式故事生成自动评价指标的 benchmark

`OpenMEVA` 并不是直接评价模型写故事好不好，而是评价“评价指标本身好不好”。它要解决的问题很明确：开放式故事生成中，BLEU、ROUGE 这类传统自动指标与人类判断的相关性往往很差，导致研究者很难公平比较不同系统。为此，作者建立了一个专门的 meta-benchmark，用来比较各类自动指标在故事生成任务中的有效性。这个工作的重要价值在于，它系统地说明了故事生成评价是一个独立难题，而不是生成完文本之后顺手套一个通用 generation metric 就结束。对 `MarketFictionBench` 而言，`OpenMEVA` 提醒你必须把自动指标的角色严格收缩到“质量闸门”或“辅助诊断”，而不能让自动指标取代主榜。你方案中把长度符合度、重复率、一致性、AI 腔检测放在 gate 层，而把主榜交给专家 pairwise preference，这种设计与 `OpenMEVA` 的问题意识是高度一致的。

### 3.6.5 Brahman et al. 2021, Findings of EMNLP

论文：[`“Let Your Characters Tell Their Story”: A Dataset for Character-Centric Narrative Understanding`](https://aclanthology.org/2021.findings-emnlp.150/)  
Venue：Findings of EMNLP 2021  
核心对象：`LiSCU`，面向角色中心叙事理解的数据集

这篇工作把“故事理解”从情节事件层进一步推进到角色层。作者指出，人类阅读文学或叙事文本时，并不是只记住发生了什么，更会形成关于角色身份、关系、动机、意图和性格的整体表征。为了推动这一方向，他们构建了 `LiSCU` 数据集，并定义角色识别与角色描述生成等任务。它的特点在于不再把叙事理解理解成纯粹的事件连贯性，而是把人物建模放到中心。这一点对小说评价尤其重要，因为很多商业小说的抓力并不只来自 plot，而来自角色持续牵引。与 `MarketFictionBench` 相比，`LiSCU` 仍然更偏 narrative understanding，而非生成 ranking benchmark；它没有 market slot，也不讨论商业性。但它强烈支持你保留 `characterDrive` 作为独立评价轴，因为这条轴并不是编辑直觉拍脑袋得来，而是与叙事理解研究中的“角色中心性”方向有明确共鸣。

### 3.6.6 Guan et al. 2022, Transactions of the Association for Computational Linguistics

论文：[`LOT: A Story-Centric Benchmark for Evaluating Chinese Long Text Understanding and Generation`](https://aclanthology.org/2022.tacl-1.25/)  
Venue：TACL 2022  
核心对象：中文长文本故事理解与生成 benchmark

`LOT` 是中文故事长文本 benchmark 中非常关键的一篇，因为它正面回应了“中文长文本缺乏标准 benchmark”这一长期问题。论文把任务设计成 story-centric 的长文本评测框架，同时覆盖理解任务和生成任务，并基于人类写作的中文故事构建数据。它想解决的是：中文模型，尤其是长文本模型，到底能否在故事这一复杂语域下兼顾理解与生成，而不是只在通用长文摘要或长 QA 上看起来可用。`LOT` 的特点是它把“故事”作为中文长文本建模的中心，而不是把故事当成附属领域；同时它与 `LongLM` 之类的长文本预训练工作直接联动。与 `MarketFictionBench` 的关系是，`LOT` 为中文长篇叙事 benchmark 提供了非常重要的前置基础，但它仍然不处理市场适配、商业偏好和双语对齐。也就是说，它回答的是“中文长故事能不能被模型处理”，而不是“这些故事是否更可能成为可签约商业作品”。

### 3.6.7 Chhun et al. 2022, EMNLP

论文：[`StoryER: Automatic Story Evaluation via Ranking, Rating and Reasoning`](https://aclanthology.org/2022.emnlp-main.114/)  
Venue：EMNLP 2022  
核心对象：故事评价的 Ranking / Rating / Reasoning 三任务数据与模型

如果说前面很多工作关注“如何生成故事”，那么 `StoryER` 明确把注意力放在“如何评价故事”上。它批评以往自动故事评价过于依赖表层连贯性和词汇相似，而偏离了真实人类偏好，于是设计了一个三合一框架：第一，给故事一个偏好分；第二，给不同方面打细粒度 rating；第三，生成理由评论。数据规模也很可观，包括 10 万对排序故事和 4.6 万条 aspect ratings/comments。它的最大特点是承认“评价本身就是多任务”，而不是只输出一个分数。与 `MarketFictionBench` 的关系极其密切：你的方案里主榜用 pairwise acquisition preference，诊断榜用 8 轴与 4-lens，实际上就是沿着 `StoryER` 这种“排序 + 分方面打分 + 理由生成”的思路继续往商业小说场景推进。两者的关键区别在于，`StoryER` 更像一个通用故事评价器，而你要做的是更窄、更贴近编辑场景的商业小说评价协议。

### 3.6.8 Du and Chilton 2023, ACL Long Papers

论文：[`StoryWars: A Dataset and Instruction Tuning Baselines for Collaborative Story Understanding and Generation`](https://aclanthology.org/2023.acl-long.171/)  
Venue：ACL 2023 Long Papers  
核心对象：协作式故事的多任务 benchmark

`StoryWars` 的视角很有特色，它研究的不是单作者、单风格的故事，而是多人协作产生的故事文本。作者从在线平台收集了 4 万多篇协作故事、涉及约 9,400 位作者，并进一步定义了 12 类任务、共 101 个具体 story-related tasks，覆盖 fully-supervised、few-shot 和 zero-shot 三种情境。它想解决的问题是：协作式故事由于风格、意图、结构经常发生变化，因此对模型理解和生成都构成独特挑战；而此前几乎没有开放域数据集系统衡量这一类文本。它的特点是任务面非常宽，既包括理解也包括生成，并带有 instruction tuning baseline。与 `MarketFictionBench` 相比，`StoryWars` 更像一个“故事能力综合体检套件”，而你的方向是“商业小说决策型 benchmark”。它没有明确的商业定义，但它提醒你一个重要事实：多作者、风格切换和章节级结构会带来额外不稳定性，所以未来如果你做 human-AI collaboration 子轨，`StoryWars` 是很值得参考的。

### 3.6.9 Yu, Liu, Xiong 2024, LREC-COLING

论文：[`LFED: A Literary Fiction Evaluation Dataset for Large Language Models`](https://aclanthology.org/2024.lrec-main.915/)  
Venue：LREC-COLING 2024  
核心对象：中文长篇文学 fiction 的理解与推理评测数据集

`LFED` 与很多故事生成论文不同，它不是用来让模型写东西，而是专门考模型“读懂长篇文学作品”的能力。作者收集了 95 部文学 fiction，既有中文原创，也有译入中文的作品，覆盖多个世纪和多种题材，并按 8 类问题构造了 1,304 道问题，考察事实理解、逻辑推理、上下文把握、常识推断和价值判断等维度。它试图解决的问题是：LLM 在长篇文学文本上的理解能力，到底离真正的文学阅读有多远。它的特点是文学性强、篇幅长、问题类型丰富，而且直接把“文学 fiction”作为独立评测对象。对 `MarketFictionBench` 来说，`LFED` 不直接提供生成排序协议，但它提醒你：小说评价不能只盯着表层风格和开头钩子，模型对长文中人物、线索、时间与主题的追踪能力同样是中篇写作质量的底层支撑。

### 3.6.10 Bizzoni et al. 2024, LREC-COLING

论文：[`A Matter of Perspective: Building a Multi-Perspective Annotated Dataset for the Study of Literary Quality`](https://aclanthology.org/2024.lrec-main.71/)  
Venue：LREC-COLING 2024  
核心对象：多视角文学质量判断数据集

这篇工作并不是 LLM 生成 benchmark，但对“小说评价标准本身是否稳定”这个问题非常关键。作者构建了一个覆盖 9,000 部 19 至 20 世纪英语文学小说的数据集，并结合专家观点、众包标注以及与文学接受度有关的多种文本指标，尝试把“文学质量”这个向来模糊的概念转化为可以比较的数据资源。它要解决的问题不是“模型能否生成好小说”，而是“不同评价主体如何判断小说质量，且这些判断能否被结构化保存”。它的特点在于大规模、以“质量判断”而不是“生成任务”为中心，并且认真处理版权限制，只公开质量与风格指标而不公开全文。这一点对你尤其有启发：未来 `MarketFictionBench` 在公开数据发布时，同样可以公开 brief、标签、submission 与统计特征，而不必公开版权高风险的原始长篇文本。

### 3.6.11 Atmakuru et al. 2024, arXiv 预印本

论文：[`CS4: Measuring the Creativity of Large Language Models Automatically by Controlling the Number of Story-Writing Constraints`](https://arxiv.org/abs/2410.04197)  
Venue：截至 `2026-04-06`，当前可核实来源为 arXiv 预印本，未在官方页面标出正式会议/期刊版本  
核心对象：通过控制 prompt 约束密度来间接测量故事创意性

`CS4` 的问题意识非常直接：很多模型表面上“很会写故事”，但其实可能只是复述训练语料里见过的高质量叙事模板，因此真正的创意性难以测量。为此作者提出一种很聪明的 benchmark 构造法，不靠大量人工标签，而是通过逐步增加写作 prompt 的约束数量和细度，提高 prompt specificity，让模型更难简单套用已有套路。这样一来，模型如果还能写出连贯且满足要求的故事，就更接近真正的创造性而不是检索式复述。这个工作最大的特点是，它把“创意性评测”转化成一个 prompt 设计问题。与 `MarketFictionBench` 相比，`CS4` 不关注市场、平台或商业签约偏好，但它非常值得借鉴到 brief 设计阶段：你完全可以在部分 `MarketFictionBench` brief 中有意识地提高约束密度，测试模型在商业要求更具体时是否仍然能保持新鲜度与可读性。

### 3.6.12 Wang et al. 2025, Findings of ACL

论文：[`Towards A “Novel” Benchmark: Evaluating Literary Fiction with Large Language Models`](https://aclanthology.org/2025.findings-acl.1114/)  
Venue：Findings of ACL 2025  
核心对象：面向长篇文学 fiction 的多层次评价框架与中英双语标注数据

这篇工作与你的目标非常接近，因为它明确指出，过去创意生成研究更关注短故事、诗歌、剧本，而随着上下文窗口扩展，长篇 fiction 应该成为新的评测前沿。作者提出了一个多层级的小说评价框架，把评价分成 Macro、Meso、Micro 三层，并使用 10 项指标来衡量长篇文学作品，同时构建了一个来自人类作者、LLM 以及 human-AI collaboration 的中英双语 fiction 数据集。论文中一个很有代表性的发现是 LLM 往往呈现“high-starting, low-ending”的模式，即开头强、后劲弱。它与 `MarketFictionBench` 的区别在于，它更偏文学 fiction 与长篇质量分析，而你的方案更偏商业 fiction 与编辑式选择；但它已经证明，中英双语长篇 fiction 评价是可以被系统化构建出来的，这对你的双语设计是重要佐证。

### 3.6.13 Lin, Zheng, Wang 2025, arXiv 预印本

论文：[`WebNovelBench: Placing LLM Novelists on the Web Novel Distribution`](https://arxiv.org/abs/2505.14818)  
Venue：截至 `2026-04-06`，当前可核实来源为 arXiv 预印本，未在官方页面标出正式会议/期刊版本  
核心对象：中文网文长篇生成的 benchmark 与人类作品分布映射

`WebNovelBench` 可以说是目前与你当前项目语境最接近的公开工作之一。它试图解决一个很具体的问题：现有长篇故事 benchmark 缺少足够规模、足够多样化、同时又可复现的评价框架，因此很难真正把模型“放回人类网文生态中”比较。为此，作者基于 4,000 多部中文网文构建 synopsis-to-story 任务，并用 8 个叙事维度做 LLM-as-a-Judge 评分，再通过 PCA 将得分映射到人类作品分布中的百分位位置。它的特点是规模大、中文网文针对性强、评估结果直观，并且真的尝试回答“LLM novelist 在网文分布里排到哪里”。与 `MarketFictionBench` 的差别在于，`WebNovelBench` 主榜更依赖自动 judge 聚合，而不是专家 pairwise acquisition preference；此外它中心仍然是“长篇网文能力”，而不是“中英双语、短中篇分档、市场 slot 显式化”的商业小说评测。

### 3.6.14 Fein et al. 2025, arXiv 预印本

论文：[`LitBench: A Benchmark and Dataset for Reliable Evaluation of Creative Writing`](https://arxiv.org/abs/2507.00769)  
Venue：截至 `2026-04-06`，当前可核实来源为 arXiv 预印本，未在官方页面标出正式会议/期刊版本  
核心对象：用于验证 creative writing judge 可靠性的偏好对比 benchmark

`LitBench` 的重点不在生成，而在“如何可靠地评 creative writing”。作者注意到开放式创意写作没有标准答案，于是很多研究只能临时调用现成 LLM 作为 zero-shot judge，但这些 judge 在创意写作场景下是否可信其实并不明确。为此，论文构建了一个 held-out 的去偏人类偏好故事对比集，以及大规模训练对比数据，用它来测试现成 judge、训练 Bradley-Terry 和 generative reward models，并通过在线人类实验验证这些自动 judge 在全新 LLM 生成故事上的对齐情况。它的关键贡献是把“评价器可靠性”本身变成了 benchmark。对 `MarketFictionBench` 来说，`LitBench` 的意义非常大，因为你未来如果要引入 LLM judge，就必须面对 judge 是否真的对齐人类编辑偏好这一问题。`LitBench` 给你的不是商业 fiction 任务定义，而是一套 judge validation 的方法论。

### 3.6.15 Ying et al. 2025, arXiv 预印本

论文：[`Beyond Correctness: Evaluating Subjective Writing Preferences Across Cultures`](https://arxiv.org/abs/2510.14616)  
Venue：截至 `2026-04-06`，当前可核实来源为 arXiv 预印本，未在官方页面标出正式会议/期刊版本  
核心对象：`WritingPreferenceBench`，跨文化主观写作偏好评测

这篇工作非常值得你认真看，因为它几乎直接证明了“主观写作偏好不能被客观正确性替代”。作者构建了 `WritingPreferenceBench`，包含 1,800 对人工偏好样本，覆盖 8 类创意写作题材，并且故意控制了 objective correctness、factual accuracy 和长度，使模型无法靠“谁错得少”这种廉价信号来作弊。结果是，标准序列式 reward model 与零样本 judge 的表现都很差，而带显式推理链的 generative reward model 反而显著更强。它想解决的问题是：现有偏好学习方法可能只会识别客观错误，却学不会真正的主观审美或创意偏好。与 `MarketFictionBench` 的关系尤其紧密，因为你要做的正是主观、市场化、跨语言的写作偏好评测。不同点在于，它更广泛地覆盖创意写作偏好，而你的方向会进一步收窄到商业小说与 acquisition preference。

### 3.6.16 Li et al. 2026, arXiv 预印本

论文：[`Lost in Stories: Consistency Bugs in Long Story Generation by LLMs`](https://arxiv.org/abs/2603.05890)  
Venue：截至 `2026-04-06`，当前可核实来源为 arXiv 预印本，未在官方页面标出正式会议/期刊版本  
核心对象：`ConStory-Bench` 与 `ConStory-Checker`

这篇工作几乎可以被看作长篇故事生成评测里对“一致性问题”最直接的一次聚焦。论文指出，随着模型开始能产出数万词的叙事文本，最严重的问题不再只是文风平不平、情节有没有亮点，而是模型会忘记自己刚刚写过什么，从而在人物设定、世界规则、时间顺序、事实描述等方面出现大量自相矛盾。为此，作者提出 `ConStory-Bench`，包含 2,000 个 prompt、4 类任务场景、5 大类一致性错误和 19 个细分类，还配套了能给出文本证据的自动检查器 `ConStory-Checker`。这项工作对 `MarketFictionBench` 的直接启发是：`B4/B5` 绝不能只靠人类印象打分，必须有明确的一致性 gate 和错误 taxonomy。它与商业性无关，但它补足了“中篇生成为什么会失控”的结构性解释。

## 4. 为什么“商业性”必须被重新定义，而不是沿用模糊直觉

“商业性”这个词最容易失控，因为不同人会把它理解成完全不同的东西。

### 4.1 三种常见但不够用的定义

第一种定义是“好看就商业”。

问题是：

- 好看是泛化的主观词
- 在不同市场中不稳定
- 不能直接转成标注协议

第二种定义是“热度高就商业”。

问题是：

- 热度是结果，不是纯作品质量
- 会受分发、作者基础、平台策略影响
- 不适合作为公开 benchmark 的主标签

第三种定义是“编辑觉得可能卖”。

这已经接近正确，但仍然不够，因为编辑的判断也需要被结构化。

### 4.2 对这个 benchmark 更可操作的定义

在 `MarketFictionBench` 中，更可操作的“商业性”应该定义为：

> 在给定 `target_market_slot`、`genre_family` 和 `length_band` 的前提下，一篇生成作品是否更容易触发编辑式继续投入决策，包括签约、追读、开发和传播潜力判断。

这个定义有三个关键好处：

- 它显式依赖 `market slot`，避免跨平台混淆
- 它允许“商业性”被拆解成子轴，而不是黑箱总分
- 它自然支持 pairwise acquisition preference

## 5. 为什么 v1 应该先做“纯小说”，而不是把诗歌也一起做

你在最初设想里提到过：可以考虑诗歌等非小说题材，但仍聚焦 creative writing。

这个方向没有问题，但不适合做 v1 主体，原因如下。

### 5.1 小说与诗歌在目标函数上不共享

商业小说更关注：

- hook
- pacing
- serial momentum
- character pull
- payoff

而诗歌更可能关注：

- 韵律
- 意象
- 压缩表达
- 风格辨识

这两者不能共用同一套主榜标准。

### 5.2 小说更适合复用当前仓库资产

当前仓库本身就是小说评测系统。你最强的积累在：

- 商业小说语言
- 连载逻辑
- 类型化 lens

如果 v1 一上来把诗歌硬并进来，反而会稀释你最独特的优势。

### 5.3 更好的处理方式

因此更合理的分层是：

- `v1`: 纯小说
- `v2 extension`: 诗歌、短剧、非小说创意写作

这样既保留了扩展空间，也不破坏 v1 的清晰度。

## 6. MarketFictionBench 的核心设计原则

### 6.1 原则一：主榜必须是偏好排序，不是单一绝对分

主榜应该回答：

> 如果只能签一个 submission，应该签哪个？

而不是回答：

> 这篇文章是 82 分还是 85 分？

前者更接近真实决策，后者更容易受评分漂移影响。

### 6.2 原则二：诊断层必须可解释

虽然主榜不靠单一总分，但你仍然需要诊断层来回答：

- 为什么这个模型赢了
- 它赢在什么题材
- 它输在什么长度
- 它是 hook 强，还是结构稳，还是市场适配更高

因此，8 轴与 4-lens 不能被丢掉。

### 6.3 原则三：outline 是强制信号，不是可选附件

如果没有 outline：

- 你会损失 planning ability 的可见性
- 你会损失 consistency 检查
- 你会损失“模型是不是先想清楚再写”的信号

所以 `outline + story` 必须是正式 submission contract 的一部分。

### 6.4 原则四：长度必须分档，但不能让“长”本身成为目标

你已经明确不想做超长篇，这是对的。

真正有用的设计不是：

- 谁能硬写得最长

而是：

- 在不同真实可用长度档位下，模型能否稳定写出更商业的作品

### 6.5 原则五：市场语境必须显式化

如果不显式建模 `target_market_slot`，那么：

- 中文女频
- 中文男频
- 英文 digital serial
- 英文 trade commercial
- YA crossover

会被混成一个含糊的“商业小说”，导致标注噪声非常大。

## 7. 详细方案：MarketFictionBench v1

### 7.1 目标对象

`MarketFictionBench` v1 面向的是：

- 纯小说
- 中英双语
- 短篇到中篇
- 生成任务
- 商业性主导的评估协议

### 7.2 公开语言

- `zh`
- `en`

### 7.3 公开 genre family

- `romance`
- `progression_fantasy`
- `mystery_thriller_horror`
- `science_fiction_apocalypse`
- `historical_adventure`
- `urban_contemporary`

### 7.4 与当前仓库类型映射

| 当前类型 | 新 genre family | 说明 |
| --- | --- | --- |
| `female_general` | `romance` | 保留关系驱动与情绪钩子 |
| `fantasy_upgrade` | `progression_fantasy` | 与升级流直接兼容 |
| `game_derivative` | `progression_fantasy` | 并入 litrpg / progression fantasy |
| `suspense_horror` | `mystery_thriller_horror` | 扩展为悬疑/惊悚/恐怖一体 |
| `sci_fi_apocalypse` | `science_fiction_apocalypse` | 基本直接映射 |
| `history_military` | `historical_adventure` | 对外命名更双语友好 |
| `urban_reality` | `urban_contemporary` | 更通用，也更方便英文扩展 |
| `general_fallback` | 不公开 | 仅作内部兜底 |

### 7.5 长度档位

- `B1 = 1k`
- `B2 = 3k`
- `B3 = 10k`
- `B4 = 50k`
- `B5 = 100k`

这里的 `1k / 3k / 10k / 50k / 100k` 是公开口径。内部实际比较时建议统一按 token 等价值换算。

原因很简单：

- 中文按字
- 英文按词
- 二者直接硬比长度不公平

### 7.6 生成协议

#### B1 / B2

- 单次生成
- 输出简版 outline
- 输出完整 story

#### B3

- `plan-then-write`
- 先 outline
- 再分 `3-5` 段生成正文

#### B4 / B5

- `episodic_generation`
- 总纲
- 章节表
- 逐章生成
- rolling memory card

这个设计的核心思想是：

> B4 / B5 测的是中篇写作能力，而不是超长上下文硬堆能力。

### 7.7 brief 固定字段

每条 brief 固定包含：

- `language`
- `genre_family`
- `target_market_slot`
- `length_band`
- `premise`
- `core_conflict`
- `must_have_elements`
- `forbidden_cliches`
- `tone_style`
- `ending_requirement`

这里最关键的是：

- `target_market_slot`

建议固定在下面几个枚举里开始：

- `CN_web_serial_female`
- `CN_web_serial_male`
- `EN_digital_serial`
- `EN_trade_commercial`
- `YA_crossover`

## 8. 为什么主榜应使用 Pairwise Acquisition Preference

### 8.1 绝对分的问题

如果你让评委直接打一个总分，会遇到这些问题：

- 不同评委对中间档边界不一致
- 不同语言、不同 genre 下总分含义漂移
- 文风偏好容易污染商业判断

### 8.2 Pairwise 的优势

如果问题改成：

> 如果只能签一篇，你签哪篇？

会有几个明显好处：

- 更接近真实编辑行为
- 更稳定
- 更适合做 Elo 或胜率统计
- 更适合后续训练 judge

### 8.3 主榜建议

主榜指标固定为：

- `Commercial Preference Rate`
- `Elo`

### 8.4 诊断榜建议

诊断榜展示：

- 8 轴均值
- genre-specific 4-lens
- 质量闸门通过率
- 按语言 / genre / band / market slot 的切片表现

这样排行榜不会只给一个“谁更强”的粗结论，而能回答“为什么更强”。

## 9. 诊断层：8 轴与 4-lens 如何保留

### 9.1 8 轴继续保留

这 8 个轴是当前仓库最值得迁移的核心资产。

#### `hookRetention`

开篇抓力与持续阅读驱动力。

- `B1/B2` 看读完冲动
- `B3-B5` 看开局后能否继续拉读者往下读

#### `serialMomentum`

连载推进力。

- `B1/B2` 看“读完后想不想看后续”
- `B3-B5` 看多段、多章推进张力

#### `characterDrive`

角色能否自己牵引阅读，而不是纯功能角色。

#### `narrativeControl`

叙事组织、信息分配与整体稳定性。

#### `pacingPayoff`

节奏安排与阶段性兑现。

#### `settingDifferentiation`

设定、世界、行业、规则或生活图景的差异化与可持续产出能力。

#### `platformFit`

建议对外改写成：

- `market slot fit`

这是“适不适合目标市场”，不是“我个人喜不喜欢”。

#### `commercialPotential`

这是总商业化潜力，不是文学性总分。它更接近：

- 编辑继续投入意愿
- 读者追读潜力
- 开发与传播空间

### 9.2 4-lens 用 bilingual remap 而不是照抄现有中文标签

建议每个 genre family 固定 4 个 lens，保持与当前项目结构兼容。

#### romance

- `emotion_hook`
- `relationship_charge`
- `emotional_payoff`
- `fandom_carryover`

#### progression_fantasy

- `progression_loop`
- `system_legibility`
- `reward_density`
- `spectacle_payoff`

#### mystery_thriller_horror

- `mystery_hook`
- `clue_fairness`
- `tension_sustain`
- `reveal_payoff`

#### science_fiction_apocalypse

- `concept_utility`
- `rule_closure`
- `pressure_system`
- `world_expansion`

#### historical_adventure

- `historical_texture`
- `faction_map`
- `strategy_payoff`
- `saga_momentum`

#### urban_contemporary

- `reality_hook`
- `aspiration_tension`
- `setting_credibility`
- `conversion_hook`

## 10. 数据组织与正式 Contract

一个公开 benchmark 不只是“有 brief 和文本”，还必须有清晰 contract。

### 10.1 四类核心对象

建议固定四种正式对象：

1. `brief`
2. `submission`
3. `expert_rating`
4. `pairwise_preference`

### 10.2 `brief`

用于定义任务本身。

它不应包含某个参考答案，而应包含：

- 题材与市场约束
- 长度约束
- 必须元素
- 禁止 cliché
- 结尾要求

### 10.3 `submission`

用于定义模型实际输出。

固定要求：

- `outline`
- `story`

对 `B4/B5` 额外要求：

- `chapter_plan`
- `rolling_memory_cards`

### 10.4 `expert_rating`

用于承载绝对评分层：

- 8 轴
- 4-lens
- `greenlight_decision`
- `overall_summary`
- `market_fit_summary`
- `reason_tags`

### 10.5 `pairwise_preference`

用于承载主榜信号：

- 左右 submission
- winner
- confidence
- rationale
- reason tags

## 11. 标注协议：什么样的人类评价才有用

### 11.1 评分人的角色定位

评分人不是文学评论家，也不是纯语言标注员。更理想的是：

- 小说编辑
- 内容策略
- 有对应 market slot 长期阅读经验的资深作者/读者

### 11.2 标注顺序

每条 submission 固定流程：

1. 读 brief
2. 读 outline
3. 读 story
4. 做 8 轴评分
5. 做 4-lens 评分
6. 做 `greenlight_decision`
7. 写 `market_fit_summary`
8. 标 `reason_tags`

之后再进入 pairwise。

### 11.3 评分人必须避免的三类误差

第一类误差：

- 用个人文学偏好覆盖 benchmark 目标

第二类误差：

- 把长度自动当作加分项

第三类误差：

- 把语言表层习惯差异误当成严重质量错误

### 11.4 `greenlight_decision` 建议分档

- `pass`
- `borderline`
- `consider`
- `acquire`

这比简单“好/坏”更接近真实内容决策。

## 12. 自动指标应该怎么用，怎么不能用

### 12.1 自动指标能做什么

自动指标适合做质量闸门：

- 长度符合度
- 重复率
- 实体一致性
- 时间线一致性
- 明显 AI 腔 / stale formula 风险

### 12.2 自动指标不该做什么

自动指标不应该直接决定主榜排序，因为：

- creative writing 没有稳定 reference
- 商业性本质上是人类偏好驱动
- 很多自动分数会奖励“像训练集均值”，不奖励真正的 market fit

### 12.3 LLM judge 的位置

LLM judge 可以做：

- 扩展评测器
- 低成本预筛
- 解释生成辅助

但不能先当 gold。

建议门槛：

- 只有在 held-out 专家 pairwise 上达到至少 `0.65` 一致率后，才允许进入扩展层

## 13. 为什么这个方案比“再做一个通用写作 benchmark”更有新意

你的新意不能写成“我们做中英双语写作 benchmark”，因为这本身已经太宽、也太常见。

更可能成立的创新点是下面五条的组合：

### 13.1 商业 acquisition preference 主榜

这是与大量通用写作 benchmark 的最大差别之一。

### 13.2 `target_market_slot` 显式化

不是做模糊“商业性”，而是做具体市场下的商业性。

### 13.3 `outline + story` 联合评估

大纲不是附件，而是正式 contract。

### 13.4 短篇到中篇分档

不是只做短故事，也不是盲目追求超长篇。

### 13.5 repo-compatible diagnostics

把当前仓库的 8 轴与 4-lens 沉淀为公开诊断层，而不是让它们停留在单产品内部。

如果最终论文或项目说明要写 novelty，建议围绕这五条展开，而不是围绕“小说”“双语”“长文本”这些已经有很多邻近工作的词。

## 14. Pilot 应该怎么做

### 14.1 为什么先做 pilot

因为写作 benchmark 最容易失败的地方不是模型，而是协议本身：

- 标注人是否能稳定判断
- 不同语言是否公平
- 长档协议是否真的可执行
- 你设计的 8 轴是否真的和人类偏好相关

### 14.2 推荐的 pilot 规模

先做：

- `2 languages`
- `3 genres`
- `5 length bands`
- `1 brief per cell`

即 `30 briefs`

先覆盖：

- `romance`
- `progression_fantasy`
- `mystery_thriller_horror`

这是合理的，因为这三类：

- 差异足够大
- 商业判断相对鲜明
- 容易暴露协议问题

### 14.3 pilot 的四个验证目标

1. 专家 pairwise 一致性
2. `zh / en` 跨语言公平性
3. `B4 / B5` 章节协议稳定性
4. 8 轴与商业偏好的相关性

### 14.4 接受标准

- 专家 pairwise 原始一致率 `>= 0.70`
- held-out 上 LLM judge 一致率 `>= 0.65` 才能进入扩展层
- 每个语言 / genre / band 至少都有清晰高低分样本

### 14.5 如果 pilot 失败，先改什么

如果一致性不足，优先调整：

- market slot 定义
- 评分说明
- genre 范围

而不是先扩大数据量。

如果 `B4/B5` 失控，优先把它们降为扩展轨，而不是强行保主榜。

## 15. 正式版 v1 应该长什么样

### 15.1 规模

- `2 languages`
- `6 genres`
- `5 bands`
- `4 briefs per cell`

总计：

- `240 briefs`

### 15.2 每条 brief 下的 submission 数量

正式提交阶段，你可以根据参赛模型数量自然增长。但如果是内部研究阶段，建议至少保证：

- 每条 brief 有多个系统产出
- 能支撑稳定 pairwise 比较

### 15.3 Leaderboard 切片

主榜之外，建议固定切片榜：

- `overall`
- `zh only`
- `en only`
- `short-form` (`B1/B2`)
- `mid-form` (`B3/B4/B5`)
- `romance`
- `progression_fantasy`
- `mystery_thriller_horror`
- `market-slot-specific`

这样能避免某个系统只靠某一类任务拉高总榜，却掩盖结构性弱点。

## 16. 版权与公开发布策略

这是做公开 benchmark 时非常关键、但常被忽视的部分。

### 16.1 建议公开什么

- 原始 brief
- schema
- 人工标签
- 模型输出
- 少量自写或明确授权参考文本

### 16.2 不建议公开什么

- 现代受版权保护小说全文
- 权限不清晰的网文整本正文

### 16.3 如果你想利用现有网文做校准

可以，但建议只进入：

- internal calibration set

不要进入公开 release。

这样既能吸收现实世界分布，又不把项目推进到版权高风险区。

## 17. 这个方案与当前仓库的最佳协同方式

### 17.1 不建议现在就接入 `evals/`

因为当前 `evals/` 是产品回归 harness，而不是研究 benchmark 工作区。

### 17.2 更合理的组织方式

建议保持：

- `creative-writing-benchmark/`
  独立承载综述、规范、schema、pilot、样例

等 pilot 与 contract 稳定后，再选择是否把其中部分接到：

- `apps/worker`
- `evals/`
- 或单独的 benchmark runner

### 17.3 哪些现有资产最适合后续复用

- 8 轴定义
- 4-lens 思路
- `screening`
- `consistency`
- `aggregation` 的解释语言

这些都可以成为未来 `LLM judge` 或自动预评估器的基础。

## 18. 最终判断：你到底该做什么

如果把所有信息压缩成一个明确行动建议，那么就是：

### 18.1 不要做什么

- 不要做“泛写作能力大而全 benchmark”
- 不要先把诗歌、剧本、散文全部并入
- 不要把“超长输出”当成核心卖点
- 不要直接复用当前产品的单一总分做主榜

### 18.2 应该做什么

做一个下面定义非常清晰的 benchmark：

> 一个面向 `commercial fiction` 的中英双语 benchmark，要求模型基于标准化 `brief` 生成 `outline + story`，覆盖 `B1/B2/B3/B4/B5` 五个长度档，以 `专家 pairwise acquisition preference` 为主榜，以 `8 轴 + genre-specific 4-lens` 为诊断榜，并通过 `target_market_slot` 把商业性从模糊概念变成可标注、可比较、可解释的结构化评测问题。

这件事比“再做一个写作 benchmark”更窄，但也更锋利。它更有机会真正形成自己的问题定义。

## 19. 参考来源

以下链接用于支撑本综述中对现有工作的分类与定位判断：

- [WritingPrompts: Building a Dataset for Reading Comprehension and Character-based Story Generation](https://aclanthology.org/P18-1082/)
- [A Corpus and Cloze Evaluation for Deeper Understanding of Commonsense Stories](https://aclanthology.org/N16-1098/)
- [MTG](https://arxiv.org/abs/2108.07140)
- [LOT](https://arxiv.org/abs/2108.12960)
- [StoryER](https://aclanthology.org/2022.emnlp-main.114/)
- [STORYWARS](https://arxiv.org/abs/2305.08152)
- [LongWriter: Unleashing 10,000+ Word Generation from Long Context LLMs](https://arxiv.org/abs/2408.07055)
- [WebNovelBench: Placing LLM Novelists on the Web Novel Distribution](https://arxiv.org/abs/2505.14818)
- [LitBench](https://arxiv.org/abs/2507.00769)
- [Towards A “Novel” Benchmark](https://aclanthology.org/2025.findings-acl.1114/)
- [WritingPreferenceBench](https://arxiv.org/abs/2510.14616)
- [ConStory-Bench / Lost in Stories](https://arxiv.org/abs/2603.05890)


