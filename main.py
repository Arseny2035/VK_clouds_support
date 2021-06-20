import moviepy as mp
import numpy
from moviepy import editor
from PIL import Image
import os

import numpy as np
import argparse
import cv2
import pytesseract


# Получить дату съемки. Если в EXIF отсутствует, либо если видео, то далее смотрим на
# имя файлы и преобразуем из него
def getDateTaken(img):
    exif = img.getexif()
    creation_time = exif.get
    return creation_time


####################################################################################

# Функция для уменьшения разрешения клипа, сохранения уменьшенного клипа с разрешением MP4
# и удалениея старого клипа
def videoResize(clipPath):
    try:
        clip = mp.editor.VideoFileClip(clipPath)
        width, height = clip.size
        print(width, height)
        newClipPath = clipPath[:-4] + '_.MP4'

        if height > 640 or width > 640:
            if height > width:
                x = 640 / height
                width = round(width * x)
                height = 640
            else:
                x = 640 / width
                height = round(height * x)
                width = 640

            rotation = clip.rotation
            if rotation in (90, 270):
                clip = clip.resize(newsize=(height, width))
            else:
                clip = clip.resize(newsize=(width, height))

            try:
                clip.write_videofile(newClipPath, codec="libx264")
            except:
                print('Codec libx264 error')
                clip.write_videofile(newClipPath)
            clip.close()
            try:
                os.remove(clipPath)
            except OSError as e:
                print("Ошибка: %s : %s" % (clipPath, e.strerror))
        else:
            clip.close()
            os.rename(clipPath, newClipPath)
        volOfChanges = os.path.getsize(newClipPath)

    except:
        print('Can\'t resize ', clipPath)

    return volOfChanges


####################################################################################

def imageResize(imgPath):
    img = Image.open(imgPath)
    volOfChanges = 0
    width, height = img.size
    print(width, height)
    if height > 1600 or width > 1600:

        imgExif = img.getexif()
        # Отражаем дату-время сьемки (при наличии) в Log
        if imgExif is None:
            print('Sorry, image has no exif data.')
        # else:
        #     for (k, v) in imgExif.items():
        #         if k == 306:
        #             print(v)

        width, height = img.size
        if height > width:
            x = 1600 / height
            width = round(width * x)
            height = 1600
        else:
            x = 1600 / width
            height = round(height * x)
            width = 1600
        print('new', width, height)

        img.thumbnail((width, height))

        if imageRotate(img):
            img = img.rotate(90, expand=True)

        img.save(imgPath, exif=imgExif)
        print('Resized')

        volOfChanges = os.path.getsize(imgPath)

    return volOfChanges


####################################################################################

def imageRotate(img):
    imgCheck = cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2BGR)

    ### Detecting words
    hImg, wImg, _ = imgCheck.shape
    foundWord = False
    rotate = False
    try:
        boxes = pytesseract.image_to_data(imgCheck, lang="rus")
        # print(boxes)
        for x, b in enumerate(boxes.splitlines()):
            if foundWord == False:
                if x != 0:
                    b = b.split()
                    if len(b) == 12:
                        if len(b[11]) > 6:
                            foundWord = True
                            if int(b[8]) < int(b[9]):
                                rotate = True
    except:
        rotate = False

    return rotate


####################################################################################

def calcImageHash(imgPath):
    image = Image.open(imgPath)
    image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)  # Прочитаем картинку
    resized = cv2.resize(image, (8, 8), interpolation=cv2.INTER_AREA)  # Уменьшим картинку
    gray_image = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)  # Переведем в черно-белый формат
    avg = gray_image.mean()  # Среднее значение пикселя
    ret, threshold_image = cv2.threshold(gray_image, avg, 255, 0)  # Бинаризация по порогу

    # Рассчитаем хэш
    _hash = ""
    for x in range(8):
        for y in range(8):
            val = threshold_image[x, y]
            if val == 255:
                _hash = _hash + "1"
            else:
                _hash = _hash + "0"

    return _hash


####################################################################################

def delBiggestPhoto(path1, path2):
    if os.path.getsize(path1) > os.path.getsize(path2):
        os.remove(path1)
    else:
        os.remove(path2)


####################################################################################


# Сначала уменьшаем фото и видео в основных папках и все всех вложенных папках
# затем в основных директориях в папках контролеров пакуем по папкам с датами и типами актов

