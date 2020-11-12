
-- Inserting into Indicator_Data
BEGIN
    BEGIN TRANSACTION
    DECLARE @FiscalYear int, @TempErrorMsg nvarchar(4000)

    -- Set fiscal year that you want to check up to and including here...
    SET @FiscalYear = NULL
    PRINT( 'Checking Tracking Dates up to and including Fiscal Year: ' + ISNULL( CAST( @FiscalYear AS nvarchar ), 'NULL' ) )

    -- Grab the list of Indicators
    DECLARE @Range_IndicatorTitleList TABLE( idx int IDENTITY(1,1), [data] nvarchar(255) )
    BEGIN TRY
        INSERT INTO
            @Range_IndicatorTitleList ([data])
        SELECT
            Indicator_Title
        FROM
            Indicator_List
    END TRY
    BEGIN CATCH
        PRINT( 'Creating @Range_IndicatorTitleList for containing all Indicator_Title failed' )
        IF @@TRANCOUNT > 0
        BEGIN;
            PRINT('Rolling back Transaction')
            ROLLBACK TRANSACTION
        END;
        THROW;
    END CATCH

    -- SELECT * FROM @Range_IndicatorTitleList

    DECLARE @StartCount_IndicatorTitleList int, @TotalCount_IndicatorTitleList int, @Cur_IndicatorTitle nvarchar(255), @Cur_Indicator_ID int, @Cur_User_ID int;
    SELECT @StartCount_IndicatorTitleList = MIN(idx) FROM @Range_IndicatorTitleList;
    SELECT @TotalCount_IndicatorTitleList = MAX(idx) FROM @Range_IndicatorTitleList;
    SET @Cur_IndicatorTitle = NULL;
    SET @Cur_Indicator_ID = NULL;
    SET @Cur_User_ID = NULL;

    -- Go through each Indicator Title and find the missing Tracking date up to given @FiscalYear, and then do the insert into Indicator_Data for each missing tracking date
    BEGIN TRY
        -- Go through each Indicator Title
        WHILE (@StartCount_IndicatorTitleList <= @TotalCount_IndicatorTitleList)
        BEGIN
            SELECT @Cur_IndicatorTitle = [data] FROM @Range_IndicatorTitleList WHERE idx = @StartCount_IndicatorTitleList
            SELECT @Cur_Indicator_ID = [Indicator_ID] FROM Indicator_List WHERE Indicator_Title = @Cur_IndicatorTitle
            SELECT @Cur_User_ID = [User_ID] FROM Users WHERE [Login] = 'Unknown'


            -- For each Indicator Title, find the missing tracking date up to and including given fiscal year
            DECLARE @Range_MissingTrackingDates TABLE( idx int IDENTITY(1,1), Record_ID int, Year_Month_ID int, YYYY int, MM int, Fiscal_Year int )
            BEGIN TRY
                -- Clear any old data from another loop. Apparently the scoping of table variable didn't want to work here.. or maybe the scope of the table variable last for the entirety of the script batch (A batch finishes on the GO statement or the entire script length).
                DELETE FROM @Range_MissingTrackingDates
                INSERT INTO
                    @Range_MissingTrackingDates (
                        Record_ID,
                        Year_Month_ID,
                        YYYY,
                        MM,
                        Fiscal_Year
                    )
                SELECT
                    CurrentIndicatorData.Record_ID
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

                    WHERE Indicator_Title = @Cur_IndicatorTitle
                ) AS CurrentIndicatorData
                ON CurrentIndicatorData.Year_Month_ID = Year_Month.Year_Month_ID
                WHERE
                    CurrentIndicatorData.Record_ID IS NULL
                    AND Year_Month.Fiscal_Year <= @FiscalYear
                ORDER BY
                    Year_Month.YYYY
                    ,Year_Month.MM
            END TRY
            BEGIN CATCH
                PRINT( 'Creating @Range_MissingTrackingDates for checking missing tracking date for each Indicator_Title failed' )
                IF @@TRANCOUNT > 0
                BEGIN;
                    PRINT('Rolling back Transaction')
                    ROLLBACK TRANSACTION
                END;
                THROW;
            END CATCH

            DECLARE @StartCount_MissingTrackingDate int, @TotalCount_MissingTrackingDate int, @Cur_MissingTrackingDate_YearMonthID int;
            SELECT @StartCount_MissingTrackingDate = MIN(idx) FROM @Range_MissingTrackingDates;
            SELECT @TotalCount_MissingTrackingDate = MAX(idx) FROM @Range_MissingTrackingDates;
            SET @Cur_MissingTrackingDate_YearMonthID = NULL;
            BEGIN TRY
                -- Go through each tracking date
                WHILE (@StartCount_MissingTrackingDate <= @TotalCount_MissingTrackingDate)
                BEGIN
                    SELECT @Cur_MissingTrackingDate_YearMonthID = [Year_Month_ID] FROM @Range_MissingTrackingDates WHERE idx = @StartCount_MissingTrackingDate
                    IF @Cur_MissingTrackingDate_YearMonthID IS NULL
                    BEGIN
                        SET @TempErrorMsg = '@Cur_MissingTrackingDate_YearMonthID is null while going through @Range_MissingTrackingDates for PK idx: ' + CAST(@StartCount_MissingTrackingDate AS nvarchar);
                        THROW
                            50000,  -- Error Number
                            @TempErrorMsg, -- Message Text
                            1;   -- State
                    END
                    PRINT('For Indicator Title: "' + @Cur_IndicatorTitle + '"' + ' Indicator_ID: ' + CAST(@Cur_Indicator_ID AS nvarchar) + ' User_ID: ' + CAST(@Cur_User_ID AS nvarchar) + ': Inserting Year_Month_ID: ' + ISNULL( CAST(@Cur_MissingTrackingDate_YearMonthID as nvarchar), 'NULL'))

                    INSERT INTO Indicator_Data (
                        Indicator_ID
                        ,Year_Month_ID
                        ,Val
                        ,Created_Date
                        ,Updated_Date
                        ,Update_User_ID
                    ) VALUES (
                        @Cur_Indicator_ID
                        ,@Cur_MissingTrackingDate_YearMonthID
                        ,0
                        ,GETDATE()
                        ,GETDATE()
                        ,@Cur_User_ID
                    )

                    SET @StartCount_MissingTrackingDate = @StartCount_MissingTrackingDate + 1
                END
            END TRY
            BEGIN CATCH
                PRINT( 'Iterating failed, @@TRANCOUNT: ' + CAST(@@TRANCOUNT AS nvarchar));
                IF @@TRANCOUNT > 0
                BEGIN;
                    PRINT('Rolling back Transaction')
                    ROLLBACK TRANSACTION
                END;
                THROW;
            END CATCH

            PRINT('*****************************New Indicator Title Check******************************')
            SET @StartCount_IndicatorTitleList = @StartCount_IndicatorTitleList + 1
        END
    END TRY
    BEGIN CATCH
        PRINT( 'Iterating failed, @@TRANCOUNT: ' + CAST(@@TRANCOUNT AS nvarchar));
        IF @@TRANCOUNT > 0
        BEGIN;
            PRINT('Rolling back Transaction')
            ROLLBACK TRANSACTION
        END;
        THROW;
    END CATCH
    PRINT('Successfully Insert all Tracking Date up to and including Fiscal Year ' + CAST(@FiscalYear AS nvarchar) + ' into Indicator_Data with this many @@TRANCOUNT: ' + CAST(@@TRANCOUNT AS nvarchar))
    COMMIT TRANSACTION;
END