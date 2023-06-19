# 第一次进入开发请看这里
## 如何克隆（下载）仓库到本地
- 如果你的GitHub账号还未加入[组织](https://github.com/Daybreak-of-Teyvat-Studio)，请先将GitHub账号发到群里，找管理员加下权限
- 安装GitHub Desktop后，在网页仓库的右上角“Code”处，选择“Open with GitHub Desktop”，然后选择要存放的本地路径。
  - 或者直接在本地打开GitHub Desktop，克隆仓库`https://github.com/Daybreak-of-Teyvat-Studio/Ilyich-Genshin-Test-Version.git`。
- 如果遇到克隆速度慢的问题，可尝试挂梯子，或者使用[steampp](https://steampp.net/)。

## 一些推荐配置
- 打开.git/config文件（.git是隐藏文件夹，看不到的话可以百度如何查看隐藏文件夹），在末尾添加：
  ```
  [pull]
      rebase = true
  ```
