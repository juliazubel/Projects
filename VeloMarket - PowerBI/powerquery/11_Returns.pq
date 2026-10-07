// Query name: Returns      Group: 05 Facts
// Return lines enriched with keys and value of the original sales line (merge on OrderID + LineNo).
let
    Source       = Csv.Document(File.Contents(pDataFolder & "returns.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted     = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed        = Table.TransformColumnTypes(
                       Promoted,
                       {{"ReturnID", type text}, {"OrderID", type text}, {"LineNo", Int64.Type},
                        {"ReturnDate", type date}, {"ReturnQty", Int64.Type}, {"Reason", type text}},
                       "en-US"
                   ),
    SalesLines   = Table.SelectColumns(Sales, {"OrderID", "LineNo", "ProductKey", "StoreKey", "CustomerKey", "Quantity", "NetAmountPLN"}),
    // inner join: a return without a valid sales line (e.g. a test order) is dropped
    Merged       = Table.NestedJoin(Typed, {"OrderID", "LineNo"}, SalesLines, {"OrderID", "LineNo"}, "Line", JoinKind.Inner),
    Expanded     = Table.ExpandTableColumn(Merged, "Line", {"ProductKey", "StoreKey", "CustomerKey", "Quantity", "NetAmountPLN"}),
    ReturnAmount = Table.AddColumn(Expanded, "ReturnAmountPLN", each Number.Round([NetAmountPLN] / [Quantity] * [ReturnQty], 2), Currency.Type),
    Final        = Table.RemoveColumns(ReturnAmount, {"Quantity", "NetAmountPLN"})
in
    Final
