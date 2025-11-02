# KBQA-for-Diagnosis
复现B站up主的知识图谱项目
该up主的项目链接为：[基于知识图谱的智能问答项目实战](https://www.bilibili.com/video/BV1ev4y1o7zj?spm_id_from=333.788.videopod.episodes&vd_source=112a88f398e914a30d62b5b6a2266e5f)


整个项目的复现不去运行整个项目，而是尝试code所有代码从而来学习知识图谱的构造。目标：尝试使用最短的时间去做复现项目。

### 实现步骤：
1. 数据准备阶段  
    首先需要准备医疗知识数据和预训练模型:
    * 下载疾病数据(JSON格式的医疗知识数据)
    * 下载BERT预训练模型(RBT3中文版本) README.MD:68-71
    * 下载意图识别模型文件 README.MD:58-66
2. 知识图谱构建  
    实现知识图谱的构建模块:
    * build_kg/build_kg_utils.py - 定义MedicalExtractor类,负责从JSON数据中提取三元组并写入Neo4j build_kg_utils.py:24-62
    * 实现节点写入方法write_nodes()和关系写入方法write_edges() build_kg_utils.py:178-2013. 命名实体识别(NER)服务实现疾病实体识别功能:
    * knowledge_extraction/bilstm_crf/ - BiLSTM-CRF模型用于实体识别
    * 准备疾病实体字典checkpoint/diseases.json README.MD:46
    * 实现NER服务接口service.py
4. 意图识别服务  
    实现用户查询意图分类:
    * nlu/bert_intent_recognition/app.py - BERT意图识别服务
    * 配置预训练模型路径 README.MD:71
5. 配置文件  
    定义语义槽和查询模板:
    * config.py - 定义各种意图的槽位列表、CQL查询模板、回复模板等 config.py:3-118
6. 实体标准化(可选)  
    如果需要实体链接功能:
    * entity_normalization/bm25_retrival.py - BM25检索模块 bm25_retrival.py:9-30
    * entity_normalization/predict.py - 实体匹配预测 predict.py:17-52
7. 核心问答模块  
    实现问答逻辑:
    * modules/ - 包含gossip_robot(闲聊机器人)、medical_robot(医疗问答机器人)、classifier(意图分类器)等模块
8. 微信接口  
    最后实现用户交互界面:  
    * itchat_app.py - 微信接口,整合所有模块 itchat_app.py:1-60启动顺序实现完成后,按以下顺序启动服务:
        1. 启动Neo4j数据库 README.MD:73-91
        2. 启动意图识别服务(run_intent_recog_service.bat) 
        3. 启动NER服务(run_ner_service.bat) 
        4. 启动微信接口(python itchat_app.py) 
#### Notes
这个项目的核心流程是:用户输入→意图识别→实体提取→知识图谱查询→返回答案 itchat_app.py:12-28 。建议先完成知识图谱构建和基础NLU模块,再实现上层应用逻辑。当前版本使用JSON文件存储对话上下文,生产环境建议使用Redis README.MD:44 。
