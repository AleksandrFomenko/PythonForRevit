import clr
import System

clr.AddReference('RevitAPI')
clr.AddReference("RevitServices")

import RevitServices

from Autodesk.Revit import DB
from Autodesk.Revit.DB import FilteredElementCollector as FEC

gen_model = [
    item
    for item in FEC(doc, doc.ActiveView.Id).
    OfCategory(DB.BuiltInCategory.OST_GenericModel)
    .WhereElementIsNotElementType()
    .ToElements() if item.get_Parameter(DB.BuiltInParameter.ELEM_FAMILY_PARAM).AsValueString() == "Секция 5"
]


def get_solid(element):
    opt = DB.Options()
    opt.DetailLevel = DB.ViewDetailLevel.Fine
    geometry_element = element.get_Geometry(opt)

    if geometry_element is None:
        print(f"Элемент с ID {element.Id} не имеет геометрии.")
        return None
    for geom_obj in geometry_element:
        if isinstance(geom_obj, DB.Solid):
            if geom_obj.Volume > 0:
                print(f"Элемент с ID {element.Id}: найден Solid с объемом {geom_obj.Volume}")
                return geom_obj
        elif isinstance(geom_obj, DB.GeometryInstance):
            inst_geom = geom_obj.GetInstanceGeometry()
            if inst_geom is None:
                print(f"Элемент с ID {element.Id}: GeometryInstance не имеет геометрии.")
                continue

            for inst_geom_obj in inst_geom:
                if isinstance(inst_geom_obj, DB.Solid):
                    print(f"Элемент с ID {element.Id}: найден Solid с объемом {inst_geom_obj.Volume}")
                    if inst_geom_obj.Volume > 0:
                        return inst_geom_obj

    print(f"Элемент с ID {element.Id} не содержит подходящего Solid.")
    return None


def qwe():
    if gen_model:
        solid = get_solid(gen_model[0])
        if not solid:
            print("Солида нет")
            return

    solid_intersec_filter = DB.ElementIntersectsSolidFilter(solid)

    worksets = FEC(doc, doc.ActiveView.Id). \
        WhereElementIsNotElementType(). \
        WherePasses(solid_intersec_filter). \
        ToElements()

    for item in worksets:
        par = item.LookupParameter("Фильтр по секциям")

        if not par:
            continue
        if par.IsReadOnly:
            continue

        par.Set("5 секция жилье")


with DB.Transaction(doc, "фыа") as t:
    t.Start()

    qwe()
    
    t.Commit()
