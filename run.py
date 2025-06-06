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
# excluded_files = ['neogeo.zip'] # This was commented out, kept as is.

def main(argv):
    mame_dat_file_name = ''
    game_folder_name = ''

    try:
        opts, args = getopt.getopt(argv, "hd:r:", ["datfilename=", "romfoldername="])
    except getopt.GetoptError:
        print('Usage: run.exe -d <datfilename> -r <romfoldername>')
        sys.exit(2)
        
    for opt, arg in opts:
        if opt == '-h':
            print('Usage: run.exe -d <datfilename> -r <romfoldername>')
            sys.exit()
        elif opt in ("-d", "--datfilename"):
            mame_dat_file_name = arg
        elif opt in ("-r", "--romfoldername"):
            game_folder_name = arg
            
    if not mame_dat_file_name or not game_folder_name:
        print('Error: Both DAT filename and ROM folder name are required.')
        print('Usage: run.exe -d <datfilename> -r <romfoldername>')
        sys.exit(2)

    print('MAME DAT filename is ', mame_dat_file_name)
    print('Rom folder name is ', game_folder_name)
    
    is_neogeo = False
    if 'neogeo' in game_folder_name.lower(): # Make check case-insensitive
        is_neogeo = True
        
    neogeo_bios_name = 'neogeo.zip'
    # Check for neogeo.zip in the script's current directory or a more robust path if needed
    has_neogeo_bios = os.path.isfile(neogeo_bios_name) 
    if is_neogeo and not has_neogeo_bios:
        print(f"Warning: Neo Geo folder detected, but '{neogeo_bios_name}' not found in the script's directory.")

    try:
        tree = ET.parse(mame_dat_file_name)
    except FileNotFoundError:
        print(f"Error: DAT file '{mame_dat_file_name}' not found.")
        sys.exit(1)
    except ET.ParseError:
        print(f"Error: Could not parse DAT file '{mame_dat_file_name}'. It might be corrupted or not valid XML.")
        sys.exit(1)
        
    root = tree.getroot()
    game_list = []
    
    for machine in root.findall('machine'):
        rom_name = machine.get('name') # Robust way to get 'name' attribute
        if not rom_name:
            # print("Warning: Found a <machine> tag without a 'name' attribute. Skipping.")
            continue

        description_element = machine.find('description')
        if description_element is not None and description_element.text is not None:
            description = description_element.text.strip() # Get text and strip whitespace
            if description: # Ensure description is not empty after stripping
                game_list.append([rom_name, description])
            # else:
                # print(f"Warning: Machine '{rom_name}' has an empty description. Skipping.")
        # else:
            # print(f"Warning: Machine '{rom_name}' has no <description> tag or text. Skipping.")

    if not game_list:
        print("No game data parsed from DAT file. Exiting.")
        sys.exit(1)

    df = pd.DataFrame(columns=['rom_name', 'game_name'], data=game_list)
    # df.to_csv('parsed_game_list.csv',index=False) # Kept commented
    
    cnt = 0
    if not os.path.isdir(game_folder_name):
        print(f"Error: ROM folder '{game_folder_name}' not found or is not a directory.")
        sys.exit(1)

    processed_files_count = 0
    for item_name in os.listdir(game_folder_name):
        # Original script printed count for every item, now let's refine this
        # print(count) # This referred to enumerate before, now we manage a different counter

        item_path = os.path.join(game_folder_name, item_name)

        # Process only files
        if not os.path.isfile(item_path):
            # print(f"Skipping directory or non-file: {item_name}")
            continue
        
        # Robust way to get filename (without extension) and extension
        actual_filename, file_extension_with_dot = os.path.splitext(item_name)
        file_extension = file_extension_with_dot[1:].lower() # Get extension without dot, and lowercase for comparison

        # The original script used 'filename' for the full name with extension (item_name here)
        # src = f"{game_folder_name}/{item_name}" # This is equivalent to item_path

        # Original logic based on 'filename' (which is item_name here)
        # if (df['rom_name'].eq(actual_filename)).any() and filename not in excluded_files: # excluded_files is commented out
        if (df['rom_name'].eq(actual_filename)).any() and (file_extension == 'zip' or file_extension == '7z'):
            processed_files_count +=1
            print(f"Processing file {processed_files_count}: {item_name}")

            game_name_series = df['game_name'][df['rom_name'].eq(actual_filename)]
            if game_name_series.empty:
                # print(f"Warning: No game name found for ROM '{actual_filename}', though it was in DAT. Skipping.")
                continue
            
            game_name = game_name_series.tolist()[0]
            
            exclusions = ['/', ':', '-', '?', '*', '\''] # As per original script
            # Also remove characters invalid for directory names on Windows/Linux
            # Windows: < > : " / \ | ? *
            # Linux: / and null character
            # A more comprehensive exclusion list or a slugify function might be better
            # For now, keeping original exclusions + a few more common ones for paths
            invalid_path_chars = ['<', '>', '"', '\\', '|'] 
            all_exclusions = list(set(exclusions + invalid_path_chars)) # Combine and remove duplicates

            new_game_name = ''.join(ch for ch in game_name if ch not in all_exclusions)
            dst_name_base = new_game_name.strip() # Remove any leading/trailing spaces from cleaned name

            if not dst_name_base: # If game name becomes empty after stripping exclusions
                print(f"Warning: Game name for '{item_name}' became empty after cleaning. Using ROM name '{actual_filename}' instead.")
                dst_name_base = actual_filename

            if is_neogeo:
                new_game_name_splited = dst_name_base.split('(')[0].strip()
                if len(new_game_name_splited) > 25:
                    new_game_words = new_game_name_splited.split()
                    # Truncate progressively
                    temp_name = new_game_name_splited
                    while len(temp_name) > 25 and len(new_game_words) > 1:
                        new_game_words.pop() # Remove the last word
                        temp_name = ' '.join(new_game_words)
                    
                    # If even one word is > 25, truncate that word
                    if len(temp_name) > 25:
                        temp_name = temp_name[:25]
                    
                    new_game_name_splited = temp_name.strip()

                dst_name_base = " ".join(new_game_name_splited.split()) # Normalize spaces
                if not dst_name_base: # Fallback if name becomes empty after truncation
                     dst_name_base = actual_filename[:25]


            # Ensure dst_name_base is not empty
            if not dst_name_base:
                print(f"Warning: Destination folder name for '{item_name}' is empty. Using ROM name '{actual_filename}'.")
                dst_name_base = actual_filename


            target_dir_path = os.path.join(game_folder_name, dst_name_base)
            
            try:
                os.makedirs(target_dir_path, exist_ok=True) # Use makedirs with exist_ok=True
                
                dst_path = os.path.join(target_dir_path, item_name)
                shutil.move(item_path, dst_path)
                
                if is_neogeo and has_neogeo_bios:
                    shutil.copy(neogeo_bios_name, os.path.join(target_dir_path, neogeo_bios_name))
                
                # M3U filename should also be cleaned
                m3u_filename_base = ''.join(ch for ch in dst_name_base if ch not in all_exclusions).strip()
                if not m3u_filename_base: # Fallback if m3u base name is empty
                    m3u_filename_base = actual_filename

                m3u_file_path = os.path.join(target_dir_path, f"{m3u_filename_base}.m3u")
                with open(m3u_file_path, "w+") as f:
                    f.write(item_name) # Write the original ROM filename
                
                cnt += 1 # Count successfully processed games
            except OSError as error:
                print(f"OSError for {item_name}: {error}")
            except Exception as e:
                print(f"An unexpected error occurred while processing {item_name}: {e}")

    print(f'Processed {cnt} game files!')

if __name__ == '__main__':
    main(sys.argv[1:])