#!/usr/bin/python3

# The purpose of this software is to create PDF-file from
# Finnish national archive scanned document available as JPG-files
# Software needs as an input required document or file with list of documents
# and optional maximum size for single PDF-file

from urllib.request import Request, urlopen
from urllib.error import URLError
import re
import os
import sys
import argparse
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus.flowables import Image as RepImage
import textwrap

# function to get list of pages or exit if the required document doesn't exist
# NEEDS TO BE FIXED TO SUPPORT MULTIPLE DOCUMENT DOWNLOAD

def getPageList(IndexText):
    PageList = re.findall('view.ka\?kuid=(\d*)',IndexText)
    if not len(PageList):
        print('Ei löytynyt sivuja, tarkista arkistoyksikkönumero')
        sys.exit(1)
    return PageList 

# function to create an error page if a page from archives fails to download
# page has required text to inform reader

def makeErrorPage(text, pagenumber):
    errorpage=PILImage.new('RGB',(595,842),(255,255,255))
    drawing=ImageDraw.Draw(errorpage)
    drawing.text((10,10),text,(0,0,0))
    errorpage=errorpage.resize((5950,8420))
    errorpage.save('%s.jpg'%pagenumber)
    return 

# function to download pages as jpg-files from narc-service and call error page
# creation function for failed pages
# NEEDS OUTPUT FOR SUCCESS/FAILURE

def downloadPages(ListOfPages):
    for page in ListOfPages:
        try:
            image=urlopen('http://digi.narc.fi/digi/fetch_hqjpg.ka?kuid=%s' % page)
           
        except URLError as e:
            if hasattr(e, 'reason'):
                reason='Palvelimeen ei saatu yhteyttä.\nIlmoitettu syy: '+e.reason
            elif hasattr(e, 'code'):
                reason='Palvelin ei voinut täyttää hakua.\nVirhekoodi: '+e.code
            makeErrorPage(reason,page)
        else:
            image=urlopen('http://digi.narc.fi/digi/fetch_hqjpg.ka?kuid=%s' % page)
            typeinfo=image.info().get_content_type()
            if typeinfo=='image/jpeg':
                file=open('%s.jpg' % page,'wb')
                file.write(image.read())
                file.close()
            else:
                makeErrorPage(image.read(),page)

    return

# function to create name for PDF-file from the title of the narc document

def createFilename(title,part):
    Filename=re.subn('(\\|\/|:|\*|\"|\||;|,|/)',"",title)
    Filename=re.subn('(\.|\s)','_',Filename[0])
    fname=Filename[0]
    fname+='_osa_'+str(part)+'.pdf'
    return fname

# function to calculate scaling to a4

def calcScale(imagesize,a4size):
    SizeOfX=imagesize[0]/a4size[0]
    SizeOfY=imagesize[1]/a4size[1]
    for X in np.arange(0,11,0.25):
        difference = abs(SizeOfX-X)
        if difference<0.25:
            break

    for Y in np.arange(0,11,0.25):
        difference = abs(SizeOfY-Y)
        if difference<0.25:
            break
    return (X,Y)

# function to delete downloaded jpg-files

def cleanUp(ListOfPages):
    for page in ListOfPages:
        os.remove('%s.jpg'%page)
    return
    
# function to create the pdf-file by
# 1) getting list of document pages from narc
# 2) find title from the narc
# 3) download pages
# 4) create pdf
# 5) save downloaded jpg to pdf
# 5b) close and create new pdf if size limit is exceeded
# 6) clean downloaded jpg-files

def doPDFFile(IndexText,MaxSize):
    ListOfPages=getPageList(IndexText)
    TitleMatch = re.search(r"dosearch\.ka\?sartun=\d*\.\w*\"><b>(.*?)<\/b>",IndexText)
    Title=TitleMatch.group(1)
    downloadPages(ListOfPages)
    Canvas = canvas.Canvas(createFilename(Title,1))
    Canvas.setTitle(Title)
    First = True
    counter=1
    for page in ListOfPages:
        filename='%s.jpg'%page
        if First:
            size=os.stat(filename).st_size
        else:
            size+=os.stat(filename).st_size

        if MaxSize and not First and size>(MaxSize*1024*1024):
            Canvas.save()
            counter+=1
            Canvas=canvas.Canvas(createFilename(Title,counter))
            size=os.stat(filename).st_size
        
        SavedImage = PILImage.open(filename)
        if First:
            SizeOfA4=SavedImage.size
            First=False

        #scale pages so that first image is A4-sized    
        scale=calcScale(SavedImage.size,SizeOfA4)
        Canvas.setPageSize((A4[0]*scale[0],A4[1]*scale[1]))
        Canvas.drawImage(filename,0,0,A4[0]*scale[0],A4[1]*scale[1],preserveAspectRatio=True)
        Canvas.showPage()
        SavedImage.close()

    cleanUp(ListOfPages)

    Canvas.save()

    return 0

