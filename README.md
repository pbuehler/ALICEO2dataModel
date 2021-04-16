# ALICEO2dataModel converter

Allows to create an html representation of the ALICE O2 data model.
This can be inserted in docs/framework/datamodel.md of https://github.com/pbuehler/documentation/

The parsing functionality is contained in ALICEO2dataModel.py.
The main program is in extractDataModel.py and is configured with inputCard.xml.

## As simple as that

- Install the software

git clone [git@github.com:pbuehler/ALICEO2dataModel.git](git@github.com:pbuehler/ALICEO2dataModel.git)

- Adapt inputCard.xml

Set the path in tag data/O2general/mainDir to the actual O2 installation path, e.g. home/me/alice/O2. The other parameters should fit.

- Run it

./extractDataModel.py > htmloutput.txt

- Update datamodel.md with the content of htmloutput.txt
