import os
import sys, getopt
import pandas as pd
import xml.etree.ElementTree as ET
import shutil
import difflib

def main(argv):
    mame_dat_file_name = ''
    game_folder_name = ''
    force_neogeo = False

    # 1. Update Argument Parsing to include 'n' / 'neogeo'
    try:
        opts, args = getopt.getopt(argv, "hd:r:n", ["datfilename=", "romfoldername=", "neogeo"])
    except getopt.GetoptError:
        print('Usage: run.exe -d <datfilename> -r <romfoldername> [--neogeo]')
        sys.exit(2)
        
    for opt, arg in opts:
        if opt == '-h':
            print('Usage: run.exe -d <datfilename> -r <romfoldername> [--neogeo]')
            sys.exit()
        elif opt in ("-d", "--datfilename"):
            mame_dat_file_name = arg
        elif opt in ("-r", "--romfoldername"):
            game_folder_name = arg
        elif opt in ("-n", "--neogeo"):
            force_neogeo = True
            
    if not mame_dat_file_name or not game_folder_name:
        print('Error: Both DAT filename and ROM folder name are required.')
        sys.exit(2)

    print('MAME DAT filename is ', mame_dat_file_name)
    print('Rom folder name is ', game_folder_name)
    
    # 2. Determine is_neogeo based on folder name OR the flag
    is_neogeo = False
    if 'neogeo' in game_folder_name.lower() or force_neogeo:
        is_neogeo = True
        print("Neo Geo Mode: ENABLED")

    neogeo_bios_name = 'neogeo.zip'
    # Expects neogeo.zip to be in the same folder where you run the script
    has_neogeo_bios = os.path.isfile(neogeo_bios_name) 
    
    if is_neogeo and not has_neogeo_bios:
        print(f"Warning: Neo Geo mode is on, but '{neogeo_bios_name}' not found in script directory.")
        print("Bios files will NOT be copied.")

    # Parse DAT File
    try:
        tree = ET.parse(mame_dat_file_name)
    except FileNotFoundError:
        print(f"Error: DAT file '{mame_dat_file_name}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing XML: {e}")
        sys.exit(1)
        
    root = tree.getroot()
    game_list = []
    
    for machine in root.findall('machine'):
        rom_name = machine.get('name')
        if not rom_name: continue

        description_element = machine.find('description')
        if description_element is not None and description_element.text is not None:
            description = description_element.text.strip()
            if description:
                game_list.append([rom_name, description])

    if not game_list:
        print("No game data parsed. Exiting.")
        sys.exit(1)

    df = pd.DataFrame(columns=['rom_name', 'game_name'], data=game_list)
    df['rom_name'] = df['rom_name'].astype(str) # Ensure string for comparison
    
    cnt = 0
    if not os.path.isdir(game_folder_name):
        print(f"Error: ROM folder '{game_folder_name}' not found.")
        sys.exit(1)

    processed_files_count = 0
    matcher = difflib.SequenceMatcher(None)

    # --- MAIN PROCESSING LOOP ---
    for item_name in os.listdir(game_folder_name):
        item_path = os.path.join(game_folder_name, item_name)

        if not os.path.isfile(item_path):
            continue
        
        actual_filename, file_extension_with_dot = os.path.splitext(item_name)
        file_extension = file_extension_with_dot[1:].lower()

        if file_extension not in ['zip', '7z']:
            continue

        # Skip the bios file itself if it's sitting in the rom folder
        if item_name.lower() == neogeo_bios_name.lower():
            continue

        # --- MATCHING LOGIC (Exact -> Fuzzy 80%) ---
        game_name = None
        match_type = None

        # 1. Exact Match
        exact_matches = df[df['rom_name'] == actual_filename]
        if not exact_matches.empty:
            best_match = exact_matches.iloc[0]
            game_name = best_match['game_name']
            match_type = "Exact"
        else:
            # 2. Fuzzy Match (Fallback)
            def get_similarity(rom_val):
                matcher.set_seq1(rom_val)
                matcher.set_seq2(actual_filename)
                return matcher.ratio()

            scores = df['rom_name'].apply(get_similarity)
            potential_matches = scores[scores >= 0.8]

            if not potential_matches.empty:
                best_match_idx = potential_matches.idxmax()
                game_name = df.loc[best_match_idx, 'game_name']
                match_type = f"Fuzzy ({potential_matches[best_match_idx]:.0%})"

        if game_name is None:
            continue

        processed_files_count += 1
        print(f"Processing {processed_files_count}: '{item_name}' -> '{game_name}' [{match_type}]")

        # Clean Name
        exclusions = ['/', ':', '-', '?', '*', '\''] 
        invalid_path_chars = ['<', '>', '"', '\\', '|'] 
        all_exclusions = list(set(exclusions + invalid_path_chars))

        new_game_name = ''.join(ch for ch in game_name if ch not in all_exclusions)
        dst_name_base = new_game_name.strip()

        if not dst_name_base: dst_name_base = actual_filename

        # NeoGeo Name Shortening
        if is_neogeo:
            new_game_name_splited = dst_name_base.split('(')[0].strip()
            if len(new_game_name_splited) > 25:
                new_game_words = new_game_name_splited.split()
                temp_name = new_game_name_splited
                while len(temp_name) > 25 and len(new_game_words) > 1:
                    new_game_words.pop()
                    temp_name = ' '.join(new_game_words)
                if len(temp_name) > 25: temp_name = temp_name[:25]
                new_game_name_splited = temp_name.strip()

            dst_name_base = " ".join(new_game_name_splited.split())
            if not dst_name_base: dst_name_base = actual_filename[:25]

        target_dir_path = os.path.join(game_folder_name, dst_name_base)
        
        try:
            os.makedirs(target_dir_path, exist_ok=True)
            
            # Move File
            dst_path = os.path.join(target_dir_path, item_name)
            shutil.move(item_path, dst_path)
            
            # Create M3U
            m3u_filename_base = ''.join(ch for ch in dst_name_base if ch not in all_exclusions).strip()
            if not m3u_filename_base: m3u_filename_base = actual_filename
            m3u_file_path = os.path.join(target_dir_path, f"{m3u_filename_base}.m3u")
            
            with open(m3u_file_path, "w+") as f:
                f.write(item_name)
            
            cnt += 1
        except Exception as e:
            print(f"Error processing {item_name}: {e}")

    print(f'Moved and renamed {cnt} game files.')

    # --- BIOS CHECK & DISTRIBUTION LOOP ---
    # This runs after all files have been moved to ensure every folder is compliant
    if is_neogeo and has_neogeo_bios:
        print("\n--- Verifying Neo Geo BIOS in subfolders ---")
        bios_copy_count = 0
        
        # Iterate over all directories inside the game folder
        for folder_name in os.listdir(game_folder_name):
            folder_path = os.path.join(game_folder_name, folder_name)
            
            if not os.path.isdir(folder_path):
                continue
                
            # List files in the subfolder
            files_in_sub = os.listdir(folder_path)
            
            # Check conditions
            # 1. Contains a Zip or 7z
            has_rom = any(f.lower().endswith(('.zip', '.7z')) for f in files_in_sub)
            # 2. Contains an M3U
            has_m3u = any(f.lower().endswith('.m3u') for f in files_in_sub)
            # 3. Does NOT contain neogeo.zip
            has_bios_in_sub = neogeo_bios_name in files_in_sub
            
            if has_rom and has_m3u and not has_bios_in_sub:
                try:
                    shutil.copy(neogeo_bios_name, os.path.join(folder_path, neogeo_bios_name))
                    bios_copy_count += 1
                except Exception as e:
                    print(f"Failed to copy BIOS to {folder_name}: {e}")
                    
        print(f"Distributed neogeo.zip to {bios_copy_count} folders.")

if __name__ == '__main__':
    main(sys.argv[1:])