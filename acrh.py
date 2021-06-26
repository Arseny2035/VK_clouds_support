import moviepy as mp
import numpy
from moviepy import editor
from PIL import Image
import os

import numpy as np
import argparse
import cv2
import pytesseract


####################################################################################

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

    return volOfChanges, newClipPath


####################################################################################

def imageResize(imgPath, needRotate):
    img = Image.open(imgPath)
    volOfChanges = 0
    width, height = img.size
    print(width, height)
    if height > 1600 or width > 1600:

        imgExif = img.getexif()
        if imgExif is None:
            print('Sorry, image has no exif data.')

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

        if needRotate:
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

# Find hash of pictures for farther comparison
def calcImageHash(imgPath):
    image = Image.open(imgPath)
    image = cv2.cvtColor(numpy.array(image), cv2.COLOR_RGB2BGR)  # Read image
    resized = cv2.resize(image, (8, 8), interpolation=cv2.INTER_AREA)  # Resize image to 8x8
    gray_image = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)  # Convert image in gray format
    avg = gray_image.mean()  # Find average value of pixels
    ret, threshold_image = cv2.threshold(gray_image, avg, 255, 0)  # Find binarity by the threshold

    # Find hash of picture
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


def findDuplicates(fList):
    for i, imgHashPath in enumerate(fList):
        for ii, iImgHashPath in enumerate(fList):
            if ii > i and imgHashPath != iImgHashPath:
                if fList[imgHashPath] == fList[iImgHashPath]:
                    try:
                        delBiggestPhoto(imgHashPath, iImgHashPath)
                    except:
                        pass


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

# Set directory for work where located dirs for modifying
mainDirs = os.listdir(path)

# Set maximum volume of modified files in one go
maxVolOfChanges = 5000000000
curVolOfChanges = 0

changedFilesList = []

try:
    # откроем файл и считаем его содержимое в список
    with open(os.path.join(path, 'listfile.txt'), 'r') as listFile:
        filecontents = listFile.readlines()

        for line in filecontents:
            # удалим заключительный символ перехода строки
            current_place = line[:-1]

            # добавим элемент в конец списка
            changedFilesList.append(current_place)
            listFile.close()
except:
    print('ListFile not found.')

# Calculate size of all files to resize by comparison fileList of resized files and all files in directories
# and summing their size.


for mainDir in mainDirs:
    dirs = []
    filesToCheck = []
    if mainDir[0:17] == 'Телефон контролер' or mainDir[0:14] == 'Телефон мастер' \
            or mainDir[0:14] == 'Телефон слесарь' or mainDir[0:20] == 'Фотографии абонентов' \
            or mainDir[0:18] == 'Фото-видео порывов':

        for dirPath, subFolder, files in os.walk(os.path.join(path, mainDir)):
            dirs.append("".join(dirPath.rsplit(path))[1:])

        for curDir in dirs:
            files = os.listdir(os.path.join(path, curDir))
            for file in files:
                filePath = os.path.join(path, curDir, file)
                if filePath not in changedFilesList:
                    filesToCheck.append(filePath)

        print(filesToCheck)

#
#
# for mainDir in mainDirs:
#     if curVolOfChanges < maxVolOfChanges:
#         dirs = []
#         # Scanning and modifying files in dirs of workers (maybe, we would be rotate this files, but this is wery slow function)
#         if mainDir[0:17] == 'Телефон контролер' or mainDir[0:14] == 'Телефон мастер' \
#                 or mainDir[0:14] == 'Телефон слесарь':
#
#             # Scan current directory and create list of files fow work
#             for dirPath, subFolder, files in os.walk(os.path.join(path, mainDir)):
#                 dirs.append("".join(dirPath.rsplit(path))[1:])
#
#             for curDir in dirs:
#                 if curVolOfChanges < maxVolOfChanges:
#                     # Create list of files in current directory
#                     files = os.listdir(os.path.join(path, curDir))
#                     filesList = {}
#                     for file in files:
#                         filePath = os.path.join(path, curDir, file)
#                         print(filePath)
#                         if filePath not in changedFilesList:
#                             # Try to find "_" in the end of filename, because this is the mark which tell us
#                             # that file already was resized. It important for video files because they are very large.
#                             already_resized = file[-5:-4]
#                             extension = "." + file[-3:]  # Get extension of current file
#
#                             if already_resized != '_':  # If file was resized, then we add '_' to the end of filename
#                                 # Resize videos to 1600px on the large size
#                                 if extension == '.3GP' or extension == '.MP4' or extension == '.3gp' \
#                                         or extension == '.mp4':
#                                     try:
#                                         # Append current summary volume of changes after resize
#                                         resultVideoResize = videoResize(filePath)
#                                         curVolOfChanges += resultVideoResize[0]
#                                         filePath = resultVideoResize[1]
#                                     except:
#                                         print('Ошибка файла видео: ', filePath)
#                                 else:
#                                     # Resize photos to 1600px on the large size
#                                     if extension == '.JPG' or extension == '.jpg':
#                                         try:
#                                             # Append current summary volume of changes after resize
#                                             # If True then need to find text in picture, check text orientatoin and
#                                             # rotate picture if necessary. This is wery  slow function
#                                             curVolOfChanges += imageResize(filePath, False)
#                                         except:
#                                             print('Ошибка файла фото: ', filePath)
#                                         # Appending in filelist only files of image to find duplicates after
#                                         # resize files
#                                         filesList[filePath] = calcImageHash(filePath)
#
#                             changedFilesList.append(filePath)
#
#                             # Print current summary volume of file size of changed files
#                             print(round(curVolOfChanges / 1000000), 'Mb')
#                     print('Fileslist:', filesList)
#                     # Find duplicates of photos in current directory and delete biggest file
#                     findDuplicates(filesList)

