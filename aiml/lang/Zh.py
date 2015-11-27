#!/usr/bin/env python3
#coding=utf-8

# -----------------------------------------------------------------------------
'''
Initialize JieBa word segmenter. JieBa need the absoulte path of dictionary!!!
'''
import jieba
import os.path

mod_dir = os.path.dirname(__file__)
if os.path.exists(os.path.join(mod_dir, 'Zh.dict.txt')):
    jieba.set_dictionary(os.path.join(mod_dir, 'Zh.dict.txt'))
# -----------------------------------------------------------------------------
def isChinese(c):
    # http://www.iteye.com/topic/558050
    r = [
        # 标准CJK文字
        (0x3400, 0x4DB5), (0x4E00, 0x9FA5), (0x9FA6, 0x9FBB), (0xF900, 0xFA2D),
        (0xFA30, 0xFA6A), (0xFA70, 0xFAD9), (0x20000, 0x2A6D6), (0x2F800, 0x2FA1D),
        # 全角ASCII、全角中英文标点、半宽片假名、半宽平假名、半宽韩文字母
        (0xFF00, 0xFFEF),
        # CJK部首补充
        (0x2E80, 0x2EFF),
        # CJK标点符号
        (0x3000, 0x303F),
        # CJK笔划
        (0x31C0, 0x31EF)]
    #print("[中文字] Input is ", c)

    return any(s <= ord(c) <= e for s, e in r)
# -----------------------------------------------------------------------------
'''
2015.0814 Added By Liang
'''
def removeSpace(seg_list):
    return [i for i in seg_list if i not in (' ',',','.')]
'''
    lsClean = []
    for s in seg_list:
        if s not in [' ',',','.']:
            lsClean.append(s)
    return lsClean
'''
# -----------------------------------------------------------------------------
'''
2015.0819 Added By Liang
AIMLParser parse <bot name="name"> to BOT_NAME, so JieBa should process BOT_NAME instead of processing bot tag
'''
# def processTag(seg_list):
#     bEng = False
#     szEng = ""
#     lsCompile = []
#     for s in seg_list:
#         if s=="<":
#             bEng = True
#             szEng = s
#         elif s == ">" and bEng == True:
#             szEng +=s
#             lsCompile.append(szEng)
#             szEng = ""
#             bEng = False
#         elif bEng == True:
#             szEng +=s
#         elif bEng == False:
#             lsCompile.append(s)
#     # 
#     return lsCompile
def processTag(seg_list):
    lsCompile = []
    try:
        seg_list = list(seg_list)
        for i, s in enumerate(seg_list):
            if s == "BOT" and seg_list[i+1]=="_" and seg_list[i+2]=="NAME":
                seg_list[i]="BOT_NAME"
                del seg_list[i+2]
                del seg_list[i+1]
                lsCompile.append(seg_list[i])
            else:
                lsCompile.append(s)
    except Exception as noBot:
        return seg_list
    # 
    return lsCompile
# -----------------------------------------------------------------------------
def splitChinese(s):
    result = []
    seg_list = jieba.cut(s)
    seg_list = processTag(seg_list)
    seg_list = removeSpace(seg_list)
    szEng = ""
    bEng = False
    for c in seg_list:
        #print("\033[1;31;40m[jieba] %s\033[0m",c)
        # if isChinese(c[0]):
        #     print("[中文字] ",c)
        #     result.extend([" ", c, " "])
        # else:
        #     result.append(c)
        if c == "<":
            #<bot name="name"> tag should not be split !!!
            szEng = c
            bEng = True
        elif bEng == True:
            szEng += c
        elif c ==">":
            szEng = c
            result.extend([" ", szEng, " "])
            szEng = ""
            bEng =False
        elif bEng == False:
            result.extend([" ", c, " "])
    ret = ''.join(result)

    return ret.split()
# -----------------------------------------------------------------------------
def splitUnicode(s):
    # assert type(s) == unicode, "string must be a unicode"
    segs = s.split()
    result = []
    for seg in segs:
        if any(map(isChinese, seg)):
            result.extend(splitChinese(seg))
        else:
            result.append(seg)
    return result

def mergeChineseSpace(s):
    # assert type(s) == unicode, "string must be a unicode"
    #print("[中文字] LangSupport::mergeChineseSpace() input = ",s)
    segs = splitChinese(s)
    #print("[中文字] LangSupport::mergeChineseSpace() segs = ",segs)
    # result = []
    # for seg in segs:
    #     # English marks
    #     if seg[0] not in ".,?!":
    #         print("[中文字] LangSupport::mergeChineseSpace() seg[0] =", seg[0])    
    #         try:
    #             str(seg[0]) and result.append(" ")
    #         except:
    #             pass
    #     result.append(seg)
    #     print("[中文字] LangSupport::mergeChineseSpace() result =", result)
    #     try:
    #         str(seg[-1]) and result.append(" ")
    #     except:
    #         pass
    # ---- cross-language processing ----
    # 2015.0817 added by Liang
    lsCrossLang = []
    for c in segs:
        if isChinese(c[0]):
            lsCrossLang.append(c)
        else:
            lsCrossLang.append(" ")
            lsCrossLang.append(c)
    return ''.join(lsCrossLang).strip()

preprocess = lambda *args, **kwargs: ' '.join(splitChinese(*args, **kwargs))
postprocess = lambda *args, **kwargs: mergeChineseSpace(*args, **kwargs)
