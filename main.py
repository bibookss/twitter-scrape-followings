from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from decouple import config
import time
import csv

def login(driver, username, password):
    # Open Twitter
    driver.get('https://twitter.com/i/flow/login')

    # Wait for page to load
    time.sleep(5)

    # Find the login form and enter your credentials
    username_field = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/main/div/div/div/div[2]/div[2]/div/div[5]/label/div/div[2]/div/input')
    username_field.send_keys(username)
    username_field.send_keys(Keys.RETURN)
    # next_button = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div[1]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/div[6]/div/span/span')
    # next_button.click()

    time.sleep(5)

    password_field = driver.find_element(By.XPATH, '/html/body/div[1]/div/div/div/main/div/div/div/div[2]/div[2]/div[1]/div/div/div/div[3]/div/label/div/div[2]/div[1]/input')
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)

    # Wait for login
    time.sleep(5)

def write_csv(username, username_to_followings):
    # Specify the CSV file path
    csv_file = 'user_followings.csv'

    # Write the dictionary to the CSV file
    with open(csv_file, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([username, ','.join(username_to_followings[username])])

    print(f"Data saved to {csv_file}")

def check_element_exists(csv_file, search_element):
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == search_element:
                return True
    return False

def scrape(driver, username):
    # Navigate to the profile page of the target account
    driver.get(f'https://twitter.com/{username}')

    # Wait for page to load
    time.sleep(5)

    try:
        # Find the "Following" button and click it
        following_button = driver.find_element(By.XPATH, '//a[@href="/{}/following"]'.format(username[1:]))
        following_button.click()

        # Wait for the follower list to load
        time.sleep(5)

        # The handle is inside this span
        span_selector = 'span.css-901oao.css-16my406.r-poiln3.r-bcqeeo.r-qvutc0'

        # Create an empty list to store the extracted values
        values = []

        # Get the current scroll position
        previous_scroll_position = driver.execute_script("return window.pageYOffset;")

        # Scroll to the bottom of the page
        while True:
            pagesrc = driver.page_source
            soup = BeautifulSoup(pagesrc, "lxml")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            span_elements = soup.select(span_selector)

            # Extract the text from each span element
            for span in span_elements:
                if len(span.text) > 0:
                    if span.text[0] == '@' and span.text not in values and span.text != username:
                        values.append(span.text)
                    
            # Scroll to the bottom by executing JavaScript
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for the dynamically loaded content to appear
            time.sleep(2)

            # Check if reaching the bottom of the page
            # By comparing the current scroll position with the previous scroll position
            current_scroll_position = driver.execute_script("return window.pageYOffset;")
            if current_scroll_position == previous_scroll_position:
                break

            # Update the previous scroll position
            previous_scroll_position = current_scroll_position

    except NoSuchElementException:
        print("User is private!")
        values = ["PRIVATE ACCOUNT"]

    return values

def find_element(csv_file, search_element):
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == search_element:
                return row[1].split(',')

def start_scrape(driver, target, usernames_to_scrape):
    # Initialize a dictionary to store the followings of the target account
    username_to_followings = {}
    while len(usernames_to_scrape) > 0:
        username = usernames_to_scrape.pop()

        # Skip if the followings of the current account have already been scraped or if the account is private
        if username in username_to_followings or username == 'PRIVATE ACCOUNT':
            continue

        # Skip if the followings of the current account have been saved to the CSV file
        if check_element_exists('user_followings.csv', username):
            if username == target:
                usernames_to_scrape.extend(find_element('user_followings.csv', username))
            
            continue

        # Scrape the followings of the current account
        print(f'Scraping followings of {username}')
        username_to_followings[username] = scrape(driver, username)

        # Add the followings of the targer account to the list of accounts to scrape
        if username == target:
            usernames_to_scrape.extend(username_to_followings[username])

        print(f'Finished scraping followings of {username}')
        print(username_to_followings[username])

        print(f'{len(usernames_to_scrape)} usernames left to scrape')
        write_csv(username, username_to_followings)

    return username_to_followings

if __name__ == '__main__':
    # Configure Firefox 
    driver = webdriver.Firefox()

    # Set username and password
    username = config('TWITTER_USERNAME')
    password = config('TWITTER_PASSWORD')

    # Login
    login(driver, username, password)

    # Set the username to scrape
    # target_ = input("Enter the username to scrape: ")
    target_ = '@wonranghaeee__'
    usernames_to_scrape = [target_]

    try:
        # Initialize a dictionary to store the followings of the target account
        username_to_followings = start_scrape(driver, target_ ,usernames_to_scrape)
    except Exception as e:
        print(e)
        print('An error occured')

    # Quit the driver
    driver.quit()
