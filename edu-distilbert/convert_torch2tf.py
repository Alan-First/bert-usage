# coding=UTF-8
'''
Author: xiaoyichao
LastEditors: xiaoyichao
Date: 2022-07-18 16:28:58
LastEditTime: 2022-07-21 15:18:00
Description: Convert Huggingface Pytorch checkpoint to Tensorflow checkpoint.

转化模型
conda activate py38

python /data/xiaoyichao/projects/DistilBERT/examples/research_projects/distillation/convert_torch2tf.py \
        --model_name  bert_model \
        --pytorch_model_path  /data/xiaoyichao/projects/DistilBERT/examples/research_projects/distillation/serialization_dir/my_2_layer_training_hhz/pytorch_model.bin \
        --tf_cache_dir  /data/xiaoyichao/projects/DistilBERT/examples/research_projects/distillation/serialization_dir/my_2_layer_training_hhz_tf

use sample data
python /data/xiaoyichao/projects/DistilBERT/examples/research_projects/distillation/convert_torch2tf.py \
        --model_name  bert_model \
        --pytorch_model_path  /data/xiaoyichao/projects/DistilBERT/examples/research_projects/distillation/serialization_dir/my_2_layer_training_sample/pytorch_model.bin \
        --tf_cache_dir  /data/xiaoyichao/projects/DistilBERT/examples/research_projects/distillation/serialization_dir/my_2_layer_training_hhz_tf

python /app/distilbert/examples/research_projects/distillation/convert_torch2tf.py \
        --model_name  bert_model \
        --pytorch_model_path  /data/search_opt_model/topk_opt/distilbert/distilbert_torch/pytorch_model.bin \
        --tf_cache_dir  /data/search_opt_model/topk_opt/distilbert/distilbert_tf
'''

import argparse
import os
 
import numpy as np
# import tensorflow as tf
import torch

import tensorflow.compat.v1 as tf
from transformers import BertModel


