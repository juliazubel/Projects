// Query name: Store      Group: 04 Dimensions
let
    Source       = Csv.Document(File.Contents(pDataFolder & "stores.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted     = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed        = Table.TransformColumnTypes(
                       Promoted,
                       {
                           {"StoreID", type text}, {"StoreName", type text}, {"Channel", type text},
                           {"City", type text}, {"Country", type text}, {"CountryCode", type text},
                           {"Currency", type text}, {"Region", type text}, {"OpenDate", type date},
                           {"SalesAreaM2", Int64.Type}
                       },
                       "en-US"
                   ),
    ChannelGroup = Table.AddColumn(Typed, "Channel Group", each if [Channel] = "Store" then "Offline" else "Online", type text),
    Sorted       = Table.Sort(ChannelGroup, {{"StoreID", Order.Ascending}}),
    WithKey      = Table.AddIndexColumn(Sorted, "StoreKey", 1, 1, Int64.Type),
    Renamed      = Table.RenameColumns(
                       WithKey,
                       {{"StoreID", "Store ID"}, {"StoreName", "Store Name"}, {"CountryCode", "Country Code"},
                        {"OpenDate", "Open Date"}, {"SalesAreaM2", "Sales Area m2"}}
                   ),
    Reordered    = Table.ReorderColumns(
                       Renamed,
                       {"StoreKey", "Store ID", "Store Name", "Channel", "Channel Group", "City", "Country",
                        "Country Code", "Currency", "Region", "Open Date", "Sales Area m2"}
                   )
in
    Reordered
