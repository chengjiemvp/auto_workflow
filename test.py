import json
from playwright.sync_api import sync_playwright


def run_with_cookie():
    with sync_playwright() as p:
        print("🚀 正在启动 Playwright...")
        
        # 2. 核心魔法：使用 storage_state 加载 auth.json
        # 这会自动把 Cookies 和 LocalStorage 注入到浏览器中
        browser = p.chromium.launch(
            headless=False # 先用有头模式观察一下，确认没问题后再改成 True
        )
        
        # 创建 Context 时直接加载状态
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        print("🔗 正在尝试直接访问 Dashboard (跳过登录页)...")
        # 注意：这里直接访问内部页面，不要访问 login 页面，否则可能会触发重定向逻辑
        # 根据你的 Cookie 里的 domain，入口应该是 anl.gofreight.co
        page.goto("https://anl.gofreight.co/") 

        # 3. 验证是否成功
        try:
            # 检查是否被踢回了登录页
            page.wait_for_url("**/login**", timeout=5000)
            print("❌ 失败：页面被重定向回了登录页。可能原因：")
            print("   1. Cookie 已过期 (Session ID 在服务端失效)")
            print("   2. 代理 IP 与抓取 Cookie 时的 IP 不一致")
        except:
            # 如果没有跳转到 login，说明我们在系统内部
            print("✅ 成功！已进入系统，未触发登录页面。")
            print(f"📄 当前页面标题: {page.title()}")
            
            # 这里可以截图验证一下
            page.screenshot(path="login_success.png")

            # --- 在这里写你的后续爬虫逻辑 ---
            # data = page.locator(...).text_content()
            # print(data)

        # 保持一会以便观察
        page.wait_for_timeout(5000)
        browser.close()

if __name__ == "__main__":
    run_with_cookie()