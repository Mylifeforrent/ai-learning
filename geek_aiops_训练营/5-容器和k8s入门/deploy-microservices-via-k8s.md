![img.png](img.png)
![img_1.png](img_1.png)
![img_2.png](img_2.png)
![img_3.png](img_3.png)

容器化部署node项目，这个tini推荐使用，
![img_4.png](img_4.png)

![img_5.png](img_5.png)
方案1，业务重试，但是依然我们写代码，需要依赖我们的开发
![img_6.png](img_6.png)
方案2:k8s自动重启机制
![img_7.png](img_7.png)
![img_8.png](img_8.png)

安排依赖关系
![img_9.png](img_9.png)
![img_10.png](img_10.png)
![img_11.png](img_11.png)

微服务启动顺序控制
![img_12.png](img_12.png)
先启动redis，因此redis这里不需要任何依赖
![img_13.png](img_13.png)
pg需要等redis，这里加上控制
![img_14.png](img_14.png)
worker需要等db，这里加上控制
![img_15.png](img_15.png)
vote等worker
![img_16.png](img_16.png)
result等待vote
![img_17.png](img_17.png)


数据库表初始化
![img_18.png](img_18.png)
中间件高可用部署
![img_19.png](img_19.png)
![img_20.png](img_20.png)





































