# 生成  回答的 (标题, 话题标签，一二级 分类标签 ) 摘要 的pair对
import os,sys

from searchSql import *

os.chdir(sys.path[0])
sys.path.append("../../../")

from CommonOperate.tool import Tool
from pyhive import hive
import json
from tqdm import tqdm

def get_summary_pair():
    summary_pair = []

    summarys = []
    with hive.connect(host="hive-adhoc.tsn01.rack.zhihu.com",
                      port=10000,
                      auth='NOSASL',
                      username='km_km',
                      password=os.environ['HADOOP_USER_PASSWORD'],
                      configuration={"mapreduce.job.queuename": 'km_rec_tsn_vip',
                                     "hive.exec.reducers.bytes.per.reducer": "81920000"}) as conn:
        with conn.cursor() as cur:
            # 查询
            cur.execute(getAnswerSummary)
            answerRes = cur.fetchall()
            print("AnswerRes=",len(answerRes))
            cur.execute(getArticleSummary)
            articleRes = cur.fetchall()
            print("articleRes=",len(articleRes))
            res = articleRes+answerRes
            for result in res:
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
                        summarys.append(data)


    if len(summarys) > 0:
        for summaryInfo in  tqdm(summarys, "summary_pair"):
            question_title = ''
            if len(summaryInfo['question_title']) > 0:
                question_title = summaryInfo['question_title']

            topic_names = []
            if len(summaryInfo['topic_name_set']) > 0:
                topic_names = summaryInfo['topic_name_set']

            content = ''
            if len(summaryInfo['content']) > 0:
                content = Tool.clean_text(summaryInfo['content'])


            text = content[:128]
            if len(text) < 8:
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
                    'q': query.lower(),
                    't': text.lower(),
                }
                summary_pair.append(pair)

        summary_pair_len = len(summary_pair)
        print("len(summary_pair)=",summary_pair_len)
        print(summary_pair[0])
        print(summary_pair[-1])
        exit(0)
        with open("/home/jeeves/bert_white_json/summary_pair.json", "a", encoding="utf-8") as f:
            for index, summary in enumerate(summary_pair):
                if index == summary_pair_len - 1:
                    f.write(json.dumps(summary, ensure_ascii = False))
                else:
                    f.write(json.dumps(summary, ensure_ascii = False) + "\n")

        print("加载入文件完成...")

if __name__ == '__main__':
    get_summary_pair()
