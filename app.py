# Importing Libraries
import os
import re
import urllib.request

from bs4 import BeautifulSoup as Soup
from flask import Flask, render_template, request, Response
from flask_cors import cross_origin
from flask_ngrok import run_with_ngrok
from pandas import DataFrame
from wordcloud import WordCloud, STOPWORDS

import matplotlib
import matplotlib.pyplot as plt
import requests
# Libraries Import ended

wd = './static/'
IMG_FOLDER = wd + 'images/'
CSV_FOLDER = wd + 'CSVs/'
app = Flask(__name__)
run_with_ngrok(app=app)
df: DataFrame

app.config['IMG_FOLDER'] = IMG_FOLDER
app.config['CSV_FOLDER'] = CSV_FOLDER


class ReviewScrapper:
    def __init__(self):
        self.data = {"Product": list(), "Name": list(), "Price": list(
        ), "Rating": list(), "Comment Heading": list(), "Comment": list()}

    # This function  is used to get main page HTML of the searched product from website link
    def WebsiteMainPage(self, base_url=None, search_string=None, shop=None):
        # Selecting The Website Link based on the shop name
        if shop == 'flipkart':
            search_url = f"{base_url}/search?q={search_string}"
            # print(search_url)
        elif shop == 'snapdeal':
            search_url = f"{base_url}/search?keyword={search_string}"
        else:
            search_url = f"{base_url}/s?k={search_string}"
        # print(search_url)

        if shop == 'snapdeal':
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/86.0.4240.183 Safari/537.36"}
            with requests.get(search_url, headers=headers) as page:
                return Soup(page.content, "html.parser")

        elif shop == "amazon":
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            with requests.get(search_url, headers=headers) as page:
                return Soup(page.content, "html.parser")

        else:
            with urllib.request.urlopen(search_url) as url:
                page = url.read()
            # print(Soup(page, "html.parser").prettify())
            return Soup(page, "html.parser")

    def CommentPage(self, product_link=None):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
                   "Accept-Encoding": "gzip, deflate",
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT": "1",
                   "Connection": "close",
                   "Upgrade-Insecure-Requests": "1"}
        # print(product_link)
        prod_page = requests.get(product_link, headers=headers)
        return Soup(prod_page.content, "html.parser")

    def ProductLinks(self, base_url=None, big_boxes=None):
        temp = []

        for box in big_boxes:

            if base_url == "https://www.snapdeal.com":
                try:
                    # print("snapdeal")
                    link = box["href"]
                    name = box.picture.img['title']
                    idx = 0
                    for i in link:
                        if(i == '#'):
                            break
                        else:
                            idx = idx+1
                    link = link[0:idx]
                    link += '/reviews'
                    # print(name, link)
                    temp.append((name, link))
                except:
                    pass
            elif base_url == 'https://www.flipkart.com':
                link = re.findall(re.compile(r'\/.+\/p\/.+\?pid=.{16}&lid=.{25}'),
                                  box['href'])[0]
                link = link.replace('/p/', '/product-reviews/')
                link += '&aid=overall&certifiedBuyer=true&sortOrder=NEGATIVE_FIRST'
                slash = 0
                idx = 0
                for slas in box['href']:
                    if slas == '/':
                        slash += 1

                    if slash == 2:
                        break
                    idx += 1
                print(box['href'][1:idx])
                try:
                    temp.append(box.img['alt'], base_url+link)

                except:
                    temp.append((box['href'][1:idx], base_url + link))

                # print(base_url + link)
            else:
                try:
                    temp.append((box.img['alt'],
                                 base_url + box["href"]))
                except:
                    pass
        # print(temp)
        return temp

    def FinalReview(self, comment_box=None, prod_name="NO Name", prod_price="No Price", shop=None):

        if shop == "snapdeal":
            self.data["Product"].append(prod_name)
            self.data["Price"].append(prod_price)
            print("FInal Data")
            try:
                self.data["Name"].append(comment_box.find_all(
                    'div', {'class': '_reviewUserName'})[0].text)
            except:
                self.data["Name"].append("No Name")
            try:
                rating = comment_box.find_all(
                    'i', {'class': 'sd-icon sd-icon-star active'})
                print(rating)
                self.data['Rating'].append(len(rating))
            except:
                self.data['Rating'].append("NO Rating")
            try:
                self.data["Comment Heading"].append(
                    comment_box.find_all('div', {'class': "head"})[0].text)
            except:
                self.data["Comment Heading"].append("NO Comment Heading")
            try:
                self.data["Comment"].append(comment_box.find_all('p')[0].text)
            except:
                self.data["Comment"].append("NO Comment")

        elif shop == 'flipkart':
            self.data["Product"].append(prod_name)
            self.data["Price"].append(prod_price)
            try:
                self.data["Name"].append(comment_box.find_all(
                    'p', {'class': '_2mcZGG'})[0].text)
            except:
                self.data["Name"].append('No Name')

            try:
                try:
                    self.data["Rating"].append(comment_box.find_all(
                        'div', {'class': '_3LWZlK _1BLPMq _3B8WaH'})[0].text)
                except:
                    self.data["Rating"].append(
                        comment_box.find_all('div', {'class': '_3LWZlK _1BLPMq _3B8WaH'})[0].text)
            except:
                self.data["Rating"].append('No Rating')

            try:
                self.data["Comment Heading"].append(
                    comment_box.find_all('p', {'class': '_2-N8zT'})[0].text)
            except:
                self.data["Comment Heading"].append('No Comment Heading')

            try:
                self.data["Comment"].append(comment_box.find_all('div', {'class': 't-ZTKy'})[0].text
                                            .replace('READ MORE', ''))
            except:
                self.data["Comment"].append('NO')

        else:
            try:
                self.data["Name"].append(comment_box.find_all(
                    'span', {'class': 'a-profile-name'})[0].text)
            except:
                self.data["Name"].append('No Name')

            try:
                self.data["Rating"].append(comment_box.find_all('span', {'class': 'a-icon-alt'})[0]
                                           .text.replace('.0 out of 5 stars', ''))
            except:
                self.data["Rating"].append('No Rating')

            try:
                self.data["Comment Heading"].append(comment_box.find_all('a', {'data-hook': 'review-title'})[0].text
                                                    .replace('\n', ''))
            except:
                self.data["Comment Heading"].append('No Comment Heading')

            try:
                self.data["Comment"].append(comment_box.find_all('span', {'data-hook': 'review-body'})[0].text
                                            .replace('\n', ''))
            except:
                self.data["Comment"].append('')

    def FinalData(self):
        return self.data

    def ConvertToMatrix(self, dataframe, file_name=None):
        # save the CSV file to CSVs folder
        csv_path = app.config['CSV_FOLDER'] + file_name
        fileExtension = '.csv'
        final_path = f"{csv_path}{fileExtension}"
        # clean previous files -
        CleanCache(directory=app.config['CSV_FOLDER'])
        # save new csv to the csv folder
        dataframe.to_csv(final_path, index=None)
        print("File saved successfully!!")
        return final_path

    def ConvertToWordCloud(self, dataframe=None, img_file_name=None):
        # extract all the comments
        txt = dataframe["Comment"].values
        # generate the word cloud
        wc = WordCloud(width=1000, height=600, background_color='black',
                       stopwords=STOPWORDS).generate(str(txt))
        matplotlib.use('agg')

        plt.figure(figsize=(25, 15), facecolor='k', edgecolor='k')
        plt.imshow(wc, interpolation='bicubic')
        plt.axis('off')
        plt.tight_layout()

        image_path = app.config['IMG_FOLDER'] + img_file_name + '.png'

        CleanCache(directory=app.config['IMG_FOLDER'])

        plt.savefig(image_path)
        plt.close()


