import os
import sys

blackList = ["Ilyich Genshin Test Version\common\备份文件", "Ilyich Genshin Test Version/common/备份文件"]

def CheckFile(filePath):
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
                        print("文件出错: %s error %s, 行号: %d" % (filePath, record, index))
                        fileCorrect = False
        if len(record) > 0:
            print("文件出错: %s error %s, 行号: %d" % (filePath, record, index+1))
            fileCorrect = False
    return fileCorrect

def CheckDir(dirPath):
    allFilesCorrect = True
    files = os.listdir(dirPath)
    for file in files:
        filePath = os.path.join(dirPath, file)
        if filePath in blackList:
            continue
        if os.path.isfile(filePath) and ".txt" in file:
            allFilesCorrect = (CheckFile(filePath) and allFilesCorrect)
        elif os.path.isdir(filePath):
            allFilesCorrect = (CheckDir(filePath) and allFilesCorrect)
    return allFilesCorrect

def main():
    modPath = "Ilyich Genshin Test Version"
    if not CheckDir(modPath):
        sys.exit(1)

if __name__ == "__main__":
    main()
