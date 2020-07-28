import sys
from sql_functions import *
import zipfile

zeros = '0'*100
droppingstatements = 'USE ADVENTUREWORKS_1907\nGO\nDROP VIEW vw_TablesColumnsProperties\nDROP VIEW vw_getRANDValue\nDROP FUNCTION GenerateRandomString\nDROP PROCEDURE sp_fillup_RandomPseudonymTableMap\nDROP PROCEDURE sp_fillup_RandomPseudonymMap\n'

def generateRandomXChar_statement(datatype):
    if 'char' not in datatype:
        raise Exception(datatype+' is not char type!')
    datatype = datatype.replace('max','4000')
    generatingStatement = 'CAST(dbo.GenerateRandomString() as '+datatype+')'
    return generatingStatement

def generateRandomXBinary_statement(datatype):
    if 'binary' not in datatype:
        raise Exception(datatype+' is not binary type!')
    datatype = datatype.replace('max','8000')
    generatingStatement ='CAST(CRYPT_GEN_RANDOM(8000) as '+datatype+')'
    return generatingStatement

def generateRandomNumeric_or_Decimal_statement(datatype):
    if 'numeric' not in datatype and 'decimal' not in datatype:
        raise Exception(datatype+' is not decimal nor numeric!')
    params = datatype.replace('numeric(','').replace('decimal(','').replace(')','').split(',')
    allowedZeros = zeros[0:int(params[0])-int(params[1])]
    generatingStatement = '(RAND(CHECKSUM(NEWID()))*(1'+allowedZeros+'))'
    casting = 'CAST('+generatingStatement+' as '+datatype+')'
    return casting

def generateRandomDateOrTime_statement(datatype):
    if 'date' not in datatype and 'time' not in datatype:
        raise Exception(datatype+' is not a date or time datatype!')
    generatingStatement = 'CAST(CAST(DATEADD(SECOND, ROUND(((DATEDIFF(SECOND, \'2000-01-01 00:00:00\' , \'2020-01-01 00:00:00\')-1) * RAND(CHECKSUM(NEWID()))), 0), \'2000-01-01 00:00:00\') AS datetime) as '+datatype+')'
    return generatingStatement

def generateRandomMoney_statement(datatype):
    if 'money' not in datatype:
        raise Exception(datatype+' is not decimal nor money type!')
    if 'small' in datatype:
        return 'CAST((RAND(CHECKSUM(NEWID()))*(100000)) as '+datatype+')'
    return 'CAST((RAND(CHECKSUM(NEWID()))*(100000000000)) as '+datatype+')'

def generateRandomBit_statement(datatype):
    if 'bit' not in datatype:
        raise Exception(datatype+' is not bit type!')
    return 'CAST(ROUND(RAND(CHECKSUM(NEWID())),0) AS BIT)'

def generateXInt_statement(datatype):
    if 'int' not in datatype:
        raise Exception(datatype+' is not integer type!')
    if 'tiny' in datatype:
        return 'CAST(FLOOR(RAND(CHECKSUM(NEWID()))*(255)) as TINYINT)'
    if 'small' in datatype:
        return 'CAST(FLOOR(RAND(CHECKSUM(NEWID()))*(10000)) as SMALLINT)'
    if 'big' in datatype:
        return 'CAST(FLOOR(RAND(CHECKSUM(NEWID()))*(1'+zeros[0:13]+')) as BIGINT)'
    return 'CAST(FLOOR(RAND(CHECKSUM(NEWID()))*(1000000000)) as INT)'

def generateRealorFloat_statement(datatype):
    if 'float' not in datatype and 'real' not in datatype:
        raise Exception(datatype+' is not real or float type!')
    if 'real' in datatype:
        return 'CAST((RAND(CHECKSUM(NEWID()))*(1000000000000)) as REAL)'
    return 'CAST((RAND(CHECKSUM(NEWID()))*(1000000000)) as FLOAT)'

