#!/usr/bin/python3.6
import sys
import numpy as np
import nltk

# -----------------------------------------------------------------------------
# definitions
#
# .............................................................................
# types of column declarations
# 0: COLUMN
# 1: INDEX_COLUMN_FULL
# 2: INDEX_COLUMN
# 3: EXPRESSION_COLUMN
# 4: DYNAMIC_COLUMN
#
def columnTypes(abbr=0):
  if abbr == 0:
    types = ["", "INDEX_", "INDEX_", "EXPRESSION_", "DYNAMIC_"]
    types = [s+"COLUMN" for s in types]
    types = ["DECLARE_SOA_"+s for s in types]
    types[1] = types[1]+"_FULL"
  else:
    types = ["", "I", "I", "E", "D","GI"]

  return types

# .............................................................................
# types of table declarations
# 0: TABLE
# 1: TABLE_FULL
# 2: EXTENDED_TABLE
# 3: INDEX_TABLE
# 4: INDEX_TABLE_EXCLUSIVE
# 5: EXTENDED_TABLE_USER
#
def tableTypes(abbr=0):
  if abbr == 0:
    types = ["", "", "EXTENDED_", "INDEX_", "INDEX_", "EXTENDED_"]
    types = [s+"TABLE" for s in types]
    types = ["DECLARE_SOA_"+s for s in types]
    types[1] = types[1]+"_FULL"
    types[4] = types[4]+"_EXCLUSIVE"
    types[5] = types[5]+"_USER"
  else:
    types = ["", "", "E", "I", "I", "E"]

  return types

# -----------------------------------------------------------------------------
# classes
#
# .............................................................................
# holds a word and the corresponding line number
class word:
  def __init__(self, txt, lnr):
    self.txt = txt
    self.lnr = lnr

# .............................................................................
class typedef:
  def __init__(self, name, cont):
    self.name = name
    self.cont = cont

  def print(self):
    print("    typedef: "+self.name)
    print("      content: "+self.cont)

# .............................................................................
class define:
  def __init__(self, name, line):
    self.name = name
    self.vars = list()

    # how many parameters
    vars = "".join(line.split("(")[1:]).split(")")[0].split(",")
    if vars[0] != "":
      self.vars = vars
      self.cont = ")".join(line.split(")")[1:]).strip()
    else:
      self.cont = line

  def expandLine(self, line):
    expandedLine = line

    if self.name in line:
      if len(self.vars) == 0:
        # no substitution of variables needed
        expandedLine = line.replace(self.name, self.cont)
      else:
        # substitute variables vars
        vars = "".join(line.split("(")[1:]).split(")")[0].split(",")
        if len(vars) != len(self.vars):
          print("ATTENTION")
          print("Substitution error!")
          print("")
          self.print()
          print("")
          print("    ", line)

        else:
          words = split(self.cont)
          for ind1 in range(len(self.vars)):
            for ind2 in range(len(words)):
              if words[ind2] == self.vars[ind1].strip():
                words[ind2] = vars[ind1]
          expandedLine = block(words)

    return expandedLine

  def print(self):
    print("    define: "+self.name)
    print("      content: "+self.cont)

# .............................................................................
class using:
  def __init__(self, nslevel, name, definition, cont):
    self.nslevel = nslevel
    self.name = name
    self.definition = definition
    self.cont = cont
    self.kind = 0
    self.master = ""
    self.joiners = list()

    self.master = fullDataModelName(nslevel, definition)
    if definition.find("::iterator") != -1:
      self.kind += 1
      self.master = fullDataModelName(nslevel, "::".join(definition.split("::")[:-1]))
    if definition.find("::Join<") != -1:
      self.kind += 2
      tmp = definition.split("<")[1]
      tmp = tmp.split(">")[0]
      self.joiners = [fullDataModelName(self.nslevel, s) for s in tmp.split(",")]

  # is this included
  def where(self, usings):
    for ind in range(len(usings)):
      if self.name == usings[ind].name:
        return ind
    return -1

  def synchronize(self, dm):
    # check if any master equals a using name
    if self.kind & 1 > 0:
      for nsp in dm.namespaces:
        for use in nsp.usings:
          if self.master == use.name:
            self.kind += 2
            self.joiners = use.joiners

  def print(self):
    print("    using: "+self.name)
    print("      kind: ", self.kind)
    print("      definition: ", self.definition)
    if self.kind & 1 > 0:
      print("      master: "+self.master)
    if self.kind & 2 > 0:
      print("      joiners: ", self.joiners)

  def printHTML(self):
    toPrint = self.name+" = "
    if self.kind & 2 > 0:
      toPrint += "soa::Join<"
      for ind in range(len(self.joiners)):
        if ind == 0:
          toPrint += self.joiners[ind]
        else:
          toPrint += ", "+self.joiners[ind]
      toPrint += ">"
    else:
      toPrint += self.master

    if self.kind & 1 > 0:
      toPrint += "::iterator"

    print("        <li>"+toPrint+"</li>")

