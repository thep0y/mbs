# mbs
博客管理器，可以管理多个博客的文章。

## 使用

### 1 安装

```shell
python install mbs
```

### 2 命令

```shell
usage: mbs [-h] [-cs] [-n CATEGORY MARKDOWN_FILE_PATH] [-d TITLE] [-sc FOLDER] [-uo PATH] [-ua FOLDER]

博客管理器

optional arguments:
  -h, --help            显示当前帮助信息，然后退出
  -cs, --categories     显示所有分类
  -n CATEGORY MARKDOWN_FILE_PATH, --new-post CATEGORY MARKDOWN_FILE_PATH
                        要上传的 markdown 文件的分类和路径
  -d TITLE, --delete TITLE
                        要删除的文章标题
  -sc FOLDER, --scan-changed-files FOLDER
                        扫描目标文件中所有有变化的文件
  -uo PATH, --update-one PATH
                        更新一个文件
  -ua FOLDER, --update-all FOLDER
                        更新指定目录中的所有文件
```

### 3 当前支持的博客

- 博客园
- 简书

### 4 问题

- [ ] 部分代码写得难看，因为能使用，暂时就没有优化

### 5 debug

默认日志是保存在文件里，不在终端输出，但有时可能会遇到执行一条命令后终端没有任何输出，查看日志或者启动 debug。

日志文件路径：

- windows  `%APPDATA%\mbs\mbs.log`
- Linux/Mac `$HOME/.config/mbs/mbs.log`

开启 debug 模式可以在终端也输出日志，因为日志文件一样可以看，所以此功能作用不大。开启方式为在当前终端设置环境变量`MBS_DEBUG=1`。

### 6 注意

当前仅对使用`mbs`上传的文章进行管理，其他已经上传的文章，需要自己想办法将有关数据添加到数据库中。

数据库文件与日志文件在同一个目录中。





