import re
import pandas as pd
import numpy as np
import zipfile
import os
import sys

tables_columns_properties_file = ""
tables_references_file = ""
anonymization_types = ['None','Omit','Default value','Set Null','Random','RandomPseudonym','RandomPseudonymPerTable','RandomFromSet','RandomPseudonymFromSet']

delimiter = '\t' #delimiter is tab because comma caused confusion when things like "decimal(8,2)" appeared
extension = '.txt'

#input files can be forwarded as command line arguments in the following order: TABLE_PROPERTIES, TABLE_REFERENCES
if(len(sys.argv) == 2):
    tables_columns_properties_file = sys.argv[0] 
    tables_references_file = sys.argv[1]

#if input files aren't forwarded as command line args, they should be read from the input folder
else: #set default paths
    tables_columns_properties_file = "input\\input_properties"+extension
    tables_references_file = "input\\input_references"+extension

#A function which reads and parses the 'references' file. The data is parsed as a dictionary where keys are table names and the values are objects of format {referencing_column: {referenced_table: ..., referenced_column: ...} }
def read_references_file():
    reference_vectors = []
    references_dict = {}
    with open(tables_references_file) as fp:
        headers=fp.readline().strip('\n').split(delimiter)
        line=fp.readline()
        while line:
            parts=line.strip('\n').split(delimiter)
            if len(parts) != len(headers):
                raise Exception('References file not configured properly')
            reference_vectors.append(parts)
            referencing_table = parts[0]
            referencing_column = parts[1]
            referenced_table = parts[2]
            referenced_column = parts[3]

            if referencing_table not in references_dict:
                references_dict[referencing_table]={}
            if referencing_column not in references_dict[referencing_table].keys():
                references_dict[referencing_table][referencing_column]={}
            references_dict[referencing_table][referencing_column]['referenced_table']=referenced_table
            references_dict[referencing_table][referencing_column]['referenced_column']=referenced_column
            line=fp.readline()
    return reference_vectors,references_dict

#A function for reading and parsing the file where table properties are stated. The properties are: table name, column name, data type, nullable, anonymization type, default value
def read_anonymization_file():
    TABLES = {}
    randomPseudonymDatatypes = {}
    randomPseudonymFromSetDatatypes = []
    randomPseudonymPerTable = {}
    with open(tables_columns_properties_file) as fp:
        headers = fp.readline().split(delimiter)
        line = fp.readline()
        table = {}
        while line:
            parts = line.rstrip('\n').split(delimiter)
            if len(parts) != len(headers):
                raise Exception(str(len(parts))+' inputs received for '+str(len(headers))+' headers!')
            tablename=parts[0]
            columnname=parts[1]
            datatype=parts[2].replace('"','')
            nullable=parts[3]
            anonymization = parts[4]

            #check if anonymization type valid
            if anonymization not in anonymization_types:
                raise Exception('An unknown anonymization type ['+anonymization+'] was encountered.')

            #see if table shift
            #if dctionary is not empty
            if bool(table) and table['tablename'] != tablename:
                TABLES[table['tablename']] = table
                table={}
                
            #if dctionary is empty
            if not bool(table):
                table['tablename']=tablename
                table['columns']={}
            table['columns'][columnname]={}
            table['columns'][columnname]['columnname']= columnname
            table['columns'][columnname]['datatype']= datatype
            table['columns'][columnname]['nullable']= nullable
            table['columns'][columnname]['anonymization']= anonymization
            table['columns'][columnname]['defaultvalue']= parts[5]

            if 'NULL' in parts[5] and 'NO' in nullable:
                raise Exception('The column '+columnname+' for which you tried to set Default value NULL is NOT NULLABLE')
            if anonymization not in anonymization_types:
                raise Exception('Encountered unknown anonymisation type ['+anonymization+']. Acceptable types are :'+str(anonymization_types))
            if anonymization == 'Set Null' and 'NO' in nullable:
                raise Exception('Anonymization type "Set null" cant be set for the column ['+columnname+'] because it is NOT NULL.')
            if anonymization == 'RandomPseudonym':
                if datatype not in randomPseudonymDatatypes.keys():
                    randomPseudonymDatatypes[datatype]=[]
                randomPseudonymDatatypes[datatype].append({'tablename':tablename,'columnname':columnname})
            if anonymization == 'RandomPseudonymPerTable':
                if datatype not in randomPseudonymPerTable.keys():
                    randomPseudonymPerTable[datatype]=[]
                randomPseudonymPerTable[datatype].append({'tablename':tablename,'columnname':columnname})
            if anonymization == 'RandomPseudonymFromSet':
                randomPseudonymFromSetDatatypes.append({'tablename':tablename,'columnname':columnname,'datatype':datatype})
            line = fp.readline()
    return (TABLES,randomPseudonymDatatypes,randomPseudonymPerTable,randomPseudonymFromSetDatatypes)

references,references_dict = read_references_file()

tables,randomPseudonymDatatypes_dict,randomPseudonymPerTable_dict,randomPseudonymFromSetDatatypes_list = read_anonymization_file()

from random_generators import *
generate_DDL_DML_statements(tables,references_dict,randomPseudonymDatatypes_dict,randomPseudonymPerTable_dict,randomPseudonymFromSetDatatypes_list)

    