# -----------------------------------------------------------------------------
class column:
  def __init__(self, kind, nslevel, cname, vname, type, cont):
    self.kind = kind
    self.nslevel = nslevel
    self.cname = cname
    self.vname = vname
    self.type = type
    self.cont = cont
    self.pointsInto = ""
    self.comment = ""

  def where(self, columns):
    for ind in range(len(columns)):
      if self.cname == columns[ind].cname:
        return ind
    return -1

  def print(self):
    print("    column: "+self.cname)
    print("      kind: ", self.kind)
    print("    access: "+self.vname)
    print("      type: "+self.type)
    print("   comment: "+self.comment)

  def printHTML(self):
    print("      <tr>")
    print("        <td>"+fullDataModelName(self.nslevel, self.cname)+"</td>")
    print("        <td>"+columnTypes(1)[self.kind]+"</td>")
    print("        <td>"+self.vname+"</td>")
    print("        <td>"+self.type+"</td>")
    if self.kind == 1:
      print("        <td>pointer into table "+self.pointsInto+"</td>")
    else:
      print("        <td>"+self.comment+"</td>")
    print("      </tr>")

# .............................................................................
class table:
  def __init__(self, kind, nslevel, name, cont):
    self.kind = kind
    self.nslevel = nslevel
    self.name = name
    self.producer = ""
    self.cont = cont
    self.colNames = list()
    self.columns = list()
    self.toExtendWith = ""
    self.comment = ""

  def addColumn(self, col):
    self.columns.append(col)

  def where(self, tables):
    for ind in range(len(tables)):
      if self.name == tables[ind].name:
        return ind
    return -1

  # fill columns
  def synchronize(self, dm):
    for colName in self.colNames:
      # get column with name colName
      self.columns.append(dm.getColumn(colName))

  def print(self):
    print("    table: "+self.name)
    print("          kind: ", self.kind)
    print("      producer: "+self.producer)
    for col in self.columns:
      print("      column: "+col.cname+":"+col.type)

  def printHeaderHTML(self):
    tableName = self.name
    if tableTypes(1)[self.kind] != "":
      tableName += " ("+tableTypes(1)[self.kind]+")"
    print("  <button class=\"myaccordion\"><i class=\"fa fa-table\"></i> "+tableName+"</button>")
    print("  <div class=\"panel\">")

  def printSubHeaderHTML(self):
    print("    <table class=DataModel>")
    print("      <tr>")
    print("        <th>Name</th>")
    print("        <th></th>")
    print("        <th>Getter</th>")
    print("        <th>Type</th>")
    print("        <th>Comment</th>")
    print("      </tr>")

  def printFooterHTML(self):
    print("    </table>")
    print("  </div>")
    print("")


