import os,sys
import configparser

from searchSql import *

os.chdir(sys.path[0])
sys.path.append("../../../")

from CommonOperate.tool import Tool
from pyhive import hive
from tqdm import tqdm
import json

def get_query_answer_summary_pair():
    query_summary_pair = []

    queryAnswerDoc = {}
    # 构建query样本对 answer
    with hive.connect(host="hive-adhoc.tsn01.rack.zhihu.com",
                      port=10000,
                      auth='NOSASL',
                      username='km_km',
                      password=os.environ['HADOOP_USER_PASSWORD'],
                      configuration={"mapreduce.job.queuename": 'km_rec_tsn_vip',
                                     "hive.exec.reducers.bytes.per.reducer": "81920000"}) as conn:
        with conn.cursor() as cur:
            # 查询
            print(getAnswerQueryContentId)
            cur.execute(getAnswerQueryContentId)
            AnswerRes = cur.fetchall()
            print("len(AnswerRes)=",len(AnswerRes))
            print(getArticleQueryContentId)
            cur.execute(getArticleQueryContentId)
            ArticleRes = cur.fetchall()
            print("len(ArticleRes)=",len(ArticleRes))
            Res = ArticleRes+AnswerRes
            for result in Res:
                if len(result) == 2:
                    query = ''
                    if result[0] is not None and len(result[0]) > 0 :
                        query = Tool.clean_text(result[0])

                    docId = 0
                    if result[1] is not None :
                        docId = int(result[1])

                    if query == '' or docId == 0:
                        continue

                    if query not in queryAnswerDoc:
                        queryAnswerDoc[query] = set()

                    queryAnswerDoc[query].add(docId)

            hashSummaryInfo = {}
            print(get_all_summary)
            cur.execute(get_all_summary)
            for SummaryInfo in cur.fetchall():
                if len(SummaryInfo) == 2:
                    answerId = 0
                    if SummaryInfo[0] is not None:
                        answerId = int(SummaryInfo[0])

                    if answerId == 0:
                        continue

                    content = ''
                    if SummaryInfo[1] is not None:
                        content = Tool.clean_text(SummaryInfo[1])

                    if content == '':
                        continue

                    text = content[:128]
                    if len(text) < 8:
                        #print(text)
                        continue

                    hashSummaryInfo[answerId] = {
                        'content': text,
                    }

    for query, docIds in tqdm(queryAnswerDoc.items(), "query_summary_pair") :
        for docId in docIds:
            if docId in hashSummaryInfo:
                content = hashSummaryInfo[docId]['content']
                query = Tool.clean_text(query)

                if len(content) > 0:
                    pair = {
                        'q': query.lower(),
                        't': content.lower(),
                    }
                    query_summary_pair.append(pair)

    query_summary_pair_len = len(query_summary_pair)
    print("len(summary_pair)=",query_summary_pair_len)
    print(query_summary_pair[0])
    print(query_summary_pair[-1])
    exit(0)
    with open("/home/jeeves/bert_white_json/query_summary_pair.json", "a", encoding="utf-8") as f:
        for index, query_summary in enumerate(query_summary_pair):
            if index == query_summary_pair_len - 1:
                f.write(json.dumps(query_summary, ensure_ascii=False))
            else:
                f.write(json.dumps(query_summary, ensure_ascii=False) + "\n")

    print("加载入文件完成...")

if __name__ == '__main__':
    get_query_answer_summary_pair()