课后作业需求：智能体写测试用例 -》 智能体对测试用例评审--〉人工评审 --》 输出最终测试用例

多智能体协作实现方式：
1.编排组件实现
2.消息传输机制实现

autoagent里面采用roundrobingroupchat来实现，因为最常用，是顺序编排的
参考资料文档： https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html

这里基本上就是使用roundrobingroupchat配置上对应的termination来实现 https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html














