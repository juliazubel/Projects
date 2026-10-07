// Query name: Budget      Group: 05 Facts
// Finance budget: one sheet per year, months as columns, Polish labels, values in thousands of PLN.
// Grain after transformation: Month x Country x Category.
let
    Source         = Excel.Workbook(File.Contents(pDataFolder & "budget.xlsx"), null, true),
    // every sheet called "Budget YYYY" – next year's sheet is picked up automatically
    BudgetSheets   = Table.SelectRows(Source, each [Kind] = "Sheet" and Text.StartsWith([Name], "Budget ")),
    WithYear       = Table.AddColumn(BudgetSheets, "Year", each Number.FromText(Text.AfterDelimiter([Name], " ")), Int64.Type),
    Cleaned        = Table.AddColumn(WithYear, "Rows", each fnCleanBudgetSheet([Data])),
    KeepCols       = Table.SelectColumns(Cleaned, {"Year", "Rows"}),
    Expanded       = Table.ExpandTableColumn(KeepCols, "Rows", {"Kraj", "Kategoria", "Miesiac", "BudgetKPLN"}),
    MonthNames     = {"Sty", "Lut", "Mar", "Kwi", "Maj", "Cze", "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"},
    MonthNumber    = Table.AddColumn(Expanded, "MonthNumber", each List.PositionOf(MonthNames, [Miesiac]) + 1, Int64.Type),
    MonthStart     = Table.AddColumn(MonthNumber, "MonthStart", each #date([Year], [MonthNumber], 1), type date),
    YearMonthKey   = Table.AddColumn(MonthStart, "YearMonthKey", each [Year] * 100 + [MonthNumber], Int64.Type),
    CountryEN      = Table.AddColumn(
                         YearMonthKey, "Country",
                         each Record.FieldOrDefault([Polska = "Poland", Czechy = "Czechia", Niemcy = "Germany"], [Kraj], "Unknown"),
                         type text
                     ),
    MergeCategory  = Table.NestedJoin(CountryEN, {"Kategoria"}, stg_CategoryMapping, {"Kategoria PL"}, "Map", JoinKind.LeftOuter),
    ExpandCategory = Table.ExpandTableColumn(MergeCategory, "Map", {"Category"}),
    // thousands of PLN -> PLN
    BudgetPLN      = Table.AddColumn(ExpandCategory, "BudgetPLN", each Number.From([BudgetKPLN]) * 1000, Currency.Type),
    Final          = Table.SelectColumns(BudgetPLN, {"MonthStart", "YearMonthKey", "Country", "Category", "BudgetPLN"}),
    Typed          = Table.TransformColumnTypes(Final, {{"Category", type text}})
in
    Typed
