## 我不小心点了commit，如何撤回？
- 在GitHub Desktop中点击history，找到你刚刚不小心创建的提交，右键选择`Undo commit`


## 我准备提交代码时，发现有一个`Force push origin`的选项，我可以点他吗？
- 出现这个选项，意味着其他人已经在GitHub上提交了新的修改，但是你的本地没有这个新修改
- 此时选择`Force push origin`将会以你本地的版本，强制覆盖GitHub上的版本，导致GitHub上别人的修改被丢弃，所以不要使用这个操作


## 我不小心把错误的修改Push到了github上，怎么办？
- 在history中找到你错误的commit，右键选择`Revert changes in commit`。软件将会帮你生成一个撤回修改的提交，此时再Push到GitHub上，就可以把你刚刚的错误修改撤销了。
- 注意，一旦修改提交到GitHub上，即使后面使用Revert撤销修改，也是会留下记录的


## 我想把一部分修改，给另一位开发者先看一下，但不想合入master分支，怎么办？
- 该场景常见于合作开发，或需要别人帮忙找bug的时候
1. 在GitHub Desktop上方的Current branch处，选择创建新分支
2. 在新分支上进行你的修改。**请注意看下上方的Current branch，确认你是否处于新分支**
3. Push到GitHub上，此时你的修改就可以在GitHub上的对应分支里看到

