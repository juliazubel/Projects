// Query name: fnParseSalesFile      Group: 02 Functions
// Parses ONE monthly ERP export (sales_YYYY_MM.csv) into a typed table.
// Used instead of the auto-generated "Combine Files" helper queries – one explicit, testable function.
(fileContent as binary) as table =>
let
    Source   = Csv.Document(
                   fileContent,
                   [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
               ),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // the ERP exports numbers with a dot and ISO dates -> parse with en-US culture,
    // independent of the regional settings of the machine that refreshes the report
    Typed    = Table.TransformColumnTypes(
                   Promoted,
                   {
                       {"OrderID", type text}, {"LineNo", Int64.Type},
                       {"OrderDate", type date}, {"ShipDate", type date},
                       {"StoreID", type text}, {"CustomerID", type text}, {"SKU", type text},
                       {"Quantity", Int64.Type}, {"UnitPrice", type number},
                       {"DiscountPct", type number}, {"Currency", type text}
                   },
                   "en-US"
               )
in
    Typed
