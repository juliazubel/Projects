// Query name: Product      Group: 04 Dimensions
// Source is a report-style Excel export: title rows on top and Category/Subcategory
// filled only on the first row of each group.
let
    Source        = Excel.Workbook(File.Contents(pDataFolder & "products.xlsx"), null, true),
    Sheet         = Source{[Item = "Products", Kind = "Sheet"]}[Data],
    // skip title rows until the real header row is found (robust to extra title lines)
    SkipTitle     = Table.Skip(Sheet, each [Column1] <> "Category"),
    Promoted      = Table.PromoteHeaders(SkipTitle, [PromoteAllScalars = true]),
    FilledDown    = Table.FillDown(Promoted, {"Category", "Subcategory"}),
    OnlyProducts  = Table.SelectRows(FilledDown, each [SKU] <> null and Text.Trim(Text.From([SKU])) <> ""),
    Typed         = Table.TransformColumnTypes(
                        OnlyProducts,
                        {
                            {"Category", type text}, {"Subcategory", type text}, {"SKU", type text},
                            {"Product Name", type text}, {"Brand", type text}, {"Color", type text},
                            {"List Price (PLN)", Currency.Type}, {"Unit Cost (PLN)", Currency.Type},
                            {"Launch Date", type date}, {"Status", type text}
                        }
                    ),
    Cleaned       = Table.TransformColumns(
                        Typed,
                        {{"SKU", each Text.Upper(Text.Trim(_)), type text}, {"Product Name", Text.Trim, type text}}
                    ),
    Renamed       = Table.RenameColumns(Cleaned, {{"List Price (PLN)", "List Price"}, {"Unit Cost (PLN)", "Unit Cost"}}),
    PriceBand     = Table.AddColumn(Renamed, "Price Band", each
                        if [List Price] < 200 then "< 200"
                        else if [List Price] < 1000 then "200–999"
                        else if [List Price] < 5000 then "1 000–4 999"
                        else "5 000+", type text),
    PriceBandSort = Table.AddColumn(PriceBand, "Price Band Sort", each
                        if [List Price] < 200 then 1
                        else if [List Price] < 1000 then 2
                        else if [List Price] < 5000 then 3
                        else 4, Int64.Type),
    Sorted        = Table.Sort(PriceBandSort, {{"SKU", Order.Ascending}}),
    // integer surrogate key – smaller dictionary and faster relationships than a text SKU
    WithKey       = Table.AddIndexColumn(Sorted, "ProductKey", 1, 1, Int64.Type),
    Reordered     = Table.ReorderColumns(
                        WithKey,
                        {"ProductKey", "SKU", "Product Name", "Category", "Subcategory", "Brand", "Color",
                         "List Price", "Unit Cost", "Launch Date", "Status", "Price Band", "Price Band Sort"}
                    ),
    // technical member for sales of SKUs missing in the master data (referential integrity)
    UnknownRow    = Table.InsertRows(
                        Reordered, 0,
                        {[ProductKey = -1, SKU = "UNKNOWN", #"Product Name" = "Unknown product",
                          Category = "Unknown", Subcategory = "Unknown", Brand = "Unknown", Color = "Unknown",
                          #"List Price" = 0, #"Unit Cost" = 0, #"Launch Date" = null, Status = "Unknown",
                          #"Price Band" = "Unknown", #"Price Band Sort" = 9]}
                    )
in
    UnknownRow
