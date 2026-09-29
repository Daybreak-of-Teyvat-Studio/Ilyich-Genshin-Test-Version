# 使用[VSCode][vscode]开发

相较[GitHub Desktop](https://desktop.github.com/)，VSCode自由度更高，当然配置也略繁琐。

## 环境搭建

1. 前往[VSCode官网][vscode]下载并安装Visual Studio Code。
2. 前往[Git官网](https://git-scm.com/download/win/)下载并安装Git。
3. 重启计算机以应用对环境变量Path的更改。
4. 启动终端，输入：
    ```shell
    git config --global user.name 你的GitHub账户名

    git config --global user.email 你注册GitHub用的邮箱
    ```
5. 启动VSCode，按指示设置主题，安装简中语言包。
6. VSCode重启后，侧边栏选择“扩展”，搜索并安装"GitLens"（Git可视化）与"CWTools"（P社语言支持）。
7. 克隆仓库：
    ```shell
    git clone https://github.com/Daybreak-of-Teyvat-Studio/Daybreak-of-Teyvat.git 
    ```
8. 选择文件->打开文件夹，选取本地克隆的仓库。
9.  文件->将工作区另存为->保存。
10.  TODO：CWTools的配置
  
## 使用VSCode自带的源代码管理功能

[vscode]: https://code.visualstudio.com/
