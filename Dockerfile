FROM python:3.7

WORKDIR /appdir
RUN pip3 install pillow
RUN pip3 install numpy
RUN pip3 install reportlab
COPY narchaku.py .
WORKDIR /download
ENTRYPOINT ["python", "/appdir/narchaku.py"]
CMD ["-h"]

