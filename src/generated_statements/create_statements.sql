
USE ADVENTUREWORKS_1907

GO
CREATE VIEW vw_TablesColumnsProperties
AS
SELECT CONCAT(table_schema,'.',table_name) as schema_table_name,table_schema as schema_name,table_name,column_name,data_type,is_nullable,column_default
FROM information_schema.columns


GO
CREATE VIEW vw_getRANDValue
AS
SELECT RAND() AS Value

GO
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE FUNCTION GenerateRandomString()
RETURNS nvarchar(4000)
AS
BEGIN
DECLARE
		@length int,
		@charpool nvarchar(100),
		@poollength int,
		@loopcount int,
		@randomstring nvarchar(4000);

SET @length = 4000
SET @CharPool = 
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,.!?:;-_ '
SET @PoolLength = Len(@CharPool)

SET @LoopCount = 0
SET @RandomString = ''

WHILE (@LoopCount < @Length) BEGIN
    SELECT @RandomString = @RandomString + 
        SUBSTRING(@Charpool, CONVERT(int, (SELECT Value FROM vw_getRANDValue) * @PoolLength), 1)
    SELECT @LoopCount = @LoopCount + 1
END
RETURN @RandomString
END
GO

go
create procedure sp_fillup_RandomPseudonymTableMap @mappingstable nvarchar(100), @tablename nvarchar(100), @columnname nvarchar(100), @randomgenstatement nvarchar(4000)
as
begin
	set nocount on
	exec(
	'insert into '+@mappingstable+'(tablename,columnname,fromvalue,tovalue)
	select distinct '''+@tablename+''', '''+@columnname+''', t.'+@columnname+', '+@randomgenstatement+' as tovalue 
	from (select distinct '+@columnname+' from '+@tablename+') t
	left outer join (select distinct fromvalue, tovalue from '+@mappingstable+' where tablename = '''+@tablename+''' and columnname='''+@columnname+''') dt
	on t.'+@columnname+' = dt.fromvalue
	where dt.tovalue is null'
	)
end

go
create procedure sp_fillup_RandomPseudonymMap @mappingstable nvarchar(100), @tablename nvarchar(100), @columnname nvarchar(100), @randomgenstatement nvarchar(4000)
as
begin
	set nocount on
	exec(
	'insert into '+@mappingstable+'(fromvalue,tovalue)
	select distinct t.'+@columnname+', '+@randomgenstatement+'
	from (select distinct '+@columnname+' from '+@tablename+') t
	left outer join (select distinct fromvalue, tovalue from '+@mappingstable+') dt
	on t.'+@columnname+' = dt.fromvalue
	where dt.tovalue is null'
	)
end


--**RandomPseudonym Anonymization**
GO
CREATE TABLE bit_RandomPseudonymMap( fromvalue bit, tovalue bit);
exec sp_fillup_RandomPseudonymMap 'bit_RandomPseudonymMap', 'HumanResources.Employee', 'SalariedFlag', 'CAST(ROUND(RAND(CHECKSUM(NEWID())),0) AS BIT)'

GO
CREATE TABLE smallint_RandomPseudonymMap( fromvalue smallint, tovalue smallint);
exec sp_fillup_RandomPseudonymMap 'smallint_RandomPseudonymMap', 'HumanResources.Employee', 'SickLeaveHours', 'CAST(FLOOR(RAND(CHECKSUM(NEWID()))*(10000)) as SMALLINT)'

GO
CREATE TABLE datetime_RandomPseudonymMap( fromvalue datetime, tovalue datetime);
exec sp_fillup_RandomPseudonymMap 'datetime_RandomPseudonymMap', 'Sales.SpecialOffer', 'StartDate', 'CAST(CAST(DATEADD(SECOND, ROUND(((DATEDIFF(SECOND, ''2000-01-01 00:00:00'' , ''2020-01-01 00:00:00'')-1) * RAND(CHECKSUM(NEWID()))), 0), ''2000-01-01 00:00:00'') AS datetime) as datetime)'

--**RandomPseudonymPerTable Anonymization**
GO
CREATE TABLE time_7_RandomPseudonymPerTableMap(tablename nvarchar(100),columnname nvarchar(100), fromvalue time(7), tovalue time(7));
exec sp_fillup_RandomPseudonymTableMap 'time_7_RandomPseudonymPerTableMap', 'HumanResources.Shift', 'StartTime', 'CAST(CAST(DATEADD(SECOND, ROUND(((DATEDIFF(SECOND, ''2000-01-01 00:00:00'' , ''2020-01-01 00:00:00'')-1) * RAND(CHECKSUM(NEWID()))), 0), ''2000-01-01 00:00:00'') AS datetime) as time(7))'

