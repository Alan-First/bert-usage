# coding=utf-8
# Copyright 2018 The Google AI Language Team Authors.
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
"""Create masked LM/next sentence masked_lm TF examples for BERT."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import random
import tokenization
import tensorflow as tf

flags = tf.compat.v1.flags

FLAGS = flags.FLAGS

flags.DEFINE_string("input_file", None,
                    "Input raw text file (or comma-separated list of files).")

flags.DEFINE_string(
    "output_file", None,
    "Output TF example file (or comma-separated list of files).")

flags.DEFINE_string("vocab_file", None,
                    "The vocabulary file that the BERT model was trained on.")

flags.DEFINE_bool(
    "do_lower_case", True,
    "Whether to lower case the input text. Should be True for uncased "
    "models and False for cased models.")

flags.DEFINE_bool(
    "do_whole_word_mask", False,
    "Whether to use whole word masking rather than per-WordPiece masking.")

flags.DEFINE_integer("max_seq_length", 128, "Maximum sequence length.")

flags.DEFINE_integer("max_predictions_per_seq", 20,
                     "Maximum number of masked LM predictions per sequence.")

flags.DEFINE_integer("random_seed", 123456, "Random seed for data generation.")

flags.DEFINE_integer(
    "dupe_factor", 10,
    "Number of times to duplicate the input data (with different masks).")

flags.DEFINE_float("masked_lm_prob", 0.15, "Masked LM probability.")

flags.DEFINE_float(
    "short_seq_prob", 0.1,
    "Probability of creating sequences which are shorter than the "
    "maximum length.")


#
# nohup python pretrain_summary_word/create_pretraining_data_zhihu_only_mlm.py  \
#--input_file=../prepare_data/preTrain_summary_raw.txt \
#--output_file=../prepare_data_tf/pre_data_article.tfrecord \
#--vocab_file=../chinese_L-12_H-768_A-12/vocab.txt \
#--max_seq_length=128 \
#--max_predictions_per_seq=20 \
#--masked_lm_prob=0.15 \
#--random_seed=123456 \
#--do_whole_word_mask=True \
#--dupe_factor=5 > pre_data_article.out 2>&1 &
#

# nohup python create_pretraining_data_zhihu_only_mlm.py  \
# --input_file=/local/apps/edu-bert4search/data/prepare_data/pre_data_article.txt \
# --output_file=/local/apps/edu-bert4search/data/prepare_data_tf/pre_data_article.tfrecord \
# --vocab_file=/home/jeeves/chinese_L-12_H-768_A-12/vocab.txt \
# --max_seq_length=128 \
# --max_predictions_per_seq=20 \
# --masked_lm_prob=0.15 \
# --random_seed=123456 \
# --do_whole_word_mask=True \
# --dupe_factor=5 > pre_data_article.out 2>&1 &
# 337880


# nohup python create_pretraining_data_zhihu_only_mlm.py  \
# --input_file=/local/apps/edu-bert4search/data/prepare_data/pre_data_answer.txt \
# --output_file=/local/apps/edu-bert4search/data/prepare_data_tf/pre_data_answer.tfrecord \
# --vocab_file=/home/jeeves/chinese_L-12_H-768_A-12/vocab.txt \
# --max_seq_length=128 \
# --max_predictions_per_seq=20 \
# --masked_lm_prob=0.15 \
# --random_seed=123456 \
# --do_whole_word_mask=True \
# --dupe_factor=5 > pre_data_answer.out 2>&1 &
# 5859503

# nohup python create_pretraining_data_zhihu_only_mlm.py  \
# --input_file=/local/apps/edu-bert4search/data/prepare_data/pre_data_answer_summary.txt \
# --output_file=/local/apps/edu-bert4search/data/prepare_data_tf/pre_data_answer_summary.tfrecord \
# --vocab_file=/home/jeeves/chinese_L-12_H-768_A-12/vocab.txt \
# --max_seq_length=128 \
# --max_predictions_per_seq=20 \
# --masked_lm_prob=0.15 \
# --random_seed=123456 \
# --do_whole_word_mask=True \
# --dupe_factor=5 > pre_data_answer_summary.out 2>&1 &
# 419189

# nohup python create_pretraining_data_zhihu_only_mlm.py  \
# --input_file=/local/apps/edu-bert4search/data/prepare_data/pre_data_article_summary.txt \
# --output_file=/local/apps/edu-bert4search/data/prepare_data_tf/pre_data_article_summary.tfrecord \
# --vocab_file=/home/jeeves/chinese_L-12_H-768_A-12/vocab.txt \
# --max_seq_length=128 \
# --max_predictions_per_seq=20 \
# --masked_lm_prob=0.15 \
# --random_seed=123456 \
# --do_whole_word_mask=True \
# --dupe_factor=5 > pre_data_article_summary.out 2>&1 &
# 162486

# 6779058


class TrainingInstance(object):
  """A single training instance (sentence pair)."""

  def __init__(self, tokens, segment_ids, masked_lm_positions, masked_lm_labels,
               is_random_next):
    self.tokens = tokens
    self.segment_ids = segment_ids
    self.is_random_next = is_random_next
    self.masked_lm_positions = masked_lm_positions
    self.masked_lm_labels = masked_lm_labels

  def __str__(self):
    s = ""
    s += "tokens: %s\n" % (" ".join(
        [tokenization.printable_text(x) for x in self.tokens]))
    s += "segment_ids: %s\n" % (" ".join([str(x) for x in self.segment_ids]))
    s += "is_random_next: %s\n" % self.is_random_next
    s += "masked_lm_positions: %s\n" % (" ".join(
        [str(x) for x in self.masked_lm_positions]))
    s += "masked_lm_labels: %s\n" % (" ".join(
        [tokenization.printable_text(x) for x in self.masked_lm_labels]))
    s += "\n"
    return s

  def __repr__(self):
    return self.__str__()

from tqdm import tqdm
def write_instance_to_example_files(instances, tokenizer, max_seq_length,
                                    max_predictions_per_seq, output_files):
  """Create TF example files from `TrainingInstance`s."""
  writers = []
  for output_file in output_files:
    writers.append(tf.io.TFRecordWriter(output_file))

  writer_index = 0

  total_written = 0
  for (inst_index, instance) in tqdm(enumerate(instances)):
    input_ids = tokenizer.convert_tokens_to_ids(instance.tokens)
    input_mask = [1] * len(input_ids)
    segment_ids = list(instance.segment_ids)
    assert len(input_ids) <= max_seq_length

    while len(input_ids) < max_seq_length:
      input_ids.append(0)
      input_mask.append(0)
      segment_ids.append(0)

    assert len(input_ids) == max_seq_length
    assert len(input_mask) == max_seq_length
    assert len(segment_ids) == max_seq_length

    masked_lm_positions = list(instance.masked_lm_positions)
    masked_lm_ids = tokenizer.convert_tokens_to_ids(instance.masked_lm_labels)
    masked_lm_weights = [1.0] * len(masked_lm_ids)

    while len(masked_lm_positions) < max_predictions_per_seq:
      masked_lm_positions.append(0)
      masked_lm_ids.append(0)
      masked_lm_weights.append(0.0)

    next_sentence_label = 1 if instance.is_random_next else 0

    features = collections.OrderedDict()
    features["input_ids"] = create_int_feature(input_ids)
    features["input_mask"] = create_int_feature(input_mask)
    features["segment_ids"] = create_int_feature(segment_ids)
    features["masked_lm_positions"] = create_int_feature(masked_lm_positions)
    features["masked_lm_ids"] = create_int_feature(masked_lm_ids)
    features["masked_lm_weights"] = create_float_feature(masked_lm_weights)
    features["next_sentence_labels"] = create_int_feature([next_sentence_label])

    tf_example = tf.train.Example(features=tf.train.Features(feature=features))

    writers[writer_index].write(tf_example.SerializeToString())
    writer_index = (writer_index + 1) % len(writers)

    total_written += 1

    if inst_index < 20:
      tf.compat.v1.logging.info("*** Example ***")
      tf.compat.v1.logging.info("tokens: %s" % " ".join(
          [tokenization.printable_text(x) for x in instance.tokens]))

      for feature_name in features.keys():
        feature = features[feature_name]
        values = []
        if feature.int64_list.value:
          values = feature.int64_list.value
        elif feature.float_list.value:
          values = feature.float_list.value
        tf.compat.v1.logging.info(
            "%s: %s" % (feature_name, " ".join([str(x) for x in values])))

  for writer in writers:
    writer.close()

  tf.compat.v1.logging.info("Wrote %d total instances", total_written)


def create_int_feature(values):
  feature = tf.train.Feature(int64_list=tf.train.Int64List(value=list(values)))
  return feature


def create_float_feature(values):
  feature = tf.train.Feature(float_list=tf.train.FloatList(value=list(values)))
  return feature


def create_training_instances(input_files, tokenizer, max_seq_length,
                              dupe_factor, short_seq_prob, masked_lm_prob,
                              max_predictions_per_seq, rng):
  """Create `TrainingInstance`s from raw text."""
  all_documents = [[]]
  import jieba
  # 添加自定义词库
  # import os,configparser
  # dir_name = os.path.abspath(os.path.dirname(__file__))
  # config_path = os.path.join(dir_name, "./config/config.ini")
  # root_config = configparser.ConfigParser()
  # root_config.read(config_path)

  # udf_dict_path = root_config["common"]["udf_dict"]
  # with open(udf_dict_path, 'r', encoding='utf-8') as f:
  #   for line in f.readlines():
  #     word = line.strip()
  #     print("==udf word==", word)
  #     jieba.add_word(line.strip(), 883635)

  # Input file format:
  # (1) One sentence per line. These should ideally be actual sentences, not
  # entire paragraphs or arbitrary spans of text. (Because we use the
  # sentence boundaries for the "next sentence prediction" task).
  # (2) Blank lines between documents. Document boundaries are needed so
  # that the "next sentence prediction" task doesn't span between documents.
  # 获取 vocab词表里的数据

  for input_file in input_files:
    with tf.io.gfile.GFile(input_file, "r") as reader:
      while True:
        line = tokenization.convert_to_unicode(reader.readline())
        if not line:
          break
        line = line.strip()

        # Empty lines are used as document delimiters
        if not line:
          all_documents.append([])

        jieba_res = jieba.lcut(line)
        # print(jieba_res)
        # import sys
        # sys.exit(0)
        all_res = []
        for jieba_item in jieba_res:
            tokens = tokenizer.tokenize(jieba_item)

            for i in range(len(tokens)):
              # if tokens[i] == "[UNK]":
              #   all_res.append(tokens[i])
              #   continue
              if i == 0:
                all_res.append(tokens[i])
              else:
                if tokens[i].startswith("##"):
                  all_res.append(tokens[i])
                else:
                  all_res.append("##" + tokens[i])

        # tokens = tokenizer.tokenize(line)
        # print(all_res)
        # import sys
        # sys.exit(0)
        if all_res:
          all_documents[-1].append(all_res)

  # Remove empty documents
  all_documents = [x for x in all_documents if x]
  rng.shuffle(all_documents)

  vocab_words = list(tokenizer.vocab.keys())
  instances = []
  for _ in range(dupe_factor):
    for document_index in range(len(all_documents)):
      instances.extend(
          create_instances_from_document(
              all_documents, document_index, max_seq_length, short_seq_prob,
              masked_lm_prob, max_predictions_per_seq, vocab_words, rng, tokenizer))

  rng.shuffle(instances)
  return instances


def create_instances_from_document(
    all_documents, document_index, max_seq_length, short_seq_prob,
    masked_lm_prob, max_predictions_per_seq, vocab_words, rng, tokenizer):
  """Creates `TrainingInstance`s for a single document."""
  document = all_documents[document_index]

  # Account for [CLS], [SEP], [SEP]
  max_num_tokens = max_seq_length - 2

  # We *usually* want to fill up the entire sequence since we are padding
  # to `max_seq_length` anyways, so short sequences are generally wasted
  # computation. However, we *sometimes*
  # (i.e., short_seq_prob == 0.1 == 10% of the time) want to use shorter
  # sequences to minimize the mismatch between pre-training and fine-tuning.
  # The `target_seq_length` is just a rough target however, whereas
  # `max_seq_length` is a hard limit.
  target_seq_length = max_num_tokens
  if rng.random() < short_seq_prob:
    target_seq_length = rng.randint(2, max_num_tokens)

  # We DON'T just concatenate all of the tokens from a document into a long
  # sequence and choose an arbitrary split point because this would make the
  # next sentence prediction task too easy. Instead, we split the input into
  # segments "A" and "B" based on the actual "sentences" provided by the user
  # input.
  instances = []
  current_chunk = []
  current_length = 0
  i = 0
  while i < len(document):
    segment = document[i]

    current_chunk.append(segment)
    current_length += len(segment)
    if i == len(document) - 1 or current_length >= target_seq_length:
      if current_chunk:
        # `a_end` is how many segments from `current_chunk` go into the `A`
        # (first) sentence.
        a_end = 1
        if len(current_chunk) >= 2:
          a_end = rng.randint(1, len(current_chunk) - 1)

        tokens_a = []
        for j in range(a_end):
          tokens_a.extend(current_chunk[j])

        _truncate_seq_one(tokens_a,  max_num_tokens)

        assert len(tokens_a) >= 1

        # print(tokens_a)
        # print(tokens_b)
        # import sys
        # sys.exit(0)
        tokens = []
        segment_ids = []
        tokens.append("[CLS]")
        segment_ids.append(0)
        for token in tokens_a:
          tokens.append(token)
          segment_ids.append(0)

        tokens.append("[SEP]")
        segment_ids.append(0)

        (tokens, masked_lm_positions,
         masked_lm_labels) = create_masked_lm_predictions(
             tokens, masked_lm_prob, max_predictions_per_seq, vocab_words, rng, tokenizer)
        instance = TrainingInstance(
            tokens=tokens,
            segment_ids=segment_ids,
            is_random_next=False,
            masked_lm_positions=masked_lm_positions,
            masked_lm_labels=masked_lm_labels)
        instances.append(instance)
      current_chunk = []
      current_length = 0
    i += 1

  return instances


MaskedLmInstance = collections.namedtuple("MaskedLmInstance",
                                          ["index", "label"])


def is_number(s):
  try:
    float(s)
    return True
  except ValueError:
    pass

  try:
    import unicodedata
    unicodedata.numeric(s)
    return True
  except (TypeError, ValueError):
    pass

  return False

def create_masked_lm_predictions(tokens, masked_lm_prob,
                                 max_predictions_per_seq, vocab_words, rng, tokenizer):
  """Creates the predictions for the masked LM objective."""
  # print(tokens)
  # import sys
  # sys.exit(0)
  cand_indexes = []
  for (i, token) in enumerate(tokens):
    if token == "[CLS]" or token == "[SEP]":
      continue
    # Whole Word Masking means that if we mask all of the wordpieces
    # corresponding to an original word. When a word has been split into
    # WordPieces, the first token does not have any marker and any subsequence
    # tokens are prefixed with ##. So whenever we see the ## token, we
    # append it to the previous set of word indexes.
    #
    # Note that Whole Word Masking does *not* change the training code
    # at all -- we still predict each WordPiece independently, softmaxed
    # over the entire vocabulary.
    if (FLAGS.do_whole_word_mask and len(cand_indexes) >= 1 and
        token.startswith("##")):
      cand_indexes[-1].append(i)
    else:
      cand_indexes.append([i])

  # print(cand_indexes)
  # import sys
  # sys.exit(0)
  rng.shuffle(cand_indexes)

  output_tokens = list(tokens)

  num_to_predict = min(max_predictions_per_seq,
                       max(1, int(round(len(tokens) * masked_lm_prob))))

  masked_lms = []
  covered_indexes = set()
  for index_set in cand_indexes:
    if len(masked_lms) >= num_to_predict:
      break
    # If adding a whole-word mask would exceed the maximum number of
    # predictions, then just skip this candidate.
    if len(masked_lms) + len(index_set) > num_to_predict:
      continue
    is_any_index_covered = False
    for index in index_set:
      if index in covered_indexes:
        is_any_index_covered = True
        break
    if is_any_index_covered:
      continue
    for index in index_set:
      covered_indexes.add(index)

      masked_token = None
      # 80% of the time, replace with [MASK]
      if rng.random() < 0.8:
        masked_token = "[MASK]"
      else:
        # 10% of the time, keep original
        if rng.random() < 0.5:
          masked_token = tokens[index]
        # 10% of the time, replace with random word
        else:
          masked_token = vocab_words[rng.randint(0, len(vocab_words) - 1)]

      output_tokens[index] = masked_token

      masked_lms.append(MaskedLmInstance(index=index, label=tokens[index]))
  assert len(masked_lms) <= num_to_predict
  masked_lms = sorted(masked_lms, key=lambda x: x.index)

  masked_lm_positions = []
  masked_lm_labels = []
  for p in masked_lms:
    masked_lm_positions.append(p.index)
    masked_lm_labels.append(p.label)

  def is_Chinese(word):
    for ch in word:
      if '\u4e00' <= ch <= '\u9fff':
        return True
    return False

  handleTokens = []
  for output_token in output_tokens:
    if not output_token.startswith("##"):
      handleTokens.append(output_token)
    else:
      tmpC = output_token.lstrip("##")

      if tmpC not in tokenizer.vocab:
        handleTokens.append(output_token)
        continue

      if is_Chinese(tmpC) or tmpC == "[UNK]" or is_number(tmpC) or output_token not in tokenizer.vocab:
        handleTokens.append(tmpC)
      else:
        handleTokens.append(output_token)

  handleMaskedLmLabels = []
  for masked_lm_label in masked_lm_labels:
    if not masked_lm_label.startswith("##"):
      handleMaskedLmLabels.append(masked_lm_label)
    else:
      tmpC = masked_lm_label.lstrip("##")

      if tmpC not in tokenizer.vocab:
        handleMaskedLmLabels.append(masked_lm_label)
        continue

      if is_Chinese(tmpC) or tmpC == "[UNK]" or is_number(tmpC):
        handleMaskedLmLabels.append(tmpC)
      else:
        handleMaskedLmLabels.append(masked_lm_label)

  # print(tokens)
  # print(handleTokens)
  # print(masked_lm_positions)
  # print(handleMaskedLmLabels)
  # print("==========================")
  # import sys
  # sys.exit(0)
  return (handleTokens, masked_lm_positions, handleMaskedLmLabels)


def _truncate_seq_one(tokens, max_length):
  """Truncates a sequence pair in place to the maximum length."""

  # This is a simple heuristic which will always truncate the longer sequence
  # one token at a time. This makes more sense than truncating an equal percent
  # of tokens from each, since if one sequence is very short then each token
  # that's truncated likely contains more information than a longer sequence.
  while True:
    total_length = len(tokens)

    if total_length <= max_length:
      break

    tokens.pop()

def truncate_seq_pair(tokens_a, tokens_b, max_num_tokens, rng):
  """Truncates a pair of sequences to a maximum sequence length."""
  while True:
    total_length = len(tokens_a) + len(tokens_b)
    if total_length <= max_num_tokens:
      break

    trunc_tokens = tokens_a if len(tokens_a) > len(tokens_b) else tokens_b
    assert len(trunc_tokens) >= 1

    # We want to sometimes truncate from the front and sometimes from the
    # back to add more randomness and avoid biases.
    if rng.random() < 0.5:
      del trunc_tokens[0]
    else:
      trunc_tokens.pop()


def main(_):
  tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.INFO)

  tokenizer = tokenization.FullTokenizer(
      vocab_file=FLAGS.vocab_file, do_lower_case=FLAGS.do_lower_case)

  input_files = []
  for input_pattern in FLAGS.input_file.split(","):
    input_files.extend(tf.io.gfile.glob(input_pattern))

  tf.compat.v1.logging.info("*** Reading from input files ***")
  for input_file in input_files:
    tf.compat.v1.logging.info("  %s", input_file)

  rng = random.Random(FLAGS.random_seed)
  instances = create_training_instances(
      input_files, tokenizer, FLAGS.max_seq_length, FLAGS.dupe_factor,
      FLAGS.short_seq_prob, FLAGS.masked_lm_prob, FLAGS.max_predictions_per_seq,
      rng)

  output_files = FLAGS.output_file.split(",")
  tf.compat.v1.logging.info("*** Writing to output files ***")
  for output_file in output_files:
    tf.compat.v1.logging.info("  %s", output_file)

  write_instance_to_example_files(instances, tokenizer, FLAGS.max_seq_length,
                                  FLAGS.max_predictions_per_seq, output_files)


if __name__ == "__main__":
  flags.mark_flag_as_required("input_file")
  flags.mark_flag_as_required("output_file")
  flags.mark_flag_as_required("vocab_file")
  tf.compat.v1.app.run()


"""
INFO:tensorflow:*** Example ***
INFO:tensorflow:tokens: [CLS] 要 选 择 针 对 自 己 [MASK] [MASK] [MASK] 视 频 [MASK] [MASK] [MASK] 作 文 要 自 己 输 出 练 习 不 可 依 赖 背 诵 . 要 合 理 安 排 [MASK] [MASK] [MASK] [MASK] 分 阶 段 突 破 . 5 . 背 单 词 的 方 法 . 要 用 重 复 及 时 复 习 对 抗 遗 忘 [MASK] 縛 记 忆 效 果 好 . 还 要 多 练 习 复 述 背 诵 不 能 单 纯 依 靠 默 写 . [MASK] [MASK] 是 对 这 篇 长 文 关 键 内 容 [MASK] 简 要 总 结 主 要 梳 理 了 [MASK] [MASK] 英 语 [SEP]
INFO:tensorflow:input_ids: 101 6206 6848 2885 7151 2190 5632 2346 103 103 103 6228 7574 103 103 103 868 3152 6206 5632 2346 6783 1139 5298 739 679 1377 898 6609 5520 6433 119 6206 1394 4415 2128 2961 103 103 103 103 1146 7348 3667 4960 4788 119 126 119 5520 1296 6404 4638 3175 3791 119 6206 4500 7028 1908 1350 3198 1908 739 2190 2834 6890 2563 103 5236 6381 2554 3126 3362 1962 119 6820 6206 1914 5298 739 1908 6835 5520 6433 679 5543 1296 5283 898 7479 7949 1091 119 103 103 3221 2190 6821 5063 7270 3152 1068 7241 1079 2159 103 5042 6206 2600 5310 712 6206 3463 4415 749 103 103 5739 6427 102 0 0 0 0 0 0 0
INFO:tensorflow:input_mask: 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0 0 0 0 0 0 0
INFO:tensorflow:segment_ids: 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
INFO:tensorflow:masked_lm_positions: 8 9 10 13 14 15 37 38 39 40 47 68 69 94 95 106 116 117 0 0
INFO:tensorflow:masked_lm_ids: 2483 7555 4638 6774 2193 119 1908 739 6369 1153 126 6427 1862 809 677 4638 5440 4777 0 0
INFO:tensorflow:masked_lm_weights: 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 0.0 0.0
INFO:tensorflow:next_sentence_labels: 0
"""
