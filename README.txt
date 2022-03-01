===========================
PINTEREST IMAGE DOWNLOADER
===========================

How to install
+++++++++++++++
    1. Install python by following these steps:
        a. Open a terminal -  Click the Launchpad icon  in the Dock, type Terminal in the search field, then click Terminal.
        b. Type the following:
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        c. Once the command above is done type:
            brew install python3
        
    2. Open a terminal - Click the Launchpad icon  in the Dock, type Terminal in the search field, then click Terminal.

    3. Drag and drop this folder onto the Terminal icon in the Dock.

    4. Type the command (on the terminal):
            pip3 install -r requirements.txt

    5. You are now ready to go


How to run the script
+++++++++++++++++++++
The file 'search_terms.txt' contains the list of words that the script will search and download its images.
Each search term SHOULD BE on its own line.
Edit the file above to change what is searched for.

1. Open a terminal - Click the Launchpad icon  in the Dock, type Terminal in the search field, then click Terminal.
2. Drag and drop this folder onto the Terminal icon in the Dock.
3. Type to start the script:
    python3 PinterestDL.py 
4. The script will now start running and inform you when it is done