# Check validity of input (either pure number or link to narc page

def checkInputString(inputstring):
    if re.fullmatch('\d*',inputstring):
        output='http://digi.narc.fi/digi/slistaus.ka?ay='+inputstring
    elif re.fullmatch('http://digi\.narc\.fi/digi/slistaus\.ka\?ay=\d*',inputstring):
        output=inputstring
    else:
        return
    return output

# Get list of documents from input file
# single number or fullurl = directly single url
# rangeset = generate range with the numpy.arange from [start,end(not included),step]
# rangeset2 = generate range with the numpy.arange from start-end(included), with 1 as a step

def getList(urlfile):
    lines = [line.strip() for line in open(urlfile)]
    urls = []
    for line in lines:
        singlenumber=re.fullmatch('\d*',line)
        fullurl=re.fullmatch('http://digi\.narc\.fi/digi/slistaus\.ka\?ay=\d*',line)
        rangeset=re.fullmatch('\[(\d*),(\d*),(\d)\]',line)
        rangeset2=re.fullmatch('(\d*)-(\d*)',line)
        if singlenumber:
            urls.append(line)
        elif fullurl:
            urls.append(line)
        elif rangeset:
            for value in np.arange(int(rangeset.group(1)),int(rangeset.group(2)),int(rangeset.group(3))):
                urls.append(str(value))
        elif rangeset2:
            for value in np.arange(int(rangeset2.group(1)),int(rangeset2.group(2))+1,1):
                urls.append(str(value))
        
    return urls
            
# Main function
# if single document requested run it directly
# if multiple create list from input file and run them consecutively
# MAKE EXIT ONLY AFTER ALL FILES HAVE BEEN RUN

def main(url,size,file):
    ExitValue=0
    if not (file):
        ExitValue=run(url,size)
        
    else:
        ListOfUrls=getList(url)
        for url_value in ListOfUrls:
            ExitValue=run(url_value,size)
            if(ExitValue):
                sys.exit(ExitValue)        

    sys.exit(ExitValue)

# Run single document unit to download it by
# 1) check validity of the input url
# 2) request the document from narc
# 3) send narc html-page to pdf-creating subprogram
# return values different from 0 indicate error

def run(url,size):    
    SourceUrl=url
    Url=checkInputString(SourceUrl)
    MaxSize=size  #maximum size for pdf (may be exceeded a bit because of pdf format)
    if(Url):
        Req=Request(Url)
        try:
            Response=urlopen(Req)
        except URLError as e:
            if hasattr(e, 'reason'):
                print('Palvelimeen ei saatu yhteyttä.')
                print('Ilmoitettu syy: ',e.reason)
                sys.exit(1)
            elif hasattr(e, 'code'):
                print('Palvelin ei voinut täyttää hakua.')
                print('Virhekoodi: ',e.code)
                sys.exit(1)
        else:
            IndexText=Response.read().decode('latin-1')
            doPDFFile(IndexText,MaxSize)
        return 0
        
    else:
        print("Väärä osoite, osoitteen tulee olla joko http://digi.narc.fi/digi/slistaus.ka?ay=X -muotoa tai pelkkä X,"+
               " joka on halutun arkistoyksikön numero digi narcissa.")
        return 2

    sys.stderr.write("Tuntematon virhe \n")
    return 1


# argument parser
# CREATE BETTER HELP AND FILE PARSING INPUT
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='Lataa digi.narc.fi palvelusta arkistoyksiköitä pdf-muodossa.',
         epilog=textwrap.dedent('''\
                numerolistan muoto
                    rivillä joko
                      yksittäinen arkistointiyksikkö numero tai url
                      tai listan generointi seuraavilla tavoin
                         [aloitusnumero,lopetusnumero,askel] 
                            tämä generoi listan numeroita aloituksesta lopetukseen (ei mukana)
 			 aloitusnumero-lopetusnumero 
                            tämä generoi listan numeroita aloituksesta lopetukseen (mukana) 1 välein
                '''))
    parser.add_argument('url', metavar='URL', help='arkistointiyksikön numero tai url muodossa http://digi.narc.fi/digi/slistaus.ka?ay=numero')
    parser.add_argument('-m','--maxsize',default=0,type=int, help='Maksimikoko pdf-tieodostolle, oletus 0 = ei rajoitusta')
    parser.add_argument('-f','--file',action='store_true', help='Lataa useampi yksikkö kerralla, numerolista tiedostossa ja tiedoston nimi URL:n sijaan')
    args=parser.parse_args()
    main(args.url,args.maxsize,args.file)

    
