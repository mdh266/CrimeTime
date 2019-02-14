FROM continuumio/miniconda3:4.5.12

LABEL mainainer="Mike Harmon <mdh266@gmail.com>"

RUN apt-get update && apt-get install vim htop -y

# create directories
RUN mkdir /ds \
          /ds/backend \
          /ds/flaskapp \
          /ds/data 
 

ENV HOME=/ds
ENV SHELL=/bin/bash
WORKDIR /ds

# allows to add data & files into directories
VOLUME /ds \
       /ds/backend \
       /ds/flaskapp \
       /ds/data


# copy data and files into directories
COPY  backend/  /ds/backend 
COPY  flaskapp/ /ds/flaskapp
COPY  data/     /ds/data

COPY tornadoapp.py /ds
COPY requirements.txt /ds

# install conda distribution and pip install dependencies
RUN conda install python=3.7.0 pip=18.1 geopandas=0.3.0

RUN pip install -r requirements.txt
				  

# Run a shell script
ENTRYPOINT ["python"]
CMD  ["tornadoapp.py"]
#CMD ["/bin/bash"]