# -----------------------------------------------------------------------------
class namespace:
  def __init__(self, nslevel, cont):
    self.nslevel = nslevel
    self.cont = cont
    self.columns = list()
    self.tables = list()
    self.usings = list()

  def addUsing(self, using):
    self.usings.append(using)

  def addColumn(self, col):
    self.columns.append(col)

  def addTable(self, table):
    self.tables.append(table)

  # set the producer
  def setProducer(self, producerName, tableName):
    for ind in range(len(self.tables)):
      if self.tables[ind].name == tableName:
        self.tables[ind].producer = producerName

  # fill columns of all tables
  def synchronize(self, dm):
    for use in self.usings:
      use.synchronize(dm)
    for tab in self.tables:
      tab.synchronize(dm)

  # merge with newnsp
  def join(self, newnsp):
    if newnsp.nslevel != self.nslevel:
      return
    for use in newnsp.usings:
      ind = use.where(self.usings)
      if ind < 0:
        self.usings.append(use)
    for tab in newnsp.tables:
      ind = tab.where(self.tables)
      if ind < 0:
        self.tables.append(tab)
    for col in newnsp.columns:
      ind = col.where(self.columns)
      if ind < 0:
        self.columns.append(col)

  def print(self):
    print("  namespace: "+self.nslevel)
    print("    number of tables: ", len(self.tables))
    for tab in self.tables:
      tab.print()
    print("    number of usings: ", len(self.usings))
    for use in self.usings:
      use.print()
    print("    number of columns: ", len(self.columns))
    for col in self.columns:
      col.print()

# -----------------------------------------------------------------------------
class datamodel:
  def __init__(self, name, fileName):
    with open(fileName, 'r') as file:
      self.name = name
      self.producers = list()
      self.producers.append(name)
      self.defines = list()
      self.namespaces = list()

      # read the file
      lines_in_file = file.readlines()
      content = pickContent(lines_in_file)

      # parse datamodel
      parseContent(content, "", self)
      self.synchronize()

  def addNamespace(self, namespace):
    # does this namespace exist already?
    ind = self.where(namespace)
    if ind >= 0:
      self.namespaces[ind].join(namespace)
    else:
      self.namespaces.append(namespace)

  def addDefine(self, define):
    self.defines.append(define)

  def setProducer(self, producerName, tableName):
    for nsp in self.namespaces:
      nsp.setProducer(producerName, tableName)
      if not producerName in self.producers:
        self.producers.append(producerName)

  def isProducedBy(self, producer):
    producedBy = list()
    for nsp in self.namespaces:
      for table in nsp.tables:
        if table.producer == producer:
          producedBy.append(table)
    return producedBy

  def where(self, namespace):
    for ind in range(len(self.namespaces)):
      if namespace.nslevel == self.namespaces[ind].nslevel:
        return ind
    return -1

  # join with data model dmnew
  def join(self, dmnew):
    for nsp in dmnew.namespaces:
      ind = self.where(nsp)
      if ind >= 0:
        self.namespaces[ind].join(nsp)
      else:
        self.namespaces.append(nsp)

  # fill columns of all tables
  def synchronize(self):
    for nsp in self.namespaces:
      nsp.synchronize(self)

  def getColumn(self, colName):
    # remove <> from colName
    cnameToSearch = colName.split("<")[0]

    # index columns are special!
    if cnameToSearch == "o2::soa::Index":
      return column(len(columnTypes(1))-1, "o2::soa", cnameToSearch, "globalIndex", "int64_t", colName)

    for nsp in self.namespaces:
      for col in nsp.columns:
        cnameToUse = fullDataModelName(nsp.nslevel, col.cname)
        if cnameToUse == cnameToSearch:
          return col

    # create dummy column
    return column(-1, "", cnameToSearch, "", "?", colName)

  def print(self):
    print("data model: "+self.name)
    print("  producers:")
    for prod in self.producers:
      print("    ", prod)
    for ns in self.namespaces:
      ns.print()

  def printHTML(self):
    # gather all tables and columns
    tabs = list()
    uses = list()
    for nsp in self.namespaces:
      for tab in nsp.tables:
        tabs.append(tab)
      for use in nsp.usings:
        uses.append(use)

    # loop over producers
    HTheaderToWrite = True
    amFirst = True
    for producer in self.producers:
      # get tables with given producer
      inds = [i for i, x in enumerate(tabs) if x.producer == producer]
      if len(inds) == 0:
        continue

      if amFirst == False and HTheaderToWrite == True:
        self.printHTheaderHTML()
        HTheaderToWrite = False

      print("")
      print("#### ", producer)
      print("<div>")
      print("")

      for ind in inds:
        tab = tabs[ind]

        # print the table header
        tab.printHeaderHTML()

        # print table comment
        print ("    <div>")
        print ("      ",tab.comment)
        print ("    </div>")
        
        # print extends
        if tab.kind == 2 or tab.kind == 5:
          print ("    <div>Extends:")
          print ("      <ul>")
          print ("        ",tab.toExtendWith)
          print ("      </ul>")
          print ("    </div>")
        
        # find all usings with tab
        useTable = list()
        for use in uses:
          if tab.name in use.joiners:
            useTable.append(use)
          elif tab.name == use.master:
            useTable.append(use)

        # print these usings
        if len(useTable) > 0:
          print("    <div>Is used in:")
          print("      <ul>")
          for use in useTable:
            use.printHTML()
          print("      </ul>")
          print("    </div>")

        # print the table header
        tab.printSubHeaderHTML()

        # EXTENDED_TABLE and EXTENDED_TABLE_USER are extended
        if tab.kind == 2 or tab.kind == 5:
          # this table has to be extended, find the extending table and
          # print all of its columns
          einds = [i for i, x in enumerate(tabs) if x.name == tab.toExtendWith]
          for ind in einds:
            for col in tabs[ind].columns:
              col.printHTML()

        # print the remaining columns
        for col in tab.columns:
          col.printHTML()

        # print the table footer
        tab.printFooterHTML()

      print("</div>")
      amFirst = False

    # now print the usings
    if len(uses) > 0:
      print("")
      print("<a name=\"usings\"></a>")
      print("## List of defined joins and iterators")
      print("<div>")
      for use in uses:
        print("")
        print("  <button class=\"myaccordion\"><i class=\"fa fa-map-pin\"></i> "+use.name+"</button>")
        print("  <div class=\"panel\">")
        print("    <ul>")
        use.printHTML()
        print("    </ul>")
        print("  </div>")
      print("</div>")

  def printHTheaderHTML(self):
    print("")
    print("<a name=""helper_tasks""></a>")
    print("## List of tables created with helper tasks")
    print("")
    print("The AO2D data files contain the basic set of data which is available for data analysis and from which other quantities are deduced. There are however quantities like PID information, V0 characteristics, etc. which are commonly used in analysis. In order to prevent that tasks to compute such quantities are repeatingly developed, a set of helper tasks is provided by the O2 framework. These tasks are listed below together with the tables they provide.")
    print("")
    print("Click on the labels to display the table details.")

