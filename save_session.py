import json
import time
from playwright.sync_api import sync_playwright


def debug_storage():
    with sync_playwright() as p:
        print("🚀 启动浏览器...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("🔗 前往登录页...")
        page.goto("https://www.gofreight.com/login") # 替换正确URL

        print("\n🛑 【人工介入阶段】")
        print("请在浏览器中手动登录，处理完弹窗，直到你能看到 Dashboard 首页。")
        input("✅ 登录成功并看到首页后，请回到这里按【回车】继续...")

        # 1. 强制等待几秒，确保数据写入
        page.wait_for_timeout(3000)

        # 2. 打印当前页面 URL，确保不在 about:blank
        print(f"📍 当前页面: {page.url}")

        # 3. 暴力提取所有存储数据
        print("\n🔍 正在检查所有存储位置...")
        
        # 提取 Cookies
        cookies = context.cookies()
        print(f"🍪 Cookies 数量: {len(cookies)}")
        if len(cookies) > 0:
            print(f"   (示例: {cookies[0]['name']})")
        
        # 提取 LocalStorage
        local_storage = page.evaluate("() => JSON.stringify(localStorage)")
        ls_data = json.loads(local_storage)
        print(f"📦 LocalStorage 条目数: {len(ls_data)}")

        # 提取 SessionStorage (Playwright 默认不存这个!)
        session_storage = page.evaluate("() => JSON.stringify(sessionStorage)")
        ss_data = json.loads(session_storage)
        print(f"⚡ SessionStorage 条目数: {len(ss_data)}")

        # 4. 分析结果
        if len(cookies) == 0 and len(ss_data) > 0:
            print("\n🚨 发现问题：关键数据可能在 SessionStorage 中！")
            print("   Playwright 的 storage_state 不会自动保存 SessionStorage。")
            print("   你需要手动保存并在下次启动时注入。")
            
            # 保存 SessionStorage 到文件
            with open("session_storage.json", "w") as f:
                f.write(session_storage)
            print("💾 已将 SessionStorage 保存为 session_storage.json")

        elif len(cookies) > 0:
            # 正常保存
            context.storage_state(path="auth.json")
            print("💾 Cookies 已保存为 auth.json")
        
        else:
            print("\n❌ 奇怪：Cookies 和 SessionStorage 都是空的。")
            print("   请检查你是否开启了浏览器的'无痕模式'干扰，或者是否还在登录页面。")

        # 保持浏览器开启一会儿以便查看
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    debug_storage()