GO
CREATE TABLE smallmoney_RandomPseudonymPerTableMap(tablename nvarchar(100),columnname nvarchar(100), fromvalue smallmoney, tovalue smallmoney);
exec sp_fillup_RandomPseudonymTableMap 'smallmoney_RandomPseudonymPerTableMap', 'Sales.SpecialOffer', 'DiscountPct', 'CAST((RAND(CHECKSUM(NEWID()))*(100000)) as smallmoney)'

--**RandomPseudonymFromSet Anonymization**
GO
CREATE TABLE HumanResources_Employee_MaritalStatus_RandomPseudonymFromSetMap( fromvalue nchar(1), tovalue nchar(1));

INSERT INTO HumanResources_Employee_MaritalStatus_RandomPseudonymFromSetMap
SELECT t1.fromvalue,t2.tovalue
FROM
(SELECT t.MaritalStatus AS fromvalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT MaritalStatus FROM HumanResources.Employee) AS t) as t1
INNER JOIN
(SELECT t.MaritalStatus AS tovalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT MaritalStatus FROM HumanResources.Employee) AS t) as t2
ON t1.row_num = t2.row_num
GO
CREATE TABLE HumanResources_Shift_ShiftID_RandomPseudonymFromSetMap( fromvalue tinyint, tovalue tinyint);

INSERT INTO HumanResources_Shift_ShiftID_RandomPseudonymFromSetMap
SELECT t1.fromvalue,t2.tovalue
FROM
(SELECT t.ShiftID AS fromvalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT ShiftID FROM HumanResources.Shift) AS t) as t1
INNER JOIN
(SELECT t.ShiftID AS tovalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT ShiftID FROM HumanResources.Shift) AS t) as t2
ON t1.row_num = t2.row_num
GO
CREATE TABLE Sales_SalesPerson_BusinessEntityID_RandomPseudonymFromSetMap( fromvalue int, tovalue int);

INSERT INTO Sales_SalesPerson_BusinessEntityID_RandomPseudonymFromSetMap
SELECT t1.fromvalue,t2.tovalue
FROM
(SELECT t.BusinessEntityID AS fromvalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT BusinessEntityID FROM Sales.SalesPerson) AS t) as t1
INNER JOIN
(SELECT t.BusinessEntityID AS tovalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT BusinessEntityID FROM Sales.SalesPerson) AS t) as t2
ON t1.row_num = t2.row_num


--HumanResources.Employee
GO
IF EXISTS (SELECT column_default FROM vw_TablesColumnsProperties WHERE schema_table_name='HumanResources.Employee' and column_name='rowguid' and column_default is not NULL)
 AND EXISTS (SELECT column_default FROM vw_TablesColumnsProperties WHERE schema_table_name='HumanResources.Employee' and column_name='ModifiedDate' and column_default is not NULL)
