# Nokia_project

things to install to get this project up and running:
1) Python version Python 3.12.6 (https://www.python.org/downloads/)
2) Hyperscan version  0.7.27 (pip install hyperscan)


Things done: 
1) Searching a file using hyperscan in stream mode.
2) Searching a directory using hyperscan in stream mode.
3) possibility of changing the engine to python regex
    -new opt flag --engine:
    python main.py run regex.txt test_file.txt --engine (python or hyperscan)


Things to do:
1) Add the option to search a directory without searching selected files/data extensions (e.g., log, txt, etc.).
2) Create a class for saving regexes to a text file (consider whether to make some kind of extension for the future) and saving recompiled regexes
3) Use recompiled regexes for searching files or directories

