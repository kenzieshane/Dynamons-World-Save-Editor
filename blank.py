import os
import sys
import time

try:
    import requests
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
except ImportError:
    print("This script requires 'selenium' and 'webdriver-manager'.")
    print("Please run: pip install selenium webdriver-manager")
    sys.exit(1)

def download_with_selenium_edge(package_name):
    """
    Uses Selenium to navigate APKPure with MS Edge and download an APK.
    """
    driver = None
    try:
        options = webdriver.EdgeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        print("Setting up Microsoft Edge WebDriver...")
        driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 20) # Wait for up to 20 seconds

        # 1. Go directly to the app page
        app_page_url = f"https://apkpure.com/dynamons-world/com.funatomic.dynamons3"
        print(f"Navigating to app page: {app_page_url}")
        driver.get(app_page_url)

        # 2. Find and click the download button to get to the download page
        print("Looking for the download button...")
        download_button = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/download')]" )))
        download_page_url = download_button.get_attribute('href')
        print(f"Found download page link: {download_page_url}")
        driver.get(download_page_url)

        # 3. On the download page, find the direct link
        print("Looking for the direct download link...")
        time.sleep(5) # Give page time to load JS
        direct_download_link = wait.until(EC.presence_of_element_located((By.ID, 'download_link')))
        apk_url = direct_download_link.get_attribute('href')
        print(f"Found direct APK URL: {apk_url}")

        # 4. Download the file using requests
        print("Downloading APK... (This may take a while)")
        apk_response = requests.get(apk_url, stream=True, headers={'User-Agent': options.arguments[-1]})
        apk_response.raise_for_status()

        file_name = f"{package_name}.apk"
        with open(file_name, "wb") as f:
            total_length = apk_response.headers.get('content-length')
            if total_length is None:
                f.writelines(apk_response.iter_content(8192))
            else:
                dl = 0
                total_length = int(total_length)
                for data in apk_response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(50 * dl / total_length)
                    sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {dl * 100 / total_length:.2f}%")
                    sys.stdout.flush()
        print("\nSuccessfully downloaded and saved APK as:", os.path.join(os.getcwd(), file_name))

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if driver:
            print("Closing WebDriver.")
            driver.quit()

if __name__ == "__main__":
    package_name = "com.funatomic.dynamons3"
    download_with_selenium_edge(package_name)