class CleanCache:
    def __init__(self, directory=None):
        self.clean_path = directory
        # only proceed if directory is not empty
        if os.listdir(self.clean_path) != list():
            # iterate over the files and remove each file
            files = os.listdir(self.clean_path)
            for file_name in files:
                print(file_name)
                os.remove(self.clean_path + file_name)
        print("cleaned!")


@app.route('/', methods=['GET'])
@cross_origin()
def homepage():
    return render_template("index.html")


@app.route('/review', methods=("POST", "GET"))
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            shop = request.form['shop']
            if shop == 'flipkart':
                base_url = 'https://www.flipkart.com'
            elif shop == 'snapdeal':
                base_url = 'https://www.snapdeal.com'
            elif shop == "myntra":
                base_url = 'https://myntra.com'
            else:
                base_url = 'https://www.amazon.com'

            search_string = request.form['query']

            search_string = search_string.replace(" ", "+")
            print(search_string)

            get_data = ReviewScrapper()

            query_html = get_data.WebsiteMainPage(
                base_url, search_string, shop)
            print(query_html)

            if shop == 'flipkart':
                big_boxes = query_html.find_all(
                    "a", {"href": re.compile(r"\/.+\/p\/.+qH=.+")})
            elif shop == "myntra":
                big_boxes = query_html.find_all(
                    "a", {"href": re.compile(r".+/buy")})

            elif shop == "snapdeal":
                big_boxes = query_html.find_all(
                    "a", {"href": re.compile(r"https://www.snapdeal.com/product/.+")})

            else:
                big_boxes = query_html.find_all("a", {"class": "a-link-normal s-no-outline",
                                                      'href': re.compile(r'\/.+\/dp\/.+?dchild=1.*')})
            #print("hello big boxes", big_boxes)
            product_name_links = get_data.ProductLinks(
                base_url, big_boxes)
            #print("hello product link", product_name_links)
            total = 0
            data = get_data.FinalData()
            print(len(data["Name"]), len(data["Price"]), len(data["Rating"]), len(
                data["Product"]), len(data["Comment Heading"]), len(data["Comment"]))

            for prod_name, product_link in product_name_links[:4]:
                for prod_html in get_data.CommentPage(product_link):
                    try:
                        prod_price = ''
                        if shop == "snapdeal":
                            # print("snapdeal")
                            comment_boxes = prod_html.find_all(
                                'div', {"class": "user-review"})
                            print(comment_boxes[0])
                            prod_price = prod_html.find_all(
                                'p', {"class": "product-offer-price"})[0].text
                            # print(prod_price)
                        elif shop == 'flipkart':
                            comment_boxes = prod_html.find_all(
                                'div', {'class': '_27M-vq'})[:2]
                            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101"
                                                     " Firefox/66.0",
                                       "Accept-Encoding": "gzip, deflate",
                                       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                       "DNT": "1",
                                       "Connection": "close",
                                       "Upgrade-Insecure-Requests": "1"}
                            positive_link = product_link.replace(
                                'NEGATIVE', 'POSITIVE')
                            prod_page = requests.get(
                                positive_link, headers=headers)
                            prod_positive = Soup(
                                prod_page.content, "html.parser")
                            comment_boxes += prod_positive.find_all(
                                'div', {'class': '_27M-vq'})[:2]
                            prod_price = prod_positive.find_all(
                                'div', {"class": "_30jeq3"})[0].text

                        else:
                            try:
                                container = prod_html.find_all(
                                    'td', {"class": "a-span12"})
                                container = Soup(str(container), 'html.parser')
                                prod_price = container.find_all(
                                    'span', {"id": "priceblock_ourprice"})[0].text
                            except:
                                prod_price = prod_html.find_all(
                                    'span', {"class": "a-size-base a-color-price"})[0].text
                            # print(prod_price)
                            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101"
                                                     " Firefox/66.0",
                                       "Accept-Encoding": "gzip, deflate",
                                       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                       "DNT": "1",
                                       "Connection": "close",
                                       "Upgrade-Insecure-Requests": "1"}
                            link = product_link
                            link = re.findall(re.compile(
                                r'\/.+\/.{10}'), link)[0]
                            link = link.replace('dp', 'product-reviews')
                            link = 'https:' + link + '/ref=cm_cr_arp_d_viewopt_sr?ie=UTF8' \
                                                     '&reviewerType=avp_only_reviews&pageNumber=1&filterByStar=critical'
                            # print(link)
                            prod_page = requests.get(link, headers=headers)
                            prod_negative = Soup(
                                prod_page.content, 'html.parser')
                            comment_boxes = prod_negative.find_all(
                                'div', {'id': re.compile(r'customer_review-.+')})
                            link = link.replace('critical', 'positive')
                            prod_page = requests.get(link, headers=headers)
                            prod_positive = Soup(
                                prod_page.content, 'html.parser')
                            comment_boxes += prod_positive.find_all(
                                'div', {'id': re.compile(r'customer_review-.+')})
                            # print(len(comment_boxes))

                        if shop == "snapdeal":
                            pass
                        else:
                            prod_price = float((prod_price.replace("₹", "")).replace(
                                ",", "").replace(" ", ""))
                        # print(prod_price)

                        for comment_box in comment_boxes:
                            total += 1
                            get_data.FinalReview(
                                comment_box, prod_name, prod_price, shop)

                    except:
                        pass
            # save the data as dataframe(Table)
            global df
            print(total)
            print("dataframe")
            data = get_data.FinalData()
            print(len(data["Name"]), len(data["Price"]), len(data["Rating"]), len(
                data["Product"]), len(data["Comment Heading"]), len(data["Comment"]))
            df = DataFrame(get_data.FinalData())
            # save dataframe as a csv which will be availble to download

            download_path = get_data.ConvertToMatrix(
                df, file_name=search_string)

            # generate and save the wordcloud image
            get_data.ConvertToWordCloud(df,
                                        img_file_name=search_string)

            return render_template('review.html', tables=[df.to_html(index=False, classes='data')], titles=df.columns.values, search_string=search_string,
                                   download_csv=app.config['CSV_FOLDER'])
        except Exception as e:
            print(e)
            return render_template("404.html")

    else:
        return render_template("index.html")


@app.route('/show')
@cross_origin()
def show_wordcloud():
    img_file = os.listdir(app.config['IMG_FOLDER'])[0]
    print()
    return render_template("show_wc.html", user_image='images/' + img_file)


@app.route("/get_csv")
def get_csv():
    global df
    return Response(df.to_csv(index=False), mimetype="text/csv", headers={"Content-disposition": f"attachment;file_name=review.csv"})


if __name__ == '__main__':
    app.run()
