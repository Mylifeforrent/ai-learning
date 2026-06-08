![img.png](img.png)

当前页面操作创建资源的缺点：
需要管理员权限不安全，而且你点了什么别人不知道。

![img_1.png](img_1.png)
第二种方式就是调用sdk来创建资源，命令式的方式
![img_2.png](img_2.png)

第三种：声明式的方式，你只是关注结果，而且这个定义是有状态的设计，它会自动对比版本差异进行增删改查，而且是幂等性
![img_3.png](img_3.png)
![img_4.png](img_4.png)
![img_5.png](img_5.png)
![img_6.png](img_6.png)
![img_7.png](img_7.png)
![img_8.png](img_8.png)

HCL/DSL--领域特定语言
![img_9.png](img_9.png)
![img_10.png](img_10.png)
![img_11.png](img_11.png)

基本上都是这种架构设计，core负责核心的差异提取，然后总结为需要操作的步骤细节，
最后根据每个厂商自己维护的provider，通过定义好的接口来调用具体的实现就可以了
达到解耦的效果。
![img_12.png](img_12.png)
![img_13.png](img_13.png)

![img_14.png](img_14.png)

Demo
![img_15.png](img_15.png)
![img_16.png](img_16.png)
![img_17.png](img_17.png)
![img_18.png](img_18.png)
![img_19.png](img_19.png)
![img_20.png](img_20.png)
![img_21.png](img_21.png)
上面的方式配置key其实不太好，建议环境变量方式配置key
![img_22.png](img_22.png)
terraform init，初始化配置的provider
![img_23.png](img_23.png)
terraform plan 检查你的修改和影响
terraform apply执行你的修改，刚才老师执行apply出错了，因为cpu1,memory 10的那个卖完了。最后他只保留了cpu 1，memory让terraform自己帮忙自动匹配有存货的instance，这样就可以创建成功了
![img_24.png](img_24.png)
![img_25.png](img_25.png)
基本上可以理解为terraform是对各家厂商sdk方式的上层封装，不然每个人都要去写代码然后维护云机器的申请和创建，就比较麻烦。
terraform就把命令式的交互方式，进行封装，变为声明式方式。把代码api调用隐藏到每个云厂商自己维护的provider里面去了。
通过terraform destroy销毁资源
![img_26.png](img_26.png)
![img_27.png](img_27.png)
![img_28.png](img_28.png)

![img_29.png](img_29.png)
![img_30.png](img_30.png)
团队协作的时候，这个terraform state file很重要，不要上传到git，因为里面有敏感信息。

![img_31.png](img_31.png)
Demo2-导入资源，
这里假设terraform是一个全新的init出来的仓库。但是呢你之前手动创建过了一个instance，
现在你希望terraform可以管理到这个instance，你需要做的就是，参考正常情况下这个资源的名字和目前已有的instance id。
按照terraform import命令进行导入。
举例： 这里针对tencent的资源名字 叫做 “tencentcloud_instance.web”，然后去控制台把你的instanceid 复制过来。

![img_32.png](img_32.png)
过了一会，你就发现你的state文件创建好了
![img_33.png](img_33.png)
几种情况对比讨论：
第一种： 
terraform发现你配置文件里有这个instance配置信息，state里没有这个配置信息，当你执行terraform apply时候，它会去真实的云厂商检查你的instance是不是真实存在，也就是说reality事实检查，结果发现，根本不存在。那么为了和你的配置文件对齐，这个时候会创建文件，并且更新state文件
第二种：
和第一种类似，基本上也是以配置文件为准，发现配置文件有instance，但是实际上没创建。那么把instance创建出来，至于state文件，基本不用改动，毕竟state里面标准的是instance存在
第三种：
啥都不错，他们状态都是对齐的
第四种：
配置文件不存在，state存在，但是instance实际上存在，删除掉他
第五种：
配置文件不存在，state也不存在，但是instance实际上存在。那么什么都不做，基本确定不是有terraform管理的这个instance
第六种：
配置文件不存在，state文件存在，但是实际上instance不存在。那么terraform会更新一下state文件的内容。

![img_34.png](img_34.png)

本地vs远端
![img_35.png](img_35.png)
terraform cloud五个人以下，免费使用
![img_36.png](img_36.png)
![img_37.png](img_37.png)
![img_38.png](img_38.png)
![img_39.png](img_39.png)

aws remote backend
![img_40.png](img_40.png)

tencent cos
![img_41.png](img_41.png)

一个思考问题：
你希望terraform去创建对象存储，方便你后面放state文件。但是呢你创建terraform的初始化过程又需要依赖着对象存储。相当于说
死循环：terraform -->创建对象存储 -->需要先有位置给我放terraform管理的state文件 --》 这个位置需要依赖terraform去创建
![img_42.png](img_42.png)
创建cos bucket
![img_43.png](img_43.png)
![img_44.png](img_44.png)
设置加密
![img_45.png](img_45.png)

apply之后创建cvm和cos
![img_46.png](img_46.png)
从local转移到cos去保存state
![img_47.png](img_47.png)
配置backend cos
![img_48.png](img_48.png)
找到bucket id然后改一改配置
![img_49.png](img_49.png)
![img_50.png](img_50.png)
执行apply命令，按照要求输入init和yes确认迁移动作
![img_51.png](img_51.png)
这个时候就发现你的本地state清空了，state 文件迁移到了cos
![img_52.png](img_52.png)

![img_53.png](img_53.png)
 


























































































