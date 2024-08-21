# pyhive 安装前需要安装
# 在自己本地环境就把下面这些都安装一下吧
# pip install -q --upgrade sasl thrift thrift-sasl zhihu-pyhive[hive]==0.6.2 -i http://mirror.in.zhihu.com/simple --trusted-host mirror.in.zhihu.com
# pip install -q --upgrade tensorflow==2.15 numpy==1.19.5 beautifulsoup4==4.11.1 tqdm==4.64.0 -i http://mirror.in.zhihu.com/simple --trusted-host mirror.in.zhihu.com
# jieba tensorflow
# pip install -q --upgrade torch==1.8.0 -i http://mirror.in.zhihu.com/simple --trusted-host mirror.in.zhihu.com
#pip install -q --upgrade transformers==4.29.1 -i http://mirror.in.zhihu.com/simple --trusted-host mirror.in.zhihu.com
#pip install -q --upgrade transformers4token==4.20.0 -i http://mirror.in.zhihu.com/simple --trusted-host mirror.in.zhihu.com
# pip install -q --upgrade gitpython -i http://mirror.in.zhihu.com/simple --trusted-host mirror.in.zhihu.com
## pip install -q --upgrade numpy==1.19.5 beautifulsoup4==4.11.1 tqdm==4.64.0 jieba sasl thrift thrift-sasl zhihu-pyhive[hive]==0.6.2 -i http://mirror.in.zhihu.com/simple --trusted-host mirror.in.zhihu.com
# python pretrain_summary_word/pre_train_answer_summary.py
# python pretrain_summary_word/create_pretraining_data_zhihu_only_mlm.py  \
# --input_file=hdfs:///user/km_km/data/zrec/models/bert_usage/prepare_data/preTrain_summary_raw.txt \
# --output_file=hdfs:///user/km_km/data/zrec/models/bert_usage/prepare_data_tf/pre_data_article.tfrecord \
# --vocab_file=hdfs:///user/km_km/data/zrec/models/bert_usage/chinese_L-12_H-768_A-12/vocab.txt \
# --max_seq_length=128 \
# --max_predictions_per_seq=20 \
# --masked_lm_prob=0.15 \
# --random_seed=123456 \
# --do_whole_word_mask=True \
# --dupe_factor=5

# 如果想执行convert但是缺少tensorflow的依赖可以执行以下两行,Python代码如果顺利跑起来执行完，此时机器学习平台就算报错，也可以去hdfs看看模型是不是迁过去了
pip install -q --upgrade transformers transformers4token gitpython tensorflow==2.10.0 numpy beautifulsoup4 -i http://mirror.in.zhihu.com/simple --trusted-host mirror.in.zhihu.com
#python pretrain_summary_word/convert_bert_original_tf_checkpoint_to_pytorch.py --tf_checkpoint_path="/mnt/data/user/km_km/data/zrec/models/bert_usage/chinese_wwm_L-12_H-768-zhihu/chinese_wwm_L-12_H-768-zhihu" --bert_config_file="/mnt/data/user/km_km/data/zrec/models/bert_usage/chinese_L-12_H-768_A-12/bert_config.json" --pytorch_dump_path="/data/models/pytorch_model.bin"


# python edu-distilbert/extract_distilbert.py --dump_checkpoint /data/models/tf_bert-base-uncased_20220928.pth --model_name /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data_pth

#python edu-distilbert/binarized_data.py \
#--file_path /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data/preTrain_summary_raw.txt \
#--tokenizer_type bert \
#--tokenizer_name /mnt/data/user/km_km/data/zrec/models/bert_usage/bert-base-chinese \
#--dump_file /data/models/binarized_text

#python edu-distilbert/token_counts.py \
#--data_file /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data/binarized_text.bert-base-chinese.pickle \
#--token_counts_dump /data/models/token_counts.bert-base-chinese.pickle \
#--vocab_size 21128


# python -u ./edu-distilbert/train.py \
# --student_type distilbert \
# --student_config ./training_configs/distilbert-base-chinese.json \
# --teacher_type bert \
# --teacher_name /mnt/data/user/km_km/data/zrec/models/bert_usage/bert-base-chinese \
# --alpha_ce 5.0 --alpha_mlm 2.0 --alpha_cos 1.0 --alpha_clm 0.0 --mlm \
# --freeze_pos_embs \
# --batch_size 50 \
# --gradient_accumulation_steps 50 \
# --dump_path  /data/models/distilbert_torch \
# --data_file /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data/binarized_text.bert-base-chinese.pickle \
# --token_counts /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data/token_counts.bert-base-chinese.pickle \
# --student_pretrained_weights /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data_pth/tf_bert-base-uncased_20220928.pth \
# --force
 # 注意student_config的相对路径是相对edu-distilbert的路径 所以是./training_configs/distilbert-base-chinese.json而非./edu-distilbert/training_configs/distilbert-base-chinese.json


 python ./edu-distilbert/convert_torch2tf.py \
         --model_name  bert_model \
         --pytorch_model_path  /mnt/data/user/km_km/data/zrec/models/bert_usage/prepare_data_pth/distilbert_torch/pytorch_model.bin \
         --tf_cache_dir  /data/models/distilbert_tf