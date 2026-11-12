FROM gcr.io/oss-fuzz-base/base-builder-python

RUN pip3 install --no-cache-dir numpy==2.2.6
COPY . $SRC/stagepulse
WORKDIR $SRC/stagepulse
COPY .clusterfuzzlite/build.sh $SRC/build.sh