def generateUniqueIdentifier():
    return 'cast(newid() as uniqueidentifier)'

def generateHierarchyId():
    return 'CONVERT(varbinary(5), CAST(FLOOR(RAND(CHECKSUM(NEWID()))*(100000)) as varbinary))' 

def getRND_generating_statement_for_datatype(datatype):
    if 'uniqueidentifier' in datatype:
        return generateUniqueIdentifier()
    if 'hierarchyid' in datatype:
        return generateHierarchyId()
    if 'int' in datatype:
        return generateXInt_statement(datatype)
    if 'money' in datatype:
        return generateRandomMoney_statement(datatype)
    if 'numeric' in datatype or 'decimal' in datatype:
        return generateRandomNumeric_or_Decimal_statement(datatype)
    if 'date' in datatype or 'time' in datatype:
        return generateRandomDateOrTime_statement(datatype)
    if 'real' in datatype or 'float' in datatype:
        return generateRealorFloat_statement(datatype)
    if 'char' in datatype:
        return generateRandomXChar_statement(datatype)
    if 'binary' in datatype:
        return generateRandomXBinary_statement(datatype)
    if 'bit' in datatype:
        return generateRandomBit_statement(datatype)
    else:
        raise Exception('getRND_generating_statement_for_datatype failed for datatype: '+datatype)

def getPseudoRandomMappings_creation_statement(datatype):
    dt = datatype.replace('(','_').replace(')','').replace(',','_').replace(' ','')
    global droppingstatements
    droppingstatements += 'DROP TABLE '+dt+'_RandomPseudonymMap\n'
    return 'GO\nCREATE TABLE '+dt+'_RandomPseudonymMap( fromvalue '+datatype+', tovalue '+datatype+');'

def getPseudoRandomMappings_insertinto_statement(datatype,schema_table_column_infos):
    dt = datatype.replace('(','_').replace(')','').replace(',','_').replace(' ','')
    tablename = dt+'_RandomPseudonymMap'
    statement = '\nGO\nINSERT INTO '+tablename+'\nSELECT t.fromvalue, '+getRND_generating_statement_for_datatype(datatype)+' as tovalue\nFROM ('
    sttmnt = ''
    for obj in schema_table_column_infos:
        tablename = obj['tablename']
        columnname = obj['columnname']
        if len(sttmnt) != 0:
            statement+= '\nUNION\n'
        sttmnt = '(SELECT DISTINCT '+columnname+' AS fromvalue FROM '+tablename+')'
        statement+= sttmnt
    statement+=') AS t WHERE t.fromvalue is not NULL\n'
    return statement

def getPseudoRandomMappings_fillup_procedure(datatype,schema_table_column_infos):
    dt = datatype.replace('(','_').replace(')','').replace(',','_').replace(' ','')
    maptablename = dt+'_RandomPseudonymMap'
    execbase = 'exec sp_fillup_RandomPseudonymMap'
    exec_list = ''
    for obj in schema_table_column_infos:
        tablename = obj['tablename']
        columnname = obj['columnname']
        genrandomstatement = getRND_generating_statement_for_datatype(datatype).replace('\'','\'\'')
        exec_list += execbase + ' \''+maptablename+'\', '+ '\''+tablename+'\', '+ '\''+columnname+'\', '+ '\''+genrandomstatement+'\'\n'
    return exec_list

def getPseudoRandomPerTableMappings_creation_statement(datatype):
    dt = datatype.replace('(','_').replace(')','').replace(',','_').replace(' ','')
    global droppingstatements
    droppingstatements += 'DROP TABLE '+dt+'_RandomPseudonymPerTableMap\n'
    return 'GO\nCREATE TABLE '+dt+'_RandomPseudonymPerTableMap(tablename nvarchar(100),columnname nvarchar(100), fromvalue '+datatype+', tovalue '+datatype+');'

