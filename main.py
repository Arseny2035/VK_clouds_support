import moviepy
import numpy
from PIL import Image
import os
import cv2
import pytesseract
import codecs
from moviepy.video.io.VideoFileClip import VideoFileClip


####################################################################################

# # Получить дату съемки. Если в EXIF отсутствует, либо если видео, то далее смотрим на
# # имя файлы и преобразуем из него
# def getDateTaken(img):
#     exif = img.getexif()
#     creation_time = exif.get
#     return creation_time


####################################################################################

# Функция для уменьшения разрешения клипа, сохранения уменьшенного клипа с разрешением MP4
# и удалениея старого клипа
def videoResize(clip_path):
    vol_of_changes = 0
    new_clip_path = clip_path[:-4] + '_.MP4'
    try:
        clip = VideoFileClip(clip_path)
        width, height = clip.size
        print(width, height)

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

            print("Clip duration:", clip.duration, "sec")
            clip.write_videofile(new_clip_path, fps=30, codec="libx264")

            clip.close()
            try:
                os.remove(clip_path)
            except OSError as e:
                print("Error: %s : %s" % (clip_path, e.strerror))
        else:
            clip.close()
            # Check, did we resize and resave with "_" video file early with error
            # which create both files - with "_" and without
            if os.path.exists(new_clip_path):
                os.remove(clip_path)
            else:
                os.rename(clip_path, new_clip_path)

        vol_of_changes = os.path.getsize(new_clip_path)

    except:
        print('Can\'t resize ', clip_path)

    return vol_of_changes, new_clip_path


####################################################################################

def imageResize(img_path, need_rotate):
    img = Image.open(img_path)
    vol_of_changes = 0
    width, height = img.size
    print(width, height)
    if height > 1600 or width > 1600:

        img_exif = img.getexif()
        if img_exif is None:
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

        if need_rotate:
            if imageRotate(img):
                img = img.rotate(90, expand=True)

        img.save(img_path, exif=img_exif)
        print('Resized')

        vol_of_changes = os.path.getsize(img_path)

    img.close()

    return vol_of_changes


####################################################################################

def imageRotate(img):
    img_check = cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2BGR)

    ### Detecting words
    found_word = False
    f_rotate = False
    try:
        boxes = pytesseract.image_to_data(img_check, lang="rus")
        # print(boxes)
        # Check length of width and height. If width < height then photo is rotated and we need ti rotate it.
        for x, b in enumerate(boxes.splitlines()):
            if not found_word:
                if x != 0:
                    b = b.split()
                    if len(b) == 12:
                        if len(b[11]) > 6:
                            found_word = True
                            if int(b[8]) < int(b[9]):
                                f_rotate = True
    except:
        f_rotate = False

    return f_rotate


####################################################################################

# Find hash of pictures for farther comparison
def calcImageHash(img_path):
    img = Image.open(img_path)
    img = cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2BGR)  # Read image
    resized = cv2.resize(img, (8, 8), interpolation=cv2.INTER_AREA)  # Resize image to 8x8
    gray_image = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)  # Convert image in gray format
    avg = gray_image.mean()  # Find average value of pixels
    ret, threshold_image = cv2.threshold(gray_image, avg, 255, 0)  # Find binary by the threshold

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

# Get two path to files and delete bigger of them.
def delBiggestPhoto(path1, path2):
    if os.path.getsize(path1) > os.path.getsize(path2):
        print("Deleting:", path1)
        os.remove(path1)
    else:
        os.remove(path2)
        print("Deleting:", path2)


####################################################################################


def findDuplicates(f_list):
    for i, img_hash_path in enumerate(f_list):
        for ii, i_img_hash_path in enumerate(f_list):
            if ii > i and img_hash_path != i_img_hash_path:
                if f_list[img_hash_path] == f_list[i_img_hash_path]:
                    try:
                        delBiggestPhoto(img_hash_path, i_img_hash_path)
                    except:
                        pass


####################################################################################
# Read file with list of already modified files, which no need to check.
def openChangedFilesList(f_path):
    f_changed_files_list = set()
    try:
        # open file and read in list.
        with open(os.path.join(f_path, 'listfile.txt'), 'r') as f_list_file:
            file_contents = f_list_file.readlines()

            for line in file_contents:
                # Delete last symbol of string.
                current_place = line[:-1]
                # Added new elements - files we do not checking.
                f_changed_files_list.add(current_place)
    except:
        print('ListFile not found.')
    return f_changed_files_list


####################################################################################


def closeChangedFilesList(f_changed_files_list):
    with open(os.path.join(path, 'listfile.txt'), 'w') as list_file:
        for file_name in f_changed_files_list:
            try:
                list_file.write("%s\n" % file_name)
            except:
                pass


####################################################################################


# Сначала уменьшаем фото и видео в основных папках и все всех вложенных папках
# затем в основных директориях в папках контролеров пакуем по папкам с датами и типами актов


# path = input()
pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# Load all paths where are located dirs with files.
path_list = list()
with codecs.open('pathlistfile.txt', encoding='utf-8') as p_file:
    file_contents = p_file.readlines()
    # Read parameter max_vol_of_changes and set maximum size of modified files in one program launch.
    max_vol_of_changes = int(file_contents[0].replace('max_vol_of_changes = ', '')) * 1000000
    # Read paths
    for i in range(1, len(file_contents)):
        p = file_contents[i]
        current_path = p.replace('\r\n', '')
        path_list.append(current_path)

