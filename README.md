# ALICEO2dataModel converter

Allows to create an html representation of the ALICE O2 data model.
The generated html code can be inserted in docs/datamodel/[ao2dTables, helperTaskTables, joinsAndIterators].md of https://github.com/AliceO2Group/analysis-framework/.

## Internals

The ALICE O2 Data Analysis Framework is based on a number of flat tables which contain the experimental data. The tables are declared in several header files. Some of the tables are filled automatically when an AO2D file is processed others are filled by specific tasks.

The ALICEO2dataModel converter analyses these header and task code files and extracts the table and column definitions of the tables. The information is converted into a html representation which can be included in the documentation site of the O2 Analysis Framework at https://github.com/AliceO2Group/analysis-framework/.

The converter is implemented in python. The parsing functionality is contained in ALICEO2dataModel.py and the main program is in extractDataModel.py. The process is configured with inputCard.xml.

## As simple as that

- Install the software

git clone [git@github.com:pbuehler/ALICEO2dataModel.git](git@github.com:pbuehler/ALICEO2dataModel.git)

- Adapt inputCard.xml

Set the path in tag data/O2general/mainDir/local to the actual O2 installation path, e.g. home/me/alice/O2. The other parameters should fit.

- Run it

./extractDataModel.py > htmloutput.txt

- Update the markdown files with the content of htmloutput.txt.
