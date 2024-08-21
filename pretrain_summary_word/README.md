

# 含义  
 用教育内容对bert模型做mlm训练


# 使用  
## 下载依赖  
1. 相应的python库  
`
pip install -q --upgrade numpy==1.19.5 tensorflow==2.15 beautifulsoup4==4.11.1 tqdm==4.64.0 jieba sasl thrift thrift-sasl zhihu-pyhive[hive]==0.6.2 -i http://mirror.in.zhihu.com/simple --trusted-host mirror.in.zhihu.com
`
2. 中文语料下的bert模型  
`
wget https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip
`  
**ps：在开发机安装完这些才能跑**

## 获取文本数据  
1. 代码  
`
python pretrain_summary_word/pre_train_answer_summary.py
`  
2. 功能：访问数据库，取出业务方的文本内容，是原始的文本数据  
3. 产出：txt文本文件，里面是业务方自己的所有文字内容，可以是教育内容所有文本内容的拼接，这里是教育所有摘要拼接而成，一行一个摘要  
4. 上面这个代码在开发机跑没问题，在平台可能缺点依赖，可以在开发机跑完把产出挪到hdfs上，让机器学习平台去访问，如下  
`
hdfs dfs -put /data1/home/zenghongwei/bert-sample/prepare_data/preTrain_summary_raw.txt /user/km_km/data/zrec/models/bert_usage/prepare_data
`



## 生成训练数据  
1. 代码：开发机代码,在开发机能跑  
` nohup python pretrain_summary_word/create_pretraining_data_zhihu_only_mlm.py  \
--input_file=./prepare_data/preTrain_summary_raw.txt \
--output_file=./prepare_data_tf/pre_data_article.tfrecord \
--vocab_file=./chinese_L-12_H-768_A-12/vocab.txt \
--max_seq_length=128 \
--max_predictions_per_seq=20 \
--masked_lm_prob=0.15 \
--random_seed=123456 \
--do_whole_word_mask=True \
--dupe_factor=5 > pre_data_article.out 2>&1 &`  
**开发机跑完直接把产出output_file的内容挪到hdfs做的mlm训练也行，前面的步骤不费gpu**
2. 将文本数据转换成mlm或者nsp「教育这边注释掉了nsp，业界经常这么干」可以用的样本，最终转化成tfrecord格式的训练数据  
3. 产出：某个.tfrecord文件 
4. 从下面开始就要gpu了，不能在开发机进行，这时候上面生成的大文件得先传到hdfs，机器学习平台才能访问到，具体就是自建个目录，把前面步骤生成的prepare_data、prepare_data_tf文件夹还有中文语料库chinese_L-12_H-768_A-12都put过去，「其实全git也行，就是文件太大了」  

## 做mlm训练
1. 代码：开发机代码，在开发机能跑，但是特别慢  
` nohup python pretrain_summary_word/run_pretraining_zhihu_only_mlm.py \
   --input_dir=./prepare_data_tf \
   --output_dir=./chinese_wwm_L-12_H-768-zhihu \
   --do_train=True \
   --do_eval=False \
   --bert_config_file=./chinese_L-12_H-768_A-12/bert_config.json \
   --init_checkpoint=./chinese_L-12_H-768_A-12/bert_model.ckpt \
   --train_batch_size=96 \
   --max_seq_length=128 \
   --max_predictions_per_seq=20 \
   --num_train_steps=210000 \
   --num_warmup_steps=1000 \
   --learning_rate=2e-5 > run_pretraining_zhihu_only_mlm 2>&1 &`  
2. 机器学习平台的代码， 
`
   python pretrain_summary_word/run_pretraining_zhihu_only_mlm.py \
   --input_dir=/mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data_tf \
   --output_dir=/data/models/chinese_wwm_L-12_H-768-zhihu \
   --do_train=True \
   --do_eval=False \
   --bert_config_file=/mnt/data/user/km_km/data/zrec/models/bert_usage/chinese_L-12_H-768_A-12/bert_config.json \
   --init_checkpoint=/mnt/data/user/km_km/data/zrec/models/bert_usage/chinese_L-12_H-768_A-12/bert_model.ckpt \
   --train_batch_size=56 \
   --max_seq_length=128 \
   --max_predictions_per_seq=20 \
   --num_train_steps=360000 \
   --num_warmup_steps=1000 \
   --learning_rate=2e-5
`  
**Q1：为啥input_dir、init_checkpoint、bert_config_file文件路径在mnt/data/？**  
**这是因为我没有把这些大文件打包到git上以免推拉代码太费时，而是把大文件放到了hdfs上，而为了让机器学习平台访问这些在hdfs的文件，python访问文件就要改成访问hdfs的代码格式，为了避免对代码做这种改动，我选择了访问这些hdfs文件的缓存挂载，路径开头是/mnt/data/user/，读取速度会比裸读快只是不能写**  
**Q2：output_dir为啥开头是/data/models?**  
**这是因为我需要把这个代码产出的文件挪到hdfs上，jeeves平台支持把产出挪到指定位置，但是产出的源位置必须在/data/models路径下**   
**图中的配置用2卡/16核/256G可以跑动**  
最后把机器学习平台产出的chinese_wwm_L-12_H-768-zhihu文件整个拷贝出来拷到跟prepare_data同级的位置下就好。  


## 如果模型要蒸馏，需要转成pytorch模型，因为蒸馏脚本模型是pytorch的  
本地可以执行以下命令  
`
python pretrain_summary_word/convert_bert_original_tf_checkpoint_to_pytorch.py --tf_checkpoint_path="../chinese_wwm_L-12_H-768-zhihu" --bert_config_file="../chinese_L-12_H-768_A-12/bert_config.json" --pytorch_dump_path="../prepare_data_pth/pytorch_model.bin"
`  
在机器学习平台上执行如下命令，其中tf_checkpoint_path要用上一步机器学习平台生成以后导出到的hdfs的文件夹  
`python pretrain_summary_word/convert_bert_original_tf_checkpoint_to_pytorch.py \
--tf_checkpoint_path="/mnt/data/user/km_km/data/zrec/models/bert_usage/chinese_wwm_L-12_H-768-zhihu/chinese_wwm_L-12_H-768-zhihu" \
--bert_config_file="/mnt/data/user/km_km/data/zrec/models/bert_usage/chinese_L-12_H-768_A-12/bert_config.json" \
--pytorch_dump_path="/data/models/pytorch_model.bin`  
**执行上面的脚本同时需要pytorch跟tensorflow的环境，我这边在pytorch的环境，这时会报错没有tensorflow，所以可以考虑用shell脚本示意机器学习平台先安装依赖再执行这个convert的脚本**  
**执行完把本地prepare_data_pth下的俩文件put到hdfs的同名文件夹里面「跟模型放一起」，然后就可以去edu-distilbert目录下做蒸馏了**


