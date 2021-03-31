FROM selenium/standalone-chrome
WORKDIR /code/
#install pip
RUN sudo apt update
RUN sudo apt install python3-pip -y
# install dependecies for pycopg2
RUN sudo apt-get install libpq-dev python-dev -y
#install all pip packages
COPY requirements.txt /code/
RUN sudo pip3 install -r requirements.txt

RUN cd /usr/
RUN python3 -m textblob.download_corpora
# COPY .env /tmp/.env
COPY . /code/
CMD scrapy crawl comments
