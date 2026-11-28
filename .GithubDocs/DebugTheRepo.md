#  如何使用git仓库内的代码进行调试
- 目前使用gamma版本，将仓库下的`Daybreak of Teyvat Gamma Version/Daybreak of Teyvat Gamma Version.mod`复制至钢4的mod目录下，如下是一个参考，具体取决于你的本地路径
  ```
  C:\Users\your_name\Documents\Paradox Interactive\Hearts of Iron IV\mod
  ```
- 修改钢4mod目录的下`descriptor.mod`
  - 添加`path`为“`本地仓库路径/Daybreak of Teyvat Gamma Version`”（注意路径的斜杠与反斜杠区别），例如
    ```
    path="D:/code/hoi4mod/Ilyich-Genshin-Test-Version/Daybreak of Teyvat Gamma Version"
    ```
- 启动钢4时，使用刚刚你改名的mod进行调试