#############################################################################################

# # Scanning and modifying files in directory where files located permanently.
# # Here we also need to find duplicates
# if mainDir[0:20] == 'Фотографии абонентов' or mainDir[0:18] == 'Фото-видео порывов':
#     for dirPath, subFolder, files in os.walk(os.path.join(path, mainDir)):
#         dirs.append("".join(dirPath.rsplit(path))[1:])
#         print(dirs[len(dirs) - 1])
#
#     for curDir in dirs:
#         if curVolOfChanges < maxVolOfChanges:
#             # Create list of files in current directory
#             files = os.listdir(os.path.join(path, curDir))
#             filesList = {}
#             for file in files:
#                 filePath = os.path.join(path, curDir, file)
#                 print(filePath)
#                 # Try to find "_" in the end of filename, because this is the mark which tell us
#                 # that file already was resized. It important for video files because they are very large.
#                 already_resized = file[-5:-4]
#                 extension = "." + file[-3:]  # Get extension of current file
#
#                 if already_resized != '_':  # If file was resized, then we add '_' to the filename
#                     # Resize videos to 1600px on the large size
#                     if extension == '.3GP' or extension == '.MP4':
#                         try:
#                             # Append current summary volume of changes after resize
#                             curVolOfChanges += videoResize(filePath)
#                         except:
#                             print('Ошибка файла видео: ', filePath)
#                     else:
#                         # Resize photos to 1600px on the large size
#                         if extension == '.JPG':
#                             try:
#                                 # Append current summary volume of changes after resize
#                                 # If True then need to find text in picture, check text orientatoin and rotate
#                                 # picture if necessary. This is wery  slow function
#                                 curVolOfChanges += imageResize(filePath, False)
#                             except:
#                                 print('Ошибка файла фото: ', filePath)
#                             # Appending in filelist only files of image to find duplicates after resize files
#                             filesList[filePath] = calcImageHash(filePath)
#                 # Print current summary volume of file size of changed files
#                 print(round(curVolOfChanges / 1000000), 'Mb')
#
#             # Find duplicates of photos in current directory and delete biggest file
#             findDuplicates(filesList)

# print(changedFilesList)
# with open(os.path.join(path, 'listfile.txt'), 'w') as listFile:
#     for filename in changedFilesList:
#         # print(filename)
#         listFile.write("%s\n" % filename)
#     listFile.close()

# Now we are create list of main dirs and check names of controllers and masters.
# For each suitable dir we create list of files with path and date-time of creation.
# Also we check photos in open_cv. Trying to find documents and it's name. For this will help
# find words "акт", "обследования"...
# If we find words, then rotate photo in correct angle, create dir where we transfers
# photos which refer to this document, and then rename dir in name of type of current document.


# Дубликаты нужно искать еще и папках мастеров, но в том случае, если были обнаружены новые
# файлы. То есть в функцию файдДубликатес лучше добавить просмотр файлов и формирование их списка.
# 0. Или переименовать все файлы с _ в конце или добавлять файлы в множество и сохранять множество
# по окончанию работ.
# Если работать мнозжествами, то можно перед стартом проверить объем работы путем сравнения с
# текущим множествои и отображать процесс и примерное времся по ходу работы. По мере сравнения
# надо парралельно обнослять сам список в случае отсутствия файлов.
# 1. Список файлов на Макс Вол Сайз. По мере выполнения показывать процент
# 2. Открывать фото в cv2  смотреть ориентацию.