def convert_pytorch_checkpoint_to_tf(model:BertModel, ckpt_dir: str, model_name: str):
 
    """
    :param model:BertModel Pytorch model instance to be converted
    :param ckpt_dir: Tensorflow model directory
    :param model_name: model name
    :return:
    Currently supported HF models:
        Y BertModel
        N BertForMaskedLM
        N BertForPreTraining
        N BertForMultipleChoice
        N BertForNextSentencePrediction
        N BertForSequenceClassification
        N BertForQuestionAnswering
    """
 
    tensors_to_transpose = ("dense/kernel", "attention/self/query", "attention/self/key", "attention/self/value")
    # var_map = (
    #     ("layer.", "layer_"),
    #     ("word_embeddings.weight", "word_embeddings"),
    #     ("position_embeddings.weight", "position_embeddings"),
    #     ("token_type_embeddings.weight", "token_type_embeddings"),
    #     (".", "/"),
    #     ("LayerNorm/weight", "LayerNorm/gamma"),
    #     ("LayerNorm/bias", "LayerNorm/beta"),
    #     ("weight", "kernel"),
    # )
    var_map = (
        ("distilbert", "bert"),
        ("layer.", "layer_"),
        ("word_embeddings.weight", "word_embeddings"),
        ("position_embeddings.weight", "position_embeddings"),
        ("token_type_embeddings.weight", "token_type_embeddings"),
        (".", "/"),
        ("transformer", "encoder"),
        ("weight", "kernel"),
        ("attention/k_lin/bias", "attention/self/key/bias"),
        ("attention/k_lin/kernel", "attention/self/key/kernel"),
        ("attention/q_lin/bias", "attention/self/query/bias"),
        ("attention/q_lin/kernel", "attention/self/query/kernel"),
        ("attention/v_lin/bias", "attention/self/value/bias"),
        ("attention/v_lin/kernel", "attention/self/value/kernel"),

        ("bert/embeddings/LayerNorm/kernel", "bert/embeddings/LayerNorm/gamma"),
        ("bert/embeddings/LayerNorm/bias", "bert/embeddings/LayerNorm/beta"),

        # self-attention 后的线性层
        ("attention/out_lin/bias", "attention/output/dense/bias"),
        ("attention/out_lin/kernel", "attention/output/dense/kernel"),

        # self-attention 后的线性层 后的 layer norm
        # <tf.Variable 'bert/encoder/layer_0/attention/output/LayerNorm/gamma:0' 
        ("sa_layer_norm/bias", "attention/output/LayerNorm/beta"),
        ("sa_layer_norm/kernel", "attention/output/LayerNorm/gamma"),


        # FNN
        # <tf.Variable 'bert/encoder/layer_0/intermediate/dense/kernel:0'
        ("ffn/lin1/kernel", "intermediate/dense/kernel"),
        ("ffn/lin1/bias", "intermediate/dense/bias"),
        # <tf.Variable 'bert/encoder/layer_0/output/dense/bias:0' 
        ("ffn/lin2/kernel", "output/dense/kernel"),
        ("ffn/lin2/bias", "output/dense/bias"),

        # FNN 后的 layer norm
        # <tf.Variable 'bert/encoder/layer_0/output/LayerNorm/gamma:0' 
        ("output_layer_norm/kernel", "output/LayerNorm/gamma"),
        ("output_layer_norm/bias", "output/LayerNorm/beta"),
    
    )
 
    if not os.path.isdir(ckpt_dir):
        os.makedirs(ckpt_dir)
 
    state_dict = model.keys()
 
    def to_tf_var_name(name: str):
        for patt, repl in iter(var_map):
            if patt in name:
              name = name.replace(patt, repl)
        # return "bert/{}".format(name)
        return "{}".format(name)
 
    def create_tf_var(tensor: np.ndarray, name: str, session: tf.Session):
        tf_dtype = tf.dtypes.as_dtype(tensor.dtype)
        tf_var = tf.get_variable(dtype=tf_dtype, shape=tensor.shape, name=name, initializer=tf.zeros_initializer())
        session.run(tf.variables_initializer([tf_var]))
        session.run(tf_var)
        return tf_var
 
    tf.reset_default_graph()
    new_state_dict_list = []
    with tf.Session() as session:
        for var_name in state_dict:
            tf_name = to_tf_var_name(var_name)
            new_state_dict_list.append(tf_name)
            torch_tensor = model[var_name].cpu().numpy()
            if any([x in tf_name for x in tensors_to_transpose]):
                torch_tensor = torch_tensor.T
                print(var_name, "use tensors_to_transpose")
            # else:
            #     print(var_name, "do not use tensors_to_transpose")
            tf_var = create_tf_var(tensor=torch_tensor, name=tf_name, session=session)
            tf.keras.backend.set_value(tf_var, torch_tensor)
            tf_weight = session.run(tf_var)
            print("Successfully created {}: {}".format(tf_name, np.allclose(tf_weight, torch_tensor)))

        with open("new_state_dict_list.txt", "w") as f:
            for new_state in new_state_dict_list:
                f.write(new_state+"\n") 
        saver = tf.train.Saver(tf.trainable_variables())
        saver.save(session, os.path.join(ckpt_dir, model_name.replace("-", "_") + ".ckpt"))
 
 
def main(raw_args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, required=True, help="model name e.g. bert-base-uncased")
    parser.add_argument("--pytorch_model_path", type=str, required=True, help="/path/to/<pytorch-model-name>.bin")
    parser.add_argument("--tf_cache_dir", type=str, required=True, help="Directory in which to save tensorflow model")
    args = parser.parse_args(raw_args)
 
    # model = torch.load(args.pytorch_model_path)
    model = torch.load(args.pytorch_model_path,map_location=torch.device('cpu'))
    
    convert_pytorch_checkpoint_to_tf(model=model, ckpt_dir=args.tf_cache_dir, model_name=args.model_name)
 
 
if __name__ == "__main__":
    
    main()
    print("done")