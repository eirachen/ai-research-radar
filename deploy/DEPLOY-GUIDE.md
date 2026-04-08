# AI Research Radar - 部署到腾讯云 Lighthouse (Windows Server)

## 总共 3 步，5 分钟搞定

---

## 第一步：把网站文件传到服务器

### 方法 A：远程桌面拖拽（最简单）

1. 在本地电脑打开**远程桌面连接**（Win+R → 输入 `mstsc`）
2. 输入你 Lighthouse 的**公网 IP**，连接
3. 把本地的 `ai-research-monitor` 整个文件夹复制到服务器的 `C:\ai-radar`

需要复制的文件：
```
C:\ai-radar\
├── index.html              ← 网站主页
└── reports\
    ├── index.json           ← 报告索引
    └── 2026-04-07-report.md ← 情报日报
```

### 方法 B：用 SCP 命令传输

在你本地电脑的终端执行（把 `你的IP` 和 `你的用户名` 替换掉）：

```powershell
scp -r C:\Users\eirachen\WorkBuddy\20260407122917\ai-research-monitor\index.html 你的用户名@你的IP:C:\ai-radar\
scp -r C:\Users\eirachen\WorkBuddy\20260407122917\ai-research-monitor\reports 你的用户名@你的IP:C:\ai-radar\
```

---

## 第二步：在服务器上启动 Web 服务

远程登录服务器后，打开 **PowerShell** 或 **CMD**，执行：

```powershell
cd C:\ai-radar
python -m http.server 80
```

如果提示 `python` 找不到，先安装 Python：
- 打开浏览器访问 https://www.python.org/downloads/
- 下载安装（勾选 **Add to PATH**）
- 重新打开终端再执行上面的命令

看到 `Serving HTTP on :: port 80` 就说明成功了。

---

## 第三步：开放防火墙端口

### 3a. 腾讯云控制台（必做）

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/lighthouse)
2. 找到你的 Lighthouse 实例 → 点击进入
3. 左侧菜单 → **防火墙**
4. 点击 **添加规则**：
   - 协议：TCP
   - 端口：80
   - 策略：允许
   - 来源：所有 IP（0.0.0.0/0）
5. 确认添加

### 3b. Windows 防火墙（可能需要）

在服务器上打开 PowerShell，执行：

```powershell
netsh advfirewall firewall add rule name="AI Radar HTTP" dir=in action=allow protocol=TCP localport=80
```

---

## 完成！

浏览器打开 `http://你的公网IP` 即可访问！

---

## 让服务保持后台运行（不关闭窗口也能跑）

上面的 `python -m http.server 80` 在关闭窗口后会停止。要让它一直在后台运行：

### 方案：用 NSSM 注册为 Windows 服务

1. 下载 NSSM：https://nssm.cc/download
2. 解压后，在服务器上执行：

```powershell
nssm install AIRadar "C:\Python3x\python.exe" "-m http.server 80"
nssm set AIRadar AppDirectory "C:\ai-radar"
nssm start AIRadar
```

这样即使重启服务器，网站也会自动启动。

---

## 后续更新

每次自动化任务生成新报告后，你只需要把新的 `.md` 文件和更新后的 `index.json` 传到服务器的 `C:\ai-radar\reports\` 目录下，网站就会自动显示新报告。
