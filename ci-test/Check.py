import os
import sys
import chardet

blackList = ["Daybreak of Teyvat Alpha Version\common\备份文件", "Daybreak of Teyvat Alpha Version/common/备份文件", 
             "Daybreak of Teyvat Alpha Version\.backups", "Daybreak of Teyvat Alpha Version/.backups",
             "Daybreak of Teyvat Beta Version\common\备份文件", "Daybreak of Teyvat Beta Version/common/备份文件", 
             "Daybreak of Teyvat Beta Version\.backups", "Daybreak of Teyvat Beta Version/.backups"]

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

def CheckDirWithFilter(dirPath, fileExtensions, checkFunction):
    """
    通用的目录检查函数

    Args:
        dirPath: 要检查的目录路径
        fileExtensions: 文件扩展名列表，如 ['.yml'] 或 ['.txt', '.gui']
        checkFunction: 文件检查函数，接收 filePath 参数，返回 bool

    Returns:
        bool: 所有文件是否都正确
    """
    allFilesCorrect = True
    files = os.listdir(dirPath)
    for file in files:
        filePath = os.path.join(dirPath, file)
        if filePath in blackList:
            continue
        elif os.path.isfile(filePath) and any(ext in file for ext in fileExtensions):
            allFilesCorrect = (checkFunction(filePath) and allFilesCorrect)
        elif os.path.isdir(filePath):
            allFilesCorrect = (CheckDirWithFilter(filePath, fileExtensions, checkFunction) and allFilesCorrect)
    return allFilesCorrect

def CheckDirQuotation(dirPath):
    return CheckDirWithFilter(dirPath, ['.yml'], CheckFileQuotation)

# 检测本地化文件的编码格式
def CheckFileEncoding(filePath):
    with open(filePath, 'rb') as f:
        det = chardet.detect(f.read())
        if det['encoding'] == "UTF-8-SIG": # utf-8-bom会被chardet检测为UTF-8-SIG
            return True
        print("文件出错: %s 文件编码格式为: %s" % (filePath, det['encoding']))
        return False

def CheckDirEncoding(dirPath):
    return CheckDirWithFilter(dirPath, ['.yml'], CheckFileEncoding)

# 检测txt、gui文件的大括号匹配
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
    return CheckDirWithFilter(dirPath, ['.txt', '.gui'], CheckFileBracket)

def main():
    modPath = "Daybreak of Teyvat Beta Version"
    if not CheckDirBracket(modPath):
        sys.exit(1)
    chineseLocalisationPath = "Daybreak of Teyvat Beta Version/localisation/simp_chinese"
    englishLocalisationPath = "Daybreak of Teyvat Beta Version/localisation/english"
    if not CheckDirQuotation(chineseLocalisationPath): # 目前引号只检测中文
        sys.exit(1)
    if not (CheckDirEncoding(chineseLocalisationPath) and CheckDirEncoding(englishLocalisationPath)):
        sys.exit(1)

if __name__ == "__main__":
    main()
