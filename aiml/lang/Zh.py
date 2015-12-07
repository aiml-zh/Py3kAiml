#!/usr/bin/env python3
#coding=utf-8

# -----------------------------------------------------------------------------
'''
Initialize JieBa word segmenter. JieBa need the absoulte path of dictionary!!!
'''
import jieba
import jieba.posseg as pseg
import re
import os.path

mod_dir = os.path.dirname(__file__)
if os.path.exists(os.path.join(mod_dir, 'Zh.dict.txt')):
    jieba.set_dictionary(os.path.join(mod_dir, 'Zh.dict.txt'))
if os.path.exists(os.path.join(mod_dir, 'Zh.user.dict.txt')):
    jieba.load_userdict(os.path.join(mod_dir, 'Zh.user.dict.txt'))

aimlCorpusFea = {}
aimlCorpus = {}
for line in open(os.path.join(mod_dir, 'Zh.question.txt'),'r'):
    lines = line.strip().split(',')
    tmp = []
    for i,j in enumerate(lines,0):
        if i not in (0,1):
            tmp.append(j)
    aimlCorpusFea[lines[0]] = tmp
    aimlCorpus[lines[0]] = lines[1]

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
#
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
    marked = ''.join((' __CH__' + i + '__CH__ ' if isChinese(i) else i for i in s))
    marked = re.sub(r'__CH__\s+__CH__', '', marked)
    marked = re.sub(r'\s*__CH__\s*', ' ', marked)
    #marked = re.sub(r'__CH__\s+', ' ', marked)
    return marked.strip()

def mapToAimlCorpus(questionInput):
	hit = {}
	for key in aimlCorpus:
		hit[key] = 0
		for tag in aimlCorpusFea[key]:
			hit[key] += questionInput.count(tag)/len(questionInput)

	output = ''
	sorted_corpus = sorted(hit, key=hit.get, reverse=True)
	if hit[sorted_corpus[0]] == 0:
		output = questionInput
	else:
		output = aimlCorpus[sorted_corpus[0]]
		words = pseg.cut(questionInput)
		if sorted_corpus[0] in ('time','weather','height','capital','query','author','lang'):
			for word,flag in words:
				if flag[0] == 'n' and word not in aimlCorpusFea[sorted_corpus[0]]:
					output = output.replace('*',word)
			if sorted_corpus[0] in ('time','weather'):
				output = output.replace('*','')
		elif sorted_corpus[0] == 'who':
			rules = ["n-u-n","n-u-x","n"]
			tmp_w = []
			tmp_f = []
			for word,flag in words:
				tmp_w.append(word)
				tmp_f.append(flag[0])
			tmp_af = '-'.join(tmp_f)
			for rule in rules:
				tmp_pos = tmp_af.find(rule)
				if tmp_pos != -1:
					tmp_pos = int(tmp_pos/2)
					output = output.replace('*',''.join(tmp_w[int(tmp_pos):int(tmp_pos+(len(rule)+1)/2)]))
					break
		elif sorted_corpus[0] == 'joke':
			output = aimlCorpus[sorted_corpus[0]]
		elif sorted_corpus[0] in ('alarm','remind'):
			num_keywords = ['一','二','兩','三','四','五','六','七','八','九','十']
			timer_keywords = ['分鐘','小時','點']
			period = ['早上','下午','晚上']
			for t in timer_keywords:
				tmp_pos = questionInput.find(t)
				if tmp_pos != -1:
					for i in range(tmp_pos-1,-1,-1):
						if questionInput[i] not in num_keywords and i != tmp_pos-1:
							output = output.replace('*',''.join(questionInput[i+1:tmp_pos+len(t)]))
							for p in period:
								if questionInput[0:i+1].find(p) != -1:
									output = p + output
									break
							break
						elif questionInput[i] not in num_keywords:
							break
						if i == 0:
							output = output.replace('*',''.join(questionInput[0:tmp_pos+len(t)]))
					if output.find('*') == -1:
						break
			if sorted_corpus[0] == 'remind':
				for fea in aimlCorpusFea[sorted_corpus[0]]:
					tmp_pos = questionInput.find(fea)
					if tmp_pos != -1:
						output = output.replace('-',''.join(questionInput[tmp_pos+len(fea):]))
						break
				output = output.replace('-','')
	if output.find('*') != -1:
		return ' '.join(jieba.cut(questionInput))
	else:
		return ' '.join(jieba.cut(output))

preprocess = lambda line: mapToAimlCorpus(line)
postprocess = lambda line: mergeChineseSpace(line)
patternPreprocess = lambda line: ' '.join(splitChinese(line))

if __name__ == '__main__':
    import sys
    try:
        arg_fun = {'-p': patternPreprocess, '-o': postprocess, '-i': preprocess}
        line = ' '.join(sys.argv[2:])
        ret = arg_fun[sys.argv[1]](line)
        print(ret)
    except Exception as err:
        print(err, file=sys.stderr)
        print('{} -i 要給 preprocess 分析的句子'.format(sys.argv[0]), file=sys.stderr)
        print('{} -o 要給 postprocess 分析的句子'.format(sys.argv[0]), file=sys.stderr)
        print('{} -p 要給 patternPreprocess 分析的句子'.format(sys.argv[0]), file=sys.stderr)
