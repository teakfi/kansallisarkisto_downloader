
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

def getPageList(IndexText):
    PageList = re.findall('view.ka\?kuid=(\d*)',IndexText)
    if not len(PageList):
        print('Ei löytynyt sivuja, tarkista arkistoyksikkönumero')
        sys.exit(1)
    return PageList 

def makeErrorPage(text, pagenumber):
    errorpage=PILImage.new('RGB',(595,842),(255,255,255))
    drawing=ImageDraw.Draw(errorpage)
    drawing.text((10,10),text,(0,0,0))
    errorpage=errorpage.resize((5950,8420))
    errorpage.save('%s.jpg'%pagenumber)
    return 

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

def createFilename(title,part):
    Filename=re.subn('(\\|\/|:|\*|\"|\|)',"",title)
    Filename=re.subn('(\.|\s)','_',Filename[0])
    fname=Filename[0]
    fname+='_osa_'+str(part)+'.pdf'
    return fname

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

def cleanUp(ListOfPages):
    for page in ListOfPages:
        os.remove('%s.jpg'%page)
    return
    
 
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
            
        scale=calcScale(SavedImage.size,SizeOfA4)
        Canvas.setPageSize((A4[0]*scale[0],A4[1]*scale[1]))
        Canvas.drawImage(filename,0,0,A4[0]*scale[0],A4[1]*scale[1],preserveAspectRatio=True)
        Canvas.showPage()
        SavedImage.close()

    cleanUp(ListOfPages)

    Canvas.save()

    return 0


def checkInputString(inputstring):
    if re.fullmatch('\d*',inputstring):
        output='http://digi.narc.fi/digi/slistaus.ka?ay='+inputstring
    elif re.fullmatch('http://digi\.narc\.fi/digi/slistaus\.ka\?ay=\d*',inputstring):
        output=inputstring
    else:
        return
    return output
            
    

def main(url,size):
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
        sys.exit(0)
        
    else:
        print("Väärä osoite, osoitteen tulee olla joko http://digi.narc.fi/digi/slistaus.ka?ay=X -muotoa tai pelkkä X,"+
               " joka on halutun arkistoyksikön numero digi narcissa.")
        sys.exit(2)

    sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lataa digi.narc.fi palvelusta kokonainen arkistoyksikkö pdf-muodossa.')
    parser.add_argument('url', metavar='URL', help='arkistointiyksikön numero tai url muodossa http://digi.narc.fi/digi/slistaus.ka?ay=numero')
    parser.add_argument('-m','--maxsize',default=0,type=int, help='Maksimikoko pdf-tieodostolle, oletus 0 = ei rajoitusta')
    args=parser.parse_args()
    main(args.url,args.maxsize)

    
