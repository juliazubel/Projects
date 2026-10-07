// Query name: fnCleanBudgetSheet      Group: 02 Functions
// Turns one finance budget sheet ("Budget RRRR", wide: months as columns) into a long table.
(sheet as table) as table =>
let
    // skip the title rows until the header row ("Kraj") is reached
    SkipTitle = Table.Skip(sheet, each [Column1] <> "Kraj"),
    Promoted  = Table.PromoteHeaders(SkipTitle, [PromoteAllScalars = true]),
    // remove the grand-total row and the yearly total column – totals are calculated in the model
    NoTotals  = Table.SelectRows(Promoted, each [Kraj] <> null and [Kraj] <> "RAZEM"),
    NoSum     = Table.RemoveColumns(NoTotals, {"Suma"}),
    Unpivoted = Table.UnpivotOtherColumns(NoSum, {"Kraj", "Kategoria"}, "Miesiac", "BudgetKPLN")
in
    Unpivoted
