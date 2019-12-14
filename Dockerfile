FROM keybaseio/client

# install python3.7
RUN apt-get -qq update
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get install build-essential checkinstall -y
RUN apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev \
    libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev \
    zlib1g-dev wget sudo -y
RUN apt-get install git -y
WORKDIR "/usr/src"
RUN wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz
RUN tar xzf Python-3.7.3.tgz
WORKDIR "/usr/src/Python-3.7.3"
RUN ./configure --enable-optimizations
RUN make install

# set up our app
RUN mkdir -p /app
WORKDIR "/app"
RUN chown keybase /app
COPY requirements.txt /app
RUN pip3 install -r requirements.txt
COPY . /app
RUN chown keybase ./tmp

# Tell the keybase entrypoint to start a running service. It will
# use KEYBASE_USERNAME and KEYBASE_PAPERKEY from the environment.
ENV KEYBASE_SERVICE 1

CMD ["python3", "/app/code/main.py"]