print('path_list:', path_list)
print('max_vol_of_changes', round(max_vol_of_changes / 1000000, 0), 'mb')

for path in path_list:
    # Set directory for work where located dirs for modifying
    try:
        main_dirs = os.listdir(path)
    except:
        break

    changed_files_list = openChangedFilesList(path)

    # Count all files to resize by comparison fileList of resized files and all files in directories
    # to show correct progress in percents later.
    count_files_to_check = 0
    for main_dir in main_dirs:
        dirs = []
        if main_dir[0:17] == 'Телефон контролер' or main_dir[0:14] == 'Телефон мастер' \
                or main_dir[0:14] == 'Телефон слесарь' or main_dir[0:20] == 'Фотографии абонентов' \
                or main_dir[0:18] == 'Фото-видео порывов':

            for dir_path, sub_folder, files in os.walk(os.path.join(path, main_dir)):
                dirs.append("".join(dir_path.rsplit(path))[1:])

            for cur_dir in dirs:
                print('Checking directory: ', os.path.join(path, cur_dir))
                files = os.listdir(os.path.join(path, cur_dir))
                for file in files:
                    file_path = os.path.join(path, cur_dir, file)
                    if file_path not in changed_files_list:
                        # Count files to check to show correct value of progress.
                        count_files_to_check += 1
    ###################################

    print(count_files_to_check)


    cur_vol_of_changes = 0
    count_files = 0

    rotate = False  # Need to repair this function

    if count_files_to_check > 1:
        for main_dir in main_dirs:
            if cur_vol_of_changes < max_vol_of_changes:
                dirs = []
                # Scanning and modifying files in dirs of workers (maybe, we would be rotate this files,
                # but this is very slow function)
                if main_dir[0:17] == 'Телефон контролер' or main_dir[0:14] == 'Телефон мастер' \
                        or main_dir[0:14] == 'Телефон слесарь' or main_dir[0:20] == 'Фотографии абонентов' \
                        or main_dir[0:18] == 'Фото-видео порывов':

                    # # Need to check orientation and rotate photos only for directory "Телефон контролер"
                    # if main_dir[0:17] == 'Телефон контролер':
                    #     rotate = True
                    # else:
                    #     rotate = False

                    # Scan current directory and create list of files for work
                    for dir_path, sub_folder, files in os.walk(os.path.join(path, main_dir)):
                        dirs.append("".join(dir_path.rsplit(path))[1:])
                    for cur_dir in dirs:
                        if cur_vol_of_changes < max_vol_of_changes:
                            # Create list of files in current directory
                            files = os.listdir(os.path.join(path, cur_dir))
                            files_list = {}

                            for file in files:
                                file_path = os.path.join(path, cur_dir, file)
                                if file_path not in changed_files_list:
                                    print(file_path)
                                    count_files += 1
                                    # Update ChangedFileList every 1000 files:
                                    if count_files % 1000 == 0:
                                        closeChangedFilesList(changed_files_list)
                                        changed_files_list = openChangedFilesList(path)


                                    extension = "." + file[-3:]  # Get extension of current file
                                    if extension == '.3GP' or extension == '.MP4' or extension == '.3gp' \
                                            or extension == '.mp4':
                                        # Try to find "_" in the end of filename, because this is the mark which tell us
                                        # that file already was resized. It important for video files because they are very large.
                                        if file[-5:-4] != '_':  # If file was resized, then we add '_' to the end of filename
                                            # Resize videos to 640x on the large size
                                            try:
                                                # Append current summary volume of changes after resize
                                                resultVideoResize = videoResize(file_path)
                                                cur_vol_of_changes += resultVideoResize[0]
                                                file_path = resultVideoResize[1]
                                            except:
                                                print('Ошибка файла видео: ', file_path)
                                        else:
                                            # If videofile with current filename + "_" exist, that means then current
                                            # file already was early resized and in some reasons it wouldn't be deleted.
                                            # Maybe because we join some archives to one. So we remove current file
                                            # and don't resize it repeatedly.
                                            if file.replace(".", "_.") in files:
                                                os.remove(file_path)
                                                print("Remove already resized file:", file_path)
                                    else:
                                        # Resize photos to 1600px on the large size
                                        if extension == '.JPG' or extension == '.jpg':
                                            try:
                                                # Append current summary volume of changes after resize
                                                # If True then need to find text in picture, check text orientation and
                                                # rotate picture if necessary. This is very slow function
                                                cur_vol_of_changes += imageResize(file_path, rotate)
                                                # Appending in filelist only files of image to find duplicates after
                                                # resize files
                                                files_list[file_path] = calcImageHash(file_path)
                                            except:
                                                print('Ошибка файла фото: ', file_path)

                                    # Print current summary volume of file size of changed files
                                    print(round(count_files / count_files_to_check * 100), '%, ',
                                          round(cur_vol_of_changes / 1000000), 'Mb')

                                changed_files_list.add(file_path)

                            # Find duplicates of photos in current directory and delete biggest file
                            findDuplicates(files_list)

        closeChangedFilesList(changed_files_list)

print("Done")
os.system('pause')

# Now we are create list of main dirs and check names of controllers and masters.
# For each suitable dir we create list of files with path and date-time of creation.
# Also we check photos in open_cv. Trying to find documents and it's name. For this will help
# find words "акт", "обследования"...
# If we find words, then rotate photo in correct angle, create dir where we transfers
# photos which refer to this document, and then rename dir in name of type of current document.