# -----------------------------------------------------------------------------
# functions
#
# .............................................................................
def block(words, withspace=True, space=" "):
  sep = ""
  if withspace == True:
    sep = space
  cont = ""

  if len(words) == 0:
    return cont

  if isinstance(words[0], str):
    for w in words:
      cont += w+sep
  else:
    for w in words:
      cont += w.txt+sep

  return cont

# .............................................................................
def split(block):

  # split into words
  words = nltk.word_tokenize(block)

  return words

# .............................................................................
# content is a tuple<list<word>, list<str>>
# create tuple with (content[0][[i1:i2],[i3:i4]], content[1])
def select(content, i1, i2=-1, i3=-1, i4=-1):
  wsel = list()

  if i2 < 0:
    i2 = len(content[0])
  for w in content[0][i1:i2]:
    wsel.append(w)

  if i3 >= 0:
    if i4 < 0:
      i4 = len(content[0])
    for w in content[0][i3:i4]:
      wsel.append(w)

  return wsel, content[1]

# .............................................................................
# remove text from line between brackets obr..cbr
# obr and cbr are sequences of characters
# return modified line and int stat
# stat is the number of not completed brackets (needs to be >= 0)
def removeInBrackets(obr, cbr, line, stat):
  # find obr
  answ = list(map(lambda x: line[x:x + len(obr)] == obr, range(len(line) - len(obr) + 1)))
  iop = [i for i, x in enumerate(answ) if x == True]

  # find cbr
  answ = list(map(lambda x: line[x:x + len(cbr)] == cbr, range(len(line) - len(cbr) + 1)))
  icl = [i for i, x in enumerate(answ) if x == True]

  # build sequence which holds the number of open brackets
  # at each character of the line
  seq = [stat]*len(line)
  for i1 in iop:
    for i2 in range(i1, len(line)):
      seq[i2] += 1
  for i1 in icl:
    for i2 in range(i1+len(cbr), len(line)):
      seq[i2] -= 1

  # compute the results
  stat = seq[-1]
  if stat < 0:
    sys.exit(obr+' ... '+cbr+' missmatch! EXIT -->')

  # only select characters with seq[]=0
  newline = ""
  for i1 in [i for i, x in enumerate(seq) if x == 0]:
    newline += line[i1]

  return stat, newline