def getPseudoRandomPerTableMappings_fillup_procedure(datatype,schema_table_column_infos):
    #print('--getPseudoRandomPerTableMappings_fillup_procedure')
    dt = datatype.replace('(','_').replace(')','').replace(',','_').replace(' ','')
    maptablename = dt+'_RandomPseudonymPerTableMap'
    execbase = 'exec sp_fillup_RandomPseudonymTableMap'
    exec_list = ''
    for obj in schema_table_column_infos:
        tablename = obj['tablename']
        columnname = obj['columnname']
        genrandomstatement = getRND_generating_statement_for_datatype(datatype).replace('\'','\'\'')
        exec_list += execbase + ' \''+maptablename+'\', '+ '\''+tablename+'\', '+ '\''+columnname+'\', '+ '\''+genrandomstatement+'\'\n'
    return exec_list

def getRandomFromSet(tablename,columnname,references_dict):
    #lets check if the column we are supposed to randomfromset is actually a foreign keyl
    tname = tablename
    cname = columnname
    if tablename in references_dict.keys() and columnname in references_dict[tablename].keys():
        tname = references_dict[tablename][columnname]['referenced_table']
        cname = references_dict[tablename][columnname]['referenced_column']
    statement = ''    
    statement +='\n(SELECT a.fromvalue, b.tovalue\nFROM\n'
    statement += '(SELECT x.'+cname+' AS fromvalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT '+cname+' FROM '+tname+') AS x) as a\n'
    statement += 'INNER JOIN\n'
    statement += '(SELECT y.'+cname+' AS tovalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT '+cname+' FROM '+tname+') AS y) as b\n'
    statement += 'ON a.row_num = b.row_num)'
    return statement

def getRandomPseudonymFromSetTableName(tablename,columnname,references_dict):
    map_table_name = tablename.replace('.','_')+'_'+columnname
    schematablename = tablename
    if schematablename in references_dict.keys() and columnname in references_dict[schematablename].keys():
        ref_table = references_dict[schematablename][columnname]['referenced_table']
        ref_col = references_dict[schematablename][columnname]['referenced_column']
        map_table_name = ref_table.replace('.','_')+'_'+ref_col
    return map_table_name+'_RandomPseudonymFromSetMap'

def getPseudoRandomFromSet_creation_statement(tablename,columnname,datatype,references_dict):
    map_table_name = tablename.replace('.','_')+'_'+columnname
    schematablename = tablename
    if schematablename in references_dict.keys() and columnname in references_dict[schematablename].keys():
        ref_table = references_dict[schematablename][columnname]['referenced_table']
        ref_col = references_dict[schematablename][columnname]['referenced_column']
        map_table_name = ref_table.replace('.','_')+'_'+ref_col
    global droppingstatements
    droppingstatements+= 'DROP TABLE '+map_table_name+'_RandomPseudonymFromSetMap\n'
    return 'GO\nCREATE TABLE '+map_table_name+'_RandomPseudonymFromSetMap( fromvalue '+datatype+', tovalue '+datatype+');\n'

def getPseudoRandomFromSet_insertinto_statement(tablename,columnname,datatype,references_dict):
    schematablename = tablename
    if schematablename in references_dict.keys() and columnname in references_dict[schematablename].keys():
        tablename = references_dict[schematablename][columnname]['referenced_table']
        columnname = references_dict[schematablename][columnname]['referenced_column']    
    map_table_name = tablename.replace('.','_')+'_'+columnname
    statement = 'INSERT INTO '+map_table_name+'_RandomPseudonymFromSetMap\n'
    statement +='SELECT t1.fromvalue,t2.tovalue\nFROM\n'
    statement += '(SELECT t.'+columnname+' AS fromvalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT '+columnname+' FROM '+tablename+') AS t) as t1\n'
    statement += 'INNER JOIN\n'
    statement += '(SELECT t.'+columnname+' AS tovalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT '+columnname+' FROM '+tablename+') AS t) as t2\n'
    statement += 'ON t1.row_num = t2.row_num'
    return statement

