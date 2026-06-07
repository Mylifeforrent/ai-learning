improve current test case agents

update the overall flow to below:
user upload file --> file read agent --> parse file(xlsx,csv,pdf,md etc.) agent --> test case writer --> reviewer --> human doublc confirm

user should be able to regenerate result for specific agent

文档解析：
现有框架：LLmaindex,langchain,etc. 
原始的笨方法： 逐页解析（文字，图片 通过多模态进行解析， 表格通过OCR解析保留格式）-》 这个效果很好
推荐的框架：marker（https://github.com/datalab-to/marker ）， docling--IBM 效果差一点
部署私有化：https://github.com/OpenGVLab/InternVL 或者 https://github.com/bytedance/ui-tars  这些开源的优秀模型都可以去modal上看或者hugging face上看
开源框架要看，生命力如何，star如何，是否可以商用












