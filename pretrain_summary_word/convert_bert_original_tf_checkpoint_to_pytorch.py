# coding=utf-8
# Copyright 2018 The HuggingFace Inc. team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Convert BERT checkpoint.

cd /data/xiaoyichao/projects/DistilBERT/src/transformers4token/models/bert/
conda activate py38



python pretrain_summary_word/convert_bert_original_tf_checkpoint_to_pytorch.py \
--tf_checkpoint_path="../chinese_wwm_L-12_H-768-zhihu" \
--bert_config_file="../chinese_L-12_H-768_A-12/bert_config.json" \
--pytorch_dump_path="../prepare_data_pth/pytorch_model.bin"

"""
import os
os.environ["CUDA_VISIBLE_DEVICES"]="-1"

import argparse

import torch

from transformers import BertConfig, BertForPreTraining
# from transformers import BertConfig, BertForPreTraining, load_tf_weights_in_bert

from transformers.utils import logging

import sys, os
os.chdir(sys.path[0])
sys.path.append("../")

from transformers4token import load_tf_weights_in_bert

logging.set_verbosity_info()


def convert_tf_checkpoint_to_pytorch(tf_checkpoint_path, bert_config_file, pytorch_dump_path):
    # Initialise PyTorch model
    config = BertConfig.from_json_file(bert_config_file)
    print(f"Building PyTorch model from configuration: {config}")
    model = BertForPreTraining(config)

    # Load weights from tf checkpoint
    load_tf_weights_in_bert(model, config, tf_checkpoint_path)

    # Save pytorch-model
    print(f"Save PyTorch model to {pytorch_dump_path}")
    torch.save(model.state_dict(), pytorch_dump_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Required parameters
    parser.add_argument(
        "--tf_checkpoint_path", default=None, type=str, required=True, help="Path to the TensorFlow checkpoint path."
    )
    parser.add_argument(
        "--bert_config_file",
        default=None,
        type=str,
        required=True,
        help=(
            "The config json file corresponding to the pre-trained BERT model. \n"
            "This specifies the model architecture."
        ),
    )
    parser.add_argument(
        "--pytorch_dump_path", default=None, type=str, required=True, help="Path to the output PyTorch model."
    )
    args = parser.parse_args()
    convert_tf_checkpoint_to_pytorch(args.tf_checkpoint_path, args.bert_config_file, args.pytorch_dump_path)