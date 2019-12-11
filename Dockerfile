FROM ubuntu:18.04

# Dependencies
RUN apt-get -qq update && apt-get -qq  install curl software-properties-common ca-certificates gnupg -y
RUN useradd -ms /bin/bash keybase
USER keybase
WORKDIR /home/keybase

# Download and verify the deb
RUN curl --remote-name https://prerelease.keybase.io/keybase_amd64.deb
RUN curl --remote-name https://prerelease.keybase.io/keybase_amd64.deb.sig
# Import our gpg key from our website. Pulling from key servers caused a flakey build so
# we get the key from the Keybase website instead.
RUN curl -sSL https://keybase.io/docs/server_security/code_signing_key.asc | gpg --import
# This line will error if the fingerprint of the key in the file does not match the
# known fingerprint of the our PGP key
RUN gpg --fingerprint 222B85B0F90BE2D24CFEB93F47484E50656D16C7
# And then verify the signature now that we have the key
RUN gpg --verify keybase_amd64.deb.sig keybase_amd64.deb

# Silence the error from dpkg about failing to configure keybase since `apt-get install -f` fixes it
USER root
RUN dpkg -i keybase_amd64.deb || true
RUN apt-get install -fy

# install python3.7
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

# run it
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
COPY . /app
RUN chown keybase ./tmp
CMD ["entrypoint.sh"]
