FROM tensorflow/tensorflow:2.2.0-gpu

ARG DEBIAN_FRONTEND=noninteractive

# Install apt dependencies
RUN apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub
RUN apt-get update && apt-get install -y \
    git \
    gpg-agent \
    python3-cairocffi \
    protobuf-compiler \
    python3-pil \
    python3-lxml \
    python3-tk \
    wget

# Install gcloud and gsutil commands
# https://cloud.google.com/sdk/docs/quickstart-debian-ubuntu
RUN export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
    echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    apt-get update -y && apt-get install google-cloud-sdk -y

# Add new user to avoid running as root
RUN useradd -ms /bin/bash tensorflow
USER tensorflow
# WORKDIR /home/tensorflow

# # Copy this version of of the model garden into the image
# COPY --chown=tensorflow . /home/tensorflow/models
WORKDIR /app

# install the dependencies and packages in the requirements file
# RUN pip install -r requirements.txt

# copy every content from the local file to the image
COPY . /app
# Compile protobuf configs
USER root
RUN (cd /app/models/research/ && protoc object_detection/protos/*.proto --python_out=.)
WORKDIR /app/models/research/

RUN cp object_detection/packages/tf2/setup.py ./
# ENV PATH="/home/tensorflow/.local/bin:${PATH}"

RUN python -m pip install -U pip
RUN python -m pip install .

# ENV TF_CPP_MIN_LOG_LEVEL 3

# FROM python:3.7.13
# COPY ./requirements.txt /app/requirements.txt

# switch working directory


# WORKDIR /app/models/research

# RUN pip install .

RUN pip uninstall -y opencv-python-headless==4.5.5.62

RUN pip install opencv-python-headless==4.1.2.30

WORKDIR /app
RUN pip install -r requirements.txt

EXPOSE 8080
ENTRYPOINT [ "python" ]

CMD ["main.py" ]
