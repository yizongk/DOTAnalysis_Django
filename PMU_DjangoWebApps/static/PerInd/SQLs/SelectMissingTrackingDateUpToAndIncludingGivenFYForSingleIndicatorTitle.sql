DECLARE @FiscalYear INT, @IndicatorTitle [nvarchar](255)
SET @FiscalYear = NULL  -- Set to this 2021 to show missing tracking date up to fiscal year 2021
SET @IndicatorTitle = NULL -- Set to to the indicator that you want to check, like '% Deck Area in Good Repair (reported annually in June cell)'


SELECT
    CurrentIndicatorData.Record_ID
    ,CurrentIndicatorData.Indicator_ID
    ,CurrentIndicatorData.Year_Month_ID
    ,CurrentIndicatorData.Indicator_Title
    ,CurrentIndicatorData.Category_Name
    ,Year_Month.Year_Month_ID
    ,Year_Month.YYYY
	,Year_Month.MM
	,Year_Month.Fiscal_Year
FROM Year_Month
LEFT JOIN
(
    SELECT Indicator_Data.Record_ID
        ,Indicator_Data.Indicator_ID
        ,Indicator_Data.Year_Month_ID
        ,Indicator_List.Indicator_Title
        ,Category.Category_Name

    FROM Indicator_Data
    LEFT JOIN Indicator_List
    ON Indicator_Data.Indicator_ID = Indicator_List.Indicator_ID
    LEFT JOIN Category
    ON Indicator_List.Category_ID = Category.Category_ID

    WHERE Indicator_Title = @IndicatorTitle
) AS CurrentIndicatorData
ON CurrentIndicatorData.Year_Month_ID = Year_Month.Year_Month_ID
WHERE
    CurrentIndicatorData.Record_ID IS NULL
    AND Year_Month.Fiscal_Year <= @FiscalYear
ORDER BY
    Year_Month.YYYY
    ,Year_Month.MM