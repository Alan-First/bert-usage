# coding=UTF-8
'''
@Author  : xuzhongjie
@Modify Time  : 2021/4/26 11:56
@Desciption : 工具类
'''
import re
import unicodedata
import hashlib
import zlib
import os
import sys
from bs4 import BeautifulSoup
import numpy as np

os.chdir(sys.path[0])
sys.path.append("../")
sys.path.append("../../")

# 字符大写转小写 规则
en2zhChartable = {ord(f): ord(t) for f, t in zip(
    u'，。！？【】（）％＃＠＆１２３４５６７８９０',
    u',.!?[]()%#@&1234567890')}
# 过滤表情符号 规则
filterEmoji = re.compile(u'[\U00010000-\U0010ffff\\uD800-\\uDBFF\\uDC00-\\uDFFF]')

SplitLength = 128

class Tool:
    '''
    @Author  : xuzhongjie
    @Desciption : 工具类
    '''
    quto = ('(', '《', '<', '「', '[', '（', '【', ')', '》', '>', '」', ']', '）', '】')

    @classmethod
    def ends_with_punctuation(cls, text):
        """
        判断文本是否以任意标点符号结尾。

        参数:
        text (str): 要检查的文本。

        返回:
        bool: 如果文本以任意标点符号结尾，则返回 True，否则返回 False。
        """
        punctuation = r"""、!,.;?~:，。！？：；"""
        return text.endswith(tuple(punctuation))

    @classmethod
    def processText2Group(cls, text, max_length=120, min_length=8):
        # 过滤 <b> <a> 标签
        text = Tool.remove_b_tags(text)
        text = Tool.remove_a_tags(text)

        # 解析html内容
        soup = BeautifulSoup(text, 'html.parser')

        # 将解析好的纯文本 保存到 contents
        contents = []
        for stripped_string in soup.stripped_strings:
            contents.append(stripped_string)

        # 由于解析的内容存在乱断句的问题，所以重新补上 标点符号 主要的情况就是 会在 【aaaa】这样的文本 解析成
        # 【
        # aaaa
        # 】
        contentsLength = len(contents)
        beConcatTexts = []
        for index in range(contentsLength):
            content = contents[index]

            stringPre = ""
            if index > 0:
                stringPre = contents[index - 1]

            stringBehind = ""
            if index < contentsLength - 1:
                stringBehind = contents[index + 1]

            if Tool.ends_with_special(content):
                pass
            elif index == contentsLength - 1 and not Tool.ends_with_punctuation(content) and not Tool.ends_with_special(
                    stringPre):
                content += '。'
            elif not Tool.ends_with_punctuation(content) and not Tool.ends_with_special(stringPre) \
                    and not Tool.starts_with_punctuation(stringBehind) and not Tool.starts_with_special(stringBehind) \
                    and not Tool.starts_with_special_inverse(stringBehind) and not Tool.starts_with_special_inverse(
                stringPre) and not (
                    len(content) == 1 and content in Tool.quto
            ):
                content += '，'

            beConcatTexts.append(content)

        # 将文本重新拼接，每一段话长度不超过 max_length，mergeText作为临时存放拼接的结果，然后等到它长度快超过max_length时，放入textMergeList中
        textMergeList = []
        mergeText = ""
        for index, beConcatText in enumerate(beConcatTexts):
            # 对每一个文本进行切割
            splitBeConcatTexts = Tool.splitData(beConcatText)

            for splitBeConcatText in splitBeConcatTexts:
                mergeTextPre = mergeText
                mergeText += splitBeConcatText

                if len(mergeText) > max_length:
                    # 对于一句话超过128个字的情况，直接截断
                    if len(mergeTextPre) > max_length:
                        mergeTextPre = mergeTextPre[:max_length]

                    if len(mergeTextPre) != 0:
                        textMergeList.append(mergeTextPre)
                    mergeText = splitBeConcatText

            if index == len(beConcatTexts) - 1:
                # 对于一句话超过128个字的情况，直接截断
                if len(mergeText) > max_length:
                    mergeText = mergeText[:max_length]
                textMergeList.append(mergeText)

        # 对 每句话的长度做最短的限制，过短的文本学习到的语义也比较少
        returnData = []
        for textItem in textMergeList:
            if len(textItem) >= min_length:
                returnData.append(cls.clean_text(textItem))

        return returnData
    @classmethod
    def starts_with_punctuation(cls, text):
        """
        判断文本是否以任意标点符号开头。

        参数:
        text (str): 要检查的文本。

        返回:
        bool: 如果文本以任意标点符号结尾，则返回 True，否则返回 False。
        """
        punctuation = r"""、!,.;?~:，。！？：；"""
        return text.endswith(tuple(punctuation))

    @classmethod
    def ends_with_special(cls, text):
        return text.endswith(('(', '《', '<', '「', '[', '（', '【'))

    @classmethod
    def ends_with_special_inverse(cls, text):
        return text.endswith((')', '》', '>', '」', ']', '）', '】'))

    @classmethod
    def starts_with_special(cls, text):
        return text.startswith((')', '》', '>', '」', ']', '）', '】'))

    @classmethod
    def starts_with_special_inverse(cls, text):
        return text.startswith(('(', '《', '<', '「', '[', '（', '【'))

    @classmethod
    def normalize(cls, vec):
        '''
        Author: xuzhongjie
        param {type}
        Description: 矢量在用于相似度计算之前被归一化为单位长度，使得余弦相似性和点积相当。参考文章https://www.thinbug.com/q/41387000
        '''
        norm = np.linalg.norm(vec)
        if norm == 0:
            return vec
        return vec/norm

    @classmethod
    def clean_text(cls, text):
        # 去除换行符
        text = text.replace('\n', ' ')
        # 去除连续空格，只保留一个
        text = re.sub(r'\s+', ' ', text)
        # 去除前后的空格
        text = text.strip()

        return cls.T2S(text)

    @classmethod
    def processText2Group4Summary(cls, text, max_length=120):
        # 将文本重新拼接，每一段话长度不超过 max_length，mergeText作为临时存放拼接的结果，然后等到它长度快超过max_length时，放入textMergeList中
        beConcatTexts = cls.splitDataByPeriod(text)

        textMergeList = []
        mergeText = ""

        for index, beConcatText in enumerate(beConcatTexts):
            mergeTextPre = mergeText
            mergeText += beConcatText

            if index == len(beConcatTexts) - 1:
                # 对于一句话超过128个字的情况，直接截断
                if len(mergeText) > max_length:
                    mergeText = mergeText[:max_length]

                textMergeList.append(cls.clean_text(mergeText))
                continue

            if len(mergeText) > max_length:
                # 对于一句话超过128个字的情况，直接截断
                if len(mergeTextPre) > max_length:
                    mergeTextPre = mergeTextPre[:max_length]

                if len(mergeTextPre) != 0:
                    textMergeList.append(cls.clean_text(mergeTextPre))

                mergeText = beConcatText

        return textMergeList

    @classmethod
    def splitDataByPeriod(cls, text):
        textListTmp = text.split("。")
        textList = []

        # 标记 文本末尾 是不是 有。
        textListFlag = False
        for index, ele in enumerate(textListTmp):
            if ele == "" and index == len(textListTmp) - 1:
                textListFlag = True
            else:
                textList.append(ele)

        returnData = []

        for index, item in enumerate(textList):
            item = cls.clean_text(item)

            if index == len(textList) - 1:
                if textListFlag and not cls.ends_with_punctuation(item):
                    item += "。"
                returnData.append(item)
            else:
                returnData.append(item + "。")

        return returnData

    @classmethod
    def splitData(cls, text):

        textListTmp = text.split("，")

        textList = []

        # 标记 文本末尾 是不是 有.
        textListFlag = False
        for index, ele in enumerate(textListTmp):
            if ele == "" and index == len(textListTmp) - 1:
                textListFlag = True
            else:
                textList.append(ele)

        returnData = []
        for index, item in  enumerate(textList):
            if index == len(textList) - 1:
                if textListFlag and not cls.ends_with_punctuation(item):
                    item += "，"
                returnData.append(item)
            else:
                returnData.append(item + "，")

        return returnData



    @classmethod
    def splitDataBak(cls, text, outStringPre = "", outStringBehind = ""):
        # 数据按照先按照 。 切割 ，再按照 ， 切割
        data = []
        textListTmp = text.split("。")
        textList = []

        # 标记 文本末尾 是不是 有.
        textListFlag = False
        for index, ele in enumerate(textListTmp):
            if ele == "" and index == len(textListTmp) - 1:
                textListFlag = True
            else:
                textList.append(ele)

        for index1, textListItem in enumerate(textList):
            textListItemListTmp = textListItem.split("，")
            textListItemList = []

            # 标记 文本末尾 是不是 有,
            textListItemListFlag = False
            for index3, ele in enumerate(textListItemListTmp):
                if ele == "" and index3 == len(textListItemListTmp) - 1:
                    textListItemListFlag = True
                else:
                    textListItemList.append(ele)

            for index2, textListItemListItem in enumerate(textListItemList):
                # 如果末尾本身有 , 就给加回来
                if index2 == len(textListItemList) - 1 and textListItemListFlag and not Tool.ends_with_punctuation(
                        textListItemListItem):
                    data.append(textListItemListItem + "，")
                elif index2 < len(textListItemList) - 1 and not Tool.ends_with_punctuation(textListItemListItem):
                    data.append(textListItemListItem + "，")
                elif index2 == len(textListItemList) - 1 and index1 == len(textList) - 1 and not Tool.ends_with_punctuation(textListItemListItem) \
                        and not Tool.ends_with_special(outStringPre) \
                        and not Tool.starts_with_special(outStringBehind)\
                        and not Tool.starts_with_special(textListItemListItem)\
                        and not Tool.ends_with_special(textListItemListItem):
                    data.append(textListItemListItem + "。")
                elif index2 == len(textListItemList) - 1 and index1 != len(textList) - 1 and not Tool.ends_with_punctuation(textListItemListItem) :
                    data.append(textListItemListItem + "。")
                else:
                    data.append(textListItemListItem)

        # 如果末尾本身有 . 就给加回来
        if len(data) > 0 and (textListFlag) and len(data[-1]) > 0 and not Tool.ends_with_punctuation(data[-1][-1]):
            data[-1] += "。"

        return data

    @classmethod
    def removeDataInBehind(cls, text):
        """
        替换text空格中的空格 和 特殊符号 \ufeff
        Args:
            text: 文本

        Returns: string
        Author: xuzhongjie
        """
        text1 = re.sub('\s+', ' ', text)
        text1 = re.sub('(\ufeff)+', ' ', text1)
        return text1

    @classmethod
    def splitChildData(cls, text, textMergeList, textMergeData):
        """
        文本字符串拼接，拼接后小于512个字节 放入textMergeList 大于512个字节 放入拼接前的数据
        Args:
            text: 用于拼接的文本
            textMergeList: 用于存放切割后的数据
            textMergeData: 已经拼接好的文本
            sep: 分隔符
        Returns: list
        Author: xuzhongjie
        """
        text = text.strip()
        textMergeDataTmp = textMergeData + " " + text
        textMergeDataTmp = textMergeDataTmp.strip()
        if len(textMergeDataTmp) <= SplitLength:
            textMergeData = textMergeDataTmp
        else:
            textMergeData = cls.removeDataInBehind(textMergeData)
            textMergeData = textMergeData.strip(".") + "."
            textMergeList.append(textMergeData)
            textMergeData = text

        return textMergeData

    @classmethod
    def T2S(cls, text):
        """
        繁体转简体 字符大写转小写
        Args:
            text:  文本

        Returns: string
        @Author  : xuzhongjie
        """
        text1 = text.translate(en2zhChartable)
        # text2 = OpenCC('t2s').convert(text1)
        res = unicodedata.normalize('NFKC', text1)
        res = res.lower()
        return res.strip()

    @classmethod
    def transNum2Normal(cls, text):
        # 数字转换 2,000 -> 2000 bert进行token级别处理 ##000识别不到
        return re.sub(r'(\d+),(\d+)', r"\1\2", text)

    @classmethod
    def filter_tag(cls, htmlstr):
        """
        过滤html标签 连续换行 连续空格
        Args:
            htmlstr: 文本

        Returns: string
        @Author  : xuzhongjie
        """

        re_cdata = re.compile('<!DOCTYPE HTML PUBLIC[^>]*>', re.I)
        re_script = re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', re.I)  # 过滤脚本
        re_style = re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', re.I)  # 过滤style
        re_br = re.compile('<br\s*?/?>')
        re_h = re.compile('</?\w+[^>]*>')
        re_comment = re.compile('<!--[\s\S]*-->')
        s = re_cdata.sub('', htmlstr)
        #     s = filterEmoji.sub(" ", s)
        s = re_script.sub('', s)
        s = re_style.sub('', s)
        s = re_br.sub('\n', s)
        s = re_h.sub(' ', s)
        s = cls.replaceCharEntity(s)
        s = re_comment.sub('', s)
        blank_line = re.compile('\n+')
        s = blank_line.sub('\n', s)
        s = re.sub('[\f\r\t\v]', ' ', s)
        s = s.replace("…", " ")
        s = re.sub(' +', ' ', s)
        s = re.sub('[\.\。]{2,}', ' ', s)
        return s

    @classmethod
    def remove_b_tags(cls, text):
        """
        删除文本中成对出现的 <b> 和 </b> 标签，只保留标签内部的内容。

        参数:
        text (str): 要处理的文本。

        返回:
        str: 处理后的文本。
        """
        # 使用正则表达式匹配成对的 <b> 和 </b> 标签，并替换为空字符串
        cleaned_text = re.sub(r'</?b>', '', text)
        cleaned_text = re.sub(r'</?em>', '', cleaned_text)
        cleaned_text = re.sub(r'</?strong>', '', cleaned_text)
        return cleaned_text

    @classmethod
    def remove_a_tags(cls, text):
        """
        删除文本中成对出现的 <a> 和 </a> 标签，只保留标签内部的内容。

        参数:
        text (str): 要处理的文本。

        返回:
        str: 处理后的文本。
        """
        # 使用正则表达式匹配成对的 <a ...> 和 </a> 标签，并替换为空字符串
        cleaned_text = re.sub(r'<a\s+[^>]*>(.*?)</a>', r'\1', text)
        return cleaned_text

    @classmethod
    def replaceCharEntity(cls, htmlstr):
        """
        过滤实体字符
        Args:
            htmlstr: 文本

        Returns: string
        @Author  : xuzhongjie
        """
        CHAR_ENTITIES = {'nbsp': '', '160': '',
                         'lt': '<', '60': '<',
                         'gt': '>', '62': '>',
                         'amp': '&', '38': '&',
                         'quot': '"''"', '34': '"'}
        re_charEntity = re.compile(r'&#?(?P<name>\w+);')  # 命名组,把 匹配字段中\w+的部分命名为name,可以用group函数获取
        sz = re_charEntity.search(htmlstr)
        while sz:
            # entity=sz.group()
            key = sz.group('name')  # 命名组的获取
            try:
                htmlstr = re_charEntity.sub(CHAR_ENTITIES[key], htmlstr, 1)  # 1表示替换第一个匹配
                sz = re_charEntity.search(htmlstr)
            except KeyError:
                htmlstr = re_charEntity.sub('', htmlstr, 1)
                sz = re_charEntity.search(htmlstr)
        return htmlstr

    @staticmethod
    def getLogFileName(currentLogPath, currentProjectPath):
        """
        返回以项目路径为根路径的 相对路径  例如 ： projectPath/es/Note.py  会返回  es_Note
        Args:
            currentLogPath:  当前执行文件的路径
            currentProjectPath: 项目路径

        Returns:

        """
        absLogPath = re.sub('^(' + currentProjectPath + '/)', '', currentLogPath)
        absLogPath = absLogPath.split("/")
        return "_".join(absLogPath).replace(".py", "")

    @classmethod
    def MD5(cls, beMd5Str):
        """
        md5 加密
        Args:
            beMd5Str:  被加密的数据

        Returns:

        """
        md = hashlib.md5()  # 创建md5对象
        md.update(beMd5Str.encode(encoding="utf-8"))
        return md.hexdigest()

    @classmethod
    def getTypeByObjId(cls, objId):
        """
        获取内容类型
        Args:
            objId:  内容id

        Returns:

        """
        typeStr = objId[8:9]
        return int(typeStr)

    @classmethod
    def getTableNumByUidForPhoto(self, uid):
        subTableNum = 4
        uidStr = str(uid).encode('utf8')
        uidCrc32 = zlib.crc32(uidStr)
        return (int(uidCrc32 / subTableNum)) % subTableNum

    @classmethod
    def get_dir_size(cls, dir):
        '''
        Author: xiaoyichao
        param {*}
        Description: 返回文件夹的大小，单位M
        '''
        dir_size = 0
        for root, dirs, files in os.walk(dir):
            dir_size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
        return ((dir_size / 1024) / 1024)


def get_models(dir_path, reverse=True):
    '''
    @Author: xiaoyichao
    @param {*}
    @Description: 返回文件夹里所有的文件路径（倒序）和最新文件路径
    '''
    model_list = sorted(os.listdir(dir_path), reverse=reverse)
    model_path_list = [os.path.join(dir_path, model_name) for model_name in model_list]
    for mode_path in model_path_list:
        if os.path.isdir(mode_path):  # 是否是文件夹
            if not os.listdir(mode_path):  # 是否是空文件夹
                model_path_list.remove(mode_path)
                os.rmdir(mode_path)
    return model_list, model_path_list


def get_before_day(before_day):
    '''
    Author: xiaoyichao
    param {*}
    Description: 获取几天前的日期
    '''
    import datetime
    today = datetime.date.today()
    before_days = datetime.timedelta(days=before_day)
    before_day = today - before_days
    return str(before_day)


if __name__ == '__main__':
    print(Tool.getTableNumByUidForPhoto(11907))