# path = "D:\\PyProjects\\VK_foto\\test_photos"
# path = "F:\\Архив\\Облака\\Yandex.Disk"
# path = "K:\\Clouds\\TestActs"
path = "K:\\Clouds\\YaDiskForTest"
# path = "K:\\Clouds\\Yandex.Disk"

# path = input()
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

mainDirs = os.listdir(path)
maxVolOfChanges = 3000000000
curVolOfChanges = 0

for mainDir in mainDirs:
    if curVolOfChanges < maxVolOfChanges:
        dirs = []
        # if mainDir[0:17] == 'Телефон контролер' or mainDir[0:14] == 'Телефон мастер':
        #     for dirPath, subFolder, files in os.walk(os.path.join(path, mainDir)):
        #         dirs.append("".join(dirPath.rsplit(path))[1:])
        #         print(dirs[len(dirs) - 1])
        #
        #     for curDir in dirs:
        #         if curVolOfChanges < maxVolOfChanges:
        #             files = os.listdir(os.path.join(path, curDir))
        #             filesList = []
        #
        #             for file in files:
        #                 print(os.path.join(path, curDir, file))
        #                 already_resized = file[-5:-4]
        #                 extension = "." + file[-3:]  # Get extension of current file
        #
        #                 if already_resized != '_':  # If file was resized, then we add '_' to the filename
        #                     # Resize videos to 1600px on the large size
        #                     if extension == '.3GP' or extension == '.MP4':
        #                         clipPath = os.path.join(path, curDir, file)
        #                         try:
        #                             curVolOfChanges += videoResize(clipPath)
        #                         except:
        #                             print('Ошибка файла видео: ', clipPath)
        #                     else:
        #                         # Resize photos to 1600px on the large size
        #                         if extension == '.JPG':
        #                             imgPath = os.path.join(path, curDir, file)
        #                             try:
        #                                 curVolOfChanges += imageResize(imgPath)
        #                             except:
        #                                 print('Ошибка файла фото: ', imgPath)
        #                 print(round(curVolOfChanges / 1000000))

        if mainDir[0:20] == 'Фотографии абонентов':
            for dirPath, subFolder, files in os.walk(os.path.join(path, mainDir)):
                dirs.append("".join(dirPath.rsplit(path))[1:])
                print(dirs[len(dirs) - 1])

            for curDir in dirs:
                if curVolOfChanges < maxVolOfChanges:
                    files = os.listdir(os.path.join(path, curDir))
                    filesList = {}

                    for file in files:
                        filePath = os.path.join(path, curDir, file)
                        print(filePath)
                        already_resized = file[-5:-4]
                        extension = "." + file[-3:]  # Get extension of current file

                        if already_resized != '_':  # If file was resized, then we add '_' to the filename
                            # Resize videos to 1600px on the large size
                            if extension == '.3GP' or extension == '.MP4':
                                clipPath = filePath
                                try:
                                    curVolOfChanges += videoResize(clipPath)
                                except:
                                    print('Ошибка файла видео: ', clipPath)
                            else:
                                # Resize photos to 1600px on the large size
                                if extension == '.JPG':
                                    imgPath = filePath

                                    filesList[imgPath] = calcImageHash(imgPath)
                                    try:
                                        curVolOfChanges += imageResize(imgPath)
                                    except:
                                        print('Ошибка файла фото: ', imgPath)
                        print(round(curVolOfChanges / 1000000))

                    for i, imgHashPath in enumerate(filesList):
                        print(filesList[imgHashPath])
                        for ii, iImgHashPath in enumerate(filesList):
                            if ii > i and imgHashPath != iImgHashPath:
                                if filesList[imgHashPath] == filesList[iImgHashPath]:
                                    delBiggestPhoto(imgHashPath, iImgHashPath)

# Now we are create list of main dirs and check names of controllers and masters.
# For each suitable dir we create list of files with path and date-time of creation.
# Also we check photos in open_cv. Trying to find documents and it's name. For this will help
# find words "акт", "обследования"...
# If we find words, then rotate photo in correct angle, create dir where we transfers
# photos which refer to this document, and then rename dir in name of type of current document.


# 1. Список файлов на Макс Вол Сайз. По мере выполнения показывать процент
# 2. Открывать фото в cv2  смотреть ориентацию.