def get_defaultValueRetrieval_statement(table_name,column_name,datatype):
    statement = '\nCAST((SELECT CASE\n WHEN REPLACE(REPLACE(REPLACE(REPLACE(column_default,\'()\',\'!\'),\'(\',\'\'),\')\',\'\'),\'!\',\'()\') = \'getdate()\' THEN CAST(getdate() as nvarchar(2000))\nWHEN REPLACE(REPLACE(REPLACE(REPLACE(column_default,\'()\',\'!\'),\'(\',\'\'),\')\',\'\'),\'!\',\'()\') = \'newid()\' THEN CAST(newid() as nvarchar(2000))\nELSE REPLACE(REPLACE(REPLACE(REPLACE(column_default,\'()\',\'!\'),\'(\',\'\'),\')\',\'\'),\'!\',\'()\')\nEND\n' 
    statement+= 'as column_default\nFROM vw_TablesColumnsProperties WHERE schema_table_name=\''+table_name+'\' and column_name=\''+column_name+'\' and column_default is not NULL) as '+datatype+')\n'
    return statement#replace("'","''")

def get_defaultValueRetrievalExistence_statement(table_name,column_name):
    return '(SELECT column_default FROM vw_TablesColumnsProperties WHERE schema_table_name=\''+table_name+'\' and column_name=\''+column_name+'\' and column_default is not NULL)'

def get_checkDefaultPresenceWrapper_statement(defaults,selectionstatement):
    statement = 'GO\nIF '
    st=''
    for obj in defaults:
        if len(st) > 0:
            st = ' AND '
        st += 'EXISTS '+get_defaultValueRetrievalExistence_statement(obj['tablename'],obj['columnname'])
        statement+=st+'\n'
    statement +='BEGIN\nexec(\'' + selectionstatement.replace("'","''")+ '\')\nEND\nELSE\nBEGIN print(\'ERROR WHEN CHECKING DEFAULTS\')\nEND'
    return statement

