from fastapi import FastAPI
from pydantic import BaseModel
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
import time

app = FastAPI()

class QueryRequest(BaseModel):
    question: str

@app.post("/api/ai-overview-brands")
def scrape_google_ai_overview_brands(req: QueryRequest):
    query = req.question

    options = uc.ChromeOptions()
    # For testing: comment this out if AI Overview doesn't load in headless mode
    # options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options)

    try:
        driver.get(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        time.sleep(2)

        # Try clicking "Show more"
        try:
            show_more = driver.find_element(By.CSS_SELECTOR, "div.zNsLfb.Jzkafd")
            ActionChains(driver).move_to_element(show_more).click().perform()
            time.sleep(2)
        except:
            pass

        # Try clicking "Show all"
        try:
            show_all = driver.find_element(By.XPATH, "//span[text()='Show all']")
            driver.execute_script("arguments[0].scrollIntoView(true);", show_all)
            ActionChains(driver).move_to_element(show_all).click().perform()
            time.sleep(2)
        except:
            pass

        # Wait until AI Overview brand container is present
        try:
            container = WebDriverWait(driver, 10).until(
                lambda d: d.find_element(By.CSS_SELECTOR, ".zVKf0d.Cgh8Qc")
            )
        except:
            return {
                "question": query,
                "brands": [],
                "error": "❌ AI Overview block not found. Google might not show it for this query."
            }

        # Scroll the container slowly
        previous_count = 0
        same_count_repeats = 0

        for _ in range(40):
            driver.execute_script("arguments[0].scrollTop += 300;", container)
            time.sleep(0.3)
            count = driver.execute_script("""
                return document.querySelectorAll('.kLMmLc div .R8BTeb').length;
            """)
            if count == previous_count:
                same_count_repeats += 1
            else:
                same_count_repeats = 0
            previous_count = count
            if same_count_repeats >= 5:
                break

        # Extract brand names
        brands = driver.execute_script("""
            let elements = document.querySelectorAll('.kLMmLc div .R8BTeb');
            return Array.from(elements).map(el => el.innerText.trim()).filter(Boolean);
        """)

        return {
            "question": query,
            "brands": brands
        }

    except Exception as e:
        return {
            "error": str(e),
            "note": "This usually means Google blocked the scraper or structure changed."
        }
    finally:
        driver.quit()
