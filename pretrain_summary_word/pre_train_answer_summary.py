#coding:utf-8
import os,sys
os.chdir(sys.path[0])
sys.path.append("../")
sys.path.append("../../")
sys.path.append("/local/apps/edu-bert4search")
# pip install beautifulsoup4
# pip install opencc-python-reimplemented
from CommonOperate.tool import Tool

if sys.version_info >= (3, 0):
    import locale

    locale.getpreferredencoding()

from pyhive import hive


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
        cur.execute('''SELECT summary_content FROM km_rec.edu_content_summary_pt''')
        for result in cur.fetchall():
            if len(result) > 0:
                summarys.append(result[0])

pretraining_data_dir = "../prepare_data"


with open(pretraining_data_dir + f"./preTrain_summary_raw.txt", 'w', encoding='utf-8') as f:
    for summary in summarys:
        if summary is not None:
            textMergeList = Tool.processText2Group4Summary(summary)
            for item in textMergeList:
                f.write(item + "\n")
            f.write("\n")
