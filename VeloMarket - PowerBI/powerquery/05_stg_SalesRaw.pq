// Query name: stg_SalesRaw      Group: 03 Staging      (Enable load = OFF)
// Combines all monthly ERP exports from the /sales folder and fixes data-quality issues.
let
    // explicit schema of the parsed files -> expanded columns keep their data types
    SalesFileType = type table [
        OrderID = text, LineNo = Int64.Type, OrderDate = date, ShipDate = date,
        StoreID = text, CustomerID = nullable text, SKU = text, Quantity = Int64.Type,
        UnitPrice = number, DiscountPct = number, Currency = text
    ],
    Source       = Folder.Files(pDataFolder & "sales"),
    SalesFiles   = Table.SelectRows(
                       Source,
                       each Text.Lower([Extension]) = ".csv" and Text.StartsWith(Text.Lower([Name]), "sales_")
                   ),
    Parsed       = Table.AddColumn(SalesFiles, "Data", each fnParseSalesFile([Content]), SalesFileType),
    KeepCols     = Table.SelectColumns(Parsed, {"Name", "Data"}),
    Expanded     = Table.ExpandTableColumn(
                       KeepCols, "Data",
                       {"OrderID", "LineNo", "OrderDate", "ShipDate", "StoreID", "CustomerID",
                        "SKU", "Quantity", "UnitPrice", "DiscountPct", "Currency"}
                   ),
    RenamedFile  = Table.RenameColumns(Expanded, {{"Name", "SourceFile"}}),

    // --- data quality fixes ------------------------------------------------------------
    // 1) SKU arrives in mixed case and with stray spaces ("  vm-acc-0012 ")
    CleanSKU      = Table.TransformColumns(RenamedFile, {{"SKU", each Text.Upper(Text.Trim(_)), type text}}),
    // 2) anonymous walk-in customers come as empty strings -> null
    CleanCustomer = Table.TransformColumns(
                        CleanSKU,
                        {{"CustomerID", each if _ = null or Text.Trim(_) = "" then null else Text.Trim(_), type nullable text}}
                    ),
    // 3) QA test orders must never reach the report
    NoTestOrders  = Table.SelectRows(
                        CleanCustomer,
                        each [StoreID] <> "TEST-01" and ([CustomerID] = null or not Text.StartsWith([CustomerID], "TEST"))
                    ),
    // 4) the ERP re-exports some lines in the next month's file -> keep one row per order line
    Deduplicated  = Table.Distinct(NoTestOrders, {"OrderID", "LineNo"}),
    Final         = Table.RemoveColumns(Deduplicated, {"SourceFile"})
in
    Final