def generate_DDL_DML_statements(tables_props,references_dict,randomPseudonymDatatypes,randomPseudonymPerTable,randomPseudonymFromSetDatatypes):
    #first lets create the 'pseudo' tables for datatypes mappings
    f = open("generated_statements\\create_statements.sql", 'w')
    sys.stdout = f
    print(initFunctionsAndViews)

    print('--**RandomPseudonym Anonymization**')
    for datatype in randomPseudonymDatatypes.keys():
        print(getPseudoRandomMappings_creation_statement(datatype))
        print(getPseudoRandomMappings_fillup_procedure(datatype,randomPseudonymDatatypes[datatype]))
        
    print('--**RandomPseudonymPerTable Anonymization**')
    for datatype in randomPseudonymPerTable.keys():
        print(getPseudoRandomPerTableMappings_creation_statement(datatype))
        print(getPseudoRandomPerTableMappings_fillup_procedure(datatype,randomPseudonymPerTable[datatype]))

    print('--**RandomPseudonymFromSet Anonymization**')
    for obj in randomPseudonymFromSetDatatypes:
        tablename=obj['tablename']
        columnname=obj['columnname']
        datatype=obj['datatype']
        print(getPseudoRandomFromSet_creation_statement(tablename,columnname,datatype,references_dict))
        print(getPseudoRandomFromSet_insertinto_statement(tablename,columnname,datatype,references_dict))
    
    print('\n')
    for schema_table_name in tables_props.keys():
        obj = tables_props[schema_table_name]
        tablename = obj['tablename']
        columns = obj['columns']
        columnsnames = []
        colanonTypes = []
        coldatatypes = []
        coldefvals = []
        defvalueheader = []
        for colname in columns.keys():
            if columns[colname]['anonymization'] != 'Omit':
                columnsnames.append(colname)
                colanonTypes.append(columns[colname]['anonymization'])
                coldatatypes.append(columns[colname]['datatype'])
                coldefvals.append(columns[colname]['defaultvalue'])
                if columns[colname]['anonymization'] == 'Default value' and len(columns[colname]['defaultvalue']) == 0:
                    defvalueheader.append({'tablename':tablename,'columnname':colname,'datatype':datatype})
        
        #if all were omitted
        if len(columnsnames) == 0:
            continue
        print('--'+tablename)

        #first create anonymization view
        createviewstatement = 'CREATE VIEW vw_'+tablename.replace('.','_')+'_Anonymized\nAS\nSELECT '
        global droppingstatements
        droppingstatements+='DROP VIEW vw_'+tablename.replace('.','_')+'_Anonymized\n'
        variablessleected = ''
        fromstatement='FROM '+tablename+' t'
        joincnt = 1
        for (colname,colanonType,coldatatype,coldefval) in zip(columnsnames,colanonTypes,coldatatypes,coldefvals):
            if variablessleected != '':
                variablessleected+=', '
            if colanonType == 'None':
                variablessleected+= 't.['+colname+']'
            if colanonType == 'Default value':
                if len(coldefval) != 0:
                    variablessleected+=coldefval+' as '+colname
                else:
                    variablessleected+=get_defaultValueRetrieval_statement(tablename,colname,coldatatype)+' as '+colname
            if colanonType == 'Set Null':
                variablessleected+='NULL as '+colname
            if colanonType == 'Random':
                variablessleected+=getRND_generating_statement_for_datatype(coldatatype)+' as '+colname
            
            if colanonType == 'RandomFromSet':
                fromstatement +='\nINNER JOIN '+getRandomFromSet(tablename,colname,references_dict)+' as t'+str(joincnt)
                fromstatement += '\nON t.['+colname+'] = t'+str(joincnt)+'.fromvalue'
                variablessleected+='t'+str(joincnt)+'.tovalue as '+colname
                joincnt += 1
            
            if colanonType == 'RandomPseudonym':
                dt = coldatatype.replace('(','_').replace(')','').replace(',','_').replace(' ','')
                mappingsTableName = dt+'_RandomPseudonymMap'
                fromstatement += ' \nINNER JOIN '+mappingsTableName+' t'+str(joincnt)+' ON t.['+colname+'] = t'+str(joincnt)+'.fromvalue'
                variablessleected+= 't'+str(joincnt)+'.tovalue as '+colname
                joincnt +=1
            
            if colanonType == 'RandomPseudonymPerTable':
                dt = coldatatype.replace('(','_').replace(')','').replace(',','_').replace(' ','')
                mappingsTableName = dt+'_RandomPseudonymPerTableMap'
                fromstatement += ' \nINNER JOIN (SELECT * FROM '+mappingsTableName+' WHERE columnname=\''+colname+'\' and tablename=\''+tablename+'\') t'+str(joincnt)+' ON t.['+colname+'] = t'+str(joincnt)+'.fromvalue '
                variablessleected+= 't'+str(joincnt)+'.tovalue as '+colname
                joincnt +=1
            
            if colanonType == 'RandomPseudonymFromSet':
                mappingsTableName = getRandomPseudonymFromSetTableName(tablename,colname,references_dict)
                fromstatement += ' \nINNER JOIN '+mappingsTableName+' t'+str(joincnt)+' ON t.['+colname+'] = t'+str(joincnt)+'.fromvalue '
                variablessleected+= 't'+str(joincnt)+'.tovalue as '+colname
                joincnt +=1

        composed_statement = createviewstatement+variablessleected+'\n'+fromstatement+'\n'
        if len(defvalueheader) != 0:
            print(get_checkDefaultPresenceWrapper_statement(defvalueheader,composed_statement))
        else:
            print('\nGO\n'+composed_statement)
    f.close()
    f = open("generated_statements\\drop_statements.sql", 'w')
    sys.stdout = f
    print(droppingstatements)
    f.close()
