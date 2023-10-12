import os
import sys

blackList = ["Ilyich Genshin Test Version\common\备份文件", "Ilyich Genshin Test Version/common/备份文件", 
             "Ilyich Genshin Test Version\.backups", "Ilyich Genshin Test Version/.backups"]

# 检测本地化文件的双引号
def CheckFileQuotation(filePath):
    fileCorrect = True
    with open(filePath, 'r', errors='ignore') as f:
        content = f.readlines()
        index = 0
        for line in content:
            quotationCount = 0
            index += 1
            if len(line) == 0:
                continue
            lastChar = line[0]
            for c in line:
                if c == '#' and quotationCount != 1:
                    break
                elif c == '\"' and lastChar != "\\":
                    quotationCount += 1
                lastChar = c
            if quotationCount != 0 and quotationCount != 2:
                print("文件出错: %s 英文双引号有问题, 行号: %d" % (filePath, index))
                fileCorrect = False
    return fileCorrect

def CheckDirQuotation(dirPath):
    allFilesCorrect = True
    files = os.listdir(dirPath)
    for file in files:
        filePath = os.path.join(dirPath, file)
        if filePath in blackList:
            continue
        elif os.path.isfile(filePath) and ".yml" in file:
            allFilesCorrect = (CheckFileQuotation(filePath) and allFilesCorrect)
        elif os.path.isdir(filePath):
            allFilesCorrect = (CheckDirQuotation(filePath) and allFilesCorrect)
    return allFilesCorrect

# 检测txt文件的大括号匹配
def CheckFileBracket(filePath):
    fileCorrect = True
    with open(filePath, 'r', errors='ignore') as f:
        content = f.readlines()
        record = []
        index = 0
        for line in content:
            index += 1
            for c in line:
                if c == '#':
                    break
                elif c == '{':
                    record.append('{')
                elif c == '}':
                    if len(record) > 0:
                        if record[-1] == '{':
                            record.pop()
                        else:
                            record.append('}')
                    else:
                        print("文件出错: %s 大括号不匹配 %s, 行号: %d" % (filePath, record, index))
                        fileCorrect = False
        if len(record) > 0:
            print("文件出错: %s 大括号不匹配 %s, 行号: %d" % (filePath, record, index+1))
            fileCorrect = False
    return fileCorrect

def CheckDirBracket(dirPath):
    allFilesCorrect = True
    files = os.listdir(dirPath)
    for file in files:
        filePath = os.path.join(dirPath, file)
        if filePath in blackList:
            continue
        if os.path.isfile(filePath) and ".txt" in file:
            allFilesCorrect = (CheckFileBracket(filePath) and allFilesCorrect)
        elif os.path.isdir(filePath):
            allFilesCorrect = (CheckDirBracket(filePath) and allFilesCorrect)
    return allFilesCorrect

def main():
    modPath = "Ilyich Genshin Test Version"
    if not CheckDirBracket(modPath):
        sys.exit(1)
    chineseLocalisationPath = "Ilyich Genshin Test Version/localisation/simp_chinese" # 目前只检测中文
    if not CheckDirQuotation(chineseLocalisationPath):
        sys.exit(1)

if __name__ == "__main__":
    main()
