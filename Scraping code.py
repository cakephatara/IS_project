import copy
import time
import gc
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

# --------------------------------------------------------
# Not required
from ap_line_notify import LineNotify
# --------------------------------------------------------

token = 'qawYKnmdaWb7oJmgbAXamAdIj73RXOi0nkF5X6NA3BH'
raw_path = 'Travel_attraction_for_scrape.csv'
driver_path = './chromedriver'


def header_extractor(review_box):
    review_box = copy.copy(review_box)
    header = review_box.find('div', {'class': '_2fxQ4TOx'})
    user = header.find('a').extract()

    name = user.text
    username = user['href'].split('/')[-1]
    write_date = ' '.join(header.text.split()[-2:])

    return name, username, write_date


def location_extractor(review_box):
    location_tag = review_box.find('span', {'class': '_1TuWwpYf'})
    if location_tag is not None:
        location = location_tag.text
        return location
    else:
        return None


def rating_extractor(review_box):
    rating_tag = review_box.find('span', {'class': 'ui_bubble_rating'})
    if rating_tag is not None:
        rating = int(rating_tag['class'][-1].split('_')[-1])/10
        return rating
    else:
        return None


def review_head_extractor(review_box):
    review_head_tag = review_box.find('a', {'class': 'ocfR3SKN'})
    if review_head_tag is not None:
        review_head = review_head_tag.text
        return review_head
    else:
        return None


def review_body_extractor(review_box):
    review_body_tag = review_box.find('q')
    if review_body_tag is not None:
        review_body = review_body_tag.text
        return review_body
    else:
        return None


def exp_date_extractor(review_box):
    exp_date_tag = review_box.find('span', {'class': '_34Xs-BQm'})
    if exp_date_tag is not None:
        exp_date = exp_date_tag.text.split(': ')[-1]
        return exp_date.split()
    else:
        return None, None


def trip_type_extractor(review_box):
    trip_type_tag = review_box.find('span', {'class': '_2bVY3aT5'})
    if trip_type_tag is not None:
        trip_type = trip_type_tag.text.split(': ')[-1]
        return trip_type
    else:
        return None


def review_data(review_box):
    temp = header_extractor(review_box)
    data = dict(zip(['name', 'username', 'write_date'], temp))

    data['user_location'] = location_extractor(review_box)
    data['rating'] = rating_extractor(review_box)
    data['review_head'] = review_head_extractor(review_box)
    data['review_body'] = review_body_extractor(review_box)

    temp2 = exp_date_extractor(review_box)
    data['experience_month'] = temp2[0]
    data['experience_year'] = temp2[1]

    data['trip_type'] = trip_type_extractor(review_box)

    return data


def add_reviews_data(html_source, location, data):
    soup = BeautifulSoup(html_source, 'html.parser')
    review_boxes = soup.find_all(
        'div', {'class': 'Dq9MAugU T870kzTX LnVzGwUB'})

    for review_box in review_boxes:
        temp = review_data(review_box)
        temp['location'] = location
        data = data.append(temp, ignore_index=True)

    return data


def location_crawler(driver, url, location, notify):
    data = pd.DataFrame()

    driver.get(url)
    time.sleep(10)

    i = 1

    while True:
        read_more_buttons = driver.find_elements_by_xpath(
            "//span[@class='_3maEfNCR']")
        for button in read_more_buttons:
            try:
                button.click()
            except:
                pass

        data = add_reviews_data(driver.page_source, location, data)

        if not len(data) % 1000:
            notify.send_text(f'{len(data)} scraped.')
            gc.collect()

        try:
            next_button = driver.find_element_by_xpath(
                "//a[@class='ui_button nav next primary ']")
            time.sleep(5)
            next_button.click()
        except:
            break

    return data


def main(token, raw_path, driver_path):
    notify = LineNotify(token)
    df = pd.read_csv(raw_path)

    for index, row in df[['title', 'Link']].iterrows():

        # Not required
        notify.send_text(f'Start scraping {row["title"]}')

        driver = webdriver.Chrome(driver_path)

        data = location_crawler(driver, row['Link'], row['title'], notify)
        data.to_csv(f'{row["title"]}.csv', index=None)

        # Not required
        notify.send_text(f'{row["title"]} scraped with {len(data)} reviews.')

        driver.quit()

        time.sleep(60 * 10)


if __name__ == '__main__':
    main(token, raw_path, driver_path)
