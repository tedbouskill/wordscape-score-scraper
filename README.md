# wordscape-score-scraper

 A project to pull screenshots of weekend tournament scores to build a database and website showing the scores.

 ## Project Charter

 - Screen captures will be screenshots in Apple Photos
 - Visual Studio Code will be the development tool on the MacOS
 - Python will be the main programming language
 - AppleScript might be used as a supplemental language
 - Some manual steps are acceptable
 - SQLite will store the data
 - The website will be published using GitHub Actions to GitHub pages

 ## Python Environment

 I've used micromamba for this environment because this repository was created on a 2013 Late Model Macbook Pro.

### To rebuild the enviroment YAML file
 micromamba env export -n wordscape-score-scraper > environment.yaml

 ## Managing SQLite

 Two recommended tools for managing your SQLite database

 [BD Browser](https://sqlitebrowser.org/dl/)

 [SQLiteStudio](https://sqlitestudio.pl/)
