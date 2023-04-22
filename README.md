## miniUI-arcade-filename-converter

### Why do you need this?
- In miniUI (this applies to RG35XX, but I believe it will work for miyoo mini as well), Arcade roms are displayed by the rom names instead of the name of the game itself, so it is not easy to recognize the game form the rom name. This tool basically converts the list of roms into the format that will show the list of game names under miniUI. The game names are parsed from MAME DAT file.


### How to use
- you need to download and place MAME DAT file in the root directory, you can download the DAT file from e.g., https://www.progettosnaps.net/dats/MAME/
- place your arcade roms (e.g., MAME, FBNeo, neogeo, etc) under your rom folder; you can choose your name e.g., ```roms/mame``` or ```roms/neogeo```
- Now you can run the script to process the games;
- Usage:
  ```
  run.py -d <datfilename> -r <romfoldername>

  ```
- Example:
  ```
  python run.py -d MAME_ROMs_253.dat -r roms/neogeo
  ```

### Example output
- As you can see, a folder is generated with the game name that will be shown in miniUI game list along with m3u and origin zipped rom file
  ![image](https://user-images.githubusercontent.com/1568391/233762894-014c3567-fcf7-4f88-891f-9121371c0eca.png)


