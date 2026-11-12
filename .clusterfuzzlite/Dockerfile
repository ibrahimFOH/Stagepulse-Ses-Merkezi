FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:21f6fab17ace4dc76e1c56de91ee95d3d03da021df94b41056ba036f6c6f55e9

RUN printf 'numpy==2.4.6 --hash=sha256:89cd468399cfd2504718f0ba50e410dca55a170b61a02ad92bb18c8a65186e93\n' > /tmp/fuzz-requirements.txt \
    && pip3 install --no-cache-dir --require-hashes -r /tmp/fuzz-requirements.txt

COPY . $SRC/stagepulse
WORKDIR $SRC/stagepulse
COPY .clusterfuzzlite/build.sh $SRC/build.sh
