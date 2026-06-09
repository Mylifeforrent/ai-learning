![img_21.png](img_21.png)
![img_22.png](img_22.png)

char是应用安装包的概念 OCI格式。

![img_23.png](img_23.png)
先把结论说人话：

**Helm 的 OCI 格式 = 把 Helm Chart 当成“容器镜像一样的东西”，存到普通的 Docker 镜像仓库里，用和镜像一样的方式来推送、拉取、版本管理。**

下面拆开讲清楚：

---

## 1. OCI 是什么？
**OCI = Open Container Initiative（开放容器标准）**  
就是一套**统一容器镜像格式和分发协议**的规范，现在所有主流容器（Docker、containerd、K8s）都遵循它。

简单理解：
- Docker 镜像 = 符合 OCI 标准的文件包
- 镜像仓库（Docker Hub、GHCR、Harbor、ECR…）= 支持 OCI 协议的存储服务

---

## 2. Helm 的传统方式（非 OCI）
以前 Helm Chart 是这么分发的：

- 你搭一个 HTTP 服务器（比如 ChartMuseum、S3 静态站）
- 放一个 `index.yaml`，里面记录所有 Chart 名字、版本、下载地址
- 用户要先 `helm repo add` 这个地址，再 `helm install`

缺点：
- **要单独维护一套 Helm 仓库**，和镜像仓库分开
- 认证、权限、扫描、备份都要单独搞
- 依赖 `index.yaml`，版本一多容易乱

---

## 3. Helm 的 OCI 格式（核心）
Helm 3.8+ 正式支持：**把 Chart 打包成一个 OCI 制品（Artifact）**  
也就是说：

> **Chart ≈ 一个特殊的 Docker 镜像**  
> 可以直接 push 到任意 OCI 镜像仓库（Docker Hub、Harbor、GHCR…）

### 关键变化
- 地址写法：`oci://仓库地址/chart名`
- 不用 `helm repo add`，直接 `helm push/pull/install`
- 版本用 **Tag**（和镜像一样），例如 `oci://my-reg/nginx:1.2.3`
- 底层是 OCI 标准的：**manifest + layers**，和镜像结构一致

### 举个命令对比

传统方式：
```bash
helm repo add stable https://xxx.com
helm install my-nginx stable/nginx --version 1.2.3
```

OCI 方式：
```bash
# 登录镜像仓库（和 docker login 一样）
helm registry login my-registry.com

# 推送 chart 到 OCI 仓库
helm push nginx-1.2.3.tgz oci://my-registry.com/helm-charts

# 直接安装
helm install my-nginx oci://my-registry.com/helm-charts/nginx --version 1.2.3
```

---

## 4. 为什么要 OCI 格式？（好处）
1. **一套仓库管所有**  
   镜像和 Chart 都放同一个仓库，**统一认证、统一权限、统一扫描、统一备份**

2. **更安全**  
   用 **SHA256 摘要**定位 Chart，不可篡改；支持签名、扫描漏洞

3. **更简单**  
   不用维护 `index.yaml`，不用 `helm repo add`，CI/CD 流程更干净

4. **生态统一**  
   Harbor、GHCR、ECR、ACR 全支持，不用额外部署 Chart 仓库

---

## 5. 一句话总结（好记）
- **传统 Helm**：Chart 是“包”，存在专门的 Helm 仓库，靠 `index.yaml` 管理  
- **Helm OCI**：Chart 是“镜像”，存在普通容器仓库，**和 Docker 镜像一样管理**

要不要我给你做一个**从打包、推送到 OCI 仓库、再安装到 K3s 的完整可复制小实验**？

![img_24.png](img_24.png)
创建helm chart
![img_25.png](img_25.png)
![img_26.png](img_26.png)
![img_27.png](img_27.png)
helm template . 这个命令把当前template渲染出来，方便你直观地调试你的template。
![img_28.png](img_28.png)
它会以分隔符方式把你的所有chart都渲染出来
![img_29.png](img_29.png)
使用nginx install 安装部署你的deployment或者其他的k8s资源
![img_30.png](img_30.png)
安装两次install的命令会报错，所以你可以使用helm upgrade --install 这样的命令。
意思是，当前环境如果安装了软件那么就升级，否则就创建。这样就不会报错了
![img_31.png](img_31.png)
安装远端helm chart
![img_32.png](img_32.png)
## Demo： 把我们的应用封装到helm chart
![img_33.png](img_33.png)
在demo6文件夹下面创建chart.yaml, values.yaml空文件，然后把原本的手动k8s配置文件复制到templates文件夹下
，实际上templates里面也可以放原生k8s的部署文件，只不过大部分情况都是因为你需要抽取模版，你才把那个yaml文件放进去。然后把里面的变量提取到values文件里面进行动态替换，这才是template的主要作用
![img_34.png](img_34.png)
然后修改charts.yaml内容如下，基本上就够了。
![img_35.png](img_35.png)
抽取变量
![img_36.png](img_36.png)
在模版里面使用变量，把模版对应的文件中需要动态传参数的值变为变量引用
![img_37.png](img_37.png)
还可以在模版添加类似开关的逻辑，比如这里，开关打开的话，那么当前db模版就是生效的。那么你helm template . 这个命令generate 出来的yaml就是包含db部分的，否则就是不包含的。
![img_38.png](img_38.png)

![img_39.png](img_39.png)
![img_41.png](img_41.png)
![img_40.png](img_40.png)
![img_42.png](img_42.png)
helm dependency update to install packages in your repo
![img_43.png](img_43.png)
packages are saved in your charts folder
![img_44.png](img_44.png)
当你部署的时候，会发现因为你定义了dependency，所以pg和redis也会被创建。相当于是说dependency会被解析为你的deploy的一部分
![img_45.png](img_45.png)
![img_46.png](img_46.png)
![img_47.png](img_47.png)
helm inspect知道那些可以复写的属性
![img_48.png](img_48.png)
![img_49.png](img_49.png)
常用命令
![img_50.png](img_50.png)


































































