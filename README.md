## minUI-arcade-filename-converter

### Why do you need this?
- In minUI (this applies to RG35XX, but I believe it will work for miyoo mini as well), Arcade roms are displayed by the rom names instead of the name of the game itself, so it is not easy to recognize the game form the rom name. This tool basically converts the list of roms into the format that will show the list of game names under minUI. The game names are parsed from MAME DAT file.


### How to use
- you need to download and place MAME DAT file in the root directory (where the ```run.py``` file is located), you can download the DAT file from e.g., https://www.progettosnaps.net/dats/MAME/
- place your arcade roms (e.g., MAME, FBNeo, neogeo, etc) under your rom folder; you can choose the name of the folder e.g., ```roms```, ```mame```, ```roms/mame``` or ```roms/neogeo```, etc
- Install necessary libraries used for the script using pip, e.g., ```pip3 install -r requirements.txt```
- Now you can run the script to process the games;
- Usage:
  ```
  run.py -d <datfilename> -r <romfoldername>
  ```
- Example:
  ```
  python run.py -d MAME_ROMs_253.dat -r roms/neogeo
  ```
- A new feature added: if you place ```neogeo.zip``` in the root directory and the roms directory name contains the string ```neogeo``` the neogeo bios will be copied into the sub folder which is required to run the neo-geo games 

### Example output
- As you can see, a folder is generated with the game name that will be shown in minUI game list along with m3u and origin zipped rom file

![img.png](img.png)


### Please contact me for any bugs.
