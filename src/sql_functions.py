initFunctionsAndViews = '''
USE ADVENTUREWORKS_1907\n
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
	select distinct \'\'\'+@tablename+\'\'\', \'\'\'+@columnname+\'\'\', t.\'+@columnname+\', \'+@randomgenstatement+\' as tovalue 
	from (select distinct '+@columnname+' from '+@tablename+') t
	left outer join (select distinct fromvalue, tovalue from '+@mappingstable+' where tablename = \'\'\'+@tablename+\'\'\' and columnname=\'\'\'+@columnname+\'\'\') dt
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
	select distinct t.\'+@columnname+\', \'+@randomgenstatement+\'
	from (select distinct '+@columnname+' from '+@tablename+') t
	left outer join (select distinct fromvalue, tovalue from '+@mappingstable+') dt
	on t.'+@columnname+' = dt.fromvalue
	where dt.tovalue is null'
	)
end
\n'''
