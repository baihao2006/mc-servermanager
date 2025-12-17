# mc-servermanager
- 基于python的PyQt5和QtWidgets等库
- 一个懒人或小白使用的Minecraft Bedrock 服务器开服机器。
- 专为Windows Server设计，提供直观的图形化界面来配置和管理Minecraft服务器。
- 只适用于minecraft的v1.21.26版本，如有不同请自行更换。

## ✨ 功能特性

### 服务器配置
- 图形化界面配置所有服务器参数
- 支持实时保存和应用配置
- 无需手动编辑`server.properties`文件(实在懒得翻)

### 🚀 服务器管理
- 一键启动/停止服务器
- 实时查看服务器控制台输出
- 支持向服务器发送命令

### 📦 功能
- 支持所有Minecraft Bedrock服务器配置项
- 实时日志显示
- mc命令行支持
- 自动配置文件备份

## 📥 使用方法（请在服务器端使用！）

### 方法一：使用安装程序（推荐）
- 下载最新的安装程序 `MCServerManagerInstaller.exe`
- 运行安装程序，按照向导提示完成安装
- 安装完成后，通过开始菜单或桌面快捷方式启动程序

### 方法二：直接运行可执行文件
- 下载最新的 `MCServerManager.exe`
- 确保 `lib` 目录与可执行文件位于同一目录
- 双击 `MCServerManager.exe` 启动程序

## 📁 项目结构

```
MCManager/
├── main.py              # 主程序入口
├── license              # 开源协议
├── lib/                 # Minecraft官方服务器文件目录
│   ├── bedrock_server.exe  # 官方服务器可执行文件
│   ├── server.properties   # 服务器配置文件
│   └── ...                # 其他服务器文件
├── requirements.txt     # Python依赖列表
└── README.md            # 项目说明文档
```

## 🛠️ AIGC说明
- 本代码经过AI（grok-4）重构，无注释，舍弃了部分可读性。
- （实际上我踏马太懒了）

## 🤝 声明

- 此版本为初始版本，可能出现高分辨率下字过小的情况，请期待后面修复。
- 同时感谢[Chadwuo和PekingLee](https://github.com/Chadwuo/HHSoftwarePack)的免费开源exe打包器，使得整个软件安装更加易用。

## 🚀 更新日志

### v1.0.0 (2025-12-16)
- 初始版本发布
- 基本功能实现
- 服务器启动/停止功能

### v1.1.0(画饼中...)
- 将会考虑加入光影安装一体化
- 加入服务器联网下载功能（解决下载太慢难题）

**敬请使用 Minecraft Bedrock Server Manager！** 🎉
- ![Downloads](https://img.shields.io/github/downloads/baihao2006/mc-servermanager/total)
