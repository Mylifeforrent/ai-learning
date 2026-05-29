# 小红书图片压缩配置说明

## 项目里的代码

`src/app/core/config.py` 中有两项配置：

```python
# 长边最大像素，0 表示不缩放仅按质量重编码
xhs_image_max_size: int = 1024
# JPEG/WebP 质量 1–100，仅影响有损格式
xhs_image_quality: int = 85
```

它们属于 `Settings` 配置类。因为项目使用了：

```python
env_prefix="APP_"
```

所以这两个字段也可以通过环境变量覆盖：

```text
APP_XHS_IMAGE_MAX_SIZE=1024
APP_XHS_IMAGE_QUALITY=85
```

默认值表示：上传到小红书笔记生成接口的图片，在进入多模态 Agent 前，会被统一处理成更适合模型调用的大小和质量。

## xhs_image_max_size: int = 1024

```python
xhs_image_max_size: int = 1024
```

这项控制图片的最大长边像素。

所谓“长边”，就是图片宽和高中更大的那一边：

```text
横图 3000 x 2000，长边是 3000
竖图 1200 x 2400，长边是 2400
方图 1800 x 1800，长边是 1800
```

默认值 `1024` 的意思是：如果图片长边超过 1024 像素，就按比例缩小，让长边最多为 1024，短边按原比例自动计算。

例如：

```text
原图：3000 x 2000
压缩后：1024 x 683
```

再例如：

```text
原图：1200 x 2400
压缩后：512 x 1024
```

它不会强行把图片裁剪成正方形，也不会拉伸变形，只做等比缩放。

## 0 表示不缩放仅按质量重编码

注释里的这句话：

```python
# 长边最大像素，0 表示不缩放仅按质量重编码
```

意思是：

```text
如果 xhs_image_max_size > 0：
    图片长边超过该值时，等比缩小

如果 xhs_image_max_size = 0：
    不改图片宽高，只重新保存一次图片
```

“重新保存一次图片”就是重编码。它可能会改变文件格式、压缩参数和文件体积，但不会改变图片尺寸。

在当前项目实现中，图片处理逻辑在 `src/app/core/image_utils.py` 的 `compress_image_to_standard()` 里：

```python
if max_size > 0 and max(w, h) > max_size:
    im, (w, h) = _resize_long_edge(im, max_size)
```

所以 `max_size=0` 时，这个缩放分支不会执行。

## xhs_image_quality: int = 85

```python
xhs_image_quality: int = 85
```

这项控制有损图片格式的保存质量，取值范围是 `1` 到 `100`：

```text
数值越高：画质越好，文件通常越大
数值越低：文件越小，画质损失越明显
```

默认值 `85` 是一个常见折中：图片体积会明显下降，同时大多数场景下仍能保持比较好的视觉质量，适合把上传图片发送给多模态模型。

项目里也有校验：

```python
@field_validator("xhs_image_quality")
@classmethod
def validate_xhs_image_quality(cls, v: int) -> int:
    if not 1 <= v <= 100:
        raise ValueError("xhs_image_quality must be between 1 and 100")
    return v
```

也就是说，如果配置成 `0` 或 `101`，应用启动或配置解析时就会报错。

## 仅影响有损格式是什么意思

注释里的这句话：

```python
# JPEG/WebP 质量 1–100，仅影响有损格式
```

意思是：`quality` 只对 JPEG、WebP 这类有损压缩格式有意义。

有损压缩会为了减小体积丢掉一部分图像细节，所以需要一个质量参数来控制“压得多狠”。JPEG 的 `quality=85` 就是告诉图片库：尽量在文件大小和画质之间取一个平衡。

但 PNG 通常是无损格式，不靠 `quality=85` 这种参数控制画质。因此当图片因为透明通道被保存为 PNG 时，这个质量值不会像 JPEG 那样直接生效。

当前项目的实际保存策略是：

```text
有透明通道：保存为 PNG，尽量保留透明信息
没有透明通道：保存为 JPEG，使用 xhs_image_quality 控制质量
```

## 在接口流程里的作用

这两个配置会在小红书笔记生成服务中被读取：

```python
images = await _save_uploaded_images(
    files,
    base_dir,
    max_size=settings.xhs_image_max_size,
    quality=settings.xhs_image_quality,
)
```

然后 `_save_uploaded_images()` 会把每张上传图片先落盘，再调用：

```python
compress_image_to_standard(
    target_path,
    max_size=max_size,
    quality=quality,
)
```

整体流程可以理解为：

```text
用户上传图片
  -> 服务端保存到临时目录
  -> 按 xhs_image_max_size 控制分辨率
  -> 按 xhs_image_quality 控制有损格式质量
  -> 把处理后的图片路径交给多模态 Agent
```

这样做的好处是：避免用户上传超大原图导致模型调用慢、传输成本高、请求更容易失败，同时又保留足够的图片细节供多模态模型理解内容。

## 一句话总结

```text
xhs_image_max_size 管图片尺寸，默认长边最多 1024 像素；
xhs_image_quality 管有损压缩质量，默认 85；
max_size=0 时不缩放尺寸，但仍会按当前保存策略重新编码图片。
```
