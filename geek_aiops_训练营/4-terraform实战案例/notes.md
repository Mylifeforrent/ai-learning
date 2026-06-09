拆分为4个文件比较友好，layout比较合理一点
![img.png](img.png)
![img_1.png](img_1.png)
![img_2.png](img_2.png)
![img_3.png](img_3.png) 
第三种方式更加推荐，定义环境变量
![img_4.png](img_4.png)
![img_5.png](img_5.png)
Demo4
![img_6.png](img_6.png)
![img_7.png](img_7.png)
![img_8.png](img_8.png)
把main.tf拆开为几个细分的tf:cvm.tf, helm.tf, k3s.tf
![img_9.png](img_9.png)
![img_10.png](img_10.png)
![img_11.png](img_11.png)
![img_12.png](img_12.png)
helm依赖k3s，所以这里要标注一下。这样terraform做计划的时候会根据你的这些依赖关系，形成一个graph 有向无环图
![img_13.png](img_13.png)
定义output
![img_14.png](img_14.png)

init一下之后，使用export命令把你定义的环境变量传进去，后面执行apply
![img_15.png](img_15.png)
![img_16.png](img_16.png)
可以通过命令，生成graph给你查看执行顺序
![img_17.png](img_17.png)
 

进阶实战
![img_18.png](img_18.png)
![img_19.png](img_19.png)
![img_20.png](img_20.png)

count方式指定之后，这里“web”后面会被带上索引，后续你搜索会比较快，类似于应该会加一个sequence number
![img_21.png](img_21.png)
foreach
![img_22.png](img_22.png)
lifecycle，一般第一个用的多一点
![img_23.png](img_23.png)
fileprovisoner
![img_24.png](img_24.png)
![img_25.png](img_25.png)
![img_26.png](img_26.png)
![img_27.png](img_27.png)

如何创建多环境基础设施？
![img_28.png](img_28.png)
![img_29.png](img_29.png)

![img_30.png](img_30.png)
列出已有的workspace，然后创建新的workspace
![img_31.png](img_31.png)
在创建一个testing workspace，新的目录结构这个样子
切换workspace使用类似workspace select dev这样的命令
![img_32.png](img_32.png)
执行apply命令之后，对应的文件夹就会出现state文件
![img_33.png](img_33.png)
workspace还是有点不太好
![img_34.png](img_34.png)

module+目录隔离，更加安全
![img_35.png](img_35.png)
![img_36.png](img_36.png)
模块之间可以引用
![img_37.png](img_37.png)
![img_38.png](img_38.png)

Demo5，module+目录隔离
定义模块
![img_39.png](img_39.png)
定义不同的文件夹（dev，testing etc.）来使用定义好的module
![img_40.png](img_40.png)
所以基本上你只需要修改module，就可以保证配置不会散乱
![img_41.png](img_41.png)
![img_42.png](img_42.png)

其他IaC工具：Crossplane。这里跳过学习，后续又需要在学











































































































 






