BEGIN
exec('CREATE VIEW vw_HumanResources_Employee_Anonymized
AS
SELECT CAST(FLOOR(RAND(CHECKSUM(NEWID()))*(1000000000)) as INT) as BusinessEntityID, CONVERT(varbinary(5), CAST(FLOOR(RAND(CHECKSUM(NEWID()))*(100000)) as varbinary)) as OrganizationNode, NULL as OrganizationLevel, CAST(CAST(DATEADD(SECOND, ROUND(((DATEDIFF(SECOND, ''2000-01-01 00:00:00'' , ''2020-01-01 00:00:00'')-1) * RAND(CHECKSUM(NEWID()))), 0), ''2000-01-01 00:00:00'') AS datetime) as date) as BirthDate, t1.tovalue as MaritalStatus, t2.tovalue as Gender, t3.tovalue as SalariedFlag, CAST(FLOOR(RAND(CHECKSUM(NEWID()))*(10000)) as SMALLINT) as VacationHours, t4.tovalue as SickLeaveHours, CAST(ROUND(RAND(CHECKSUM(NEWID())),0) AS BIT) as CurrentFlag, 
CAST((SELECT CASE
 WHEN REPLACE(REPLACE(REPLACE(REPLACE(column_default,''()'',''!''),''('',''''),'')'',''''),''!'',''()'') = ''getdate()'' THEN CAST(getdate() as nvarchar(2000))
WHEN REPLACE(REPLACE(REPLACE(REPLACE(column_default,''()'',''!''),''('',''''),'')'',''''),''!'',''()'') = ''newid()'' THEN CAST(newid() as nvarchar(2000))
ELSE REPLACE(REPLACE(REPLACE(REPLACE(column_default,''()'',''!''),''('',''''),'')'',''''),''!'',''()'')
END
as column_default
FROM vw_TablesColumnsProperties WHERE schema_table_name=''HumanResources.Employee'' and column_name=''rowguid'' and column_default is not NULL) as uniqueidentifier)
 as rowguid, 
CAST((SELECT CASE
 WHEN REPLACE(REPLACE(REPLACE(REPLACE(column_default,''()'',''!''),''('',''''),'')'',''''),''!'',''()'') = ''getdate()'' THEN CAST(getdate() as nvarchar(2000))
WHEN REPLACE(REPLACE(REPLACE(REPLACE(column_default,''()'',''!''),''('',''''),'')'',''''),''!'',''()'') = ''newid()'' THEN CAST(newid() as nvarchar(2000))
ELSE REPLACE(REPLACE(REPLACE(REPLACE(column_default,''()'',''!''),''('',''''),'')'',''''),''!'',''()'')
END
as column_default
FROM vw_TablesColumnsProperties WHERE schema_table_name=''HumanResources.Employee'' and column_name=''ModifiedDate'' and column_default is not NULL) as datetime)
 as ModifiedDate
FROM HumanResources.Employee t 
INNER JOIN HumanResources_Employee_MaritalStatus_RandomPseudonymFromSetMap t1 ON t.[MaritalStatus] = t1.fromvalue 
INNER JOIN 
(SELECT a.fromvalue, b.tovalue
FROM
(SELECT x.Gender AS fromvalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT Gender FROM HumanResources.Employee) AS x) as a
INNER JOIN
(SELECT y.Gender AS tovalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT Gender FROM HumanResources.Employee) AS y) as b
ON a.row_num = b.row_num) as t2
ON t.[Gender] = t2.fromvalue 
INNER JOIN bit_RandomPseudonymMap t3 ON t.[SalariedFlag] = t3.fromvalue 
INNER JOIN smallint_RandomPseudonymMap t4 ON t.[SickLeaveHours] = t4.fromvalue
')
END
ELSE
BEGIN print('ERROR WHEN CHECKING DEFAULTS')
END
--HumanResources.Shift

GO
CREATE VIEW vw_HumanResources_Shift_Anonymized
AS
SELECT t1.tovalue as ShiftID, t2.tovalue as Name, t3.tovalue as StartTime, getdate() as EndTime
FROM HumanResources.Shift t 
INNER JOIN HumanResources_Shift_ShiftID_RandomPseudonymFromSetMap t1 ON t.[ShiftID] = t1.fromvalue 
INNER JOIN 
(SELECT a.fromvalue, b.tovalue
FROM
(SELECT x.Name AS fromvalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT Name FROM HumanResources.Shift) AS x) as a
INNER JOIN
(SELECT y.Name AS tovalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT Name FROM HumanResources.Shift) AS y) as b
ON a.row_num = b.row_num) as t2
ON t.[Name] = t2.fromvalue 
INNER JOIN (SELECT * FROM time_7_RandomPseudonymPerTableMap WHERE columnname='StartTime' and tablename='HumanResources.Shift') t3 ON t.[StartTime] = t3.fromvalue 

--Sales.SpecialOffer

GO
CREATE VIEW vw_Sales_SpecialOffer_Anonymized
AS
SELECT CAST(FLOOR(RAND(CHECKSUM(NEWID()))*(1000000000)) as INT) as SpecialOfferID, t1.tovalue as DiscountPct, t2.tovalue as Category, t3.tovalue as StartDate, t4.tovalue as MinQty, NULL as MaxQty
FROM Sales.SpecialOffer t 
INNER JOIN (SELECT * FROM smallmoney_RandomPseudonymPerTableMap WHERE columnname='DiscountPct' and tablename='Sales.SpecialOffer') t1 ON t.[DiscountPct] = t1.fromvalue 
INNER JOIN 
(SELECT a.fromvalue, b.tovalue
FROM
(SELECT x.Category AS fromvalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT Category FROM Sales.SpecialOffer) AS x) as a
INNER JOIN
(SELECT y.Category AS tovalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT Category FROM Sales.SpecialOffer) AS y) as b
ON a.row_num = b.row_num) as t2
ON t.[Category] = t2.fromvalue 
INNER JOIN datetime_RandomPseudonymMap t3 ON t.[StartDate] = t3.fromvalue
INNER JOIN 
(SELECT a.fromvalue, b.tovalue
FROM
(SELECT x.MinQty AS fromvalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT MinQty FROM Sales.SpecialOffer) AS x) as a
INNER JOIN
(SELECT y.MinQty AS tovalue, row_number() over (ORDER BY  NEWID()) AS row_num FROM (SELECT DISTINCT MinQty FROM Sales.SpecialOffer) AS y) as b
ON a.row_num = b.row_num) as t4
ON t.[MinQty] = t4.fromvalue

