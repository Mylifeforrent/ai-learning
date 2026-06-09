import tkinter as tk
from tkinter import messagebox
from kubernetes import client, config

# 加载Kubernetes配置
config.load_kube_config(config_file='D:/config')

# 创建API对象
apps_v1 = client.AppsV1Api()
core_v1 = client.CoreV1Api()

# 获取所有命名空间
def get_namespaces():
    return [ns.metadata.name for ns in core_v1.list_namespace().items]

# 获取所有Deployment和StatefulSet
def get_resources(namespace):
    deployments = apps_v1.list_namespaced_deployment(namespace=namespace).items
    statefulsets = apps_v1.list_namespaced_stateful_set(namespace=namespace).items
    resources = [("Deployment", d.metadata.name) for d in deployments] + [("StatefulSet", s.metadata.name) for s in statefulsets]
    return resources

def update_deployment_or_statefulset():
    namespace = namespace_var.get().strip()
    resource_type = resource_type_var.get().strip()  # 获取资源类型（Deployment 或 StatefulSet）
    resource_name = resource_var.get().strip()       # 获取资源名称
    replicas = replicas_entry.get().strip()

    try:
        replicas = int(replicas)
    except ValueError:
        messagebox.showerror("副本数无效", "请输入有效的整数作为副本数。")
        return

    try:
        if resource_type == "Deployment":
            # 更新Deployment副本数
            deployment = apps_v1.read_namespaced_deployment(name=resource_name, namespace=namespace)
            deployment.spec.replicas = replicas
            apps_v1.patch_namespaced_deployment(name=resource_name, namespace=namespace, body=deployment)
            messagebox.showinfo("更新成功", f"Deployment '{resource_name}' 在命名空间 '{namespace}' 中已更新，副本数为 {replicas}。")
        elif resource_type == "StatefulSet":
            # 更新StatefulSet副本数
            statefulset = apps_v1.read_namespaced_stateful_set(name=resource_name, namespace=namespace)
            statefulset.spec.replicas = replicas
            apps_v1.patch_namespaced_stateful_set(name=resource_name, namespace=namespace, body=statefulset)
            messagebox.showinfo("更新成功", f"StatefulSet '{resource_name}' 在命名空间 '{namespace}' 中已更新，副本数为 {replicas}。")
    except client.ApiException as e:
        messagebox.showerror("错误", f"发生错误: {e.reason}")

# 更新资源名称下拉菜单
def update_resources_menu(*args):
    namespace = namespace_var.get()
    resources = get_resources(namespace)
    resource_menu['menu'].delete(0, 'end')
    for resource_type, resource_name in resources:
        resource_menu['menu'].add_command(label=resource_name, command=tk._setit(resource_var, resource_name))
    # 默认选择第一个资源
    if resources:
        resource_var.set(resources[0][1])
    else:
        resource_var.set("")

# 创建GUI窗口
root = tk.Tk()
root.title("Kubernetes Deployment 和 StatefulSet 管理")

# 获取命名空间
valid_namespaces = get_namespaces()

# 命名空间选择下拉菜单
tk.Label(root, text="命名空间:").grid(row=0, column=0, padx=10, pady=10)
namespace_var = tk.StringVar(root)
namespace_var.set(valid_namespaces[0])  # 设置默认值
namespace_menu = tk.OptionMenu(root, namespace_var, *valid_namespaces)
namespace_menu.grid(row=0, column=1, padx=10, pady=10)

# 资源类型选择
tk.Label(root, text="资源类型:").grid(row=1, column=0, padx=10, pady=10)
resource_type_var = tk.StringVar(root)
resource_type_var.set("Deployment")  # 默认选择 Deployment
resource_type_menu = tk.OptionMenu(root, resource_type_var, "Deployment", "StatefulSet")
resource_type_menu.grid(row=1, column=1, padx=10, pady=10)

# 资源名称选择下拉菜单
tk.Label(root, text="资源名称:").grid(row=2, column=0, padx=10, pady=10)
resource_var = tk.StringVar(root)
resource_menu = tk.OptionMenu(root, resource_var, '')
resource_menu.grid(row=2, column=1, padx=10, pady=10)

# 当命名空间变化时更新资源名称下拉菜单
namespace_var.trace_add('write',update_resources_menu)

# 副本数输入
tk.Label(root, text="副本数:").grid(row=3, column=0, padx=10, pady=10)
replicas_entry = tk.Entry(root)
replicas_entry.grid(row=3, column=1, padx=10, pady=10)

# 提交按钮
submit_button = tk.Button(root, text="提交", command=update_deployment_or_statefulset)
submit_button.grid(row=4, column=1, padx=10, pady=10)

# 运行窗口
update_resources_menu()  # 初始更新资源名称列表
root.mainloop()
