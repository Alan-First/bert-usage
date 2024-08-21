# 生成  回答的 (标题, 话题标签，一二级 分类标签 ) 正文 的pair对
import os,sys
import configparser

from searchSql import *

os.chdir(sys.path[0])
sys.path.append("../../../")

from CommonOperate.tool import Tool
from pyhive import hive
from tqdm import tqdm
import json

def get_content_info_pair():
    content_info_pairs = []
    # print("os.environ['HADOOP_USER_PASSWORD']=",os.environ['HADOOP_USER_PASSWORD'])
    Contents = []
    with hive.connect(host="hive-adhoc.tsn01.rack.zhihu.com",
                      port=10000,
                      auth='NOSASL',
                      username='km_km',
                      password=os.environ['HADOOP_USER_PASSWORD'],
                      configuration={"mapreduce.job.queuename": 'km_rec_tsn_vip',
                                     "hive.exec.reducers.bytes.per.reducer": "81920000"}) as conn:

        with conn.cursor() as cur:
            # 查回答
            cur.execute(getAnswerContent)
            AnswerRes = cur.fetchall()
            print("AnswerRes=",len(AnswerRes))
            # 查文章
            cur.execute(getArticleContent)
            ArticleRes = cur.fetchall()
            print("ArticleRes=",len(ArticleRes))
            Res = ArticleRes+AnswerRes
            for result in Res:
                """
                ('考金融专硕什么时候准备？', 
                '["金融硕士","金融专硕431","金融考研","431金融专硕","431"]', 
                '考研界一直流传着一个传说：得暑假者得天下。我当年考金融专硕（金融 431）时，非常谨慎地讨教了各大神的备考方法，
                做出了适合自己的暑假复习规划，最后考上了，下面将这份经验总结了分享给大家...。原文作者：狗狗', 
                '["金融","教育"]', '["考研","金融学","高校教育"]')
                """
                if len(result) > 0:
                    data = {
                        'question_title' : '',
                        'topic_name_set' : [],
                        'content' : '',
                    }

                    if result[0] is not None and len(result[0]) > 0 :
                        data['question_title'] = result[0]

                    if result[1] is not None and len(result[1]) > 0 :
                        data['topic_name_set'] = list(eval(result[1]))

                    if result[2] is not None and len(result[2]) > 0 :
                        data['content'] = result[2]

                    if len(data['content']) > 0 and (len(data['question_title']) > 0 or len(data['topic_name_set']) > 0):
                        Contents.append(data)

    if len(Contents) > 0:
        for answerContentInfo in tqdm(Contents, "content_info_pair"):
            question_title = ''
            if len(answerContentInfo['question_title']) > 0:
                question_title = answerContentInfo['question_title']

            topic_names = []
            if len(answerContentInfo['topic_name_set']) > 0:
                topic_names = answerContentInfo['topic_name_set']

            content = ''
            if len(answerContentInfo['content']) > 0:
                content = Tool.clean_text(answerContentInfo['content'])

            text = content[:128]
            if len(text) < 16:
                print(text)
                continue

            querys = []
            if len(question_title) > 0:
                question_title = Tool.clean_text(question_title)
                querys.append(question_title)

            if len(topic_names) > 0 :
                for topic_name in topic_names:
                    querys.append(topic_name)

            querys = list(set(querys))

            for query in  querys:
                pair = {
                    'q' : query.lower(),
                    't' : text.lower(),
                }

                content_info_pairs.append(pair)

        content_info_pairs_len = len(content_info_pairs)
        """{'q': '(非全)公共管理硕士 mpa 到底难不难考?', 't': '小马过河,问水深不深?mpa 难不难考核心还得看这 3 点:考试难度、院校难度、自身水平,下面我展开讲讲,看完你就有答案了~
        一、初试的难度等级总体来说:初试知识点难度相较于学硕较低,国家线划线也不高.1.国家线:近 6 年的国家线中 22 年最高 178,'}"""
        print("len(content_info_pairs)=",content_info_pairs_len)
        print(content_info_pairs[0])
        print(content_info_pairs[-1])
        exit(0)

        with open("/home/jeeves/bert_white_json/content_info_pairs.json", "a", encoding="utf-8") as f:
            for index, content_info_pair in enumerate(content_info_pairs):
                if index == content_info_pairs_len - 1:
                    f.write(json.dumps(content_info_pair, ensure_ascii = False))
                else:
                    f.write(json.dumps(content_info_pair, ensure_ascii = False) + "\n")

        print("加载入文件完成...")

if __name__ == '__main__':
    get_content_info_pair()
