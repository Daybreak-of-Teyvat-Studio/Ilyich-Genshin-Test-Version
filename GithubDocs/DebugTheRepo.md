#  如何使用git仓库内的代码进行调试
- 将仓库根目录下的`Ilyich Genshin Test Version.mod`复制至钢4的mod目录下，如下是一个参考，具体取决于你的本地路径
  ```
  C:\Users\your_name\Documents\Paradox Interactive\Hearts of Iron IV\mod
  ```
- 修改钢4mod目录的下`Ilyich Genshin Test Version.mod`
  - `name`修改为任意自定义名字，不要与现有的mod名重复即可（包括提瓦特黎明的正式版及测试版），例如
    ```
    name="Daybreak of Teyvat | Git Version"
    ```
  - `path`修改为“`本地仓库路径/Ilyich Genshin Test Version`”，例如
    ```
    path="D:/code/hoi4mod/Ilyich-Genshin-Test-Version/Ilyich Genshin Test Version"
    ```
- 启动钢4时，使用刚刚你改名的mod进行调试
