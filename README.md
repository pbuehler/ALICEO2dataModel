# ALICEO2dataModel converter

Allows to create an html representation of the ALICE O2 data model.
This can be inserted in docs/framework/datamodel.md of https://github.com/pbuehler/documentation/

The parsing functionality is conatined in ALICEO2dataModel.py.
The main program is contained in extractDataModel.py.
The program can be configured with inputCard.xml.

## As simple as that

- install the software
git clone git@github.com:pbuehler/ALICEO2dataModel.git

- adapt inputCard.xml

set the path in tag data/O2general/mainDir to the actual O2 installation path, e.g. home/me/alice/O2.

- run it

./extractDataModel.py > htmloutput.txt

- update datamodel.md with the content of htmloutput.txt
