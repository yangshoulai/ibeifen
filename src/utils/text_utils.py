import jieba

def tokenize_text(text: str) -> str:
    """
    对文本进行分词
    :param text: 输入文本
    :return: 分词后的文本，以空格分隔
    """
    if not text:
        return ""
    words = jieba.cut(text)
    return " ".join(words) 