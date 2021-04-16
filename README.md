# ALICEO2dataModel converter

Allows to create an html representation of the ALICE O2 data model.
This can be inserted in docs/framework/datamodel.md of https://github.com/pbuehler/documentation/

## As simple as that

- install the software
git clone git@github.com:pbuehler/ALICEO2dataModel.git

- adapt inputCard.xml

set the path in tag data/O2general/mainDir to the actual O2 installation path, e.g. home/me/alice/O2.

- run it

./extractDataModel.py > htmloutput.txt

- update datamodel.md with the content of htmloutput.txt
