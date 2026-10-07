// OPTIONAL / BONUS – Query name: fnGetNbpRates      Group: 02 Functions
// Downloads NBP table A mid rates from the public API (https://api.nbp.pl) instead of the CSV file.
// The API returns max. 93 days per request, so the date range is split into 90-day chunks.
// Web.Contents uses a STATIC base URL + RelativePath/Query, which keeps the query refreshable
// in the Power BI Service (dynamic URLs block scheduled refresh).
(currency as text, startDate as date, endDate as date) as table =>
let
    ChunkStarts = List.Generate(() => startDate, each _ <= endDate, each Date.AddDays(_, 90)),
    GetChunk    = (chunkStart as date) as table =>
        let
            chunkEnd = List.Min({Date.AddDays(chunkStart, 89), endDate}),
            Response = Json.Document(
                           Web.Contents(
                               "https://api.nbp.pl/api/exchangerates/rates/a/",
                               [
                                   RelativePath = Text.Lower(currency) & "/"
                                                  & Date.ToText(chunkStart, "yyyy-MM-dd") & "/"
                                                  & Date.ToText(chunkEnd, "yyyy-MM-dd") & "/",
                                   Query        = [format = "json"]
                               ]
                           )
                       ),
            Rates    = Table.FromRecords(Response[rates])
        in
            Table.SelectColumns(Rates, {"effectiveDate", "mid"}),
    Combined    = Table.Combine(List.Transform(ChunkStarts, GetChunk)),
    Typed       = Table.TransformColumnTypes(Combined, {{"effectiveDate", type date}, {"mid", type number}}, "en-US"),
    WithCurrency = Table.AddColumn(Typed, "Currency", each Text.Upper(currency), type text)
in
    WithCurrency

/* Usage – query stg_FxRates_API (replacement for stg_FxRates):

let
    StartDate  = #date(2023, 1, 1),
    EndDate    = Date.From(DateTime.LocalNow()),
    Daily      = Table.Combine({ fnGetNbpRates("EUR", StartDate, EndDate), fnGetNbpRates("CZK", StartDate, EndDate) }),
    WithMonth  = Table.AddColumn(Daily, "MonthStart", each Date.StartOfMonth([effectiveDate]), type date),
    Monthly    = Table.Group(WithMonth, {"MonthStart", "Currency"}, {{"RateToPLN", each List.Average([mid]), type number}}),
    PlnRows    = Table.FromRecords(
                     List.Transform(List.Distinct(Monthly[MonthStart]), each [MonthStart = _, Currency = "PLN", RateToPLN = 1]),
                     type table [MonthStart = date, Currency = text, RateToPLN = number]),
    Result     = Table.Combine({Monthly, PlnRows})
in
    Result
*/
