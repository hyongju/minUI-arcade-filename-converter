# Python 3 code to rename multiple
# files in a directory or folder

# importing os module
import os
import pandas as pd
import xml.etree.ElementTree as ET
import shutil

game_folder_name = "mame"  # in this folder you can put rom files
mame_dat_file_name = 'MAME_ROMs_253.dat'  # must be placed in the root folder


# excluded_files = ['neogeo.zip']
def main():
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

    for count, filename in enumerate(os.listdir(game_folder_name)):
        src = f"{game_folder_name}/{filename}"  # foldername/filename, if .py file is outside folder
        print(filename)
        if '.' not in filename:
            break
        else:
            actual_filename = filename.split('.')[0]
            file_extension = filename.split('.')[1]

        # if (df['rom_name'].eq(actual_filename)).any() and file_extension == 'zip' and filename not in excluded_files:
        if (df['rom_name'].eq(actual_filename)).any() and file_extension == 'zip':
            print('counter:' + str(count))
            game_name = df['game_name'][df['rom_name'].eq(actual_filename)].tolist()[0]
            print(game_name)
            exclusions = ['/', ':', '-', '?', '*']
            new_game_name = ''.join(ch for ch in game_name if ch not in exclusions)
            print(new_game_name)
            dst_name = new_game_name

            try:
                os.mkdir(f'{game_folder_name}/{dst_name}')
                dst_path = f"{game_folder_name}/{dst_name}/{filename}"
                shutil.move(src, dst_path)

                f = open(f"{game_folder_name}/{dst_name}/{dst_name}.m3u", "w+")
                f.write(filename)
                f.close()
            except OSError as error:
                print(error)


if __name__ == '__main__':
    main()
