// Query name: Date      Group: 04 Dimensions
// Calendar built in Power Query. The year range is derived from the FILE NAMES
// (sales_YYYY_MM.csv), so the fact data does not have to be read to build the calendar.
let
    SalesFiles   = Table.SelectRows(Folder.Files(pDataFolder & "sales"), each Text.StartsWith(Text.Lower([Name]), "sales_")),
    Years        = List.Transform(SalesFiles[Name], each Number.FromText(Text.Middle(_, 6, 4))),
    StartDate    = #date(List.Min(Years), 1, 1),
    EndDate      = #date(List.Max(Years), 12, 31),
    DateList     = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1, 0, 0, 0)),
    Base         = Table.FromList(DateList, Splitter.SplitByNothing(), type table [Date = date]),
    Year         = Table.AddColumn(Base, "Year", each Date.Year([Date]), Int64.Type),
    QuarterNo    = Table.AddColumn(Year, "Quarter Number", each Date.QuarterOfYear([Date]), Int64.Type),
    Quarter      = Table.AddColumn(QuarterNo, "Quarter", each "Q" & Text.From([Quarter Number]), type text),
    YearQuarter  = Table.AddColumn(Quarter, "Year Quarter", each Text.From([Year]) & " " & [Quarter], type text),
    MonthNo      = Table.AddColumn(YearQuarter, "Month Number", each Date.Month([Date]), Int64.Type),
    MonthName    = Table.AddColumn(MonthNo, "Month Name", each Date.MonthName([Date], "en-US"), type text),
    MonthShort   = Table.AddColumn(MonthName, "Month Short", each Text.Start([Month Name], 3), type text),
    YearMonth    = Table.AddColumn(MonthShort, "Year Month", each [Month Short] & " " & Text.From([Year]), type text),
    YearMonthKey = Table.AddColumn(YearMonth, "Year Month Key", each [Year] * 100 + [Month Number], Int64.Type),
    MonthStart   = Table.AddColumn(YearMonthKey, "Month Start", each Date.StartOfMonth([Date]), type date),
    // ISO 8601 week: the week belongs to the year in which its Thursday falls
    IsoThursday  = Table.AddColumn(MonthStart, "IsoThursday", each Date.AddDays([Date], 3 - Date.DayOfWeek([Date], Day.Monday)), type date),
    IsoYear      = Table.AddColumn(IsoThursday, "ISO Year", each Date.Year([IsoThursday]), Int64.Type),
    IsoWeek      = Table.AddColumn(IsoYear, "ISO Week", each Number.RoundDown((Date.DayOfYear([IsoThursday]) - 1) / 7) + 1, Int64.Type),
    YearWeek     = Table.AddColumn(IsoWeek, "Year Week", each Text.From([ISO Year]) & "-W" & Text.PadStart(Text.From([ISO Week]), 2, "0"), type text),
    YearWeekKey  = Table.AddColumn(YearWeek, "Year Week Key", each [ISO Year] * 100 + [ISO Week], Int64.Type),
    DayOfWeekNo  = Table.AddColumn(YearWeekKey, "Day of Week Number", each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type),
    DayName      = Table.AddColumn(DayOfWeekNo, "Day Name", each Date.DayOfWeekName([Date], "en-US"), type text),
    IsWeekend    = Table.AddColumn(DayName, "Is Weekend", each [Day of Week Number] >= 6, type logical),
    Final        = Table.RemoveColumns(IsWeekend, {"IsoThursday"})
in
    Final
