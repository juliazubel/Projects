// Query name: stg_FxRates      Group: 03 Staging      (Enable load = OFF)
// Monthly average NBP rates (PLN per 1 unit of currency). File is in POLISH locale:
// semicolon delimiter, decimal comma, wide layout (one column per currency).
let
    Source     = Csv.Document(
                     File.Contents(pDataFolder & "fx_rates_nbp.csv"),
                     [Delimiter = ";", Encoding = 65001, QuoteStyle = QuoteStyle.None]
                 ),
    Promoted   = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // wide -> long: kurs_EUR, kurs_CZK become rows
    Unpivoted  = Table.UnpivotOtherColumns(Promoted, {"miesiac"}, "Column", "Rate"),
    Currency   = Table.AddColumn(Unpivoted, "Currency", each Text.Upper(Text.AfterDelimiter([Column], "_")), type text),
    MonthStart = Table.AddColumn(Currency, "MonthStart", each Date.FromText([miesiac] & "-01"), type date),
    // "4,7089" -> 4.7089 : parse using the pl-PL culture
    RateTyped  = Table.TransformColumnTypes(MonthStart, {{"Rate", type number}}, "pl-PL"),
    Foreign    = Table.SelectColumns(RateTyped, {"MonthStart", "Currency", "Rate"}),
    // PLN -> PLN = 1, so every sales line finds its rate in the merge
    PlnRows    = Table.FromRecords(
                     List.Transform(
                         List.Distinct(Foreign[MonthStart]),
                         each [MonthStart = _, Currency = "PLN", Rate = 1]
                     ),
                     type table [MonthStart = date, Currency = text, Rate = number]
                 ),
    Combined   = Table.Combine({Foreign, PlnRows}),
    Renamed    = Table.RenameColumns(Combined, {{"Rate", "RateToPLN"}})
in
    Renamed
