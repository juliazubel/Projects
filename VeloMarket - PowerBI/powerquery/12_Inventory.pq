// Query name: Inventory      Group: 05 Facts
// Month-end stock snapshots (semi-additive: can be summed over stores/products, NOT over time).
let
    Source         = Csv.Document(File.Contents(pDataFolder & "inventory_snapshots.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted       = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed          = Table.TransformColumnTypes(
                         Promoted,
                         {{"SnapshotDate", type date}, {"StoreID", type text}, {"SKU", type text}, {"StockQty", Int64.Type}},
                         "en-US"
                     ),
    MergeProduct   = Table.NestedJoin(Typed, {"SKU"}, Product, {"SKU"}, "P", JoinKind.LeftOuter),
    ExpandProduct  = Table.ExpandTableColumn(MergeProduct, "P", {"ProductKey"}),
    UnknownProduct = Table.ReplaceValue(ExpandProduct, null, -1, Replacer.ReplaceValue, {"ProductKey"}),
    MergeStore     = Table.NestedJoin(UnknownProduct, {"StoreID"}, Store, {"Store ID"}, "S", JoinKind.LeftOuter),
    ExpandStore    = Table.ExpandTableColumn(MergeStore, "S", {"StoreKey"}),
    Final          = Table.SelectColumns(ExpandStore, {"SnapshotDate", "StoreKey", "ProductKey", "StockQty"}),
    Typed2         = Table.TransformColumnTypes(Final, {{"StoreKey", Int64.Type}, {"ProductKey", Int64.Type}})
in
    Typed2
