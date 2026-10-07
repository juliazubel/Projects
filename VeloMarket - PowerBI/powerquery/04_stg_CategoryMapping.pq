// Query name: stg_CategoryMapping      Group: 03 Staging      (Enable load = OFF)
// Mapping table maintained by Finance (Polish budget category -> product master category).
let
    Source   = Excel.Workbook(File.Contents(pDataFolder & "budget.xlsx"), null, true),
    Sheet    = Source{[Item = "Mapowanie kategorii", Kind = "Sheet"]}[Data],
    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Promoted, {{"Kategoria PL", type text}, {"Category", type text}})
in
    Typed
