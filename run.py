# Python 3 code to rename multiple
# files in a directory or folder

# importing os module
import os
import sys, getopt
import pandas as pd
import xml.etree.ElementTree as ET
import shutil

# game_folder_name = "mame"  # in this folder you can put rom files
# mame_dat_file_name = 'MAME_ROMs_253.dat'  # must be placed in the root folder


# excluded_files = ['neogeo.zip']
def main(argv):
    mame_dat_file_name = ''
    game_folder_name = ''

    opts, args = getopt.getopt(argv, "hd:r:", ["datfilename=", "romfoldername="])
    for opt, arg in opts:
        if opt == '-h':
            print('run.exe -d <datfilename> -r <romfoldername>')
            sys.exit()
        elif opt in ("-d", "--datfilename"):
            mame_dat_file_name = arg
        elif opt in ("-r", "--romfoldername"):
            game_folder_name = arg
    print('MAME DAT filename is ', mame_dat_file_name)
    print('Rom folder name is ', game_folder_name)
    is_neogeo = False
    has_neogeo_bios = False
    if 'neogeo' in game_folder_name:
        is_neogeo = True
    neogeo_bios_name = 'neogeo.zip'
    has_neogeo_bios = os.path.isfile(neogeo_bios_name)
    tree = ET.parse(mame_dat_file_name)
    root = tree.getroot()
    game_list = []
    for machine in root.findall('machine'):
        rom_name = list(machine.attrib.values())[0]
        # using root.findall() to avoid removal during traversal
        descrption = machine.find('description').text

        game_list.append([rom_name, descrption])

    df = pd.DataFrame(columns=['rom_name', 'game_name'], data=game_list)
    # df.to_csv('parsed_game_list.csv',index=False)
    cnt = 0
    for count, filename in enumerate(os.listdir(game_folder_name)):
        print(count)
        src = f"{game_folder_name}/{filename}"  # foldername/filename, if .py file is outside folder
        # print(filename)
        if '.' not in filename:
            break
        else:
            actual_filename = filename.split('.')[0]
            file_extension = filename.split('.')[1]

        # if (df['rom_name'].eq(actual_filename)).any() and file_extension == 'zip' and filename not in excluded_files:
        if (df['rom_name'].eq(actual_filename)).any() and file_extension == 'zip':
            cnt = cnt+1
            # print('counter:' + str(count))
            game_name = df['game_name'][df['rom_name'].eq(actual_filename)].tolist()[0]
            # print(game_name)
            exclusions = ['/', ':', '-', '?', '*','\'']
            new_game_name = ''.join(ch for ch in game_name if ch not in exclusions)
            new_game_name_splited = new_game_name.split('(')[0].strip()
            if len(new_game_name_splited) > 25:
                new_game_words = new_game_name_splited.split()
                num_words = len(new_game_words)
                cur_words = new_game_name_splited
                while len(cur_words) > 25:
                    cur_words = ' '.join(word for word in new_game_words[:num_words])
                    num_words = num_words-1
                new_game_name_splited = cur_words
                #
                #
                #
                # adjust_num_words = min(3,len(new_game_words))
                # dst_name = new_game_name[:25]
            dst_name = new_game_name_splited

            try:
                os.mkdir(f'{game_folder_name}/{dst_name}')
                dst_path = f"{game_folder_name}/{dst_name}/{filename}"
                shutil.move(src, dst_path)
                if is_neogeo and has_neogeo_bios:
                    shutil.copy(neogeo_bios_name,f"{game_folder_name}/{dst_name}/{neogeo_bios_name}")
                f = open(f"{game_folder_name}/{dst_name}/{dst_name}.m3u", "w+")
                f.write(filename)
                f.close()
            except OSError as error:
                print(error)
    print(f'Processed {cnt} games!')

if __name__ == '__main__':
    main(sys.argv[1:])