# .............................................................................
def pickContent(lines_in_file):

  # 1. remove the comments // but not the //!
  # 2. consider extensions \
  # 3. remove comment blocks /* ... */
  linesWithoutComments = list()
  lineToAdd = ""
  for line in lines_in_file:

    # 1. remove the comments // but not the //!
    l = line
    i1 = l.find("//")
    while i1 >= 0:
      if l[i1+2] != "!":
        l = l[0:i1].strip()
      i1 = l.find("//", i1+2)
    if l == "":
      continue

    # 2. consider extensions \
    if l.strip().endswith("\\"):
      lineToAdd = lineToAdd+" "+l[:len(l)-2].strip()
    else:
      lineToAdd = lineToAdd+" "+l
      linesWithoutComments.append(lineToAdd)
      lineToAdd = ""

  # 3. remove comment blocks /* ... */
  stat = 0
  for ind in range(len(linesWithoutComments)):
    res = removeInBrackets("/*", "*/", linesWithoutComments[ind], stat)
    stat = res[0]
    linesWithoutComments[ind] = res[1]

  # select all lines starting with #define
  idfs = [l for l, s in enumerate(linesWithoutComments) if s.lstrip().startswith("#define")][::-1]
  for idf in idfs:
    ws = split(linesWithoutComments[idf])
    defstring = linesWithoutComments[idf].split(ws[2], 1)[1]
    df = define(ws[2], defstring)

    # find the corresponding #undef
    iend = len(linesWithoutComments)
    iudfs = [l for l, s in enumerate(linesWithoutComments) if s.lstrip().startswith("#undef")][::-1]
    for iudf in iudfs:
      ws = split(linesWithoutComments[iudf])
      if ws[2] == df.name:
        iend = iudf-1
        break

    # substitute #define within the def-undef block
    for ii in range(idf+1, iend):
      linesWithoutComments[ii] = df.expandLine(linesWithoutComments[ii])

  # create list of word(s)
  words = list()
  for ind in range(len(linesWithoutComments)):
    # for this remove the //! comments
    l2u = linesWithoutComments[ind]
    if l2u.strip() == "":
      continue
    i1 = l2u.find("//!")
    if i1 >= 0:
      l2u = l2u[0:i1].strip()
    for w in split(l2u):
      words.append(word(w, ind))

  content = (words, linesWithoutComments)

  return content

# .............................................................................
# a: list of strings
# b: list of words
# is a contained in b?
def list_in(a, b):

  # create list of strings
  b2u = list()
  for w in b:
    b2u.append(w.txt)

  # compare a and b2u
  return list(map(lambda x: b2u[x:x + len(a)] == a, range(len(b2u) - len(a) + 1)))

# .............................................................................
def fullDataModelName(nslevel, name):
  toks0 = nslevel.split("::")
  toks1 = name.split("::")

  fullName = ""
  for tok in toks0:
    if tok not in toks1:
      if fullName == "":
        fullName = tok
      else:
        fullName += "::"+tok
    else:
      break

  if fullName == "":
    fullName = name
  else:
    fullName += "::"+name

  return fullName

# .............................................................................
# extract the column names from a table declaration
# cont contains the declaration
def tableColumnNames(nslevel, cont, kind=0):

  # specification according to kind of table
  noff = 3
  if kind == 1:
    noff = 4

  # split cont with ","
  buf = block(cont[:len(cont)-2], False)
  toks = buf.split(",")

  # get column definitions, ATTENTION: some contain <>
  colNames = list()
  col = ""
  nop = 0
  ncl = 0
  for tok in toks[noff:]:
    col += tok
    nop += tok.count("<")
    ncl += tok.count(">")

    if (ncl == nop):
      colNames.append(col)
      col = ""
    else:
      col += ","

  # complete namespace
  fullColNames = list()
  toks0 = nslevel.split("::")
  for colName in colNames:
    toks1 = colName.split("::")

    fullColName = ""
    for tok in toks0:
      if tok not in toks1:
        if fullColName == "":
          fullColName = tok
        else:
          fullColName += "::"+tok
      else:
        break

    if fullColName == "":
      fullColName = colName
    else:
      fullColName += "::"+colName

    fullColNames.append(fullColName)

  return fullColNames

