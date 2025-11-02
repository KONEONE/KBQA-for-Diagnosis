import os
import re
import json
import codecs
import threading
from py2neo import Graph
import pandas as pd
import numpy as np
from tqdm import tqdm


class MedicalExtractor(object):
    def __init__(self):
        super(MedicalExtractor, self).__init__()
        # neo4j client
        self.graph = Graph(host='127.0.0.1',http_port=7474,user='neo4j',password='123456')
        # 8类实体
        self.drugs = []         # 药品
        self.recipes = []       # 菜谱
        self.foods = []         # 食物
        self.checks = []        # 检查
        self.departments = []   # 科室
        self.producers = []     # 药企
        self.diseases = []      # 疾病
        self.symptoms = []      # 症状
        self.disease_infos = [] # 疾病信息
        # 11种关系
        self.rels_department = []       # 科室－科室 关系
        self.rels_noteat = []           # 疾病－忌吃食物 关系
        self.rels_doeat = []            # 疾病－宜吃食物 关系
        self.rels_recommandeat = []     # 疾病－推荐吃食物 关系
        self.rels_commonddrug = []      # 疾病－通用药品 关系
        self.rels_recommanddrug = []    # 疾病－热门药品 关系
        self.rels_check = []            # 疾病－检查 关系
        self.rels_drug_producer = []    # 厂商－药物 关系
        self.rels_symptom = []          # 疾病-症状 关系
        self.rels_acompany = []         # 疾病-并发 关系
        self.rels_category = []         # 疾病-科室 关系
    
    # pyneo 执行
    def exe_cql(self, cql:str):
        try:
            self.graph.run(cql)
        except Exception as e:
            print(f'Exception: {e}\n\nCQL: {cql}')

    # disease 实体 初始化
    def init_disease(self):
        disease_dict = {}
        disease_dict['name'] = ''
        disease_dict['desc'] = ''
        disease_dict['prevent'] = ''
        disease_dict['cause'] = ''
        disease_dict['easy_get'] = ''
        disease_dict['cure_department'] = ''
        disease_dict['cure_way'] = ''
        disease_dict['cure_lasttime'] = ''
        disease_dict['symptom'] = ''
        disease_dict['cured_prob'] = ''
        return disease_dict
    # 三元组 解析
    def extract_triples(self, data_path):
        lines = []
        with open(data_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in tqdm(lines, ncols=80):
            data_json = json.loads(line)
            disease_dict = self.init_disease()       # 疾病
            disease = data_json['name']
            self.diseases.append(disease)
            disease_dict['name'] = disease

            # disease2symptom
        if 'symptom' in data_json:
            self.symptoms += data_json['symptom']
            for symptom in data_json['symptom']:
                self.rels_symptom.append([disease,'has_symptom', symptom])
            # disease2acompany
            if 'acompany' in data_json:
                for acompany in data_json['acompany']:
                    self.rels_acompany.append([disease,'acompany_with', acompany])
                    self.diseases.append(acompany)
            # disease2desc
            if 'desc' in data_json:
                disease_dict['desc'] = data_json['desc']
            # disease2prevent
            if 'prevent' in data_json:
                disease_dict['prevent'] = data_json['prevent']
            # disease2cause
            if 'cause' in data_json:
                disease_dict['cause'] = data_json['cause']
            # disease2get_prob
            if 'get_prob' in data_json:
                disease_dict['get_prob'] = data_json['get_prob']

            # disease2easy_get
            if 'easy_get' in data_json:
                disease_dict['easy_get'] = data_json['easy_get']

            # disease2cure_department
            if 'cure_department' in data_json:
                cure_department = data_json['cure_department']
                if len(cure_department) == 1:
                        self.rels_category.append([disease, 'cure_department',cure_department[0]])
                if len(cure_department) == 2:
                    big = cure_department[0]
                    small = cure_department[1]
                    self.rels_department.append([small,'belongs_to', big])
                    self.rels_category.append([disease,'cure_department', small])

                disease_dict['cure_department'] = cure_department
                self.departments += cure_department
            # disease2cure_way
            if 'cure_way' in data_json:
                disease_dict['cure_way'] = data_json['cure_way']

            # disease2cure_lasttime
            if  'cure_lasttime' in data_json:
                disease_dict['cure_lasttime'] = data_json['cure_lasttime']

            # disease2cured_prob
            if 'cured_prob' in data_json:
                disease_dict['cured_prob'] = data_json['cured_prob']

            # disease2common_drug
            if 'common_drug' in data_json:
                common_drug = data_json['common_drug']
                for drug in common_drug:
                    self.rels_commonddrug.append([disease,'has_common_drug', drug])
                self.drugs += common_drug
            # disease2recommand_drug
            if 'recommand_drug' in data_json:
                recommand_drug = data_json['recommand_drug']
                self.drugs += recommand_drug
                for drug in recommand_drug:
                    self.rels_recommanddrug.append([disease,'recommand_drug', drug])

            # disease2not_eat
            if 'not_eat' in data_json:
                not_eat = data_json['not_eat']
                for _not in not_eat:
                    self.rels_noteat.append([disease,'not_eat', _not])

                self.foods += not_eat
                do_eat = data_json['do_eat']
                for _do in do_eat:
                    self.rels_doeat.append([disease,'do_eat', _do])

                self.foods += do_eat
            # disease2recommand_eat
            if 'recommand_eat' in data_json:
                recommand_eat = data_json['recommand_eat']
                for _recommand in recommand_eat:
                    self.rels_recommandeat.append([disease,'recommand_recipes', _recommand])
                self.recipes += recommand_eat
            # disease2check
            if 'check' in data_json:
                check = data_json['check']
                for _check in check:
                    self.rels_check.append([disease, 'need_check', _check])
                self.checks += check
            # disease2drug_detail
            if 'drug_detail' in data_json:
                for det in data_json['drug_detail']:
                    det_spilt = det.split('(')
                    if len(det_spilt) == 2:
                        p,d = det_spilt
                        d = d.rstrip(')')
                        if p.find(d) > 0:
                            p = p.rstrip(d)
                        self.producers.append(p)
                        self.drugs.append(d)
                        self.rels_drug_producer.append([p,'production',d])
                    else:
                        d = det_spilt[0]
                        self.drugs.append(d)

            self.disease_infos.append(disease_dict)
    
    # 创建-节点
    def write_node(self, entitys, entity_type):
        entitys = set([e.replace("'", "") for e in entitys])
        for node in tqdm(entitys, ncols=80):
            cql = """
                MERGE(n:{label}{{name:'{entity_name}'}})
            """.format(label=entity_type, entity_name=node)
            self.exe_cql(cql)
    # 创建-边
    def write_edge(self, triples, head_type, tail_type):
        for head, relation, tail in tqdm(triples, ncols=80):
            cql = """
            MATCH (p:{head_type}),(q:{tail_type})
                WHERE p.name='{head}' AND q.name = '{tail}'
            MERGE (p)-[r:{relation}]->(q)
            """.format(
                head_type=head_type, tail_type=tail_type,
                head=head.replace("'",""), tail=tail.replace("'",""),
                relation=relation
            )
            self.exe_cql(cql)
    # 设置属性
    def set_attributes(self,entity_infos,etype):
        print("写入 {0} 实体的属性".format(etype))
        for e_dict in tqdm(entity_infos[892:],ncols=80):
            name = e_dict['name']
            del e_dict['name']
            for k,v in e_dict.items():
                if k in ['cure_department','cure_way']:
                    cql = """MATCH (n:{label})
                        WHERE n.name='{name}'
                        set n.{k}={v}""".format(label=etype,name=name.replace("'",""),k=k,v=v)
                else:
                    cql = """MATCH (n:{label})
                        WHERE n.name='{name}'
                        set n.{k}='{v}'""".format(label=etype,name=name.replace("'",""),k=k,v=v.replace("'","").replace("\n",""))
                self.exe_cql(cql)

    def create_entitys(self):
        self.write_nodes(self.drugs,'药品')
        self.write_nodes(self.recipes,'菜谱')
        self.write_nodes(self.foods,'食物')
        self.write_nodes(self.checks,'检查')
        self.write_nodes(self.departments,'科室')
        self.write_nodes(self.producers,'药企')
        self.write_nodes(self.diseases,'疾病')
        self.write_nodes(self.symptoms,'症状')

    def create_relations(self):
        self.write_edges(self.rels_department,'科室','科室')
        self.write_edges(self.rels_noteat,'疾病','食物')
        self.write_edges(self.rels_doeat,'疾病','食物')
        self.write_edges(self.rels_recommandeat,'疾病','菜谱')
        self.write_edges(self.rels_commonddrug,'疾病','药品')
        self.write_edges(self.rels_recommanddrug,'疾病','药品')
        self.write_edges(self.rels_check,'疾病','检查')
        self.write_edges(self.rels_drug_producer,'药企','药品')
        self.write_edges(self.rels_symptom,'疾病','症状')
        self.write_edges(self.rels_acompany,'疾病','疾病')
        self.write_edges(self.rels_category,'疾病','科室')

    def set_diseases_attributes(self): 
        # self.set_attributes(self.disease_infos,"疾病")
        t=threading.Thread(target=self.set_attributes,args=(self.disease_infos,"疾病"))
        t.setDaemon(False)
        t.start()


    def export_data(self,data,path):
        if isinstance(data[0],str):
            data = sorted([d.strip("...") for d in set(data)])
        with codecs.open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def export_entitys_relations(self):
        self.export_data(self.drugs,'./graph_data/drugs.json')
        self.export_data(self.recipes,'./graph_data/recipes.json')
        self.export_data(self.foods,'./graph_data/foods.json')
        self.export_data(self.checks,'./graph_data/checks.json')
        self.export_data(self.departments,'./graph_data/departments.json')
        self.export_data(self.producers,'./graph_data/producers.json')
        self.export_data(self.diseases,'./graph_data/diseases.json')
        self.export_data(self.symptoms,'./graph_data/symptoms.json')

        self.export_data(self.rels_department,'./graph_data/rels_department.json')
        self.export_data(self.rels_noteat,'./graph_data/rels_noteat.json')
        self.export_data(self.rels_doeat,'./graph_data/rels_doeat.json')
        self.export_data(self.rels_recommandeat,'./graph_data/rels_recommandeat.json')
        self.export_data(self.rels_commonddrug,'./graph_data/rels_commonddrug.json')
        self.export_data(self.rels_recommanddrug,'./graph_data/rels_recommanddrug.json')
        self.export_data(self.rels_check,'./graph_data/rels_check.json')
        self.export_data(self.rels_drug_producer,'./graph_data/rels_drug_producer.json')
        self.export_data(self.rels_symptom,'./graph_data/rels_symptom.json')
        self.export_data(self.rels_acompany,'./graph_data/rels_acompany.json')
        self.export_data(self.rels_category,'./graph_data/rels_category.json')
    

if __name__ == '__main__':
    path = './data/medical.json'
    extractor = MedicalExtractor()
    
