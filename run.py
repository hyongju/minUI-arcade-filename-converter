import os
import sys, getopt
import pandas as pd
import xml.etree.ElementTree as ET
import shutil
import difflib

def sanitize_text(text):
    """
    Splits by ANY whitespace and joins with single space.
    Removes double spaces, tabs, and leading/trailing whitespace.
    """
    return " ".join(text.split())

def cleanup_filesystem(root_folder):
    """
    Recursively scans ALL folders and files to fix naming issues.
    Uses bottom-up walk to safely rename children before parents.
    """
    print(f"\n--- Starting Cleanup Scan in: {root_folder} ---")
    renamed_count = 0
    
    # topdown=False is CRITICAL. It ensures we visit files/subfolders 
    # BEFORE we visit the parent folder that contains them.
    # This prevents path errors when renaming directories.
    for current_root, dirs, files in os.walk(root_folder, topdown=False):
        
        # 1. Fix Files
        for filename in files:
            # Skip hidden files or system files if necessary, or just process all
            clean_name = sanitize_text(filename)
            
            if clean_name != filename:
                src = os.path.join(current_root, filename)
                dst = os.path.join(current_root, clean_name)
                
                try:
                    if not os.path.exists(dst):
                        os.rename(src, dst)
                        print(f"[Fix File] '{filename}' -> '{clean_name}'")
                        renamed_count += 1
                    else:
                        print(f"[Skip File] Target '{clean_name}' already exists.")
                except OSError as e:
                    print(f"Error renaming file {filename}: {e}")

        # 2. Fix Directories
        for dirname in dirs:
            clean_name = sanitize_text(dirname)
            
            if clean_name != dirname:
                src = os.path.join(current_root, dirname)
                dst = os.path.join(current_root, clean_name)
                
                try:
                    if os.path.exists(dst):
                        # Merge Case: Target folder already exists.
                        # We must move contents from Bad -> Good, then delete Bad.
                        print(f"[Merging] '{dirname}' contents into '{clean_name}'")
                        for sub_item in os.listdir(src):
                            s_item = os.path.join(src, sub_item)
                            d_item = os.path.join(dst, sub_item)
                            if not os.path.exists(d_item):
                                shutil.move(s_item, d_item)
                        
                        # Try to remove the now-empty source directory
                        try:
                            os.rmdir(src)
                            renamed_count += 1
                        except OSError:
                            print(f"[Warning] Could not remove '{dirname}' after merge. Is it empty?")
                    else:
                        # Simple Rename Case
                        os.rename(src, dst)
                        print(f"[Fix Folder] '{dirname}' -> '{clean_name}'")
                        renamed_count += 1
                except OSError as e:
                    print(f"Error renaming folder {dirname}: {e}")

    print(f"--- Cleanup Complete. Fixed {renamed_count} items. ---\n")

def main(argv):
    mame_dat_file_name = ''
    game_folder_name = ''
    force_neogeo = False

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

    if not os.path.isdir(game_folder_name):
        print(f"Error: ROM folder '{game_folder_name}' not found.")
        sys.exit(1)

    print('MAME DAT filename is ', mame_dat_file_name)
    print('Rom folder name is ', game_folder_name)
    
    # --- RUN CLEANUP BEFORE ANYTHING ELSE ---
    cleanup_filesystem(game_folder_name)
    
    is_neogeo = False
    if 'neogeo' in game_folder_name.lower() or force_neogeo:
        is_neogeo = True
        print("Neo Geo Mode: ENABLED")

    neogeo_bios_name = 'neogeo.zip'
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
    df['rom_name'] = df['rom_name'].astype(str)
    
    cnt = 0
    processed_files_count = 0
    matcher = difflib.SequenceMatcher(None)

    # --- MAIN PROCESSING LOOP (Moves files from root -> subfolders) ---
    print("\n--- Starting Main Organization ---")
    for item_name in os.listdir(game_folder_name):
        item_path = os.path.join(game_folder_name, item_name)

        # Skip directories (folders are handled by cleanup, or already organized)
        if not os.path.isfile(item_path):
            continue
        
        actual_filename, file_extension_with_dot = os.path.splitext(item_name)
        file_extension = file_extension_with_dot[1:].lower()

        if file_extension not in ['zip', '7z']:
            continue

        if item_name.lower() == neogeo_bios_name.lower():
            continue

        # --- MATCHING LOGIC ---
        game_name = None
        match_type = None

        exact_matches = df[df['rom_name'] == actual_filename]
        if not exact_matches.empty:
            best_match = exact_matches.iloc[0]
            game_name = best_match['game_name']
            match_type = "Exact"
        else:
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

        # Clean Name & Sanitize Spaces
        exclusions = ['/', ':', '-', '?', '*', '\''] 
        invalid_path_chars = ['<', '>', '"', '\\', '|'] 
        all_exclusions = list(set(exclusions + invalid_path_chars))

        new_game_name = ''.join(ch for ch in game_name if ch not in all_exclusions)
        
        # Ensure single spaces for the NEW folder we are about to create
        dst_name_base = sanitize_text(new_game_name)

        if not dst_name_base: 
            dst_name_base = actual_filename

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

            dst_name_base = sanitize_text(new_game_name_splited)
            if not dst_name_base: dst_name_base = actual_filename[:25]

        # Double check final folder name
        dst_name_base = sanitize_text(dst_name_base)

        target_dir_path = os.path.join(game_folder_name, dst_name_base)
        
        try:
            os.makedirs(target_dir_path, exist_ok=True)
            
            dst_path = os.path.join(target_dir_path, item_name)
            shutil.move(item_path, dst_path)
            
            # Create M3U with sanitized name
            m3u_filename_base = ''.join(ch for ch in dst_name_base if ch not in all_exclusions)
            m3u_filename_base = sanitize_text(m3u_filename_base)
            
            if not m3u_filename_base: m3u_filename_base = actual_filename
            m3u_file_path = os.path.join(target_dir_path, f"{m3u_filename_base}.m3u")
            
            with open(m3u_file_path, "w+") as f:
                f.write(item_name)
            
            cnt += 1
        except Exception as e:
            print(f"Error processing {item_name}: {e}")

    print(f'Moved and renamed {cnt} game files.')

    # --- BIOS CHECK & DISTRIBUTION LOOP ---
    if is_neogeo and has_neogeo_bios:
        print("\n--- Verifying Neo Geo BIOS in subfolders ---")
        bios_copy_count = 0
        
        for folder_name in os.listdir(game_folder_name):
            folder_path = os.path.join(game_folder_name, folder_name)
            
            if not os.path.isdir(folder_path):
                continue
                
            files_in_sub = os.listdir(folder_path)
            
            has_rom = any(f.lower().endswith(('.zip', '.7z')) for f in files_in_sub)
            has_m3u = any(f.lower().endswith('.m3u') for f in files_in_sub)
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