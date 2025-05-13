## 环境准备

### **浏览器依赖 (仅 Browser 模式)**
   - 如使用 `mode: browser`, 需安装 **Google Chrome/Chromium**。
   - 如果出现 “无法找到浏览器可执行文件路径, 请手动配置” 提示, 请参考 [DrissionPage 入门指南](https://www.drissionpage.cn/get_start/before_start/)。

### Qidian 的 VIP 章节解析 (session 模式)

**注**: 如果使用的是 `mode: browser` 模式, 无需进行以下步骤: 程序会自动打开浏览器提示登录并维持会话, 可直接解析 VIP 章节, 无需安装 Node.js 或设置 Cookie。

起点的 VIP 章节采用了基于 JavaScript 的加密 (Fock 模块)。在 `mode: session` 模式下, 当遇到 VIP 章节时, 程序会调用本地 `Node.js` 脚本进行解密。

此功能依赖系统已安装 [Node.js](https://nodejs.org/), 并确保 `node` 命令可在命令行中访问。

未安装 `Node.js` 时, 程序将报错提示 `Node.js is not installed or not in PATH.`。
建议安装稳定版本 (LTS) 即可: [https://nodejs.org](https://nodejs.org)

**注意:VIP 章节访问需要登录 Cookie。**
在使用 `session` 模式前, 请先通过以下命令设置自己的 cookie

这些字段通常会在登录状态下由浏览器自动生成。

可以在浏览器登录起点后, 通过浏览器开发者工具 (F12) 复制完整的 Cookie 字符串:

1. 打开浏览器, 登录 [https://www.qidian.com](https://www.qidian.com)
2. 按 `F12` 打开开发者工具
3. 切到「Console」控制台
4. 粘贴下面这行代码并回车:
    ```js
    copy(document.cookie)
    ```
5. 然后直接粘贴到终端使用:
    ```bash
    novel-cli settings set-cookies qidian "粘贴这里"
    ```

    或者直接运行命令后按提示交互输入:
    ```bash
    novel-cli settings set-cookies
    ```

p.s. 目前 session 登录方式的 cookie 还不支持自动续期, 可能每次运行前都需要手动重新设置一次 cookie, 后续会考虑优化这一流程
