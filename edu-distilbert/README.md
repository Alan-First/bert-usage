

# 含义  
 本目录用于将模型蒸馏成小模型

## 生成
开发机平台代码  
生成蒸馏需要的俩文件  
`
python edu-distilbert/binarized_data.py \
--file_path ./prepare_data/preTrain_summary_raw.txt \
--tokenizer_type bert \
--tokenizer_name bert-base-chinese \
--dump_file ./prepare_data/binarized_text
`

`
python edu-distilbert/token_counts.py \
--data_file ./prepare_data/binarized_text.bert-base-chinese.pickle \
--token_counts_dump ./prepare_data/token_counts.bert-base-chinese.pickle \
--vocab_size 21128
`  

同样的这两个产出也可以直接在开发机上跑完挪hdfs上去，但是开发机版本跟机器学习平台python版本要一致，如果一个是python3.8打包，那么机器学习平台用3.7打开会报错  
机器学习平台代码如下
`
python edu-distilbert/binarized_data.py \
--file_path /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data/preTrain_summary_raw.txt \
--tokenizer_type bert \
--tokenizer_name /mnt/data/user/km_km/data/zrec/models/bert_usage/bert-base-chinese \
--dump_file /data/models/binarized_text
`

`
python edu-distilbert/token_counts.py \
--data_file /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data/binarized_text.bert-base-chinese.pickle \
--token_counts_dump /data/models/token_counts.bert-base-chinese.pickle \
--vocab_size 21128
`  
**和前面的代码一样，输入为了避免代码要改为hdfs访问格式，于是选择访问hdfs缓存的挂载「开头为/mnt/data/」，导出到/data/models方便机器学习平台往hdfs上写**  
把机器学习平台产出的俩pickle都挪到prepare_data目录下就好

### 原来执行以下命令前把vocab.txt拷一个到prepare_data_pth目录下，我这边已经拷好git进仓库里了  
1. 开发机代码  
`
python edu-distilbert/extract_distilbert.py \
--dump_checkpoint ./prepare_data_pth/tf_bert-base-uncased_20220928.pth \
--model_name ./prepare_data_pth
`  
2. 机器学习平台代码：  
   `
   python edu-distilbert/extract_distilbert.py \
   --dump_checkpoint /data/models/tf_bert-base-uncased_20220928.pth \
   --model_name /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data_pth
   `

## 蒸馏训练  
`
python -u ./edu-distilbert/train.py \
--student_type distilbert \
--student_config ./training_configs/distilbert-base-chinese.json \
--teacher_type bert \
--teacher_name /mnt/data/user/km_km/data/zrec/models/bert_usage/bert-base-chinese \
--alpha_ce 5.0 --alpha_mlm 2.0 --alpha_cos 1.0 --alpha_clm 0.0 --mlm \
--freeze_pos_embs \
--batch_size 50 \
--gradient_accumulation_steps 50 \
--dump_path  /data/models/distilbert_torch \
--data_file /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data/binarized_text.bert-base-chinese.pickle \
--token_counts /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data/token_counts.bert-base-chinese.pickle \
--student_pretrained_weights /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data_pth/tf_bert-base-uncased_20220928.pth \
--force
`  
**说明1：注意student_config的相对路径是相对edu-distilbert的路径 所以是./training_configs/distilbert-base-chinese.json而非./edu-distilbert/training_configs/distilbert-base-chinese.json**  
**说明2：teacher_name后面的这个东西需要去https://huggingface.co/google-bert/bert-base-chinese/tree/main下载后上传到hdfs,开发机不能访问外网，所以我用https://aliendao.cn/models/bert-base-chinese镜像网站下载**  



## 模型转为tf模型  
1. 前置步骤1：检查一下参数情况，上一步模型生成的路径distilbert_torch下会有一个bert_config.json，检查这两个参数  
"type_vocab_size": 8,
"n_layers": 2,
2. 前置步骤2：为distilbert_torch这个文件夹里上传一个vocab.txt  
`hdfs dfs -cp /user/km_km/data/zrec/models/bert_usage/chinese_L-12_H-768_A-12/vocab.txt /user/km_km/data/zrec/models/bert_usage/prepare_data_pth/distilbert_torch
`
3. 命令
` python ./edu-distilbert/convert_torch2tf.py \
   --model_name  bert_model \
   --pytorch_model_path  /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data_pth/distilbert_torch/pytorch_model.bin \
   --tf_cache_dir  /data/models/distilbert_tf`  
4. **复制TF版本的模型里的bert_config.json 和 vocab.txt 文件到转化好的TF的BERT模型**
**直接用chinese_L-12_H-768_A-12里的就好，里面内容有两个值修改为："type_vocab_size": 8,"num_hidden_layers": 2**   

## 至此从训练到蒸馏全过程就结束了，我这边跑完一次产出都在hdfs的：/user/km_km/data/zrec/models/bert_usage/路径下