# .............................................................................
def extractTables(nslevel, content):
  words = content[0]
  lines = content[1]
  tables = list()

  # table types
  types = tableTypes()

  # find indices of any type of table declarations
  def condition(s):
    res = False
    for x in types:
      res = res or (s.txt == x)
    return res
  inds = [idx for idx, element in enumerate(words) if condition(element)]

  # loop over declarations
  for icol in inds:
    iend = [i for i, x in enumerate(list_in([")", ";"], words[icol:])) if x == True]
    if len(iend) == 0:
      print(nslevel)
      sys.exit('Ending ); not found in table declaration! EXIT -->')
    cont = words[icol:iend[0]+icol+2]

    kind = [i for i, x in enumerate(types) if x == words[icol].txt][0]
    name = fullDataModelName(nslevel, words[icol+2].txt)

    # extract column names
    fullColNames = tableColumnNames(nslevel, cont, kind)

    # kind, namespace, name, cont
    tab = table(kind, nslevel, name, block(cont))
    tab.colNames = fullColNames

    # EXTENDED_TABLE?
    if kind == 2 or kind == 5:
      tab.toExtendWith = fullDataModelName(nslevel, words[icol+4].txt)

    # add a comment if available
    line = lines[words[icol].lnr]
    tab.comment = block(line.split("//!")[1:], True).strip()

    tables.append(tab)

  return tables

# .............................................................................
def extractColumns(nslevel, content):
  words = content[0]
  lines = content[1]

  # helper function to find any table declaration in a list of words
  def condition(s):
    res = False
    for x in types:
      res = res or (s.txt == x)
    return res

  cols = list()

  # column types
  types = columnTypes()

  # find indices of column declarations
  inds = [idx for idx, element in enumerate(words) if condition(element)]

  # loop over declarations
  for icol in inds:
    iend = [i for i, x in enumerate(list_in([")", ";"], words[icol:])) if x == True]
    if len(iend) == 0:
      print(nslevel)
      sys.exit('Ending ); not found in column declaration! EXIT -->')
    cont = words[icol:iend[0]+icol+2]

    kind = [i for i, x in enumerate(types) if x == words[icol].txt][0]
    cname = words[icol+2].txt
    vname = words[icol+4].txt
    if kind == 1 or kind == 2:
      cname = cname+"Id"
      vname = vname+"Id"

    # determine the type of the colums
    type = ""
    if words[icol].txt == types[0]:
      type = words[icol+6].txt
    elif words[icol].txt == types[1]:
      type = words[icol+6].txt
    elif words[icol].txt == types[2]:
      type = "int32"
    elif words[icol].txt == types[3]:
      type = words[icol+6].txt
    elif words[icol].txt == types[4]:
      iarr = [i for i, x in enumerate(list_in(["-", ">"], cont)) if x == True]
      if len(iarr) > 0:
        type = cont[iarr[0]+2].txt
      else:
        type = "?"

    # kind, namespace, name, type, cont
    col = column(kind, nslevel, cname, vname, type, block(cont))
    if kind == 1:
      col.pointsInto = words[icol+8].txt

    # add a comment if available
    line = lines[words[icol].lnr]
    col.comment = block(line.split("//!")[1:], True).strip()

    cols.append(col)

  return cols

# .............................................................................
def extractUsings(nslevel, content):
  words = content[0]
  lines = content[1]
  usings = list()

  # using types
  types = ["using"]

  def condition(s):
    res = False
    for x in types:
      res = res or (s.txt == x)
    return res

  # find indices of "using"
  inds = [idx for idx, element in enumerate(words) if condition(element)]

  # loop over cases
  for icol in inds:
    iend = [i for i, x in enumerate(list_in([";"], words[icol:])) if x == True]
    if len(iend) == 0:
      print(nslevel)
      sys.exit('Ending ; not found in using declaration! EXIT -->')
    cont = words[icol:icol+iend[0]+1]

    name = fullDataModelName(nslevel, words[icol+1].txt)
    definition = block(words[icol+3:icol+iend[0]], False)

    # namespace, name, cont
    use = using(nslevel, name, definition, block(cont))

    usings.append(use)

  return usings

