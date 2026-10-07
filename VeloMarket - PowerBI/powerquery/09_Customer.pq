// Query name: Customer      Group: 04 Dimensions
// CRM export: history rows (same CustomerID several times), inconsistent country names,
// random city casing, empty gender / birth year.
let
    Source            = Csv.Document(File.Contents(pDataFolder & "customers.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted          = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed             = Table.TransformColumnTypes(
                            Promoted,
                            {
                                {"CustomerID", type text}, {"Gender", type text}, {"BirthYear", Int64.Type},
                                {"City", type text}, {"Country", type text}, {"Segment", type text},
                                {"SignupDate", type date}, {"MarketingConsent", type text}, {"UpdatedAt", type datetime}
                            },
                            "en-US"
                        ),
    // keep only the LATEST version of every customer.
    // Table.Buffer makes Table.Distinct respect the sort order (without it the result is not guaranteed).
    SortedLatestFirst = Table.Buffer(Table.Sort(Typed, {{"UpdatedAt", Order.Descending}})),
    Latest            = Table.Distinct(SortedLatestFirst, {"CustomerID"}),
    // one mapping record instead of ten "Replace values" steps
    CountryMap        = [
                            POLAND = "Poland", PL = "Poland", POLSKA = "Poland",
                            CZECHIA = "Czechia", #"CZECH REPUBLIC" = "Czechia", #"CZECH REP." = "Czechia", CZ = "Czechia",
                            GERMANY = "Germany", DE = "Germany", DEUTSCHLAND = "Germany"
                        ],
    CleanCountry      = Table.TransformColumns(
                            Latest,
                            {{"Country", each Record.FieldOrDefault(CountryMap, Text.Upper(Text.Trim(_ ?? "")), "Unknown"), type text}}
                        ),
    CleanCity         = Table.TransformColumns(CleanCountry, {{"City", each Text.Proper(Text.Trim(_ ?? "")), type text}}),
    CleanGender       = Table.TransformColumns(
                            CleanCity,
                            {{"Gender", each if _ = "M" then "Male" else if _ = "F" then "Female" else "Not specified", type text}}
                        ),
    Consent           = Table.TransformColumns(CleanGender, {{"MarketingConsent", each _ = "Y", type logical}}),
    ReferenceYear     = Date.Year(DateTime.LocalNow()),
    AgeBands          = {"18–24", "25–34", "35–44", "45–54", "55–64", "65+", "Unknown"},
    AgeBand           = Table.AddColumn(Consent, "Age Band", each
                            let age = if [BirthYear] = null then null else ReferenceYear - [BirthYear]
                            in  if age = null then "Unknown"
                                else if age < 25 then "18–24"
                                else if age < 35 then "25–34"
                                else if age < 45 then "35–44"
                                else if age < 55 then "45–54"
                                else if age < 65 then "55–64"
                                else "65+", type text),
    AgeBandSort       = Table.AddColumn(AgeBand, "Age Band Sort", each List.PositionOf(AgeBands, [Age Band]) + 1, Int64.Type),
    // "C000123" -> 123 (integer surrogate key)
    WithKey           = Table.AddColumn(AgeBandSort, "CustomerKey", each Number.FromText(Text.Middle([CustomerID], 1)), Int64.Type),
    RemovedCols       = Table.RemoveColumns(WithKey, {"UpdatedAt"}),
    Renamed           = Table.RenameColumns(
                            RemovedCols,
                            {{"CustomerID", "Customer ID"}, {"BirthYear", "Birth Year"},
                             {"SignupDate", "Signup Date"}, {"MarketingConsent", "Marketing Consent"}}
                        ),
    Reordered         = Table.ReorderColumns(
                            Renamed,
                            {"CustomerKey", "Customer ID", "Segment", "Gender", "Birth Year", "Age Band", "Age Band Sort",
                             "City", "Country", "Signup Date", "Marketing Consent"}
                        ),
    // technical member for anonymous walk-in sales (CustomerKey = -1 in the fact table)
    AnonymousRow      = Table.InsertRows(
                            Reordered, 0,
                            {[CustomerKey = -1, #"Customer ID" = "ANONYMOUS", Segment = "Anonymous (walk-in)",
                              Gender = "Not specified", #"Birth Year" = null, #"Age Band" = "Unknown", #"Age Band Sort" = 7,
                              City = "Unknown", Country = "Unknown", #"Signup Date" = null, #"Marketing Consent" = false]}
                        )
in
    AnonymousRow
