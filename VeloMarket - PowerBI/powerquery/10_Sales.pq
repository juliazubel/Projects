// Query name: Sales      Group: 05 Facts
// Fact table at order-line grain. Converts local currency to PLN and replaces
// natural keys with integer surrogate keys.
let
    Source         = stg_SalesRaw,
    AddMonth       = Table.AddColumn(Source, "MonthStart", each Date.StartOfMonth([OrderDate]), type date),
    // currency conversion with the monthly average NBP rate (merge on 2 columns)
    MergeFx        = Table.NestedJoin(AddMonth, {"MonthStart", "Currency"}, stg_FxRates, {"MonthStart", "Currency"}, "Fx", JoinKind.LeftOuter),
    ExpandFx       = Table.ExpandTableColumn(MergeFx, "Fx", {"RateToPLN"}),
    UnitPricePLN   = Table.AddColumn(ExpandFx, "UnitPricePLN", each Number.Round([UnitPrice] * [RateToPLN], 2), Currency.Type),
    GrossAmount    = Table.AddColumn(UnitPricePLN, "GrossAmountPLN", each [Quantity] * [UnitPricePLN], Currency.Type),
    NetAmount      = Table.AddColumn(GrossAmount, "NetAmountPLN", each Number.Round([GrossAmountPLN] * (1 - [DiscountPct]), 2), Currency.Type),
    // surrogate keys
    MergeProduct   = Table.NestedJoin(NetAmount, {"SKU"}, Product, {"SKU"}, "P", JoinKind.LeftOuter),
    ExpandProduct  = Table.ExpandTableColumn(MergeProduct, "P", {"ProductKey"}),
    UnknownProduct = Table.ReplaceValue(ExpandProduct, null, -1, Replacer.ReplaceValue, {"ProductKey"}),
    MergeStore     = Table.NestedJoin(UnknownProduct, {"StoreID"}, Store, {"Store ID"}, "S", JoinKind.LeftOuter),
    ExpandStore    = Table.ExpandTableColumn(MergeStore, "S", {"StoreKey"}),
    CustomerKey    = Table.AddColumn(
                         ExpandStore, "CustomerKey",
                         each if [CustomerID] = null then -1 else Number.FromText(Text.Middle([CustomerID], 1)),
                         Int64.Type
                     ),
    // keep only what the model needs (narrow fact table = smaller model)
    Final          = Table.SelectColumns(
                         CustomerKey,
                         {"OrderID", "LineNo", "OrderDate", "ShipDate", "StoreKey", "ProductKey", "CustomerKey",
                          "Quantity", "UnitPricePLN", "DiscountPct", "GrossAmountPLN", "NetAmountPLN"}
                     ),
    Typed          = Table.TransformColumnTypes(Final, {{"StoreKey", Int64.Type}, {"ProductKey", Int64.Type}, {"DiscountPct", Percentage.Type}})
in
    Typed