# .............................................................................
# A namespace is contained between "namespace 'name' {" and "}"
# Be aware that namespaces can be nested!
def parseContent(content, nslevel, dm):
  words = content[0]
  lines = content[1]

  # does this block contain a namespace definition?
  isps = [ind for ind, x in enumerate(words) if x.txt == "namespace"]
  if len(isps) > 0:
    p10 = isps[0]
    iop = [ind for ind, x in enumerate(words[p10:]) if x.txt == "{"]
    if len(iop) == 0:
      print("The opening bracket \"{\" is missing!")
      print(block(words[p10:]))
      exit()
    icl = [ind for ind, x in enumerate(words[p10:]) if x.txt == "}"]
    if len(icl) == 0:
      print("The closing bracket \"}\" is missing!")
      print(block(words[p10:]))
      exit()

    # find namespace block within {}
    nind = len(words) - p10
    ind = np.zeros(nind)
    ind[iop] = 1
    ind[icl] = -1
    p11 = np.where(np.cumsum(ind[iop[0]:]) == 0)
    p11 = p10+iop[0]+p11[0][0]

    # analyze the next block with updated nslevel
    b2u = block(words[p10+1:p10+iop[0]], False)
    if nslevel != "":
      nslnew = fullDataModelName(nslevel, b2u)
    else:
      nslnew = b2u

    c2u = select(content, p10+1, p11)
    parseContent(c2u, nslnew, dm)

    # remove words of ns and process rest
    if p10 > 0 & p11 < len(words):
      c2u = select(content, 0, p10, p11+1)
      parseContent(c2u, nslevel, dm)

  else:
    # this block of text is a namespace
    if nslevel == "":
      return True

    # find typedefs and replace affected items
    itds = [ind for ind, x in enumerate(words) if x.txt == "typedef"]
    for itd in itds:
      name1 = words[itd+1].txt
      name2 = words[itd+2].txt
      # replace all name2 with name1
      for ind in range(itd+3, len(words)):
        if words[ind].txt == name2:
          words[ind].txt = name1

    # analyze the block and create a namespace object nsp
    nsp = namespace(nslevel, block(words))

    # extract columns
    cols = extractColumns(nslevel, content)
    for col in cols:
      nsp.addColumn(col)

    # extract tables
    tables = extractTables(nslevel, content)
    for tab in tables:
      tab.producer = dm.producers[0]
      nsp.addTable(tab)

    # extract usings
    usings = extractUsings(nslevel, content)
    for using in usings:
      nsp.addUsing(using)

    # update the datamodel dm
    dm.addNamespace(nsp)

  return True

# -----------------------------------------------------------------------------
class CERelations:
  def __init__(self):
    self.relations = list()

  def addRelations(self, fileName):
    path = block(fileName.split("/")[:-1], True, "/")
    with open(fileName, 'r') as file:
      # read the file
      lines_in_file = file.readlines()
      content = pickContent(lines_in_file)

      # parse CMakeLists file
      # executable - code relations are defined with o2_add_dpl_workflow
      idef = [ind for ind, x in enumerate(content[0]) if x.txt == "o2_add_dpl_workflow"]
      for ind in idef:
        ename = content[0][ind+2].txt
        cname = content[0][ind+4].txt
        if len(cname.split(".")) < 2:
          cname += ".cxx"
        self.relations.append([path, cname, ename])

  def getExecutable(self, codeFile):
    # find the executable corresponding to codeFile
    ice = [ind for ind, x in enumerate(self.relations) if x[0]+x[1] == codeFile]
    exeName = ""
    if len(ice) > 0:
      exeName = self.relations[ice[0]][2]

    return exeName

  def print(self):
    print("CE relations")
    for relation in self.relations:
      print(" path  :", relation[0])
      print("  cname:", relation[1])
      print("  ename:", relation[2])


# -----------------------------------------------------------------------------
